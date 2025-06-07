"""
小红书Cookie管理模块

负责Cookie的获取、保存、加载和验证功能
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.config import XHSConfig
from ..core.browser import ChromeDriverManager
from ..core.exceptions import AuthenticationError, handle_exception
from ..xiaohongshu.models import CRITICAL_CREATOR_COOKIES
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CookieManager:
    """Cookie管理器"""
    
    def __init__(self, config: XHSConfig):
        """
        初始化Cookie管理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.browser_manager = ChromeDriverManager(config)
    
    @handle_exception
    def save_cookies_interactive(self) -> bool:
        """
        交互式保存cookies - 支持创作者中心
        
        Returns:
            是否成功保存cookies
            
        Raises:
            AuthenticationError: 当保存过程出错时
        """
        logger.info("🌺 开始获取小红书创作者中心Cookies...")
        logger.info("📝 注意：将直接跳转到创作者登录页面，确保获取完整的创作者权限cookies")
        
        try:
            # 创建浏览器驱动
            driver = self.browser_manager.create_driver()
            
            # 导航到创作者中心
            self.browser_manager.navigate_to_creator_center()
            
            logger.info("\n📋 请按照以下步骤操作:")
            logger.info("1. 在浏览器中手动登录小红书创作者中心")
            logger.info("2. 登录成功后，确保能正常访问创作者中心功能")
            logger.info("3. 建议点击进入【发布笔记】页面，确认权限完整")
            logger.info("4. 完成后，在此终端中按 Enter 键继续...")
            
            input()  # 等待用户输入
            
            logger.info("🍪 开始获取cookies...")
            cookies = driver.get_cookies()
            
            if not cookies:
                raise AuthenticationError("未获取到cookies，请确保已正确登录", auth_type="cookie_save")
            
            # 验证关键创作者cookies
            validation_result = self._validate_critical_cookies(cookies)
            
            # 保存cookies
            save_result = self._save_cookies_to_file(cookies, validation_result)
            
            if save_result:
                logger.info("\n🎉 Cookies获取成功！")
                logger.info("💡 现在可以正常访问创作者中心功能了")
                return True
            else:
                raise AuthenticationError("Cookies保存失败", auth_type="cookie_save")
            
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            else:
                raise AuthenticationError(f"获取cookies过程出错: {str(e)}", auth_type="cookie_save") from e
        finally:
            # 确保浏览器被关闭
            self.browser_manager.close_driver()
    
    def _validate_critical_cookies(self, cookies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证关键创作者cookies
        
        Args:
            cookies: Cookie列表
            
        Returns:
            验证结果字典
        """
        logger.info("🔍 验证关键创作者cookies...")
        
        found_critical = []
        for cookie in cookies:
            if cookie.get('name') in CRITICAL_CREATOR_COOKIES:
                found_critical.append(cookie.get('name'))
        
        logger.info(f"✅ 找到关键创作者cookies: {found_critical}")
        
        missing_critical = set(CRITICAL_CREATOR_COOKIES[:4]) - set(found_critical)  # 检查前4个基础cookies
        if missing_critical:
            logger.warning(f"⚠️ 缺少关键cookies: {missing_critical}")
            logger.warning("💡 建议确认是否已完整登录创作者中心")
        
        return {
            "found_critical": found_critical,
            "missing_critical": list(missing_critical),
            "total_cookies": len(cookies)
        }
    
    def _save_cookies_to_file(self, cookies: List[Dict[str, Any]], validation_result: Dict[str, Any]) -> bool:
        """
        保存cookies到文件
        
        Args:
            cookies: Cookie列表
            validation_result: 验证结果
            
        Returns:
            是否保存成功
        """
        try:
            # 创建cookies目录
            cookies_dir = Path(self.config.cookies_dir)
            cookies_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建新格式的cookies数据
            cookies_data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'domain': 'creator.xiaohongshu.com',  # 标记为创作者中心cookies
                'critical_cookies_found': validation_result["found_critical"],
                'version': '2.0'  # 版本标记
            }
            
            # 保存cookies
            cookies_file = Path(self.config.cookies_file)
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Cookies已保存到: {cookies_file}")
            logger.info(f"📊 共保存了 {len(cookies)} 个cookies")
            logger.info(f"🔑 关键创作者cookies: {len(validation_result['found_critical'])}/{len(CRITICAL_CREATOR_COOKIES)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存cookies失败: {e}")
            return False
    
    @handle_exception
    def load_cookies(self) -> List[Dict[str, Any]]:
        """
        加载cookies - 支持新旧格式兼容
        
        Returns:
            Cookie列表
            
        Raises:
            AuthenticationError: 当加载失败时
        """
        cookies_file = Path(self.config.cookies_file)
        
        if not cookies_file.exists():
            logger.warning(f"Cookies文件不存在: {cookies_file}")
            return []
        
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # 兼容新旧格式
            if isinstance(cookies_data, list):
                # 旧格式：直接是cookies列表
                cookies = cookies_data
                logger.debug("检测到旧版本cookies格式")
            else:
                # 新格式：包含元数据
                cookies = cookies_data.get('cookies', [])
                version = cookies_data.get('version', '1.0')
                domain = cookies_data.get('domain', 'unknown')
                logger.debug(f"检测到新版本cookies格式，版本: {version}, 域名: {domain}")
            
            logger.debug(f"成功加载 {len(cookies)} 个cookies")
            return cookies
            
        except Exception as e:
            raise AuthenticationError(f"加载cookies失败: {str(e)}", auth_type="cookie_load") from e
    
    def display_cookies_info(self) -> None:
        """显示当前cookies信息"""
        cookies_file = Path(self.config.cookies_file)
        
        if not cookies_file.exists():
            logger.warning("❌ Cookies文件不存在")
            return
        
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # 兼容新旧格式
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
            
            # 显示关键创作者cookies状态
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
                        exp_date = datetime.fromtimestamp(expires)
                        expires = exp_date.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                # 标记关键cookies
                critical_mark = "🔑" if name in CRITICAL_CREATOR_COOKIES else "  "
                print(f"{critical_mark}{i:2d}. {name:35s} | {domain:25s} | 过期: {expires}")
            
        except Exception as e:
            logger.error(f"❌ 读取cookies失败: {e}")
    
    @handle_exception
    def validate_cookies(self) -> bool:
        """
        验证cookies是否有效
        
        Returns:
            cookies是否有效
            
        Raises:
            AuthenticationError: 当验证过程出错时
        """
        cookies_file = Path(self.config.cookies_file)
        
        if not cookies_file.exists():
            logger.warning("❌ Cookies文件不存在")
            return False
        
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # 兼容新旧格式
            if isinstance(cookies_data, list):
                cookies = cookies_data
                logger.warning("⚠️ 检测到旧版本cookies，建议重新获取")
            else:
                cookies = cookies_data.get('cookies', [])
                version = cookies_data.get('version', '1.0')
                logger.info(f"📦 Cookies版本: {version}")
            
            logger.info("🔍 验证cookies...")
            
            # 检查关键创作者cookies
            found_cookies = []
            for cookie in cookies:
                if cookie.get('name') in CRITICAL_CREATOR_COOKIES:
                    found_cookies.append(cookie.get('name'))
            
            logger.info(f"✅ 找到关键创作者cookies: {found_cookies}")
            
            missing = set(CRITICAL_CREATOR_COOKIES[:4]) - set(found_cookies)  # 检查基础cookies
            if missing:
                logger.warning(f"⚠️ 缺少重要cookies: {list(missing)}")
                logger.warning("💡 这可能导致创作者中心访问失败")
            
            # 检查过期时间
            current_time = time.time()
            expired_cookies = []
            
            for cookie in cookies:
                expiry = cookie.get('expiry')
                if expiry and expiry < current_time:
                    expired_cookies.append(cookie.get('name'))
            
            if expired_cookies:
                logger.warning(f"⚠️ 已过期的cookies: {expired_cookies}")
            else:
                logger.info("✅ 所有cookies都未过期")
            
            # 综合评估
            is_valid = len(missing) <= 1 and len(expired_cookies) == 0  # 允许缺少1个非关键cookie
            
            if is_valid:
                logger.info("✅ Cookies验证通过，应该可以正常访问创作者中心")
            else:
                logger.warning("❌ Cookies验证失败，建议重新获取")
                logger.info("💡 运行命令: python xhs_toolkit.py cookie save")
            
            return is_valid
            
        except Exception as e:
            raise AuthenticationError(f"验证cookies失败: {str(e)}", auth_type="cookie_validate") from e
    
    @handle_exception
    def test_chromedriver_config(self) -> bool:
        """
        测试ChromeDriver配置是否正确
        
        Returns:
            测试是否通过
            
        Raises:
            AuthenticationError: 当测试失败时
        """
        logger.info("🔧 开始测试ChromeDriver配置...")
        
        try:
            driver = self.browser_manager.create_driver()
            logger.info("🌐 正在访问测试页面...")
            
            driver.get("https://www.google.com")
            title = driver.title
            logger.info(f"📄 页面标题: {title}")
            
            if "Google" in title:
                logger.info("✅ ChromeDriver配置测试成功！")
                result = True
            else:
                logger.warning("⚠️ 页面加载异常，请检查网络连接")
                result = False
                
            return result
            
        except Exception as e:
            raise AuthenticationError(f"ChromeDriver配置测试失败: {str(e)}", auth_type="chromedriver_test") from e
        finally:
            # 确保浏览器被关闭
            self.browser_manager.close_driver()


# 便捷函数
def create_cookie_manager(config: XHSConfig) -> CookieManager:
    """
    创建Cookie管理器的便捷函数
    
    Args:
        config: 配置管理器实例
        
    Returns:
        Cookie管理器实例
    """
    return CookieManager(config) 