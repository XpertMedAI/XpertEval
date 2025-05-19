# coding: utf-8
"""
CMMLU (Chinese Massive Multitask Language Understanding) 数据集转换器

将CMMLU格式的数据集转换为XpertFormat格式。
支持从原始CSV文件转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_cmmlu_to_xpert
    
    # 转换单个CSV文件
    convert_cmmlu_to_xpert("data/downloads/cmmlu/cmmlu_v1_0_1/test/agronomy.csv", 
                          "data/integrated/cmmlu/agronomy_test.jsonl")
                        
    # 转换一个学科的所有测试数据
    convert_cmmlu_to_xpert("data/downloads/cmmlu/cmmlu_v1_0_1/test", 
                          "data/integrated/cmmlu/test_all.jsonl")
                        
    # 转换整个CMMLU数据集的测试集
    convert_cmmlu_to_xpert("data/downloads/cmmlu/cmmlu_v1_0_1", 
                          "data/integrated/cmmlu/dataset.jsonl", 
                          split="test")

命令行使用:
    # 转换单个CSV文件
    python -m xperteval.datasets.converters.cmmlu_converter --source data/downloads/cmmlu/cmmlu_v1_0_1/test/agronomy.csv --output data/integrated/cmmlu/agronomy_test.jsonl
    
    # 转换一个目录下的所有CSV文件
    python -m xperteval.datasets.converters.cmmlu_converter --source data/downloads/cmmlu/cmmlu_v1_0_1/test --output data/integrated/cmmlu/test_all.jsonl
    
    # 转换整个CMMLU数据集的指定分割
    python -m xperteval.datasets.converters.cmmlu_converter --source data/downloads/cmmlu/cmmlu_v1_0_1 --output data/integrated/cmmlu/dataset.jsonl --split test
"""

import os
import sys
import json
import argparse
import pandas as pd
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import glob

from ...utils import get_logger
from .format_validator import validate_xpert_format

# 配置日志
logger = get_logger(__name__)

def convert_cmmlu_csv_to_xpert(source_dir: str, output_path: str, split: str = 'test', validate: bool = True) -> bool:
    """
    将CMMLU数据集的CSV文件转换为XpertFormat格式
    
    Args:
        source_dir: 数据集目录路径，可以是直接包含CSV文件的目录，也可以包含多个子目录
        output_path: 输出文件路径
        split: 数据集分割，如'test', 'dev'等
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将CMMLU数据集转换为XpertFormat格式...")
    
    # 将路径字符串转换为Path对象，便于后续操作
    source_dir = Path(source_dir)
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return False
    
    # 是否存在split子目录
    split_dir = source_dir / split
    if split_dir.exists() and split_dir.is_dir():
        source_dir = split_dir
    
    # 在当前目录中查找CSV文件
    csv_files = list(source_dir.glob("*.csv"))
    
    # 收集所有转换后的数据
    all_data = []
    
    if not csv_files:
        logger.warning(f"在 {source_dir} 中未找到CSV文件")
        return False
    
    # 处理发现的所有CSV文件
    for csv_file in csv_files:
        # 从文件名中获取学科名称
        subject_name = csv_file.stem
        logger.info(f"处理学科: {subject_name}")
        
        data = process_csv_file(csv_file, subject_name)
        all_data.extend(data)
    
    # 如果没有找到任何数据
    if not all_data:
        logger.error("未能成功转换任何数据")
        return False
    
    # 验证数据格式
    if validate:
        logger.info(f"验证转换后的数据格式...")
        is_valid, errors, _ = validate_xpert_format(all_data)
        if not is_valid:
            logger.warning(f"数据格式验证失败，发现 {len(errors)} 个问题:")
            for i, error in enumerate(errors[:10]):  # 只显示前10个错误
                logger.warning(f"  {i+1}. {error}")
            if len(errors) > 10:
                logger.warning(f"  ... 及其他 {len(errors) - 10} 个问题")
            # 即使有错误也继续保存
            logger.warning("尽管存在格式问题，仍将保存转换后的数据")
        else:
            logger.info("数据格式验证成功")
    
    # 保存转换后的数据
    try:
        # 确保输出目录存在
        output_dir = Path(output_path).parent
        os.makedirs(output_dir, exist_ok=True)
        
        # 以JSONL格式写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功将 {len(all_data)} 个样本保存到 {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"保存转换后的数据失败: {e}")
        return False

def process_csv_file(csv_file: Path, subject_name: str = None) -> List[Dict[str, Any]]:
    """
    处理单个CSV文件，将其转换为XpertFormat样本列表
    
    Args:
        csv_file: CSV文件路径
        subject_name: 学科名称
        
    Returns:
        转换后的样本列表
    """
    logger.info(f"处理文件: {csv_file}")
    data = []
    
    try:
        # 使用pandas读取CSV文件
        df = pd.read_csv(csv_file)
        
        # 逐行处理数据并转换为XpertFormat
        for _, row in df.iterrows():
            # 提取数据字段
            # CMMLU CSV格式：index, Question, A, B, C, D, Answer
            question = row['Question']
            options = [row['A'], row['B'], row['C'], row['D']]
            answer = row['Answer']  # 答案是字母 A, B, C, D
            
            # 将字母答案转换为对应索引 (0-based)
            answer_mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            answer_idx = answer_mapping.get(answer, 0)
            
            # 创建符合XpertFormat规范的样本
            sample = {
                "id": f"cmmlu_{subject_name}_{len(data)}",  # 创建唯一ID
                "query": question,            # 问题文本
                "choices": [                  # 选项列表
                    {"id": "A", "content": str(options[0])},
                    {"id": "B", "content": str(options[1])},
                    {"id": "C", "content": str(options[2])},
                    {"id": "D", "content": str(options[3])}
                ],
                "answer": {                   # 答案信息
                    "type": "choice",
                    "value": answer,          # 直接使用字母答案
                    "explanation": None
                },
                "meta": {                     # 元数据
                    "task_type": "choice",
                    "subject": subject_name,
                    "source": "CMMLU"
                }
            }
            
            data.append(sample)
        
        logger.info(f"从 {csv_file} 成功转换了 {len(df)} 个样本")
        return data
            
    except Exception as e:
        logger.error(f"处理文件 {csv_file} 时出错: {e}")
        return []

def convert_single_cmmlu_csv(csv_file: str, output_path: str, validate: bool = True) -> bool:
    """
    转换单个CMMLU CSV文件到XpertFormat
    
    Args:
        csv_file: CSV文件路径
        output_path: 输出文件路径
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始转换单个CMMLU CSV文件: {csv_file}")
    
    try:
        # 从文件路径提取学科名称
        file_path = Path(csv_file)
        subject_name = file_path.stem
        
        # 处理CSV文件
        data = process_csv_file(file_path, subject_name)
        
        if not data:
            logger.error(f"未能成功转换任何数据从 {csv_file}")
            return False
        
        # 验证数据格式
        if validate:
            logger.info(f"验证转换后的数据格式...")
            is_valid, errors, _ = validate_xpert_format(data)
            if not is_valid:
                logger.warning(f"数据格式验证失败，发现 {len(errors)} 个问题:")
                for i, error in enumerate(errors[:10]):  # 只显示前10个错误
                    logger.warning(f"  {i+1}. {error}")
                if len(errors) > 10:
                    logger.warning(f"  ... 及其他 {len(errors) - 10} 个问题")
                # 即使有错误也继续保存
                logger.warning("尽管存在格式问题，仍将保存转换后的数据")
            else:
                logger.info("数据格式验证成功")
        
        # 保存转换后的数据
        output_dir = Path(output_path).parent
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功将 {len(data)} 个样本保存到 {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return False

def convert_cmmlu_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将CMMLU数据集转换为XpertFormat格式
    
    支持转换CMMLU原始CSV文件
    
    Args:
        source_path: 数据集文件或目录路径
        output_path: 输出文件路径
        **kwargs: 额外参数
            - split: 数据集分割，默认为'test'
            - subject: 特定学科，默认为None(全部学科)
            - validate: 是否验证数据格式，默认为True
        
    Returns:
        布尔值，表示转换是否成功
    """
    source_path = Path(source_path)
    split = kwargs.get('split', 'test')
    subject = kwargs.get('subject', None)
    validate = kwargs.get('validate', True)
    
    # 检查是否是CSV文件
    if source_path.is_file() and source_path.suffix.lower() == '.csv':
        return convert_single_cmmlu_csv(str(source_path), output_path, validate=validate)
    
    # 检查是否是包含CSV文件的目录
    elif source_path.is_dir():
        # 如果指定了subject，只处理该学科
        if subject:
            # 根据source_path是否包含split目录来确定正确的文件路径
            split_dir = source_path / split
            if split_dir.exists() and split_dir.is_dir():
                csv_file = split_dir / f"{subject}.csv"
            else:
                csv_file = source_path / f"{subject}.csv"
            
            if csv_file.exists():
                return convert_single_cmmlu_csv(str(csv_file), output_path, validate=validate)
            else:
                logger.error(f"未找到学科 {subject} 的CSV文件: {csv_file}")
                return False
        
        # 处理整个目录
        return convert_cmmlu_csv_to_xpert(str(source_path), output_path, split, validate=validate)
    
    else:
        logger.error(f"不支持的数据源: {source_path}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换CMMLU数据集
    
    用法：
        python -m xperteval.datasets.converters.cmmlu_converter --source <source_path> --output <output_path> [--split <split>] [--subject <subject>] [--no-validate]
    """
    parser = argparse.ArgumentParser(description='将CMMLU数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--split', default='test', help='数据集分割(test/dev)')
    parser.add_argument('--subject', help='学科名称，如果指定则只转换该学科')
    parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return 1
    
    # 根据源路径类型选择不同的转换方法
    success = False
    
    if source_path.is_file() and source_path.suffix.lower() == '.csv':
        logger.info(f"转换单个CSV文件: {source_path}")
        success = convert_single_cmmlu_csv(str(source_path), args.output, validate=not args.no_validate)
    elif source_path.is_dir():
        params = {
            "split": args.split,
            "validate": not args.no_validate
        }
        if args.subject:
            params["subject"] = args.subject
            logger.info(f"转换特定学科: {args.subject}, 分割: {args.split}")
        else:
            logger.info(f"转换目录: {source_path}, 分割: {args.split}")
        success = convert_cmmlu_to_xpert(str(source_path), args.output, **params)
    else:
        logger.error(f"不支持的源路径: {source_path}")
        return 1
    
    if success:
        logger.info(f"转换完成，结果保存到: {args.output}")
        return 0
    else:
        logger.error("转换失败")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 