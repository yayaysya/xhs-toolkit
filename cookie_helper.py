#!/usr/bin/env python3
"""
小红书Cookies助手工具

这个工具帮助用户更容易地获取和管理小红书的cookies
支持创作者中心cookies获取，解决跳转失效问题
"""

import json
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from datetime import datetime
import shutil

# 加载环境变量配置
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

# 创作者中心特有的关键cookies
CRITICAL_CREATOR_COOKIES = [
    'web_session', 'a1', 'gid', 'webId', 
    'customer-sso-sid', 'x-user-id-creator.xiaohongshu.com',
    'access-token-creator.xiaohongshu.com', 'galaxy_creator_session_id',
    'galaxy.creator.beaker.session.id'
]

def get_chrome_driver():
    """获取Chrome驱动，兼容Windows、Mac、Linux三端"""
    
    # 从环境变量获取ChromeDriver路径
    chromedriver_path = os.getenv("WEBDRIVER_CHROME_DRIVER")
    
    # 如果环境变量中没有配置，则尝试从PATH中查找
    if not chromedriver_path:
        chromedriver_path = shutil.which("chromedriver")
    
    # 从环境变量获取Chrome浏览器路径（可选）
    chrome_path = os.getenv("CHROME_PATH")
    
    # 如果没有指定Chrome路径，使用默认查找逻辑
    if not chrome_path:
        chrome_path = _get_default_chrome_path()
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # 设置Chrome二进制文件路径（如果配置了）
    if chrome_path and os.path.exists(chrome_path):
        chrome_options.binary_location = chrome_path
    
    try:
        if chromedriver_path and os.path.exists(chromedriver_path):
            # 使用指定的ChromeDriver路径
            service = Service(chromedriver_path)
            print(f"🔧 使用ChromeDriver: {chromedriver_path}")
        else:
            # 尝试使用系统PATH中的ChromeDriver
            service = Service()
            print("🔧 使用系统PATH中的ChromeDriver")
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome驱动启动成功")
        return driver
        
    except Exception as e:
        print(f"❌ Chrome驱动启动失败: {e}")
        print("\n📖 解决方案：")
        print("1. 检查ChromeDriver是否已安装并配置到PATH")
        print("2. 或在.env文件中配置WEBDRIVER_CHROME_DRIVER路径")
        print("3. 参考 ChromeDriver安装指南.md 进行配置")
        print("\n💡 .env文件配置示例：")
        print("# Windows:")
        print("# WEBDRIVER_CHROME_DRIVER=C:\\chromedriver\\chromedriver.exe")
        print("# CHROME_PATH=C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        print("\n# Mac:")
        print("# WEBDRIVER_CHROME_DRIVER=/usr/local/bin/chromedriver")
        print("# CHROME_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        print("\n# Linux:")
        print("# WEBDRIVER_CHROME_DRIVER=/usr/local/bin/chromedriver")
        print("# CHROME_PATH=/usr/bin/google-chrome")
        raise

def _get_default_chrome_path():
    """获取默认Chrome浏览器路径（跨平台）"""
    import platform
    
    system = platform.system().lower()
    
    # 常见的Chrome安装路径
    chrome_paths = []
    
    if system == "windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]
    
    # 检查路径是否存在
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    # 如果都找不到，返回None，让Selenium自动检测
    return None

def save_cookies_interactive():
    """交互式保存cookies - 改进版本，支持创作者中心"""
    print("🌺 小红书Cookies获取工具（创作者中心版）")
    print("=" * 50)
    
    try:
        print("🚀 启动Chrome浏览器...")
        driver = get_chrome_driver()
        
        if driver is None:
            return False
        
        print("🌐 导航到小红书创作者中心...")
        print("📝 注意：将直接跳转到创作者登录页面，确保获取完整的创作者权限cookies")
        
        # **核心修复**：直接访问创作者中心，获取完整权限cookies
        driver.get("https://creator.xiaohongshu.com")
        time.sleep(3)  # 等待页面加载
        
        print("\n📋 请按照以下步骤操作:")
        print("1. 在浏览器中手动登录小红书创作者中心")
        print("2. 登录成功后，确保能正常访问创作者中心功能")
        print("3. 建议点击进入【发布笔记】页面，确认权限完整")
        print("4. 完成后，在此终端中按 Enter 键继续...")
        
        input()  # 等待用户输入
        
        print("🍪 获取cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ 未获取到cookies，请确保已正确登录")
            return False
        
        # **改进的cookies验证**
        print("🔍 验证关键创作者cookies...")
        found_critical = []
        for cookie in cookies:
            if cookie.get('name') in CRITICAL_CREATOR_COOKIES:
                found_critical.append(cookie.get('name'))
        
        print(f"✅ 找到关键创作者cookies: {found_critical}")
        
        missing_critical = set(CRITICAL_CREATOR_COOKIES[:4]) - set(found_critical)  # 检查前4个基础cookies
        if missing_critical:
            print(f"⚠️ 缺少关键cookies: {missing_critical}")
            print("💡 建议确认是否已完整登录创作者中心")
        
        # 创建cookies目录
        cookies_dir = Path("xhs/cookies")
        cookies_dir.mkdir(parents=True, exist_ok=True)
        
        # **改进的cookies保存格式**
        cookies_data = {
            'cookies': cookies,
            'saved_at': datetime.now().isoformat(),
            'domain': 'creator.xiaohongshu.com',  # 标记为创作者中心cookies
            'critical_cookies_found': found_critical,
            'version': '2.0'  # 版本标记
        }
        
        # 保存cookies
        cookies_file = cookies_dir / "xiaohongshu_cookies.json"
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Cookies已保存到: {cookies_file}")
        print(f"📊 共保存了 {len(cookies)} 个cookies")
        print(f"🔑 关键创作者cookies: {len(found_critical)}/{len(CRITICAL_CREATOR_COOKIES)}")
        
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
            cookies_data = json.load(f)
        
        # **兼容新旧格式**
        if isinstance(cookies_data, list):
            # 旧格式：直接是cookies列表
            cookies = cookies_data
            saved_at = "未知"
            domain = "未知"
            version = "1.0"
        else:
            # 新格式：包含元数据
            cookies = cookies_data.get('cookies', [])
            saved_at = cookies_data.get('saved_at', '未知')
            domain = cookies_data.get('domain', '未知')
            version = cookies_data.get('version', '1.0')
        
        print(f"🍪 Cookies信息 ({cookies_file})")
        print("=" * 60)
        print(f"📊 总数量: {len(cookies)}")
        print(f"💾 保存时间: {saved_at}")
        print(f"🌐 域名: {domain}")
        print(f"📦 版本: {version}")
        
        # **显示关键创作者cookies状态**
        if version != "1.0":
            print("\n🔑 关键创作者cookies状态:")
            found_critical = []
            for cookie in cookies:
                if cookie.get('name') in CRITICAL_CREATOR_COOKIES:
                    found_critical.append(cookie.get('name'))
                    print(f"  ✅ {cookie.get('name')}")
            
            missing = set(CRITICAL_CREATOR_COOKIES) - set(found_critical)
            for missing_cookie in missing:
                print(f"  ❌ {missing_cookie} (缺失)")
        
        print("\n📋 所有Cookies列表:")
        
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
            
            # 标记关键cookies
            critical_mark = "🔑" if name in CRITICAL_CREATOR_COOKIES else "  "
            print(f"{critical_mark}{i:2d}. {name:35s} | {domain:25s} | 过期: {expires}")
        
    except Exception as e:
        print(f"❌ 读取cookies失败: {e}")

def validate_cookies():
    """验证cookies是否有效 - 改进版本"""
    cookies_file = Path("xhs/cookies/xiaohongshu_cookies.json")
    
    if not cookies_file.exists():
        print("❌ Cookies文件不存在")
        return False
    
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        # 兼容新旧格式
        if isinstance(cookies_data, list):
            cookies = cookies_data
            print("⚠️ 检测到旧版本cookies，建议重新获取")
        else:
            cookies = cookies_data.get('cookies', [])
            version = cookies_data.get('version', '1.0')
            print(f"📦 Cookies版本: {version}")
        
        print("🔍 验证cookies...")
        
        # **改进的验证逻辑：检查创作者关键cookies**
        found_cookies = []
        for cookie in cookies:
            if cookie.get('name') in CRITICAL_CREATOR_COOKIES:
                found_cookies.append(cookie.get('name'))
        
        print(f"✅ 找到关键创作者cookies: {found_cookies}")
        
        missing = set(CRITICAL_CREATOR_COOKIES[:4]) - set(found_cookies)  # 检查基础cookies
        if missing:
            print(f"⚠️ 缺少重要cookies: {list(missing)}")
            print("💡 这可能导致创作者中心访问失败")
        
        # 检查过期时间
        import time
        current_time = time.time()
        expired_cookies = []
        
        for cookie in cookies:
            expiry = cookie.get('expiry')
            if expiry and expiry < current_time:
                expired_cookies.append(cookie.get('name'))
        
        if expired_cookies:
            print(f"⚠️ 已过期的cookies: {expired_cookies}")
        else:
            print("✅ 所有cookies都未过期")
        
        # **综合评估**
        is_valid = len(missing) <= 1 and len(expired_cookies) == 0  # 允许缺少1个非关键cookie
        
        if is_valid:
            print("✅ Cookies验证通过，应该可以正常访问创作者中心")
        else:
            print("❌ Cookies验证失败，建议重新获取")
            print("💡 运行命令: python cookie_helper.py save")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ 验证cookies失败: {e}")
        return False

def test_chromedriver_config():
    """测试ChromeDriver配置是否正确"""
    print("🔧 开始测试ChromeDriver配置...")
    
    try:
        driver = get_chrome_driver()
        print("🌐 正在访问测试页面...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"📄 页面标题: {title}")
        
        if "Google" in title:
            print("✅ ChromeDriver配置测试成功！")
            result = True
        else:
            print("⚠️ 页面加载异常，请检查网络连接")
            result = False
            
        driver.quit()
        return result
        
    except Exception as e:
        print(f"❌ ChromeDriver配置测试失败: {e}")
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
        print("  python cookie_helper.py test     - 测试ChromeDriver配置")
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
    elif command == "test":
        if test_chromedriver_config():
            print("✅ ChromeDriver配置正常")
        else:
            print("❌ ChromeDriver配置有问题")
    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: save, show, validate, test")

if __name__ == "__main__":
    main() 