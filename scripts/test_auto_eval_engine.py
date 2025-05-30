#!/usr/bin/env python
# coding: utf-8
"""
测试自动化评测引擎的功能
"""

import os
import sys
import json
from pathlib import Path

# 将项目根目录添加到系统路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xperteval.core.auto_eval_engine import AutoEvalEngine
from xperteval.datasets.xpert_format import XpertFormatDataset
from xperteval.evaluators import get_evaluator

def test_auto_eval_engine():
    """测试自动化评测引擎的基本功能"""
    print("开始测试自动化评测引擎...")
    
    # 加载示例数据集
    dataset_path = Path("data/examples/choice_example.jsonl")
    if not dataset_path.exists():
        print(f"错误: 示例数据集不存在: {dataset_path}")
        return False
    
    dataset = XpertFormatDataset(str(dataset_path))
    print(f"成功加载数据集，样本数量: {len(dataset)}")
    
    # 创建模型配置
    model_configs = [
        {
            "OPENAI_API_BASE": "https://api.example1.com/v1",
            "OPENAI_API_KEY": "fake_key_1",
            "MODEL_NAME": "test-model-1",
            "MODEL_TYPE": "text",
            "MAIN_API": True,
            "MAX_TOKENS": 1000,
            "TEMPERATURE": 0.5
        },
        {
            "OPENAI_API_BASE": "https://api.example2.com/v1",
            "OPENAI_API_KEY": "fake_key_2",
            "MODEL_NAME": "test-model-2",
            "MODEL_TYPE": "text",
            "MAIN_API": False,
            "MAX_TOKENS": 1000,
            "TEMPERATURE": 0.7
        }
    ]
    
    # 创建评测器
    evaluators = [get_evaluator("accuracy")]
    
    # 创建临时输出目录
    output_dir = Path("results/test_auto_eval_engine")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建评测引擎
    try:
        engine = AutoEvalEngine(
            model_configs=model_configs,
            dataset=dataset,
            evaluators=evaluators,
            output_dir=str(output_dir)
        )
        print("成功创建评测引擎")
    except Exception as e:
        print(f"创建评测引擎失败: {e}")
        return False
    
    # 由于我们使用的是假的API配置，实际运行评测会失败
    # 这里仅测试初始化和结构是否正确
    print("评测引擎初始化成功，API调用将使用模拟数据")
    
    # 打印评测引擎的基本信息
    print(f"模型数量: {len(engine.model_configs)}")
    print(f"评测器数量: {len(engine.evaluators)}")
    print(f"输出目录: {engine.output_dir}")
    
    print("测试完成")
    return True

if __name__ == "__main__":
    success = test_auto_eval_engine()
    sys.exit(0 if success else 1) 