"""
小红书客户端模块

负责与小红书平台的交互，包括笔记发布、搜索、用户信息获取等功能
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..core.config import XHSConfig
from ..core.browser import ChromeDriverManager
from ..core.exceptions import PublishError, NetworkError, handle_exception
from ..auth.cookie_manager import CookieManager
from ..utils.text_utils import clean_text_for_browser, truncate_text
from ..utils.logger import get_logger
from .models import XHSNote, XHSSearchResult, XHSUser, XHSPublishResult

logger = get_logger(__name__)


class XHSClient:
    """小红书客户端类"""
    
    def __init__(self, config: XHSConfig):
        """
        初始化小红书客户端
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.browser_manager = ChromeDriverManager(config)
        self.cookie_manager = CookieManager(config)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self) -> None:
        """设置requests会话"""
        try:
            cookies = self.cookie_manager.load_cookies()
            if cookies:
                for cookie in cookies:
                    self.session.cookies.set(
                        name=cookie['name'],
                        value=cookie['value'],
                        domain=cookie['domain']
                    )
                logger.debug(f"已设置 {len(cookies)} 个cookies到会话")
        except Exception as e:
            logger.warning(f"设置会话cookies失败: {e}")
    
    @handle_exception
    async def publish_note(self, note: XHSNote) -> XHSPublishResult:
        """
        发布小红书笔记
        
        Args:
            note: 笔记对象
            
        Returns:
            发布结果
            
        Raises:
            PublishError: 当发布过程出错时
        """
        logger.info(f"📝 开始发布小红书笔记: {note.title}")
        
        try:
            # 创建浏览器驱动
            driver = self.browser_manager.create_driver()
            
            # 导航到创作者中心
            self.browser_manager.navigate_to_creator_center()
            
            # 加载cookies
            cookies = self.cookie_manager.load_cookies()
            cookie_result = self.browser_manager.load_cookies(cookies)
            
            logger.info(f"🍪 Cookies加载结果: {cookie_result}")
            
            # 访问发布页面
            return await self._publish_note_process(note)
            
        except Exception as e:
            if isinstance(e, PublishError):
                raise
            else:
                raise PublishError(f"发布笔记过程出错: {str(e)}", publish_step="初始化") from e
        finally:
            # 确保浏览器被关闭
            self.browser_manager.close_driver()
    
    async def _publish_note_process(self, note: XHSNote) -> XHSPublishResult:
        """执行发布笔记的具体流程"""
        driver = self.browser_manager.driver
        
        try:
            logger.info("🌐 直接访问小红书发布页面...")
            driver.get("https://creator.xiaohongshu.com/publish/publish?from=menu")
            await asyncio.sleep(3)
            
            if "publish" not in driver.current_url:
                raise PublishError("无法访问发布页面，可能需要重新登录", publish_step="页面访问")
            
            # 处理图片上传
            await self._handle_image_upload(note)
            
            # 填写笔记内容
            await self._fill_note_content(note)
            
            # 发布笔记
            return await self._submit_note(note)
            
        except Exception as e:
            self.browser_manager.take_screenshot("publish_error_screenshot.png")
            if isinstance(e, PublishError):
                raise
            else:
                raise PublishError(f"发布流程执行失败: {str(e)}", publish_step="流程执行") from e
    
    async def _handle_image_upload(self, note: XHSNote) -> None:
        """处理图片上传"""
        try:
            driver = self.browser_manager.driver
            
            if note.images:
                upload_input = driver.find_element(By.CSS_SELECTOR, ".upload-input")
                logger.info(f"📸 准备上传 {len(note.images)} 张图片...")
                upload_input.send_keys('\n'.join(note.images))
                await asyncio.sleep(1)
                logger.info("✅ 图片上传指令已发送")
                    
        except Exception as e:
            logger.warning(f"⚠️ 处理上传区域时出错: {e}")
    
    async def _fill_note_content(self, note: XHSNote) -> None:
        """填写笔记内容"""
        driver = self.browser_manager.driver
        wait = WebDriverWait(driver, 15)
        
        await asyncio.sleep(1)
        
        # 填写标题
        try:
            logger.info("✏️ 填写标题...")
            title = clean_text_for_browser(truncate_text(note.title, 20))
            title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".d-text")))
            title_input.send_keys(title)
            logger.info(f"✅ 标题已填写: {title}")
        except Exception as e:
            raise PublishError(f"填写标题失败: {str(e)}", publish_step="填写标题") from e
        
        # 填写内容
        try:
            logger.info("📝 填写内容...")
            content_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor")))
            content_input.send_keys(clean_text_for_browser(note.content))
            logger.info("✅ 内容已填写")
        except Exception as e:
            raise PublishError(f"填写内容失败: {str(e)}", publish_step="填写内容") from e
        
        await asyncio.sleep(2)
    
    async def _submit_note(self, note: XHSNote) -> XHSPublishResult:
        """提交发布笔记"""
        driver = self.browser_manager.driver
        
        try:
            logger.info("🚀 点击发布按钮...")
            submit_btn = driver.find_element(By.CSS_SELECTOR, ".publishBtn")
            submit_btn.click()
            logger.info("✅ 发布按钮已点击")
            await asyncio.sleep(3)
            
            current_url = driver.current_url
            logger.info(f"📍 发布后页面URL: {current_url}")
            
            return XHSPublishResult(
                success=True,
                message=f"笔记发布成功！标题: {note.title}",
                note_title=note.title,
                final_url=current_url
            )
            
        except Exception as e:
            raise PublishError(f"点击发布按钮失败: {str(e)}", publish_step="提交发布") from e


# 便捷函数
def create_xhs_client(config: XHSConfig) -> XHSClient:
    """
    创建小红书客户端的便捷函数
    
    Args:
        config: 配置管理器实例
        
    Returns:
        小红书客户端实例
    """
    return XHSClient(config) 