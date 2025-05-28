# coding: utf-8
"""
评测器基类模块

定义评测器的抽象基类和通用接口，所有具体评测指标都应该继承此基类。
"""

import abc

from ..utils import get_logger
from typing import Dict, List, Any, Optional, Union, Tuple

# 配置日志
logger = get_logger(__name__)


class BaseEvaluator(abc.ABC):
    """
    评测器抽象基类
    
    所有具体评测指标的实现都应该继承这个基类，并实现evaluate方法。
    """
    
    def __init__(self, **kwargs):
        """
        初始化评测器
        
        Args:
            **kwargs: 评测器的其他参数
        """
        self.name = kwargs.get('name', self.__class__.__name__)
        self.kwargs = kwargs
    
    @abc.abstractmethod
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估模型预测结果
        
        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表，每个参考是一个字典，包含答案类型、值等信息
            
        Returns:
            包含评测指标名称和分数的字典，例如 {"accuracy": 0.85}
        """
        pass

    def _pre_evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        预处理预测和参考答案

        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表，每个参考是一个字典，包含答案类型、值等信息

        Returns:
            处理后的预测和参考答案列表
        """
        # 判断预测和参考答案数量是否一致
        if len(predictions) != len(references):
            logger.warning(f"预测数量({len(predictions)})与参考答案数量({len(references)})不匹配")
            # 取最小长度
            length = min(len(predictions), len(references))
            predictions = predictions[:length]
            references = references[:length]

        # 返回处理后的预测和参考答案
        return predictions, references
    
    def _is_valid_sample(self, prediction: str, reference: Dict[str, Any]) -> bool:
        """
        检查样本是否有效
        
        Args:
            prediction: 单个预测结果
            reference: 单个参考答案
            
        Returns:
            布尔值，表示样本是否有效
        """
        # 基本检查：预测和参考都不应为None
        if prediction is None or reference is None:
            return False
        
        # 检查参考答案格式
        if not isinstance(reference, dict) or "answer" not in reference:
            return False
        
        # 检查answer字段格式
        answer = reference.get("answer", {})
        if not isinstance(answer, dict) or "value" not in answer:
            return False
        
        return True
    
    def aggregate_scores(self, individual_scores: List[float]) -> Dict[str, float]:
        """
        聚合单个样本的评分
        
        Args:
            individual_scores: 单个样本的评分列表
            
        Returns:
            包含聚合评分的字典，例如 {"score": 平均分, "min": 最低分, "max": 最高分}
        """
        if not individual_scores:
            return {"score": 0.0, "min": 0.0, "max": 0.0, "count": 0}
        
        return {
            "score": sum(individual_scores) / len(individual_scores),  # 平均分
            "min": min(individual_scores),                             # 最低分
            "max": max(individual_scores),                             # 最高分
            "count": len(individual_scores)                            # 有效样本数
        } 