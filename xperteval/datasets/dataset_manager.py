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
from typing import Dict, Any, List, Union, Optional, Tuple
import subprocess
import requests
from tqdm import tqdm

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
        # 这里需要实现具体的Hugging Face数据集下载逻辑
        # 可以使用datasets库或直接使用HTTP请求
        logger.info(f"尝试从Hugging Face下载数据集 {dataset_id}...")
        
        try:
            # 这里是一个简化的实现，实际应用中可能需要更复杂的逻辑
            # 例如使用datasets库: datasets.load_dataset(dataset_id)
            
            # 模拟下载成功
            # 实际实现时，这里应该是真正的下载代码
            with open(target_dir / "download_info.json", 'w', encoding='utf-8') as f:
                json.dump({
                    "source": "huggingface",
                    "url": dataset_info.get("huggingface_url"),
                    "downloaded_at": "2025-05-19"
                }, f, ensure_ascii=False, indent=2)
            
            # 创建一个示例文件，表示下载成功
            # 实际下载时，这里应该保存真正的数据集文件
            with open(target_dir / "example.txt", 'w', encoding='utf-8') as f:
                f.write(f"这是从Hugging Face下载的{dataset_id}数据集示例文件")
            
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
        # 这里需要实现具体的ModelScope数据集下载逻辑
        logger.info(f"尝试从ModelScope下载数据集 {dataset_id}...")
        
        try:
            # 这里是一个简化的实现，实际应用中需要使用ModelScope SDK
            # 模拟下载成功
            with open(target_dir / "download_info.json", 'w', encoding='utf-8') as f:
                json.dump({
                    "source": "modelscope",
                    "url": dataset_info.get("modelscope_url"),
                    "downloaded_at": "2025-05-19"
                }, f, ensure_ascii=False, indent=2)
            
            # 创建一个示例文件，表示下载成功
            with open(target_dir / "example.txt", 'w', encoding='utf-8') as f:
                f.write(f"这是从ModelScope下载的{dataset_id}数据集示例文件")
            
            return True
            
        except Exception as e:
            logger.error(f"从ModelScope下载数据集 {dataset_id} 失败: {e}")
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
                  auto_convert: bool = False) -> Optional[BaseDataset]:
        """
        获取指定数据集的实例
        
        Args:
            dataset_id: 数据集ID
            auto_download: 如果数据集不存在，是否自动下载
            auto_convert: 如果数据集未转换，是否自动转换
            
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
            return XpertFormatDataset(str(dataset_path), media_dir=str(media_dir) if media_dir else None)
        except Exception as e:
            logger.error(f"创建数据集 {dataset_id} 实例失败: {e}")
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