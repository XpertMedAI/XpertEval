# coding: utf-8
"""
数据集处理与加载 - 数据集基类
"""
import abc

class BaseDataset(abc.ABC):
    @abc.abstractmethod
    def __init__(self, dataset_path: str, **kwargs):
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        pass

    @abc.abstractmethod
    def __getitem__(self, idx: int) -> dict:
        pass

    @abc.abstractmethod
    def load_data(self):
        pass 