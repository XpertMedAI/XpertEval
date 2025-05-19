---
layout: default
title: 数据集使用指南
parent: 数据集文档
nav_order: 3
toc: true
---

# 数据集使用指南
{: .no_toc }

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

本文档介绍如何在 XpertEval 框架中使用各种评测数据集，包括集成数据集和自定义数据集。

## 数据集注册与管理

XpertEval 提供了一套完整的数据集注册和管理机制，可以方便地加载、分割、采样和过滤数据集。

### 列出可用数据集

```python
from xperteval.datasets.registered_datasets import list_available_datasets

# 列出所有已注册的数据集
datasets = list_available_datasets()
for dataset in datasets:
    print(f"ID: {dataset['id']}")
    print(f"名称: {dataset['name']}")
    print(f"类型: {dataset['type']}")
    print(f"描述: {dataset['description']}")
    print("-" * 50)
```

### 获取数据集实例

```python
from xperteval.datasets.registered_datasets import get_dataset

# 加载已集成的数据集
dataset = get_dataset(dataset_id="mmlu")

# 加载特定分割
train_dataset = get_dataset(dataset_id="mmlu", split="train")
dev_dataset = get_dataset(dataset_id="mmlu", split="dev")
test_dataset = get_dataset(dataset_id="mmlu", split="test")

# 直接加载文件
custom_dataset = get_dataset(
    dataset_path="path/to/dataset.jsonl",
    dataset_type="xpert-format"
)

# 获取数据集大小
print(f"数据集大小: {len(dataset)}")

# 访问单个样本
sample = dataset[0]
print(f"样本ID: {sample['id']}")
print(f"问题: {sample['query']}")
print(f"答案: {sample['response']}")
```

### 使用数据集管理器

数据集管理器提供了更多高级功能，如下载、转换、分割、采样和过滤：

```python
from xperteval.datasets.dataset_manager import DatasetManager

# 创建数据集管理器
manager = DatasetManager()

# 列出可用数据集
datasets = manager.list_available_datasets()

# 下载数据集
manager.download_dataset("mmlu")

# 转换数据集
manager.convert_dataset("mmlu")

# 创建数据集分割
manager.create_dataset_split(
    dataset_id="mmlu",
    train_ratio=0.8,
    dev_ratio=0.1,
    test_ratio=0.1
)

# 获取数据集实例（支持自动下载和转换）
dataset = manager.get_dataset(
    dataset_id="mmlu",
    auto_download=True,
    auto_convert=True
)

# 采样数据集
sampled_dataset = manager.get_dataset(
    dataset_id="mmlu",
    sample_size=100
)

# 过滤数据集
def filter_func(sample):
    # 只保留数学类题目
    return sample.get("meta", {}).get("subject") == "mathematics"

filtered_dataset = manager.get_dataset(
    dataset_id="mmlu",
    filter_func=filter_func
)
```

## 数据集迭代与批处理

XpertEval 的数据集类支持标准的 Python 迭代接口：

```python
# 遍历数据集
for sample in dataset:
    print(sample["query"])

# 批处理
batch_size = 16
for i in range(0, len(dataset), batch_size):
    batch = [dataset[j] for j in range(i, min(i + batch_size, len(dataset)))]
    # 处理批次
    process_batch(batch)
```

## 多模态数据处理

对于包含图像、音频或视频的多模态数据集，可以这样处理：

```python
# 加载多模态数据集
mmbench = get_dataset(dataset_id="mmbench")

# 访问样本
sample = mmbench[0]

# 获取文件路径
if "files" in sample:
    for file_info in sample["files"]:
        file_path = file_info["path"]
        file_type = file_info["type"]
        
        if file_type == "image":
            # 处理图像
            from PIL import Image
            image = Image.open(file_path)
            # 进一步处理...
            
        elif file_type == "audio":
            # 处理音频
            # ...
            
        elif file_type == "video":
            # 处理视频
            # ...
```

## 创建自定义数据集

### 创建 XpertFormat 格式数据集

您可以创建符合 XpertFormat 规范的自定义数据集：

```python
import json

# 创建样本列表
samples = [
    {
        "id": "custom_1",
        "query": "这是一个测试问题?",
        "response": "这是一个测试回答",
        "meta": {
            "task_type": "qa",
            "category": "测试"
        }
    },
    # 更多样本...
]

# 保存为 JSONL 文件
with open("custom_dataset.jsonl", "w", encoding="utf-8") as f:
    for sample in samples:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

# 加载自定义数据集
from xperteval.datasets.xpert_format import XpertFormatDataset
custom_dataset = XpertFormatDataset("custom_dataset.jsonl")
```

### 实现自定义数据集类

如果您有特殊的数据格式需求，可以通过继承 `BaseDataset` 类来实现自定义数据集：

```python
from xperteval.datasets.base_dataset import BaseDataset

class MyCustomDataset(BaseDataset):
    def __init__(self, dataset_path, **kwargs):
        super().__init__(dataset_path, **kwargs)
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        self.data = []
        # 实现自定义的数据加载逻辑
        # ...
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]
    
    def get_statistics(self):
        """获取数据集统计信息"""
        # 实现统计逻辑
        return {
            "total_samples": len(self.data),
            # 其他统计信息...
        }

# 注册自定义数据集类
from xperteval.datasets.registered_datasets import register_dataset_type
register_dataset_type("my-custom", MyCustomDataset)

# 使用自定义数据集
dataset = get_dataset(
    dataset_path="path/to/data",
    dataset_type="my-custom"
)
```

## 数据集分割与交叉验证

### 创建数据集分割

```python
from xperteval.datasets.dataset_manager import DatasetManager

manager = DatasetManager()

# 创建训练/验证/测试分割
manager.create_dataset_split(
    dataset_id="custom_dataset",
    train_ratio=0.8,
    dev_ratio=0.1,
    test_ratio=0.1,
    shuffle=True,
    seed=42
)

# 加载各个分割
train_set = manager.get_dataset(dataset_id="custom_dataset", split="train")
dev_set = manager.get_dataset(dataset_id="custom_dataset", split="dev")
test_set = manager.get_dataset(dataset_id="custom_dataset", split="test")
```

### 交叉验证

```python
import numpy as np
from sklearn.model_selection import KFold

# 加载数据集
dataset = get_dataset(dataset_id="custom_dataset")
data = dataset.data

# 创建 K 折交叉验证
k_fold = KFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_indices, val_indices) in enumerate(k_fold.split(data)):
    print(f"Fold {fold + 1}:")
    
    # 获取训练集和验证集
    train_data = [data[i] for i in train_indices]
    val_data = [data[i] for i in val_indices]
    
    print(f"  训练集大小: {len(train_data)}")
    print(f"  验证集大小: {len(val_data)}")
    
    # 进一步处理...
```

## 数据集预览和统计

XpertEval 提供了数据集预览和统计功能，帮助您了解数据集的基本情况：

```python
# 获取数据集统计信息
stats = dataset.get_statistics()
print(f"样本总数: {stats['total_samples']}")
print(f"任务类型分布: {stats.get('task_type_distribution', {})}")
print(f"类别分布: {stats.get('category_distribution', {})}")

# 预览数据集
def preview_dataset(dataset, n=5):
    """预览数据集的前n个样本"""
    for i in range(min(n, len(dataset))):
        sample = dataset[i]
        print(f"样本 {i+1}:")
        print(f"  ID: {sample['id']}")
        print(f"  问题: {sample['query']}")
        print(f"  答案: {sample['response']}")
        print("-" * 50)

preview_dataset(dataset)
```

## 命令行数据集预览工具

XpertEval 还提供了命令行工具用于预览和检查数据集：

```bash
# 预览数据集
python scripts/preview_dataset.py --dataset-id mmlu --samples 5

# 显示数据集统计信息
python scripts/preview_dataset.py --dataset-id mmlu --stats

# 预览自定义数据集文件
python scripts/preview_dataset.py --file path/to/dataset.jsonl --samples 5
``` 