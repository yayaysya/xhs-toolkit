"""
小红书工具包文本处理工具模块

提供文本清理、格式化等工具函数
"""

import re
from typing import List, Optional


def clean_text_for_browser(text: str) -> str:
    """
    清理文本中ChromeDriver不支持的字符
    
    ChromeDriver只支持BMP(Basic Multilingual Plane)字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
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
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    # 确保后缀不会超过最大长度
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def parse_tags_string(tags_string: str) -> List[str]:
    """
    解析标签字符串
    
    Args:
        tags_string: 标签字符串，用逗号分隔
        
    Returns:
        标签列表
    """
    if not tags_string:
        return []
    
    # 分割并清理标签
    tags = [tag.strip() for tag in tags_string.split(",") if tag.strip()]
    
    # 移除重复标签（保持顺序）
    unique_tags = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)
    
    return unique_tags


def parse_file_paths_string(paths_string: str) -> List[str]:
    """
    解析文件路径字符串
    
    Args:
        paths_string: 文件路径字符串，用逗号分隔
        
    Returns:
        文件路径列表
    """
    if not paths_string:
        return []
    
    # 分割并清理路径
    paths = [path.strip() for path in paths_string.split(",") if path.strip()]
    
    return paths


def validate_note_content(title: str, content: str) -> List[str]:
    """
    验证笔记内容
    
    Args:
        title: 笔记标题
        content: 笔记内容
        
    Returns:
        验证错误列表，空列表表示验证通过
    """
    errors = []
    
    # 检查标题
    if not title or not title.strip():
        errors.append("标题不能为空")
    elif len(title.strip()) > 50:
        errors.append("标题长度不能超过50个字符")
    
    # 检查内容
    if not content or not content.strip():
        errors.append("内容不能为空")
    elif len(content.strip()) > 1000:
        errors.append("内容长度不能超过1000个字符")
    
    return errors


def safe_print(text: str) -> None:
    """
    安全打印函数，处理Windows下的Unicode编码问题
    
    Args:
        text: 要打印的文本
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # 替换常见的emoji字符为文本
        replacements = {
            '🔧': '[配置]',
            '✅': '[成功]',  
            '❌': '[失败]',
            '⚠️': '[警告]',
            '🍪': '[Cookie]',
            '🚀': '[启动]',
            '🛑': '[停止]',
            '🔍': '[检查]',
            '📝': '[笔记]',
            '📊': '[状态]',
            '💻': '[系统]',
            '🐍': '[Python]',
            '💡': '[提示]',
            '📄': '[文件]',
            '🧪': '[测试]',
            '📱': '[发布]',
            '🎉': '[完成]',
            '🌺': '[小红书]',
            '🧹': '[清理]',
            '👋': '[再见]',
            '📡': '[信号]'
        }
        
        safe_text = text
        for emoji, replacement in replacements.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        print(safe_text) 