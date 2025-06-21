"""
小红书内容填写器

专门负责标题、内容、标签等文本内容的填写，遵循单一职责原则
"""

import asyncio
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from ..interfaces import IContentFiller, IBrowserManager
from ..constants import (XHSConfig, XHSSelectors, get_title_input_selectors)
from ...core.exceptions import PublishError, handle_exception
from ...utils.logger import get_logger
from ...utils.text_utils import clean_text_for_browser

logger = get_logger(__name__)


class XHSContentFiller(IContentFiller):
    """小红书内容填写器"""
    
    def __init__(self, browser_manager: IBrowserManager):
        """
        初始化内容填写器
        
        Args:
            browser_manager: 浏览器管理器
        """
        self.browser_manager = browser_manager
    
    @handle_exception
    async def fill_title(self, title: str) -> bool:
        """
        填写标题
        
        Args:
            title: 标题内容
            
        Returns:
            填写是否成功
        """
        logger.info(f"📝 开始填写标题: {title}")
        
        try:
            # 验证标题
            self._validate_title(title)
            
            # 查找标题输入框
            title_input = await self._find_title_input()
            if not title_input:
                raise PublishError("未找到标题输入框", publish_step="标题填写")
            
            # 执行标题填写
            return await self._perform_title_fill(title_input, title)
            
        except Exception as e:
            if isinstance(e, PublishError):
                raise
            else:
                logger.error(f"❌ 标题填写失败: {e}")
                return False
    
    @handle_exception
    async def fill_content(self, content: str) -> bool:
        """
        填写内容
        
        Args:
            content: 笔记内容
            
        Returns:
            填写是否成功
        """
        logger.info(f"📝 开始填写内容: {content[:50]}...")
        
        try:
            # 验证内容
            self._validate_content(content)
            
            # 查找内容编辑器
            content_editor = await self._find_content_editor()
            if not content_editor:
                raise PublishError("未找到内容编辑器", publish_step="内容填写")
            
            # 执行内容填写
            return await self._perform_content_fill(content_editor, content)
            
        except Exception as e:
            if isinstance(e, PublishError):
                raise
            else:
                logger.error(f"❌ 内容填写失败: {e}")
                return False
    
    @handle_exception
    async def fill_tags(self, tags: List[str]) -> bool:
        """
        填写标签
        
        Args:
            tags: 标签列表
            
        Returns:
            填写是否成功
        """
        logger.info(f"🏷️ 开始填写标签: {tags}")
        
        try:
            # 验证标签
            self._validate_tags(tags)
            
            # 小红书的标签通常集成在内容中，使用#符号
            # 这里实现一个简单的标签处理逻辑
            return await self._perform_tags_fill(tags)
            
        except Exception as e:
            logger.warning(f"⚠️ 标签填写失败: {e}")
            return False  # 标签填写失败不影响主流程
    
    def _validate_title(self, title: str) -> None:
        """
        验证标题
        
        Args:
            title: 标题内容
            
        Raises:
            PublishError: 当标题验证失败时
        """
        if not title or not title.strip():
            raise PublishError("标题不能为空", publish_step="标题验证")
        
        if len(title.strip()) > XHSConfig.MAX_TITLE_LENGTH:
            raise PublishError(f"标题长度超限，最多{XHSConfig.MAX_TITLE_LENGTH}个字符", 
                             publish_step="标题验证")
    
    def _validate_content(self, content: str) -> None:
        """
        验证内容
        
        Args:
            content: 笔记内容
            
        Raises:
            PublishError: 当内容验证失败时
        """
        if not content or not content.strip():
            raise PublishError("内容不能为空", publish_step="内容验证")
        
        if len(content.strip()) > XHSConfig.MAX_CONTENT_LENGTH:
            raise PublishError(f"内容长度超限，最多{XHSConfig.MAX_CONTENT_LENGTH}个字符", 
                             publish_step="内容验证")
    
    def _validate_tags(self, tags: List[str]) -> None:
        """
        验证标签
        
        Args:
            tags: 标签列表
            
        Raises:
            PublishError: 当标签验证失败时
        """
        if len(tags) > XHSConfig.MAX_TAGS:
            raise PublishError(f"标签数量超限，最多{XHSConfig.MAX_TAGS}个", 
                             publish_step="标签验证")
        
        for tag in tags:
            if len(tag) > XHSConfig.MAX_TAG_LENGTH:
                raise PublishError(f"标签长度超限: {tag}，最多{XHSConfig.MAX_TAG_LENGTH}个字符", 
                                 publish_step="标签验证")
    
    async def _find_title_input(self):
        """
        查找标题输入框
        
        Returns:
            标题输入元素，如果未找到返回None
        """
        driver = self.browser_manager.driver
        wait = WebDriverWait(driver, XHSConfig.DEFAULT_WAIT_TIME)
        
        # 尝试多个选择器
        for selector in get_title_input_selectors():
            try:
                logger.debug(f"🔍 尝试标题选择器: {selector}")
                title_input = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                if title_input and title_input.is_enabled():
                    logger.info(f"✅ 找到标题输入框: {selector}")
                    return title_input
                    
            except TimeoutException:
                logger.debug(f"⏰ 标题选择器超时: {selector}")
                continue
            except Exception as e:
                logger.debug(f"⚠️ 标题选择器错误: {selector}, {e}")
                continue
        
        logger.error("❌ 未找到可用的标题输入框")
        return None
    
    async def _find_content_editor(self):
        """
        查找内容编辑器
        
        Returns:
            内容编辑器元素，如果未找到返回None
        """
        driver = self.browser_manager.driver
        wait = WebDriverWait(driver, XHSConfig.DEFAULT_WAIT_TIME)
        
        try:
            logger.debug(f"🔍 查找内容编辑器: {XHSSelectors.CONTENT_EDITOR}")
            content_editor = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, XHSSelectors.CONTENT_EDITOR))
            )
            
            if content_editor and content_editor.is_enabled():
                logger.info("✅ 找到内容编辑器")
                return content_editor
            
        except TimeoutException:
            logger.error("⏰ 内容编辑器查找超时")
        except Exception as e:
            logger.error(f"⚠️ 内容编辑器查找错误: {e}")
        
        logger.error("❌ 未找到可用的内容编辑器")
        return None
    
    async def _perform_title_fill(self, title_input, title: str) -> bool:
        """
        执行标题填写
        
        Args:
            title_input: 标题输入元素
            title: 标题内容
            
        Returns:
            填写是否成功
        """
        try:
            # 清空现有内容
            title_input.clear()
            await asyncio.sleep(0.5)
            
            # 输入标题
            cleaned_title = clean_text_for_browser(title)
            title_input.send_keys(cleaned_title)
            
            # 验证输入是否成功
            await asyncio.sleep(1)
            current_value = title_input.get_attribute("value") or title_input.text
            
            if cleaned_title in current_value or len(current_value) > 0:
                logger.info("✅ 标题填写成功")
                return True
            else:
                logger.error("❌ 标题填写验证失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 标题填写过程出错: {e}")
            return False
    
    async def _perform_content_fill(self, content_editor, content: str) -> bool:
        """
        执行内容填写
        
        Args:
            content_editor: 内容编辑器元素
            content: 笔记内容
            
        Returns:
            填写是否成功
        """
        try:
            # 点击编辑器以获得焦点
            content_editor.click()
            await asyncio.sleep(0.5)
            
            # 清空现有内容
            content_editor.clear()
            
            # 尝试使用Ctrl+A全选然后删除
            content_editor.send_keys(Keys.CONTROL + "a")
            await asyncio.sleep(0.2)
            content_editor.send_keys(Keys.DELETE)
            await asyncio.sleep(0.5)
            
            # 输入内容
            cleaned_content = clean_text_for_browser(content)
            
            # 分段输入，避免一次输入过多内容
            lines = cleaned_content.split('\n')
            for i, line in enumerate(lines):
                content_editor.send_keys(line)
                if i < len(lines) - 1:
                    content_editor.send_keys(Keys.ENTER)
                await asyncio.sleep(0.1)  # 短暂等待
            
            # 验证输入是否成功
            await asyncio.sleep(1)
            current_text = content_editor.text or content_editor.get_attribute("textContent") or ""
            
            # 简单验证：检查是否包含部分内容
            if (len(current_text) > 0 and 
                (cleaned_content[:20] in current_text or 
                 len(current_text) >= len(cleaned_content) * 0.8)):
                logger.info("✅ 内容填写成功")
                return True
            else:
                logger.error(f"❌ 内容填写验证失败，期望长度: {len(cleaned_content)}, 实际长度: {len(current_text)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 内容填写过程出错: {e}")
            return False
    
    async def _perform_tags_fill(self, tags: List[str]) -> bool:
        """
        执行标签填写
        
        在小红书中，标签通常是在内容中使用#符号，或在专门的标签区域
        这里实现一个通用的标签处理方法
        
        Args:
            tags: 标签列表
            
        Returns:
            填写是否成功
        """
        try:
            driver = self.browser_manager.driver
            
            # 尝试查找标签输入区域
            tag_selectors = [
                "input[placeholder*='标签']",
                "input[placeholder*='tag']", 
                ".tag-input",
                ".tags-input"
            ]
            
            tag_input = None
            for selector in tag_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        tag_input = elements[0]
                        break
                except:
                    continue
            
            if tag_input:
                # 如果找到专门的标签输入框
                logger.info("✅ 找到标签输入框")
                
                for tag in tags:
                    tag_input.send_keys(f"#{tag}")
                    tag_input.send_keys(Keys.SPACE)  # 或 Keys.ENTER
                    await asyncio.sleep(0.3)
                
                logger.info("✅ 标签填写完成")
                return True
            else:
                # 如果没有专门的标签输入框，在内容末尾添加标签
                logger.info("🏷️ 未找到专门标签输入框，将在内容中添加标签")
                
                content_editor = await self._find_content_editor()
                if content_editor:
                    # 移动到内容末尾
                    content_editor.send_keys(Keys.END)
                    content_editor.send_keys(Keys.ENTER)
                    content_editor.send_keys(Keys.ENTER)
                    
                    # 添加标签
                    tag_text = " ".join([f"#{tag}" for tag in tags])
                    content_editor.send_keys(tag_text)
                    
                    logger.info("✅ 标签已添加到内容末尾")
                    return True
                
                logger.warning("⚠️ 无法找到合适的位置填写标签")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ 标签填写过程出错: {e}")
            return False
    
    def get_current_content(self) -> dict:
        """
        获取当前页面的内容信息
        
        Returns:
            包含当前内容信息的字典
        """
        try:
            driver = self.browser_manager.driver
            
            result = {
                "title": "",
                "content": "",
                "has_title_input": False,
                "has_content_editor": False
            }
            
            # 获取标题
            for selector in get_title_input_selectors():
                try:
                    title_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if title_elements and title_elements[0].is_displayed():
                        result["has_title_input"] = True
                        result["title"] = title_elements[0].get_attribute("value") or ""
                        break
                except:
                    continue
            
            # 获取内容
            try:
                content_elements = driver.find_elements(By.CSS_SELECTOR, XHSSelectors.CONTENT_EDITOR)
                if content_elements and content_elements[0].is_displayed():
                    result["has_content_editor"] = True
                    result["content"] = content_elements[0].text or ""
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 获取当前内容失败: {e}")
            return {"error": str(e)} 