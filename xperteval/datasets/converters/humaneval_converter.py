# coding: utf-8
"""
HumanEval (Human Evaluation) 数据集转换器

将HumanEval代码生成数据集转换为XpertFormat格式。
支持从Hugging Face下载的parquet文件转换。

用法:
    # 导入转换器
    from xperteval.datasets.converters import convert_humaneval_to_xpert
    
    # 转换HumanEval数据集
    convert_humaneval_to_xpert("data/downloads/humaneval/openai_humaneval/test-00000-of-00001.parquet", 
                              "data/integrated/humaneval/humaneval.jsonl")

命令行使用:
    # 转换HumanEval数据集
    python -m xperteval.datasets.converters.humaneval_converter --source data/downloads/humaneval/openai_humaneval/test-00000-of-00001.parquet --output data/integrated/humaneval/humaneval.jsonl
    
    # 或者使用直接运行模式
    python xperteval/datasets/converters/humaneval_converter.py --source data/downloads/humaneval/openai_humaneval/test-00000-of-00001.parquet --output data/integrated/humaneval/humaneval.jsonl
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

def process_humaneval_file(parquet_file: Path) -> List[Dict[str, Any]]:
    """
    处理HumanEval parquet文件，将其转换为XpertFormat样本列表
    
    Args:
        parquet_file: parquet文件路径
        
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
            task_id = row['task_id']
            prompt = row['prompt']
            canonical_solution = row['canonical_solution']
            test = row['test']
            entry_point = row['entry_point']
            
            # 从prompt中提取问题描述（通常是函数签名和文档字符串）
            # 处理缩进，确保代码可以直接执行
            solution = adjust_indentation(prompt, canonical_solution)
            
            # 创建符合XpertFormat规范的样本
            sample = {
                "id": f"humaneval_{task_id.replace('/', '_')}",  # 创建唯一ID
                "query": prompt,                                # 问题文本（代码提示）
                "answer": {                                     # 答案信息
                    "type": "code",
                    "value": solution,                          # 完整代码
                    "explanation": f"Entry point: {entry_point}\nTest: {test}"  # 将entry_point放在explanation中
                },
                "meta": {                                       # 元数据
                    "task_type": "code",
                    "language": "python",                       # 代码语言
                    "source": "HumanEval"                       # 不再包含entry_point字段
                }
            }
            
            data.append(sample)
        
        logger.info(f"从 {parquet_file} 成功转换了 {len(df)} 个样本")
        return data
            
    except Exception as e:
        logger.error(f"处理文件 {parquet_file} 时出错: {e}")
        return []

def adjust_indentation(prompt: str, solution: str) -> str:
    """
    调整代码缩进，确保解决方案与提示正确对齐
    
    Args:
        prompt: 代码提示（函数签名和文档字符串）
        solution: 代码解决方案
        
    Returns:
        正确缩进的完整代码
    """
    # 检查prompt是否以换行符结束
    if not prompt.endswith('\n'):
        prompt = prompt + '\n'
    
    # 确保solution的缩进与prompt中的最后一行对齐
    return prompt + solution

def convert_humaneval_to_xpert(source_path: str, output_path: str, **kwargs) -> bool:
    """
    将HumanEval数据集转换为XpertFormat格式
    
    Args:
        source_path: 数据集文件路径
        output_path: 输出文件路径
        **kwargs: 额外参数
            - validate: 是否验证数据格式，默认为True
        
    Returns:
        布尔值，表示转换是否成功
    """
    logger.info(f"开始将HumanEval数据集转换为XpertFormat格式...")
    
    source_path = Path(source_path)
    validate = kwargs.get('validate', True)
    
    if not source_path.exists():
        logger.error(f"源文件不存在: {source_path}")
        return False
    
    # 处理parquet文件
    data = process_humaneval_file(source_path)
    
    if not data:
        logger.error(f"未能成功转换任何数据")
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
    try:
        # 确保输出目录存在
        output_dir = Path(output_path).parent
        os.makedirs(output_dir, exist_ok=True)
        
        # 以JSONL格式写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"成功将 {len(data)} 个样本保存到 {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"保存转换后的数据失败: {e}")
        return False

def main():
    """
    命令行入口函数
    
    支持通过命令行参数转换HumanEval数据集
    
    用法：
        python -m xperteval.datasets.converters.humaneval_converter --source <source_path> --output <output_path> [--no-validate]
    """
    parser = argparse.ArgumentParser(description='将HumanEval数据集转换为XpertFormat格式')
    parser.add_argument('--source', required=True, help='源数据文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--no-validate', action='store_true', help='跳过数据格式验证')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    
    if not source_path.exists():
        logger.error(f"源路径不存在: {source_path}")
        return 1
    
    # 执行转换
    success = convert_humaneval_to_xpert(str(source_path), args.output, validate=not args.no_validate)
    
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