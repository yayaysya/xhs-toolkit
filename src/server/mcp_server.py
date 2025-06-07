"""
小红书MCP服务器模块

提供MCP协议的服务器实现，支持AI客户端通过MCP协议与小红书交互
"""

import os
import json
import asyncio
import signal
import sys
import socket
import uuid
import time
from typing import Dict, Any
from dataclasses import dataclass, asdict

from fastmcp import FastMCP

from ..core.config import XHSConfig
from ..core.exceptions import format_error_message, XHSToolkitError
from ..xiaohongshu.client import XHSClient
from ..xiaohongshu.models import XHSNote
from ..utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


@dataclass
class PublishTask:
    """发布任务数据类"""
    task_id: str
    status: str  # "pending", "uploading", "filling", "publishing", "completed", "failed"
    note: XHSNote
    progress: int  # 0-100
    message: str
    result: Dict[str, Any] = None
    start_time: float = None
    end_time: float = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 移除note对象，避免序列化问题
        if 'note' in data:
            data['note_title'] = self.note.title
            data['note_has_images'] = bool(self.note.images)
            data['note_has_videos'] = bool(self.note.videos)
            del data['note']
        return data


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, PublishTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, note: XHSNote) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]  # 使用短ID
        task = PublishTask(
            task_id=task_id,
            status="pending",
            note=note,
            progress=0,
            message="任务已创建，准备开始",
            start_time=time.time()
        )
        self.tasks[task_id] = task
        logger.info(f"📋 创建新任务: {task_id} - {note.title}")
        return task_id
    
    def get_task(self, task_id: str) -> PublishTask:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: str = None, progress: int = None, message: str = None, result: Dict = None):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if status:
                task.status = status
            if progress is not None:
                task.progress = progress
            if message:
                task.message = message
            if result:
                task.result = result
            if status in ["completed", "failed"]:
                task.end_time = time.time()
            logger.info(f"📋 更新任务 {task_id}: {status} ({progress}%) - {message}")
    
    def remove_old_tasks(self, max_age_seconds: int = 3600):
        """移除超过指定时间的旧任务"""
        current_time = time.time()
        expired_tasks = []
        for task_id, task in self.tasks.items():
            if task.end_time and (current_time - task.end_time) > max_age_seconds:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self.tasks[task_id]
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
            logger.info(f"🗑️ 清理过期任务: {task_id}")


class MCPServer:
    """MCP服务器管理器"""
    
    def __init__(self, config: XHSConfig):
        """
        初始化MCP服务器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.xhs_client = XHSClient(config)
        self.mcp = FastMCP("小红书MCP服务器")
        self.task_manager = TaskManager()  # 添加任务管理器
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    def _setup_tools(self) -> None:
        """设置MCP工具"""
        
        @self.mcp.tool()
        async def test_connection() -> str:
            """
            测试MCP连接是否正常
            
            Returns:
                连接状态信息
            """
            logger.info("🧪 收到连接测试请求")
            try:
                import time
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                # 检查配置
                config_status = self.config.to_dict()
                config_status["current_time"] = current_time
                
                logger.info(f"✅ 连接测试完成: {config_status}")
                
                result = {
                    "status": "success",
                    "message": "MCP连接正常！",
                    "config": config_status,
                    "timestamp": current_time
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"连接测试失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return error_msg
        
        @self.mcp.tool()
        async def start_publish_task(title: str, content: str, tags: str = "", 
                                   location: str = "", images: str = "", videos: str = "") -> str:
            """
            启动异步发布任务（解决MCP超时问题）
            
            Args:
                title (str): 笔记标题，例如："今日分享"
                content (str): 笔记内容，例如："今天去了一个很棒的地方"
                tags (str, optional): 标签，用逗号分隔，例如："生活,旅行,美食"
                location (str, optional): 位置信息，例如："北京"
                images (str, optional): 图片文件路径，用逗号分隔
                videos (str, optional): 视频文件路径，用逗号分隔
            
            Returns:
                str: 任务ID和状态信息
            """
            logger.info(f"🚀 启动异步发布任务: 标题='{title}', 标签='{tags}', 位置='{location}', 图片='{images}', 视频='{videos}'")
            
            try:
                # 创建笔记对象
                note = XHSNote.from_strings(
                    title=title,
                    content=content,
                    tags_str=tags,
                    location=location,
                    images_str=images,
                    videos_str=videos
                )
                
                # 创建异步任务
                task_id = self.task_manager.create_task(note)
                
                # 启动后台任务
                async_task = asyncio.create_task(self._execute_publish_task(task_id))
                self.task_manager.running_tasks[task_id] = async_task
                
                result = {
                    "success": True,
                    "task_id": task_id,
                    "message": f"发布任务已启动，任务ID: {task_id}",
                    "next_step": f"请使用 check_task_status('{task_id}') 查看进度"
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"启动发布任务失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "message": error_msg
                }, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def check_task_status(task_id: str) -> str:
            """
            检查发布任务状态
            
            Args:
                task_id (str): 任务ID
            
            Returns:
                str: 任务状态信息
            """
            logger.info(f"📊 检查任务状态: {task_id}")
            
            task = self.task_manager.get_task(task_id)
            if not task:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 不存在"
                }, ensure_ascii=False, indent=2)
            
            # 计算运行时间
            elapsed_time = 0
            if task.start_time:
                elapsed_time = int(time.time() - task.start_time)
            
            result = {
                "success": True,
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "elapsed_seconds": elapsed_time,
                "is_completed": task.status in ["completed", "failed"]
            }
            
            # 如果任务完成，包含结果
            if task.result:
                result["result"] = task.result
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def get_task_result(task_id: str) -> str:
            """
            获取已完成任务的结果
            
            Args:
                task_id (str): 任务ID
            
            Returns:
                str: 任务结果信息
            """
            logger.info(f"📋 获取任务结果: {task_id}")
            
            task = self.task_manager.get_task(task_id)
            if not task:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 不存在"
                }, ensure_ascii=False, indent=2)
            
            if task.status not in ["completed", "failed"]:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 尚未完成，当前状态: {task.status}",
                    "current_status": task.status,
                    "progress": task.progress
                }, ensure_ascii=False, indent=2)
            
            # 返回完整结果
            result = {
                "success": task.status == "completed",
                "task_id": task_id,
                "status": task.status,
                "message": task.message,
                "execution_time": int(task.end_time - task.start_time) if task.end_time and task.start_time else 0
            }
            
            if task.result:
                result["publish_result"] = task.result
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def close_browser() -> str:
            """
            关闭浏览器
            
            Returns:
                关闭状态信息
            """
            logger.info("🔒 收到关闭浏览器请求")
            try:
                self.xhs_client.browser_manager.close_driver()
                logger.info("✅ 浏览器已关闭")
                return json.dumps({
                    "success": True,
                    "message": "浏览器已成功关闭"
                }, ensure_ascii=False, indent=2)
            except Exception as e:
                error_msg = f"关闭浏览器失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "message": error_msg
                }, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def test_publish_params(title: str, content: str, image_path: str = "") -> str:
            """
            测试发布参数解析（不实际发布）
            
            Args:
                title (str): 测试标题
                content (str): 测试内容
                image_path (str, optional): 测试图片路径
            
            Returns:
                str: 参数解析结果
            """
            logger.info(f"🧪 测试参数解析: title='{title}', content='{content}', image_path='{image_path}'")
            
            result = {
                "test_mode": True,
                "received_params": {
                    "title": title,
                    "content": content,
                    "image_path": image_path,
                    "title_length": len(title),
                    "content_length": len(content),
                    "image_path_valid": bool(image_path and image_path.startswith("/"))
                },
                "message": "参数接收成功，这是测试模式，未实际发布",
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            logger.info(f"✅ 测试完成: {result}")
            return json.dumps(result, ensure_ascii=False, indent=2)
    
    async def _execute_publish_task(self, task_id: str) -> None:
        """
        执行发布任务的后台逻辑
        
        Args:
            task_id: 任务ID
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            logger.error(f"❌ 任务 {task_id} 不存在")
            return
        
        try:
            # 阶段1：初始化浏览器
            self.task_manager.update_task(task_id, status="initializing", progress=10, message="正在初始化浏览器...")
            
            # 创建新的客户端实例，避免并发冲突
            client = XHSClient(self.config)
            
            # 阶段2：上传文件
            if task.note.images or task.note.videos:
                self.task_manager.update_task(task_id, status="uploading", progress=20, message="正在上传文件...")
                
                # 执行发布过程
                result = await client.publish_note(task.note)
                
                if result.success:
                    self.task_manager.update_task(
                        task_id, 
                        status="completed", 
                        progress=100, 
                        message="发布成功！",
                        result=result.to_dict()
                    )
                else:
                    self.task_manager.update_task(
                        task_id, 
                        status="failed", 
                        progress=0, 
                        message=f"发布失败: {result.message}",
                        result=result.to_dict()
                    )
            else:
                # 没有文件的快速发布
                self.task_manager.update_task(task_id, status="publishing", progress=60, message="正在发布笔记...")
                
                result = await client.publish_note(task.note)
                
                if result.success:
                    self.task_manager.update_task(
                        task_id, 
                        status="completed", 
                        progress=100, 
                        message="发布成功！",
                        result=result.to_dict()
                    )
                else:
                    self.task_manager.update_task(
                        task_id, 
                        status="failed", 
                        progress=0, 
                        message=f"发布失败: {result.message}",
                        result=result.to_dict()
                    )
                
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            logger.error(f"❌ 任务 {task_id} 执行失败: {e}")
            self.task_manager.update_task(
                task_id, 
                status="failed", 
                progress=0, 
                message=error_msg,
                result={"success": False, "message": error_msg}
            )
        finally:
            # 清理运行任务记录
            if task_id in self.task_manager.running_tasks:
                del self.task_manager.running_tasks[task_id]

    def _setup_resources(self) -> None:
        """设置MCP资源"""
        
        @self.mcp.resource("xhs://config")
        def get_xhs_config() -> str:
            """获取小红书MCP服务器配置信息"""
            config_info = self.config.to_dict()
            config_info["server_status"] = "running"
            return json.dumps(config_info, ensure_ascii=False, indent=2)
        
        @self.mcp.resource("xhs://help")
        def get_xhs_help() -> str:
            """获取小红书MCP服务器使用帮助"""
            help_text = """
# 小红书MCP服务器使用帮助

## 可用工具

### 1. test_connection
- 功能: 测试MCP连接
- 参数: 无

### 2. start_publish_task
- 功能: 启动异步发布任务（解决MCP超时问题）
- 参数:
  - title: 笔记标题
  - content: 笔记内容
  - tags: 标签（逗号分隔）
  - location: 位置信息
  - images: 图片路径（逗号分隔多个路径）
  - videos: 视频路径（逗号分隔多个路径）

### 3. check_task_status
- 功能: 检查发布任务状态
- 参数:
  - task_id: 任务ID

### 4. get_task_result
- 功能: 获取已完成任务的结果
- 参数:
  - task_id: 任务ID

### 5. close_browser
- 功能: 关闭浏览器

### 6. test_publish_params
- 功能: 测试发布参数解析（调试用）
- 参数:
  - title: 测试标题
  - content: 测试内容
  - image_path: 测试图片路径

## 可用资源

- xhs://config - 查看服务器配置
- xhs://help - 查看此帮助信息

## 环境变量

- CHROME_PATH: Chrome浏览器路径
- WEBDRIVER_CHROME_DRIVER: ChromeDriver路径
- json_path: Cookies文件路径
"""
            return help_text
    
    def _setup_prompts(self) -> None:
        """设置MCP提示词"""
        
        @self.mcp.prompt()
        def xiaohongshu_content_creation(topic: str, style: str = "生活分享") -> str:
            """
            小红书内容创作助手
            
            Args:
                topic: 内容主题
                style: 写作风格（生活分享、美妆护肤、美食探店、旅行攻略等）
            
            Returns:
                内容创作提示词
            """
            prompt = f"""
请帮我创作一篇关于"{topic}"的小红书笔记，风格为"{style}"。

要求：
1. 标题要吸引人，包含emoji和关键词
2. 内容要有价值，包含具体的建议或信息
3. 适当使用emoji让内容更生动
4. 添加相关标签（3-5个）
5. 字数控制在200-500字
6. 语言风格要贴近小红书用户习惯

请按以下格式输出：

【标题】
[在这里写标题]

【正文】
[在这里写正文内容]

【标签】
[在这里列出相关标签]

【发布建议】
[发布时间、配图建议等]
"""
            return prompt
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info("👋 收到停止信号，正在优雅关闭服务器...")
            # 清理资源
            try:
                if hasattr(self.xhs_client, 'browser_manager') and self.xhs_client.browser_manager.is_initialized:
                    logger.info("🧹 清理残留的浏览器实例...")
                    self.xhs_client.browser_manager.close_driver()
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理资源时出错: {cleanup_error}")
            
            logger.info("✅ 服务器已停止")
            os._exit(0)  # 强制退出避免ASGI错误
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self) -> None:
        """启动MCP服务器"""
        logger.info("🚀 启动小红书 MCP 服务器...")
        
        # 设置日志级别
        setup_logger(self.config.log_level)
        
        # 验证配置
        logger.info("🔍 验证配置...")
        validation = self.config.validate_config()
        
        if not validation["valid"]:
            logger.error("❌ 配置验证失败:")
            for issue in validation["issues"]:
                logger.error(f"   • {issue}")
            logger.error("💡 请检查 .env 文件配置")
            return
        
        logger.info("✅ 配置验证通过")
        
        # 检查cookies
        cookies = self.xhs_client.cookie_manager.load_cookies()
        if not cookies:
            logger.warning("⚠️ 未找到cookies文件，请先运行获取cookies")
            logger.info("💡 运行命令: python xhs_toolkit.py cookie save")
        else:
            logger.info(f"✅ 已加载 {len(cookies)} 个cookies")
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 获取本机IP地址
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.254.254.254", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"📡 本机IP地址: {local_ip}")
        except Exception:
            local_ip = "未知"
            
        logger.info(f"🚀 启动SSE服务器 (端口{self.config.server_port})")
        logger.info("📡 可通过以下地址访问:")
        logger.info(f"   • http://localhost:{self.config.server_port}/sse (本机)")
        if local_ip != "未知":
            logger.info(f"   • http://{local_ip}:{self.config.server_port}/sse (内网)")
        
        logger.info("🎯 MCP工具列表:")
        logger.info("   • test_connection - 测试连接")
        logger.info("   • start_publish_task - 启动异步发布任务")
        logger.info("   • check_task_status - 检查任务状态")
        logger.info("   • get_task_result - 获取任务结果")
        logger.info("   • close_browser - 关闭浏览器")
        logger.info("   • test_publish_params - 测试参数")
        
        logger.info("🔧 按 Ctrl+C 停止服务器")
        logger.info("💡 终止时的ASGI错误信息是正常现象，可以忽略")
        
        try:
            # 使用FastMCP内置的run方法
            self.mcp.run(transport="sse", port=self.config.server_port, host=self.config.server_host)
            
        except KeyboardInterrupt:
            logger.info("👋 收到停止信号，正在关闭服务器...")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {e}")
            raise
        finally:
            # 清理资源
            try:
                if hasattr(self.xhs_client, 'browser_manager') and self.xhs_client.browser_manager.is_initialized:
                    logger.info("🧹 清理残留的浏览器实例...")
                    self.xhs_client.browser_manager.close_driver()
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理资源时出错: {cleanup_error}")
            
            logger.info("✅ 服务器已停止")


# 便捷函数
def create_mcp_server(config: XHSConfig) -> MCPServer:
    """
    创建MCP服务器的便捷函数
    
    Args:
        config: 配置管理器实例
        
    Returns:
        MCP服务器实例
    """
    return MCPServer(config)


def main():
    """主函数入口"""
    from ..core.config import XHSConfig
    
    config = XHSConfig()
    server = MCPServer(config)
    server.start()


if __name__ == "__main__":
    main() 