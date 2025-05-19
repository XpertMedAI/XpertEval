---
layout: default
title: 首页
nav_order: 1
permalink: /
---

# XpertEval - 全模态大模型一站式评测框架
{: .fs-9 }

轻量级、全面的大模型评测工具，支持通用能力和专业领域评测
{: .fs-6 .fw-300 }

[快速开始](/quick_start.html){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[查看GitHub](https://github.com/XpertMedAI/XpertEval){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## 主要特点

- **领域定制与通用性兼顾**：既评估模型在中医药领域的专业表现，也监控其通用能力的稳定性
- **轻量化与易用性**：100% 基于 OpenAI API 兼容接口进行评测，无需复杂的本地模型部署
- **多模型对比分析**：支持至少两个模型同时进行评测，提供横向对比分析
- **评测模式多样性**：同时支持自动化评测和人工辅助评测，满足不同评测需求
- **多模态支持**：支持文本、图像、音频、视频等多种模态的评测任务

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/XpertMedAI/XpertEval.git
cd xperteval

# 安装依赖
pip install -r requirements.txt

# 运行示例评测
python main.py --config config_example.yaml --dataset_path data/examples/choice_example.jsonl
```

## 文档目录

- [快速开始](./quick_start)
- 用户手册
  - [配置指南](./user_manual/configuration)
  - [WebUI 使用说明](./user_manual/web_ui)
- 数据集文档
  - [数据集概览](./datasets/index)
  - [XpertFormat 规范](./datasets/xpert_format_spec)
  - [数据集转换工具](./datasets/dataset_conversion)
  - [数据集使用指南](./datasets/dataset_usage)
- 开发者指南
  - [架构设计](./developer_guide/architecture)
  - [扩展指南](./developer_guide/extending)

## 支持的评测能力

### 通用能力评测

- 自我认知
- 企业/单位认知
- 常识问答
- 图像描述
- 声音识别
- 文本摘要
- 实体抽取
- 关系抽取

### 中医药专业能力评测

- 中医四诊信息判定（望诊、闻诊、问诊、切诊）
- 中医辨证论治
- 方剂推荐
- 其他中医疗法推荐

### 性能评测

- 响应速度
- 吞吐量
- Token 使用效率

## 支持的数据集

XpertEval 支持多种评测数据集，包括：

- **通用文本评测数据集**：MMLU、CMMLU、GSM8K、MATH、HumanEval、C-Eval 等
- **多模态评测数据集**：MMBench、LLaVA-Bench、SEED-Bench、MM-Vet 等
- **中医药领域评测数据集**：正在开发中

详细信息请参阅 [数据集文档](/datasets/index)。

## 贡献

欢迎贡献代码、报告问题或提出新功能建议！请参阅 [贡献指南](./developer_guide/contributing) 了解详情。

---

## 许可证

本项目采用 Apache 2.0 许可证。详见 [LICENSE](https://github.com/XpertMedAI/XpertEval/blob/main/LICENSE) 文件。 