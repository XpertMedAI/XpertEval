# coding: utf-8
"""
数据集处理与加载模块

提供统一的数据集接口、解析器和注册管理功能。
"""

from .base_dataset import BaseDataset
from .ms_swift_parser import MsSwiftDataset
from .registered_datasets import (
    get_dataset,
    list_available_datasets,
    register_dataset_type,
    scan_integrated_datasets
)

__all__ = [
    'BaseDataset',
    'MsSwiftDataset',
    'get_dataset',
    'list_available_datasets',
    'register_dataset_type',
    'scan_integrated_datasets'
] 