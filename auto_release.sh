#!/bin/bash

# 小红书MCP工具包自动发布脚本
# 适用于CI/CD环境或完全自动化发布

set -e

echo "🌺 小红书MCP工具包自动发布脚本"
echo "================================"

# 检查参数
BUMP_TYPE=${1:-patch}  # major, minor, patch

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "❌ 错误: 无效的版本递增类型: $BUMP_TYPE"
    echo "📋 用法: $0 [major|minor|patch]"
    echo "   major: 1.0.0 -> 2.0.0"
    echo "   minor: 1.0.0 -> 1.1.0"
    echo "   patch: 1.0.0 -> 1.0.1"
    exit 1
fi

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 不在git仓库中"
    exit 1
fi

# 检查工作目录是否干净
if ! git diff-index --quiet HEAD --; then
    echo "❌ 错误: 工作目录有未提交的变更"
    echo "请先提交所有变更后再发布"
    exit 1
fi

# 获取当前版本
if [ -f "version.txt" ]; then
    CURRENT_VERSION=$(cat version.txt | tr -d '[:space:]')
    echo "📋 当前版本: v$CURRENT_VERSION"
else
    echo "❌ 错误: 未找到version.txt文件"
    exit 1
fi

# 自动计算新版本号
IFS='.' read -ra ADDR <<< "$CURRENT_VERSION"
MAJOR=${ADDR[0]}
MINOR=${ADDR[1]}
PATCH=${ADDR[2]}

case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "📈 新版本: v$NEW_VERSION ($BUMP_TYPE 递增)"

# 检查标签是否已存在
if git tag -l | grep -q "^v$NEW_VERSION$"; then
    echo "❌ 错误: 标签 v$NEW_VERSION 已存在"
    exit 1
fi

# 更新版本文件
echo "$NEW_VERSION" > version.txt
echo "📝 更新version.txt到 v$NEW_VERSION"

# 提交版本文件变更
git add version.txt
git commit -m "🔖 Bump version to $NEW_VERSION"
echo "📤 推送版本更新到main分支..."
git push origin main

# 创建标签
echo "🏷️  创建标签 v$NEW_VERSION..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION

🌺 小红书MCP工具包 v$NEW_VERSION

✨ 主要特性:
- 支持小红书图文笔记自动发布
- 完整的MCP协议支持，与Claude Desktop无缝集成
- 智能Cookie管理和验证
- 多平台二进制文件支持

📦 构建平台:
- Linux x64
- Windows x64  
- macOS x64

🔗 项目地址: https://github.com/aki66938/xiaohongshu-mcp-toolkit"

# 推送标签
echo "📤 推送标签到远程仓库..."
git push origin "v$NEW_VERSION"

echo ""
echo "🎉 自动发布完成!"
echo "📋 版本: v$NEW_VERSION"
echo "🏷️  标签: v$NEW_VERSION"
echo "🤖 GitHub Actions正在自动构建..."
echo ""
echo "🔗 查看构建状态: https://github.com/aki66938/xiaohongshu-mcp-toolkit/actions"
echo "📦 发布页面: https://github.com/aki66938/xiaohongshu-mcp-toolkit/releases"
echo ""
echo "⏰ 构建预计需要5-10分钟..."
echo "�� 构建完成后将自动创建Release" 