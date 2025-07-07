#!/usr/bin/env python3
"""
Result.txt文件使用示例

展示如何通过MCP客户端使用result.txt文件处理功能
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def example_usage():
    """使用示例"""
    
    # 连接到MCP服务器
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server.mcp_server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            print("🚀 连接到小红书MCP服务器")
            
            # 1. 测试连接
            print("\n1️⃣ 测试连接...")
            result = await session.call_tool("test_connection", {})
            result_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            print(f"连接状态: {result_text[:100]}...")
            
            # 2. 预览result.txt文件
            print("\n2️⃣ 预览result.txt文件...")
            preview_result = await session.call_tool("preview_result_file", {
                "file_path": "result.txt"
            })
            preview_text = preview_result.content[0].text if hasattr(preview_result.content[0], 'text') else str(preview_result.content[0])
            preview_data = json.loads(preview_text)
            
            if preview_data["success"]:
                print(f"✅ 文件预览成功")
                print(f"📊 文件信息: {preview_data['file_info']}")
                print(f"📋 内容摘要: {preview_data['content_summary']}")
                
                # 显示建议
                if preview_data.get("recommendations"):
                    print("💡 建议:")
                    for rec in preview_data["recommendations"]:
                        print(f"   • {rec}")
            else:
                print(f"❌ 预览失败: {preview_data['message']}")
            
            # 3. 发布单个条目
            print("\n3️⃣ 发布result.txt文件内容...")
            publish_result = await session.call_tool("publish_from_result_file", {
                "file_path": "result.txt"
            })
            publish_text = publish_result.content[0].text if hasattr(publish_result.content[0], 'text') else str(publish_result.content[0])
            publish_data = json.loads(publish_text)
            
            if publish_data["success"]:
                task_id = publish_data["task_id"]
                print(f"✅ 发布任务已启动，任务ID: {task_id}")
                
                # 4. 检查任务状态
                print(f"\n4️⃣ 检查任务状态...")
                status_result = await session.call_tool("check_task_status", {
                    "task_id": task_id
                })
                status_text = status_result.content[0].text if hasattr(status_result.content[0], 'text') else str(status_result.content[0])
                status_data = json.loads(status_text)
                
                if status_data["success"]:
                    print(f"📊 任务状态: {status_data['status']}")
                    print(f"📈 进度: {status_data['progress']}%")
                    print(f"💬 消息: {status_data['message']}")
                    
                    # 如果任务完成，获取结果
                    if status_data["is_completed"]:
                        print(f"\n5️⃣ 获取任务结果...")
                        result_data = await session.call_tool("get_task_result", {
                            "task_id": task_id
                        })
                        final_result = json.loads(result_data.content[0].text)
                        
                        if final_result["success"]:
                            print(f"🎉 发布成功!")
                            if "publish_result" in final_result:
                                print(f"📝 发布结果: {final_result['publish_result']}")
                        else:
                            print(f"❌ 发布失败: {final_result['message']}")
                else:
                    print(f"❌ 状态检查失败: {status_data['message']}")
            else:
                print(f"❌ 发布失败: {publish_data['message']}")
            
            # 5. 批量处理示例（如果有批量文件）
            print(f"\n6️⃣ 测试批量处理...")
            try:
                batch_result = await session.call_tool("batch_publish_from_result_files", {
                    "file_path": "result_batch_example.txt",
                    "max_items": 2
                })
                batch_data = json.loads(batch_result.content[0].text)
                
                if batch_data["success"]:
                    print(f"✅ 批量处理成功")
                    print(f"📊 处理信息: {batch_data['batch_info']}")
                    print(f"🆔 任务ID列表: {batch_data['task_ids']}")
                else:
                    print(f"❌ 批量处理失败: {batch_data['message']}")
            except Exception as e:
                print(f"⚠️ 批量处理测试跳过: {e}")

async def main():
    """主函数"""
    try:
        await example_usage()
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("📖 Result.txt文件使用示例")
    print("=" * 50)
    asyncio.run(main()) 