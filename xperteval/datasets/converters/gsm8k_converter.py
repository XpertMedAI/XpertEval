# coding: utf-8
"""
GSM8K (Grade School Math 8K) 数据集转换器

将GSM8K格式的数据集转换为XpertFormat格式。
支持从Hugging Face下载的parquet文件转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_gsm8k_to_xpert
    
    # 转换单个parquet文件
    convert_gsm8k_to_xpert("data/downloads/gsm8k/main/test-00000-of-00001.parquet", 
                          "data/integrated/gsm8k/main_test.jsonl")
                        
    # 转换一个数据集版本的所有测试数据
    convert_gsm8k_to_xpert("data/downloads/gsm8k/main", 
                          "data/integrated/gsm8k/main_test.jsonl", 
                          split="test")
                        
    # 转换整个GSM8K数据集的测试集
    convert_gsm8k_to_xpert("data/downloads/gsm8k", 
                          "data/integrated/gsm8k/dataset.jsonl", 
                          split="test")

命令行使用:
    # 转换单个parquet文件
    python -m xperteval.datasets.converters.gsm8k_converter --source data/downloads/gsm8k/main/test-00000-of-00001.parquet --output data/integrated/gsm8k/main_test.jsonl
    
    # 转换一个数据集版本的所有测试数据
    python -m xperteval.datasets.converters.gsm8k_converter --source data/downloads/gsm8k/main --output data/integrated/gsm8k/main_test.jsonl --split test
    
    # 转换整个GSM8K数据集的测试集（包括main和socratic）
    python -m xperteval.datasets.converters.gsm8k_converter --source data/downloads/gsm8k --output data/integrated/gsm8k/dataset.jsonl --split test
"""

import os
import sys
import json
import re
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ...utils import get_logger
from .format_validator import validate_xpert_format

# 配置日志
logger = get_logger(__name__)

def convert_gsm8k_parquet_to_xpert(source_dir: str, output_path: str, split: str = 'test', validate: bool = True) -> bool:
    """
    将从Hugging Face下载的GSM8K数据集的parquet文件转换为XpertFormat格式
    
    Args:
        source_dir: 数据集目录路径，可以是直接包含parquet文件的目录，也可以包含多个子目录
        output_path: 输出文件路径
        split: 数据集分割，如'test', 'train'等
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将GSM8K数据集从parquet格式转换为XpertFormat格式...")
    
    # 将路径字符串转换为Path对象，便于后续操作
    source_dir = Path(source_dir)
    if not source_dir.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return False
    
    # 在当前目录中查找对应分割的parquet文件
    parquet_files = list(source_dir.glob(f"{split}-*.parquet"))
    # 默认使用目录名作为版本名
    version_name = source_dir.name  
    
    # 收集所有转换后的数据
    all_data = []
    
    # 如果当前目录没有parquet文件，再查找子目录
    if not parquet_files:
        # 查找所有子目录（假设每个子目录对应一个版本）
        # 排除.git等隐藏目录
        version_dirs = [d for d in source_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not version_dirs:
            logger.warning(f"在 {source_dir} 中未找到parquet文件或子目录")
            return False
        
        # 处理每个版本目录
        for version_dir in version_dirs:
            version_name = version_dir.name
            logger.info(f"处理版本: {version_name}")
            
            # 查找对应分割的parquet文件
            parquet_files = list(version_dir.glob(f"{split}-*.parquet"))
            if not parquet_files:
                logger.warning(f"未找到版本 {version_name} 的 {split} 分割文件")
                continue
            
            # 处理这个版本的所有parquet文件
            for parquet_file in parquet_files:
                data = process_parquet_file(parquet_file, version_name)
                all_data.extend(data)
    else:
        # 直接处理当前目录下的parquet文件
        logger.info(f"处理目录 {source_dir} 中的 {len(parquet_files)} 个parquet文件")
        for parquet_file in parquet_files:
            data = process_parquet_file(parquet_file, version_name)
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

def extract_final_answer(answer_text: str) -> str:
    """
    从GSM8K答案文本中提取最终答案
    
    Args:
        answer_text: 带有解题过程的答案文本
        
    Returns:
        最终答案（数字）
    """
    # GSM8K答案格式通常以 "#### 数字" 结尾
    final_answer_match = re.search(r'####\s*([-+]?\d*\.?\d+)', answer_text)
    if final_answer_match:
        return final_answer_match.group(1)
    
    # 如果无法提取标准格式的最终答案，尝试提取最后一个计算结果
    calculation_match = re.findall(r'<<.*?=\s*([-+]?\d*\.?\d+)>>', answer_text)
    if calculation_match:
        return calculation_match[-1]
    
    # 如果都无法提取，返回原始文本
    return answer_text

def process_parquet_file(parquet_file: Path, version_name: str = None) -> List[Dict[str, Any]]:
    """
    处理单个parquet文件，将其转换为XpertFormat样本列表
    
    Args:
        parquet_file: parquet文件路径
        version_name: 数据集版本名称，如'main'或'socratic'
        
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
            answer = row['answer']
            
            # 从答案中提取最终值
            final_answer = extract_final_answer(answer)
            
            # 创建符合XpertFormat规范的样本
            sample = {
                "id": f"gsm8k_{version_name}_{i}",  # 创建唯一ID
                "query": question,                   # 问题文本
                "answer": {                          # 答案信息
                    "type": "step_by_step",
                    "value": final_answer,           # 最终答案
                    "explanation": answer            # 带步骤的完整答案
                },
                "meta": {                            # 元数据
                    "task_type": "math",
                    "source": f"GSM8K-{version_name}"
                }
            }
            
            data.append(sample)
        
        logger.info(f"从 {parquet_file} 成功转换了 {len(df)} 个样本")
        return data
            
    except Exception as e:
        logger.error(f"处理文件 {parquet_file} 时出错: {e}")
        return []

def convert_single_gsm8k_parquet(parquet_file: str, output_path: str, validate: bool = True) -> bool:
    """
    转换单个GSM8K parquet文件到XpertFormat
    
    Args:
        parquet_file: parquet文件路径
        output_path: 输出文件路径
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始转换单个GSM8K parquet文件: {parquet_file}")
    
    try:
        # 从文件路径提取版本名称
        file_path = Path(parquet_file)
        version_name = file_path.parent.name
        
        # 处理parquet文件
        data = process_parquet_file(file_path, version_name)
        
        if not data:
            logger.error(f"未能成功转换任何数据从 {parquet_file}")
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

def convert_gsm8k_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将GSM8K数据集转换为XpertFormat格式
    
    支持转换从Hugging Face下载的parquet文件
    
    Args:
        source_path: 数据集文件或目录路径
        output_path: 输出文件路径
        **kwargs: 额外参数
            - split: 数据集分割，默认为'test'
            - version: 特定版本，如'main'或'socratic'，默认为None(全部版本)
            - validate: 是否验证数据格式，默认为True
        
    Returns:
        布尔值，表示转换是否成功
    """
    source_path = Path(source_path)
    split = kwargs.get('split', 'test')
    version = kwargs.get('version', None)
    validate = kwargs.get('validate', True)
    
    # 检查是否是parquet文件
    if source_path.is_file() and source_path.suffix.lower() == '.parquet':
        return convert_single_gsm8k_parquet(str(source_path), output_path, validate=validate)
    
    # 检查是否是包含parquet文件的目录
    elif source_path.is_dir():
        # 如果指定了version，只处理该版本
        if version:
            version_dir = source_path / version
            if version_dir.exists() and version_dir.is_dir():
                return convert_gsm8k_parquet_to_xpert(str(version_dir), output_path, split, validate=validate)
            else:
                logger.error(f"未找到版本目录: {version_dir}")
                return False
        
        # 处理整个目录
        return convert_gsm8k_parquet_to_xpert(str(source_path), output_path, split, validate=validate)
    
    else:
        logger.error(f"不支持的数据源: {source_path}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换GSM8K数据集
    
    用法：
        python -m xperteval.datasets.converters.gsm8k_converter --source <source_path> --output <output_path> [--split <split>] [--version <version>] [--no-validate]
    """
    parser = argparse.ArgumentParser(description='将GSM8K数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--split', default='test', help='数据集分割(test/train)')
    parser.add_argument('--version', help='数据集版本(main/socratic)，如果指定则只转换该版本')
    parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return 1
    
    # 根据源路径类型选择不同的转换方法
    success = False
    
    if source_path.is_file() and source_path.suffix.lower() == '.parquet':
        logger.info(f"转换单个parquet文件: {source_path}")
        success = convert_single_gsm8k_parquet(str(source_path), args.output, validate=not args.no_validate)
    elif source_path.is_dir():
        params = {
            "split": args.split,
            "validate": not args.no_validate
        }
        if args.version:
            params["version"] = args.version
            logger.info(f"转换特定版本: {args.version}, 分割: {args.split}")
        else:
            logger.info(f"转换目录: {source_path}, 分割: {args.split}")
        success = convert_gsm8k_to_xpert(str(source_path), args.output, **params)
    else:
        logger.error(f"不支持的源路径: {source_path}")
        return 1
    
    if success:
        logger.info(f"转换完成，结果保存到: {args.output}")
        return 0
    else:
        logger.error("转换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 