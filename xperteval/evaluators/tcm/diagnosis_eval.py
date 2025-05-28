# coding: utf-8
"""
中医药特定评测指标 - 诊断准确性评测器
中医诊断准确性等指标
"""

import re
import difflib

from typing import Dict, List, Any, Optional, Union, Set
from ...utils import get_logger
from ...core.base_evaluator import BaseEvaluator

# 配置日志
logger = get_logger(__name__)


class TcmDiagnosisEvaluator(BaseEvaluator):
    """
    中医诊断准确性评测器
    
    用于评估模型在中医辨证论治方面的能力，包括对症候的识别、疾病诊断的准确性等。
    支持多种诊断评估方式：
    1. 症候匹配：评估模型识别出的证候与标准答案的匹配程度
    2. 疾病诊断：评估模型诊断出的疾病与标准答案的一致性
    3. 治法选择：评估模型提出的治法是否与标准答案一致
    """
    
    def __init__(self, **kwargs):
        """
        初始化中医诊断准确性评测器
        
        Args:
            **kwargs: 评测器参数
                - match_threshold: 浮点数，匹配阈值，默认为0.7
                - exact_match: 布尔值，是否要求精确匹配，默认为False
                - partial_credit: 布尔值，是否给予部分分数，默认为True
                - keywords_weight: 浮点数，关键词匹配权重，默认为0.6
                - normalize_tcm_terms: 布尔值，是否规范化中医术语，默认为True
        """
        super().__init__(**kwargs)
        self.match_threshold = kwargs.get('match_threshold', 0.7)
        self.exact_match = kwargs.get('exact_match', False)
        self.partial_credit = kwargs.get('partial_credit', True)
        self.keywords_weight = kwargs.get('keywords_weight', 0.6)
        self.normalize_tcm_terms = kwargs.get('normalize_tcm_terms', True)
        
        # 中医术语同义词表（简化版）
        self.tcm_synonyms = {
            "气虚": ["气虚", "气不足", "肺气虚", "脾气虚", "气虚证", "气短"],
            "阴虚": ["阴虚", "阴不足", "阴亏", "阴津亏", "阴虚证", "津亏"],
            "血虚": ["血虚", "血亏", "血不足", "血少", "血虚证"],
            "阳虚": ["阳虚", "阳不足", "阳气虚", "阳亏", "阳虚证", "畏寒"],
            "湿热": ["湿热", "湿热蕴结", "湿热内蕴", "湿热证"],
            "气滞": ["气滞", "气机不畅", "气机阻滞", "气郁", "气滞证"],
            "血瘀": ["血瘀", "瘀血", "血瘀证", "瘀阻", "血行不畅"],
            "痰湿": ["痰湿", "痰浊", "痰湿内停", "痰湿证", "痰浊内停"],
            "肝郁": ["肝郁", "肝气郁结", "肝气不舒", "肝郁气滞"]
        }
    
    def evaluate(self, predictions: List[str], references: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        评估模型在中医诊断方面的表现
        
        Args:
            predictions: 模型生成的预测结果列表
            references: 数据集中的标准答案/参考列表
            
        Returns:
            包含评测分数的字典
        """
        if len(predictions) != len(references):
            logger.warning(f"预测数量({len(predictions)})与参考答案数量({len(references)})不匹配")
            # 取最小长度
            length = min(len(predictions), len(references))
            predictions = predictions[:length]
            references = references[:length]
        
        individual_scores = []
        syndrome_scores = []  # 证候评分
        disease_scores = []   # 疾病评分
        treatment_scores = [] # 治法评分
        
        for i, (pred, ref) in enumerate(zip(predictions, references)):
            # 检查样本有效性
            if not self._is_valid_sample(pred, ref):
                logger.warning(f"样本 {i} 无效，已跳过")
                continue
            
            # 获取评测类型和标准答案
            eval_type = ref.get("meta", {}).get("tcm_eval_type", "syndrome")
            answer_value = ref.get("answer", {}).get("value", "")
            
            # 根据评测类型选择评测方法
            if eval_type == "syndrome":  # 证候评测
                score = self._evaluate_syndrome(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
                    syndrome_scores.append(score)
            elif eval_type == "disease":  # 疾病评测
                score = self._evaluate_disease(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
                    disease_scores.append(score)
            elif eval_type == "treatment":  # 治法评测
                score = self._evaluate_treatment(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
                    treatment_scores.append(score)
            else:  # 默认评测方法
                score = self._evaluate_text_similarity(pred, answer_value)
                if score is not None:
                    individual_scores.append(score)
        
        # 聚合分数
        result = {
            "tcm_diagnosis": self.aggregate_scores(individual_scores)
        }
        
        # 添加各类型的详细分数
        if syndrome_scores:
            result["syndrome"] = self.aggregate_scores(syndrome_scores)
        if disease_scores:
            result["disease"] = self.aggregate_scores(disease_scores)
        if treatment_scores:
            result["treatment"] = self.aggregate_scores(treatment_scores)
        
        return result
    
    def _evaluate_syndrome(self, prediction: str, reference: str) -> float:
        """
        评估证候辨识准确性
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案文本
            
        Returns:
            评分，范围0.0-1.0
        """
        if not prediction or not reference:
            return 0.0
        
        # 规范化文本
        if self.normalize_tcm_terms:
            prediction = self._normalize_tcm_text(prediction)
            reference = self._normalize_tcm_text(reference)
        
        # 提取证候关键词
        pred_syndromes = self._extract_tcm_syndromes(prediction)
        ref_syndromes = self._extract_tcm_syndromes(reference)
        
        # 计算匹配度
        return self._calculate_set_similarity(pred_syndromes, ref_syndromes)
    
    def _evaluate_disease(self, prediction: str, reference: str) -> float:
        """
        评估疾病诊断准确性
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案文本
            
        Returns:
            评分，范围0.0-1.0
        """
        if not prediction or not reference:
            return 0.0
        
        # 由于疾病诊断通常需要精确匹配，这里使用更严格的评分方式
        # 提取疾病名称
        pred_diseases = self._extract_disease_names(prediction)
        ref_diseases = self._extract_disease_names(reference)
        
        # 计算匹配度
        return self._calculate_set_similarity(pred_diseases, ref_diseases)
    
    def _evaluate_treatment(self, prediction: str, reference: str) -> float:
        """
        评估治法选择准确性
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案文本
            
        Returns:
            评分，范围0.0-1.0
        """
        if not prediction or not reference:
            return 0.0
        
        # 提取治法关键词
        pred_treatments = self._extract_tcm_treatments(prediction)
        ref_treatments = self._extract_tcm_treatments(reference)
        
        # 计算匹配度
        return self._calculate_set_similarity(pred_treatments, ref_treatments)
    
    def _evaluate_text_similarity(self, prediction: str, reference: str) -> float:
        """
        评估文本相似度
        
        Args:
            prediction: 模型预测文本
            reference: 参考答案文本
            
        Returns:
            评分，范围0.0-1.0
        """
        if not prediction or not reference:
            return 0.0
        
        # 使用difflib计算文本相似度
        similarity = difflib.SequenceMatcher(None, prediction, reference).ratio()
        
        # 如果需要精确匹配，设置阈值
        if self.exact_match:
            return 1.0 if similarity >= self.match_threshold else 0.0
        
        # 否则，返回相似度分数
        return similarity
    
    def _extract_tcm_syndromes(self, text: str) -> Set[str]:
        """
        从文本中提取中医证候
        
        Args:
            text: 输入文本
            
        Returns:
            证候集合
        """
        syndromes = set()
        
        # 常见证候模式
        patterns = [
            r'(气虚|阴虚|阳虚|血虚|气滞|血瘀|痰湿|湿热|肝郁|脾虚|肾虚|心虚)(?:证|症)?',
            r'(肝|脾|肺|肾|心|胃|胆)(气|阴|阳|血)(虚|实|热|寒|湿|燥|郁)',
            r'(内|外|虚|实|寒|热|表|里|气|血)(证|症)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # 对于多组捕获的情况，组合成完整的证候名
                        syndrome = ''.join(match).strip()
                    else:
                        syndrome = match.strip()
                    
                    if syndrome:
                        syndromes.add(syndrome)
        
        # 处理同义词，将各种表达方式标准化
        normalized_syndromes = set()
        for syndrome in syndromes:
            found = False
            for standard, synonyms in self.tcm_synonyms.items():
                if syndrome in synonyms:
                    normalized_syndromes.add(standard)
                    found = True
                    break
            
            if not found:
                normalized_syndromes.add(syndrome)
        
        return normalized_syndromes
    
    def _extract_disease_names(self, text: str) -> Set[str]:
        """
        从文本中提取疾病名称
        
        Args:
            text: 输入文本
            
        Returns:
            疾病名称集合
        """
        diseases = set()
        
        # 中医疾病名称通常比较规范，可以使用常见后缀
        patterns = [
            r'([\u4e00-\u9fff]{2,6}(?:病|证|症))',
            r'([\u4e00-\u9fff]{2,}性[\u4e00-\u9fff]{1,3})',
            r'([\u4e00-\u9fff]{2,}型[\u4e00-\u9fff]{1,3})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            diseases.update([match.strip() for match in matches if match.strip()])
        
        return diseases
    
    def _extract_tcm_treatments(self, text: str) -> Set[str]:
        """
        从文本中提取中医治法
        
        Args:
            text: 输入文本
            
        Returns:
            治法集合
        """
        treatments = set()
        
        # 常见治法模式
        patterns = [
            r'(补|泻|清|温|润|化|消|散|解|固|通|行|调|和|升|降|开|合|回|引|畅|疏)(气|血|阴|阳|湿|痰|热|寒|毒|风)',
            r'([\u4e00-\u9fff]{1,2})(气|血|阴|阳|湿|痰|热|寒|毒|风)',
            r'(补|泻|清|温|润|化|消|散|解|固|通|行|调|和|升|降|开|合|回|引|畅|疏)(肝|脾|肺|肾|心|胃|胆)',
            r'(健脾|补肾|疏肝|化痰|利湿|消食|解表|活血|止痛|固表)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        treatment = ''.join(match).strip()
                    else:
                        treatment = match.strip()
                    
                    if treatment:
                        treatments.add(treatment)
        
        return treatments
    
    def _normalize_tcm_text(self, text: str) -> str:
        """
        规范化中医文本
        
        Args:
            text: 输入文本
            
        Returns:
            规范化后的文本
        """
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 统一术语表示
        for standard, synonyms in self.tcm_synonyms.items():
            for synonym in synonyms:
                if synonym != standard:
                    text = text.replace(synonym, standard)
        
        # 替换常见不一致表达
        replacements = [
            (r'证候', '证'),
            (r'症候', '证'),
            (r'肝气郁结', '肝郁'),
            (r'脾胃虚弱', '脾虚'),
            (r'肾精亏虚', '肾虚')
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _calculate_set_similarity(self, pred_set: Set[str], ref_set: Set[str]) -> float:
        """
        计算两个集合的相似度
        
        Args:
            pred_set: 预测集合
            ref_set: 参考集合
            
        Returns:
            相似度分数，范围0.0-1.0
        """
        if not pred_set and not ref_set:
            return 1.0  # 两个空集合视为完全匹配
        
        if not pred_set or not ref_set:
            return 0.0  # 一个空一个非空，视为完全不匹配
        
        # 计算交集、并集
        intersection = pred_set.intersection(ref_set)
        union = pred_set.union(ref_set)
        
        # 计算Jaccard相似度
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # 计算召回率和精确率
        recall = len(intersection) / len(ref_set) if ref_set else 0.0
        precision = len(intersection) / len(pred_set) if pred_set else 0.0
        
        # 如果需要精确匹配，直接比较集合是否相等
        if self.exact_match:
            return 1.0 if pred_set == ref_set else 0.0
        
        # 如果允许部分匹配，计算加权分数
        if self.partial_credit:
            # 使用F1分数：精确率和召回率的调和平均
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0
            
            # 结合Jaccard和F1
            return self.keywords_weight * f1 + (1 - self.keywords_weight) * jaccard
        
        # 默认使用Jaccard相似度
        return jaccard 