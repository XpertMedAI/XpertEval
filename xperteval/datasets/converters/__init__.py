# coding: utf-8
"""
数据集转换器

提供将各种格式的数据集转换为XpertFormat格式的功能。
"""

# 导入转换工具
from .converter_utils import convert_to_xpert_format, batch_convert

# 导入mmlu转换器（已实现）
from .mmlu_converter import convert_mmlu_to_xpert

# 导入cmmlu转换器（已实现）
from .cmmlu_converter import convert_cmmlu_to_xpert

# 导入gsm8k转换器（已实现）
from .gsm8k_converter import convert_gsm8k_to_xpert

# 定义占位函数，用于尚未实现的转换器
def _not_implemented(*args, **kwargs):
    raise NotImplementedError("此转换器尚未实现")

# 为尚未实现的转换器提供占位函数
convert_math_to_xpert = _not_implemented
convert_humaneval_to_xpert = _not_implemented
convert_ceval_to_xpert = _not_implemented
convert_mmbench_to_xpert = _not_implemented
convert_llava_bench_to_xpert = _not_implemented
convert_seed_bench_to_xpert = _not_implemented
convert_mm_vet_to_xpert = _not_implemented

# 导入格式验证器
from .format_validator import (
    validate_xpert_format
)

__all__ = [
    'convert_mmlu_to_xpert',
    'convert_cmmlu_to_xpert',
    'convert_gsm8k_to_xpert',
    'convert_math_to_xpert',
    'convert_humaneval_to_xpert',
    'convert_ceval_to_xpert',
    'convert_mmbench_to_xpert',
    'convert_llava_bench_to_xpert',
    'convert_seed_bench_to_xpert',
    'convert_mm_vet_to_xpert',
    'convert_to_xpert_format',
    'batch_convert',
    'validate_xpert_format'
] 