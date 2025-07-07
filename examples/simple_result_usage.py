#!/usr/bin/env python3
"""
简化的Result.txt文件使用示例

展示如何使用result.txt文件处理功能，不依赖MCP客户端
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server.mcp_server import create_mcp_server
from src.core.config import XHSConfig

async def demo_result_file_processing():
    """演示result.txt文件处理功能"""
    
    print("🚀 Result.txt文件处理功能演示")
    print("=" * 50)
    
    # 创建MCP服务器实例
    config = XHSConfig()
    server = create_mcp_server(config)
    
    # 1. 检查文件是否存在
    if not os.path.exists("result.txt"):
        print("❌ result.txt文件不存在，请先创建该文件")
        return
    
    print("✅ 找到result.txt文件")
    
    # 2. 读取并解析文件
    try:
        with open("result.txt", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 成功解析JSON文件")
        print(f"📋 包含字段: {list(data.keys())}")
        
        # 3. 验证必需字段
        if 'wenan' not in data:
            print("❌ 缺少必需字段 'wenan'")
            return
        
        content = data['wenan']
        print(f"📝 文案长度: {len(content)} 字符")
        
        # 4. 提取标题
        lines = content.split('\n')
        title = lines[0].strip()
        if len(title) > 50:
            title = title[:47] + "..."
        print(f"📌 提取的标题: {title}")
        
        # 5. 处理图片
        images = []
        
        if 'fengmian' in data and data['fengmian']:
            images.append(data['fengmian'])
            print(f"📸 封面图片: 已添加")
        
        if 'neirongtu' in data and data['neirongtu']:
            if isinstance(data['neirongtu'], list):
                images.extend(data['neirongtu'])
                print(f"📸 内容图片: {len(data['neirongtu'])} 张")
            else:
                images.append(data['neirongtu'])
                print(f"📸 内容图片: 1 张")
        
        if 'jiewei' in data and data['jiewei']:
            images.append(data['jiewei'])
            print(f"📸 结尾图片: 已添加")
        
        print(f"📊 总图片数: {len(images)} 张")
        
        # 6. 检查限制
        if len(images) > 9:
            print(f"⚠️ 图片数量超过小红书限制(9张)，将只使用前9张")
            images = images[:9]
        
        # 7. 模拟创建笔记
        print(f"\n📝 模拟创建小红书笔记...")
        print(f"   标题: {title}")
        print(f"   图片: {len(images)} 张")
        print(f"   文案: {len(content)} 字符")
        
        # 8. 显示发布建议
        print(f"\n💡 发布建议:")
        print(f"   • 使用 publish_from_result_file() 发布单个条目")
        print(f"   • 使用 batch_publish_from_result_files() 批量发布")
        print(f"   • 使用 preview_result_file() 预览文件内容")
        
        print(f"\n✅ 文件处理演示完成")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
    except Exception as e:
        print(f"❌ 处理失败: {e}")

async def demo_batch_processing():
    """演示批量处理功能"""
    
    print(f"\n🔄 批量处理功能演示")
    print("=" * 30)
    
    # 检查批量示例文件
    if not os.path.exists("result_batch_example.txt"):
        print("❌ result_batch_example.txt文件不存在")
        return
    
    try:
        with open("result_batch_example.txt", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            print(f"✅ 成功解析批量文件，包含 {len(data)} 个条目")
            
            for idx, item in enumerate(data):
                print(f"\n📋 条目 {idx + 1}:")
                
                if 'wenan' in item:
                    content = item['wenan']
                    lines = content.split('\n')
                    title = lines[0].strip()
                    if len(title) > 50:
                        title = title[:47] + "..."
                    print(f"  标题: {title}")
                    print(f"  文案长度: {len(content)} 字符")
                
                # 统计图片
                images = []
                if 'fengmian' in item and item['fengmian']:
                    images.append(item['fengmian'])
                if 'neirongtu' in item and item['neirongtu']:
                    if isinstance(item['neirongtu'], list):
                        images.extend(item['neirongtu'])
                    else:
                        images.append(item['neirongtu'])
                if 'jiewei' in item and item['jiewei']:
                    images.append(item['jiewei'])
                
                print(f"  图片数量: {len(images)} 张")
            
            print(f"\n💡 批量发布建议:")
            print(f"   • 使用 batch_publish_from_result_files('result_batch_example.txt', 3) 发布前3个条目")
            print(f"   • 每个条目会创建独立的发布任务")
            print(f"   • 使用任务ID跟踪每个条目的发布进度")
        
        print(f"✅ 批量处理演示完成")
        
    except Exception as e:
        print(f"❌ 批量处理演示失败: {e}")

def show_usage_instructions():
    """显示使用说明"""
    
    print(f"\n📖 使用说明")
    print("=" * 30)
    
    print("1️⃣ 准备数据文件:")
    print("   • 创建result.txt文件，包含JSON格式的数据")
    print("   • 确保包含 'wenan' 字段（必需）")
    print("   • 可选字段: fengmian, neirongtu, jiewei")
    
    print(f"\n2️⃣ 使用MCP工具:")
    print("   • preview_result_file() - 预览文件内容")
    print("   • publish_from_result_file() - 发布单个条目")
    print("   • batch_publish_from_result_files() - 批量发布")
    
    print(f"\n3️⃣ 监控发布进度:")
    print("   • check_task_status(task_id) - 检查任务状态")
    print("   • get_task_result(task_id) - 获取发布结果")
    
    print(f"\n4️⃣ 文件格式示例:")
    print("   • 单个条目: JSON对象")
    print("   • 批量条目: JSON数组")
    print("   • 支持网络图片URL")
    print("   • 自动下载和处理图片")

async def main():
    """主函数"""
    try:
        # 演示单个文件处理
        await demo_result_file_processing()
        
        # 演示批量处理
        await demo_batch_processing()
        
        # 显示使用说明
        show_usage_instructions()
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 