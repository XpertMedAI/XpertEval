#!/usr/bin/env python
# coding: utf-8
"""
数据集转换工具

提供将各种格式的数据集转换为XpertFormat格式的命令行工具。
这是一个统一的入口点，避免直接使用模块导入方式运行转换器。

用法:
    # 转换MMLU数据集
    python scripts/convert_dataset.py mmlu --source data/downloads/mmlu/abstract_algebra --output data/integrated/mmlu/abstract_algebra.jsonl --split test
    
    # 转换CMMLU数据集
    python scripts/convert_dataset.py cmmlu --source data/downloads/cmmlu/cmmlu_v1_0_1/test --output data/integrated/cmmlu/test_all.jsonl
    
    # 转换GSM8K数据集
    python scripts/convert_dataset.py gsm8k --source data/downloads/gsm8k/main --output data/integrated/gsm8k/main_test.jsonl --split test
    
    # 转换HumanEval数据集
    python scripts/convert_dataset.py humaneval --source data/downloads/humaneval/openai_humaneval/test-00000-of-00001.parquet --output data/integrated/humaneval/humaneval.jsonl
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 导入转换器
from xperteval.datasets.converters import (
    convert_mmlu_to_xpert,
    convert_cmmlu_to_xpert,
    convert_gsm8k_to_xpert,
    convert_humaneval_to_xpert
)
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def main():
    """命令行工具入口函数"""
    
    # 创建父解析器
    parser = argparse.ArgumentParser(
        description='将各种格式的数据集转换为XpertFormat格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  # 转换MMLU数据集
  python scripts/convert_dataset.py mmlu --source data/downloads/mmlu/abstract_algebra --output data/integrated/mmlu/abstract_algebra.jsonl --split test
  
  # 转换CMMLU数据集
  python scripts/convert_dataset.py cmmlu --source data/downloads/cmmlu/cmmlu_v1_0_1/test --output data/integrated/cmmlu/test_all.jsonl
  
  # 转换GSM8K数据集
  python scripts/convert_dataset.py gsm8k --source data/downloads/gsm8k/main --output data/integrated/gsm8k/main_test.jsonl --split test
  
  # 转换HumanEval数据集
  python scripts/convert_dataset.py humaneval --source data/downloads/humaneval/openai_humaneval/test-00000-of-00001.parquet --output data/integrated/humaneval/humaneval.jsonl
"""
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest='dataset_type', help='数据集类型')
    
    # MMLU解析器
    mmlu_parser = subparsers.add_parser('mmlu', help='转换MMLU数据集')
    mmlu_parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    mmlu_parser.add_argument('--output', required=True, help='输出文件路径')
    mmlu_parser.add_argument('--split', default='test', help='数据集分割(test/validation)')
    mmlu_parser.add_argument('--subject', help='学科名称，如果指定则只转换该学科')
    mmlu_parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    # CMMLU解析器
    cmmlu_parser = subparsers.add_parser('cmmlu', help='转换CMMLU数据集')
    cmmlu_parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    cmmlu_parser.add_argument('--output', required=True, help='输出文件路径')
    cmmlu_parser.add_argument('--split', default='test', help='数据集分割(test/dev)')
    cmmlu_parser.add_argument('--subject', help='学科名称，如果指定则只转换该学科')
    cmmlu_parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    # GSM8K解析器
    gsm8k_parser = subparsers.add_parser('gsm8k', help='转换GSM8K数据集')
    gsm8k_parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    gsm8k_parser.add_argument('--output', required=True, help='输出文件路径')
    gsm8k_parser.add_argument('--split', default='test', help='数据集分割(test/train)')
    gsm8k_parser.add_argument('--version', help='数据集版本(main/socratic)，如果指定则只转换该版本')
    gsm8k_parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    # HumanEval解析器
    humaneval_parser = subparsers.add_parser('humaneval', help='转换HumanEval数据集')
    humaneval_parser.add_argument('--source', required=True, help='源数据文件路径')
    humaneval_parser.add_argument('--output', required=True, help='输出文件路径')
    humaneval_parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有指定数据集类型，显示帮助信息
    if not args.dataset_type:
        parser.print_help()
        return 1
    
    # 检查源路径是否存在
    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return 1
    
    # 根据数据集类型选择不同的转换方法
    success = False
    validate = not getattr(args, 'no_validate', False)
    
    if args.dataset_type == 'mmlu':
        params = {
            "split": args.split,
            "validate": validate
        }
        if args.subject:
            params["subject"] = args.subject
        logger.info(f"转换MMLU数据集: {args.source}")
        success = convert_mmlu_to_xpert(args.source, args.output, **params)
    
    elif args.dataset_type == 'cmmlu':
        params = {
            "split": args.split,
            "validate": validate
        }
        if args.subject:
            params["subject"] = args.subject
        logger.info(f"转换CMMLU数据集: {args.source}")
        success = convert_cmmlu_to_xpert(args.source, args.output, **params)
    
    elif args.dataset_type == 'gsm8k':
        params = {
            "split": args.split,
            "validate": validate
        }
        if args.version:
            params["version"] = args.version
        logger.info(f"转换GSM8K数据集: {args.source}")
        success = convert_gsm8k_to_xpert(args.source, args.output, **params)
    
    elif args.dataset_type == 'humaneval':
        logger.info(f"转换HumanEval数据集: {args.source}")
        success = convert_humaneval_to_xpert(args.source, args.output, validate=validate)
    
    # 输出结果
    if success:
        logger.info(f"转换完成，结果保存到: {args.output}")
        return 0
    else:
        logger.error("转换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 