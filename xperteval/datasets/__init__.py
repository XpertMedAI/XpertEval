# coding: utf-8
"""
数据集处理与加载模块

提供统一的数据集接口、解析器和注册管理功能。
"""

from .base_dataset import BaseDataset
from .xpert_format import XpertFormatDataset
from .registered_datasets import (
    get_dataset,
    list_available_datasets,
    register_dataset_type,
    scan_integrated_datasets
)
from .dataset_manager import DatasetManager
from .common_benchmarks import (
    MMLUDataset,
    CMMLUDataset,
    GSM8KDataset,
    MATHDataset,
    HumanEvalDataset,
    CEvalDataset
)
from .multimodal_benchmarks import (
    MMBenchDataset,
    LLaVABenchDataset,
    SEEDBenchDataset,
    MMVetDataset
)

__all__ = [
    'BaseDataset',
    'XpertFormatDataset',
    'DatasetManager',
    'get_dataset',
    'list_available_datasets',
    'register_dataset_type',
    'scan_integrated_datasets',

    # Common benchmarks
    'MMLUDataset',
    'CMMLUDataset',
    'GSM8KDataset',
    'MATHDataset',
    'HumanEvalDataset',
    'CEvalDataset',
    
    # Multimodal benchmarks
    'MMBenchDataset',
    'LLaVABenchDataset',
    'SEEDBenchDataset',
    'MMVetDataset'
] 