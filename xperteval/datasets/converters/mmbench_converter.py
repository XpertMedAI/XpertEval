# coding: utf-8
"""
MMBench (Multimodal Benchmark) 数据集转换器

将MMBench格式的数据集转换为XpertFormat格式。
支持从MMBench数据集下载的TSV文件转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_mmbench_to_xpert
    
    # 转换单个TSV文件
    convert_mmbench_to_xpert("data/downloads/mmbench/MMBench_TEST_EN_legacy.tsv", 
                           "data/integrated/mmbench/mmbench_test_en.jsonl")
                           
    # 转换一个目录下的所有TSV文件
    convert_mmbench_to_xpert("data/downloads/mmbench", 
                           "data/integrated/mmbench/dataset.jsonl")

命令行使用:
    # 转换单个TSV文件
    python -m xperteval.datasets.converters.mmbench_converter --source path/to/file.tsv --output path/to/output.jsonl
    
    # 转换目录中所有MMBench和CCBench文件
    python -m xperteval.datasets.converters.mmbench_converter --source data/downloads/mmbench --output data/integrated/mmbench/dataset.jsonl

备注：
    1. 图像数据以Base64格式存储在TSV文件中，转换时会保留这种格式。
    2. 测试集（TEST）没有答案字段，而开发集（DEV）有答案字段。
"""

import os
import sys
import json
import argparse
import base64
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ..base_dataset import BaseDataset
from ...utils import get_logger
from .format_validator import validate_xpert_format

# 配置日志
logger = get_logger(__name__)

def convert_mmbench_tsv_to_xpert(source_path: str, output_path: str, validate: bool = True) -> bool:
    """
    将MMBench格式的TSV文件转换为XpertFormat格式
    
    Args:
        source_path: TSV文件路径
        output_path: 输出文件路径
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将MMBench TSV文件转换为XpertFormat格式: {source_path}")
    
    try:
        # 使用pandas读取TSV文件
        df = pd.read_csv(source_path, sep='\t', quoting=csv.QUOTE_ALL)
        
        # 获取文件名用于确定类型
        file_name = Path(source_path).name.lower()
        is_dev = 'dev' in file_name
        is_cn = 'cn' in file_name
        is_ccbench = 'ccbench' in file_name
        
        logger.info(f"检测到文件类型: {'开发集' if is_dev else '测试集'}, {'中文' if is_cn else '英文'}, {'CCBench' if is_ccbench else 'MMBench'}")
        
        # 转换数据
        all_data = []
        
        for i, row in df.iterrows():
            # 为每一行创建唯一ID
            entry_id = f"mmbench_{'cc' if is_ccbench else 'mm'}_{row['index']}"
            
            # 准备query，如果有hint提示信息，附加到query中
            query = row['question']
            if 'hint' in row and pd.notna(row['hint']) and row['hint']:
                query = f"{query}\n\n提示: {row['hint']}"
            
            # 创建XpertFormat样本
            sample = {
                "id": entry_id,
                "query": query,
                "choices": [
                    {"id": "A", "content": row['A']},
                    {"id": "B", "content": row['B']}
                ],
                "files": [{
                    "path": f"image_{row['index']}.jpg",  # 虚拟路径，需要提供以通过验证
                    "type": "image",
                    "content": row['image']  # Base64编码的图像
                }],
                "meta": {
                    "task_type": "choice",
                    "category": row['category']
                }
            }
            
            # 添加标签信息，合并自l2-category、source等字段
            tags = []
            
            # 添加二级分类（如果存在）
            if 'l2-category' in row and pd.notna(row['l2-category']) and row['l2-category']:
                tags.append(f"l2:{row['l2-category']}")
            
            # 添加来源（如果存在）
            if 'source' in row and pd.notna(row['source']) and row['source']:
                tags.append(f"source:{row['source']}")
            
            # 添加分割信息
            if 'split' in row and pd.notna(row['split']) and row['split']:
                tags.append(f"split:{row['split']}")
            
            # 添加数据集类型
            tags.append("CCBench" if is_ccbench else "MMBench")
            
            # 添加语言信息
            tags.append("zh" if is_cn else "en")
            
            # 设置标签
            if tags:
                sample["meta"]["tags"] = tags
                
            # 设置语言
            sample["meta"]["language"] = "zh" if is_cn else "en"
            
            # 添加C、D选项（如果存在）
            if 'C' in row and pd.notna(row['C']) and row['C']:
                sample["choices"].append({"id": "C", "content": row['C']})
            
            if 'D' in row and pd.notna(row['D']) and row['D']:
                sample["choices"].append({"id": "D", "content": row['D']})
            
            # 添加答案（如果存在，Dev集中有，Test集中没有）
            if 'answer' in row and pd.notna(row['answer']):
                sample["answer"] = {
                    "type": "choice",
                    "value": row['answer'],
                    "explanation": None
                }
            
            all_data.append(sample)
        
        logger.info(f"已从 {source_path} 转换 {len(all_data)} 个样本")
        
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
        output_dir = Path(output_path).parent
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功将 {len(all_data)} 个样本保存到 {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"处理文件 {source_path} 时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def convert_mmbench_dir_to_xpert(source_dir: str, output_path: str, validate: bool = True) -> bool:
    """
    将目录中的MMBench TSV文件转换为XpertFormat格式
    
    Args:
        source_dir: 源目录路径
        output_path: 输出文件路径
        validate: 是否验证转换后的数据格式
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将MMBench目录转换为XpertFormat格式: {source_dir}")
    
    source_dir = Path(source_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"源目录不存在或不是目录: {source_dir}")
        return False
    
    # 查找所有MMBench和CCBench的TSV文件
    tsv_files = []
    for pattern in ["MMBench_*.tsv", "CCBench_*.tsv", "CCBench*.tsv", "MMBench*.tsv"]:
        tsv_files.extend(list(source_dir.glob(pattern)))
    
    if not tsv_files:
        logger.error(f"在目录 {source_dir} 中没有找到MMBench或CCBench的TSV文件")
        return False
    
    logger.info(f"在目录 {source_dir} 中找到 {len(tsv_files)} 个TSV文件")
    
    # 转换所有TSV文件
    all_data = []
    
    for tsv_file in tsv_files:
        # 忽略错误的或临时文件
        if "GMAI_mm_bench_TEST" in tsv_file.name:
            logger.info(f"跳过错误位置的文件: {tsv_file.name}")
            continue
            
        logger.info(f"处理文件: {tsv_file.name}")
        
        try:
            # 使用pandas读取TSV文件
            df = pd.read_csv(tsv_file, sep='\t', quoting=csv.QUOTE_ALL)
            
            # 获取文件名用于确定类型
            file_name = tsv_file.name.lower()
            is_dev = 'dev' in file_name
            is_cn = 'cn' in file_name
            is_ccbench = 'ccbench' in file_name
            
            # 转换数据
            for i, row in df.iterrows():
                # 为每一行创建唯一ID
                entry_id = f"mmbench_{'cc' if is_ccbench else 'mm'}_{row['index']}"
                
                # 准备query，如果有hint提示信息，附加到query中
                query = row['question']
                if 'hint' in row and pd.notna(row['hint']) and row['hint']:
                    query = f"{query}\n\n提示: {row['hint']}"
                
                # 创建XpertFormat样本
                sample = {
                    "id": entry_id,
                    "query": query,
                    "choices": [
                        {"id": "A", "content": row['A']},
                        {"id": "B", "content": row['B']}
                    ],
                    "files": [{
                        "path": f"image_{row['index']}.jpg",  # 虚拟路径，需要提供以通过验证
                        "type": "image",
                        "content": row['image']  # Base64编码的图像
                    }],
                    "meta": {
                        "task_type": "choice",
                        "category": row['category']
                    }
                }
                
                # 添加标签信息，合并自l2-category、source等字段
                tags = []
                
                # 添加二级分类（如果存在）
                if 'l2-category' in row and pd.notna(row['l2-category']) and row['l2-category']:
                    tags.append(f"l2:{row['l2-category']}")
                
                # 添加来源（如果存在）
                if 'source' in row and pd.notna(row['source']) and row['source']:
                    tags.append(f"source:{row['source']}")
                
                # 添加分割信息
                if 'split' in row and pd.notna(row['split']) and row['split']:
                    tags.append(f"split:{row['split']}")
                
                # 添加文件名信息
                tags.append(f"file:{tsv_file.name}")
                
                # 添加数据集类型
                tags.append("CCBench" if is_ccbench else "MMBench")
                
                # 添加语言信息
                tags.append("zh" if is_cn else "en")
                
                # 设置标签
                if tags:
                    sample["meta"]["tags"] = tags
                    
                # 设置语言
                sample["meta"]["language"] = "zh" if is_cn else "en"
                
                # 添加C、D选项（如果存在）
                if 'C' in row and pd.notna(row['C']) and row['C']:
                    sample["choices"].append({"id": "C", "content": row['C']})
                
                if 'D' in row and pd.notna(row['D']) and row['D']:
                    sample["choices"].append({"id": "D", "content": row['D']})
                
                # 添加答案（如果存在，Dev集中有，Test集中没有）
                if 'answer' in row and pd.notna(row['answer']):
                    sample["answer"] = {
                        "type": "choice",
                        "value": row['answer'],
                        "explanation": None
                    }
                
                all_data.append(sample)
            
            logger.info(f"已从 {tsv_file.name} 转换 {len(df)} 个样本")
            
        except Exception as e:
            logger.error(f"处理文件 {tsv_file.name} 时出错: {str(e)}")
            # 继续处理其他文件
    
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
    output_dir = Path(output_path).parent
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in all_data:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    logger.info(f"成功将 {len(all_data)} 个样本保存到 {output_path}")
    return True

def convert_mmbench_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将MMBench数据集转换为XpertFormat格式
    
    Args:
        source_path: 源文件或目录路径
        output_path: 输出文件路径
        **kwargs: 额外参数
            - validate: 是否验证数据格式，默认为True
        
    Returns:
        布尔值，表示转换是否成功
    """
    validate = kwargs.get('validate', True)
    source_path = Path(source_path)
    
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return False
    
    if source_path.is_file() and source_path.suffix.lower() == '.tsv':
        return convert_mmbench_tsv_to_xpert(str(source_path), output_path, validate)
    elif source_path.is_dir():
        return convert_mmbench_dir_to_xpert(str(source_path), output_path, validate)
    else:
        logger.error(f"不支持的源路径类型: {source_path}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换MMBench数据集
    
    用法：
        python -m xperteval.datasets.converters.mmbench_converter --source <source_path> --output <output_path> [--no-validate]
    """
    parser = argparse.ArgumentParser(description='将MMBench数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源TSV文件或目录路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    args = parser.parse_args()
    
    success = convert_mmbench_to_xpert(args.source, args.output, validate=not args.no_validate)
    
    if success:
        logger.info(f"转换完成，结果保存到: {args.output}")
        return 0
    else:
        logger.error("转换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 