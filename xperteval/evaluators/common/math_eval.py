# coding: utf-8
"""
通用评测指标 - 数学评测器
计算数学问题解答的正确性
"""

import re
import math

from typing import Dict, List, Any, Optional, Union, Tuple
from ...utils import get_logger
from ...core.base_evaluator import BaseEvaluator

# 配置日志
logger = get_logger(__name__)


class MathEvaluator(BaseEvaluator):
    """
    数学评测器
    
    用于评估数学问题的解答，支持数值比较、公式比较等。
    主要适用于：
    1. 算术计算：加减乘除、分数、小数等
    2. 方程求解：得到正确的数值答案
    3. 简单代数：多项式计算等
    """
    
    def __init__(self, **kwargs):
        """
        初始化数学评测器
        
        Args:
            **kwargs: 评测器参数
                - tolerance: 浮点数，答案容差，默认为1e-6
                - normalize: 布尔值，是否规范化答案，默认为True
                - require_units: 布尔值，是否需要单位一致，默认为False
                - strict_format: 布尔值，是否严格格式匹配，默认为False
        """
        super().__init__(**kwargs)
        self.tolerance = kwargs.get('tolerance', 1e-6)
        self.normalize = kwargs.get('normalize', True)
        self.require_units = kwargs.get('require_units', False)
        self.strict_format = kwargs.get('strict_format', False)
    
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估模型对数学问题的解答
        
        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表
            
        Returns:
            包含评测分数的字典
        """
        # 预处理预测和参考答案
        predictions, references = self._pre_evaluate(predictions, references)
        
        # 汇总分数
        individual_scores = []
        
        # 遍历预测和参考答案
        for i, (pred, ref) in enumerate(zip(predictions, references)):
            # 检查样本有效性
            if not self._is_valid_sample(pred, ref):
                logger.warning(f"样本 {i} 无效，已跳过")
                continue
            
            # 获取答案类型和值
            answer_type = ref.get("answer", {}).get("type", "number")
            answer_value = ref.get("answer", {}).get("value", "")
            
            # 对于数学问题，只处理 number 和 text 类型的答案
            if answer_type not in ["number", "text"]:
                logger.warning(f"样本 {i} 答案类型不是数学类型，已跳过")
                continue
            
            # 计算当前样本的分数
            score = self._evaluate_math_answer(pred, answer_value)
            individual_scores.append(score)
        
        # 聚合分数
        result = {
            "math_accuracy": self.aggregate_scores(individual_scores)
        }
        
        return result
    
    def _evaluate_math_answer(self, prediction: str, reference: str) -> float:
        """
        评估数学答案的正确性
        
        Args:
            prediction: 预测文本
            reference: 参考答案文本
            
        Returns:
            评分，1.0表示完全正确，0.0表示完全错误
        """
        if not prediction or not reference:
            return 0.0
        
        # 提取数值和单位
        pred_value, pred_unit = self._extract_number_and_unit(prediction)
        ref_value, ref_unit = self._extract_number_and_unit(reference)
        
        # 如果无法提取数值，返回0分
        if pred_value is None or ref_value is None:
            return 0.0
        
        # 检查单位一致性（如果需要）
        if self.require_units and pred_unit != ref_unit:
            return 0.0
        
        # 计算数值误差
        try:
            # 对于接近0的值，使用绝对误差
            if abs(ref_value) < self.tolerance:
                error = abs(pred_value - ref_value)
                return 1.0 if error <= self.tolerance else 0.0
            
            # 对于其他值，使用相对误差
            relative_error = abs((pred_value - ref_value) / ref_value)
            return 1.0 if relative_error <= self.tolerance else 0.0
        except Exception as e:
            logger.warning(f"计算数值误差时出错: {e}")
            return 0.0
    
    def _extract_number_and_unit(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        从文本中提取数值和单位
        
        Args:
            text: 输入文本
            
        Returns:
            (数值, 单位)的元组，如果无法提取则数值为None
        """
        # 规范化文本
        if self.normalize:
            text = self._normalize_math_text(text)
        
        # 匹配数字和可能的单位
        # 例如: "42.5 kg", "1/2", "-3.14", "2e-3 m/s"
        pattern = r'(-?\d+\.?\d*(?:e[+-]?\d+)?|\d+/\d+)\s*([a-zA-Z°/%]*)'
        match = re.search(pattern, text)
        
        if not match:
            return None, None
        
        number_str = match.group(1)
        unit = match.group(2).strip() if match.group(2) else None
        
        # 转换分数形式
        if '/' in number_str and not 'e' in number_str.lower():
            try:
                num, denom = map(float, number_str.split('/'))
                value = num / denom if denom != 0 else None
            except Exception:
                value = None
        else:
            try:
                value = float(number_str)
            except Exception:
                value = None
        
        return value, unit
    
    def _normalize_math_text(self, text: str) -> str:
        """
        规范化数学文本
        
        Args:
            text: 输入文本
            
        Returns:
            规范化后的文本
        """
        # 去除前后空白
        text = text.strip()
        
        # 替换全角数字和符号为半角
        full_to_half = str.maketrans('０１２３４５６７８９．－＋（）／', '0123456789.-+()/') 
        text = text.translate(full_to_half)
        
        # 替换常见词语为数字
        text = re.sub(r'负\s*(\d+)', r'-\1', text)  # 负3 -> -3
        text = re.sub(r'零点(\d+)', r'0.\1', text)  # 零点五 -> 0.5
        
        # 替换中文分数表示
        text = re.sub(r'(\d+)\s*分之\s*(\d+)', r'\2/\1', text)  # 2分之1 -> 1/2
        
        return text 