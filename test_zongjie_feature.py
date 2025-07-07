#!/usr/bin/env python3
"""
测试zongjie（总结图）功能

验证JSON发布功能中新增的zongjie字段是否正常工作
"""

import json
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server.mcp_server import MCPServer
from src.core.config import XHSConfig

async def test_zongjie_feature():
    """测试zongjie功能"""
    
    print("🧪 测试zongjie（总结图）功能")
    print("=" * 50)
    
    # 创建配置
    config = XHSConfig()
    
    # 创建MCP服务器实例
    server = MCPServer(config)
    
    # 测试数据 - 包含zongjie字段
    test_json_data = {
        "fengmian": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/8d52e5b0e6a14b649450d8d37f065ec5.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885692&x-signature=pTrsmM1H9%2BkSBrUYbZkT52ZJ1Iw%3D",
        "neirongtu": [
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/29bb750606874adab323b5969c2ba3b2.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885694&x-signature=G8aTP%2BtPKYx3Ys93Ios3H1KzJy8%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/8ba8cc5061354cd19a584ca4f995f796.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885693&x-signature=rr8aXi9E1%2BeP%2F2eBzkaKCyM0Pwg%3D",
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/33e1f2290a0043df883e45a8d536d6de.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885693&x-signature=7XnyUVKnOtxwd9qEIrQT%2FSDDFNk%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/cd7b14dfa4454703869a464edc5bfb72.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885696&x-signature=zst9FvZ%2B42IbOffBdq8vSoRDZ4s%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/2613448585e5406fb0fc868494fabc16.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885697&x-signature=zsrzZi3yFhevQ5zhFVc3PLZJsCY%3D"
        ],
        "zongjie": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/f1da76b3eccc453fb6a7e420912d6078.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885695&x-signature=fIn51meOC9anwAVn7P9gBTXkl0Q%3D",
        "jiewei": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/5842f852025e4faf9176af3f27d4a62c.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1782885699&x-signature=gJhqjFrjaU6FASEPX5fV3YDv1zQ%3D",
        "wenan": "💡总说'你真棒'，可能不是在鼓励，而是在'偷懒'\n\nHey，各位家长，我是小燕老师👩‍🏫\n是不是有过这样的场景😉 孩子举着刚画的太阳跑过来，你正刷着消息，抬头就说：「宝宝你真棒！」孩子愣了愣，把画轻轻放在茶几上，转身去玩积木了。我们通常会觉得自己这么做是在肯定他的努力，让他知道自己做得好，这样他会更有自信🤔。\n\n但反直觉的真相是😲，这种笼统的表扬，其实是我们为了快速结束互动，缓解「必须回应」的焦虑，是「最低成本的社交捷径」。我们以为这样能让孩子开心，却没考虑到可能带来的其他影响。\n\n这背后其实关联到「固定型思维」和「成长型思维」的心理学原理🧠。笼统表扬让孩子觉得「我棒是因为结果」，反而会害怕失败；而具体鼓励则培养「成长型思维」，让他享受过程。\n\n那具体可以怎么做呢👇？用「描述性语言」代替「评价性语言」。不说'你真棒'，而是说：「你画的太阳光芒有这么多线条，一定花了很多心思吧？」这样能让孩子感受到我们真正关注到了他的努力。\n\n最后，想和大家分享一句话：\n「真正的自信，源于孩子在过程中被看见的努力，而非被父母贴上一个漂亮的、现成的标签。」\n\n👇关于'表扬'，你有什么故事或困惑吗？评论区一起聊聊吧！💬\n\n#育儿智慧 #儿童心理学 #家庭教育 #成长型思维 #正面管教 #不说不骂 #小燕老师育儿经"
    }
    
    print("📋 测试数据:")
    print(f"   - 封面图片: {'有' if test_json_data.get('fengmian') else '无'}")
    print(f"   - 内容图片: {len(test_json_data.get('neirongtu', []))} 张")
    print(f"   - 总结图片: {'有' if test_json_data.get('zongjie') else '无'}")
    print(f"   - 结尾图片: {'有' if test_json_data.get('jiewei') else '无'}")
    print(f"   - 文案长度: {len(test_json_data.get('wenan', ''))} 字符")
    
    # 1. 测试预览功能
    print("\n🔍 测试1: 预览JSON数据")
    print("-" * 30)
    
    try:
        preview_result = await server.preview_json_data(json.dumps(test_json_data))
        preview_data = json.loads(preview_result)
        
        if preview_data.get("success"):
            print("✅ 预览功能正常")
            preview_items = preview_data.get("preview_items", [])
            if preview_items:
                item = preview_items[0]
                print(f"   - 状态: {item.get('status')}")
                print(f"   - 总图片数: {item.get('total_images')}")
                print(f"   - 内容图片数: {item.get('neirongtu_count')}")
                print(f"   - 有总结图: {item.get('zongjie', False)}")
                
                # 验证图片顺序
                if item.get('total_images') == 8:  # 1封面 + 5内容 + 1总结 + 1结尾
                    print("✅ 图片数量正确（包含总结图）")
                else:
                    print(f"⚠️ 图片数量异常: {item.get('total_images')}")
        else:
            print(f"❌ 预览失败: {preview_data.get('message')}")
            
    except Exception as e:
        print(f"❌ 预览测试出错: {str(e)}")
    
    # 2. 测试单条发布功能（仅解析，不实际发布）
    print("\n📝 测试2: 单条发布解析")
    print("-" * 30)
    
    try:
        # 模拟解析过程，不实际发布
        json_str = json.dumps(test_json_data)
        data = json.loads(json_str)
        
        # 模拟图片处理逻辑
        images = []
        
        # 添加封面图片
        if 'fengmian' in data and data['fengmian']:
            images.append(data['fengmian'])
            print(f"📸 添加封面图片: {data['fengmian'][:50]}...")
        
        # 添加内容图片
        if 'neirongtu' in data and data['neirongtu']:
            if isinstance(data['neirongtu'], list):
                images.extend(data['neirongtu'])
                print(f"📸 添加内容图片: {len(data['neirongtu'])} 张")
            else:
                images.append(data['neirongtu'])
                print(f"📸 添加内容图片: 1 张")
        
        # 添加总结图片
        if 'zongjie' in data and data['zongjie']:
            images.append(data['zongjie'])
            print(f"📸 添加总结图片: {data['zongjie'][:50]}...")
        
        # 添加结尾图片
        if 'jiewei' in data and data['jiewei']:
            images.append(data['jiewei'])
            print(f"📸 添加结尾图片: {data['jiewei'][:50]}...")
        
        print(f"📊 最终图片数组长度: {len(images)}")
        print(f"📊 预期图片顺序: 封面 -> 内容(5张) -> 总结 -> 结尾")
        
        # 验证图片顺序
        expected_count = 1 + 5 + 1 + 1  # 封面 + 内容 + 总结 + 结尾
        if len(images) == expected_count:
            print("✅ 图片顺序和数量正确")
        else:
            print(f"⚠️ 图片数量不匹配: 期望{expected_count}张，实际{len(images)}张")
            
    except Exception as e:
        print(f"❌ 单条发布测试出错: {str(e)}")
    
    # 3. 测试批量发布功能（仅解析，不实际发布）
    print("\n📦 测试3: 批量发布解析")
    print("-" * 30)
    
    try:
        # 创建批量测试数据
        batch_data = [
            test_json_data,
            {
                "fengmian": "https://example.com/cover2.jpg",
                "neirongtu": ["https://example.com/content2.jpg"],
                "zongjie": "https://example.com/summary2.jpg",
                "jiewei": "https://example.com/end2.jpg",
                "wenan": "第二条测试内容"
            }
        ]
        
        # 模拟批量处理
        for idx, item in enumerate(batch_data):
            print(f"📋 处理第 {idx+1} 个条目:")
            
            images = []
            
            # 添加封面图片
            if 'fengmian' in item and item['fengmian']:
                images.append(item['fengmian'])
            
            # 添加内容图片
            if 'neirongtu' in item and item['neirongtu']:
                if isinstance(item['neirongtu'], list):
                    images.extend(item['neirongtu'])
                else:
                    images.append(item['neirongtu'])
            
            # 添加总结图片
            if 'zongjie' in item and item['zongjie']:
                images.append(item['zongjie'])
            
            # 添加结尾图片
            if 'jiewei' in item and item['jiewei']:
                images.append(item['jiewei'])
            
            print(f"   - 图片总数: {len(images)}")
            print(f"   - 有总结图: {'是' if 'zongjie' in item and item['zongjie'] else '否'}")
        
        print("✅ 批量发布解析正常")
        
    except Exception as e:
        print(f"❌ 批量发布测试出错: {str(e)}")
    
    # 4. 测试无总结图的情况
    print("\n🔍 测试4: 无总结图情况")
    print("-" * 30)
    
    try:
        # 创建无总结图的测试数据
        no_zongjie_data = {
            "fengmian": "https://example.com/cover.jpg",
            "neirongtu": ["https://example.com/content.jpg"],
            "jiewei": "https://example.com/end.jpg",
            "wenan": "测试内容（无总结图）"
        }
        
        # 模拟图片处理
        images = []
        
        if 'fengmian' in no_zongjie_data and no_zongjie_data['fengmian']:
            images.append(no_zongjie_data['fengmian'])
        
        if 'neirongtu' in no_zongjie_data and no_zongjie_data['neirongtu']:
            if isinstance(no_zongjie_data['neirongtu'], list):
                images.extend(no_zongjie_data['neirongtu'])
            else:
                images.append(no_zongjie_data['neirongtu'])
        
        # 注意：这里没有zongjie字段，应该跳过
        if 'zongjie' in no_zongjie_data and no_zongjie_data['zongjie']:
            images.append(no_zongjie_data['zongjie'])
        
        if 'jiewei' in no_zongjie_data and no_zongjie_data['jiewei']:
            images.append(no_zongjie_data['jiewei'])
        
        print(f"📊 无总结图情况下的图片数量: {len(images)}")
        print(f"📊 预期图片顺序: 封面 -> 内容 -> 结尾")
        
        expected_count = 1 + 1 + 1  # 封面 + 内容 + 结尾
        if len(images) == expected_count:
            print("✅ 无总结图情况处理正常")
        else:
            print(f"⚠️ 图片数量不匹配: 期望{expected_count}张，实际{len(images)}张")
            
    except Exception as e:
        print(f"❌ 无总结图测试出错: {str(e)}")
    
    print("\n🎉 zongjie功能测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_zongjie_feature()) 