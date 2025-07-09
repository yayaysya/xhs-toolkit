"""
Playwright 浏览器管理模块
"""
from __future__ import annotations
import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser as PlaywrightBrowser,
    BrowserContext,
    Page
)
from .config import XHSConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Browser:
    """一个Playwright浏览器的封装类"""

    def __init__(self, browser: PlaywrightBrowser, context: BrowserContext):
        self.browser = browser
        self.context = context

    @classmethod
    async def create(
        cls,
        config: XHSConfig,
        proxy: Optional[Dict[str, str]] = None,
        cookies: Optional[List[Dict]] = None
    ) -> Browser:
        """创建一个新的浏览器实例"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=config.headless,
            proxy=proxy
        )
        context = await browser.new_context(
            user_agent=config.user_agent
        )
        if cookies:
            await context.add_cookies(cookies)
        return cls(browser, context)

    async def new_page(self) -> Page:
        """创建一个新的页面"""
        return await self.context.new_page()

    async def close(self) -> None:
        """关闭浏览器"""
        await self.context.close()
        await self.browser.close()
        # 正常关闭playwright
        try:
            playwright = self.browser.playwright
            if playwright.is_connected():
                 await playwright.stop()
        except Exception as e:
            logger.debug(f"关闭Playwright时出错: {e}")


_browser_config: Optional[XHSConfig] = None

def get_browser_config() -> XHSConfig:
    global _browser_config
    if _browser_config is None:
        _browser_config = XHSConfig()
    return _browser_config

def get_playwright_proxy(proxy_str: Optional[str]) -> Optional[Dict]:
    if not proxy_str:
        return None
    # 简单的http/https代理格式
    return {"server": proxy_str} 