@echo off
:: 小红书工具包 - Windows 启动脚本

cd /d "%~dp0"

:: 检查是否有参数
if "%~1"=="" (
    :: 无参数，启动交互式界面
    if exist ".venv\Scripts\python.exe" (
        .venv\Scripts\python.exe xhs_toolkit_interactive.py
    ) else if exist "venv\Scripts\python.exe" (
        venv\Scripts\python.exe xhs_toolkit_interactive.py
    ) else (
        python xhs_toolkit_interactive.py || python3 xhs_toolkit_interactive.py || py xhs_toolkit_interactive.py
    )
) else (
    :: 有参数，执行传统命令
    if exist ".venv\Scripts\python.exe" (
        .venv\Scripts\python.exe xhs_toolkit.py %*
    ) else if exist "venv\Scripts\python.exe" (
        venv\Scripts\python.exe xhs_toolkit.py %*
    ) else (
        python xhs_toolkit.py %* || python3 xhs_toolkit.py %* || py xhs_toolkit.py %*
    )
)