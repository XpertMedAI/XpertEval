---
layout: default
title: 数据集文档
nav_order: 3
has_children: true
permalink: /datasets
---

# XpertEval 数据集文档
{: .no_toc }

XpertEval 框架支持多种评测数据集，包括通用文本评测数据集、多模态评测数据集以及专业领域（如中医药）评测数据集。本文档提供 XpertEval 数据集相关功能的概述和指南。

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## 数据集格式

XpertEval 使用统一的 XpertFormat 格式来表示各种评测数据集。这种格式基于 JSONL（JSON Lines），支持多种任务类型和多模态内容。详细的格式规范请参阅 [XpertFormat 规范文档](./xpert_format_spec.html)。

## 支持的数据集

XpertEval 目前支持以下类型的评测数据集：

### 通用文本评测数据集

- **MMLU (Massive Multitask Language Understanding)**：包含57个学科领域的多选题评测集，测试模型的知识广度
- **CMMLU (Chinese Massive Multitask Language Understanding)**：专注于中文知识评测，涵盖67个中文学科领域
- **GSM8K (Grade School Math 8K)**：小学数学应用题，需要多步推理
- **MATH**：高中和大学水平的数学问题，包含复杂公式，需要形式化推理
- **HumanEval**：代码生成任务，需要根据描述生成完整可运行的函数
- **C-Eval**：中文评测集，包含多个领域的选择题

### 多模态评测数据集

- **MMBench**：视觉-语言理解任务，需要模型理解图像内容并回答问题
- **LLaVA-Bench**：对话式视觉-语言任务，评测模型对图像的理解和描述能力
- **SEED-Bench**：包含图像和视频理解任务，测试模型对视觉内容的多方面理解能力
- **MM-Vet**：专注于复杂的视觉推理任务，包括图表理解、视觉常识推理等

### 专业领域评测数据集

- **中医药领域评测数据集**：正在开发中，将包括中医四诊信息判定、中医辨证论治、方剂推荐等任务

## 数据集工具

XpertEval 提供了一系列工具来处理和管理评测数据集：

- **数据集转换工具**：将各种格式的数据集转换为统一的 XpertFormat 格式，详见 [数据集转换工具文档](./dataset_conversion.html)
- **数据集管理器**：提供数据集下载、转换、分割、采样和过滤等功能
- **数据集预览工具**：用于预览和检查数据集内容

## 使用指南

关于如何在 XpertEval 框架中使用各种评测数据集，请参阅 [数据集使用指南](./dataset_usage.html)。

## 自定义数据集

XpertEval 支持创建和使用自定义评测数据集。您可以：

1. 创建符合 XpertFormat 规范的 JSONL 文件
2. 实现自定义数据集类，继承 `BaseDataset` 类
3. 使用数据集转换工具将现有数据集转换为 XpertFormat 格式

详细指南请参阅 [数据集使用指南](./dataset_usage.html) 中的"创建自定义数据集"部分。

## 相关脚本

XpertEval 提供了以下与数据集相关的命令行脚本：

- `scripts/convert_dataset.py`：数据集格式转换工具
- `scripts/preview_dataset.py`：数据集预览工具
- `scripts/test_dataset_manager.py`：数据集管理器测试工具

## 数据集目录结构

XpertEval 使用以下目录结构来组织评测数据集：

```
data/
├── custom/                 # 用户自定义数据集
├── downloads/              # 数据集下载临时目录
├── examples/               # 示例数据集
│   ├── choice_example.jsonl
│   ├── math_example.jsonl
│   ├── code_example.jsonl
│   └── multimodal_example.jsonl
└── integrated/             # 集成的开源/自建数据集
    ├── mmlu/
    │   ├── dataset.jsonl   # 主数据集文件
    │   ├── train.jsonl     # 训练集分割
    │   ├── dev.jsonl       # 验证集分割
    │   ├── test.jsonl      # 测试集分割
    │   └── original/       # 原始格式数据文件
    ├── cmmlu/
    └── ...
``` 