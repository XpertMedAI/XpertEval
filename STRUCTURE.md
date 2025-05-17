# XpertEval - 项目架构设计 (STRUCTURE.md)

## 1. 概述

本文档定义了 XpertEval 项目的目录结构和关键组件的功能。项目采用模块化设计，以便于维护、扩展和协作开发。所有命名均使用英文，但代码内部注释和文档将使用中文。

## 2. 根目录结构

```
.XpertEval/
├── .github/                    # GitHub 相关配置 (例如 workflows 用于 CI/CD)
│   └── workflows/
│       └── docs_deploy.yml     # GitHub Actions 用于部署文档到 GitHub Pages
├── xperteval/                  # 项目核心代码包
│   ├── config/                 # 模型 API 配置、全局参数配置模块
│   │   ├── __init__.py
│   │   └── config_loader.py    # 加载和解析模型及全局配置文件 (yaml/json)
│   ├── core/                   # 评测核心逻辑
│   │   ├── __init__.py
│   │   ├── api_caller.py       # 封装对 OpenAI 兼容 API 的调用逻辑
│   │   ├── auto_eval_engine.py # 自动化评测引擎
│   │   ├── manual_eval_engine.py# 人工评测辅助引擎
│   │   └── base_evaluator.py   # 评测器基类 (定义评测指标接口)
│   ├── datasets/               # 数据集处理与加载
│   │   ├── __init__.py
│   │   ├── base_dataset.py     # 数据集基类
│   │   ├── ms_swift_parser.py  # 解析 ms-swift 格式数据集
│   │   └── registered_datasets.py # 管理和注册已集成的数据集
│   ├── evaluators/             # 具体评测指标实现
│   │   ├── __init__.py
│   │   ├── common/             # 通用能力评测指标
│   │   │   ├── __init__.py
│   │   │   └── accuracy.py     # (示例) 准确率等通用指标
│   │   └── tcm/                # 中医药领域特定评测指标
│   │       ├── __init__.py
│   │       └── diagnosis_eval.py # (示例) 中医诊断准确性等指标
│   ├── models/                 # 模型接口的进一步封装 (如果需要)
│   │   ├── __init__.py
│   │   └── model_handler.py    # 处理不同模型类型的特定逻辑 (可选)
│   ├── reporters/              # 评测报告生成模块
│   │   ├── __init__.py
│   │   └── report_generator.py # 生成多维度对比报告 (图表、文本等)
│   ├── webui/                  # Gradio Web 用户界面
│   │   ├── __init__.py
│   │   ├── app_gradio.py       # Gradio 应用主逻辑
│   │   └── components/         # UI 组件 (可选，如自定义 Gradio 组件)
│   └── utils/                  # 通用工具函数
│       ├── __init__.py
│       ├── file_utils.py       # 文件操作相关工具
│       └── log_utils.py        # 日志配置与记录工具
├── data/                       # 存放评测数据集
│   ├── custom/                 # 用户自定义数据集存放目录
│   │   └── README.md           # 说明自定义数据集格式和放置要求
│   └── integrated/             # 集成的开源/自建数据集
│       ├── tcm_tongue_example/ # (示例) 中医舌诊图片评测集
│       └── common_qa_example/  # (示例) 通用问答评测集
├── docs/                       # 项目文档 (用于 GitHub Pages)
│   ├── _config.yml             # Jekyll 或其他静态站点生成器配置文件 (适配 Ant Design 风格)
│   ├── index.md                # 文档首页
│   ├── quick_start.md          # 快速开始指南
│   ├── user_manual/            # 用户手册
│   │   ├── configuration.md    # 配置指南
│   │   └── web_ui.md           # WebUI 使用说明
│   ├── developer_guide/        # 开发者指南
│   │   ├── architecture.md     # 架构设计 (可引用本 STRUCTURE.md)
│   │   └── extending.md        # 如何扩展 (新评测集、新指标)
│   └── assets/                 # 文档相关的静态资源 (图片、CSS等)
├── tests/                      # 测试代码
│   ├── unit/                   # 单元测试 (unit tests)
│   │   └── test_config_loader.py
│   └── integration/            # 集成测试 (integration tests)
│       └── test_full_eval_flow.py
├── scripts/                    # 辅助脚本
│   ├── run_tests.sh            # 运行测试脚本
│   └── build_docker.sh         # 构建 Docker 镜像脚本
├── results/                    # 评测结果默认输出目录 (由 .gitignore 排除)
├── templates/                  # 模板文件 (例如报告模板)
│   └── report_template.html    # HTML 报告模板示例
├── .gitignore                  # Git 忽略文件配置
├── app.py                      # WebUI (Gradio) 启动入口
├── main.py                     # 命令行评测程序入口
├── config_example.yaml         # 模型API配置文件示例
├── Dockerfile                  # Docker 配置文件
├── LICENSE                     # 开源协议文件 (Apache 2.0)
├── REQUIREMENTS.md             # 项目需求文档 (已创建)
├── README.md                   # 项目介绍文档 (已创建)
├── STRUCTURE.md                # 项目架构设计文档 (本文档)
├── DEV_PLAN.md                 # 项目开发计划文档
├── DEV_RECORDS.md              # 项目开发记录文档
├── requirements.txt            # Python 依赖包列表
└── VERSION                     # 项目版本号文件
```

## 3. 模块/文件功能详解

### 3.1 `xperteval/` (核心代码包)

-   **`config/config_loader.py`**: 
    -   **功能**: 负责加载和验证 `models.yaml` 或 `models.json` 等配置文件。
    -   **内容**: 解析模型API信息（`OPENAI_API_BASE`, `OPENAI_API_KEY`, `MODEL_NAME`, `MODEL_TYPE`, `MAIN_API`等）以及全局默认参数（`MAX_TOKENS`, `TEMPERATURE`等）。校验配置的有效性，如至少两个模型，`MAIN_API`的正确设置。
    -   **中文注释**: 详细说明配置项含义及校验逻辑。

-   **`core/api_caller.py`**: 
    -   **功能**: 封装与 OpenAI API 兼容接口的 HTTP(S) 通信。
    -   **内容**: 实现发送请求、处理响应、错误处理、超时控制、重试机制（可选）。支持不同模态（文本、图像、音频）的API请求格式。
    -   **中文注释**: 详细解释 API 请求参数、响应结构及错误码处理。

-   **`core/auto_eval_engine.py`**: 
    -   **功能**: 驱动自动化评测流程。
    -   **内容**: 协调数据集加载、模型调用（通过 `api_caller.py`）、评测指标计算（调用 `evaluators/` 中的模块）、结果汇总。
    -   **中文注释**: 清晰描述自动化评测的各个步骤和数据流转。

-   **`core/manual_eval_engine.py`**: 
    -   **功能**: 支持人工评测模式的后端逻辑。
    -   **内容**: 从数据集中抽取题目或接收用户输入，调用各模型获取匿名答案，管理人工评分的输入和存储（可临时存储或与 WebUI 交互）。确保满足人工评测的有效性要求（如题目数量）。
    -   **中文注释**: 说明人工评测的流程和数据处理方式。

-   **`core/base_evaluator.py`**: 
    -   **功能**: 定义评测器的抽象基类。
    -   **内容**: 规定评测指标的接口标准，如 `evaluate()` 方法，方便后续扩展新的评测维度。
    -   **中文注释**: 解释基类接口的设计目的和使用方法。

-   **`datasets/`**: 
    -   **`base_dataset.py`**: 数据集基类，定义加载、迭代等通用接口。
    -   **`ms_swift_parser.py`**: 实现对 `ms-swift` 标准数据集格式的解析逻辑，支持多轮对话。
    -   **`registered_datasets.py`**: 提供注册机制，方便按名称引用和加载集成的数据集。
    -   **中文注释**: 说明数据加载逻辑和支持的数据格式。

-   **`evaluators/`**: 
    -   **`common/`**: 存放通用能力评测指标的实现，如文本生成的流畅度、图像描述的准确性等。
    -   **`tcm/`**: 存放中医药领域特定的评测指标实现，如舌象分析准确率、方剂推荐合理性等。
    -   **中文注释**: 详细解释每个评测指标的计算方法和评估维度。

-   **`models/model_handler.py` (可选)**: 
    -   **功能**: 如果不同类型的模型（text, vision, audio, mllm）在API调用前或响应处理后需要特定逻辑，可在此模块中实现。
    -   **内容**: 例如，对视觉模型的输入进行预处理，或对音频模型的输出进行特定格式转换。
    -   **中文注释**: 说明模型特定处理的逻辑。

-   **`reporters/report_generator.py`**: 
    -   **功能**: 根据评测结果生成结构化的评测报告。
    -   **内容**: 支持生成多种格式的报告（如 HTML, Markdown, PDF），包含对比图表（柱状图、雷达图等）、评分汇总、主API为中心的总结。可能使用模板引擎（如 Jinja2）。
    -   **中文注释**: 解释报告的生成逻辑和定制方式。

-   **`webui/app_gradio.py`**: 
    -   **功能**: Gradio Web 应用的入口和主要逻辑。
    -   **内容**: 定义界面布局、组件（API配置、数据集选择、评测启动按钮、进度显示、结果展示、人工打分区域等），并将其与后端评测引擎连接。
    -   **中文注释**: 详细描述Gradio界面的构建和回调函数逻辑。

-   **`utils/`**: 
    -   **`file_utils.py`**: 文件读写、路径操作等辅助函数。
    -   **`log_utils.py`**: 配置全局日志记录器，方便调试和问题追踪。
    -   **中文注释**: 说明各工具函数的功能和使用场景。

### 3.2 `data/` (评测数据集)

-   **`custom/`**: 用户存放自定义数据集的目录。`README.md` 中需详细说明数据格式要求（应与 `ms-swift` 兼容）。
-   **`integrated/`**: 存放项目集成的各类评测数据集，按领域或类型分子目录。
    -   **中文注释**: 每个集成数据集目录下可以有一个简短的 `README.cn.md` 说明数据集来源、内容和格式。

### 3.3 `docs/` (项目文档)

-   **`_config.yml`**: 若使用 Jekyll 或类似工具生成 GitHub Pages，此为配置文件，用于主题、插件、导航等设置，以实现 Ant Design 风格（可能需要引入相应主题或自定义 CSS）。
-   其他 Markdown 文件构成文档的主体内容，如快速入门、用户手册（配置、WebUI）、开发者指南（架构、扩展）等。
    -   **中文**: 所有文档内容均为中文。

### 3.4 `tests/` (测试)

-   **`unit/`**: 针对各模块的小粒度单元测试，确保独立功能的正确性。
-   **`integration/`**: 针对多个模块协同工作的集成测试，如完整的评测流程。
    -   **中文注释**: 测试用例的描述和断言的目的。

### 3.5 `scripts/` (辅助脚本)

-   **`run_tests.sh`**: 自动化运行所有测试用例的脚本。
-   **`build_docker.sh`**: 构建项目 Docker 镜像的脚本。

### 3.6 根目录文件

-   **`app.py`**: 启动 Gradio WebUI 的 Python 脚本。
    -   **中文注释**: 启动参数说明。
-   **`main.py`**: 项目的命令行界面 (CLI) 入口。
    -   **功能**: 解析命令行参数（如配置文件路径、数据集名称、输出目录等），调用自动化评测引擎执行评测，并将结果输出到指定位置或控制台。
    -   **中文注释**: 命令行参数的用法说明。
-   **`config_example.yaml`**: 提供一个模型 API 配置的样例文件，方便用户参考。
-   **`Dockerfile`**: 定义 Docker 镜像的构建步骤，包括依赖安装、代码复制、暴露端口、启动命令等。
-   **`LICENSE`**: Apache 2.0 开源协议文本。
-   **`REQUIREMENTS.md`, `README.md`, `STRUCTURE.md`, `DEV_PLAN.md`**: 项目元文档。
-   **`requirements.txt`**: 列出项目运行所需的所有 Python 依赖及其版本。
-   **`VERSION`**: 纯文本文件，仅包含当前项目的版本号 (例如 `0.1.0`)。
-   **`.gitignore`**: 指定 Git 版本控制系统应忽略的文件和目录（如 `__pycache__/`, `*.pyc`, `results/`, `data/custom/local_only_data/` 等）。

## 4. 技术选型备注

- **配置文件格式**: YAML (首选) 或 JSON，兼顾可读性和易解析性。
- **WebUI框架**: Gradio，快速搭建交互式界面。
- **文档风格**: Ant Design，通过 GitHub Pages 主题或自定义 CSS 实现。
- **版本管理**: `VERSION` 文件 + Git 标签。

此架构设计旨在为 XpertEval 项目的开发提供清晰的蓝图。在实际开发过程中，可能会根据具体需求进行微调。 