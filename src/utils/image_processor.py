"""
图片处理模块

支持多种图片输入格式的处理：
- 本地文件路径
- 网络URL
"""

from __future__ import annotations
import asyncio
import os
import tempfile
from pathlib import Path
from typing import List, Union, Optional, Tuple
import uuid
import aiohttp
from .logger import get_logger
from ..core.playwright_browser import (
    Browser,
    get_browser_config,
    get_playwright_proxy
)


logger = get_logger(__name__)


class ImageProcessor:
    """图片处理器，支持本地文件、网络URL及浏览器下载"""
    
    def __init__(self, temp_dir: Optional[str] = None, cookies: Optional[List] = None):
        """
        初始化图片处理器
        
        Args:
            temp_dir: 临时文件目录路径
            cookies: 浏览器cookies，用于下载需要登录的图片
        """
        # 设置临时目录
        if temp_dir:
            self.temp_dir = Path(temp_dir)
        else:
            # 使用系统临时目录
            temp_base = tempfile.gettempdir() or "/tmp"
            self.temp_dir = Path(temp_base) / "xhs_images"
        
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存cookies用于下载
        self.cookies = cookies or []
        
        logger.info(f"图片处理器初始化，临时目录: {self.temp_dir}, Cookies数量: {len(self.cookies)}")
    
    async def process_images(self, images_input: Union[str, List, None], strict_mode: bool = True) -> List[str]:
        """
        处理各种格式的图片输入，返回本地文件路径列表
        
        支持格式：
        - 本地路径: "/path/to/image.jpg"
        - 网络地址: "https://example.com/image.jpg"
        - 混合列表: ["path.jpg", "https://..."]
        
        Args:
            images_input: 图片输入（支持多种格式）
            strict_mode: 严格模式，如果为True，则所有图片必须下载成功，否则抛出错误
            
        Returns:
            List[str]: 本地文件路径列表
            
        Raises:
            Exception: 当strict_mode=True且图片下载不完整时抛出错误
        """
        if not images_input:
            return []
        
        # 统一转换为列表格式
        images_list = self._normalize_to_list(images_input)
        
        if not images_list:
            return []
        
        logger.info(f"📸 开始处理图片，总数: {len(images_list)} 张，严格模式: {strict_mode}")

        # 改为顺序下载，避免因URL时效性或服务器并发限制导致失败
        processed_results: List[Union[str, None]] = []
        for i, img in enumerate(images_list):
            result = await self._process_single_image(img, i)
            processed_results.append(result)

        successful_downloads: List[str] = []
        failed_images: List[Tuple[int, str]] = []
        
        for i, result in enumerate(processed_results):
            if isinstance(result, str):
                successful_downloads.append(result)
                logger.info(f"✅ 处理图片成功 [{i+1}/{len(images_list)}]: {result}")
            else: # result is None or Exception
                failed_images.append((i, images_list[i]))
                if isinstance(result, Exception):
                     logger.error(f"❌ 处理图片时发生异常 [{i+1}/{len(images_list)}]: {images_list[i]} (错误: {str(result)})")
                else:
                     logger.error(f"❌ 处理图片失败 [{i+1}/{len(images_list)}]: {images_list[i]} (未获得本地路径)")

        # 检查下载完整性
        success_count = len(successful_downloads)
        total_count = len(images_list)
        
        logger.info(f"📊 图片处理完成，成功: {success_count}/{total_count} 张")
        
        # 严格模式下检查完整性
        if strict_mode and success_count != total_count:
            error_msg = f"图片下载不完整！需要 {total_count} 张，实际下载成功 {success_count} 张"
            if failed_images:
                error_msg += f"\n失败的图片:\n" + "\n".join([f"第{idx+1}张图片: {url}" for idx, url in failed_images])
            
            logger.error(f"❌ {error_msg}")
            
            # 清理已下载的临时文件
            await self._cleanup_downloaded_files(successful_downloads)
            
            raise Exception(error_msg)
        
        if success_count != total_count:
            logger.warning(f"⚠️ 部分图片处理失败，但继续执行（非严格模式）")
        
        return successful_downloads
    
    def _normalize_to_list(self, images_input: Union[str, List]) -> List:
        """将各种输入格式统一转换为列表"""
        if isinstance(images_input, str):
            # 单个字符串，可能是路径或逗号分隔的多个路径
            if ',' in images_input:
                # 逗号分隔的多个路径
                return [img.strip() for img in images_input.split(',') if img.strip()]
            else:
                return [images_input]
        elif isinstance(images_input, list):
            return images_input
        else:
            # 其他类型，返回空列表
            logger.warning(f"⚠️ 不支持的输入类型: {type(images_input)}")
            return []
    
    async def _process_single_image(self, img_input: str, index: int) -> Optional[str]:
        """
        处理单个图片输入
        
        Args:
            img_input: 图片输入（字符串）
            index: 图片索引
            
        Returns:
            Optional[str]: 本地文件路径，失败返回None
        """
        if not isinstance(img_input, str):
            logger.warning(f"⚠️ 无效的图片输入类型: {type(img_input)}")
            return None
            
        # 如果是网络地址，改用浏览器下载，确保成功率
        if img_input.startswith(('http://', 'https://')):
            return await self._download_with_browser(img_input, index)
        elif os.path.exists(img_input):
            # 本地文件
            return os.path.abspath(img_input)
        else:
            logger.warning(f"⚠️ 无效的图片路径: {img_input}")
            return None
    
    async def _download_with_browser(self, url: str, index: int) -> Optional[str]:
        """使用Playwright浏览器下载图片，解决复杂防盗链问题"""
        logger.info(f"🚀 尝试使用浏览器下载: {url}")
        browser_instance = None
        try:
            config = get_browser_config()
            browser_instance = await Browser.create(
                config=config,
                proxy=get_playwright_proxy(config.proxy),
                cookies=self.cookies
            )
            page = await browser_instance.new_page()
            
            # 导航到图片URL
            response = await page.goto(url, wait_until="networkidle", timeout=120000)
            
            if response is None or not response.ok:
                logger.error(f"❌ 浏览器导航失败: {url}, 状态: {response.status if response else 'N/A'}")
                await browser_instance.close()
                return None

            # 获取图片内容
            image_bytes = await response.body()
            if not image_bytes:
                logger.error(f"❌ 未能从浏览器获取图片内容: {url}")
                await browser_instance.close()
                return None

            # 从响应头获取文件类型，如果失败则从URL猜测
            content_type = response.headers.get('content-type', '')
            ext = self._get_extension_from_content_type(content_type)
            if not ext:
                url_path = Path(url.split('?')[0])
                ext = url_path.suffix if url_path.suffix else ".png"

            filename = f"browser_download_{index}_{uuid.uuid4().hex[:8]}{ext}"
            filepath = self.temp_dir / filename
            filepath.write_bytes(image_bytes)
            
            logger.info(f"✅ 浏览器下载成功: {url} -> {filepath}")
            await browser_instance.close()
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ 浏览器下载异常: {url}, 错误: {e}")
            if browser_instance:
                await browser_instance.close()
            return None

    async def _download_from_url(self, url: str, index: int) -> Optional[str]:
        """
        下载网络图片到本地（HTTP GET请求，作为备用方案）
        
        Args:
            url: 图片URL
            index: 图片索引
            
        Returns:
            Optional[str]: 本地文件路径，失败返回None
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    await asyncio.sleep(1 * attempt)  # 重试延迟
                    logger.info(f"🔄 重试HTTP下载 (第{attempt+1}次): {url}")
                else:
                    logger.info(f"⬇️ 尝试HTTP直接下载: {url}")
                
                # 为HTTP下载设置一个通用的请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }

                # 设置cookies jar (仅对小红书域名使用)
                jar = aiohttp.CookieJar()
                if self.cookies and 'xiaohongshu.com' in url:
                    logger.debug(f"🍪 使用 {len(self.cookies)} 个cookies下载图片")
                    for cookie in self.cookies:
                        try:
                            domain = cookie.get('domain', '.xiaohongshu.com')
                            if domain.startswith('.'):
                                domain = domain[1:]
                            
                            from yarl import URL
                            jar.update_cookies({
                                cookie['name']: cookie['value']
                            }, response_url=URL(f"https://{domain}"))
                        except Exception as e:
                            logger.debug(f"处理cookie失败: {e}")
                
                # 创建连接器，忽略SSL验证（某些图床可能有SSL问题）
                connector = aiohttp.TCPConnector(ssl=False, limit=10)
                
                async with aiohttp.ClientSession(headers=headers, cookie_jar=jar, connector=connector) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                        if response.status != 200:
                            if attempt == max_retries - 1:  # 最后一次重试失败
                                logger.error(f"❌ 下载图片失败: {url}, 状态码: {response.status}")
                                return None
                            else:
                                logger.warning(f"⚠️ 下载图片失败 (第{attempt+1}次): {url}, 状态码: {response.status}, 准备重试...")
                                continue
                        
                        # 获取文件扩展名
                        content_type = response.headers.get('content-type', '')
                        ext = self._get_extension_from_content_type(content_type)
                        if not ext:
                            # 从URL中尝试获取扩展名
                            url_path = Path(url.split('?')[0])
                            ext = url_path.suffix or '.jpg'
                        
                        # 生成唯一文件名
                        filename = f"download_{index}_{uuid.uuid4().hex[:8]}{ext}"
                        filepath = self.temp_dir / filename
                        
                        # 保存文件
                        content = await response.read()
                        filepath.write_bytes(content)
                        
                        logger.info(f"✅ 下载图片成功: {url} -> {filepath}")
                        return str(filepath)
                        
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    raise Exception(f"下载图片超时: {url}")
                else:
                    logger.warning(f"⚠️ 下载图片超时 (第{attempt+1}次): {url}, 准备重试...")
                    continue
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"下载图片失败: {url}, 错误: {str(e)}")
                else:
                    logger.warning(f"⚠️ 下载图片异常 (第{attempt+1}次): {url}, 错误: {str(e)}, 准备重试...")
                    continue
        
        # 如果所有重试都失败了
        return None
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """根据content-type获取文件扩展名"""
        mapping = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        
        # 提取主要的内容类型（去除参数）
        main_type = content_type.split(';')[0].strip().lower()
        return mapping.get(main_type, '')
    
    async def _cleanup_downloaded_files(self, file_paths: List[str]) -> None:
        """
        清理下载失败时的临时文件
        
        Args:
            file_paths: 要清理的文件路径列表
        """
        if not file_paths:
            return
        
        cleaned_count = 0
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    cleaned_count += 1
                    logger.debug(f"🗑️ 清理临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ 清理临时文件失败: {file_path}, 错误: {e}")
        
        if cleaned_count > 0:
            logger.info(f"🧹 清理了 {cleaned_count} 个临时文件")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        清理超过指定时间的临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        import time
        current_time = time.time()
        cleaned_count = 0
        
        try:
            for file in self.temp_dir.iterdir():
                if file.is_file():
                    file_age_hours = (current_time - file.stat().st_mtime) / 3600
                    if file_age_hours > max_age_hours:
                        try:
                            file.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"清理文件失败: {file}, 错误: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 清理了 {cleaned_count} 个临时文件")
                
        except Exception as e:
            logger.error(f"清理临时文件出错: {e}")