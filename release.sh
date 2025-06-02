#!/bin/bash

# 小红书MCP工具包发布脚本

set -e

echo "🌺 小红书MCP工具包发布脚本"
echo "================================"

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

# 提供版本选项
echo ""
echo "🔢 版本选择:"
echo "1. 发布当前版本 v$CURRENT_VERSION"
echo "2. 自动递增版本号（补丁版本）"
echo "3. 手动输入新版本号"
echo "4. 取消发布"
echo ""

read -p "请选择 (1-4): " choice

case $choice in
    1)
        NEW_VERSION=$CURRENT_VERSION
        ;;
    2)
        # 自动递增补丁版本
        IFS='.' read -ra ADDR <<< "$CURRENT_VERSION"
        MAJOR=${ADDR[0]}
        MINOR=${ADDR[1]}
        PATCH=${ADDR[2]}
        PATCH=$((PATCH + 1))
        NEW_VERSION="$MAJOR.$MINOR.$PATCH"
        echo "📈 新版本: v$NEW_VERSION"
        ;;
    3)
        read -p "🔢 请输入新版本号（如 1.0.1）: " NEW_VERSION
        if [[ ! $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "❌ 错误: 版本号格式不正确，应为 x.y.z"
            exit 1
        fi
        ;;
    4)
        echo "❌ 取消发布"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 检查标签是否已存在
if git tag -l | grep -q "^v$NEW_VERSION$"; then
    echo "❌ 错误: 标签 v$NEW_VERSION 已存在"
    exit 1
fi

# 如果版本号变化，更新version.txt
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    echo "$NEW_VERSION" > version.txt
    echo "📝 更新version.txt到 v$NEW_VERSION"
    
    # 提交版本文件变更
    git add version.txt
    git commit -m "🔖 Bump version to $NEW_VERSION"
    echo "📤 推送版本更新到main分支..."
    git push origin main
fi

echo ""
echo "🔍 准备发布版本 v$NEW_VERSION"
echo "📋 发布内容:"
echo "   - 版本标签: v$NEW_VERSION"
echo "   - 自动构建: Linux x64, Windows x64, macOS x64"
echo "   - 自动发布到GitHub Releases"
echo ""

read -p "🚀 确认发布? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消发布"
    exit 0
fi

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

echo "📤 推送标签到远程仓库..."
git push origin "v$NEW_VERSION"

echo ""
echo "🎉 发布完成!"
echo "📋 版本: v$NEW_VERSION"
echo "🏷️  标签: v$NEW_VERSION"
echo "🤖 GitHub Actions正在自动构建..."
echo ""
echo "🔗 查看构建状态: https://github.com/aki66938/xiaohongshu-mcp-toolkit/actions"
echo "📦 发布页面: https://github.com/aki66938/xiaohongshu-mcp-toolkit/releases"
echo ""
echo "⏰ 构建预计需要5-10分钟..."
echo "�� 构建完成后将自动创建Release" 