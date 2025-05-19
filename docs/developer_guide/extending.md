 ---
layout: default
title: 扩展指南
parent: 开发者指南
nav_order: 2
---

# 扩展指南
{: .no_toc }

<details open markdown="block">
  <summary>
    目录
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

本文档介绍如何扩展 XpertEval 框架的功能，包括添加新的数据集、评测指标、模型类型等。

## 添加新的数据集

XpertEval 支持多种评测数据集，您可以通过以下方式添加新的数据集支持。

### 添加新的数据集解析器

1. 创建新的数据集解析器类，继承 `BaseDataset` 类：

```python
# xperteval/datasets/common_benchmarks/my_dataset.py
from xperteval.datasets.base_dataset import BaseDataset

class MyDataset(BaseDataset):
    """我的自定义数据集解析器"""
    
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
```

2. 在 `registered_datasets.py` 中注册新数据集类型：

```python
# xperteval/datasets/registered_datasets.py
from xperteval.datasets.common_benchmarks.my_dataset import MyDataset

# 添加到 DATASET_REGISTRY 字典
DATASET_REGISTRY.update({
    "my-dataset": {
        "class": MyDataset,
        "name": "我的数据集",
        "description": "这是一个自定义数据集",
        "type": "text"  # 或 "vision", "audio", "multi" 等
    }
})
```

### 添加数据集转换器

如果您需要将自定义格式转换为 XpertFormat，可以添加新的转换器：

```python
# xperteval/datasets/converters/to_xpert_format.py
from xperteval.datasets.converters.to_xpert_format import register_converter

@register_converter("my-format")
def convert_my_format(input_path, output_path, **kwargs):
    """
    将自定义格式转换为 XpertFormat
    
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

### 集成开源数据集

要集成开源评测数据集，您需要：

1. 在 `datasets_config.json` 中添加数据集信息：

```json
{
  "my-dataset": {
    "name": "我的数据集",
    "description": "这是一个自定义数据集",
    "download_url": "https://example.com/my-dataset.zip",
    "type": "text",
    "format": "my-format",
    "version": "1.0.0"
  }
}
```

2. 实现数据集下载和转换逻辑（如果需要）：

```python
# xperteval/datasets/dataset_manager.py 中添加相应的处理逻辑
```

## 添加新的评测指标

要添加新的评测指标，您需要创建一个新的评测器类，继承 `BaseEvaluator` 类。

### 通用评测指标

```python
# xperteval/evaluators/common/my_metric.py
from xperteval.core.base_evaluator import BaseEvaluator

class MyMetricEvaluator(BaseEvaluator):
    """我的自定义评测指标"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化代码...
    
    def evaluate(self, predictions, references):
        """
        计算评测指标
        
        Args:
            predictions: 模型预测结果列表
            references: 参考答案列表
        
        Returns:
            dict: 包含指标名称和分数的字典
        """
        # 实现评测逻辑
        scores = []
        for pred, ref in zip(predictions, references):
            # 计算单个样本的分数
            score = self._calculate_score(pred, ref)
            scores.append(score)
        
        # 返回评测结果
        return {
            "my_metric": sum(scores) / len(scores) if scores else 0
        }
    
    def _calculate_score(self, prediction, reference):
        """计算单个样本的分数"""
        # 实现具体的分数计算逻辑
        # ...
        return score
```

### 中医药领域评测指标

```python
# xperteval/evaluators/tcm/my_tcm_metric.py
from xperteval.core.base_evaluator import BaseEvaluator

class MyTcmMetricEvaluator(BaseEvaluator):
    """中医药领域自定义评测指标"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化代码...
    
    def evaluate(self, predictions, references):
        """实现评测逻辑"""
        # ...
        return {
            "tcm_metric": score
        }
```

### 注册评测指标

在 `xperteval/evaluators/__init__.py` 中注册新的评测指标：

```python
# xperteval/evaluators/__init__.py
from xperteval.evaluators.common.my_metric import MyMetricEvaluator
from xperteval.evaluators.tcm.my_tcm_metric import MyTcmMetricEvaluator

# 添加到 EVALUATOR_REGISTRY 字典
EVALUATOR_REGISTRY.update({
    "my_metric": MyMetricEvaluator,
    "tcm_metric": MyTcmMetricEvaluator
})
```

## 添加新的模型类型

如果您需要支持新的模型类型，需要修改以下模块：

### 更新配置验证逻辑

在 `xperteval/config/config_loader.py` 中更新模型类型验证：

```python
# xperteval/config/config_loader.py
def _validate_model_config(model_config):
    # ...
    # 更新 MODEL_TYPE 的有效值
    valid_model_types = ["text", "vision", "audio", "mllm", "my_new_type"]
    if model_config.get("MODEL_TYPE") not in valid_model_types:
        raise ValueError(f"MODEL_TYPE 必须是以下值之一: {', '.join(valid_model_types)}")
    # ...
```

### 更新 API 调用逻辑

在 `xperteval/core/api_caller.py` 中添加新模型类型的处理：

```python
# xperteval/core/api_caller.py
def invoke_model_api(model_config, request_payload):
    # ...
    # 根据模型类型构造请求
    model_type = model_config.get("MODEL_TYPE")
    if model_type == "my_new_type":
        # 处理新模型类型的请求
        # ...
    # ...
```

## 添加新的报告格式

要添加新的报告格式，您需要修改 `xperteval/reporters/report_generator.py`：

```python
# xperteval/reporters/report_generator.py
class ReportGenerator:
    # ...
    
    def generate_report(self, output_formats, output_dir, main_api_name):
        # ...
        for format in output_formats:
            if format == "markdown":
                self._generate_markdown_report(output_dir, main_api_name)
            elif format == "json":
                self._generate_json_report(output_dir)
            elif format == "html":
                self._generate_html_report(output_dir, main_api_name)
            elif format == "my_format":
                self._generate_my_format_report(output_dir, main_api_name)
            # ...
    
    def _generate_my_format_report(self, output_dir, main_api_name):
        """生成自定义格式的报告"""
        # 实现报告生成逻辑
        # ...
```

## 扩展 WebUI

要扩展 WebUI 功能，您需要修改 `xperteval/webui/app_gradio.py`：

### 添加新的界面组件

```python
# xperteval/webui/app_gradio.py
def create_gradio_app():
    # ...
    with gr.Blocks() as app:
        # ...
        with gr.Tab("我的新功能"):
            # 添加新的 Gradio 组件
            input_text = gr.Textbox(label="输入")
            output_text = gr.Textbox(label="输出")
            submit_btn = gr.Button("提交")
            
            # 添加回调函数
            submit_btn.click(
                fn=my_new_function,
                inputs=[input_text],
                outputs=[output_text]
            )
        # ...
    return app

def my_new_function(text):
    """新功能的实现"""
    # ...
    return result
```

## 添加新的命令行参数

要添加新的命令行参数，您需要修改 `main.py`：

```python
# main.py
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="XpertEval 命令行工具")
    # ...
    # 添加新的命令行参数
    parser.add_argument("--my-option", help="我的新选项")
    # ...
    return parser.parse_args()

def main():
    args = parse_args()
    # 处理新的命令行参数
    if args.my_option:
        # ...
    # ...
```

## 单元测试

为您的新功能添加单元测试，确保其正确性：

```python
# tests/unit/test_my_feature.py
import unittest
from xperteval.your_module import your_function

class TestMyFeature(unittest.TestCase):
    def test_your_function(self):
        # 测试代码
        result = your_function(input_data)
        self.assertEqual(result, expected_output)
        # ...

if __name__ == "__main__":
    unittest.main()
```

## 文档更新

最后，为您的新功能添加文档：

1. 更新相关的 Markdown 文档
2. 添加代码注释
3. 更新 README.md（如适用）

例如，如果您添加了新的数据集支持，可以更新 `docs/datasets/index.md` 文件：

```markdown
## 支持的数据集

XpertEval 目前支持以下类型的评测数据集：

### 通用文本评测数据集

- ...
- **我的数据集**：这是一个自定义数据集，用于...
```