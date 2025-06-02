# 🌺 小红书MCP工具包

[![构建状态](https://github.com/aki66938/xiaohongshu-mcp-toolkit/workflows/🚀%20构建和发布小红书MCP工具包/badge.svg)](https://github.com/aki66938/xhs-toolkit/actions)
[![最新版本](https://img.shields.io/github/v/release/aki66938/xiaohongshu-mcp-toolkit)](https://github.com/aki66938/xhs-toolkit/releases/latest)
[![许可证](https://img.shields.io/github/license/aki66938/xhs-toolkit)](LICENSE)

一个强大的小红书自动化工具包，支持通过MCP协议与AI客户端（如Claude Desktop等）集成，实现智能内容创作和发布。

## ✨ 主要特性

- 🍪 **Cookie管理**: 安全获取、验证和管理小红书登录凭证
- 🤖 **MCP协议支持**: 与Claude Desktop等AI客户端无缝集成
- 📝 **自动发布**: 支持图文笔记的自动化发布
- 🔍 **内容搜索**: 搜索小红书笔记
- 👤 **用户信息**: 获取用户档案
- 🎯 **统一接口**: 一个工具解决llm操作小红书自动化需求

## 📋 功能清单

- [x] **图文发布** - 支持发布图文笔记
- [ ] **视频发布** - 支持发布视频笔记（开发中）

## 🚀 快速开始

### 一键安装（推荐）

```bash
# 下载并运行安装脚本
curl -sSL https://raw.githubusercontent.com/aki66938/xiaohongshu-mcp-toolkit/main/install.sh | bash

# 或者手动运行
git clone https://github.com/aki66938/xiaohongshu-mcp-toolkit.git
cd xiaohongshu-mcp-toolkit
bash install.sh
```

### 下载使用

1. 从 [Releases页面](https://github.com/aki66938/xhs-toolkit/releases/latest) 下载适合你操作系统的版本
2. 解压并运行：
   ```bash
   # macOS/Linux
   chmod +x xhs-toolkit
   ./xhs-toolkit status
   
   # Windows
   xhs-toolkit.exe status
   ```

### 从源码运行

```bash
git clone https://github.com/aki66938/xiaohongshu-mcp-toolkit.git
cd xiaohongshu-mcp-toolkit
pip install -r requirements.txt
python xhs_toolkit.py status
```

## 📋 环境要求

- **浏览器**: Google Chrome 浏览器
- **驱动**: ChromeDriver (`brew install chromedriver`)

## 🛠️ 使用指南

### 1. 创建配置文件

复制并编辑配置文件：

```bash
cp env_example.txt .env
vim .env  # 编辑配置
```

**必需配置**：
```bash
# Chrome浏览器路径
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ChromeDriver路径  
WEBDRIVER_CHROME_DRIVER="/opt/homebrew/bin/chromedriver"

# 手机号码（用于登录）
phone="您的手机号码"

# Cookies存储路径
json_path="./xhs/cookies"
```

### 2. 获取登录凭证

```bash
./xhs-toolkit cookie save
```

在弹出的浏览器中登录小红书，完成后按回车键保存。

### 3. 启动MCP服务器

```bash
./xhs-toolkit server start
```

### 4. 配置Claude Desktop

在 `~/.claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "command": "curl",
      "args": [
        "-N",
        "-H", "Accept: text/event-stream",
        "http://localhost:8000/sse"
      ]
    }
  }
}
```

## 🔧 主要功能

### MCP工具列表

| 工具名称 | 功能说明 | 参数 |
|---------|----------|------|
| `test_connection` | 测试连接 | 无 |
| `search_xiaohongshu_notes` | 搜索笔记 | keyword, limit |
| `publish_xiaohongshu_note` | 发布笔记 | title, content, tags, images |
| `get_xiaohongshu_user_info` | 获取用户信息 | user_id |

### 快速发布

```bash
# 命令行发布
./xhs-toolkit publish "标题" "内容" --tags "生活,分享"

# 通过Claude发布（推荐）
# 在Claude中：请发布一篇小红书笔记，标题："今日分享"，内容："..."
```

## 🎯 使用场景

- **内容创作者**: 批量发布、数据分析
- **市场营销**: 品牌推广、用户分析
- **AI集成**: 与Claude协作创作内容

## 🔐 安全承诺

- ✅ **本地存储**: 所有数据仅保存在本地
- ✅ **开源透明**: 代码完全开源，可审计
- ✅ **用户控制**: 您完全控制自己的数据

## 🛠️ 常用命令

```bash
# 检查状态
./xhs-toolkit status

# Cookie管理
./xhs-toolkit cookie save      # 获取cookies
./xhs-toolkit cookie validate  # 验证cookies

# 服务器管理
./xhs-toolkit server start     # 启动服务器
./xhs-toolkit server start --port 8080  # 自定义端口
./xhs-toolkit server stop      # 停止服务器
./xhs-toolkit server status    # 检查服务器状态
```

## ⚠️ 重要提示

- **ASGI错误可忽略**：使用`Ctrl+C`停止服务器时出现的ASGI错误是正常现象，不影响功能
- **推荐停止方法**：使用`./xhs-toolkit server stop`命令优雅停止服务器
- **进程清理**：停止时会自动清理ChromeDriver进程

## 🐛 问题反馈

- 查看 [Issues](https://github.com/aki66938/xhs-toolkit/issues)
- 创建 [新Issue](https://github.com/aki66938/xhs-toolkit/issues/new)

## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。

---

<div align="center">
Made with ❤️ for content creators
</div> 
