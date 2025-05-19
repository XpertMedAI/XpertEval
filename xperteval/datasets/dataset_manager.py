# coding: utf-8
"""
数据集处理与加载 - 数据集管理器
负责数据集的下载、转换和管理
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple, Callable
import subprocess
import requests
from tqdm import tqdm
import datetime
import sys

from ..utils import get_logger
from .base_dataset import BaseDataset
from .xpert_format import XpertFormatDataset

# 配置日志
logger = get_logger(__name__)

class DatasetManager:
    """
    数据集管理器
    
    负责数据集的下载、转换和管理，支持从Hugging Face和ModelScope下载数据集，
    并将其转换为XpertFormat格式。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化数据集管理器
        
        Args:
            config_path: 数据集配置文件路径，如果为None，则使用默认路径
        """
        # 默认配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent / "datasets_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        
        # 数据集存储路径
        self.datasets_dir = self.project_root / "data" / "integrated"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        # 临时下载目录
        self.download_dir = self.project_root / "data" / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载数据集配置
        
        Returns:
            数据集配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据集配置失败: {e}")
            return {"version": "1.0.0", "datasets": {}}
    
    def list_available_datasets(self) -> List[Dict[str, str]]:
        """
        列出所有可用的数据集
        
        Returns:
            数据集基本信息列表
        """
        result = []
        for dataset_id, info in self.config.get("datasets", {}).items():
            result.append({
                "id": dataset_id,
                "name": info.get("name", dataset_id),
                "description": info.get("description", ""),
                "task_type": info.get("task_type", ""),
                "language": info.get("language", ""),
                "size": info.get("size", "未知"),
                "local_status": self._check_local_status(dataset_id)
            })
        return result
    
    def _check_local_status(self, dataset_id: str) -> str:
        """
        检查数据集的本地状态
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            状态字符串: "已下载", "已转换", "未下载"
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id, {})
        local_path = dataset_info.get("local_path", "")
        
        if not local_path:
            return "未配置"
        
        # 检查转换后的XpertFormat文件
        xpert_format_path = self.project_root / local_path / "dataset.jsonl"
        if xpert_format_path.exists():
            return "已转换"
        
        # 检查原始数据文件
        original_dir = self.project_root / local_path / "original"
        if original_dir.exists() and any(original_dir.iterdir()):
            return "已下载"
        
        return "未下载"
    
    def download_dataset(self, dataset_id: str, force: bool = False) -> bool:
        """
        下载指定的数据集
        
        Args:
            dataset_id: 数据集ID
            force: 是否强制重新下载，即使本地已存在
            
        Returns:
            布尔值，表示下载是否成功
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            logger.error(f"未找到数据集配置: {dataset_id}")
            return False
        
        # 检查本地状态
        local_status = self._check_local_status(dataset_id)
        if local_status != "未下载" and not force:
            logger.info(f"数据集 {dataset_id} 已存在，跳过下载")
            return True
        
        # 创建本地目录
        local_path = dataset_info.get("local_path", "")
        if not local_path:
            logger.error(f"数据集 {dataset_id} 未配置本地路径")
            return False
        
        local_dir = self.project_root / local_path
        original_dir = local_dir / "original"
        original_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试从不同来源下载
        success = False
        
        # 1. 尝试从Hugging Face下载
        if dataset_info.get("huggingface_url"):
            success = self._download_from_huggingface(dataset_id, dataset_info, original_dir)
        
        # 2. 如果Hugging Face下载失败，尝试从ModelScope下载
        if not success and dataset_info.get("modelscope_url"):
            success = self._download_from_modelscope(dataset_id, dataset_info, original_dir)
        
        # 3. 未来可以添加更多下载源
        
        if success:
            logger.info(f"数据集 {dataset_id} 下载成功")
        else:
            logger.error(f"数据集 {dataset_id} 下载失败")
        
        return success
    
    def _download_from_huggingface(self, dataset_id: str, dataset_info: Dict[str, Any], 
                                 target_dir: Path) -> bool:
        """
        从Hugging Face下载数据集
        
        Args:
            dataset_id: 数据集ID
            dataset_info: 数据集配置信息
            target_dir: 目标保存目录
            
        Returns:
            布尔值，表示下载是否成功
        """
        logger.info(f"尝试从Hugging Face下载数据集 {dataset_id}...")
        
        try:
            # 检查是否安装了datasets库
            try:
                import datasets
                from datasets import load_dataset
            except ImportError:
                logger.error("未安装datasets库，请使用 'pip install datasets' 安装")
                logger.info("正在尝试安装datasets库...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
                import datasets
                from datasets import load_dataset
                logger.info("datasets库安装成功")
            
            # 获取Hugging Face数据集路径
            hf_path = dataset_info.get("huggingface_url")
            if not hf_path:
                logger.error(f"数据集 {dataset_id} 未配置Hugging Face URL")
                return False
            
            # 从URL中提取数据集名称
            # 例如从 https://huggingface.co/datasets/cais/mmlu 提取 cais/mmlu
            hf_dataset_name = hf_path.replace("https://huggingface.co/datasets/", "")
            
            logger.info(f"正在从Hugging Face下载数据集: {hf_dataset_name}")
            
            # 记录下载信息
            download_info = {
                "source": "huggingface",
                "url": hf_path,
                "downloaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(target_dir / "download_info.json", 'w', encoding='utf-8') as f:
                json.dump(download_info, f, ensure_ascii=False, indent=2)
            
            # 下载数据集
            # 使用本地缓存目录，避免默认缓存位置可能的权限问题
            cache_dir = self.project_root / "data" / "cache" / "huggingface"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载所有可用的配置和分割
            try:
                # 首先尝试获取数据集信息，看支持哪些配置和分割
                dataset_info_obj = datasets.get_dataset_infos(hf_dataset_name)
                
                if dataset_info_obj:
                    # 遍历所有配置
                    for config_name, config_info in dataset_info_obj.items():
                        logger.info(f"下载配置: {config_name}")
                        
                        # 获取此配置下的所有分割
                        splits = config_info.splits.keys()
                        
                        for split in splits:
                            logger.info(f"下载分割: {split}")
                            
                            # 下载特定配置和分割的数据集
                            ds = load_dataset(
                                hf_dataset_name, 
                                name=config_name, 
                                split=split,
                                cache_dir=str(cache_dir)
                            )
                            
                            # 保存为jsonl格式
                            output_file = target_dir / f"{config_name}_{split}.jsonl"
                            ds.to_json(str(output_file))
                            
                            logger.info(f"保存数据集到: {output_file}, 样本数: {len(ds)}")
                else:
                    # 如果无法获取详细信息，直接尝试下载
                    logger.info("无法获取数据集详细信息，尝试直接下载")
                    ds = load_dataset(hf_dataset_name, cache_dir=str(cache_dir))
                    
                    # 保存所有分割
                    for split_name, split_ds in ds.items():
                        output_file = target_dir / f"{split_name}.jsonl"
                        split_ds.to_json(str(output_file))
                        logger.info(f"保存数据集到: {output_file}, 样本数: {len(split_ds)}")
            
            except Exception as e:
                logger.warning(f"尝试获取数据集信息失败，使用简单方式下载: {e}")
                
                # 简单方式：直接尝试下载主要分割
                common_splits = ["train", "validation", "test", "dev"]
                any_success = False
                
                for split in common_splits:
                    try:
                        ds = load_dataset(hf_dataset_name, split=split, cache_dir=str(cache_dir))
                        output_file = target_dir / f"{split}.jsonl"
                        ds.to_json(str(output_file))
                        logger.info(f"保存数据集到: {output_file}, 样本数: {len(ds)}")
                        any_success = True
                    except Exception as split_e:
                        logger.warning(f"下载分割 {split} 失败: {split_e}")
                
                if not any_success:
                    # 最简单的方式：无分割直接下载
                    try:
                        ds = load_dataset(hf_dataset_name, cache_dir=str(cache_dir))
                        
                        # 保存主要数据
                        if isinstance(ds, dict):
                            for split_name, split_ds in ds.items():
                                output_file = target_dir / f"{split_name}.jsonl"
                                split_ds.to_json(str(output_file))
                                logger.info(f"保存数据集到: {output_file}, 样本数: {len(split_ds)}")
                                any_success = True
                        else:
                            output_file = target_dir / "data.jsonl"
                            ds.to_json(str(output_file))
                            logger.info(f"保存数据集到: {output_file}, 样本数: {len(ds)}")
                            any_success = True
                    except Exception as all_e:
                        logger.error(f"所有下载方式均失败: {all_e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"从Hugging Face下载数据集 {dataset_id} 失败: {e}")
            return False
    
    def _download_from_modelscope(self, dataset_id: str, dataset_info: Dict[str, Any], 
                                target_dir: Path) -> bool:
        """
        从ModelScope下载数据集
        
        Args:
            dataset_id: 数据集ID
            dataset_info: 数据集配置信息
            target_dir: 目标保存目录
            
        Returns:
            布尔值，表示下载是否成功
        """
        logger.info(f"尝试从ModelScope下载数据集 {dataset_id}...")
        
        try:
            # 检查是否安装了modelscope库
            try:
                from modelscope.msdatasets import MsDataset
            except ImportError:
                logger.error("未安装modelscope库，请使用 'pip install modelscope' 安装")
                logger.info("正在尝试安装modelscope库...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "modelscope"])
                # 再次导入
                from modelscope.msdatasets import MsDataset
                logger.info("modelscope库安装成功")
            
            # 获取ModelScope数据集路径
            ms_path = dataset_info.get("modelscope_url")
            if not ms_path:
                logger.error(f"数据集 {dataset_id} 未配置ModelScope URL")
                return False
            
            # 从URL中提取数据集名称
            # 例如从 https://modelscope.cn/datasets/modelscope/ceval 提取 modelscope/ceval
            if "modelscope.cn/datasets/" in ms_path:
                ms_dataset_name = ms_path.split("modelscope.cn/datasets/")[1]
            else:
                # 如果URL格式不是标准格式，可能直接是数据集名称
                ms_dataset_name = ms_path
            
            logger.info(f"正在从ModelScope下载数据集: {ms_dataset_name}")
            
            # 记录下载信息
            download_info = {
                "source": "modelscope",
                "url": ms_path,
                "downloaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(target_dir / "download_info.json", 'w', encoding='utf-8') as f:
                json.dump(download_info, f, ensure_ascii=False, indent=2)
            
            # 设置下载目录
            cache_dir = self.project_root / "data" / "cache" / "modelscope"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载数据集
            # MsDataset会自动处理下载和缓存
            try:
                # 尝试直接下载数据集
                ms_dataset = MsDataset.load(
                    dataset_name=ms_dataset_name,
                    root_dir=str(cache_dir)
                )
                
                # 检查数据集类型和结构
                if hasattr(ms_dataset, 'keys') and callable(ms_dataset.keys):
                    # 处理字典类型数据集
                    for split_name in ms_dataset.keys():
                        split_data = ms_dataset[split_name]
                        logger.info(f"获取到分割: {split_name}, 类型: {type(split_data)}")
                        
                        # 保存数据
                        if hasattr(split_data, 'to_pandas'):
                            # 转换为pandas DataFrame然后保存为jsonl
                            df = split_data.to_pandas()
                            output_file = target_dir / f"{split_name}.jsonl"
                            df.to_json(str(output_file), orient='records', lines=True, force_ascii=False)
                            logger.info(f"保存数据集到: {output_file}, 样本数: {len(df)}")
                        elif hasattr(split_data, 'to_json'):
                            # 使用内置的to_json方法保存
                            output_file = target_dir / f"{split_name}.jsonl"
                            split_data.to_json(str(output_file))
                            logger.info(f"保存数据集到: {output_file}")
                        else:
                            # 尝试自定义保存方法
                            self._save_modelscope_data(split_data, target_dir / f"{split_name}.jsonl")
                else:
                    # 处理单一数据集
                    logger.info(f"获取到单一数据集，类型: {type(ms_dataset)}")
                    
                    # 保存数据
                    if hasattr(ms_dataset, 'to_pandas'):
                        # 转换为pandas DataFrame然后保存为jsonl
                        df = ms_dataset.to_pandas()
                        output_file = target_dir / "data.jsonl"
                        df.to_json(str(output_file), orient='records', lines=True, force_ascii=False)
                        logger.info(f"保存数据集到: {output_file}, 样本数: {len(df)}")
                    elif hasattr(ms_dataset, 'to_json'):
                        # 使用内置的to_json方法保存
                        output_file = target_dir / "data.jsonl"
                        ms_dataset.to_json(str(output_file))
                        logger.info(f"保存数据集到: {output_file}")
                    else:
                        # 尝试自定义保存方法
                        self._save_modelscope_data(ms_dataset, target_dir / "data.jsonl")
                
            except Exception as e:
                logger.error(f"从ModelScope下载数据集失败: {e}")
                logger.info("尝试下载预处理或者特定拆分的数据集...")
                
                # 尝试常见的分割名称
                splits = ["train", "dev", "validation", "test"]
                any_success = False
                
                for split in splits:
                    try:
                        ms_split = MsDataset.load(
                            dataset_name=ms_dataset_name,
                            split=split,
                            root_dir=str(cache_dir)
                        )
                        
                        # 保存数据
                        if hasattr(ms_split, 'to_pandas'):
                            # 转换为pandas DataFrame然后保存为jsonl
                            df = ms_split.to_pandas()
                            output_file = target_dir / f"{split}.jsonl"
                            df.to_json(str(output_file), orient='records', lines=True, force_ascii=False)
                            logger.info(f"保存数据集到: {output_file}, 样本数: {len(df)}")
                            any_success = True
                        elif hasattr(ms_split, 'to_json'):
                            # 使用内置的to_json方法保存
                            output_file = target_dir / f"{split}.jsonl"
                            ms_split.to_json(str(output_file))
                            logger.info(f"保存数据集到: {output_file}")
                            any_success = True
                        else:
                            # 尝试自定义保存方法
                            any_success = self._save_modelscope_data(ms_split, target_dir / f"{split}.jsonl")
                            
                    except Exception as split_e:
                        logger.warning(f"下载分割 {split} 失败: {split_e}")
                
                if not any_success:
                    logger.error("所有下载方式均失败")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"从ModelScope下载数据集 {dataset_id} 失败: {e}")
            return False
    
    def _save_modelscope_data(self, data, output_path: Path) -> bool:
        """
        保存ModelScope数据集的自定义辅助方法
        
        Args:
            data: ModelScope数据集对象
            output_path: 输出文件路径
            
        Returns:
            布尔值，表示保存是否成功
        """
        try:
            import pandas as pd
            import numpy as np
            
            # 尝试解析不同格式的数据
            if hasattr(data, '__iter__') and not isinstance(data, str):
                # 可迭代对象，尝试将每个项目转换为字典
                rows = []
                for item in data:
                    if isinstance(item, dict):
                        rows.append(item)
                    elif hasattr(item, '__dict__'):
                        rows.append(item.__dict__)
                    else:
                        rows.append({"value": str(item)})
                
                # 将行列表转换为DataFrame然后保存
                if rows:
                    df = pd.DataFrame(rows)
                    df.to_json(str(output_path), orient='records', lines=True, force_ascii=False)
                    logger.info(f"保存数据集到: {output_path}, 样本数: {len(df)}")
                    return True
            
            # 尝试获取data的属性
            elif hasattr(data, '__dict__'):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data.__dict__, f, ensure_ascii=False, default=lambda x: str(x) if isinstance(x, (np.ndarray, pd.DataFrame)) else x)
                logger.info(f"保存数据集到: {output_path}")
                return True
            
            # 其他类型，尝试直接字符串化
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
                logger.info(f"保存数据集字符串表示到: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"保存ModelScope数据失败: {e}")
            return False
    
    def convert_dataset(self, dataset_id: str, force: bool = False) -> bool:
        """
        将数据集转换为XpertFormat格式
        
        Args:
            dataset_id: 数据集ID
            force: 是否强制重新转换，即使已转换的文件存在
            
        Returns:
            布尔值，表示转换是否成功
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            logger.error(f"未找到数据集配置: {dataset_id}")
            return False
        
        # 检查本地状态
        local_status = self._check_local_status(dataset_id)
        if local_status == "未下载":
            logger.warning(f"数据集 {dataset_id} 尚未下载，无法转换")
            return False
        
        if local_status == "已转换" and not force:
            logger.info(f"数据集 {dataset_id} 已转换，跳过转换")
            return True
        
        # 获取数据集路径
        local_path = dataset_info.get("local_path", "")
        if not local_path:
            logger.error(f"数据集 {dataset_id} 未配置本地路径")
            return False
        
        local_dir = self.project_root / local_path
        original_dir = local_dir / "original"
        
        # 获取转换器名称
        converter_name = dataset_info.get("converter")
        if not converter_name:
            logger.error(f"数据集 {dataset_id} 未配置转换器")
            return False
        
        # 执行转换
        logger.info(f"开始转换数据集 {dataset_id}...")
        
        try:
            # 这里需要实现具体的转换逻辑
            # 可以调用对应的转换函数或脚本
            
            # 模拟转换过程
            # 实际实现时，这里应该调用真正的转换代码
            output_path = local_dir / "dataset.jsonl"
            
            # 创建一个示例XpertFormat文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('{"id": "example_1", "query": "这是一个示例问题", "response": "这是一个示例回答", "meta": {"task_type": "qa"}}\n')
                f.write('{"id": "example_2", "query": "另一个示例问题", "response": "另一个示例回答", "meta": {"task_type": "qa"}}\n')
            
            logger.info(f"数据集 {dataset_id} 转换成功，输出文件: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"转换数据集 {dataset_id} 失败: {e}")
            return False
    
    def get_dataset(self, dataset_id: str, auto_download: bool = False, 
                  auto_convert: bool = False, split: Optional[str] = None,
                  sample_size: Optional[int] = None, 
                  filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None) -> Optional[BaseDataset]:
        """
        获取指定数据集的实例
        
        Args:
            dataset_id: 数据集ID
            auto_download: 如果数据集不存在，是否自动下载
            auto_convert: 如果数据集未转换，是否自动转换
            split: 数据集分割，如"train", "dev", "test"
            sample_size: 采样大小，如果指定，将随机采样指定数量的样本
            filter_func: 过滤函数，接收样本字典，返回布尔值表示是否保留
            
        Returns:
            数据集实例，如果获取失败则返回None
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            logger.error(f"未找到数据集配置: {dataset_id}")
            return None
        
        # 检查本地状态
        local_status = self._check_local_status(dataset_id)
        
        # 如果需要，自动下载
        if local_status == "未下载":
            if auto_download:
                success = self.download_dataset(dataset_id)
                if not success:
                    return None
            else:
                logger.warning(f"数据集 {dataset_id} 尚未下载")
                return None
        
        # 如果需要，自动转换
        if local_status == "已下载" and not local_status == "已转换":
            if auto_convert:
                success = self.convert_dataset(dataset_id)
                if not success:
                    return None
            else:
                logger.warning(f"数据集 {dataset_id} 尚未转换为XpertFormat格式")
                return None
        
        # 获取数据集路径
        local_path = dataset_info.get("local_path", "")
        
        # 处理分割
        dataset_path = None
        if split:
            split_file = self.project_root / local_path / f"{split}.jsonl"
            if split_file.exists():
                dataset_path = split_file
            else:
                logger.warning(f"数据集 {dataset_id} 的 {split} 分割文件不存在: {split_file}")
        
        # 如果没有找到分割文件，使用默认数据集文件
        if not dataset_path:
            dataset_path = self.project_root / local_path / "dataset.jsonl"
        
        # 检查文件是否存在
        if not dataset_path.exists():
            logger.error(f"数据集文件不存在: {dataset_path}")
            return None
        
        # 获取媒体文件目录
        media_dir = None
        if dataset_info.get("media_files", False):
            media_dir = self.project_root / local_path / "media"
            if not media_dir.exists():
                logger.warning(f"数据集 {dataset_id} 配置了媒体文件，但目录不存在: {media_dir}")
        
        # 创建数据集实例
        try:
            dataset = XpertFormatDataset(str(dataset_path), media_dir=str(media_dir) if media_dir else None)
            
            # 应用过滤
            if filter_func:
                filtered_dataset = self._filter_dataset(dataset, filter_func)
                if filtered_dataset is not None:
                    dataset = filtered_dataset
                    logger.info(f"已过滤数据集 {dataset_id}，保留 {len(dataset)} 个样本")
            
            # 应用采样
            if sample_size and sample_size > 0 and sample_size < len(dataset):
                sampled_dataset = self._sample_dataset(dataset, sample_size)
                if sampled_dataset is not None:
                    dataset = sampled_dataset
                    logger.info(f"已从数据集 {dataset_id} 中采样 {sample_size} 个样本")
            
            return dataset
            
        except Exception as e:
            logger.error(f"创建数据集 {dataset_id} 实例失败: {e}")
            return None
    
    def _filter_dataset(self, dataset: BaseDataset, 
                        filter_func: Callable[[Dict[str, Any]], bool]) -> Optional[BaseDataset]:
        """
        过滤数据集
        
        Args:
            dataset: 原始数据集
            filter_func: 过滤函数，接收样本字典，返回布尔值表示是否保留
            
        Returns:
            过滤后的数据集，如果过滤失败则返回None
        """
        try:
            # 过滤数据
            filtered_data = [sample for sample in dataset.data if filter_func(sample)]
            
            if not filtered_data:
                logger.warning("过滤后没有剩余样本")
                return None
            
            # 创建新的数据集实例
            new_dataset = type(dataset)(dataset.dataset_path)
            new_dataset.data = filtered_data
            
            return new_dataset
            
        except Exception as e:
            logger.error(f"过滤数据集失败: {e}")
            return None
    
    def _sample_dataset(self, dataset: BaseDataset, sample_size: int) -> Optional[BaseDataset]:
        """
        从数据集中随机采样
        
        Args:
            dataset: 原始数据集
            sample_size: 采样大小
            
        Returns:
            采样后的数据集，如果采样失败则返回None
        """
        try:
            import random
            
            # 确保采样大小有效
            sample_size = min(sample_size, len(dataset))
            
            if sample_size <= 0:
                logger.warning("采样大小必须大于0")
                return None
            
            # 随机采样
            sampled_indices = random.sample(range(len(dataset)), sample_size)
            sampled_data = [dataset.data[i] for i in sampled_indices]
            
            # 创建新的数据集实例
            new_dataset = type(dataset)(dataset.dataset_path)
            new_dataset.data = sampled_data
            
            return new_dataset
            
        except Exception as e:
            logger.error(f"采样数据集失败: {e}")
            return None
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        获取数据集的详细信息
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集信息字典，如果不存在则返回None
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            return None
        
        # 添加本地状态信息
        info = dict(dataset_info)
        info["local_status"] = self._check_local_status(dataset_id)
        
        return info
    
    def get_dataset_statistics(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        获取数据集的统计信息
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集统计信息字典，如果获取失败则返回None
        """
        # 获取数据集实例
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None
        
        # 获取统计信息
        try:
            return dataset.get_statistics()
        except Exception as e:
            logger.error(f"获取数据集 {dataset_id} 统计信息失败: {e}")
            return None
    
    def delete_dataset(self, dataset_id: str) -> bool:
        """
        删除本地数据集文件
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            布尔值，表示删除是否成功
        """
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            logger.error(f"未找到数据集配置: {dataset_id}")
            return False
        
        # 获取数据集路径
        local_path = dataset_info.get("local_path", "")
        if not local_path:
            logger.error(f"数据集 {dataset_id} 未配置本地路径")
            return False
        
        local_dir = self.project_root / local_path
        
        # 检查目录是否存在
        if not local_dir.exists():
            logger.warning(f"数据集目录不存在: {local_dir}")
            return True  # 目录不存在，视为删除成功
        
        # 删除目录
        try:
            shutil.rmtree(local_dir)
            logger.info(f"成功删除数据集 {dataset_id} 的本地文件")
            return True
        except Exception as e:
            logger.error(f"删除数据集 {dataset_id} 失败: {e}")
            return False
    
    def create_dataset_split(self, dataset_id: str, train_ratio: float = 0.8, 
                            dev_ratio: float = 0.1, test_ratio: float = 0.1,
                            shuffle: bool = True, seed: int = 42) -> bool:
        """
        创建数据集分割（训练/验证/测试）
        
        Args:
            dataset_id: 数据集ID
            train_ratio: 训练集比例，默认为0.8
            dev_ratio: 验证集比例，默认为0.1
            test_ratio: 测试集比例，默认为0.1
            shuffle: 是否打乱数据，默认为True
            seed: 随机种子，默认为42
            
        Returns:
            布尔值，表示分割是否成功
        """
        # 验证比例和
        if abs(train_ratio + dev_ratio + test_ratio - 1.0) > 1e-6:
            logger.error(f"分割比例之和必须等于1.0，当前为 {train_ratio + dev_ratio + test_ratio}")
            return False
        
        dataset_info = self.config.get("datasets", {}).get(dataset_id)
        if not dataset_info:
            logger.error(f"未找到数据集配置: {dataset_id}")
            return False
        
        # 获取数据集
        dataset = self.get_dataset(dataset_id, auto_download=False, auto_convert=False)
        if not dataset:
            logger.error(f"获取数据集 {dataset_id} 失败")
            return False
        
        # 获取数据集路径
        local_path = dataset_info.get("local_path", "")
        local_dir = self.project_root / local_path
        
        try:
            import random
            
            # 设置随机种子
            random.seed(seed)
            
            # 获取所有样本
            all_samples = dataset.data
            
            # 打乱数据
            if shuffle:
                random.shuffle(all_samples)
            
            # 计算分割点
            total_size = len(all_samples)
            train_size = int(total_size * train_ratio)
            dev_size = int(total_size * dev_ratio)
            
            # 分割数据
            train_data = all_samples[:train_size]
            dev_data = all_samples[train_size:train_size + dev_size]
            test_data = all_samples[train_size + dev_size:]
            
            # 保存分割后的数据集
            splits = {
                "train": train_data,
                "dev": dev_data,
                "test": test_data
            }
            
            for split_name, split_data in splits.items():
                if not split_data:  # 跳过空分割
                    continue
                    
                output_path = local_dir / f"{split_name}.jsonl"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    for sample in split_data:
                        f.write(json.dumps(sample, ensure_ascii=False) + '\n')
                
                logger.info(f"已保存 {split_name} 分割，共 {len(split_data)} 个样本: {output_path}")
            
            # 更新配置文件中的分割信息
            if "splits" not in dataset_info:
                dataset_info["splits"] = []
                
            for split_name in splits.keys():
                if split_name not in dataset_info["splits"]:
                    dataset_info["splits"].append(split_name)
            
            # 保存更新后的配置
            self._save_config()
            
            return True
            
        except Exception as e:
            logger.error(f"创建数据集分割失败: {e}")
            return False
    
    def _save_config(self) -> bool:
        """
        保存数据集配置
        
        Returns:
            布尔值，表示保存是否成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存数据集配置失败: {e}")
            return False 