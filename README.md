# XpertEval - 全模态大模型一站式评测框架

[![开源协议](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Stars](https://img.shields.io/github/stars/XpertMedAI/XpertEval.svg?style=social&label=Star&maxAge=2592000)](https://github.com/XpertMedAI/XpertEval/stargazers/)
[![GitHub Forks](https://img.shields.io/github/forks/XpertMedAI/XpertEval.svg?style=social&label=Fork&maxAge=2592000)](https://github.com/XpertMedAI/XpertEval/network/members)

**项目语言: 中文** | **作者: [rookie-littleblack](https://github.com/rookie-littleblack)** | **GitHub: [XpertMedAI/XpertEval](https://github.com/XpertMedAI/XpertEval)**

---

## 项目简介

XpertEval 是一个专为全模态大模型设计的通用型、一站式评测框架。它致力于提供一个轻量级、易用、可扩展的解决方案，用于全面评估大模型在各类任务上的表现。特别地，XpertEval 强调对特定专业领域（如中医药）微调后的大模型进行深度评测，同时确保其通用能力的保持性。

## 项目目标

- **核心目标**：构建轻量级框架，支持对中医药领域微调后的全模态（文本/图像/视频/音频）大模型进行能力评测。
- **双重验证**：
    - 评估模型在领域专项能力（如中医四诊、辨证论治、方剂推荐、针灸方案等）上的提升。
    - 检验模型在通用能力（如常识问答、多模态理解、内容创作等）上的保留程度。
- **解决痛点**：
    - **纯API评测**：100% 基于 OpenAI API 兼容接口进行，无需本地部署大模型，降低使用门槛。
    - **多模型对比**：支持至少两个模型同时进行横向对比评测。
    - **双模式评测**：提供自动化评测与人工辅助评测两种模式。

## 核心特性

- **全模态支持**：能够评测文本、图像、音频、视频等多种模态或其组合的理解与生成能力。
- **OpenAI API 兼容**：通过标准化的 API 接口与各类大模型进行交互，配置简单。
- **专业领域扩展**：首期重点支持中医药领域，未来可方便地扩展至其他专业领域。
- **自动化与人工结合**：提供自动化的客观指标评测，辅以灵活的人工主观评价体系。
- **多维度评测报告**：生成详尽的评测报告，从不同角度可视化模型性能，并以主评测模型为基准进行对比。
- **灵活的数据集支持**：集成常用公开评测集，支持自定义数据集，并特别关注中医药相关数据集的建设。
- **Gradio WebUI**：提供友好的图形用户界面，简化配置、执行评测和查看结果的流程。
- **模块化与可扩展**：采用模块化设计，便于开发者贡献新的评测方法、数据集或功能。
- **Docker化部署**：支持 Docker 容器化部署，简化环境配置。

## 快速开始 (示例)

*（此部分将在项目开发到一定阶段后补充详细的安装、配置和运行步骤）*

1.  **环境准备**：
    ```bash
    # git clone https://github.com/XpertMedAI/XpertEval.git
    # cd XpertEval
    # conda create -n xperteval -y python=3.10
    # conda activate xperteval
    # pip install pyyaml
    # pip install tqdm
    # pip install tabulate matplotlib pillow
    # pip install -r requirements.txt
    ```
2.  **配置模型 API**：
    编辑 `config.yaml` (或 `.json`) 文件，填入您的模型 API 信息。确保至少配置两个模型，并指定一个为主API。
    ```yaml
    # 示例 config.yaml
    default_params:
      MAX_TOKENS: 4096
      TEMPERATURE: 0.7
      # ... 其他全局默认参数

    models:
      - OPENAI_API_BASE: "your_openai_api_base_1"
        OPENAI_API_KEY: "your_api_key_1"
        MODEL_NAME: "model_A (e.g., gpt-4)"
        MODEL_TYPE: "mllm"
        MAIN_API: true
        # ... model_A 特定参数 (可选)

      - OPENAI_API_BASE: "your_openai_api_base_2"
        OPENAI_API_KEY: "your_api_key_2"
        MODEL_NAME: "model_B (e.g., a fine-tuned model)"
        MODEL_TYPE: "mllm"
        MAIN_API: false
        # ... model_B 特定参数 (可选)
    ```
3.  **准备评测数据**：
    （说明如何选择内置数据集或放置自定义数据集到 `data/` 目录）

4.  **运行评测 (命令行)**：
    ```bash
    # python main.py --config config.yaml --dataset_name some_dataset --output_dir results/
    ```
5.  **启动 WebUI**：
    ```bash
    # python app.py
    ```
    然后通过浏览器访问 Gradio 界面进行操作。

## 项目状态

 Alpha / 开发中

## 文档

详细的项目文档（包括用户手册、开发指南、API参考等）将部署在：[XpertEval GitHub Pages链接 (待定)]()

## 开源协议

本项目采用 [Apache 2.0](https://opensource.org/licenses/Apache-2.0) 开源协议。

## 如何贡献

我们欢迎各种形式的贡献，包括但不限于：
- 提交 Bug报告和功能建议
- 贡献代码 (Pull Requests)
- 完善文档
- 分享和推广 XpertEval

请在提交 Pull Request 前阅读我们的贡献指南 (CONTRIBUTING.md - 待创建)。

## 联系我们

- **项目仓库**: [XpertMedAI/XpertEval](https://github.com/XpertMedAI/XpertEval) 
- **项目作者**: [rookie-littleblack](https://github.com/rookie-littleblack)