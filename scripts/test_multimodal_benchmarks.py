#!/usr/bin/env python
# coding: utf-8
"""
测试多模态评测数据集解析器

这个脚本用于测试多模态评测数据集解析器的功能，包括MMBench、LLaVA-Bench、SEED-Bench和MM-Vet。
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xperteval.datasets.multimodal_benchmarks import (
    MMBenchDataset,
    LLaVABenchDataset,
    SEEDBenchDataset,
    MMVetDataset
)
from xperteval.utils import get_logger

# 配置日志
logger = get_logger(__name__)

def create_test_data():
    """
    创建测试数据
    
    Returns:
        测试数据目录路径
    """
    # 创建测试数据目录
    test_dir = Path("data/test_multimodal")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建图像目录
    image_dir = test_dir / "images"
    image_dir.mkdir(exist_ok=True)
    
    # 创建视频目录
    video_dir = test_dir / "videos"
    video_dir.mkdir(exist_ok=True)
    
    # 创建测试图像文件（空文件，仅用于测试路径解析）
    (image_dir / "test_image1.jpg").touch()
    (image_dir / "test_image2.jpg").touch()
    (video_dir / "test_video.mp4").touch()
    
    # 创建MMBench测试数据
    mmbench_data = [
        {
            "question_id": "test_001",
            "image": "test_image1.jpg",
            "question": "这张图片中有什么？",
            "choices": ["猫", "狗", "鸟", "鱼"],
            "answer": "A",
            "category": "图像识别",
            "difficulty": "简单"
        },
        {
            "question_id": "test_002",
            "image": "test_image2.jpg",
            "question": "图中的动物是什么颜色？",
            "choices": ["红色", "蓝色", "绿色", "黄色"],
            "answer": "D",
            "category": "属性识别",
            "difficulty": "中等"
        }
    ]
    
    with open(test_dir / "mmbench_test.json", "w", encoding="utf-8") as f:
        json.dump(mmbench_data, f, ensure_ascii=False, indent=2)
    
    # 创建LLaVA-Bench测试数据
    llava_bench_data = [
        {
            "id": "test_001",
            "image": "test_image1.jpg",
            "conversations": [
                {"role": "human", "content": "这张图片中有什么？"},
                {"role": "assistant", "content": "图片中有一只猫。"},
                {"role": "human", "content": "它是什么颜色的？"},
                {"role": "assistant", "content": "这只猫是橘色的。"}
            ],
            "category": "图像描述"
        }
    ]
    
    with open(test_dir / "llava_bench_test.json", "w", encoding="utf-8") as f:
        json.dump(llava_bench_data, f, ensure_ascii=False, indent=2)
    
    # 创建SEED-Bench测试数据
    seed_bench_data = [
        {
            "sample_id": "test_001",
            "image_paths": ["test_image1.jpg", "test_image2.jpg"],
            "question": "这两张图片有什么区别？",
            "choices": ["颜色不同", "大小不同", "形状不同", "没有区别"],
            "answer": 0,
            "task_type": "图像比较"
        },
        {
            "sample_id": "test_002",
            "image_paths": ["test_image1.jpg"],
            "video_path": "test_video.mp4",
            "question": "视频中的动物与图片中的是同一种吗？",
            "choices": ["是", "否"],
            "answer": 1,
            "task_type": "视频理解"
        }
    ]
    
    with open(test_dir / "seed_bench_test.json", "w", encoding="utf-8") as f:
        json.dump(seed_bench_data, f, ensure_ascii=False, indent=2)
    
    # 创建MM-Vet测试数据
    mm_vet_data = [
        {
            "id": "test_001",
            "image": "test_image1.jpg",
            "question": "详细描述这张图片中的场景。",
            "answer": "图片中是一只橘色的猫，它正坐在窗台上。",
            "category": "场景描述",
            "difficulty": "简单"
        },
        {
            "id": "test_002",
            "image": "test_image2.jpg",
            "question": "图中的动物可能在做什么？",
            "choices": ["吃东西", "睡觉", "玩耍", "奔跑"],
            "answer": "B",
            "category": "行为推理",
            "difficulty": "中等"
        }
    ]
    
    with open(test_dir / "mm_vet_test.json", "w", encoding="utf-8") as f:
        json.dump(mm_vet_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"创建测试数据完成，路径: {test_dir}")
    return test_dir

def test_mmbench_dataset(test_dir: Path):
    """
    测试MMBench数据集解析器
    
    Args:
        test_dir: 测试数据目录
    """
    logger.info("测试 MMBench 数据集解析器...")
    
    # 初始化数据集
    dataset = MMBenchDataset(
        dataset_path=str(test_dir / "mmbench_test.json"),
        image_dir=str(test_dir / "images")
    )
    
    # 测试数据加载
    logger.info(f"加载了 {len(dataset)} 个样本")
    
    # 测试样本访问
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"样本ID: {sample['id']}")
        logger.info(f"问题: {sample['query']}")
        logger.info(f"选项数量: {len(sample.get('choices', []))}")
        logger.info(f"答案: {sample['answer']['value']}")
    
    # 测试统计信息
    stats = dataset.get_statistics()
    logger.info(f"统计信息: {stats}")
    
    # 测试验证图像
    valid, total = dataset.verify_images()
    logger.info(f"图像验证: {valid}/{total} 有效")
    
    logger.info("MMBench 测试完成")

def test_llava_bench_dataset(test_dir: Path):
    """
    测试LLaVA-Bench数据集解析器
    
    Args:
        test_dir: 测试数据目录
    """
    logger.info("测试 LLaVA-Bench 数据集解析器...")
    
    # 初始化数据集
    dataset = LLaVABenchDataset(
        dataset_path=str(test_dir / "llava_bench_test.json"),
        image_dir=str(test_dir / "images")
    )
    
    # 测试数据加载
    logger.info(f"加载了 {len(dataset)} 个样本")
    
    # 测试样本访问
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"样本ID: {sample['id']}")
        logger.info(f"问题: {sample['query']}")
        logger.info(f"回答: {sample['response']}")
        if 'history' in sample:
            logger.info(f"历史对话轮次: {len(sample['history']) // 2}")
    
    # 测试统计信息
    stats = dataset.get_statistics()
    logger.info(f"统计信息: {stats}")
    
    # 测试验证图像
    valid, total = dataset.verify_images()
    logger.info(f"图像验证: {valid}/{total} 有效")
    
    logger.info("LLaVA-Bench 测试完成")

def test_seed_bench_dataset(test_dir: Path):
    """
    测试SEED-Bench数据集解析器
    
    Args:
        test_dir: 测试数据目录
    """
    logger.info("测试 SEED-Bench 数据集解析器...")
    
    # 初始化数据集
    dataset = SEEDBenchDataset(
        dataset_path=str(test_dir / "seed_bench_test.json"),
        media_dir=str(test_dir)  # 使用测试目录作为媒体目录的父目录
    )
    
    # 测试数据加载
    logger.info(f"加载了 {len(dataset)} 个样本")
    
    # 测试样本访问
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"样本ID: {sample['id']}")
        logger.info(f"问题: {sample['query']}")
        logger.info(f"文件数量: {len(sample.get('files', []))}")
        logger.info(f"选项数量: {len(sample.get('choices', []))}")
        logger.info(f"答案: {sample['answer']['value']}")
    
    # 测试统计信息
    stats = dataset.get_statistics()
    logger.info(f"统计信息: {stats}")
    
    # 测试验证媒体文件
    media_stats = dataset.verify_media_files()
    logger.info(f"媒体文件验证: {media_stats}")
    
    logger.info("SEED-Bench 测试完成")

def test_mm_vet_dataset(test_dir: Path):
    """
    测试MM-Vet数据集解析器
    
    Args:
        test_dir: 测试数据目录
    """
    logger.info("测试 MM-Vet 数据集解析器...")
    
    # 初始化数据集
    dataset = MMVetDataset(
        dataset_path=str(test_dir / "mm_vet_test.json"),
        image_dir=str(test_dir / "images")
    )
    
    # 测试数据加载
    logger.info(f"加载了 {len(dataset)} 个样本")
    
    # 测试样本访问
    if len(dataset) > 0:
        sample = dataset[0]
        logger.info(f"样本ID: {sample['id']}")
        logger.info(f"问题: {sample['query']}")
        logger.info(f"回答: {sample['response']}")
        logger.info(f"答案类型: {sample['answer']['type']}")
    
    # 测试统计信息
    stats = dataset.get_statistics()
    logger.info(f"统计信息: {stats}")
    
    # 测试验证图像
    valid, total = dataset.verify_images()
    logger.info(f"图像验证: {valid}/{total} 有效")
    
    logger.info("MM-Vet 测试完成")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="测试多模态评测数据集解析器")
    parser.add_argument("--test-dir", type=str, help="测试数据目录，如果不指定则创建临时测试数据")
    parser.add_argument("--dataset", type=str, choices=["mmbench", "llava", "seed", "mmvet", "all"],
                        default="all", help="要测试的数据集，默认为全部")
    
    args = parser.parse_args()
    
    # 获取测试数据目录
    test_dir = Path(args.test_dir) if args.test_dir else create_test_data()
    
    # 根据参数选择要测试的数据集
    if args.dataset == "all" or args.dataset == "mmbench":
        test_mmbench_dataset(test_dir)
    
    if args.dataset == "all" or args.dataset == "llava":
        test_llava_bench_dataset(test_dir)
    
    if args.dataset == "all" or args.dataset == "seed":
        test_seed_bench_dataset(test_dir)
    
    if args.dataset == "all" or args.dataset == "mmvet":
        test_mm_vet_dataset(test_dir)
    
    logger.info("所有测试完成")

if __name__ == "__main__":
    main() 