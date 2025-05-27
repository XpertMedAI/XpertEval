# coding: utf-8
"""
中医药特定评测指标

提供一系列用于评估模型在中医药领域表现的评测指标，如辨证准确率、方剂评估等。
"""

from .diagnosis_eval import TcmDiagnosisEvaluator

__all__ = ['TcmDiagnosisEvaluator'] 