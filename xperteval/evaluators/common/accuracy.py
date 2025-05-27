# coding: utf-8
"""
通用评测指标 - 准确率评测器
计算分类任务的准确率等指标
"""

import re
from typing import Dict, List, Any, Optional, Union
import logging

from ...core.base_evaluator import BaseEvaluator
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

class AccuracyEvaluator(BaseEvaluator):
    """
    准确率评测器
    
    用于评估分类任务（如选择题）的准确率，以及简单文本匹配的精确匹配率。
    支持不同答案类型的评测：
    1. 选择题 (choice): 提取选项标识符（如A、B、C、D）并比较
    2. 文本 (text): 精确匹配或部分匹配
    3. 数值 (number): 数值比较，允许一定的误差
    """
    
    def __init__(self, **kwargs):
        """
        初始化准确率评测器
        
        Args:
            **kwargs: 评测器参数
                - exact_match: 布尔值，是否要求完全匹配，默认为True
                - case_sensitive: 布尔值，是否区分大小写，默认为False
                - allow_partial: 布尔值，是否允许部分匹配，默认为False
                - numeric_tolerance: 浮点数，数值比较的容差，默认为0.0001
        """
        super().__init__(**kwargs)
        self.exact_match = kwargs.get('exact_match', True)
        self.case_sensitive = kwargs.get('case_sensitive', False)
        self.allow_partial = kwargs.get('allow_partial', False)
        self.numeric_tolerance = kwargs.get('numeric_tolerance', 0.0001)
    
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估模型预测结果的准确率
        
        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表
            
        Returns:
            包含准确率评分的字典
        """
        if len(predictions) != len(references):
            logger.warning(f"预测数量({len(predictions)})与参考答案数量({len(references)})不匹配")
            # 取最小长度
            length = min(len(predictions), len(references))
            predictions = predictions[:length]
            references = references[:length]
        
        individual_scores = []
        choice_scores = []
        text_scores = []
        number_scores = []
        
        for i, (pred, ref) in enumerate(zip(predictions, references)):
            # 检查样本有效性
            if not self._is_valid_sample(pred, ref):
                logger.warning(f"样本 {i} 无效，已跳过")
                continue
            
            # 获取答案类型
            answer_type = ref.get("answer", {}).get("type", "text")
            answer_value = ref.get("answer", {}).get("value", "")
            
            # 根据答案类型选择评分方法
            if answer_type == "choice":
                score = self._evaluate_choice(pred, ref)
                if score is not None:
                    individual_scores.append(score)
                    choice_scores.append(score)
            elif answer_type == "number":
                score = self._evaluate_number(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
                    number_scores.append(score)
            else:  # 默认为文本类型
                score = self._evaluate_text(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
                    text_scores.append(score)
        
        # 聚合分数
        result = {
            "accuracy": self.aggregate_scores(individual_scores)
        }
        
        # 添加各类型的详细分数
        if choice_scores:
            result["choice_accuracy"] = self.aggregate_scores(choice_scores)
        if text_scores:
            result["text_accuracy"] = self.aggregate_scores(text_scores)
        if number_scores:
            result["number_accuracy"] = self.aggregate_scores(number_scores)
        
        return result
    
    def _evaluate_choice(self, prediction: str, reference: Dict[str, Any]) -> Optional[float]:
        """
        评估选择题类型的准确率
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案
            
        Returns:
            评分，1.0表示正确，0.0表示错误，None表示无法评估
        """
        # 获取正确答案
        answer_value = reference.get("answer", {}).get("value", "").strip()
        if not answer_value:
            logger.warning("参考答案为空")
            return None
        
        # 尝试从预测中提取选项
        choice_match = self._extract_choice(prediction)
        if choice_match:
            # 如果提取成功，直接比较选项
            return 1.0 if choice_match.upper() == answer_value.upper() else 0.0
        
        # 如果没有提取到明确的选项，检查选项内容是否在预测中
        choices = reference.get("choices", [])
        if choices and isinstance(choices, list):
            # 查找正确选项的内容
            correct_choice_content = None
            for choice in choices:
                if isinstance(choice, dict) and choice.get("id", "").upper() == answer_value.upper():
                    correct_choice_content = choice.get("content", "")
                    break
            
            if correct_choice_content:
                # 检查正确选项内容是否在预测中
                normalized_pred = self._normalize_text(prediction)
                normalized_content = self._normalize_text(correct_choice_content)
                
                if normalized_content in normalized_pred:
                    return 1.0
                
                # 检查其他错误选项是否在预测中
                for choice in choices:
                    if isinstance(choice, dict) and choice.get("id", "").upper() != answer_value.upper():
                        wrong_content = choice.get("content", "")
                        normalized_wrong = self._normalize_text(wrong_content)
                        
                        # 如果预测中包含错误选项但不包含正确选项，则判定为错误
                        if normalized_wrong in normalized_pred:
                            return 0.0
        
        # 无法确定选择，尝试常规文本匹配
        return self._evaluate_text(prediction, answer_value)
    
    def _evaluate_text(self, prediction: str, reference: str) -> float:
        """
        评估文本类型的准确率
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案文本
            
        Returns:
            评分，1.0表示正确，0.0表示错误
        """
        if not prediction or not reference:
            return 0.0
        
        # 文本规范化
        if not self.case_sensitive:
            prediction = prediction.lower()
            reference = reference.lower()
        
        # 去除前后空白
        prediction = prediction.strip()
        reference = reference.strip()
        
        # 精确匹配
        if self.exact_match:
            return 1.0 if prediction == reference else 0.0
        
        # 部分匹配
        if self.allow_partial:
            return 1.0 if reference in prediction or prediction in reference else 0.0
        
        return 0.0
    
    def _evaluate_number(self, prediction: str, reference: str) -> Optional[float]:
        """
        评估数值类型的准确率
        
        Args:
            prediction: 模型预测文本
            reference: 参考数值（字符串格式）
            
        Returns:
            评分，1.0表示正确，0.0表示错误，None表示无法评估
        """
        # 提取数字
        pred_num = self._extract_number(prediction)
        ref_num = self._extract_number(reference)
        
        if pred_num is None or ref_num is None:
            return None
        
        # 数值比较，允许一定的容差
        return 1.0 if abs(pred_num - ref_num) <= self.numeric_tolerance else 0.0
    
    def _extract_choice(self, text: str) -> Optional[str]:
        """
        从文本中提取选择题选项（A、B、C、D等）
        
        Args:
            text: 输入文本
            
        Returns:
            提取到的选项，如果没有找到则返回None
        """
        # 匹配常见的选择题答案模式
        patterns = [
            r'^[^\w]*([A-Da-d])[^\w]*$',  # 单独的A/B/C/D
            r'^\s*(?:选项|选择|答案|answer|option)[^\w]*([A-Da-d])[^\w]*$',  # "选项A"或"答案是B"
            r'^\s*([A-Da-d])[^\w]*(?:是正确的|是正确答案|is correct|is the answer)',  # "A是正确的"
            r'正确(?:的?选项|的?答案)[是为:：\s]+([A-Da-d])',  # "正确答案是A"
            r'选择\s*([A-Da-d])',  # "选择A"
            r'答案[是为:：\s]+([A-Da-d])',  # "答案是A"
            r'答案[:：\s]*([A-Da-d])',  # "答案：A"
            r'(?:The answer is|I choose|My answer is)[^\w]*([A-Da-d])',  # 英文常见表达
        ]
        
        # 尝试所有模式
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # 查找文本中出现的所有选项
        all_choices = re.findall(r'\b([A-Da-d])\b', text, re.IGNORECASE)
        if len(all_choices) == 1:
            # 如果只有一个选项，很可能是答案
            return all_choices[0].upper()
        
        return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """
        从文本中提取数字
        
        Args:
            text: 输入文本
            
        Returns:
            提取到的数字，如果没有找到则返回None
        """
        # 尝试直接转换
        try:
            return float(text.strip())
        except (ValueError, TypeError):
            pass
        
        # 尝试正则表达式提取
        number_pattern = r'-?\d+\.?\d*'
        match = re.search(number_pattern, text)
        if match:
            try:
                return float(match.group(0))
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _normalize_text(self, text: str) -> str:
        """
        文本规范化处理
        
        Args:
            text: 输入文本
            
        Returns:
            规范化后的文本
        """
        if not self.case_sensitive:
            text = text.lower()
        
        # 去除前后空白
        text = text.strip()
        
        return text 