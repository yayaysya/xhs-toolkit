# 🌺 小红书MCP工具包

[![许可证](https://img.shields.io/github/license/aki66938/xhs-toolkit)](LICENSE)
[![微信公众号](https://img.shields.io/badge/凯隐的无人化生产矩阵-公众号-bule?style=flat-square&logo=wechat)](src/static/qrcode_for_gh_19088e185f66_258.jpg)

一个强大的小红书自动化工具包，支持通过MCP协议与AI客户端（如Claude Desktop等）集成，实现智能内容创作和发布。

## ✨ 主要特性

- 🍪 **Cookie管理**: 安全获取、验证和管理小红书登录凭证
- 🤖 **MCP协议支持**: 与Claude Desktop等AI客户端无缝集成
- 📝 **自动发布**: 支持图文笔记的自动化发布
- 👤 **用户信息**: 获取用户档案
- 🎯 **统一接口**: 一个工具解决llm操作小红书自动化需求

## 📋 功能清单

- [x] **图文发布** - 支持发布图文笔记
- [ ] **视频发布** - 支持发布视频笔记（开发中）
- [ ] **内容搜索** - 支持指定搜索（开发计划中）

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
cp env_example .env
vim .env  # 编辑配置
```

**必需配置**：
```bash
# Chrome浏览器路径
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ChromeDriver路径  
WEBDRIVER_CHROME_DRIVER="/opt/homebrew/bin/chromedriver"

# Cookies存储路径
json_path="./xhs/cookies"
```

### 2. 获取登录凭证（改进版本）

```bash
./xhs-toolkit cookie save
```

**重要改进**：新版本直接获取创作者中心权限cookies，解决跳转失效问题

在弹出的浏览器中：
1. 登录小红书创作者中心
2. 确保能正常访问创作者中心功能
3. 建议点击进入【发布笔记】页面，确认权限完整
4. 完成后按回车键保存

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
# 在Claude（或者其他Ai agent）的提示词中：请发布一篇小红书笔记，标题："今日分享"，内容："..."，图片路径："图片所在路径包含图片的文件名（例如：/User/me/xhs/poster.png）"
```

发布原理：
手工上传过程中，浏览器会弹窗让用户选中文件路径
告诉ai路径位置，ai会把路径参数对应丢给mcp的参数中，完成上传动作

## 🎯 使用场景

- **内容创作者**: 自动发布（未完成）
- **市场营销**: 用户分析（未完成）
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


## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。

---

<div align="center">
Made with ❤️ for content creators
</div> 
