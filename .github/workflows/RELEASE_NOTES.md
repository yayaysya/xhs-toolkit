# 📕 小红书MCP工具包 v1.2.0 - 发布说明

> 🎯 **数据分析功能** - 新增创作者数据采集与AI分析功能

## 新增功能

### 📊 数据采集与分析
- **自动数据采集**: 支持仪表板、内容分析、粉丝数据的自动采集
- **中文数据表头**: CSV文件使用中文表头，便于AI理解和分析
- **AI数据分析**: 新增 `get_creator_data_analysis` MCP工具，供AI分析账号表现
- **定时任务**: 支持cron表达式的定时数据采集（env环境变量中修改）
- **数据存储**: 数据存储在 `data/creator_db/` 目录，目前仅支持csv本地存储，目录：./data/creator_db

### 🔧 功能优化
- **MCP工具精简**: 移除冗余的数据采集状态工具，保留核心分析功能
- **目录结构优化**: 数据目录从 `csv` 重命名为 `creator_db`，更好地反映用途

## 🎯 使用场景

现在AI可以：
1. 调用 `get_creator_data_analysis` 获取完整的创作者数据
2. 基于中文表头准确理解数据含义
3. 提供数据驱动的内容优化建议
4. 分析账号表现趋势和粉丝增长情况

## 📋 MCP工具列表

| 工具名称 | 功能说明 |
|---------|----------|
| `test_connection` | 测试MCP连接 |
| `start_publish_task` | 启动异步发布任务 |
| `check_task_status` | 检查任务状态 |
| `get_task_result` | 获取任务结果 |
| `close_browser` | 关闭浏览器 |
| `test_publish_params` | 测试发布参数 |
| `get_creator_data_analysis` | 获取创作者数据分析 |

**enjoy it！**