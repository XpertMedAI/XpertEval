# 快速开始

本指南将帮助您快速上手 XpertEval 框架，了解如何安装、配置和运行基本的模型评测。

## 1. 安装

### 1.1 环境要求

- Python 3.8 或更高版本
- pip 或 conda 包管理器

### 1.2 安装步骤

#### 方法一：从 GitHub 克隆

```bash
# 克隆仓库
git clone https://github.com/yourusername/xperteval.git
cd xperteval

# 创建并激活虚拟环境（可选但推荐）
conda create -n xperteval python=3.8
conda activate xperteval

# 安装依赖
pip install -r requirements.txt
```

#### 方法二：使用 Docker

```bash
# 构建 Docker 镜像
docker build -t xperteval .

# 运行 Docker 容器
docker run -it --name xperteval-container -p 7860:7860 xperteval
```

## 2. 配置

XpertEval 需要配置至少两个模型的 API 信息才能进行评测。配置文件支持 YAML 或 JSON 格式。

### 2.1 创建配置文件

创建一个名为 `config.yaml` 的文件，内容如下：

```yaml
default_params:
  MAX_TOKENS: 4096
  TEMPERATURE: 0.7
  TOP_P: 0.95
  TOP_K: 0.95
  FREQUENCY_PENALTY: 0.0
  PRESENCE_PENALTY: 0.0
  REQUEST_TIMEOUT: 120

models:
  - MODEL_NAME: "gpt-4"
    MODEL_TYPE: "text"
    OPENAI_API_BASE: "https://api.openai.com/v1"
    OPENAI_API_KEY: "your-api-key-1"
    MAIN_API: true
    
  - MODEL_NAME: "claude-3-opus-20240229"
    MODEL_TYPE: "text"
    OPENAI_API_BASE: "https://api.anthropic.com/v1/messages"
    OPENAI_API_KEY: "your-api-key-2"
    MAIN_API: false
```

> **注意**：请将 `your-api-key-1` 和 `your-api-key-2` 替换为您的实际 API 密钥。

### 2.2 配置说明

- `default_params`：全局默认参数，适用于所有模型
- `models`：模型配置列表，至少需要两个模型
  - `MODEL_NAME`：模型名称
  - `MODEL_TYPE`：模型类型，可选值：`text`、`vision`、`audio`、`mllm`
  - `OPENAI_API_BASE`：API 服务地址
  - `OPENAI_API_KEY`：API 密钥
  - `MAIN_API`：是否为主评测 API，只能有一个模型设置为 `true`

## 3. 运行评测

### 3.1 命令行评测

使用内置评测数据集：

```bash
python main.py --config config.yaml --dataset_id mmlu --evaluators accuracy
```

使用自定义数据集：

```bash
python main.py --config config.yaml --dataset_path data/custom/my_dataset.jsonl --dataset_type xpert-format
```

### 3.2 参数说明

- `--config`：模型配置文件路径
- `--dataset_id`：内置数据集的 ID
- `--dataset_path`：自定义数据集文件路径
- `--dataset_type`：数据集类型，默认为 `xpert-format`
- `--evaluators`：使用的评测指标，多个指标用逗号分隔
- `--output_dir`：评测结果输出目录
- `--report_formats`：报告格式，可选值：`markdown`、`json`、`html`

### 3.3 启动 Web UI

XpertEval 提供了基于 Gradio 的 Web 界面，方便进行评测配置和结果查看：

```bash
python app.py
```

启动后，在浏览器中访问 `http://localhost:7860` 即可使用 Web UI。

## 4. 示例

### 4.1 基本评测示例

```bash
# 使用 MMLU 数据集评测模型
python main.py --config config.yaml --dataset_id mmlu --evaluators accuracy,f1_score

# 使用选择题示例数据集
python main.py --config config.yaml --dataset_path data/examples/choice_example.jsonl
```

### 4.2 多模态评测示例

```bash
# 使用 MMBench 多模态数据集
python main.py --config config.yaml --dataset_id mmbench
```

### 4.3 人工评测示例

```bash
# 启动人工评测模式
python main.py --config config.yaml --dataset_id mmlu --mode manual
```

## 5. 查看评测报告

评测完成后，结果将保存在指定的输出目录（默认为 `results/<timestamp>/`）中，包括：

- `report.md`：Markdown 格式的评测报告
- `report.json`：JSON 格式的详细评测结果
- `report.html`：HTML 格式的可视化评测报告（如果指定了 `html` 格式）

## 6. 下一步

- 了解如何[创建自定义数据集](./datasets/dataset_usage.md#4-创建自定义数据集)
- 学习如何[配置和使用 Web UI](./user_manual/web_ui.md)
- 探索[支持的评测指标](./user_manual/metrics.md)
- 查看[架构设计](./developer_guide/architecture.md)，了解如何扩展框架 