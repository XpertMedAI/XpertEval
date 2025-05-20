# coding: utf-8
"""
CEval (Chinese Evaluation) 数据集转换器

将CEval格式的数据集转换为XpertFormat格式。
支持从Hugging Face下载的parquet文件转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_ceval_to_xpert
    
    # 转换单个parquet文件
    convert_ceval_to_xpert("data/downloads/ceval/high_school_mathematics/test-00000-of-00001.parquet", 
                          "data/integrated/ceval/high_school_mathematics_test.jsonl")
                        
    # 转换一个学科的所有测试数据
    convert_ceval_to_xpert("data/downloads/ceval/high_school_mathematics", 
                          "data/integrated/ceval/high_school_mathematics.jsonl", 
                          split="test")
                        
    # 转换整个CEval数据集的测试集
    convert_ceval_to_xpert("data/downloads/ceval", 
                          "data/integrated/ceval/dataset.jsonl", 
                          split="test")

命令行使用:
    # 转换单个parquet文件
    python -m xperteval.datasets.converters.ceval_converter --source data/downloads/ceval/high_school_mathematics/test-00000-of-00001.parquet --output data/integrated/ceval/high_school_mathematics_test.jsonl
    
    # 转换一个学科的所有测试数据
    python -m xperteval.datasets.converters.ceval_converter --source data/downloads/ceval/high_school_mathematics --output data/integrated/ceval/high_school_mathematics.jsonl --split test
    
    # 转换整个CEval数据集的测试集
    python -m xperteval.datasets.converters.ceval_converter --source data/downloads/ceval --output data/integrated/ceval/dataset.jsonl --split test
"""

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# 添加项目根目录到路径以便直接执行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 根据执行方式选择合适的导入方式
if __name__ == '__main__':
    # 直接执行脚本时使用绝对导入
    from xperteval.utils import get_logger
    from xperteval.datasets.converters.format_validator import validate_xpert_format
else:
    # 作为模块导入时使用相对导入
    from ...utils import get_logger
    from .format_validator import validate_xpert_format

# 配置日志
logger = get_logger(__name__)

def convert_ceval_parquet_to_xpert(source_dir: str, output_path: str, split: str = 'test', validate: bool = True) -> bool:
    """
    将从Hugging Face下载的CEval数据集的parquet文件转换为XpertFormat格式
    
    Args:
        source_dir: 数据集目录路径，可以是直接包含parquet文件的目录，也可以包含多个学科子目录
        output_path: 输出文件路径
        split: 数据集分割，如'test', 'val', 'dev'等
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将CEval数据集从parquet格式转换为XpertFormat格式...")
    
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
            options = {
                'A': row['A'],
                'B': row['B'],
                'C': row['C'],
                'D': row['D']
            }
            
            # 检查是否有有效的答案字段（不是None、不是空字符串）
            answer = None
            if 'answer' in row and row['answer'] is not None and row['answer'] != '':
                answer = row['answer']
            
            # 检查是否有有效的解释字段（不是None、不是空字符串）
            explanation = None
            if 'explanation' in row and row['explanation'] is not None and row['explanation'] != '':
                explanation = row['explanation']
            
            # 创建符合XpertFormat规范的样本
            sample = {
                "id": f"ceval_{subject_name}_{i}",  # 创建唯一ID
                "query": question,                 # 问题文本
                "choices": [                       # 选项列表
                    {"id": "A", "content": options['A']},
                    {"id": "B", "content": options['B']},
                    {"id": "C", "content": options['C']},
                    {"id": "D", "content": options['D']}
                ],
                "meta": {                          # 元数据
                    "task_type": "choice",
                    "subject": subject_name,
                    "source": "CEval"
                }
            }
            
            # 只有当答案是有效值时，才添加答案字段
            if answer:
                sample["answer"] = {
                    "type": "choice",
                    "value": answer
                }
                # 如果存在解释，添加到答案字段
                if explanation:
                    sample["answer"]["explanation"] = explanation
            
            data.append(sample)
        
        logger.info(f"从 {parquet_file} 成功转换了 {len(df)} 个样本")
        return data
            
    except Exception as e:
        logger.error(f"处理文件 {parquet_file} 时出错: {e}")
        return []

def convert_single_ceval_parquet(parquet_file: str, output_path: str, validate: bool = True) -> bool:
    """
    转换单个CEval parquet文件到XpertFormat
    
    Args:
        parquet_file: parquet文件路径
        output_path: 输出文件路径
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始转换单个CEval parquet文件: {parquet_file}")
    
    try:
        # 从文件路径提取学科名称
        file_path = Path(parquet_file)
        subject_name = file_path.parent.name
        
        # 处理parquet文件
        data = process_parquet_file(file_path, subject_name)
        
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

def convert_ceval_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将CEval数据集转换为XpertFormat格式
    
    支持转换从Hugging Face下载的parquet文件
    
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
    
    # 检查是否是parquet文件
    if source_path.is_file() and source_path.suffix.lower() == '.parquet':
        return convert_single_ceval_parquet(str(source_path), output_path, validate=validate)
    
    # 检查是否是包含parquet文件的目录
    elif source_path.is_dir():
        # 如果指定了subject，只处理该学科
        if subject:
            subject_dir = source_path / subject
            if subject_dir.exists() and subject_dir.is_dir():
                return convert_ceval_parquet_to_xpert(str(subject_dir), output_path, split, validate=validate)
            else:
                logger.error(f"未找到学科目录: {subject_dir}")
                return False
        
        # 处理整个目录
        return convert_ceval_parquet_to_xpert(str(source_path), output_path, split, validate=validate)
    
    else:
        logger.error(f"不支持的数据源: {source_path}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换CEval数据集
    
    用法：
        python -m xperteval.datasets.converters.ceval_converter --source <source_path> --output <output_path> [--split <split>] [--subject <subject>] [--no-validate]
    """
    parser = argparse.ArgumentParser(description='将CEval数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源数据目录或文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--split', default='test', help='数据集分割(test/val/dev)')
    parser.add_argument('--subject', help='学科名称，如果指定则只转换该学科')
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
        success = convert_single_ceval_parquet(str(source_path), args.output, validate=not args.no_validate)
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
        success = convert_ceval_to_xpert(str(source_path), args.output, **params)
    else:
        logger.error(f"不支持的源路径: {source_path}")
        return 1
    
    if success:
        logger.info(f"转换完成，结果保存到: {args.output}")
        return 0
    else:
        logger.error("转换失败")
        return 1

# 直接调用main的入口点，避免使用模块导入方式
def run_cli():
    """直接执行命令行，避免通过python -m方式导入"""
    sys.exit(main())

# 这种方式避免模块被其他模块导入时就执行main函数
if __name__ == "__main__":
    run_cli() 