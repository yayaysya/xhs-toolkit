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
from typing import Dict, Any

from fastmcp import FastMCP

from ..core.config import XHSConfig
from ..core.exceptions import format_error_message, XHSToolkitError
from ..xiaohongshu.client import XHSClient
from ..xiaohongshu.models import XHSNote
from ..utils.logger import get_logger, setup_logger

logger = get_logger(__name__)


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
        async def publish_xiaohongshu_note(title: str, content: str, tags: str = "", 
                                         location: str = "", images: str = "") -> str:
            """
            发布小红书笔记
            
            Args:
                title (str): 笔记标题，例如："今日分享"
                content (str): 笔记内容，例如："今天去了一个很棒的地方"
                tags (str, optional): 标签，用逗号分隔，例如："生活,旅行,美食"
                location (str, optional): 位置信息，例如："北京"
                images (str, optional): 图片文件路径，用逗号分隔，例如："/Volumes/xhs-files/image1.jpg,/Volumes/xhs-files/image2.jpg"
            
            Returns:
                str: 发布结果的JSON字符串
                
            Example:
                title="今日美食", content="推荐一家好吃的餐厅", tags="美食,生活", images="/Volumes/xhs-files/food.jpg"
            """
            logger.info(f"📝 开始发布小红书笔记: 标题='{title}', 标签='{tags}', 位置='{location}', 图片='{images}'")
            
            try:
                note = XHSNote.from_strings(
                    title=title,
                    content=content,
                    tags_str=tags,
                    location=location,
                    images_str=images
                )
                
                logger.info(f"📸 处理图片路径: {note.images}")
                logger.info("📱 正在初始化浏览器...")
                
                result = await self.xhs_client.publish_note(note)
                logger.info(f"✅ 发布笔记完成: {result.success}")
                
                return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"发布笔记失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                if isinstance(e, XHSToolkitError):
                    return json.dumps({
                        "success": False,
                        "message": format_error_message(e),
                        "error_type": e.error_code
                    }, ensure_ascii=False, indent=2)
                else:
                    return json.dumps({
                        "success": False,
                        "message": error_msg,
                        "error_type": "UNKNOWN_ERROR"
                    }, ensure_ascii=False, indent=2)
        
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

### 2. publish_xiaohongshu_note
- 功能: 发布新笔记
- 参数:
  - title: 笔记标题
  - content: 笔记内容
  - tags: 标签（逗号分隔）
  - location: 位置信息
  - images: 图片路径（逗号分隔多个路径）

### 3. close_browser
- 功能: 关闭浏览器

### 4. test_publish_params
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
        logger.info("   • publish_xiaohongshu_note - 发布笔记")
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