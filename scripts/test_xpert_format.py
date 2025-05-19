#!/usr/bin/env python
# coding: utf-8
"""
XpertFormat数据集解析器测试脚本
"""

import os
import sys
import json
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from xperteval.datasets import XpertFormatDataset
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def test_choice_dataset():
    """测试选择题格式数据集"""
    dataset_path = project_root / "data" / "examples" / "choice_example.jsonl"
    dataset = XpertFormatDataset(dataset_path)
    
    logger.info(f"加载选择题数据集，共有 {len(dataset)} 个样本")
    
    # 打印第一个样本
    sample = dataset[0]
    logger.info(f"样本ID: {sample['id']}")
    logger.info(f"问题: {sample['query']}")
    logger.info(f"选项: {sample.get('choices', [])}")
    logger.info(f"答案类型: {sample['answer']['type']}")
    logger.info(f"答案值: {sample['answer']['value']}")
    logger.info(f"任务类型: {sample['meta']['task_type']}")
    
    # 统计信息
    stats = dataset.get_statistics()
    logger.info(f"数据集统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    return len(dataset) > 0

def test_math_dataset():
    """测试数学问题格式数据集"""
    dataset_path = project_root / "data" / "examples" / "math_example.jsonl"
    dataset = XpertFormatDataset(dataset_path)
    
    logger.info(f"加载数学问题数据集，共有 {len(dataset)} 个样本")
    
    # 打印第一个样本
    sample = dataset[0]
    logger.info(f"样本ID: {sample['id']}")
    logger.info(f"问题: {sample['query']}")
    logger.info(f"答案类型: {sample['answer']['type']}")
    logger.info(f"答案值: {sample['answer']['value']}")
    logger.info(f"解释: {sample['answer']['explanation']}")
    logger.info(f"任务类型: {sample['meta']['task_type']}")
    
    # 统计信息
    stats = dataset.get_statistics()
    logger.info(f"数据集统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    return len(dataset) > 0

def test_code_dataset():
    """测试代码生成任务格式数据集"""
    dataset_path = project_root / "data" / "examples" / "code_example.jsonl"
    dataset = XpertFormatDataset(dataset_path)
    
    logger.info(f"加载代码生成任务数据集，共有 {len(dataset)} 个样本")
    
    # 打印第一个样本
    sample = dataset[0]
    logger.info(f"样本ID: {sample['id']}")
    logger.info(f"问题: {sample['query']}")
    logger.info(f"答案类型: {sample['answer']['type']}")
    logger.info(f"编程语言: {sample['meta'].get('language', 'unknown')}")
    logger.info(f"评估指标: {sample.get('evaluation', {}).get('metrics', [])}")
    
    # 统计信息
    stats = dataset.get_statistics()
    logger.info(f"数据集统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    return len(dataset) > 0

def test_multimodal_dataset():
    """测试多模态任务格式数据集"""
    dataset_path = project_root / "data" / "examples" / "multimodal_example.jsonl"
    dataset = XpertFormatDataset(dataset_path)
    
    logger.info(f"加载多模态任务数据集，共有 {len(dataset)} 个样本")
    
    # 打印第一个样本
    sample = dataset[0]
    logger.info(f"样本ID: {sample['id']}")
    logger.info(f"问题: {sample['query']}")
    logger.info(f"文件: {sample.get('files', [])}")
    logger.info(f"是否多模态: {sample.get('is_multimodal', False)}")
    logger.info(f"任务类型: {sample['meta']['task_type']}")
    
    # 统计信息
    stats = dataset.get_statistics()
    logger.info(f"数据集统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    return len(dataset) > 0

def main():
    """主函数"""
    logger.info("开始测试XpertFormat数据集解析器")
    
    tests = [
        ("选择题数据集", test_choice_dataset),
        ("数学问题数据集", test_math_dataset),
        ("代码生成任务数据集", test_code_dataset),
        ("多模态任务数据集", test_multimodal_dataset)
    ]
    
    success_count = 0
    for name, test_func in tests:
        logger.info(f"测试 {name}")
        try:
            if test_func():
                logger.info(f"{name} 测试通过")
                success_count += 1
            else:
                logger.error(f"{name} 测试失败：数据集为空")
        except Exception as e:
            logger.error(f"{name} 测试失败：{e}")
    
    logger.info(f"测试完成，共 {len(tests)} 项测试，通过 {success_count} 项")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 