---
layout: default
title: 开发者指南
nav_order: 5
has_children: true
permalink: /developer_guide
toc: true
---

# XpertEval 开发者指南
{: .no_toc }

欢迎使用 XpertEval 开发者指南！本指南提供了 XpertEval 框架的架构设计、扩展方法和贡献指南，帮助开发者理解框架并进行功能扩展。

## 指南内容

本开发者指南包含以下内容：

- [架构设计](./developer_guide/architecture.html)：详细介绍 XpertEval 框架的架构设计
- [扩展指南](./developer_guide/extending.html)：说明如何扩展 XpertEval 框架的功能

## 快速参考

### 项目结构

```
.XpertEval/
├── xperteval/                  # 项目核心代码包
│   ├── config/                 # 模型 API 配置模块
│   ├── core/                   # 评测核心逻辑
│   ├── datasets/               # 数据集处理与加载
│   ├── evaluators/             # 评测指标实现
│   ├── models/                 # 模型接口封装
│   ├── reporters/              # 报告生成模块
│   ├── webui/                  # Gradio Web 界面
│   └── utils/                  # 通用工具函数
├── data/                       # 评测数据集
├── docs/                       # 项目文档
├── tests/                      # 测试代码
├── scripts/                    # 辅助脚本
└── ...
```

### 核心模块

- **配置管理**：`xperteval/config/config_loader.py`
- **数据集处理**：`xperteval/datasets/`
- **API 调用**：`xperteval/core/api_caller.py`
- **评测引擎**：`xperteval/core/auto_eval_engine.py`, `xperteval/core/manual_eval_engine.py`
- **评测指标**：`xperteval/evaluators/`
- **报告生成**：`xperteval/reporters/report_generator.py`
- **Web 界面**：`xperteval/webui/app_gradio.py`

## 开发环境设置

### 克隆仓库

```bash
git clone https://github.com/XpertMedAI/XpertEval.git
cd XpertEval
```

### 创建开发环境

```bash
# 使用 conda 创建环境
conda create -n xperteval-dev -y python=3.10
conda activate xperteval-dev

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 运行测试

```bash
# 运行单元测试
python -m unittest discover -s tests/unit

# 运行集成测试
python -m unittest discover -s tests/integration

# 使用脚本运行所有测试
bash scripts/run_tests.sh
```

## 代码规范

### Python 代码风格

- 遵循 PEP 8 编码规范
- 使用 4 个空格缩进
- 行长度限制为 100 字符
- 使用 Google 风格的文档字符串

### 注释规范

- 所有函数、类和模块都应有中文注释
- 复杂逻辑应有详细的行内注释
- 文档字符串应包含参数、返回值和异常说明

### 提交规范

- 提交信息应简洁明了，描述变更内容
- 使用前缀标识变更类型，如 `feat:`、`fix:`、`docs:`、`test:` 等
- 每个提交应专注于单一功能或修复

## 贡献流程

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码变更
4. 确保测试通过
5. 提交 Pull Request

## 获取帮助

如果您在开发过程中遇到任何问题，可以：

1. 查阅本文档的相关章节
2. 检查[项目 GitHub 仓库](https://github.com/XpertMedAI/XpertEval)的 Issues 部分
3. 提交新的 Issue 描述您的问题
4. 联系项目维护者获取支持