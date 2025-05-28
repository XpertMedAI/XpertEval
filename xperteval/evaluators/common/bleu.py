# coding: utf-8
"""
通用评测指标 - BLEU评测器
计算生成文本与参考答案的BLEU分数
"""

import re
import nltk
import jieba

from typing import Dict, List, Any, Optional, Union, Callable
from ...utils import get_logger
from ...core.base_evaluator import BaseEvaluator

# 配置日志
logger = get_logger(__name__)

# 确保下载nltk需要的数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class BLEUEvaluator(BaseEvaluator):
    """
    BLEU评测器
    
    用于评估生成文本与参考答案之间的相似度，通过计算n-gram精确率来衡量。
    BLEU分数适用于机器翻译、文本生成等任务。
    """
    
    def __init__(self, **kwargs):
        """
        初始化BLEU评测器
        
        Args:
            **kwargs: 评测器参数
                - n_gram: 整数，BLEU计算中的最大n-gram大小，默认为4
                - weights: 列表，不同n-gram的权重，默认为[0.25, 0.25, 0.25, 0.25]
                - smoothing: 布尔值，是否使用平滑处理，默认为True
                - language: 字符串，文本语言，支持'en'(英文)和'zh'(中文)，默认为'auto'(自动检测)
        """
        super().__init__(**kwargs)
        self.n_gram = kwargs.get('n_gram', 4)
        self.weights = kwargs.get('weights', [1.0/self.n_gram] * self.n_gram)
        self.smoothing = kwargs.get('smoothing', True)
        self.language = kwargs.get('language', 'auto')
        
        # 确保weights长度与n_gram一致
        if len(self.weights) != self.n_gram:
            logger.warning(f"权重数量({len(self.weights)})与n-gram({self.n_gram})不匹配，将使用均匀权重")
            self.weights = [1.0/self.n_gram] * self.n_gram
    
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估模型预测结果的BLEU分数
        
        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表
            
        Returns:
            包含BLEU评分的字典
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
            
            # 获取参考答案文本
            reference_text = ref.get("answer", {}).get("value", "")
            if not reference_text:
                reference_text = ref.get("response", "")
            
            if not reference_text:
                logger.warning(f"样本 {i} 没有有效的参考答案，已跳过")
                continue
            
            # 处理多参考答案情况
            if isinstance(reference_text, list):
                reference_texts = reference_text
            else:
                reference_texts = [reference_text]
            
            # 计算当前样本的BLEU分数
            try:
                score = self._calculate_bleu(pred, reference_texts)
                individual_scores.append(score)
            except Exception as e:
                logger.warning(f"计算样本 {i} 的BLEU分数时出错: {e}")
        
        # 聚合分数
        result = {
            "bleu": self.aggregate_scores(individual_scores)
        }
        
        return result
    
    def _calculate_bleu(self, prediction: str, references: List[str]) -> float:
        """
        计算单个样本的BLEU分数
        
        Args:
            prediction: 预测文本
            references: 参考答案文本列表
            
        Returns:
            BLEU分数，范围0.0-1.0
        """
        if not prediction:
            return 0.0
        
        # 确定语言并选择相应的分词器
        language = self._detect_language(prediction) if self.language == 'auto' else self.language
        tokenize_func = self._get_tokenize_function(language)
        
        # 分词
        tokenized_pred = tokenize_func(prediction)
        tokenized_refs = [tokenize_func(ref) for ref in references]
        
        # 使用nltk计算BLEU分数
        smoothing_function = nltk.translate.bleu_score.SmoothingFunction().method1 if self.smoothing else None
        
        bleu_score = nltk.translate.bleu_score.sentence_bleu(
            tokenized_refs, 
            tokenized_pred,
            weights=self.weights,
            smoothing_function=smoothing_function
        )
        
        return bleu_score
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 输入文本
            
        Returns:
            语言代码: 'zh'表示中文，'en'表示英文
        """
        # 简单的语言检测：计算中文字符的比例
        chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_char_count = len(text)
        
        # 如果中文字符比例超过20%，认为是中文
        if total_char_count > 0 and chinese_char_count / total_char_count > 0.2:
            return 'zh'
        else:
            return 'en'
    
    def _get_tokenize_function(self, language: str) -> Callable:
        """
        获取对应语言的分词函数
        
        Args:
            language: 语言代码，'zh'或'en'
            
        Returns:
            分词函数
        """
        if language == 'zh':
            return lambda text: list(jieba.cut(text))
        else:  # 默认使用英文分词
            return nltk.word_tokenize 