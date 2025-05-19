# XpertFormat 数据集格式规范

XpertFormat 是 XpertEval 框架中使用的统一数据集格式，设计用于支持各种评测任务，包括文本问答、选择题、数学问题、代码生成以及多模态任务。本文档详细说明了 XpertFormat 的规范和使用方法。

## 1. 基本格式

XpertFormat 使用 JSONL（JSON Lines）格式，每行包含一个完整的 JSON 对象，代表一个评测样本。基本结构如下：

```json
{
  "id": "样本唯一标识符",
  "query": "问题文本",
  "response": "参考答案或标准答案",
  "history": [  // 可选，用于多轮对话
    {"role": "human", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ],
  "files": [  // 可选，用于多模态内容
    {"path": "相对或绝对路径", "type": "image|audio|video", "description": "可选描述"}
  ],
  "choices": [  // 可选，用于选择题
    {"id": "A", "content": "选项A内容"},
    {"id": "B", "content": "选项B内容"},
    {"id": "C", "content": "选项C内容"},
    {"id": "D", "content": "选项D内容"}
  ],
  "answer": {  // 统一的答案字段
    "type": "choice|text|code|step_by_step",  // 答案类型
    "value": "A",  // 选择题答案、文本答案或代码
    "explanation": "解释或分步解答"  // 可选的解释
  },
  "meta": {  // 元数据
    "task_type": "qa|choice|code|math|vision|audio|multi",  // 任务类型
    "category": "主题/类别",
    "subject": "学科领域",
    "difficulty": "难度级别",
    "source": "数据集来源",
    "tags": ["标签1", "标签2"]  // 可选的标签列表
  },
  "evaluation": {  // 评估相关信息，可选
    "metrics": ["accuracy", "bleu"],  // 适用的评估指标
    "scoring_criteria": "评分标准描述"
  }
}
```

## 2. 必需字段

每个样本必须包含以下字段：

- `id`: 样本的唯一标识符，字符串类型
- `query`: 问题或提示文本，字符串类型
- `response`: 参考答案或标准答案，字符串类型

## 3. 可选字段

根据任务类型和需求，可以包含以下可选字段：

### 3.1 多轮对话支持

对于多轮对话任务，可以使用 `history` 字段存储对话历史：

```json
"history": [
  {"role": "human", "content": "你好，请介绍一下自己"},
  {"role": "assistant", "content": "我是一个AI助手，可以回答您的问题"},
  {"role": "human", "content": "你能做什么?"}
]
```

### 3.2 多模态内容支持

对于包含图像、音频或视频的任务，可以使用 `files` 字段引用相关文件：

```json
"files": [
  {"path": "images/sample1.jpg", "type": "image", "description": "一张猫的照片"},
  {"path": "audio/sample1.mp3", "type": "audio", "description": "一段语音"}
]
```

文件路径可以是相对路径或绝对路径，建议使用相对于数据集根目录的相对路径。

### 3.3 选择题支持

对于选择题，可以使用 `choices` 字段列出选项：

```json
"choices": [
  {"id": "A", "content": "选项A内容"},
  {"id": "B", "content": "选项B内容"},
  {"id": "C", "content": "选项C内容"},
  {"id": "D", "content": "选项D内容"}
]
```

### 3.4 结构化答案

使用 `answer` 字段提供结构化的答案信息：

```json
"answer": {
  "type": "choice",
  "value": "A",
  "explanation": "选择A是因为..."
}
```

答案类型包括：
- `choice`: 选择题答案
- `text`: 文本答案
- `code`: 代码答案
- `step_by_step`: 分步解答（如数学问题）

### 3.5 元数据

使用 `meta` 字段提供样本的元数据：

```json
"meta": {
  "task_type": "choice",
  "category": "科学",
  "subject": "物理",
  "difficulty": "中等",
  "source": "MMLU数据集",
  "tags": ["多选题", "物理学"]
}
```

## 4. 任务类型特定格式

### 4.1 选择题格式

```json
{
  "id": "choice_1",
  "query": "下列哪项是正确的?",
  "choices": [
    {"id": "A", "content": "选项A内容"},
    {"id": "B", "content": "选项B内容"},
    {"id": "C", "content": "选项C内容"},
    {"id": "D", "content": "选项D内容"}
  ],
  "answer": {
    "type": "choice",
    "value": "A"
  },
  "meta": {
    "task_type": "choice",
    "category": "科学",
    "subject": "物理"
  }
}
```

### 4.2 数学问题格式

```json
{
  "id": "math_1",
  "query": "计算 5x + 3 = 18 中的 x 值",
  "response": "x = 3",
  "answer": {
    "type": "step_by_step",
    "value": "3",
    "explanation": "5x + 3 = 18\n5x = 15\nx = 3"
  },
  "meta": {
    "task_type": "math",
    "difficulty": "简单"
  }
}
```

### 4.3 代码生成格式

```json
{
  "id": "code_1",
  "query": "编写一个函数，计算斐波那契数列的第n项",
  "response": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "answer": {
    "type": "code",
    "value": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
  },
  "meta": {
    "task_type": "code",
    "programming_language": "python"
  },
  "evaluation": {
    "metrics": ["functional_correctness", "code_quality"]
  }
}
```

### 4.4 多模态问答格式

```json
{
  "id": "vision_1",
  "query": "描述这张图片中的内容",
  "files": [
    {"path": "images/cat.jpg", "type": "image"}
  ],
  "response": "这是一只橙色的猫咪，正在草地上休息",
  "meta": {
    "task_type": "vision"
  }
}
```

## 5. 数据集目录结构

建议的数据集目录结构如下：

```
dataset_name/
├── dataset.jsonl       # 主数据集文件
├── train.jsonl         # 训练集分割（可选）
├── dev.jsonl           # 验证集分割（可选）
├── test.jsonl          # 测试集分割（可选）
├── media/              # 媒体文件目录
│   ├── images/         # 图像文件
│   ├── audio/          # 音频文件
│   └── video/          # 视频文件
├── original/           # 原始格式数据（可选）
└── README.md           # 数据集说明文件
```

## 6. 验证工具

XpertEval 提供了数据集格式验证工具，可以检查数据集是否符合 XpertFormat 规范：

```python
from xperteval.datasets.converters.format_validator import validate_xpert_format

# 验证单个样本
sample = {...}  # 样本JSON对象
is_valid, errors = validate_xpert_format(sample)
if not is_valid:
    print(f"验证失败: {errors}")

# 验证整个数据集文件
from xperteval.datasets.converters.format_validator import validate_xpert_format_file
is_valid, errors = validate_xpert_format_file("path/to/dataset.jsonl")
if not is_valid:
    print(f"数据集验证失败: {errors}")
```

## 7. 转换工具

XpertEval 提供了将各种格式转换为 XpertFormat 的工具，详见 [数据集转换工具文档](./dataset_conversion.md)。 