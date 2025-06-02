#!/usr/bin/env python3
"""
小红书Cookies助手工具

这个工具帮助用户更容易地获取和管理小红书的cookies
"""

import json
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

# 加载环境变量配置
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

def get_chrome_driver():
    """获取Chrome驱动"""
    chrome_path = os.getenv("CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    chromedriver_path = os.getenv("WEBDRIVER_CHROME_DRIVER", "/opt/homebrew/bin/chromedriver")
    
    # 检查chromedriver是否存在
    if not os.path.exists(chromedriver_path):
        print(f"❌ ChromeDriver未找到: {chromedriver_path}")
        print("💡 请确保已安装ChromeDriver:")
        print("   brew install chromedriver")
        print("   或者设置环境变量 WEBDRIVER_CHROME_DRIVER 指向正确路径")
        return None
    
    # 检查Chrome浏览器是否存在
    if not os.path.exists(chrome_path):
        print(f"❌ Chrome浏览器未找到: {chrome_path}")
        print("💡 请确保已安装Google Chrome浏览器")
        print("   或者设置环境变量 CHROME_PATH 指向正确路径")
        return None
    
    chrome_options = Options()
    chrome_options.binary_location = chrome_path
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # 使用Service对象替代executable_path
        service = Service(executable_path=chromedriver_path)
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"❌ 创建Chrome驱动失败: {e}")
        print("💡 可能的解决方案:")
        print("   1. 确保ChromeDriver版本与Chrome浏览器版本兼容")
        print("   2. 运行: brew install --cask chromedriver")
        print("   3. 如果遇到权限问题，运行: xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver")
        return None

def save_cookies_interactive():
    """交互式保存cookies"""
    print("🌺 小红书Cookies获取工具")
    print("=" * 40)
    
    try:
        print("🚀 启动Chrome浏览器...")
        driver = get_chrome_driver()
        
        if driver is None:
            return False
        
        print("🌐 导航到小红书登录页面...")
        driver.get("https://www.xiaohongshu.com")
        
        print("\n📋 请按照以下步骤操作:")
        print("1. 在浏览器中手动登录小红书")
        print("2. 登录成功后，确保可以正常访问小红书内容")
        print("3. 完成后，在此终端中按 Enter 键继续...")
        
        input()  # 等待用户输入
        
        print("🍪 获取cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ 未获取到cookies，请确保已正确登录")
            return False
        
        # 创建cookies目录
        cookies_dir = Path("xhs/cookies")
        cookies_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存cookies
        cookies_file = cookies_dir / "xiaohongshu_cookies.json"
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Cookies已保存到: {cookies_file}")
        print(f"📊 共保存了 {len(cookies)} 个cookies")
        
        # 验证cookies
        print("🔍 验证cookies...")
        valid_cookies = []
        for cookie in cookies:
            if cookie.get('name') and cookie.get('value'):
                valid_cookies.append(cookie)
        
        print(f"✅ 有效cookies数量: {len(valid_cookies)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 获取cookies失败: {e}")
        return False
    finally:
        if 'driver' in locals() and driver is not None:
            driver.quit()

def load_and_display_cookies():
    """加载并显示当前cookies"""
    cookies_file = Path("xhs/cookies/xiaohongshu_cookies.json")
    
    if not cookies_file.exists():
        print("❌ Cookies文件不存在")
        return
    
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"🍪 Cookies信息 ({cookies_file})")
        print("=" * 50)
        print(f"📊 总数量: {len(cookies)}")
        print("\n📋 Cookies列表:")
        
        for i, cookie in enumerate(cookies, 1):
            name = cookie.get('name', 'N/A')
            domain = cookie.get('domain', 'N/A')
            expires = cookie.get('expiry', 'N/A')
            
            if expires != 'N/A':
                try:
                    import datetime
                    exp_date = datetime.datetime.fromtimestamp(expires)
                    expires = exp_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"  {i:2d}. {name:25s} | {domain:20s} | 过期: {expires}")
        
    except Exception as e:
        print(f"❌ 读取cookies失败: {e}")

def validate_cookies():
    """验证cookies是否有效"""
    cookies_file = Path("xhs/cookies/xiaohongshu_cookies.json")
    
    if not cookies_file.exists():
        print("❌ Cookies文件不存在")
        return False
    
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print("🔍 验证cookies...")
        
        # 检查必要的cookies
        required_cookies = ['customerClientId', 'webId', 'a1']
        found_cookies = []
        
        for cookie in cookies:
            if cookie.get('name') in required_cookies:
                found_cookies.append(cookie.get('name'))
        
        print(f"✅ 找到必要cookies: {found_cookies}")
        
        missing = set(required_cookies) - set(found_cookies)
        if missing:
            print(f"⚠️  缺少cookies: {list(missing)}")
        
        # 检查过期时间
        import time
        current_time = time.time()
        expired_cookies = []
        
        for cookie in cookies:
            expiry = cookie.get('expiry')
            if expiry and expiry < current_time:
                expired_cookies.append(cookie.get('name'))
        
        if expired_cookies:
            print(f"⚠️  已过期的cookies: {expired_cookies}")
        else:
            print("✅ 所有cookies都未过期")
        
        return len(missing) == 0 and len(expired_cookies) == 0
        
    except Exception as e:
        print(f"❌ 验证cookies失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🌺 小红书Cookies助手工具")
        print("=" * 30)
        print("使用方法:")
        print("  python cookie_helper.py save     - 获取并保存cookies")
        print("  python cookie_helper.py show     - 显示当前cookies")
        print("  python cookie_helper.py validate - 验证cookies有效性")
        return
    
    command = sys.argv[1].lower()
    
    if command == "save":
        save_cookies_interactive()
    elif command == "show":
        load_and_display_cookies()
    elif command == "validate":
        if validate_cookies():
            print("✅ Cookies验证通过")
        else:
            print("❌ Cookies验证失败")
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main() 