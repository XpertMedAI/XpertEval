---
layout: default
title: 评测器详解
parent: 用户手册
nav_order: 3
toc: true
---

# 评测器详解
{: .no_toc }

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

本文档详细介绍 XpertEval 框架中的评测器系统，包括评测器基类、内置评测器以及它们的具体实现细节。

## 评测器概述

评测器（Evaluator）是 XpertEval 框架的核心组件之一，负责对大模型生成的回答与标准答案进行比较，并给出量化的评分结果。XpertEval 设计了一套完整的评测器体系，包括：

1. **通用评测器**：如准确率（Accuracy）、BLEU分数等，适用于各种常见任务类型
2. **专业领域评测器**：如中医诊断评测器，针对特定专业领域的评测需求

所有评测器都继承自 `BaseEvaluator` 抽象基类，遵循统一的接口标准，便于扩展和使用。

## 评测器基类

`BaseEvaluator` 定义了所有评测器必须实现的接口和共享的基础功能。

### 基类定义

```python
class BaseEvaluator(abc.ABC):
    """评测器抽象基类"""
    
    def __init__(self, **kwargs):
        """初始化评测器"""
        self.name = kwargs.get('name', self.__class__.__name__)
        self.kwargs = kwargs
    
    @abc.abstractmethod
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估模型预测结果"""
        pass
```

### 关键方法

**1. `_is_valid_sample`方法**

检查样本是否有效，确保预测结果和参考答案符合预期格式。

```python
def _is_valid_sample(self, prediction: str, reference: Dict[str, Any]) -> bool:
    """检查样本是否有效"""
    # 基本检查：预测和参考都不应为None
    if prediction is None or reference is None:
        return False
    
    # 检查参考答案格式
    if not isinstance(reference, dict) or "answer" not in reference:
        return False
    
    # 检查answer字段格式
    answer = reference.get("answer", {})
    if not isinstance(answer, dict) or "value" not in answer:
        return False
    
    return True
```

**2. `aggregate_scores`方法**

聚合多个样本的评分结果，计算平均分、最高分、最低分等统计指标。

```python
def aggregate_scores(self, individual_scores: List[float]) -> Dict[str, float]:
    """聚合单个样本的评分"""
    if not individual_scores:
        return {"score": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    
    return {
        "score": sum(individual_scores) / len(individual_scores),  # 平均分
        "min": min(individual_scores),                             # 最低分
        "max": max(individual_scores),                             # 最高分
        "count": len(individual_scores)                            # 样本数量
    }
```

## 通用评测器

### 准确率评测器 (AccuracyEvaluator)

准确率评测器用于评估分类任务（如选择题）的准确率，以及简单文本匹配的精确匹配率。

#### 初始化参数

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| exact_match | 布尔值 | True | 是否要求完全匹配 |
| case_sensitive | 布尔值 | False | 是否区分大小写 |
| allow_partial | 布尔值 | False | 是否允许部分匹配 |
| numeric_tolerance | 浮点数 | 0.0001 | 数值比较的容差 |

#### 支持的答案类型

1. **选择题 (choice)**
   - 从预测文本中提取选项标识符（如A、B、C、D）
   - 与参考答案中的选项值进行比较
   - 返回1.0（正确）或0.0（错误）

2. **文本 (text)**
   - 支持精确匹配：预测文本必须与参考答案完全一致
   - 支持部分匹配：预测文本包含参考答案或参考答案包含预测文本
   - 可选是否区分大小写

3. **数值 (number)**
   - 从预测文本中提取数值
   - 与参考答案进行比较，允许一定的误差范围

#### 实现细节

**选择题评估逻辑：**

```python
def _evaluate_choice(self, prediction: str, reference: Dict[str, Any]) -> float:
    """评估选择题的准确率"""
    # 获取标准答案
    answer_value = reference.get("answer", {}).get("value", "")
    if not answer_value:
        return 0.0
    
    # 从预测文本中提取选项
    extracted_choice = self._extract_choice(prediction)
    if not extracted_choice:
        return 0.0
    
    # 比较选项（不区分大小写）
    if extracted_choice.upper() == answer_value.upper():
        return 1.0
    
    return 0.0
```

**文本评估逻辑：**

```python
def _evaluate_text(self, prediction: str, reference: str) -> float:
    """评估文本类型的准确率"""
    if not prediction or not reference:
        return 0.0
    
    # 文本规范化
    if not self.case_sensitive:
        prediction = prediction.lower()
        reference = reference.lower()
    
    # 去除前后空白
    prediction = prediction.strip()
    reference = reference.strip()
    
    # 精确匹配
    if self.exact_match:
        return 1.0 if prediction == reference else 0.0
    
    # 部分匹配
    if self.allow_partial:
        return 1.0 if reference in prediction or prediction in reference else 0.0
    
    return 0.0
```

#### 输出结果

准确率评测器返回的结果示例：

```json
{
    "accuracy": {
        "score": 0.75,  // 总体准确率
        "min": 0.0,     // 最低分
        "max": 1.0,     // 最高分
        "count": 4      // 样本数量
    },
    "choice_accuracy": {  // 选择题准确率（如果有选择题样本）
        "score": 0.67,
        "min": 0.0,
        "max": 1.0,
        "count": 3
    },
    "text_accuracy": {    // 文本准确率（如果有文本样本）
        "score": 1.0,
        "min": 1.0,
        "max": 1.0,
        "count": 1
    }
}
```

### BLEU评测器 (BLEUEvaluator)

BLEU评测器用于评估生成文本与参考答案之间的相似度，通过计算n-gram精确率来衡量。BLEU分数适用于机器翻译、文本生成等任务。

#### 初始化参数

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| n_gram | 整数 | 4 | BLEU计算中的最大n-gram大小 |
| weights | 列表 | [0.25, 0.25, 0.25, 0.25] | 不同n-gram的权重 |
| smoothing | 布尔值 | True | 是否使用平滑处理 |
| language | 字符串 | 'auto' | 文本语言，支持'en'(英文)和'zh'(中文) |

#### 实现细节

**语言检测逻辑：**

```python
def _detect_language(self, text: str) -> str:
    """检测文本语言"""
    # 简单的语言检测：计算中文字符的比例
    chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_char_count = len(text)
    
    # 如果中文字符比例超过20%，认为是中文
    if total_char_count > 0 and chinese_char_count / total_char_count > 0.2:
        return 'zh'
    else:
        return 'en'
```

**分词处理：**

- 英文文本：使用 NLTK 的 `word_tokenize` 函数
- 中文文本：使用结巴分词 (`jieba.cut`)

**BLEU计算：**

```python
def _calculate_bleu(self, prediction: str, references: List[str]) -> float:
    """计算单个样本的BLEU分数"""
    if not prediction:
        return 0.0
    
    # 确定语言并选择相应的分词器
    language = self._detect_language(prediction) if self.language == 'auto' else self.language
    tokenize_func = self._get_tokenize_function(language)
    
    # 分词
    tokenized_pred = tokenize_func(prediction)
    tokenized_refs = [tokenize_func(ref) for ref in references]
    
    # 使用nltk计算BLEU分数
    smoothing_function = nltk.translate.bleu_score.SmoothingFunction().method1 if self.smoothing else None
    
    bleu_score = nltk.translate.bleu_score.sentence_bleu(
        tokenized_refs, 
        tokenized_pred,
        weights=self.weights,
        smoothing_function=smoothing_function
    )
    
    return bleu_score
```

#### 输出结果

BLEU评测器返回的结果示例：

```json
{
    "bleu": {
        "score": 0.68,  // 平均BLEU分数
        "min": 0.45,    // 最低BLEU分数
        "max": 0.92,    // 最高BLEU分数
        "count": 5      // 样本数量
    }
}
```

### 数学评测器 (MathEvaluator)

数学评测器用于评估数学问题的解答，支持数值比较、公式比较等。

#### 初始化参数

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| tolerance | 浮点数 | 1e-6 | 答案容差 |
| normalize | 布尔值 | True | 是否规范化答案 |
| require_units | 布尔值 | False | 是否需要单位一致 |
| strict_format | 布尔值 | False | 是否严格格式匹配 |

#### 适用场景

1. **算术计算**：加减乘除、分数、小数等
2. **方程求解**：得到正确的数值答案
3. **简单代数**：多项式计算等

#### 实现细节

**数值提取逻辑：**

```python
def _extract_number_and_unit(self, text: str) -> Tuple[Optional[float], Optional[str]]:
    """从文本中提取数值和单位"""
    # 规范化文本
    if self.normalize:
        text = self._normalize_math_text(text)
    
    # 匹配数字和可能的单位
    # 例如: "42.5 kg", "1/2", "-3.14", "2e-3 m/s"
    pattern = r'(-?\d+\.?\d*(?:e[+-]?\d+)?|\d+/\d+)\s*([a-zA-Z°/%]*)'
    match = re.search(pattern, text)
    
    if not match:
        return None, None
    
    number_str = match.group(1)
    unit = match.group(2).strip() if match.group(2) else None
    
    # 转换分数形式
    if '/' in number_str and not 'e' in number_str.lower():
        try:
            num, denom = map(float, number_str.split('/'))
            value = num / denom if denom != 0 else None
        except Exception:
            value = None
    else:
        try:
            value = float(number_str)
        except Exception:
            value = None
    
    return value, unit
```

**文本规范化：**

```python
def _normalize_math_text(self, text: str) -> str:
    """规范化数学文本"""
    # 去除前后空白
    text = text.strip()
    
    # 替换全角数字和符号为半角
    full_to_half = str.maketrans('０１２３４５６７８９．－＋（）／', '0123456789.-+()/') 
    text = text.translate(full_to_half)
    
    # 替换常见词语为数字
    text = re.sub(r'负\s*(\d+)', r'-\1', text)  # 负3 -> -3
    text = re.sub(r'零点(\d+)', r'0.\1', text)  # 零点五 -> 0.5
    
    # 替换中文分数表示
    text = re.sub(r'(\d+)\s*分之\s*(\d+)', r'\2/\1', text)  # 2分之1 -> 1/2
    
    return text
```

**答案评估逻辑：**

```python
def _evaluate_math_answer(self, prediction: str, reference: str) -> float:
    """评估数学答案的正确性"""
    if not prediction or not reference:
        return 0.0
    
    # 提取数值和单位
    pred_value, pred_unit = self._extract_number_and_unit(prediction)
    ref_value, ref_unit = self._extract_number_and_unit(reference)
    
    # 如果无法提取数值，返回0分
    if pred_value is None or ref_value is None:
        return 0.0
    
    # 检查单位一致性（如果需要）
    if self.require_units and pred_unit != ref_unit:
        return 0.0
    
    # 计算数值误差
    try:
        # 对于接近0的值，使用绝对误差
        if abs(ref_value) < self.tolerance:
            error = abs(pred_value - ref_value)
            return 1.0 if error <= self.tolerance else 0.0
        
        # 对于其他值，使用相对误差
        relative_error = abs((pred_value - ref_value) / ref_value)
        return 1.0 if relative_error <= self.tolerance else 0.0
    except Exception as e:
        logger.warning(f"计算数值误差时出错: {e}")
        return 0.0
```

#### 输出结果

数学评测器返回的结果示例：

```json
{
    "math_accuracy": {
        "score": 0.83,  // 平均正确率
        "min": 0.0,     // 最低分
        "max": 1.0,     // 最高分
        "count": 6      // 样本数量
    }
}
```

## 专业领域评测器

### 中医诊断评测器 (TcmDiagnosisEvaluator)

中医诊断评测器用于评估模型在中医辨证论治方面的能力，包括对症候的识别、疾病诊断的准确性等。

#### 初始化参数

| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| match_threshold | 浮点数 | 0.7 | 匹配阈值 |
| exact_match | 布尔值 | False | 是否要求精确匹配 |
| partial_credit | 布尔值 | True | 是否给予部分分数 |
| keywords_weight | 浮点数 | 0.6 | 关键词匹配权重 |
| normalize_tcm_terms | 布尔值 | True | 是否规范化中医术语 |

#### 支持的评测类型

1. **症候匹配 (syndrome)**
   - 评估模型识别出的证候与标准答案的匹配程度
   - 使用证候关键词提取和相似度计算

2. **疾病诊断 (disease)**
   - 评估模型诊断出的疾病与标准答案的一致性
   - 通常要求更高的精确匹配度

3. **治法选择 (treatment)**
   - 评估模型提出的治法是否与标准答案一致
   - 通过关键词匹配计算相似度

#### 中医术语同义词表

评测器内置了中医术语同义词表，用于规范化不同表述的相同概念：

```python
self.tcm_synonyms = {
    "气虚": ["气虚", "气不足", "肺气虚", "脾气虚", "气虚证", "气短"],
    "阴虚": ["阴虚", "阴不足", "阴亏", "阴津亏", "阴虚证", "津亏"],
    "血虚": ["血虚", "血亏", "血不足", "血少", "血虚证"],
    "阳虚": ["阳虚", "阳不足", "阳气虚", "阳亏", "阳虚证", "畏寒"],
    "湿热": ["湿热", "湿热蕴结", "湿热内蕴", "湿热证"],
    "气滞": ["气滞", "气机不畅", "气机阻滞", "气郁", "气滞证"],
    "血瘀": ["血瘀", "瘀血", "血瘀证", "瘀阻", "血行不畅"],
    "痰湿": ["痰湿", "痰浊", "痰湿内停", "痰湿证", "痰浊内停"],
    "肝郁": ["肝郁", "肝气郁结", "肝气不舒", "肝郁气滞"]
}
```

#### 实现细节

**症候评估逻辑：**

```python
def _evaluate_syndrome(self, prediction: str, reference: str) -> float:
    """评估证候辨识准确性"""
    if not prediction or not reference:
        return 0.0
    
    # 规范化文本
    if self.normalize_tcm_terms:
        prediction = self._normalize_tcm_text(prediction)
        reference = self._normalize_tcm_text(reference)
    
    # 提取证候关键词
    pred_syndromes = self._extract_tcm_syndromes(prediction)
    ref_syndromes = self._extract_tcm_syndromes(reference)
    
    # 计算匹配度
    return self._calculate_set_similarity(pred_syndromes, ref_syndromes)
```

**集合相似度计算：**

```python
def _calculate_set_similarity(self, pred_set: Set[str], ref_set: Set[str]) -> float:
    """计算两个集合的相似度"""
    if not pred_set and not ref_set:
        return 1.0  # 两个空集合视为完全匹配
    
    if not pred_set or not ref_set:
        return 0.0  # 一个空一个非空，视为完全不匹配
    
    # 计算交集、并集
    intersection = pred_set.intersection(ref_set)
    union = pred_set.union(ref_set)
    
    # 计算Jaccard相似度
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # 计算召回率和精确率
    recall = len(intersection) / len(ref_set) if ref_set else 0.0
    precision = len(intersection) / len(pred_set) if pred_set else 0.0
    
    # 如果需要精确匹配，直接比较集合是否相等
    if self.exact_match:
        return 1.0 if pred_set == ref_set else 0.0
    
    # 如果允许部分匹配，计算加权分数
    if self.partial_credit:
        # 使用F1分数：精确率和召回率的调和平均
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
        
        # 结合Jaccard和F1
        return self.keywords_weight * f1 + (1 - self.keywords_weight) * jaccard
    
    # 默认使用Jaccard相似度
    return jaccard
```

#### 输出结果

中医诊断评测器返回的结果示例：

```json
{
    "tcm_diagnosis": {
        "score": 0.73,  // 总体评分
        "min": 0.2,     // 最低分
        "max": 1.0,     // 最高分
        "count": 8      // 样本数量
    },
    "syndrome": {        // 证候评分（如果有症候样本）
        "score": 0.81,
        "min": 0.5,
        "max": 1.0,
        "count": 4
    },
    "disease": {         // 疾病评分（如果有疾病样本）
        "score": 0.65,
        "min": 0.3,
        "max": 1.0,
        "count": 2
    },
    "treatment": {       // 治法评分（如果有治法样本）
        "score": 0.60,
        "min": 0.2,
        "max": 0.9,
        "count": 2
    }
}
```

## 评测器注册和使用

XpertEval 框架提供了一套评测器注册和管理机制，便于动态获取和使用评测器。

### 评测器注册表

```python
# 评测器注册表
EVALUATOR_REGISTRY = {
    # 通用评测器
    "accuracy": AccuracyEvaluator,
    "bleu": BLEUEvaluator,
    "math": MathEvaluator,
    
    # 中医药特定评测器
    "tcm_diagnosis": TcmDiagnosisEvaluator,
    
    # 其他评测器会在这里注册
}
```

### 获取评测器

```python
def get_evaluator(evaluator_name: str, **kwargs) -> BaseEvaluator:
    """获取指定名称的评测器实例"""
    if evaluator_name not in EVALUATOR_REGISTRY:
        available_evaluators = ", ".join(EVALUATOR_REGISTRY.keys())
        raise ValueError(f"未知的评测器: {evaluator_name}，可用的评测器有: {available_evaluators}")
    
    evaluator_class = EVALUATOR_REGISTRY[evaluator_name]
    return evaluator_class(**kwargs)
```

### 获取多个评测器

```python
def get_evaluators(evaluator_names: List[str], **kwargs) -> List[BaseEvaluator]:
    """获取多个评测器实例"""
    return [get_evaluator(name, **kwargs) for name in evaluator_names]
```

### 列出所有可用评测器

```python
def list_evaluators() -> List[str]:
    """列出所有可用的评测器名称"""
    return list(EVALUATOR_REGISTRY.keys())
```

### 注册自定义评测器

```python
def register_evaluator(name: str, evaluator_class: Type[BaseEvaluator]) -> None:
    """注册新的评测器"""
    if not issubclass(evaluator_class, BaseEvaluator):
        raise TypeError(f"评测器类必须继承自BaseEvaluator")
    
    EVALUATOR_REGISTRY[name] = evaluator_class
```

## 实际使用示例

### 基础使用

```python
from xperteval.evaluators import get_evaluator

# 获取准确率评测器
accuracy_evaluator = get_evaluator("accuracy", exact_match=True, case_sensitive=False)

# 预测结果和参考答案
predictions = ["选择A", "我认为答案是B", "这是正确的文本"]
references = [
    {"answer": {"type": "choice", "value": "A"}, "choices": [{"id": "A"}, {"id": "B"}]},
    {"answer": {"type": "choice", "value": "C"}, "choices": [{"id": "A"}, {"id": "B"}, {"id": "C"}]},
    {"answer": {"type": "text", "value": "这是正确的文本"}}
]

# 执行评测
result = accuracy_evaluator.evaluate(predictions, references)
print(result)
```

### 多评测器组合

```python
from xperteval.evaluators import get_evaluators

# 获取多个评测器
evaluators = get_evaluators(["accuracy", "bleu"])

# 执行多个评测
results = []
for evaluator in evaluators:
    result = evaluator.evaluate(predictions, references)
    results.append(result)
```

### 自定义评测器

```python
from xperteval.core.base_evaluator import BaseEvaluator
from xperteval.evaluators import register_evaluator

# 定义自定义评测器
class MyCustomEvaluator(BaseEvaluator):
    def evaluate(self, predictions, references):
        # 自定义评测逻辑
        scores = []
        for pred, ref in zip(predictions, references):
            # 计算分数...
            scores.append(score)
        
        return {"my_metric": self.aggregate_scores(scores)}

# 注册自定义评测器
register_evaluator("my_custom", MyCustomEvaluator)

# 使用自定义评测器
custom_evaluator = get_evaluator("my_custom")
result = custom_evaluator.evaluate(predictions, references)
```

## 注意事项

1. **数据格式要求**：
   - 预测结果必须是字符串列表
   - 参考答案必须是字典列表，且每个字典必须包含 `answer` 字段
   - `answer` 字段必须是字典，包含 `type` 和 `value` 字段

2. **评测器配置**：
   - 根据具体任务需要选择合适的评测器
   - 通过初始化参数调整评测器的行为

3. **错误处理**：
   - 评测器会跳过无效样本，并在日志中记录警告信息
   - 对于无法处理的情况，会返回默认分数（通常为0）

4. **扩展性**：
   - 如需添加新的评测器，确保继承 `BaseEvaluator` 并实现 `evaluate` 方法
   - 使用 `register_evaluator` 函数注册新的评测器，使其可通过 `get_evaluator` 获取 