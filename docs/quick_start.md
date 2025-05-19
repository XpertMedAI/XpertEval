---
layout: default
title: 快速开始
nav_order: 2
toc: true
---

# 快速开始

## 安装

### 系统要求

- Python 3.10
- pip 或 conda 包管理器
- Git (可选，用于克隆仓库)

### 安装步骤

1. 克隆仓库（或下载ZIP包）

```bash
git clone https://github.com/XpertMedAI/XpertEval.git
cd XpertEval
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 验证安装

```bash
python -c "import xperteval; print(f'XpertEval 安装成功，版本 {open(\"VERSION\").read().strip()}')"
```

## 配置模型

XpertEval 需要配置至少两个模型进行对比评测。创建一个配置文件（YAML或JSON格式）：

```yaml
default_params:
  MAX_TOKENS: 4096
  TEMPERATURE: 0.7
  TOP_P: 0.95
  TOP_K: 40
  FREQUENCY_PENALTY: 0.0
  PRESENCE_PENALTY: 0.0
  REQUEST_TIMEOUT: 120

models:
  - OPENAI_API_BASE: "https://api.openai.com/v1"
    OPENAI_API_KEY: "sk-xxxx"
    MODEL_NAME: "gpt-4"
    MODEL_TYPE: "text"
    MAIN_API: true
    
  - OPENAI_API_BASE: "http://localhost:8000/v1"
    OPENAI_API_KEY: "sk-xxxx"
    MODEL_NAME: "llama3-70b"
    MODEL_TYPE: "text"
    MAIN_API: false
```

将此配置保存为 `models.yaml`。

## 运行评测

### 命令行评测

使用内置示例数据集运行评测：

```bash
python main.py --config models.yaml --dataset_path data/examples/choice_example.jsonl
```

指定输出目录：

```bash
python main.py --config models.yaml --dataset_path data/examples/choice_example.jsonl --output_dir results/my_test
```

### 使用Web界面

启动Gradio Web界面：

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:7860`。

## 查看结果

评测完成后，结果将保存在指定的输出目录（默认为 `results/<timestamp>/`）。

结果包括：
- `report.md`：Markdown格式的评测报告
- `report.json`：JSON格式的详细评测数据
- `report.html`：HTML格式的可视化报告（如果启用）

## 常见问题

### API连接问题

如果遇到API连接问题，请检查：
1. API地址是否正确
2. API密钥是否有效
3. 网络连接是否正常

### 内存不足

对于大型数据集，可以使用批处理模式：

```bash
python main.py --config models.yaml --dataset_path large_dataset.jsonl --batch_size 10
```

### 自定义评测指标

要使用自定义评测指标，请参阅[开发者指南](/developer_guide/extending.html) 