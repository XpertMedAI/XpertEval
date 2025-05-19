#!/usr/bin/env python
# coding: utf-8
"""
通用评测数据集解析器测试脚本
"""

import os
import sys
import json
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from xperteval.datasets.common_benchmarks import (
    MMLUDataset,
    CMMLUDataset,
    GSM8KDataset,
    MATHDataset,
    HumanEvalDataset,
    CEvalDataset
)
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def create_test_data():
    """创建测试数据"""
    os.makedirs("data/test_data/mmlu", exist_ok=True)
    os.makedirs("data/test_data/cmmlu", exist_ok=True)
    os.makedirs("data/test_data/gsm8k", exist_ok=True)
    os.makedirs("data/test_data/math/algebra", exist_ok=True)
    os.makedirs("data/test_data/human_eval", exist_ok=True)
    os.makedirs("data/test_data/ceval", exist_ok=True)
    
    # 创建MMLU测试数据
    with open("data/test_data/mmlu/test.csv", "w", encoding="utf-8") as f:
        f.write("What is the capital of France?,Paris,London,Berlin,Madrid,A\n")
        f.write("Which planet is closest to the Sun?,Mercury,Venus,Earth,Mars,A\n")
    
    # 创建CMMLU测试数据
    with open("data/test_data/cmmlu/test.csv", "w", encoding="utf-8") as f:
        f.write("中国的首都是哪个城市？,北京,上海,广州,深圳,A\n")
        f.write("长江是中国第几长的河流？,第一,第二,第三,第四,A\n")
    
    # 创建GSM8K测试数据
    with open("data/test_data/gsm8k/test.jsonl", "w", encoding="utf-8") as f:
        f.write('{"question": "John has 5 apples. He buys 2 more. How many apples does he have now?", "answer": "John has 5 apples. He buys 2 more. So he has 5 + 2 = 7 apples. \\nAnswer: 7"}\n')
        f.write('{"question": "Mary has 10 candies. She gives 3 to her friend. How many candies does she have left?", "answer": "Mary has 10 candies. She gives 3 to her friend. So she has 10 - 3 = 7 candies left. \\nAnswer: 7"}\n')
    
    # 创建MATH测试数据
    with open("data/test_data/math/algebra/test.json", "w", encoding="utf-8") as f:
        json.dump([
            {
                "problem": "Solve the equation: $2x + 3 = 7$",
                "level": "Level 1",
                "type": "Algebra",
                "solution": "We have $2x + 3 = 7$. Subtracting 3 from both sides, we get $2x = 4$. Dividing both sides by 2, we get $x = 2$.",
                "answer": "x = 2"
            },
            {
                "problem": "Find the value of $x$ if $3x - 5 = 10$",
                "level": "Level 1",
                "type": "Algebra",
                "solution": "We have $3x - 5 = 10$. Adding 5 to both sides, we get $3x = 15$. Dividing both sides by 3, we get $x = 5$.",
                "answer": "x = 5"
            }
        ], f, ensure_ascii=False, indent=2)
    
    # 创建HumanEval测试数据
    with open("data/test_data/human_eval/test.json", "w", encoding="utf-8") as f:
        json.dump({
            "HumanEval/1": {
                "task_id": "HumanEval/1",
                "prompt": "def add(a, b):\\n    \"\"\"\n    Add two numbers and return the result.\n    \"\"\"\n",
                "entry_point": "add",
                "canonical_solution": "def add(a, b):\\n    return a + b\\n",
                "test": "def test_add():\\n    assert add(1, 2) == 3\\n    assert add(2, 3) == 5\\n",
                "language": "python"
            },
            "HumanEval/2": {
                "task_id": "HumanEval/2",
                "prompt": "def subtract(a, b):\\n    \"\"\"\n    Subtract b from a and return the result.\n    \"\"\"\n",
                "entry_point": "subtract",
                "canonical_solution": "def subtract(a, b):\\n    return a - b\\n",
                "test": "def test_subtract():\\n    assert subtract(3, 1) == 2\\n    assert subtract(5, 2) == 3\\n",
                "language": "python"
            }
        }, f, ensure_ascii=False, indent=2)
    
    # 创建C-Eval测试数据
    with open("data/test_data/ceval/test.json", "w", encoding="utf-8") as f:
        json.dump([
            {
                "id": "1",
                "question": "下列哪个是中国的省会城市？",
                "options": ["北京", "上海", "广州", "成都"],
                "answer": "A",
                "field": "地理",
                "category": "中国地理"
            },
            {
                "id": "2",
                "question": "中国的国花是什么？",
                "options": ["牡丹", "梅花", "菊花", "荷花"],
                "answer": "A",
                "field": "文化",
                "category": "中国文化"
            }
        ], f, ensure_ascii=False, indent=2)
    
    logger.info("测试数据创建完成")

def test_mmlu_dataset():
    """测试MMLU数据集解析器"""
    logger.info("测试MMLU数据集解析器")
    
    dataset = MMLUDataset("data/test_data/mmlu/test.csv")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/mmlu/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def test_cmmlu_dataset():
    """测试CMMLU数据集解析器"""
    logger.info("测试CMMLU数据集解析器")
    
    dataset = CMMLUDataset("data/test_data/cmmlu/test.csv")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/cmmlu/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def test_gsm8k_dataset():
    """测试GSM8K数据集解析器"""
    logger.info("测试GSM8K数据集解析器")
    
    dataset = GSM8KDataset("data/test_data/gsm8k/test.jsonl")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/gsm8k/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def test_math_dataset():
    """测试MATH数据集解析器"""
    logger.info("测试MATH数据集解析器")
    
    dataset = MATHDataset("data/test_data/math")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/math/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def test_human_eval_dataset():
    """测试HumanEval数据集解析器"""
    logger.info("测试HumanEval数据集解析器")
    
    dataset = HumanEvalDataset("data/test_data/human_eval/test.json")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/human_eval/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def test_ceval_dataset():
    """测试C-Eval数据集解析器"""
    logger.info("测试C-Eval数据集解析器")
    
    dataset = CEvalDataset("data/test_data/ceval/test.json")
    
    logger.info(f"样本数量: {len(dataset)}")
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"第一个样本: {json.dumps(sample, ensure_ascii=False, indent=2)}")
    
    # 测试转换
    output_path = "data/test_data/ceval/output.jsonl"
    success = dataset.convert_to_xpert_format(output_path)
    logger.info(f"转换结果: {'成功' if success else '失败'}")
    
    return success

def main():
    """主函数"""
    logger.info("开始测试通用评测数据集解析器")
    
    # 创建测试数据
    create_test_data()
    
    tests = [
        ("MMLU", test_mmlu_dataset),
        ("CMMLU", test_cmmlu_dataset),
        ("GSM8K", test_gsm8k_dataset),
        ("MATH", test_math_dataset),
        ("HumanEval", test_human_eval_dataset),
        ("C-Eval", test_ceval_dataset)
    ]
    
    success_count = 0
    for name, test_func in tests:
        logger.info(f"测试 {name} 数据集解析器")
        try:
            if test_func():
                logger.info(f"{name} 测试通过")
                success_count += 1
            else:
                logger.error(f"{name} 测试失败")
        except Exception as e:
            logger.error(f"{name} 测试失败：{e}")
    
    logger.info(f"测试完成，共 {len(tests)} 个测试，通过 {success_count} 个")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 