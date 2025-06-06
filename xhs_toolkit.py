#!/usr/bin/env python3
"""
小红书MCP工具包 - 统一入口

集成cookie管理和MCP服务器功能的统一工具
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path

# 加载环境变量配置
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

def print_banner():
    """打印工具横幅"""
    banner = """
╭─────────────────────────────────────────╮
│          🌺 小红书MCP工具包             │
│     Xiaohongshu MCP Toolkit v1.0        │
╰─────────────────────────────────────────╯
"""
    print(banner)

def cookie_command(action):
    """处理cookie相关命令"""
    print(f"🍪 执行Cookie操作: {action}")
    
    if action == "save":
        print("📝 注意：新版本直接获取创作者中心权限cookies")
        print("🔧 这将解决跳转到创作者中心时cookies失效的问题")
    
    try:
        # 直接导入并调用具体函数，更清晰更可靠
        import cookie_helper
        
        if action == "save":
            result = cookie_helper.save_cookies_interactive()
            if result:
                print("\n🎉 Cookies获取成功！")
                print("💡 现在可以正常访问创作者中心功能了")
            return result
        elif action == "show":
            cookie_helper.load_and_display_cookies()
            return True
        elif action == "validate":
            result = cookie_helper.validate_cookies()
            if result:
                print("✅ Cookies验证通过，可以正常使用创作者功能")
            else:
                print("❌ Cookies验证失败，可能影响创作者中心访问")
                print("💡 建议重新获取: python cookie_helper.py save")
            return result
        else:
            print(f"❌ 未知操作: {action}")
            return False
            
    except Exception as e:
        print(f"❌ Cookie操作失败: {e}")
        if action == "save":
            print("💡 常见解决方案:")
            print("   1. 确保Chrome和ChromeDriver版本兼容")
            print("   2. 检查网络连接是否正常")
            print("   3. 确认小红书网站可以正常访问")
        return False

def server_command(action, port=8000, host="0.0.0.0"):
    """服务器管理命令"""
    if action == "start":
        print("🚀 启动MCP服务器...")
        os.environ["FASTMCP_SERVER_PORT"] = str(port)
        os.environ["FASTMCP_SERVER_HOST"] = host
        
        try:
            import xhs_mcp_server
            xhs_mcp_server.main()
        except KeyboardInterrupt:
            print("👋 服务器已停止")
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            
    elif action == "stop":
        print("🛑 正在停止MCP服务器...")
        import subprocess
        import signal
        
        try:
            # 查找MCP服务器进程
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            mcp_processes = []
            for line in result.stdout.split('\n'):
                if 'xhs_mcp_server.py' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        mcp_processes.append(pid)
            
            if not mcp_processes:
                print("❌ 未找到运行中的MCP服务器")
                return
            
            for pid in mcp_processes:
                print(f"🔍 找到MCP服务器进程: {pid}")
                try:
                    # 发送SIGTERM信号
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"📡 已发送停止信号给进程 {pid}")
                    
                    # 等待进程结束
                    import time
                    time.sleep(2)
                    
                    # 检查进程是否还在运行
                    try:
                        os.kill(int(pid), 0)  # 检查进程是否存在
                        print(f"⚠️  进程 {pid} 仍在运行，强制结束...")
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        print(f"✅ 进程 {pid} 已停止")
                        
                except (ValueError, ProcessLookupError) as e:
                    print(f"⚠️  停止进程 {pid} 时出错: {e}")
            
            # 清理可能残留的ChromeDriver进程
            print("🧹 清理ChromeDriver进程...")
            try:
                subprocess.run(["pkill", "-f", "chromedriver"], 
                             capture_output=True, text=True)
            except:
                pass
                
            print("✅ MCP服务器已停止")
            
        except Exception as e:
            print(f"❌ 停止服务器时出错: {e}")
            
    elif action == "status":
        print("🔍 检查MCP服务器状态...")
        import subprocess
        
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            mcp_processes = []
            for line in result.stdout.split('\n'):
                if 'xhs_mcp_server.py' in line and 'grep' not in line:
                    mcp_processes.append(line.strip())
            
            if mcp_processes:
                print(f"✅ 找到 {len(mcp_processes)} 个运行中的MCP服务器:")
                for proc in mcp_processes:
                    parts = proc.split()
                    pid = parts[1] if len(parts) > 1 else "unknown"
                    print(f"   • 进程ID: {pid}")
            else:
                print("❌ 未找到运行中的MCP服务器")
                
        except Exception as e:
            print(f"❌ 检查状态时出错: {e}")
            
    else:
        print(f"❌ 未知的服务器操作: {action}")
        print("💡 可用操作: start, stop, status")

def publish_command(title, content, tags="", location="", images=""):
    """直接发布命令"""
    print(f"📝 发布笔记: {title}")
    
    # 检查服务器是否运行
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=1)
        print("⚠️  检测到MCP服务器正在运行，建议通过MCP客户端发布")
    except:
        print("📱 启动临时发布会话...")
        
        # 导入客户端
        from xhs_mcp_server import XHSConfig, XHSClient, XHSNote
        
        config = XHSConfig()
        client = XHSClient(config)
        
        # 创建笔记对象
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        image_list = [img.strip() for img in images.split(",") if img.strip()] if images else []
        
        note = XHSNote(
            title=title,
            content=content,
            images=image_list if image_list else None,
            tags=tag_list,
            location=location if location else None
        )
        
        # 发布笔记
        import asyncio
        result = asyncio.run(client.publish_note(note))
        print(f"📊 发布结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

def status_command():
    """显示系统状态"""
    print("📊 系统状态检查")
    print("=" * 40)
    
    # 检查Chrome
    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        chrome_exists = os.path.exists(chrome_path)
        print(f"🌐 Chrome浏览器: {'✅ 已安装' if chrome_exists else '❌ 未找到'}")
        if not chrome_exists:
            print(f"   配置路径: {chrome_path}")
    else:
        # 尝试自动检测Chrome
        from cookie_helper import _get_default_chrome_path
        auto_chrome_path = _get_default_chrome_path()
        if auto_chrome_path:
            print(f"🌐 Chrome浏览器: ✅ 自动检测到")
            print(f"   路径: {auto_chrome_path}")
        else:
            print("🌐 Chrome浏览器: ❌ 未找到")
            print("   请在.env文件中配置CHROME_PATH")
    
    # 检查ChromeDriver
    chromedriver_path = os.getenv("WEBDRIVER_CHROME_DRIVER")
    if chromedriver_path:
        chromedriver_exists = os.path.exists(chromedriver_path)
        print(f"🚗 ChromeDriver: {'✅ 已安装' if chromedriver_exists else '❌ 未找到'}")
        if not chromedriver_exists:
            print(f"   配置路径: {chromedriver_path}")
    else:
        # 尝试从PATH中查找
        import shutil
        chromedriver_path = shutil.which("chromedriver")
        if chromedriver_path:
            print(f"🚗 ChromeDriver: ✅ 在PATH中找到")
            print(f"   路径: {chromedriver_path}")
        else:
            print("🚗 ChromeDriver: ❌ 未找到")
            print("   请在.env文件中配置WEBDRIVER_CHROME_DRIVER或添加到PATH")
    
    # 检查Cookies
    cookies_file = Path("xhs/cookies/xiaohongshu_cookies.json")
    cookies_exists = cookies_file.exists()
    print(f"🍪 Cookies文件: {'✅ 存在' if cookies_exists else '❌ 不存在'}")
    
    if cookies_exists:
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            print(f"   数量: {len(cookies)} 个cookies")
            
            # 检查过期时间
            import time
            current_time = time.time()
            expired_count = 0
            for cookie in cookies:
                expiry = cookie.get('expiry')
                if expiry and expiry < current_time:
                    expired_count += 1
            
            if expired_count > 0:
                print(f"   ⚠️  {expired_count} 个cookies已过期")
            else:
                print("   ✅ 所有cookies有效")
                
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
    
    # 检查MCP服务器状态
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=1)
        print("🖥️  MCP服务器: ✅ 正在运行")
    except:
        print("🖥️  MCP服务器: ⏹️  未运行")
    
    # 环境建议
    print("\n💡 环境建议:")
    if not chrome_exists:
        print("   • 请安装Google Chrome浏览器")
    if not chromedriver_exists:
        print("   • 请运行: brew install chromedriver")
    if not cookies_exists:
        print("   • 请运行: python xhs_toolkit.py cookie save")

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env配置文件不存在")
        print("💡 请先创建.env文件:")
        print("   1. cp env_example.txt .env")
        print("   2. 编辑.env文件，填入您的配置")
        print("   3. 必需配置: CHROME_PATH, WEBDRIVER_CHROME_DRIVER")
        return False
    
    print("✅ .env文件存在")
    
    # 检查必需的环境变量
    required_vars = {
        "CHROME_PATH": "Chrome浏览器路径",
        "WEBDRIVER_CHROME_DRIVER": "ChromeDriver路径"
    }
    
    missing_vars = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({desc})")
        elif var in ["CHROME_PATH", "WEBDRIVER_CHROME_DRIVER"] and not os.path.exists(value):
            print(f"❌ {desc}不存在: {value}")
            return False
        else:
            print(f"✅ {desc}: {value}")
    
    if missing_vars:
        print("❌ 缺少必需的环境变量:")
        for var in missing_vars:
            print(f"   • {var}")
        print("💡 请在.env文件中配置这些变量")
        return False
    
    # 检查Cookies目录
    cookies_path = os.getenv("json_path", "./xhs/cookies")
    cookies_file = Path(cookies_path) / "xiaohongshu_cookies.json"
    if not cookies_file.exists():
        print("⚠️  Cookies文件不存在，请先运行: ./xhs-toolkit cookie save")
    else:
        print("✅ Cookies文件存在")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='小红书MCP工具包 - 统一管理cookies和MCP服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python xhs_toolkit.py status                    # 检查系统状态
  python xhs_toolkit.py cookie save               # 获取cookies
  python xhs_toolkit.py cookie validate           # 验证cookies
  python xhs_toolkit.py server start              # 启动MCP服务器
  python xhs_toolkit.py publish "标题" "内容"      # 快速发布笔记
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 状态命令
    subparsers.add_parser('status', help='显示系统状态')
    
    # Cookie相关命令
    cookie_parser = subparsers.add_parser('cookie', help='Cookie管理')
    cookie_parser.add_argument('action', choices=['save', 'show', 'validate'], 
                              help='Cookie操作: save(获取), show(显示), validate(验证)')
    
    # 服务器命令
    server_parser = subparsers.add_parser('server', help='MCP服务器管理')
    server_parser.add_argument('action', choices=['start', 'stop', 'status'], help='服务器操作')
    server_parser.add_argument('--port', default=8000, type=int, help='服务器端口 (默认8000)')
    server_parser.add_argument('--host', default="0.0.0.0", help='服务器主机 (默认0.0.0.0)')
    
    # 发布命令
    publish_parser = subparsers.add_parser('publish', help='快速发布笔记')
    publish_parser.add_argument('title', help='笔记标题')
    publish_parser.add_argument('content', help='笔记内容')
    publish_parser.add_argument('--tags', default="", help='标签 (逗号分隔)')
    publish_parser.add_argument('--location', default="", help='位置信息')
    publish_parser.add_argument('--images', default="", help='图片路径 (逗号分隔)')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        print_banner()
        parser.print_help()
        return
    
    print_banner()
    
    try:
        if args.command == 'status':
            status_command()
        elif args.command == 'cookie':
            cookie_command(args.action)
        elif args.command == 'server':
            server_command(args.action, args.port, args.host)
        elif args.command == 'publish':
            publish_command(args.title, args.content, args.tags, args.location, args.images)
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 