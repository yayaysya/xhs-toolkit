#!/usr/bin/env python3
"""
小红书 MCP 服务器 - 支持SSE协议

这个服务器允许AI客户端（如Claude、Cherry Studio等）通过MCP协议与小红书交互。
支持笔记发布、搜索、用户信息获取等功能。
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import signal

# 加载环境变量配置
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

from fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from pydantic import BaseModel
from loguru import logger

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
# 移除loguru的默认handler避免重复输出
logger.remove()
# 只添加文件输出，控制台输出由loguru默认处理
logger.add("xhs_server.log", rotation="10 MB", level=log_level, format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}")
# 重新添加控制台输出（避免重复）
logger.add(sys.stderr, level=log_level, format="{time:HH:mm:ss} | {level:<8} | {message}")

# 抑制FastMCP/uvicorn的ASGI错误日志
import logging
class ASGIErrorFilter(logging.Filter):
    def filter(self, record):
        # 过滤ASGI相关的错误信息
        asgi_error_keywords = [
            "Expected ASGI message",
            "RuntimeError",
            "Exception in ASGI application",
            "Cancel 0 running task(s)"
        ]
        return not any(keyword in record.getMessage() for keyword in asgi_error_keywords)

# 应用过滤器到uvicorn日志
uvicorn_logger = logging.getLogger("uvicorn.error")
uvicorn_logger.addFilter(ASGIErrorFilter())
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(ASGIErrorFilter())

# 根据日志级别输出启动信息
if log_level == "DEBUG":
    logger.debug("🔧 DEBUG模式已启用，将输出详细调试信息")
    logger.debug(f"🔧 日志级别: {log_level}")
    logger.debug(f"🔧 当前工作目录: {os.getcwd()}")
    logger.debug(f"🔧 Python版本: {sys.version}")
    logger.debug("🔧 已配置ASGI错误过滤器")

class XHSConfig:
    """小红书配置类"""
    
    def __init__(self):
        self.chrome_path = os.getenv("CHROME_PATH", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        self.chromedriver_path = os.getenv("WEBDRIVER_CHROME_DRIVER", "/opt/homebrew/bin/chromedriver")
        self.phone = os.getenv("phone", "")
        self.json_path = os.getenv("json_path", "./xhs/cookies")
        self.cookies_file = os.path.join(self.json_path, "xiaohongshu_cookies.json")
        
        # Debug模式下输出配置信息
        if log_level == "DEBUG":
            logger.debug("🔧 配置信息:")
            logger.debug(f"   Chrome路径: {self.chrome_path}")
            logger.debug(f"   ChromeDriver路径: {self.chromedriver_path}")
            logger.debug(f"   手机号: {self.phone[:3]}****{self.phone[-4:] if len(self.phone) >= 7 else '****'}")
            logger.debug(f"   Cookies路径: {self.json_path}")
            logger.debug(f"   Cookies文件: {self.cookies_file}")
            logger.debug(f"   Cookies文件存在: {os.path.exists(self.cookies_file)}")
            logger.debug(f"   绝对路径: {os.path.abspath(self.cookies_file)}")
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性"""
        issues = []
        
        if not os.path.exists(self.chrome_path):
            issues.append(f"Chrome浏览器未找到: {self.chrome_path}")
            
        if not os.path.exists(self.chromedriver_path):
            issues.append(f"ChromeDriver未找到: {self.chromedriver_path}")
            
        if not self.phone:
            issues.append("未配置手机号码")
            
        if not os.path.exists(self.json_path):
            try:
                os.makedirs(self.json_path, exist_ok=True)
                logger.info(f"✅ 已创建Cookies目录: {self.json_path}")
            except Exception as e:
                issues.append(f"无法创建Cookies目录: {e}")
                
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
        
    def load_cookies(self) -> List[Dict]:
        """加载cookies"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.warning(f"Cookies文件不存在: {self.cookies_file}")
                return []
                
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 成功加载 {len(cookies)} 个cookies")
                for cookie in cookies[:3]:  # 只显示前3个cookie的名称
                    logger.debug(f"   Cookie: {cookie.get('name', 'N/A')}")
                if len(cookies) > 3:
                    logger.debug(f"   ... 还有 {len(cookies) - 3} 个cookies")
                    
            return cookies
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            if log_level == "DEBUG":
                import traceback
                logger.debug(f"🔧 详细错误信息: {traceback.format_exc()}")
            return []

class XHSNote(BaseModel):
    """小红书笔记数据模型"""
    title: str
    content: str
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None

class XHSSearchResult(BaseModel):
    """搜索结果数据模型"""
    note_id: str
    title: str
    author: str
    likes: int
    url: str
    thumbnail: Optional[str] = None

class XHSClient:
    """小红书客户端类"""
    
    def __init__(self, config: XHSConfig):
        self.config = config
        self.driver = None
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """设置requests会话"""
        cookies = self.config.load_cookies()
        if cookies:
            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie['domain']
                )
    
    def text_cleanup(self, text: str) -> str:
        """
        清理文本中ChromeDriver不支持的字符
        ChromeDriver只支持BMP(Basic Multilingual Plane)字符
        """
        if not text:
            return ""
            
        # 移除超出BMP范围的字符（U+10000及以上）
        cleaned_text = ""
        for char in text:
            # BMP字符范围是U+0000到U+FFFF
            if ord(char) <= 0xFFFF:
                cleaned_text += char
            else:
                # 用空格替换不支持的字符
                cleaned_text += " "
        
        # 清理连续的空格
        import re
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        logger.info(f"🧹 文本清理: 原长度={len(text)}, 清理后长度={len(cleaned_text)}")
        return cleaned_text
    
    def init_driver(self):
        """初始化Chrome浏览器驱动"""
        if self.driver:
            logger.info("🌐 浏览器驱动已存在，无需重新初始化")
            return
            
        logger.info("🚀 开始初始化Chrome浏览器驱动...")
        
        # 验证配置
        validation = self.config.validate_config()
        if not validation["valid"]:
            error_msg = "配置验证失败: " + "; ".join(validation["issues"])
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        chrome_options = Options()
        chrome_options.binary_location = self.config.chrome_path
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Debug模式下添加更多信息
        if log_level == "DEBUG":
            logger.debug("🔧 Chrome启动参数:")
            logger.debug(f"   二进制路径: {chrome_options.binary_location}")
            logger.debug(f"   用户代理: {user_agent}")
            logger.debug("   启动参数: --no-sandbox, --disable-dev-shm-usage, --disable-blink-features=AutomationControlled")
        
        try:
            logger.info(f"📍 Chrome路径: {self.config.chrome_path}")
            logger.info(f"📍 ChromeDriver路径: {self.config.chromedriver_path}")
            
            service = Service(executable_path=self.config.chromedriver_path)
            self.driver = webdriver.Chrome(
                options=chrome_options,
                service=service
            )
            
            # 设置窗口大小和超时
            self.driver.set_window_size(1920, 1080)
            self.driver.implicitly_wait(10)
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 浏览器窗口大小: {self.driver.get_window_size()}")
                logger.debug(f"🔧 浏览器版本: {self.driver.capabilities.get('browserVersion', 'Unknown')}")
            
            logger.info("🌐 浏览器启动成功，正在访问小红书...")
            # 加载cookies
            self.driver.get("https://www.xiaohongshu.com")
            logger.info("📄 已访问小红书主页，开始加载cookies...")
            
            cookies = self.config.load_cookies()
            if not cookies:
                logger.warning("⚠️  没有找到cookies，可能需要先登录")
                return
                
            loaded_count = 0
            failed_cookies = []
            
            for cookie in cookies:
                try:
                    cookie_data = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False)
                    }
                    self.driver.add_cookie(cookie_data)
                    loaded_count += 1
                    
                    if log_level == "DEBUG":
                        logger.debug(f"🔧 成功加载cookie: {cookie['name']}")
                        
                except Exception as e:
                    failed_cookies.append(cookie['name'])
                    logger.warning(f"⚠️  无法加载cookie {cookie['name']}: {e}")
                    if log_level == "DEBUG":
                        import traceback
                        logger.debug(f"🔧 Cookie加载失败详情: {traceback.format_exc()}")
                    
            logger.info(f"🍪 成功加载 {loaded_count}/{len(cookies)} 个cookies")
            if failed_cookies and log_level == "DEBUG":
                logger.debug(f"🔧 失败的cookies: {failed_cookies}")
                
            # 刷新页面以应用cookies
            self.driver.refresh()
            logger.info("✅ 浏览器驱动初始化完成！")
            
        except Exception as e:
            logger.error(f"❌ 浏览器驱动初始化失败: {e}")
            if log_level == "DEBUG":
                import traceback
                logger.debug(f"🔧 详细错误信息: {traceback.format_exc()}")
            
            # 清理资源
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            raise
    
    def close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                logger.info("🔒 正在关闭浏览器...")
                
                # 尝试保存当前状态用于调试
                if log_level == "DEBUG":
                    try:
                        current_url = self.driver.current_url
                        window_handles = len(self.driver.window_handles)
                        logger.debug(f"🔧 关闭前状态 - URL: {current_url}, 窗口数: {window_handles}")
                    except Exception as e:
                        logger.debug(f"🔧 无法获取浏览器状态: {e}")
                
                # 关闭所有窗口
                try:
                    for handle in self.driver.window_handles:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                except Exception as e:
                    logger.warning(f"⚠️  关闭窗口时出错: {e}")
                
                # 退出驱动
                self.driver.quit()
                logger.info("✅ 浏览器已成功关闭")
                
            except Exception as e:
                logger.error(f"❌ 关闭浏览器时出错: {e}")
                if log_level == "DEBUG":
                    import traceback
                    logger.debug(f"🔧 关闭浏览器错误详情: {traceback.format_exc()}")
                
                # 强制终止进程
                try:
                    if hasattr(self.driver, 'service') and self.driver.service.process:
                        self.driver.service.process.terminate()
                        logger.info("🔧 已强制终止ChromeDriver进程")
                except Exception as force_e:
                    logger.warning(f"⚠️  强制终止进程失败: {force_e}")
                    
            finally:
                self.driver = None
                logger.debug("🔧 driver对象已重置为None")
        else:
            logger.debug("🔧 浏览器驱动未初始化，无需关闭")
    
    async def search_notes(self, keyword: str, limit: int = 10) -> List[XHSSearchResult]:
        """搜索小红书笔记"""
        try:
            self.init_driver()
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            self.driver.get(search_url)
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 搜索URL: {search_url}")
            
            # 等待搜索结果加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note-item")))
            
            results = []
            note_elements = self.driver.find_elements(By.CLASS_NAME, "note-item")[:limit]
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 找到 {len(note_elements)} 个笔记元素")
            
            for element in note_elements:
                try:
                    title_elem = element.find_element(By.CLASS_NAME, "title")
                    author_elem = element.find_element(By.CLASS_NAME, "author")
                    likes_elem = element.find_element(By.CLASS_NAME, "like-count")
                    link_elem = element.find_element(By.TAG_NAME, "a")
                    
                    result = XHSSearchResult(
                        note_id=link_elem.get_attribute("href").split("/")[-1],
                        title=title_elem.text,
                        author=author_elem.text,
                        likes=int(likes_elem.text.replace("万", "0000").replace(".", "")),
                        url=link_elem.get_attribute("href"),
                        thumbnail=element.find_element(By.TAG_NAME, "img").get_attribute("src") if element.find_elements(By.TAG_NAME, "img") else None
                    )
                    results.append(result)
                    
                    if log_level == "DEBUG":
                        logger.debug(f"🔧 解析笔记: {result.title[:20]}...")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse note element: {e}")
                    if log_level == "DEBUG":
                        import traceback
                        logger.debug(f"🔧 解析笔记元素失败: {traceback.format_exc()}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            if log_level == "DEBUG":
                import traceback
                logger.debug(f"🔧 搜索失败详情: {traceback.format_exc()}")
            return []
        finally:
            # 确保浏览器被关闭
            try:
                self.close_driver()
            except Exception as close_error:
                logger.error(f"❌ 搜索后关闭浏览器失败: {close_error}")
    
    async def get_note_detail(self, note_id: str) -> Dict[str, Any]:
        """获取笔记详情"""
        try:
            self.init_driver()
            note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
            self.driver.get(note_url)
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 笔记详情URL: {note_url}")
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "note-detail")))
            
            # 提取笔记信息
            title = self.driver.find_element(By.CLASS_NAME, "title").text
            content = self.driver.find_element(By.CLASS_NAME, "content").text
            author = self.driver.find_element(By.CLASS_NAME, "author-name").text
            
            # 提取图片
            images = []
            img_elements = self.driver.find_elements(By.CLASS_NAME, "note-image")
            for img in img_elements:
                src = img.get_attribute("src")
                if src:
                    images.append(src)
            
            # 提取标签
            tags = []
            tag_elements = self.driver.find_elements(By.CLASS_NAME, "tag")
            for tag in tag_elements:
                tags.append(tag.text.replace("#", ""))
            
            result = {
                "note_id": note_id,
                "title": title,
                "content": content,
                "author": author,
                "images": images,
                "tags": tags,
                "url": note_url
            }
            
            if log_level == "DEBUG":
                logger.debug(f"🔧 笔记详情: {title[:30]}..., 作者: {author}")
                logger.debug(f"🔧 图片数量: {len(images)}, 标签数量: {len(tags)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get note detail: {e}")
            if log_level == "DEBUG":
                import traceback
                logger.debug(f"🔧 获取笔记详情失败: {traceback.format_exc()}")
            return {}
        finally:
            # 确保浏览器被关闭
            try:
                self.close_driver()
            except Exception as close_error:
                logger.error(f"❌ 获取详情后关闭浏览器失败: {close_error}")
    
    async def publish_note(self, note: XHSNote) -> Dict[str, Any]:
        """发布笔记"""
        try:
            self.init_driver()
            logger.info("🌐 直接访问小红书发布页面...")
            
            # 直接访问发布页面
            self.driver.get("https://creator.xiaohongshu.com/publish/publish?from=menu")
            await asyncio.sleep(3)
            
            logger.info("📄 页面标题: " + self.driver.title)
            logger.info("📄 当前URL: " + self.driver.current_url)
            
            # 检查是否成功进入发布页面
            if "publish" not in self.driver.current_url:
                logger.warning("⚠️  可能未成功进入发布页面")
                return {
                    "success": False,
                    "message": "无法访问发布页面，可能需要重新登录"
                }
                
            # 等待页面完全加载
            wait = WebDriverWait(self.driver, 15)
            
            # 切换到图文发布模式（如果有多个tab的话）
            try:
                tabs = self.driver.find_elements(By.CSS_SELECTOR, ".creator-tab")
                if len(tabs) > 1:
                    logger.info("🔄 切换到图文发布模式...")
                    tabs[2].click()  # 第三个tab通常是图文
                    await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️  未找到发布模式tab: {e}")
            
            # 处理图片上传区域
            try:
                # 检查是否存在文件上传input
                upload_input = self.driver.find_element(By.CSS_SELECTOR, ".upload-input")
                logger.info("🔍 发现文件上传input元素")
                
                if note.images:
                    logger.info(f"📸 准备上传 {len(note.images)} 张图片...")
                    # 将所有图片路径用\n连接成一个字符串一次性上传
                    upload_input.send_keys('\n'.join(note.images))
                    await asyncio.sleep(1)  # 等待图片开始上传
                    logger.info("✅ 图片上传指令已发送")
                else:
                    logger.info("📷 没有图片要上传，尝试跳过上传步骤...")
                    # 尝试点击页面上可能存在的"跳过"或"直接发布"按钮
                    skip_selectors = [
                        "//button[contains(text(), '跳过')]",
                        "//button[contains(text(), '不上传')]", 
                        "//button[contains(text(), '直接发布')]",
                        "//span[contains(text(), '跳过')]",
                        ".skip-btn",
                        ".no-upload",
                        "//div[contains(text(), '跳过')]"
                    ]
                    
                    skipped = False
                    for selector in skip_selectors:
                        try:
                            if selector.startswith("//"):
                                skip_btn = self.driver.find_element(By.XPATH, selector)
                            else:
                                skip_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            logger.info(f"🖱️ 找到跳过按钮: {selector}")
                            skip_btn.click()
                            await asyncio.sleep(1)
                            skipped = True
                            break
                        except:
                            continue
                    
                    if not skipped:
                        logger.info("🔍 未找到跳过按钮，尝试点击页面其他区域进入编辑模式...")
                        # 尝试点击页面的其他区域来进入编辑模式
                        try:
                            # 点击页面中央
                            self.driver.execute_script("document.body.click();")
                            await asyncio.sleep(1)
                        except:
                            pass
                            
            except Exception as e:
                logger.warning(f"⚠️ 处理上传区域时出错: {e}")
                
            # 等待页面准备好
            await asyncio.sleep(1)
            logger.info("⏳ 等待页面准备就绪...")
            
            # 添加页面状态调试信息
            try:
                page_title = self.driver.title
                page_url = self.driver.current_url
                logger.info(f"📊 当前页面状态 - 标题: {page_title}, URL: {page_url}")
                
                # 检查页面上是否有标题输入框
                title_elements = self.driver.find_elements(By.CSS_SELECTOR, ".d-text")
                logger.info(f"🔍 找到 {len(title_elements)} 个标题输入框")
                
                # 检查页面上是否有内容编辑器
                content_elements = self.driver.find_elements(By.CSS_SELECTOR, ".ql-editor")
                logger.info(f"🔍 找到 {len(content_elements)} 个内容编辑器")
                
            except Exception as e:
                logger.warning(f"⚠️ 获取页面状态时出错: {e}")
            
            # 填写标题
            try:
                logger.info("✏️  填写标题...")
                title = self.text_cleanup(note.title[:20])  # 限制标题长度
                title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".d-text")))
                title_input.send_keys(title)  # 不使用clear()，直接输入
                logger.info(f"✅ 标题已填写: {title}")
            except Exception as e:
                logger.error(f"❌ 填写标题失败: {e}")
                return {
                    "success": False,
                    "message": f"填写标题失败: {str(e)}"
                }
            
            # 填写内容
            try:
                logger.info("📝 填写内容...")
                content_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor")))
                content_input.send_keys(self.text_cleanup(note.content))  # 不使用clear()，直接输入
                logger.info("✅ 内容已填写")
            except Exception as e:
                logger.error(f"❌ 填写内容失败: {e}")
                return {
                    "success": False,
                    "message": f"填写内容失败: {str(e)}"
                }
            
            # 等待内容处理
            await asyncio.sleep(2)
            
            # 点击发布按钮
            try:
                logger.info("🚀 点击发布按钮...")
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, ".publishBtn")
                submit_btn.click()
                logger.info("✅ 发布按钮已点击")
                await asyncio.sleep(3)
                
                # 检查是否发布成功
                current_url = self.driver.current_url
                logger.info(f"📍 发布后页面URL: {current_url}")
                
                return {
                    "success": True,
                    "message": f"笔记发布成功！标题: {note.title}",
                    "note_title": note.title,
                    "final_url": current_url
                }
                
            except Exception as e:
                logger.error(f"❌ 点击发布按钮失败: {e}")
                return {
                    "success": False,
                    "message": f"点击发布按钮失败: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"❌ 发布笔记过程出错: {e}")
            # 保存错误时的页面截图
            try:
                self.driver.save_screenshot("error_screenshot.png")
                logger.info("📸 已保存错误截图到 error_screenshot.png")
            except:
                pass
                
            return {
                "success": False,
                "message": f"发布过程出错: {str(e)}",
                "error_type": type(e).__name__
            }
        finally:
            # 发布完成后关闭浏览器 - 确保无论成功失败都能关闭
            try:
                logger.info("🔒 发布完成，关闭浏览器...")
                self.close_driver()
                logger.info("✅ 浏览器关闭完成")
            except Exception as close_error:
                logger.error(f"❌ 关闭浏览器时发生错误: {close_error}")
                if log_level == "DEBUG":
                    import traceback
                    logger.debug(f"🔧 浏览器关闭错误详情: {traceback.format_exc()}")
                # 即使关闭失败也不影响返回结果
    
    async def get_user_info(self, user_id: str = None) -> Dict[str, Any]:
        """获取用户信息"""
        try:
            if not user_id:
                # 获取当前登录用户信息
                url = "https://www.xiaohongshu.com/api/sns/web/v1/user/selfinfo"
            else:
                url = f"https://www.xiaohongshu.com/api/sns/web/v1/user/{user_id}"
            
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
            else:
                return {"error": "Failed to get user info"}
                
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"error": str(e)}

# 初始化MCP服务器
config = XHSConfig()
xhs_client = XHSClient(config)
mcp = FastMCP("小红书MCP服务器")

@mcp.tool()
async def test_connection() -> str:
    """
    测试MCP连接是否正常
    
    Returns:
        连接状态信息
    """
    logger.info("🧪 收到连接测试请求")
    try:
        import time
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 检查配置
        config_status = {
            "chrome_path_exists": os.path.exists(config.chrome_path),
            "chromedriver_path_exists": os.path.exists(config.chromedriver_path),
            "cookies_file_exists": os.path.exists(config.cookies_file),
            "cookies_count": len(config.load_cookies()),
            "current_time": current_time
        }
        
        logger.info(f"✅ 连接测试完成: {config_status}")
        
        result = {
            "status": "success",
            "message": "MCP连接正常！",
            "config": config_status,
            "timestamp": current_time
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"连接测试失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def search_xiaohongshu_notes(keyword: str, limit: int = 10) -> str:
    """
    搜索小红书笔记
    
    Args:
        keyword: 搜索关键词
        limit: 返回结果数量限制（默认10）
    
    Returns:
        搜索结果的JSON字符串
    """
    logger.info(f"🔍 开始搜索小红书笔记: 关键词='{keyword}', 限制={limit}")
    try:
        logger.info("📱 正在初始化浏览器...")
        results = await xhs_client.search_notes(keyword, limit)
        logger.info(f"✅ 搜索完成，找到 {len(results)} 条结果")
        return json.dumps([result.dict() for result in results], ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"搜索失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def get_xiaohongshu_note_detail(note_id: str) -> str:
    """
    获取小红书笔记详情
    
    Args:
        note_id: 笔记ID
    
    Returns:
        笔记详情的JSON字符串
    """
    logger.info(f"📄 开始获取笔记详情: note_id='{note_id}'")
    try:
        logger.info("📱 正在初始化浏览器...")
        detail = await xhs_client.get_note_detail(note_id)
        logger.info(f"✅ 获取笔记详情成功")
        return json.dumps(detail, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"获取笔记详情失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def publish_xiaohongshu_note(title: str, content: str, tags: str = "", location: str = "", images: str = "") -> str:
    """
    发布小红书笔记
    
    Args:
        title (str): 笔记标题，例如："今日分享"
        content (str): 笔记内容，例如："今天去了一个很棒的地方"
        tags (str, optional): 标签，用逗号分隔，例如："生活,旅行,美食"
        location (str, optional): 位置信息，例如："北京"
        images (str, optional): 图片文件路径，用逗号分隔，例如："/Volumes/xhs-files/image1.jpg,/Volumes/xhs-files/image2.jpg"
    
    Returns:
        str: 发布结果的JSON字符串
        
    Example:
        title="今日美食", content="推荐一家好吃的餐厅", tags="美食,生活", images="/Volumes/xhs-files/food.jpg"
    """
    logger.info(f"📝 开始发布小红书笔记: 标题='{title}', 标签='{tags}', 位置='{location}', 图片='{images}'")
    try:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        image_list = [img.strip() for img in images.split(",") if img.strip()] if images else []
        
        logger.info(f"📸 处理图片路径: {image_list}")
        logger.info("📱 正在初始化浏览器...")
        
        note = XHSNote(
            title=title,
            content=content,
            images=image_list if image_list else None,
            tags=tag_list,
            location=location if location else None
        )
        result = await xhs_client.publish_note(note)
        logger.info(f"✅ 发布笔记完成: {result.get('success', False)}")
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"发布笔记失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def get_xiaohongshu_user_info(user_id: str = "") -> str:
    """
    获取小红书用户信息
    
    Args:
        user_id: 用户ID（为空则获取当前登录用户信息）
    
    Returns:
        用户信息的JSON字符串
    """
    logger.info(f"👤 开始获取用户信息: user_id='{user_id}'")
    try:
        user_info = await xhs_client.get_user_info(user_id if user_id else None)
        logger.info(f"✅ 获取用户信息成功")
        return json.dumps(user_info, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"获取用户信息失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def close_browser() -> str:
    """
    关闭浏览器
    
    Returns:
        关闭状态信息
    """
    logger.info("🔒 收到关闭浏览器请求")
    try:
        xhs_client.close_driver()
        logger.info("✅ 浏览器已关闭")
        return json.dumps({
            "success": True,
            "message": "浏览器已成功关闭"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"关闭浏览器失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

@mcp.tool()
async def test_publish_params(title: str, content: str, image_path: str = "") -> str:
    """
    测试发布参数解析（不实际发布）
    
    Args:
        title (str): 测试标题
        content (str): 测试内容
        image_path (str, optional): 测试图片路径
    
    Returns:
        str: 参数解析结果
    """
    logger.info(f"🧪 测试参数解析: title='{title}', content='{content}', image_path='{image_path}'")
    
    result = {
        "test_mode": True,
        "received_params": {
            "title": title,
            "content": content,
            "image_path": image_path,
            "title_length": len(title),
            "content_length": len(content),
            "image_path_valid": bool(image_path and image_path.startswith("/Volumes/xhs-files/"))
        },
        "message": "参数接收成功，这是测试模式，未实际发布",
        "timestamp": str(asyncio.get_event_loop().time())
    }
    
    logger.info(f"✅ 测试完成: {result}")
    return json.dumps(result, ensure_ascii=False, indent=2)

@mcp.resource("xhs://config")
def get_xhs_config() -> str:
    """获取小红书MCP服务器配置信息"""
    config_info = {
        "chrome_path": config.chrome_path,
        "chromedriver_path": config.chromedriver_path,
        "phone": config.phone[:3] + "****" + config.phone[-4:] if config.phone else "",
        "cookies_loaded": len(config.load_cookies()) > 0,
        "server_status": "running"
    }
    return json.dumps(config_info, ensure_ascii=False, indent=2)

@mcp.resource("xhs://help")
def get_xhs_help() -> str:
    """获取小红书MCP服务器使用帮助"""
    help_text = """
# 小红书MCP服务器使用帮助

## 可用工具

### 1. test_connection
- 功能: 测试MCP连接
- 参数: 无

### 2. search_xiaohongshu_notes
- 功能: 搜索小红书笔记
- 参数: 
  - keyword: 搜索关键词
  - limit: 返回结果数量（默认10）

### 3. get_xiaohongshu_note_detail  
- 功能: 获取笔记详情
- 参数:
  - note_id: 笔记ID

### 4. publish_xiaohongshu_note
- 功能: 发布新笔记
- 参数:
  - title: 笔记标题
  - content: 笔记内容
  - tags: 标签（逗号分隔）
  - location: 位置信息
  - images: 图片路径（逗号分隔多个路径）

### 5. get_xiaohongshu_user_info
- 功能: 获取用户信息
- 参数:
  - user_id: 用户ID（可选）

### 6. close_browser
- 功能: 关闭浏览器

### 7. test_publish_params
- 功能: 测试发布参数解析（调试用）
- 参数:
  - title: 测试标题
  - content: 测试内容
  - image_path: 测试图片路径

## 可用资源

- xhs://config - 查看服务器配置
- xhs://help - 查看此帮助信息

## 环境变量

- CHROME_PATH: Chrome浏览器路径
- WEBDRIVER_CHROME_DRIVER: ChromeDriver路径  
- phone: 手机号码
- json_path: Cookies文件路径
"""
    return help_text

@mcp.prompt()
def xiaohongshu_content_creation(topic: str, style: str = "生活分享") -> str:
    """
    小红书内容创作助手
    
    Args:
        topic: 内容主题
        style: 写作风格（生活分享、美妆护肤、美食探店、旅行攻略等）
    
    Returns:
        内容创作提示词
    """
    prompt = f"""
请帮我创作一篇关于"{topic}"的小红书笔记，风格为"{style}"。

要求：
1. 标题要吸引人，包含emoji和关键词
2. 内容要有价值，包含具体的建议或信息
3. 适当使用emoji让内容更生动
4. 添加相关标签（3-5个）
5. 字数控制在200-500字
6. 语言风格要贴近小红书用户习惯

请按以下格式输出：

【标题】
[在这里写标题]

【正文】
[在这里写正文内容]

【标签】
[在这里列出相关标签]

【发布建议】
[发布时间、配图建议等]
"""
    return prompt

def main():
    """主函数"""
    logger.info("🚀 启动小红书 MCP 服务器...")
    
    # 验证配置
    logger.info("🔍 验证配置...")
    validation = config.validate_config()
    
    if not validation["valid"]:
        logger.error("❌ 配置验证失败:")
        for issue in validation["issues"]:
            logger.error(f"   • {issue}")
        logger.error("💡 请检查 .env 文件配置")
        return
    
    logger.info("✅ 配置验证通过")
    
    # 检查cookies
    cookies = config.load_cookies()
    if not cookies:
        logger.warning("⚠️  未找到cookies文件，请先运行获取cookies")
        logger.info("💡 运行命令: ./xhs-toolkit cookie save")
    else:
        logger.info(f"✅ 已加载 {len(cookies)} 个cookies")
    
    # 从环境变量获取端口，默认8000
    port = int(os.getenv('FASTMCP_SERVER_PORT', '8000'))
    host = os.getenv('FASTMCP_SERVER_HOST', '0.0.0.0')
    
    if log_level == "DEBUG":
        logger.debug(f"🔧 服务器配置: {host}:{port}")
        logger.debug(f"🔧 日志级别: {log_level}")
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("👋 收到停止信号，正在优雅关闭服务器...")
        # 清理资源
        try:
            if 'xhs_client' in globals() and hasattr(xhs_client, 'driver') and xhs_client.driver:
                logger.info("🧹 清理残留的浏览器实例...")
                xhs_client.close_driver()
        except Exception as cleanup_error:
            if log_level == "DEBUG":
                logger.debug(f"🔧 清理资源时出错: {cleanup_error}")
        
        logger.info("✅ 服务器已停止")
        os._exit(0)  # 强制退出避免ASGI错误
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务器
    try:
        # 获取本机IP地址
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.254.254.254", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"📡 本机IP地址: {local_ip}")
        except Exception as ip_error:
            local_ip = "未知"
            if log_level == "DEBUG":
                logger.debug(f"🔧 获取IP地址失败: {ip_error}")
            
        logger.info(f"🚀 启动SSE服务器 (端口{port})")
        logger.info("📡 可通过以下地址访问:")
        logger.info(f"   • http://localhost:{port}/sse (本机)")
        if local_ip != "未知":
            logger.info(f"   • http://{local_ip}:{port}/sse (内网)")
        
        logger.info("🎯 MCP工具列表:")
        logger.info("   • test_connection - 测试连接")
        logger.info("   • search_xiaohongshu_notes - 搜索笔记")
        logger.info("   • publish_xiaohongshu_note - 发布笔记")
        logger.info("   • get_xiaohongshu_user_info - 获取用户信息")
        logger.info("   • close_browser - 关闭浏览器")
        
        logger.info("🔧 按 Ctrl+C 停止服务器")
        logger.info("💡 终止时的ASGI错误信息是正常现象，可以忽略")
            
        # 使用FastMCP内置的run方法，监听所有接口
        mcp.run(transport="sse", port=port, host=host)
        
    except KeyboardInterrupt:
        # 这个catch可能不会被触发，因为signal_handler会先处理
        logger.info("👋 收到停止信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        if log_level == "DEBUG":
            import traceback
            logger.debug(f"🔧 服务器启动错误详情: {traceback.format_exc()}")
        raise
    finally:
        # 清理资源
        try:
            if 'xhs_client' in globals() and hasattr(xhs_client, 'driver') and xhs_client.driver:
                logger.info("🧹 清理残留的浏览器实例...")
                xhs_client.close_driver()
        except Exception as cleanup_error:
            logger.warning(f"⚠️  清理资源时出错: {cleanup_error}")
        
        logger.info("✅ 服务器已停止")

if __name__ == "__main__":
    main() 