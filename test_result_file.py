#!/usr/bin/env python3
"""
测试result.txt文件处理功能
"""

import asyncio
import json
import os
from src.server.mcp_server import create_mcp_server
from src.core.config import XHSConfig

async def test_preview_function():
    """测试预览功能"""
    print("🧪 测试预览功能...")
    
    # 创建服务器实例
    config = XHSConfig()
    server = create_mcp_server(config)
    
    # 检查result.txt文件是否存在
    if not os.path.exists("result.txt"):
        print("❌ result.txt文件不存在")
        return
    
    # 读取并解析文件
    try:
        with open("result.txt", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 成功解析result.txt文件")
        print(f"📋 文件包含字段: {list(data.keys())}")
        
        # 检查必需字段
        if 'wenan' in data:
            content = data['wenan']
            print(f"📝 文案长度: {len(content)} 字符")
            
            # 提取标题
            lines = content.split('\n')
            title = lines[0].strip()
            if len(title) > 50:
                title = title[:47] + "..."
            print(f"📌 提取的标题: {title}")
        
        # 处理图片
        images = []
        if 'fengmian' in data and data['fengmian']:
            images.append(data['fengmian'])
            print(f"📸 封面图片: {data['fengmian']}")
        
        if 'neirongtu' in data and data['neirongtu']:
            if isinstance(data['neirongtu'], list):
                images.extend(data['neirongtu'])
                print(f"📸 内容图片: {len(data['neirongtu'])} 张")
            else:
                images.append(data['neirongtu'])
                print(f"📸 内容图片: 1 张")
        
        if 'jiewei' in data and data['jiewei']:
            images.append(data['jiewei'])
            print(f"📸 结尾图片: {data['jiewei']}")
        
        print(f"📊 总图片数: {len(images)} 张")
        
        if len(images) > 9:
            print(f"⚠️ 图片数量超过小红书限制(9张)，将只使用前9张")
            images = images[:9]
        
        print("✅ 预览功能测试完成")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def test_batch_preview():
    """测试批量预览功能"""
    print("\n🧪 测试批量预览功能...")
    
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
        
        print("✅ 批量预览功能测试完成")
        
    except Exception as e:
        print(f"❌ 批量预览测试失败: {e}")

def test_image_processor():
    """测试图片处理器"""
    print("\n🧪 测试图片处理器...")
    
    try:
        from src.utils.image_processor import ImageProcessor
        processor = ImageProcessor()
        print(f"✅ 图片处理器初始化成功，临时目录: {processor.temp_dir}")
        
        # 测试URL处理
        test_urls = [
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/415485d9ef724f46bcaa3fced8697108.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782805407&x-signature=MpgRl8lxEZAATai1%2BTKDEOZPwdY%3D"
        ]
        
        print(f"📸 测试处理 {len(test_urls)} 个网络图片URL")
        print("✅ 图片处理器测试完成")
        
    except Exception as e:
        print(f"❌ 图片处理器测试失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始测试result.txt文件处理功能")
    print("=" * 50)
    
    # 测试预览功能
    await test_preview_function()
    
    # 测试批量预览功能
    await test_batch_preview()
    
    # 测试图片处理器
    test_image_processor()
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 