# coding: utf-8
"""
数据集格式转换工具

提供各种数据集格式到XpertFormat的转换功能。
"""

import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from ..common_benchmarks import (
    MMLUDataset,
    CMMLUDataset,
    GSM8KDataset,
    MATHDataset,
    HumanEvalDataset,
    CEvalDataset
)
from ..multimodal_benchmarks import (
    MMBenchDataset,
    LLaVABenchDataset,
    SEEDBenchDataset,
    MMVetDataset
)
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

# 数据集类型映射
DATASET_TYPE_MAP = {
    'mmlu': MMLUDataset,
    'cmmlu': CMMLUDataset,
    'gsm8k': GSM8KDataset,
    'math': MATHDataset,
    'humaneval': HumanEvalDataset,
    'ceval': CEvalDataset,
    'mmbench': MMBenchDataset,
    'llava_bench': LLaVABenchDataset,
    'seed_bench': SEEDBenchDataset,
    'mm_vet': MMVetDataset
}

def convert_to_xpert_format(
    input_path: str, 
    output_path: str, 
    dataset_type: str,
    **kwargs
) -> bool:
    """
    通用的数据集格式转换函数
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        dataset_type: 数据集类型，必须是DATASET_TYPE_MAP中的一个键
        **kwargs: 额外参数，将传递给具体的转换函数
        
    Returns:
        布尔值，表示转换是否成功
    """
    # 检查数据集类型是否支持
    dataset_type = dataset_type.lower()
    if dataset_type not in DATASET_TYPE_MAP:
        supported_types = ", ".join(DATASET_TYPE_MAP.keys())
        logger.error(f"不支持的数据集类型: {dataset_type}。支持的类型有: {supported_types}")
        return False
    
    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        logger.error(f"输入路径不存在: {input_path}")
        return False
    
    # 创建输出目录（如果不存在）
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 根据数据集类型选择相应的转换函数
    try:
        # 实例化对应的数据集类
        dataset_class = DATASET_TYPE_MAP[dataset_type]
        dataset = dataset_class(input_path, **kwargs)
        
        # 转换并保存
        success = dataset.convert_to_xpert_format(output_path)
        
        if success:
            logger.info(f"成功将 {dataset_type} 数据集转换为XpertFormat并保存到 {output_path}")
            
            # 输出数据集统计信息
            stats = dataset.get_statistics()
            logger.info(f"数据集统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        else:
            logger.error(f"转换 {dataset_type} 数据集失败")
        
        return success
    
    except Exception as e:
        logger.error(f"转换数据集时发生错误: {e}")
        return False

# 以下是针对各种特定数据集格式的转换函数

def convert_mmlu_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将MMLU格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - subject: 学科名称，可选
            - split: 数据集分割(dev/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'mmlu', **kwargs)

def convert_cmmlu_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将CMMLU格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - subject: 学科名称，可选
            - split: 数据集分割(dev/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'cmmlu', **kwargs)

def convert_gsm8k_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将GSM8K格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - split: 数据集分割(train/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'gsm8k', **kwargs)

def convert_math_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将MATH格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - level: 难度级别，可选
            - type: 数学分支，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'math', **kwargs)

def convert_humaneval_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将HumanEval格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - language: 编程语言，默认为"python"
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'humaneval', **kwargs)

def convert_ceval_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将C-Eval格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - field: 领域，可选
            - split: 数据集分割(dev/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'ceval', **kwargs)

def convert_mmbench_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将MMBench格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - image_dir: 图像文件目录，可选
            - split: 数据集分割(dev/test)，可选
            - language: 语言(en/zh)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'mmbench', **kwargs)

def convert_llava_bench_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将LLaVA-Bench格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - image_dir: 图像文件目录，可选
            - split: 数据集分割(dev/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'llava_bench', **kwargs)

def convert_seed_bench_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将SEED-Bench格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - media_dir: 媒体文件目录，可选
            - split: 数据集分割(dev/test)，可选
            - verify_media: 是否验证媒体文件存在，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'seed_bench', **kwargs)

def convert_mm_vet_to_xpert(input_path: str, output_path: str, **kwargs) -> bool:
    """
    将MM-Vet格式数据集转换为XpertFormat
    
    Args:
        input_path: 输入数据集文件或目录路径
        output_path: 输出XpertFormat文件路径
        **kwargs: 额外参数
            - image_dir: 图像文件目录，可选
            - split: 数据集分割(dev/test)，可选
            
    Returns:
        布尔值，表示转换是否成功
    """
    return convert_to_xpert_format(input_path, output_path, 'mm_vet', **kwargs)

def batch_convert(
    input_dir: str,
    output_dir: str,
    dataset_type: str,
    file_pattern: str = "*",
    recursive: bool = False,
    **kwargs
) -> Dict[str, bool]:
    """
    批量转换数据集
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        dataset_type: 数据集类型
        file_pattern: 文件匹配模式，默认为"*"
        recursive: 是否递归处理子目录，默认为False
        **kwargs: 额外参数，将传递给convert_to_xpert_format
        
    Returns:
        字典，键为输入文件路径，值为转换是否成功
    """
    results = {}
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"输入目录不存在或不是目录: {input_dir}")
        return results
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取文件列表
    glob_pattern = "**/" + file_pattern if recursive else file_pattern
    files = list(input_path.glob(glob_pattern))
    
    if not files:
        logger.warning(f"在 {input_dir} 中没有找到匹配的文件")
        return results
    
    # 批量转换
    for file_path in files:
        if file_path.is_file():
            relative_path = file_path.relative_to(input_path)
            output_path = Path(output_dir) / f"{relative_path.stem}.jsonl"
            
            # 创建输出子目录（如果需要）
            os.makedirs(output_path.parent, exist_ok=True)
            
            # 执行转换
            success = convert_to_xpert_format(
                str(file_path),
                str(output_path),
                dataset_type,
                **kwargs
            )
            
            results[str(file_path)] = success
    
    # 输出统计信息
    success_count = sum(1 for success in results.values() if success)
    logger.info(f"批量转换完成: {success_count}/{len(results)} 个文件成功转换")
    
    return results 