# coding: utf-8
"""
MMLU (Massive Multitask Language Understanding) 数据集转换器

将MMLU格式的数据集转换为XpertFormat格式。
支持从Hugging Face下载的parquet文件和原始CSV文件的转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_mmlu_to_xpert
    
    # 转换单个parquet文件
    convert_mmlu_to_xpert("data/downloads/mmlu/abstract_algebra/test-00000-of-00001.parquet", 
                        "data/integrated/mmlu/abstract_algebra_test.jsonl")
                        
    # 转换一个学科的所有测试数据
    convert_mmlu_to_xpert("data/downloads/mmlu/abstract_algebra", 
                        "data/integrated/mmlu/abstract_algebra.jsonl", 
                        split="test")
                        
    # 转换整个MMLU数据集的测试集
    convert_mmlu_to_xpert("data/downloads/mmlu", 
                        "data/integrated/mmlu/dataset.jsonl", 
                        split="test")

命令行使用:
    # 转换单个parquet文件
    python -m xperteval.datasets.converters.mmlu_converter --source path/to/file.parquet --output path/to/output.jsonl
    
    # 转换一个学科的所有测试数据
    python -m xperteval.datasets.converters.mmlu_converter --source data/downloads/mmlu/abstract_algebra --output data/integrated/mmlu/abstract_algebra.jsonl --split test
    
    # 转换整个MMLU数据集的测试集
    python -m xperteval.datasets.converters.mmlu_converter --source data/downloads/mmlu --output data/integrated/mmlu/dataset.jsonl --split test

备注：
    1. 请先通过命令“git clone https://huggingface.co/datasets/cais/mmlu.git -o data/downloads”将原测试集下载到本地；
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import glob

from ..base_dataset import BaseDataset
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

def convert_mmlu_parquet_to_xpert(source_dir: str, output_path: str, split: str = 'test') -> bool:
    """
    将从Hugging Face下载的MMLU数据集的parquet文件转换为XpertFormat格式
    
    Args:
        source_dir: 数据集目录路径，可以是直接包含parquet文件的目录，也可以包含多个学科子目录
        output_path: 输出文件路径
        split: 数据集分割，如'test', 'validation', 'dev'等
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将MMLU数据集从parquet格式转换为XpertFormat格式...")
    
    # 将路径字符串转换为Path对象，便于后续操作
    source_dir = Path(source_dir)
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return False
    
    # 在当前目录中查找对应分割的parquet文件
    parquet_files = list(source_dir.glob(f"{split}-*.parquet"))
    # 默认使用目录名作为学科名
    subject_name = source_dir.name  
    
    # 收集所有转换后的数据
    all_data = []
    
    # 如果当前目录没有parquet文件，再查找子目录
    if not parquet_files:
        # 查找所有子目录（假设每个子目录对应一个学科）
        # 排除.git等隐藏目录
        subject_dirs = [d for d in source_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not subject_dirs:
            logger.warning(f"在 {source_dir} 中未找到parquet文件或学科子目录")
            return False
        
        # 处理每个学科目录
        for subject_dir in subject_dirs:
            subject_name = subject_dir.name
            logger.info(f"处理学科: {subject_name}")
            
            # 查找对应分割的parquet文件
            parquet_files = list(subject_dir.glob(f"{split}-*.parquet"))
            if not parquet_files:
                logger.warning(f"未找到学科 {subject_name} 的 {split} 分割文件")
                continue
            
            # 处理这个学科的所有parquet文件
            for parquet_file in parquet_files:
                data = process_parquet_file(parquet_file, subject_name)
                all_data.extend(data)
    else:
        # 直接处理当前目录下的parquet文件
        logger.info(f"处理目录 {source_dir} 中的 {len(parquet_files)} 个parquet文件")
        for parquet_file in parquet_files:
            data = process_parquet_file(parquet_file, subject_name)
            all_data.extend(data)
    
    # 如果没有找到任何数据
    if not all_data:
        logger.error("未能成功转换任何数据")
        return False
    
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

def process_parquet_file(parquet_file: Path, subject_name: str = None) -> List[Dict[str, Any]]:
    """
    处理单个parquet文件，将其转换为XpertFormat样本列表
    
    Args:
        parquet_file: parquet文件路径
        subject_name: 学科名称，如果为None则从数据中提取
        
    Returns:
        转换后的样本列表
    """
    logger.info(f"处理文件: {parquet_file}")
    data = []
    
    try:
        # 使用pandas读取parquet文件
        df = pd.read_parquet(parquet_file)
        
        # 逐行处理数据并转换为XpertFormat
        for i, row in df.iterrows():
            # 提取数据字段
            question = row['question']
            # 优先使用行数据中的subject字段，如果没有则使用传入的subject_name，如果都没有则使用'unknown'
            subject = row.get('subject', subject_name) if subject_name else row.get('subject', 'unknown')
            choices = row['choices']
            answer = row['answer']
            
            # 处理choices字段，确保格式正确
            # choices可能是numpy数组或普通列表
            if isinstance(choices, np.ndarray):
                choice_options = choices.tolist()
            elif isinstance(choices, list):
                choice_options = choices
            else:
                logger.warning(f"未知的choices格式: {type(choices)}")
                continue
            
            # 创建符合XpertFormat规范的样本
            sample = {
                "id": f"mmlu_{subject}_{i}",  # 创建唯一ID
                "query": question,            # 问题文本
                "choices": [                  # 选项列表
                    {"id": "A", "content": str(choice_options[0])},
                    {"id": "B", "content": str(choice_options[1])},
                    {"id": "C", "content": str(choice_options[2])},
                    {"id": "D", "content": str(choice_options[3])}
                ],
                "answer": {                   # 答案信息
                    "type": "choice",
                    "value": "ABCD"[answer],  # 将数字索引(0,1,2,3)转换为选项字母(A,B,C,D)
                    "explanation": None
                },
                "meta": {                     # 元数据
                    "task_type": "choice",
                    "subject": subject,
                    "source": "MMLU"
                }
            }
            
            data.append(sample)
        
        logger.info(f"从 {parquet_file} 成功转换了 {len(df)} 个样本")
        return data
            
    except Exception as e:
        logger.error(f"处理文件 {parquet_file} 时出错: {e}")
        return []

def convert_single_mmlu_parquet(parquet_file: str, output_path: str) -> bool:
    """
    转换单个MMLU parquet文件到XpertFormat
    
    Args:
        parquet_file: parquet文件路径
        output_path: 输出文件路径
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始转换单个MMLU parquet文件: {parquet_file}")
    
    try:
        # 读取parquet文件
        df = pd.read_parquet(parquet_file)
        
        # 收集转换后的数据
        all_data = []
        
        # 从文件路径提取学科名称
        file_path = Path(parquet_file)
        subject_name = file_path.parent.name
        
        # 转换为XpertFormat
        for i, row in df.iterrows():
            # 提取数据
            question = row['question']
            subject = row.get('subject', subject_name)
            choices = row['choices']
            answer = row['answer']
            
            # 确保choices是正确的格式并进行转换
            if isinstance(choices, np.ndarray):
                choice_options = choices.tolist()
            elif isinstance(choices, list):
                choice_options = choices
            else:
                logger.warning(f"未知的choices格式: {type(choices)}")
                continue
            
            # 确保有足够的选项
            if len(choice_options) < 4:
                logger.warning(f"选项数量不足4个: {choice_options}")
                continue
            
            # 创建XpertFormat样本
            sample = {
                "id": f"mmlu_{subject}_{i}",
                "query": question,
                "choices": [
                    {"id": "A", "content": str(choice_options[0])},
                    {"id": "B", "content": str(choice_options[1])},
                    {"id": "C", "content": str(choice_options[2])},
                    {"id": "D", "content": str(choice_options[3])}
                ],
                "answer": {
                    "type": "choice",
                    "value": "ABCD"[answer],  # 将数字索引转换为选项字母
                    "explanation": None
                },
                "meta": {
                    "task_type": "choice",
                    "subject": subject,
                    "source": "MMLU"
                }
            }
            
            all_data.append(sample)
        
        # 保存转换后的数据
        output_dir = Path(output_path).parent
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功将 {len(all_data)} 个样本保存到 {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return False

def convert_mmlu_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将MMLU数据集转换为XpertFormat格式
    
    支持转换从Hugging Face下载的parquet文件或原始CSV文件
    
    Args:
        source_path: 数据集文件或目录路径
        output_path: 输出文件路径
        **kwargs: 额外参数
            - split: 数据集分割，默认为'test'
            - subject: 特定学科，默认为None(全部学科)
        
    Returns:
        布尔值，表示转换是否成功
    """
    source_path = Path(source_path)
    split = kwargs.get('split', 'test')
    
    # 检查是否是parquet文件
    if source_path.is_file() and source_path.suffix == '.parquet':
        return convert_single_mmlu_parquet(str(source_path), output_path)
    
    # 检查是否是包含parquet文件的目录
    elif source_path.is_dir():
        parquet_files = list(source_path.glob(f"**/{split}-*.parquet"))
        if parquet_files:
            return convert_mmlu_parquet_to_xpert(str(source_path), output_path, split)
        
        # 如果没有找到parquet文件，尝试使用MMLUDataset进行转换
        try:
            from ..common_benchmarks.mmlu_dataset import MMLUDataset
            dataset = MMLUDataset(str(source_path), split=split, **kwargs)
            return dataset.convert_to_xpert_format(output_path)
        except Exception as e:
            logger.error(f"使用MMLUDataset转换失败: {e}")
            return False
    
    else:
        logger.error(f"不支持的数据源: {source_path}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换MMLU数据集，可处理parquet格式和CSV格式的数据。
    
    用法示例：
        # 转换单个parquet文件
        python -m xperteval.datasets.converters.mmlu_converter --source data/downloads/mmlu/abstract_algebra/test-00000-of-00001.parquet --output data/integrated/mmlu/abstract_algebra_test.jsonl
        
        # 转换一个学科的所有测试数据
        python -m xperteval.datasets.converters.mmlu_converter --source data/downloads/mmlu/abstract_algebra --output data/integrated/mmlu/abstract_algebra.jsonl --split test
        
        # 转换整个MMLU数据集的测试集
        python -m xperteval.datasets.converters.mmlu_converter --source data/downloads/mmlu --output data/integrated/mmlu/dataset.jsonl --split test
    """
    parser = argparse.ArgumentParser(description='将MMLU数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--split', default='test', help='数据集分割(test/validation/dev)')
    parser.add_argument('--subject', help='指定学科(仅在处理CSV格式时使用)')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return 1
    
    # 根据源路径类型选择不同的转换方法
    success = False
    
    if source_path.is_file():
        if source_path.suffix.lower() == '.parquet':
            logger.info(f"转换单个Parquet文件: {source_path}")
            success = convert_single_mmlu_parquet(str(source_path), args.output)
        elif source_path.suffix.lower() == '.csv':
            logger.info(f"转换单个CSV文件: {source_path}")
            try:
                from ..common_benchmarks.mmlu_dataset import MMLUDataset
                dataset = MMLUDataset(str(source_path), split=args.split, subject=args.subject)
                success = dataset.convert_to_xpert_format(args.output)
            except Exception as e:
                logger.error(f"转换CSV文件失败: {e}")
                return 1
        else:
            logger.error(f"不支持的文件格式: {source_path.suffix}")
            return 1
    elif source_path.is_dir():
        logger.info(f"转换目录: {source_path}, 分割: {args.split}")
        # 尝试转换，可能是parquet格式或CSV格式
        success = convert_mmlu_to_xpert(str(source_path), args.output, split=args.split, subject=args.subject)
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