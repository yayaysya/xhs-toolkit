# Result.txt 文件集成功能

## 概述

小红书MCP服务器现在支持读取 `result.txt` 格式的文件，并自动将内容发布到小红书。这个功能可以处理包含网络图片和文案的JSON文件，支持单个条目和批量条目两种格式。

## 功能特性

- ✅ 支持网络图片URL下载
- ✅ 支持单个和批量条目处理
- ✅ 自动提取标题（从文案第一行）
- ✅ 智能图片排序（封面→内容→结尾）
- ✅ 文件格式验证和预览
- ✅ 异步发布任务管理
- ✅ 详细的错误处理和日志

## 文件格式

### 单个条目格式

```json
{
  "fengmian": "https://example.com/cover.jpg",
  "jiewei": "https://example.com/end.jpg",
  "neirongtu": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
  "wenan": "文案内容..."
}
```

### 批量条目格式

```json
[
  {
    "fengmian": "https://example.com/cover1.jpg",
    "neirongtu": ["https://example.com/img1.jpg"],
    "wenan": "第一条文案内容..."
  },
  {
    "fengmian": "https://example.com/cover2.jpg",
    "neirongtu": ["https://example.com/img2.jpg"],
    "wenan": "第二条文案内容..."
  }
]
```

## 字段说明

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `fengmian` | string | 否 | 封面图片URL |
| `jiewei` | string | 否 | 结尾图片URL |
| `neirongtu` | array/string | 否 | 内容图片URL数组或单个URL |
| `wenan` | string | 是 | 文案内容（必需字段） |

## 可用工具

### 1. preview_result_file

预览result.txt文件内容，不执行发布操作。

```python
# 预览默认的result.txt文件
preview_result_file()

# 预览指定文件
preview_result_file("my_data.txt")
```

**返回信息：**
- 文件基本信息（大小、条目数等）
- 每个条目的解析状态
- 图片数量和内容长度统计
- 格式验证结果和建议

### 2. publish_from_result_file

处理单个result.txt文件并发布到小红书。

```python
# 使用默认文件
publish_from_result_file()

# 指定文件路径和自定义标题
publish_from_result_file("my_data.txt", "我的自定义标题")
```

**参数：**
- `file_path`: 文件路径（默认: "result.txt"）
- `title`: 自定义标题（可选，不提供则从文案中提取）

### 3. batch_publish_from_result_files

批量处理多个条目并发布。

```python
# 处理默认文件，最多5个条目
batch_publish_from_result_files()

# 处理指定文件，最多10个条目
batch_publish_from_result_files("batch_data.txt", 10)
```

**参数：**
- `file_path`: 文件路径（默认: "result.txt"）
- `max_items`: 最大处理条目数（默认: 5）

## 使用流程

### 1. 准备数据文件

创建符合格式的 `result.txt` 文件：

```json
{
  "fengmian": "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/415485d9ef724f46bcaa3fced8697108.png",
  "neirongtu": [
    "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/a26727e8c65a42b0b4dd4580bd5f8ada.png",
    "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e27a6ff6fd6546188bd9e9d8a6240191.png"
  ],
  "wenan": "🧠亲子沟通有妙招，这样说话孩子才会听\n\n各位家长好，我是小燕老师..."
}
```

### 2. 预览文件内容

```python
# 预览文件，检查格式是否正确
result = preview_result_file("result.txt")
print(result)
```

### 3. 发布内容

```python
# 发布单个条目
task_id = publish_from_result_file("result.txt")

# 检查发布状态
status = check_task_status(task_id)

# 获取发布结果
result = get_task_result(task_id)
```

### 4. 批量发布

```python
# 批量发布多个条目
batch_result = batch_publish_from_result_files("result_batch.txt", 3)

# 检查所有任务状态
for task_id in batch_result["task_ids"]:
    status = check_task_status(task_id)
    print(f"任务 {task_id}: {status}")
```

## 错误处理

### 常见错误及解决方案

1. **文件不存在**
   ```
   错误: 文件不存在: result.txt
   解决: 检查文件路径是否正确
   ```

2. **JSON格式错误**
   ```
   错误: JSON解析失败: Expecting property name enclosed in double quotes
   解决: 检查JSON格式，确保使用双引号
   ```

3. **缺少必需字段**
   ```
   错误: 缺少必需字段: ['wenan']
   解决: 确保每个条目都包含wenan字段
   ```

4. **图片数量超限**
   ```
   警告: 图片数量(12)超过小红书限制(9张)
   解决: 系统会自动截取前9张图片
   ```

## 注意事项

1. **图片限制**: 小红书最多支持9张图片，超出会自动截取
2. **文案长度**: 建议控制在1000字符以内
3. **网络图片**: 支持HTTP/HTTPS链接，会自动下载到本地
4. **异步处理**: 发布任务在后台执行，使用任务ID跟踪进度
5. **文件编码**: 确保文件使用UTF-8编码

## 示例文件

项目根目录包含以下示例文件：

- `result.txt`: 单个条目示例
- `result_batch_example.txt`: 批量条目示例

## 技术支持

如果遇到问题，请检查：

1. 文件格式是否符合JSON规范
2. 网络图片URL是否可访问
3. 文案内容是否包含必需字段
4. 小红书登录状态是否有效

使用 `preview_result_file()` 工具可以帮助诊断文件格式问题。 