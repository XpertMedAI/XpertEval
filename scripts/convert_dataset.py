#!/usr/bin/env python
# coding: utf-8
"""
数据集格式转换命令行工具

用于将各种格式的数据集转换为XpertFormat格式。
"""

import os
import sys
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xperteval.datasets.converters import (
    convert_to_xpert_format,
    batch_convert,
    convert_mmlu_to_xpert,
    convert_cmmlu_to_xpert,
    convert_gsm8k_to_xpert,
    convert_math_to_xpert,
    convert_humaneval_to_xpert,
    convert_ceval_to_xpert,
    convert_mmbench_to_xpert,
    convert_llava_bench_to_xpert,
    convert_seed_bench_to_xpert,
    convert_mm_vet_to_xpert
)
from xperteval.datasets.converters.format_validator import validate_file, get_format_guidelines
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

# 支持的数据集类型
SUPPORTED_DATASET_TYPES = [
    'mmlu', 'cmmlu', 'gsm8k', 'math', 'humaneval', 'ceval',
    'mmbench', 'llava_bench', 'seed_bench', 'mm_vet'
]

def parse_args():
    """
    解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='数据集格式转换工具',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # convert命令
    convert_parser = subparsers.add_parser('convert', help='转换数据集')
    convert_parser.add_argument('--input', '-i', required=True, help='输入数据集文件或目录路径')
    convert_parser.add_argument('--output', '-o', required=True, help='输出XpertFormat文件路径')
    convert_parser.add_argument('--type', '-t', required=True, choices=SUPPORTED_DATASET_TYPES,
                              help='数据集类型')
    convert_parser.add_argument('--media-dir', help='媒体文件目录，用于多模态数据集')
    convert_parser.add_argument('--split', default='test', help='数据集分割(dev/test)，默认为"test"')
    convert_parser.add_argument('--language', default='zh', help='语言(en/zh)，默认为"zh"')
    convert_parser.add_argument('--verify-media', action='store_true', help='验证媒体文件是否存在')
    
    # batch命令
    batch_parser = subparsers.add_parser('batch', help='批量转换数据集')
    batch_parser.add_argument('--input-dir', '-i', required=True, help='输入目录')
    batch_parser.add_argument('--output-dir', '-o', required=True, help='输出目录')
    batch_parser.add_argument('--type', '-t', required=True, choices=SUPPORTED_DATASET_TYPES,
                            help='数据集类型')
    batch_parser.add_argument('--pattern', default='*', help='文件匹配模式，默认为"*"')
    batch_parser.add_argument('--recursive', '-r', action='store_true', help='递归处理子目录')
    batch_parser.add_argument('--media-dir', help='媒体文件目录，用于多模态数据集')
    batch_parser.add_argument('--split', default='test', help='数据集分割(dev/test)，默认为"test"')
    batch_parser.add_argument('--language', default='zh', help='语言(en/zh)，默认为"zh"')
    batch_parser.add_argument('--verify-media', action='store_true', help='验证媒体文件是否存在')
    
    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证XpertFormat格式')
    validate_parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    validate_parser.add_argument('--fix', '-f', action='store_true', help='尝试修复并保存')
    
    # guidelines命令
    guidelines_parser = subparsers.add_parser('guidelines', help='显示XpertFormat格式指南')
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    args = parse_args()
    
    if args.command == 'convert':
        # 转换单个数据集
        kwargs = {
            'split': args.split,
            'language': args.language
        }
        
        # 添加媒体目录参数（如果提供）
        if args.media_dir:
            if args.type in ['mmbench', 'llava_bench', 'mm_vet']:
                kwargs['image_dir'] = args.media_dir
            elif args.type == 'seed_bench':
                kwargs['media_dir'] = args.media_dir
        
        # 添加验证媒体文件参数
        if args.verify_media:
            kwargs['verify_media'] = True
        
        # 执行转换
        success = convert_to_xpert_format(
            args.input,
            args.output,
            args.type,
            **kwargs
        )
        
        if success:
            logger.info(f"转换成功: {args.input} -> {args.output}")
            sys.exit(0)
        else:
            logger.error(f"转换失败: {args.input}")
            sys.exit(1)
    
    elif args.command == 'batch':
        # 批量转换数据集
        kwargs = {
            'split': args.split,
            'language': args.language
        }
        
        # 添加媒体目录参数（如果提供）
        if args.media_dir:
            if args.type in ['mmbench', 'llava_bench', 'mm_vet']:
                kwargs['image_dir'] = args.media_dir
            elif args.type == 'seed_bench':
                kwargs['media_dir'] = args.media_dir
        
        # 添加验证媒体文件参数
        if args.verify_media:
            kwargs['verify_media'] = True
        
        # 执行批量转换
        results = batch_convert(
            args.input_dir,
            args.output_dir,
            args.type,
            args.pattern,
            args.recursive,
            **kwargs
        )
        
        # 输出统计信息
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"批量转换完成: {success_count}/{total_count} 个文件成功转换")
        
        if success_count == total_count:
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.command == 'validate':
        # 验证XpertFormat格式
        valid, errors, fixed_file_path = validate_file(args.input, args.fix)
        
        if valid:
            logger.info(f"验证通过: {args.input}")
            sys.exit(0)
        else:
            logger.error(f"验证失败: {args.input}")
            for error in errors:
                logger.error(f"  - {error}")
            
            if fixed_file_path:
                logger.info(f"已修复并保存到: {fixed_file_path}")
            
            sys.exit(1)
    
    elif args.command == 'guidelines':
        # 显示XpertFormat格式指南
        print(get_format_guidelines())
        sys.exit(0)
    
    else:
        # 未指定命令，显示帮助信息
        parse_args.__globals__['parser'].print_help()
        sys.exit(1)

if __name__ == '__main__':
    main() 