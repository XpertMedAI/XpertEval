---
layout: default
title: 数据集转换工具
parent: 数据集文档
nav_order: 2
toc: true
---

# 数据集转换工具
{: .no_toc }

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

XpertEval 框架提供了一套完整的工具，用于将各种常见评测数据集格式转换为统一的 XpertFormat 格式。本文档介绍如何使用这些转换工具。

## 命令行转换工具

XpertEval 提供了命令行工具 `convert_dataset.py`，可以方便地进行数据集格式转换：

```bash
# 激活环境
conda activate xperteval

# 基本用法
python scripts/convert_dataset.py --input <输入文件路径> --output <输出文件路径> --type <数据集类型>

# 查看帮助信息
python scripts/convert_dataset.py --help

# 查看支持的数据集类型
python scripts/convert_dataset.py guidelines
```

### 参数说明

- `--input`: 输入文件或目录路径
- `--output`: 输出文件路径，默认为 `<输入文件名>_xpert.jsonl`
- `--type`: 数据集类型，如 `mmlu`, `cmmlu`, `gsm8k` 等
- `--media-dir`: 媒体文件目录路径，用于多模态数据集
- `--validate`: 转换后验证数据格式
- `--verbose`: 显示详细日志
- `--overwrite`: 覆盖已存在的输出文件

### 示例

```bash
# 转换 MMLU 数据集
python scripts/convert_dataset.py --input data/original/mmlu/dev.csv --output data/integrated/mmlu/dev.jsonl --type mmlu

# 转换多模态数据集
python scripts/convert_dataset.py --input data/original/mmbench/data.json --output data/integrated/mmbench/dataset.jsonl --type mmbench --media-dir data/integrated/mmbench/media
```

## 编程接口

也可以在 Python 代码中直接使用转换函数：

```python
from xperteval.datasets.converters.to_xpert_format import convert_to_xpert_format

# 转换单个文件
result = convert_to_xpert_format(
    input_path="path/to/input.csv",
    output_path="path/to/output.jsonl",
    dataset_type="mmlu"
)
print(f"转换结果: {result}")

# 批量转换
from xperteval.datasets.converters.to_xpert_format import batch_convert
results = batch_convert(
    input_dir="path/to/input_dir",
    output_dir="path/to/output_dir",
    dataset_type="cmmlu",
    file_pattern="*.csv"
)
print(f"批量转换结果: {results}")
```

## 支持的数据集类型

XpertEval 目前支持以下数据集类型的转换：

### 通用评测数据集

| 数据集类型 | 描述 | 原始格式 |
|------------|------|----------|
| `mmlu` | Massive Multitask Language Understanding | CSV |
| `cmmlu` | Chinese Massive Multitask Language Understanding | CSV |
| `gsm8k` | Grade School Math 8K | JSON |
| `math` | MATH | JSON |
| `human_eval` | HumanEval | JSON |
| `ceval` | C-Eval | JSON |

### 多模态评测数据集

| 数据集类型 | 描述 | 原始格式 |
|------------|------|----------|
| `mmbench` | MMBench | JSON/JSONL |
| `llava_bench` | LLaVA-Bench | JSON |
| `seed_bench` | SEED-Bench | JSONL |
| `mm_vet` | MM-Vet | JSON |

## 自定义转换器

如果需要支持新的数据集格式，可以扩展 `to_xpert_format.py` 模块，添加自定义转换函数：

```python
from xperteval.datasets.converters.to_xpert_format import register_converter

@register_converter("my_dataset")
def convert_my_dataset(input_path, output_path, **kwargs):
    """
    将自定义数据集转换为 XpertFormat
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        **kwargs: 其他参数
    
    Returns:
        bool: 转换是否成功
    """
    # 实现转换逻辑
    # ...
    
    return True
```

注册后，可以使用命令行或编程接口调用自定义转换器：

```bash
python scripts/convert_dataset.py --input my_data.json --output my_data_xpert.jsonl --type my_dataset
```

## 转换后的验证

建议在转换后使用验证工具检查数据格式是否符合 XpertFormat 规范：

```bash
# 命令行验证
python scripts/convert_dataset.py validate --input path/to/converted.jsonl

# 或在转换时添加 --validate 参数
python scripts/convert_dataset.py --input input.csv --output output.jsonl --type mmlu --validate
```

## 常见问题解决

### 媒体文件路径问题

多模态数据集转换时，需要特别注意媒体文件路径的处理：

- 使用相对路径：建议使用相对于数据集根目录的路径，便于移植
- 指定媒体目录：使用 `--media-dir` 参数指定媒体文件的存放目录
- 文件不存在：转换工具会检查媒体文件是否存在，如果不存在会发出警告

### 字符编码问题

处理中文或其他非ASCII字符时，可能遇到编码问题：

- 输入文件应使用 UTF-8 编码
- 输出文件将使用 UTF-8 编码保存
- 如果遇到编码错误，可以尝试手动指定编码：

```python
from xperteval.datasets.converters.to_xpert_format import convert_to_xpert_format

convert_to_xpert_format(
    input_path="path/to/input.csv",
    output_path="path/to/output.jsonl",
    dataset_type="cmmlu",
    encoding="gb18030"  # 指定输入文件编码
)
```

### 大型数据集处理

对于特别大的数据集，可以使用流式处理模式减少内存占用：

```bash
python scripts/convert_dataset.py --input large_dataset.json --output large_dataset_xpert.jsonl --type mmlu --streaming
``` 