# 📕 小红书MCP工具包 v1.2.1 - 发布说明

## 修复说明
🔧 修复pandas依赖打包问题

- 从PyInstaller excludes中移除pandas和numpy
- 在hiddenimports中明确添加pandas及其依赖
- 修复可执行文件运行时'no module named pandas'错误"

## MCP工具列表

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