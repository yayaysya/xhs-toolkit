# 🚀 发布指南

本项目提供了两种发布方式：交互式发布和自动化发布。

## 📋 发布工作流说明

### 🤖 自动化触发条件

GitHub Actions会在以下情况自动触发：

1. **代码质量检查** - 推送到`main`分支或创建PR时
2. **构建测试** - 推送到`main`分支时构建但不发布
3. **正式发布** - 推送版本标签（如`v1.0.0`）时自动构建并发布

### 🛠️ 发布脚本

#### 1. 交互式发布（推荐）
```bash
./release.sh
```

**功能特性：**
- 📊 显示当前版本
- 🔢 提供多种版本选择：
  - 发布当前版本
  - 自动递增补丁版本（1.0.0 → 1.0.1）
  - 手动输入新版本号
- ✅ 安全检查（工作目录、重复标签）
- 🔒 确认提示，避免误操作

#### 2. 自动化发布
```bash
# 补丁版本递增（默认）1.0.0 → 1.0.1
./auto_release.sh

# 小版本递增 1.0.0 → 1.1.0  
./auto_release.sh minor

# 大版本递增 1.0.0 → 2.0.0
./auto_release.sh major
```

**适用场景：**
- CI/CD环境
- 自动化脚本
- 批量发布

## 🔄 完整发布流程

### 准备阶段
1. **确保代码已提交**
   ```bash
   git status  # 检查工作目录
   git add .
   git commit -m "准备发布"
   git push origin main
   ```

2. **检查当前版本**
   ```bash
   cat version.txt  # 查看当前版本
   ```

### 发布阶段
1. **选择发布方式**
   ```bash
   # 交互式（推荐新手）
   ./release.sh
   
   # 自动化（推荐CI/CD）
   ./auto_release.sh patch
   ```

2. **自动化流程**
   - 📝 更新`version.txt`
   - 🔖 创建版本标签
   - 📤 推送到GitHub
   - 🤖 触发自动构建
   - 📦 自动创建Release

### 验证阶段
1. **检查构建状态**
   - 访问：https://github.com/aki66938/xiaohongshu-mcp-toolkit/actions
   - 查看构建进度和日志

2. **确认发布结果**
   - 访问：https://github.com/aki66938/xiaohongshu-mcp-toolkit/releases
   - 下载测试构建产物

## 🎯 版本命名规范

遵循 [语义化版本控制](https://semver.org/lang/zh-CN/) 规范：

- **MAJOR.MINOR.PATCH** （如：1.2.3）
- **MAJOR**：不兼容的API修改
- **MINOR**：向下兼容的功能性新增
- **PATCH**：向下兼容的问题修正

### 示例
- `1.0.0` → `1.0.1`：Bug修复
- `1.0.0` → `1.1.0`：新功能
- `1.0.0` → `2.0.0`：重大更新

## ⚠️ 注意事项

1. **发布前检查**
   - ✅ 代码已测试
   - ✅ 文档已更新
   - ✅ 工作目录干净

2. **版本标签唯一性**
   - 每个版本只能发布一次
   - 如需重新发布，需要递增版本号

3. **构建时间**
   - 多平台构建需要5-10分钟
   - 请耐心等待构建完成

4. **回滚处理**
   ```bash
   # 如需删除错误的标签
   git tag -d v1.0.1
   git push origin :refs/tags/v1.0.1
   ```

## 🔧 故障排除

### 常见问题

1. **标签已存在**
   ```
   ❌ 错误: 标签 v1.0.0 已存在
   ```
   **解决**：使用新的版本号

2. **工作目录不干净**
   ```
   ❌ 错误: 工作目录有未提交的变更
   ```
   **解决**：先提交所有变更

3. **构建失败**
   - 检查GitHub Actions日志
   - 确认依赖安装正确
   - 验证代码语法无误

### 获取帮助

- 📖 查看完整文档：[README.md](README.md)
- 🐛 报告问题：[Issues](https://github.com/aki66938/xiaohongshu-mcp-toolkit/issues)
- 💬 讨论交流：[Discussions](https://github.com/aki66938/xiaohongshu-mcp-toolkit/discussions) 