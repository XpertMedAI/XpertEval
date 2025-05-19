 ---
layout: default
title: 配置指南
parent: 用户手册
nav_order: 1
---

# 配置指南
{: .no_toc }

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

本文档详细介绍如何配置 XpertEval 框架，包括模型 API 配置、评测参数配置等。

## 模型配置

XpertEval 需要配置至少两个模型的 API 信息才能进行评测。配置文件支持 YAML 或 JSON 格式。

### 配置文件格式

创建一个名为 `models.yaml` 的文件，内容如下：

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

或者使用 JSON 格式：

```json
{
  "default_params": {
    "MAX_TOKENS": 4096,
    "TEMPERATURE": 0.7,
    "TOP_P": 0.95,
    "TOP_K": 40,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.0,
    "REQUEST_TIMEOUT": 120
  },
  "models": [
    {
      "OPENAI_API_BASE": "https://api.openai.com/v1",
      "OPENAI_API_KEY": "sk-xxxx",
      "MODEL_NAME": "gpt-4",
      "MODEL_TYPE": "text",
      "MAIN_API": true
    },
    {
      "OPENAI_API_BASE": "http://localhost:8000/v1",
      "OPENAI_API_KEY": "sk-xxxx",
      "MODEL_NAME": "llama3-70b",
      "MODEL_TYPE": "text",
      "MAIN_API": false
    }
  ]
}
```

### 配置项说明

#### 全局默认参数 (default_params)

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| MAX_TOKENS | 整数 | 4096 | 生成的最大 token 数量 |
| TEMPERATURE | 浮点数 | 0.7 | 生成的随机性，值越大越随机 |
| TOP_P | 浮点数 | 0.95 | 核采样阈值 |
| TOP_K | 整数 | 40 | 考虑的最高概率词数 |
| FREQUENCY_PENALTY | 浮点数 | 0.0 | 频率惩罚系数 |
| PRESENCE_PENALTY | 浮点数 | 0.0 | 存在惩罚系数 |
| REQUEST_TIMEOUT | 整数 | 120 | API 请求超时时间（秒） |

#### 模型配置 (models)

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| OPENAI_API_BASE | 字符串 | 是 | API 服务地址，例如 `https://api.openai.com/v1` |
| OPENAI_API_KEY | 字符串 | 是 | API 密钥 |
| MODEL_NAME | 字符串 | 是 | 模型名称，例如 `gpt-4`、`llama3-70b` |
| MODEL_TYPE | 字符串 | 是 | 模型类型，可选值：`text`、`vision`、`audio`、`mllm` |
| MAIN_API | 布尔值 | 是 | 是否为主评测 API，只能有一个模型设置为 `true` |
| MAX_TOKENS | 整数 | 否 | 覆盖默认的最大 token 数量 |
| TEMPERATURE | 浮点数 | 否 | 覆盖默认的温度参数 |
| TOP_P | 浮点数 | 否 | 覆盖默认的核采样阈值 |
| TOP_K | 整数 | 否 | 覆盖默认的 TOP_K 值 |
| FREQUENCY_PENALTY | 浮点数 | 否 | 覆盖默认的频率惩罚系数 |
| PRESENCE_PENALTY | 浮点数 | 否 | 覆盖默认的存在惩罚系数 |
| REQUEST_TIMEOUT | 整数 | 否 | 覆盖默认的请求超时时间 |

### 配置验证规则

XpertEval 对配置文件进行严格验证，包括：

1. **模型数量检查**：必须配置至少两个模型
2. **主 API 检查**：
   - 如果多个模型设置了 `MAIN_API: true`，则以第一个为准，其余置为 `false`
   - 如果没有模型设置 `MAIN_API: true`，则默认第一个模型为主 API
3. **必需字段检查**：每个模型配置必须包含 `OPENAI_API_BASE`、`OPENAI_API_KEY`、`MODEL_NAME`、`MODEL_TYPE`
4. **字段类型检查**：验证各字段的数据类型是否正确
5. **枚举值检查**：验证 `MODEL_TYPE` 是否为预定义的枚举值之一

## 命令行参数

使用命令行运行评测时，可以指定以下参数：

```bash
python main.py --config models.yaml --dataset_path data/examples/choice_example.jsonl --output_dir results/my_test
```

### 参数说明

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| --config | 字符串 | 是 | - | 模型配置文件路径 |
| --dataset_id | 字符串 | 否* | - | 内置数据集的 ID |
| --dataset_path | 字符串 | 否* | - | 自定义数据集文件路径 |
| --dataset_type | 字符串 | 否 | xpert-format | 数据集类型 |
| --evaluators | 字符串 | 否 | accuracy | 使用的评测指标，多个指标用逗号分隔 |
| --output_dir | 字符串 | 否 | results/<timestamp> | 评测结果输出目录 |
| --report_formats | 字符串 | 否 | markdown,json | 报告格式，可选值：`markdown`、`json`、`html` |
| --batch_size | 整数 | 否 | 1 | 批处理大小 |
| --mode | 字符串 | 否 | auto | 评测模式，可选值：`auto`、`manual` |

*注：`dataset_id` 和 `dataset_path` 必须提供其中之一

## 环境变量配置

XpertEval 也支持通过环境变量进行配置：

```bash
# 设置日志级别
export XPERTEVAL_LOG_LEVEL=DEBUG

# 设置默认配置文件路径
export XPERTEVAL_CONFIG_PATH=./my_config.yaml

# 设置数据集目录
export XPERTEVAL_DATA_DIR=./my_data
```

### 支持的环境变量

| 环境变量名 | 默认值 | 描述 |
|------------|--------|------|
| XPERTEVAL_LOG_LEVEL | INFO | 日志级别，可选值：`DEBUG`、`INFO`、`WARNING`、`ERROR` |
| XPERTEVAL_CONFIG_PATH | ./config.yaml | 默认配置文件路径 |
| XPERTEVAL_DATA_DIR | ./data | 数据集目录 |
| XPERTEVAL_RESULTS_DIR | ./results | 结果输出目录 |
| XPERTEVAL_CACHE_DIR | ~/.cache/xperteval | 缓存目录 |

## 配置最佳实践

### 安全性建议

1. **不要在代码仓库中提交 API 密钥**：
   - 使用环境变量或配置文件模板
   - 将包含实际 API 密钥的配置文件添加到 `.gitignore`

2. **使用配置模板**：
   ```bash
   # 创建配置模板
   cp config_example.yaml my_config.yaml
   
   # 编辑配置文件添加 API 密钥
   vim my_config.yaml
   
   # 使用自定义配置文件
   python main.py --config my_config.yaml ...
   ```

### 多环境配置

对于不同环境（开发、测试、生产），可以创建多个配置文件：

```
config/
├── dev.yaml     # 开发环境配置
├── test.yaml    # 测试环境配置
└── prod.yaml    # 生产环境配置
```

然后在运行时指定相应的配置文件：

```bash
# 开发环境
python main.py --config config/dev.yaml ...

# 测试环境
python main.py --config config/test.yaml ...

# 生产环境
python main.py --config config/prod.yaml ...
```