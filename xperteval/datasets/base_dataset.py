# coding: utf-8
"""
数据集处理与加载 - 数据集基类

提供统一的数据集接口，所有特定格式的数据集解析器都应该继承此基类。
"""
import abc
from typing import Dict, Any, List, Union, Optional
from pathlib import Path

class BaseDataset(abc.ABC):
    """
    数据集基类
    
    所有特定格式的数据集解析器都应继承此类。
    提供统一的接口用于加载和访问不同格式的评测数据集。
    """
    
    @abc.abstractmethod
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化数据集
        
        Args:
            dataset_path: 数据集文件路径
            **kwargs: 其他特定于数据集的参数
        """
        self.dataset_path = Path(dataset_path)
        self.data = []  # 初始化为空列表，在load_data中填充
        
    @abc.abstractmethod
    def __len__(self) -> int:
        """
        返回数据集中样本的数量
        
        Returns:
            整数，表示数据集的长度
        """
        pass

    @abc.abstractmethod
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        获取指定索引的数据样本
        
        Args:
            idx: 样本索引
            
        Returns:
            包含样本数据的字典
        """
        pass

    @abc.abstractmethod
    def load_data(self) -> None:
        """
        加载和预处理数据集
        
        实现具体的数据加载逻辑，如读取文件、解析json等
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取数据集的元数据信息
        
        Returns:
            包含数据集描述、格式、大小等信息的字典
        """
        return {
            "name": self.__class__.__name__,
            "path": str(self.dataset_path),
            "size": len(self),
            "format": self.get_format_name()
        }
    
    def get_format_name(self) -> str:
        """
        返回数据集格式名称
        
        Returns:
            字符串，表示数据集的格式
        """
        return "base" 