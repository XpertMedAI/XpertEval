# coding: utf-8
"""
数据集转换工具

提供通用的数据集转换工具函数。
"""

import os
import glob
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union

from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

def convert_to_xpert_format(source_path: str, output_path: str, converter: Callable, **kwargs) -> bool:
    """
    通用的数据集转换函数，将任意格式的数据集转换为XpertFormat格式
    
    Args:
        source_path: 源数据集路径
        output_path: 输出文件路径
        converter: 转换函数，接收source_path和output_path参数
        **kwargs: 传递给converter的额外参数
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始转换数据集: {source_path} -> {output_path}")
    
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用具体的转换器函数
        result = converter(source_path, output_path, **kwargs)
        
        if result:
            logger.info(f"数据集转换成功: {output_path}")
        else:
            logger.error(f"数据集转换失败: {source_path}")
            
        return result
        
    except Exception as e:
        logger.error(f"数据集转换出错: {e}")
        return False

def batch_convert(
    input_dir: str,
    output_dir: str,
    dataset_type: str = None,
    file_pattern: str = "*",
    recursive: bool = False,
    **kwargs
) -> Dict[str, bool]:
    """
    批量转换指定目录下的所有匹配文件
    
    此函数是为了兼容to_xpert_format.py中的batch_convert函数调用方式
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        dataset_type: 数据集类型，用于确定使用哪个转换器
        file_pattern: 文件匹配模式，默认为"*"
        recursive: 是否递归搜索子目录，默认为False
        **kwargs: 传递给转换器的额外参数
        
    Returns:
        转换结果字典，键为文件路径，值为转换是否成功
    """
    from . import (
        convert_mmlu_to_xpert,
        convert_cmmlu_to_xpert,
        convert_gsm8k_to_xpert,
        convert_math_to_xpert,
        convert_humaneval_to_xpert,
        convert_ceval_to_xpert
    )
    
    # 转换器映射
    converter_map = {
        'mmlu': convert_mmlu_to_xpert,
        'cmmlu': convert_cmmlu_to_xpert,
        'gsm8k': convert_gsm8k_to_xpert,
        'math': convert_math_to_xpert,
        'humaneval': convert_humaneval_to_xpert,
        'ceval': convert_ceval_to_xpert
    }
    
    if dataset_type and dataset_type not in converter_map:
        logger.error(f"不支持的数据集类型: {dataset_type}")
        return {}
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找匹配的文件
    search_pattern = os.path.join(input_dir, "**" if recursive else "", file_pattern)
    matched_files = glob.glob(search_pattern, recursive=recursive)
    
    results = {}
    
    for file_path in matched_files:
        if os.path.isfile(file_path):
            # 根据文件名或父目录名确定数据集类型
            file_dataset_type = dataset_type
            if not file_dataset_type:
                # 尝试从路径中猜测数据集类型
                for dt in converter_map.keys():
                    if dt in file_path.lower():
                        file_dataset_type = dt
                        break
            
            if not file_dataset_type:
                logger.warning(f"无法确定文件 {file_path} 的数据集类型，跳过")
                results[file_path] = False
                continue
            
            converter = converter_map.get(file_dataset_type)
            if not converter:
                logger.warning(f"未找到数据集类型 {file_dataset_type} 的转换器，跳过")
                results[file_path] = False
                continue
            
            # 生成输出文件路径
            base_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_path = os.path.join(output_dir, f"{name_without_ext}.jsonl")
            
            try:
                # 执行转换
                logger.info(f"转换文件: {file_path} -> {output_path}")
                result = converter(file_path, output_path, **kwargs)
                results[file_path] = result
            except Exception as e:
                logger.error(f"转换文件 {file_path} 出错: {e}")
                results[file_path] = False
    
    # 输出结果统计
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"批量转换完成: {success_count}/{len(results)} 个文件转换成功")
    
    return results

def batch_convert_datasets(source_dirs: List[str], output_dir: str, converter_map: Dict[str, Callable]) -> Dict[str, bool]:
    """
    批量转换多个数据集
    
    Args:
        source_dirs: 源数据集目录列表
        output_dir: 输出目录
        converter_map: 数据集转换器映射表，键为数据集类型，值为转换函数
        
    Returns:
        转换结果字典，键为数据集路径，值为转换是否成功
    """
    results = {}
    
    for source_dir in source_dirs:
        # 获取数据集类型（假设是路径的最后一个目录名）
        dataset_type = os.path.basename(source_dir)
        
        # 获取对应的转换器
        converter = converter_map.get(dataset_type)
        if not converter:
            logger.warning(f"未找到数据集类型 {dataset_type} 的转换器，跳过")
            results[source_dir] = False
            continue
        
        # 设置输出路径
        output_path = os.path.join(output_dir, f"{dataset_type}.jsonl")
        
        # 执行转换
        logger.info(f"转换数据集: {source_dir} -> {output_path}")
        try:
            result = convert_to_xpert_format(source_dir, output_path, converter)
            results[source_dir] = result
        except Exception as e:
            logger.error(f"转换数据集 {source_dir} 出错: {e}")
            results[source_dir] = False
    
    # 输出结果统计
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"批量转换完成: {success_count}/{len(results)} 个数据集转换成功")
    
    return results 