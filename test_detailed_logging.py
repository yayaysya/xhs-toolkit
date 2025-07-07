#!/usr/bin/env python3
"""
测试增强后的执行流程日志
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server.mcp_server import create_mcp_server
from src.core.config import XHSConfig
from src.xiaohongshu.models import XHSNote

async def test_detailed_logging():
    """测试详细的执行流程日志"""
    
    print("🧪 测试增强后的执行流程日志")
    print("=" * 50)
    
    # 创建MCP服务器实例
    config = XHSConfig()
    server = create_mcp_server(config)
    
    # 创建一个测试笔记（使用async_smart_create来处理网络图片）
    test_note = await XHSNote.async_smart_create(
        title="测试详细日志",
        content="这是一个测试详细执行流程日志的笔记",
        images=["https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/415485d9ef724f46bcaa3fced8697108.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782805407&x-signature=MpgRl8lxEZAATai1%2BTKDEOZPwdY%3D"]
    )
    
    # 创建任务
    task_id = server.task_manager.create_task(test_note)
    print(f"📋 创建测试任务: {task_id}")
    
    # 启动后台任务
    async_task = asyncio.create_task(server._execute_publish_task(task_id))
    server.task_manager.running_tasks[task_id] = async_task
    
    print(f"🚀 任务已启动，开始监控执行流程...")
    print(f"💡 请观察控制台输出的详细日志信息")
    print(f"📊 使用 check_task_status('{task_id}') 查看任务状态")
    
    # 监控任务状态
    max_wait_time = 60  # 最多等待60秒
    check_interval = 2  # 每2秒检查一次
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        task = server.task_manager.get_task(task_id)
        if task:
            print(f"⏰ [{elapsed_time:2d}s] 状态: {task.status} | 进度: {task.progress}% | 消息: {task.message}")
            
            if task.status in ["completed", "failed"]:
                print(f"🏁 任务结束，最终状态: {task.status}")
                if task.result:
                    print(f"📋 结果: {json.dumps(task.result, ensure_ascii=False, indent=2)}")
                break
        else:
            print(f"❌ 任务 {task_id} 不存在")
            break
        
        await asyncio.sleep(check_interval)
        elapsed_time += check_interval
    
    if elapsed_time >= max_wait_time:
        print(f"⏰ 等待超时，任务可能仍在执行中")
    
    print(f"\n✅ 测试完成")
    print(f"💡 详细日志已输出到控制台，请查看每个执行阶段的状态信息")

async def test_result_file_with_logging():
    """测试result.txt文件处理时的详细日志"""
    
    print(f"\n🧪 测试result.txt文件处理的详细日志")
    print("=" * 50)
    
    # 检查result.txt文件是否存在
    if not os.path.exists("result.txt"):
        print("❌ result.txt文件不存在，跳过测试")
        return
    
    # 创建MCP服务器实例
    config = XHSConfig()
    server = create_mcp_server(config)
    
    print(f"📁 找到result.txt文件，开始测试...")
    print(f"💡 请观察控制台输出的详细执行流程日志")
    
    # 这里只是演示，实际调用需要MCP客户端
    print(f"📋 实际使用时，请通过MCP客户端调用:")
    print(f"   • publish_from_result_file('result.txt')")
    print(f"   • check_task_status(task_id)")
    print(f"   • get_task_result(task_id)")
    
    print(f"\n✅ result.txt文件处理测试说明完成")

async def main():
    """主函数"""
    try:
        # 测试详细日志
        await test_detailed_logging()
        
        # 测试result.txt文件处理
        await test_result_file_with_logging()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 