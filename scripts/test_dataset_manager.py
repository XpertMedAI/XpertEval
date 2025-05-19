#!/usr/bin/env python
# coding: utf-8
"""
数据集管理器测试脚本
"""

import os
import sys
import json
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from xperteval.datasets import DatasetManager
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def test_list_datasets():
    """测试列出所有可用的数据集"""
    manager = DatasetManager()
    datasets = manager.list_available_datasets()
    
    logger.info(f"可用数据集数量: {len(datasets)}")
    for ds in datasets:
        logger.info(f"数据集: {ds['id']} - {ds['name']} ({ds['task_type']}, {ds['language']})")
    
    return len(datasets) > 0

def test_dataset_info():
    """测试获取数据集详细信息"""
    manager = DatasetManager()
    
    # 获取第一个数据集的ID
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    
    dataset_id = datasets[0]['id']
    info = manager.get_dataset_info(dataset_id)
    
    if not info:
        logger.error(f"获取数据集 {dataset_id} 信息失败")
        return False
    
    logger.info(f"数据集 {dataset_id} 信息:")
    logger.info(f"  名称: {info.get('name')}")
    logger.info(f"  描述: {info.get('description')}")
    logger.info(f"  任务类型: {info.get('task_type')}")
    logger.info(f"  语言: {info.get('language')}")
    logger.info(f"  大小: {info.get('size')}")
    logger.info(f"  本地状态: {info.get('local_status')}")
    
    return True

def test_download_dataset():
    """测试下载数据集"""
    manager = DatasetManager()
    
    # 获取第一个数据集的ID
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    
    dataset_id = datasets[0]['id']
    
    # 下载数据集
    logger.info(f"开始下载数据集 {dataset_id}...")
    success = manager.download_dataset(dataset_id)
    
    if success:
        logger.info(f"数据集 {dataset_id} 下载成功")
    else:
        logger.error(f"数据集 {dataset_id} 下载失败")
    
    return success

def test_convert_dataset():
    """测试转换数据集"""
    manager = DatasetManager()
    
    # 获取第一个数据集的ID
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    
    dataset_id = datasets[0]['id']
    
    # 确保数据集已下载
    if manager._check_local_status(dataset_id) == "未下载":
        logger.info(f"数据集 {dataset_id} 尚未下载，先进行下载...")
        if not manager.download_dataset(dataset_id):
            logger.error(f"数据集 {dataset_id} 下载失败，无法进行转换测试")
            return False
    
    # 转换数据集
    logger.info(f"开始转换数据集 {dataset_id}...")
    success = manager.convert_dataset(dataset_id)
    
    if success:
        logger.info(f"数据集 {dataset_id} 转换成功")
    else:
        logger.error(f"数据集 {dataset_id} 转换失败")
    
    return success

def test_get_dataset():
    """测试获取数据集实例"""
    manager = DatasetManager()
    
    # 获取第一个数据集的ID
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    
    dataset_id = datasets[0]['id']
    
    # 确保数据集已下载并转换
    local_status = manager._check_local_status(dataset_id)
    if local_status == "未下载":
        logger.info(f"数据集 {dataset_id} 尚未下载，先进行下载和转换...")
        if not manager.download_dataset(dataset_id) or not manager.convert_dataset(dataset_id):
            logger.error(f"数据集 {dataset_id} 准备失败，无法获取数据集实例")
            return False
    elif local_status == "已下载":
        logger.info(f"数据集 {dataset_id} 已下载但未转换，先进行转换...")
        if not manager.convert_dataset(dataset_id):
            logger.error(f"数据集 {dataset_id} 转换失败，无法获取数据集实例")
            return False
    
    # 获取数据集实例
    logger.info(f"获取数据集 {dataset_id} 实例...")
    dataset = manager.get_dataset(dataset_id)
    
    if dataset is None:
        logger.error(f"获取数据集 {dataset_id} 实例失败")
        return False
    
    logger.info(f"成功获取数据集 {dataset_id} 实例")
    logger.info(f"  样本数量: {len(dataset)}")
    
    # 获取第一个样本
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"  第一个样本ID: {sample.get('id')}")
        logger.info(f"  第一个样本问题: {sample.get('query')}")
    
    return dataset is not None

def test_auto_download_convert():
    """测试自动下载和转换数据集"""
    manager = DatasetManager()
    
    # 获取第一个数据集的ID
    datasets = manager.list_available_datasets()
    if not datasets:
        logger.warning("没有可用的数据集")
        return False
    
    dataset_id = datasets[0]['id']
    
    # 确保数据集未下载
    if manager._check_local_status(dataset_id) != "未下载":
        logger.info(f"删除数据集 {dataset_id} 的本地文件以测试自动下载功能")
        manager.delete_dataset(dataset_id)
    
    # 测试自动下载和转换
    logger.info(f"测试自动下载和转换数据集 {dataset_id}...")
    dataset = manager.get_dataset(dataset_id, auto_download=True, auto_convert=True)
    
    if dataset is None:
        logger.error(f"自动下载和转换数据集 {dataset_id} 失败")
        return False
    
    logger.info(f"自动下载和转换数据集 {dataset_id} 成功")
    return True

def main():
    """主函数"""
    logger.info("开始测试数据集管理器")
    
    tests = [
        ("列出数据集", test_list_datasets),
        ("获取数据集信息", test_dataset_info),
        ("下载数据集", test_download_dataset),
        ("转换数据集", test_convert_dataset),
        ("获取数据集实例", test_get_dataset),
        ("自动下载和转换", test_auto_download_convert)
    ]
    
    success_count = 0
    for name, test_func in tests:
        logger.info(f"测试 {name}")
        try:
            if test_func():
                logger.info(f"{name} 测试通过")
                success_count += 1
            else:
                logger.error(f"{name} 测试失败")
        except Exception as e:
            logger.error(f"{name} 测试失败：{e}")
    
    logger.info(f"测试完成，共 {len(tests)} 项测试，通过 {success_count} 项")
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 