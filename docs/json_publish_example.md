# JSON发布功能使用示例

## 概述

小红书MCP工具包现在支持通过JSON字符串直接发布内容，无需依赖文件读取。这提供了更可靠和灵活的发布方式。

## 可用工具

### 1. publish_from_json
- **功能**: 通过JSON字符串发布单个内容到小红书
- **参数**:
  - `json_data`: JSON格式的字符串，包含发布内容
  - `title`: 自定义标题（可选，不提供则从文案中提取）

### 2. batch_publish_from_json
- **功能**: 批量处理JSON字符串中的多个数据条目并发布到小红书
- **参数**:
  - `json_data`: JSON格式的字符串，包含多个发布条目
  - `max_items`: 最大处理条目数（默认: 5）

### 3. preview_json_data
- **功能**: 预览JSON数据内容，不执行发布操作
- **参数**:
  - `json_data`: JSON格式的字符串

## JSON数据格式

### 单个条目格式
```json
{
  "fengmian": "https://example.com/cover.jpg",
  "neirongtu": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
  "zongjie": "https://example.com/summary.jpg",
  "jiewei": "https://example.com/end.jpg",
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

- **fengmian**: 封面图片URL（可选）
- **neirongtu**: 内容图片URL数组（可选）
- **zongjie**: 总结图片URL（可选，在内容图之后，结尾图之前）
- **jiewei**: 结尾图片URL（可选）
- **wenan**: 文案内容（必需）

## 使用示例

### 示例1: 发布单个内容

```python
# JSON数据
json_data = {
    "fengmian": "https://via.placeholder.com/800x600/FF0000/FFFFFF?text=Cover",
    "neirongtu": [
        "https://via.placeholder.com/800x600/00FF00/FFFFFF?text=Content1",
        "https://via.placeholder.com/800x600/0000FF/FFFFFF?text=Content2"
    ],
    "zongjie": "https://via.placeholder.com/800x600/FF00FF/FFFFFF?text=Summary",
    "jiewei": "https://via.placeholder.com/800x600/FFFF00/000000?text=End",
    "wenan": "这是一个测试发布\n\n今天天气很好，适合出门走走。\n\n#测试 #小红书 #发布"
}

# 发布内容
result = await publish_from_json(json.dumps(json_data))
```

### 示例2: 批量发布内容

```python
# 批量JSON数据
json_data = [
    {
        "fengmian": "https://via.placeholder.com/800x600/FF0000/FFFFFF?text=Cover1",
        "neirongtu": ["https://via.placeholder.com/800x600/00FF00/FFFFFF?text=Content1"],
        "wenan": "第一条测试内容\n\n这是第一条测试发布的内容。\n\n#测试1 #小红书"
    },
    {
        "fengmian": "https://via.placeholder.com/800x600/0000FF/FFFFFF?text=Cover2",
        "neirongtu": ["https://via.placeholder.com/800x600/FFFF00/000000?text=Content2"],
        "wenan": "第二条测试内容\n\n这是第二条测试发布的内容。\n\n#测试2 #小红书"
    }
]

# 批量发布内容
result = await batch_publish_from_json(json.dumps(json_data), max_items=2)
```

### 示例3: 预览JSON数据

```python
# 预览JSON数据
result = await preview_json_data(json.dumps(json_data))
```

## 使用流程

1. **登录小红书**: 使用 `login_xiaohongshu()` 登录小红书
2. **预览数据**: 使用 `preview_json_data()` 预览JSON数据内容
3. **发布内容**: 使用 `publish_from_json()` 或 `batch_publish_from_json()` 发布内容
4. **查看进度**: 使用 `check_task_status()` 查看发布进度
5. **获取结果**: 使用 `get_task_result()` 获取发布结果

## 优势

1. **更可靠**: 避免了文件读取可能出现的问题
2. **更灵活**: 可以直接在代码中构造JSON数据
3. **更高效**: 减少了文件I/O操作
4. **更安全**: 避免了文件路径和权限问题

## 注意事项

1. **图片数量限制**: 小红书最多支持9张图片，超过会自动截取前9张
2. **文案必需**: `wenan` 字段是必需的，不能为空
3. **URL格式**: 图片URL必须是有效的网络地址
4. **批量限制**: 批量发布默认最多处理5个条目，可通过 `max_items` 参数调整 