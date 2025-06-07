"""
小红书相关数据模型

定义小红书笔记、用户、搜索结果等数据结构
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from ..utils.text_utils import validate_note_content, parse_tags_string, parse_file_paths_string


class XHSNote(BaseModel):
    """小红书笔记数据模型"""
    
    title: str
    content: str
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    
    @validator('title')
    def validate_title(cls, v):
        """验证标题"""
        if not v or not v.strip():
            raise ValueError("标题不能为空")
        if len(v.strip()) > 50:
            raise ValueError("标题长度不能超过50个字符")
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """验证内容"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        if len(v.strip()) > 1000:
            raise ValueError("内容长度不能超过1000个字符")
        return v.strip()
    
    @validator('images')
    def validate_images(cls, v):
        """验证图片列表"""
        if v is None:
            return v
        
        # 限制图片数量
        if len(v) > 9:
            raise ValueError("图片数量不能超过9张")
        
        # 检查路径格式
        import os
        for image_path in v:
            if not os.path.isabs(image_path):
                raise ValueError(f"图片路径必须是绝对路径: {image_path}")
            if not os.path.exists(image_path):
                raise ValueError(f"图片文件不存在: {image_path}")
        
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签列表"""
        if v is None:
            return v
        
        # 限制标签数量
        if len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        
        # 检查标签长度
        for tag in v:
            if len(tag) > 20:
                raise ValueError(f"标签长度不能超过20个字符: {tag}")
        
        return v
    
    @classmethod
    def from_strings(cls, title: str, content: str, tags_str: str = "", 
                    location: str = "", images_str: str = "") -> 'XHSNote':
        """
        从字符串参数创建笔记对象
        
        Args:
            title: 笔记标题
            content: 笔记内容
            tags_str: 标签字符串（逗号分隔）
            location: 位置信息
            images_str: 图片路径字符串（逗号分隔）
            
        Returns:
            XHSNote实例
        """
        tag_list = parse_tags_string(tags_str) if tags_str else None
        image_list = parse_file_paths_string(images_str) if images_str else None
        
        return cls(
            title=title,
            content=content,
            images=image_list,
            tags=tag_list,
            location=location if location else None
        )


class XHSSearchResult(BaseModel):
    """搜索结果数据模型"""
    
    note_id: str
    title: str
    author: str
    likes: int
    url: str
    thumbnail: Optional[str] = None
    
    @validator('note_id')
    def validate_note_id(cls, v):
        """验证笔记ID"""
        if not v or not v.strip():
            raise ValueError("笔记ID不能为空")
        return v.strip()
    
    @validator('likes')
    def validate_likes(cls, v):
        """验证点赞数"""
        if v < 0:
            raise ValueError("点赞数不能为负数")
        return v


class XHSUser(BaseModel):
    """小红书用户数据模型"""
    
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    notes_count: Optional[int] = None
    
    @validator('followers', 'following', 'notes_count')
    def validate_counts(cls, v):
        """验证计数字段"""
        if v is not None and v < 0:
            raise ValueError("计数不能为负数")
        return v


class XHSPublishResult(BaseModel):
    """发布结果数据模型"""
    
    success: bool
    message: str
    note_title: Optional[str] = None
    final_url: Optional[str] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "note_title": self.note_title,
            "final_url": self.final_url,
            "error_type": self.error_type
        }


class CookieInfo(BaseModel):
    """Cookie信息数据模型"""
    
    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False
    expiry: Optional[int] = None
    
    @validator('name', 'value', 'domain')
    def validate_required_fields(cls, v):
        """验证必需字段"""
        if not v or not v.strip():
            raise ValueError("Cookie的name、value、domain字段不能为空")
        return v.strip()


class CookiesData(BaseModel):
    """Cookies数据容器"""
    
    cookies: List[CookieInfo]
    saved_at: str
    domain: str = "creator.xiaohongshu.com"
    critical_cookies_found: List[str] = []
    version: str = "2.0"
    
    @validator('cookies')
    def validate_cookies_list(cls, v):
        """验证cookies列表"""
        if not v:
            raise ValueError("cookies列表不能为空")
        return v
    
    def get_critical_cookies(self) -> List[str]:
        """获取关键cookies列表"""
        critical_names = [
            'web_session', 'a1', 'gid', 'webId', 
            'customer-sso-sid', 'x-user-id-creator.xiaohongshu.com',
            'access-token-creator.xiaohongshu.com', 'galaxy_creator_session_id',
            'galaxy.creator.beaker.session.id'
        ]
        
        found_critical = []
        for cookie in self.cookies:
            if cookie.name in critical_names:
                found_critical.append(cookie.name)
        
        return found_critical
    
    def is_valid(self) -> bool:
        """检查cookies是否有效"""
        critical_cookies = self.get_critical_cookies()
        # 至少需要前4个基础cookies中的3个
        required_basic = ['web_session', 'a1', 'gid', 'webId']
        found_basic = [name for name in critical_cookies if name in required_basic]
        
        return len(found_basic) >= 3


# 创作者中心关键cookies
CRITICAL_CREATOR_COOKIES = [
    'web_session', 'a1', 'gid', 'webId', 
    'customer-sso-sid', 'x-user-id-creator.xiaohongshu.com',
    'access-token-creator.xiaohongshu.com', 'galaxy_creator_session_id',
    'galaxy.creator.beaker.session.id'
] 