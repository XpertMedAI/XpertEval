#!/usr/bin/env python
# coding: utf-8
"""
数据集预览工具

这个脚本用于预览和检查数据集内容，支持显示样本、统计信息和可视化。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import random
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xperteval.datasets.registered_datasets import (
    scan_integrated_datasets,
    get_dataset,
    list_available_datasets
)
from xperteval.datasets.dataset_manager import DatasetManager
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def preview_samples(dataset, num_samples=5, random_samples=False):
    """
    预览数据集样本
    
    Args:
        dataset: 数据集实例
        num_samples: 显示的样本数量
        random_samples: 是否随机选择样本
    """
    if len(dataset) == 0:
        logger.warning("数据集为空!")
        return
    
    if random_samples:
        indices = random.sample(range(len(dataset)), min(num_samples, len(dataset)))
    else:
        indices = range(min(num_samples, len(dataset)))
    
    for i, idx in enumerate(indices):
        sample = dataset[idx]
        print(f"\n=== 样本 {i+1}/{len(indices)} (索引: {idx}) ===")
        
        # 显示基本信息
        print(f"ID: {sample.get('id', 'N/A')}")
        print(f"问题: {sample.get('query', 'N/A')}")
        
        # 显示选项（如果有）
        if 'choices' in sample:
            print("\n选项:")
            for choice in sample['choices']:
                print(f"  {choice.get('id', 'N/A')}: {choice.get('content', 'N/A')}")
        
        # 显示答案
        print(f"\n参考答案: {sample.get('response', 'N/A')}")
        
        # 显示结构化答案（如果有）
        if 'answer' in sample:
            answer = sample['answer']
            print("\n结构化答案:")
            print(f"  类型: {answer.get('type', 'N/A')}")
            print(f"  值: {answer.get('value', 'N/A')}")
            if 'explanation' in answer:
                print(f"  解释: {answer['explanation'][:100]}..." if len(answer['explanation']) > 100 else f"  解释: {answer['explanation']}")
        
        # 显示元数据
        if 'meta' in sample:
            print("\n元数据:")
            for key, value in sample['meta'].items():
                print(f"  {key}: {value}")
        
        # 显示文件信息
        if 'files' in sample and sample['files']:
            print("\n文件:")
            for file_info in sample['files']:
                print(f"  路径: {file_info.get('path', 'N/A')}")
                print(f"  类型: {file_info.get('type', 'N/A')}")
                if 'description' in file_info:
                    print(f"  描述: {file_info['description']}")
        
        print("-" * 80)

def show_statistics(dataset):
    """
    显示数据集统计信息
    
    Args:
        dataset: 数据集实例
    """
    # 基本统计
    print(f"\n=== 数据集统计信息 ===")
    print(f"样本总数: {len(dataset)}")
    
    # 尝试获取数据集的统计信息方法
    try:
        stats = dataset.get_statistics()
        for key, value in stats.items():
            if key == "total_samples":
                continue  # 已经显示过了
            
            if isinstance(value, dict):
                print(f"\n{key}:")
                for subkey, subvalue in value.items():
                    print(f"  {subkey}: {subvalue}")
            else:
                print(f"{key}: {value}")
    except (AttributeError, NotImplementedError):
        # 如果没有统计方法，手动计算一些统计信息
        task_types = {}
        categories = {}
        has_choices = 0
        has_files = 0
        answer_types = {}
        
        for sample in dataset.data:
            # 统计任务类型
            task_type = sample.get('meta', {}).get('task_type', 'unknown')
            task_types[task_type] = task_types.get(task_type, 0) + 1
            
            # 统计类别
            category = sample.get('meta', {}).get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # 统计选择题数量
            if 'choices' in sample:
                has_choices += 1
            
            # 统计多模态样本数量
            if 'files' in sample and sample['files']:
                has_files += 1
            
            # 统计答案类型
            answer_type = sample.get('answer', {}).get('type', 'unknown')
            answer_types[answer_type] = answer_types.get(answer_type, 0) + 1
        
        print("\n任务类型分布:")
        for task_type, count in task_types.items():
            print(f"  {task_type}: {count} ({count/len(dataset)*100:.1f}%)")
        
        print("\n类别分布:")
        for category, count in categories.items():
            print(f"  {category}: {count} ({count/len(dataset)*100:.1f}%)")
        
        print(f"\n选择题数量: {has_choices} ({has_choices/len(dataset)*100:.1f}%)")
        print(f"多模态样本数量: {has_files} ({has_files/len(dataset)*100:.1f}%)")
        
        print("\n答案类型分布:")
        for answer_type, count in answer_types.items():
            print(f"  {answer_type}: {count} ({count/len(dataset)*100:.1f}%)")

def visualize_dataset(dataset, output_dir=None):
    """
    可视化数据集统计信息
    
    Args:
        dataset: 数据集实例
        output_dir: 输出目录，如果指定则保存图表
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.error("可视化需要安装 matplotlib，请运行 'pip install matplotlib'")
        return
    
    # 确保输出目录存在
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 获取统计数据
    task_types = {}
    categories = {}
    
    for sample in dataset.data:
        # 统计任务类型
        task_type = sample.get('meta', {}).get('task_type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1
        
        # 统计类别
        category = sample.get('meta', {}).get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1
    
    # 绘制任务类型分布饼图
    plt.figure(figsize=(10, 6))
    plt.pie(list(task_types.values()), labels=list(task_types.keys()), autopct='%1.1f%%')
    plt.title('任务类型分布')
    if output_dir:
        plt.savefig(os.path.join(output_dir, 'task_types.png'))
        print(f"已保存任务类型分布图到 {os.path.join(output_dir, 'task_types.png')}")
    else:
        plt.show()
    
    # 如果类别太多，只显示前10个
    if len(categories) > 10:
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        top_categories = dict(sorted_categories[:10])
        other_count = sum(dict(sorted_categories[10:]).values())
        if other_count > 0:
            top_categories['其他'] = other_count
        categories = top_categories
    
    # 绘制类别分布柱状图
    plt.figure(figsize=(12, 6))
    plt.bar(list(categories.keys()), list(categories.values()))
    plt.title('类别分布')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    if output_dir:
        plt.savefig(os.path.join(output_dir, 'categories.png'))
        print(f"已保存类别分布图到 {os.path.join(output_dir, 'categories.png')}")
    else:
        plt.show()

def list_datasets():
    """列出所有可用的数据集"""
    print("\n=== 可用数据集列表 ===")
    
    # 扫描集成数据集
    scan_integrated_datasets()
    datasets = list_available_datasets()
    
    if not datasets:
        print("未找到可用数据集")
        return
    
    # 准备表格数据
    table_data = []
    for dataset in datasets:
        table_data.append([
            dataset['id'],
            dataset['name'],
            dataset['type'],
            dataset['description']
        ])
    
    # 打印表格
    headers = ["ID", "名称", "类型", "描述"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据集预览工具')
    parser.add_argument('--dataset-id', help='数据集ID')
    parser.add_argument('--file', help='数据集文件路径')
    parser.add_argument('--type', default='xpert-format', help='数据集类型，默认为xpert-format')
    parser.add_argument('--samples', type=int, default=5, help='显示的样本数量')
    parser.add_argument('--random', action='store_true', help='随机选择样本')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--visualize', action='store_true', help='可视化数据集')
    parser.add_argument('--output-dir', help='可视化输出目录')
    parser.add_argument('--list', action='store_true', help='列出所有可用的数据集')
    parser.add_argument('--split', help='数据集分割，如train, dev, test')
    
    args = parser.parse_args()
    
    # 列出所有数据集
    if args.list:
        list_datasets()
        return 0
    
    # 加载数据集
    dataset = None
    
    if args.dataset_id:
        try:
            dataset = get_dataset(dataset_id=args.dataset_id, split=args.split)
            print(f"已加载数据集: {args.dataset_id}" + (f" ({args.split}分割)" if args.split else ""))
        except Exception as e:
            logger.error(f"加载数据集 {args.dataset_id} 失败: {e}")
            return 1
    elif args.file:
        try:
            dataset = get_dataset(dataset_path=args.file, dataset_type=args.type)
            print(f"已加载数据集文件: {args.file}")
        except Exception as e:
            logger.error(f"加载数据集文件 {args.file} 失败: {e}")
            return 1
    else:
        logger.error("请指定数据集ID或文件路径")
        parser.print_help()
        return 1
    
    # 显示统计信息
    if args.stats:
        show_statistics(dataset)
    
    # 可视化数据集
    if args.visualize:
        visualize_dataset(dataset, args.output_dir)
    
    # 如果没有指定统计或可视化，则默认显示样本
    if not args.stats and not args.visualize:
        preview_samples(dataset, args.samples, args.random)
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 