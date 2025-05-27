# coding: utf-8
"""
评测器模块

本模块提供各种评测指标的实现，包括通用评测指标和领域特定评测指标。
并提供评测器注册和获取的功能。
"""

from typing import Dict, List, Type, Any, Optional

from ..core.base_evaluator import BaseEvaluator
from .common import AccuracyEvaluator, BLEUEvaluator, MathEvaluator
from .tcm import TcmDiagnosisEvaluator

# 评测器注册表
EVALUATOR_REGISTRY = {
    # 通用评测器
    "accuracy": AccuracyEvaluator,
    "bleu": BLEUEvaluator,
    "math": MathEvaluator,
    
    # 中医药特定评测器
    "tcm_diagnosis": TcmDiagnosisEvaluator,
    
    # 其他评测器会在这里注册
}

def get_evaluator(evaluator_name: str, **kwargs) -> BaseEvaluator:
    """
    获取指定名称的评测器实例
    
    Args:
        evaluator_name: 评测器名称，必须在EVALUATOR_REGISTRY中注册
        **kwargs: 传递给评测器构造函数的参数
        
    Returns:
        评测器实例
        
    Raises:
        ValueError: 如果评测器名称未注册
    """
    if evaluator_name not in EVALUATOR_REGISTRY:
        available_evaluators = ", ".join(EVALUATOR_REGISTRY.keys())
        raise ValueError(f"未知的评测器: {evaluator_name}，可用的评测器有: {available_evaluators}")
    
    evaluator_class = EVALUATOR_REGISTRY[evaluator_name]
    return evaluator_class(**kwargs)

def get_evaluators(evaluator_names: List[str], **kwargs) -> List[BaseEvaluator]:
    """
    获取多个评测器实例
    
    Args:
        evaluator_names: 评测器名称列表
        **kwargs: 传递给所有评测器构造函数的公共参数
        
    Returns:
        评测器实例列表
    """
    return [get_evaluator(name, **kwargs) for name in evaluator_names]

def list_evaluators() -> List[str]:
    """
    列出所有可用的评测器名称
    
    Returns:
        评测器名称列表
    """
    return list(EVALUATOR_REGISTRY.keys())

def register_evaluator(name: str, evaluator_class: Type[BaseEvaluator]) -> None:
    """
    注册新的评测器
    
    Args:
        name: 评测器名称
        evaluator_class: 评测器类
    """
    if not issubclass(evaluator_class, BaseEvaluator):
        raise TypeError(f"评测器类必须继承自BaseEvaluator，而不是 {type(evaluator_class)}")
    
    EVALUATOR_REGISTRY[name] = evaluator_class 