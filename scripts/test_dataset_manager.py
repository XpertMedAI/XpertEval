#!/usr/bin/env python
# coding: utf-8
"""
测试数据集管理器

这个脚本用于测试数据集管理器的功能，包括数据集注册、扫描、分割、采样和过滤等。
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xperteval.datasets.registered_datasets import (
    scan_integrated_datasets,
    get_dataset,
    list_available_datasets,
    register_dataset_type,
    DATASET_REGISTRY
)
from xperteval.datasets.dataset_manager import DatasetManager
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def test_dataset_download():
    """测试数据集下载"""
    logger.info("=== 测试数据集下载 ===")
    logger.info(f"已注册的数据集类型: {list(DATASET_REGISTRY.keys())}")
    
    # 创建数据集管理器
    manager = DatasetManager()
    
    # 列出所有可用的数据集
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    logger.info(f"可用的数据集数量: {len(datasets)}")
    
    # 打印所有可用数据集
    logger.info("可用的数据集列表:")
    for i, dataset in enumerate(datasets):
        status = dataset.get('local_status', '未知')
        logger.info(f"  [{i}] {dataset['id']} - {dataset['name']} ({status})")
    
    # 尝试下载一个数据集作为示例
    # 选择一个数据集进行测试 - 优先选择未下载的数据集
    dataset_id = None
    for ds in datasets:
        if ds.get('local_status') == '未下载' and (
            manager.get_dataset_info(ds['id']).get('huggingface_url') or 
            manager.get_dataset_info(ds['id']).get('modelscope_url')
        ):
            dataset_id = ds['id']
            break
    
    # 如果没有未下载的数据集，选择第一个
    if not dataset_id:
        dataset_id = datasets[0]['id'] if datasets else None
    
    # 如果没有数据集，返回失败
    if not dataset_id:
        logger.error("没有可用的数据集进行下载测试")
        return False
    
    logger.info(f"选择数据集 {dataset_id} 进行下载测试")
    
    # 检查当前状态
    info = manager.get_dataset_info(dataset_id)
    if not info:
        logger.error(f"获取数据集 {dataset_id} 信息失败")
        return False
    
    local_status = info.get('local_status')
    logger.info(f"数据集 {dataset_id} 当前状态: {local_status}")
    
    # 定义是否强制重新下载
    force_download = False
    if local_status in ['已下载', '已转换']:
        logger.info(f"数据集 {dataset_id} 已经下载过")
        # 询问是否强制重新下载
        forced_download_options = ["y", "n", "yes", "no"]
        if sys.stderr.isatty():  # 如果是交互式终端
            choice = input(f"是否强制重新下载数据集 {dataset_id}? (y/n): ").lower()
            force_download = choice in ["y", "yes"]
        
        if force_download:
            logger.info(f"将强制重新下载数据集 {dataset_id}")
        else:
            logger.info(f"跳过数据集 {dataset_id} 的下载")
            success = True
    else:
        # 尝试下载数据集
        logger.info(f"开始下载数据集 {dataset_id}...")
        success = manager.download_dataset(dataset_id, force=force_download)
        
        if success:
            logger.info(f"数据集 {dataset_id} 下载成功")
            
            # 尝试下载后的状态
            new_info = manager.get_dataset_info(dataset_id)
            new_status = new_info.get('local_status') if new_info else '未知'
            logger.info(f"下载后数据集 {dataset_id} 状态: {new_status}")
        else:
            logger.error(f"数据集 {dataset_id} 下载失败")
    
    # 列出所有支持的数据集类型
    available_types = list(DATASET_REGISTRY.keys())
    logger.info(f"当前支持的数据集类型: {available_types}")
    
    # 可选：测试转换功能
    if success and local_status == '已下载':
        logger.info(f"尝试将数据集 {dataset_id} 转换为XpertFormat格式...")
        convert_success = manager.convert_dataset(dataset_id)
        if convert_success:
            logger.info(f"数据集 {dataset_id} 转换成功")
        else:
            logger.warning(f"数据集 {dataset_id} 转换失败")
    
    return success

def test_dataset_registry():
    """测试数据集注册表"""
    logger.info("=== 测试数据集注册表 ===")
    logger.info(f"已注册的数据集类型: {list(DATASET_REGISTRY.keys())}")
    
    # 检查是否包含所有期望的数据集类型
    expected_types = [
        "xpert-format", "mmlu", "cmmlu", "gsm8k", "math", 
        "human_eval", "ceval", "mmbench", "llava_bench", 
        "seed_bench", "mm_vet"
    ]
    
    all_found = True
    for expected_type in expected_types:
        if expected_type not in DATASET_REGISTRY:
            logger.error(f"缺少数据集类型: {expected_type}")
            all_found = False
    
    if all_found:
        logger.info("所有期望的数据集类型都已注册")
    
    return all_found

def test_scan_datasets(base_dir=None):
    """测试扫描集成数据集"""
    logger.info("=== 测试扫描集成数据集 ===")
    datasets = scan_integrated_datasets(base_dir)
    logger.info(f"发现 {len(datasets)} 个集成数据集")
    
    for dataset_id, info in datasets.items():
        logger.info(f"数据集: {dataset_id}")
        logger.info(f"  - 名称: {info['name']}")
        logger.info(f"  - 类型: {info['type']}")
        logger.info(f"  - 路径: {info['path']}")
        logger.info(f"  - 描述: {info['description']}")
        
        if info.get('splits'):
            logger.info(f"  - 分割: {', '.join(info['splits'])}")
        
        if info.get('media_dir'):
            logger.info(f"  - 媒体目录: {info['media_dir']}")
    
    return len(datasets) > 0

def test_dataset_manager():
    """测试数据集管理器"""
    logger.info("=== 测试数据集管理器 ===")
    manager = DatasetManager()
    
    # 列出可用数据集
    datasets = manager.list_available_datasets()
    logger.info(f"配置文件中的数据集数量: {len(datasets)}")
    
    if not datasets:
        logger.warning("配置文件中没有数据集")
        return False
    
    # 选择第一个数据集进行测试
    dataset_id = datasets[0]['id']
    logger.info(f"选择数据集 {dataset_id} 进行测试")
    
    # 获取数据集信息
    info = manager.get_dataset_info(dataset_id)
    if not info:
        logger.error(f"获取数据集 {dataset_id} 信息失败")
        return False
    
    logger.info(f"数据集信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
    
    return True

def test_dataset_split(dataset_id, train_ratio=0.8, dev_ratio=0.1, test_ratio=0.1):
    """测试数据集分割"""
    logger.info(f"=== 测试数据集分割: {dataset_id} ===")
    manager = DatasetManager()
    
    # 获取数据集
    dataset = manager.get_dataset(dataset_id, auto_download=False, auto_convert=False)
    if not dataset:
        logger.error(f"获取数据集 {dataset_id} 失败")
        return False
    
    logger.info(f"原始数据集大小: {len(dataset)}")
    
    # 创建分割
    success = manager.create_dataset_split(
        dataset_id, 
        train_ratio=train_ratio, 
        dev_ratio=dev_ratio, 
        test_ratio=test_ratio
    )
    
    if not success:
        logger.error(f"创建数据集分割失败")
        return False
    
    # 加载各个分割
    splits = ["train", "dev", "test"]
    for split in splits:
        split_dataset = manager.get_dataset(dataset_id, split=split)
        if split_dataset:
            logger.info(f"{split} 分割大小: {len(split_dataset)}")
        else:
            logger.warning(f"加载 {split} 分割失败")
    
    return True

def test_dataset_sample_filter(dataset_id, sample_size=10):
    """测试数据集采样和过滤"""
    logger.info(f"=== 测试数据集采样和过滤: {dataset_id} ===")
    manager = DatasetManager()
    
    # 获取原始数据集
    dataset = manager.get_dataset(dataset_id)
    if not dataset:
        logger.error(f"获取数据集 {dataset_id} 失败")
        return False
    
    logger.info(f"原始数据集大小: {len(dataset)}")
    
    # 测试采样
    sampled_dataset = manager.get_dataset(dataset_id, sample_size=sample_size)
    if not sampled_dataset:
        logger.error(f"采样数据集失败")
        return False
    
    logger.info(f"采样后数据集大小: {len(sampled_dataset)}")
    
    # 测试过滤（示例：只保留包含特定关键词的样本）
    def filter_func(sample):
        query = sample.get('query', '')
        return '?' in query  # 只保留问句
    
    filtered_dataset = manager.get_dataset(dataset_id, filter_func=filter_func)
    if not filtered_dataset:
        logger.warning(f"过滤后没有剩余样本")
    else:
        logger.info(f"过滤后数据集大小: {len(filtered_dataset)}")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试数据集管理器')
    parser.add_argument('--test-all', action='store_true', help='运行所有测试')
    parser.add_argument('--test-download', action='store_true', help='测试数据集下载')
    parser.add_argument('--test-registry', action='store_true', help='测试数据集注册表')
    parser.add_argument('--test-scan', action='store_true', help='测试扫描集成数据集')
    parser.add_argument('--test-manager', action='store_true', help='测试数据集管理器')
    parser.add_argument('--test-split', action='store_true', help='测试数据集分割')
    parser.add_argument('--test-sample-filter', action='store_true', help='测试数据集采样和过滤')
    parser.add_argument('--dataset-id', help='用于测试的数据集ID')
    parser.add_argument('--sample-size', type=int, default=10, help='采样大小')
    
    args = parser.parse_args()
    
    # 如果没有指定任何测试，则运行所有测试
    if not (args.test_download or args.test_registry or args.test_scan or args.test_manager or 
            args.test_split or args.test_sample_filter):
        args.test_all = True
    
    # 运行测试
    results = {}

    if args.test_all or args.test_download:
        results['download'] = test_dataset_download()
    
    if args.test_all or args.test_registry:
        results['registry'] = test_dataset_registry()
    
    if args.test_all or args.test_scan:
        results['scan'] = test_scan_datasets()
    
    if args.test_all or args.test_manager:
        results['manager'] = test_dataset_manager()
    
    if args.test_all or args.test_split:
        if args.dataset_id:
            results['split'] = test_dataset_split(args.dataset_id)
        else:
            logger.warning("未指定数据集ID，跳过分割测试")
    
    if args.test_all or args.test_sample_filter:
        if args.dataset_id:
            results['sample_filter'] = test_dataset_sample_filter(args.dataset_id, args.sample_size)
        else:
            logger.warning("未指定数据集ID，跳过采样和过滤测试")
    
    # 输出结果
    logger.info("=== 测试结果 ===")
    all_success = True
    for test_name, success in results.items():
        logger.info(f"{test_name}: {'成功' if success else '失败'}")
        if not success:
            all_success = False
    
    return 0 if all_success else 1

if __name__ == '__main__':
    sys.exit(main()) 