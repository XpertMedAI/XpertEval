# XpertEval 数据集处理模块

本文档详细介绍了XpertEval支持的各类评测数据集格式，以及统一这些格式的方案。

## 1. 主要评测数据集格式分析

### 1.1 通用文本评测数据集

#### MMLU (Massive Multitask Language Understanding)
- **格式**: CSV或JSON文件
- **结构**:
  ```json
  {
    "question": "问题文本",
    "choices": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",  // 正确答案索引或文本
    "subject": "数学",  // 学科分类
    "difficulty": "中等"  // 可选的难度标签
  }
  ```
- **特点**: 多选题格式，包含57个学科领域，测试模型的知识广度

#### CMMLU (Chinese Massive Multitask Language Understanding)
- **格式**: CSV或JSON文件
- **结构**: 与MMLU类似，但专注于中文内容
  ```json
  {
    "question": "中文问题文本",
    "choices": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "subject": "中国历史",
    "difficulty": "困难"
  }
  ```
- **特点**: 专注于中文知识评测，涵盖67个中文学科领域

#### GSM8K (Grade School Math 8K)
- **格式**: JSON文件
- **结构**:
  ```json
  {
    "question": "数学问题描述",
    "answer": "解题步骤\n最终答案: 42",
    "tags": ["加法", "乘法"]  // 可选的问题标签
  }
  ```
- **特点**: 小学数学应用题，需要多步推理，答案包含解题步骤和最终结果

#### MATH
- **格式**: JSON文件
- **结构**:
  ```json
  {
    "problem": "数学问题描述，可能包含LaTeX公式",
    "level": "高中",  // 难度级别
    "type": "代数",  // 数学分支
    "solution": "详细的解题过程，包含LaTeX公式",
    "answer": "最终答案"
  }
  ```
- **特点**: 高中和大学水平的数学问题，包含复杂公式，需要形式化推理

#### HumanEval
- **格式**: JSON文件
- **结构**:
  ```json
  {
    "task_id": "HumanEval/1",
    "prompt": "函数签名和描述，可能包含示例",
    "entry_point": "function_name",
    "canonical_solution": "标准答案代码",
    "test": "测试代码",
    "language": "python"  // 编程语言
  }
  ```
- **特点**: 代码生成任务，需要根据描述生成完整可运行的函数，并通过测试用例

#### C-Eval
- **格式**: JSON文件
- **结构**: 类似MMLU和CMMLU，但专注于中文内容和中国特定知识领域
  ```json
  {
    "id": "问题ID",
    "question": "中文问题文本",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "field": "科学",
    "category": "物理"
  }
  ```
- **特点**: 中文评测集，包含多个领域的选择题

### 1.2 多模态评测数据集

#### MMBench
- **格式**: JSON或JSONL文件
- **结构**:
  ```json
  {
    "question_id": "unique_id",
    "image": "image_path.jpg",
    "question": "关于图像的问题",
    "choices": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "category": "图像理解",
    "difficulty": "中等"
  }
  ```
- **特点**: 视觉-语言理解任务，需要模型理解图像内容并回答问题

#### LLaVA-Bench
- **格式**: JSON文件
- **结构**:
  ```json
  {
    "id": "样本ID",
    "image": "image_path.jpg",
    "conversations": [
      {"role": "human", "content": "问题文本"},
      {"role": "assistant", "content": "参考答案"}
    ],
    "category": "图像描述"
  }
  ```
- **特点**: 对话式视觉-语言任务，评测模型对图像的理解和描述能力

#### SEED-Bench
- **格式**: JSONL文件
- **结构**:
  ```json
  {
    "sample_id": "unique_id",
    "image_paths": ["image1.jpg", "image2.jpg"],  // 可能包含多个图像
    "video_path": "video.mp4",  // 可选的视频路径
    "question": "关于图像或视频的问题",
    "choices": ["选项A", "选项B", "选项C", "选项D"],
    "answer": 0,  // 正确选项的索引
    "task_type": "图像理解"
  }
  ```
- **特点**: 包含图像和视频理解任务，测试模型对视觉内容的多方面理解能力

#### MM-Vet
- **格式**: JSON文件
- **结构**:
  ```json
  {
    "id": "样本ID",
    "image": "image_path.jpg",
    "question": "复杂的多模态任务描述",
    "answer": "参考答案",
    "category": "视觉推理",
    "difficulty": "专家级"
  }
  ```
- **特点**: 专注于复杂的视觉推理任务，包括图表理解、视觉常识推理等

### 1.3 MS-SWIFT格式(当前已实现)

- **格式**: JSONL文件
- **结构**:
  ```json
  {
    "id": "样本ID",
    "query": "用户问题",
    "response": "参考答案",
    "history": [  // 可选的历史对话
      {"role": "human", "content": "之前的问题"},
      {"role": "assistant", "content": "之前的回答"}
    ],
    "files": [  // 可选的多模态文件
      {"path": "image.jpg", "type": "image"},
      {"path": "audio.mp3", "type": "audio"}
    ],
    "meta": {  // 可选的元数据
      "category": "分类",
      "difficulty": "难度"
    }
  }
  ```
- **特点**: 灵活的格式，支持单轮/多轮对话，支持多种模态的文件引用

## 2. 格式对比分析

### 2.1 相同点

1. **基本问答结构**: 所有数据集都包含问题和答案/参考答案
2. **分类信息**: 大多数数据集都有主题/类别/学科等分类标签
3. **难度指示**: 许多数据集包含难度级别信息
4. **JSON兼容**: 大部分数据集使用JSON或可转换为JSON的格式

### 2.2 不同点

1. **任务类型差异**:
   - 选择题(MMLU, CMMLU, C-Eval)
   - 开放式问答(GSM8K部分题目)
   - 代码生成(HumanEval)
   - 多模态理解(MMBench, LLaVA-Bench)

2. **答案格式差异**:
   - 选项索引(A, B, C, D)
   - 数值答案
   - 文本答案
   - 代码答案
   - 分步解答

3. **多模态支持**:
   - 纯文本(MMLU, GSM8K等)
   - 图像+文本(MMBench, LLaVA-Bench)
   - 视频+文本(SEED-Bench)

4. **对话结构**:
   - 单轮问答(大多数数据集)
   - 多轮对话(LLaVA-Bench部分)

## 3. 统一格式方案

基于以上分析，我们提出一个扩展的MS-SWIFT格式作为统一的内部表示格式，称为**XpertFormat**:

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
  "evaluation": {  // 评估相关信息
    "metrics": ["accuracy", "bleu"],  // 适用的评估指标
    "scoring_criteria": "评分标准描述"
  }
}
```

## 4. 格式转换策略

### 4.1 选择题类数据集(MMLU, CMMLU, C-Eval)
- `query` = 问题文本
- `choices` = 选项列表
- `answer.type` = "choice"
- `answer.value` = 正确选项ID
- `meta.task_type` = "choice"
- `meta.subject` = 学科分类

### 4.2 数学问题(GSM8K, MATH)
- `query` = 问题文本
- `response` = 完整解答
- `answer.type` = "step_by_step"
- `answer.value` = 最终答案
- `answer.explanation` = 解题步骤
- `meta.task_type` = "math"
- `meta.difficulty` = 难度级别

### 4.3 代码生成(HumanEval)
- `query` = 函数描述和要求
- `response` = 标准答案代码
- `answer.type` = "code"
- `answer.value` = 代码答案
- `meta.task_type` = "code"
- `evaluation.metrics` = ["pass@k", "functional_correctness"]

### 4.4 多模态数据集(MMBench, LLaVA-Bench)
- `query` = 问题文本
- `files` = 图像/视频文件列表
- `choices` = 选项列表(如适用)
- `answer.type` = 根据任务类型("choice"或"text")
- `answer.value` = 正确答案
- `meta.task_type` = "vision"或"multi"

## 5. 评分策略

针对不同任务类型的评分策略:

### 5.1 选择题评分
- **指标**: 准确率(Accuracy)
- **方法**: 直接比较模型输出与标准答案是否匹配
- **实现**: 从模型输出中提取选项ID(A/B/C/D)，与`answer.value`比较

### 5.2 数学问题评分
- **指标**: 答案准确率、步骤合理性
- **方法**: 
  - 提取最终数值答案进行比较
  - 可选择使用LLM评估解题步骤的合理性
- **实现**: 使用正则表达式提取数值，允许合理的格式变化

### 5.3 代码生成评分
- **指标**: Pass@k, 功能正确性
- **方法**: 执行生成的代码，检查是否通过测试用例
- **实现**: 使用安全的代码执行环境，运行测试用例

### 5.4 多模态评分
- **指标**: 准确率、相关性、详细度
- **方法**: 
  - 选择题直接比较答案
  - 开放式回答可使用LLM评估或与参考答案计算相似度
- **实现**: 结合规则和LLM评估方法

## 6. 实现计划

1. **核心解析器**:
   - 为每种主要数据集格式实现专门的解析器
   - 所有解析器继承`BaseDataset`并实现标准接口

2. **转换工具**:
   - 实现从原始格式到XpertFormat的转换函数
   - 提供批量转换工具和命令行接口

3. **统一接口**:
   - 确保所有数据集解析器提供一致的数据访问方法
   - 标准化评估流程，使其适用于所有数据集类型

4. **元数据管理**:
   - 实现数据集版本控制
   - 提供数据集统计和预览功能

## 7. 注意事项

1. **格式兼容性**: 确保转换过程不丢失原始数据集的关键信息
2. **多模态资源**: 妥善处理图像、音频、视频等资源文件的路径和加载
3. **评分灵活性**: 设计评分系统时考虑不同任务类型的特殊需求
4. **扩展性**: 保持架构开放，便于添加新的数据集格式
5. **文档完善**: 为每种数据集格式和转换方法提供详细文档 