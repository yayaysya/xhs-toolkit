# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, '../src')

# 收集src目录下的所有模块
def collect_src_modules():
    """收集src目录下的所有Python模块"""
    modules = []
    src_path = Path('../src')
    
    for py_file in src_path.rglob('*.py'):
        if py_file.name != '__init__.py':
            # 转换为模块路径格式
            module_path = str(py_file.with_suffix('')).replace(os.sep, '.')
            modules.append(module_path)
            print(f"发现模块: {module_path}")
    
    return modules

# 收集隐藏导入
hidden_imports = [
    # 标准库
    'asyncio',
    'json',
    'os',
    'sys',
    'time',
    'pathlib',
    'argparse',
    'platform',
    'subprocess',
    'signal',
    'uuid',  # 新增：异步任务ID生成
    'socket',  # 新增：网络功能
    'dataclasses',  # 新增：任务数据类
    
    # 第三方库
    'dotenv',
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.common.exceptions',
    'fastmcp',
    'fastmcp.server',
    'fastmcp.utilities',  # 新增：FastMCP工具类
    'loguru',
    'pydantic',
    'pydantic.dataclasses',
    'DrissionPage',
    'DrissionPage.chromium',
    'requests',
    'aiohttp',  # 新增：异步HTTP客户端
    'asyncio.exceptions',  # 新增：异步异常处理
    
    # 数据处理库 - 项目实际使用
    'pandas',
    'numpy',  # pandas的依赖
    'pytz',   # pandas的时区处理依赖
    'dateutil',  # pandas的日期处理依赖
    
    # 收集src目录下的所有模块
    *collect_src_modules()
]

# 数据文件
datas = [
    ('../env_example', '.'),
    ('../src', 'src'),
    ('../README.md', '.'),
    ('../LICENSE', '.'),
]

a = Analysis(
    ['../xhs_toolkit.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        # 'numpy',  # pandas依赖numpy，不能排除
        # 'pandas',  # 项目实际使用pandas，不能排除
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='xhs-toolkit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 