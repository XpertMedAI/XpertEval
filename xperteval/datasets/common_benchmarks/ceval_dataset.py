# coding: utf-8
"""
C-Eval 数据集解析器

负责解析和转换C-Eval格式的数据集到XpertFormat格式。
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ..base_dataset import BaseDataset
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

class CEvalDataset(BaseDataset):
    """
    C-Eval数据集解析器
    
    C-Eval是一个中文评测集，包含多个领域的选择题，专注于中文内容和中国特定知识领域。
    
    原始格式:
    JSON文件，每个样本包含问题ID、问题、选项、答案、领域和类别
    {
        "id": "问题ID",
        "question": "中文问题文本",
        "options": ["选项A", "选项B", "选项C", "选项D"],
        "answer": "A",
        "field": "科学",
        "category": "物理"
    }
    
    转换后的XpertFormat:
    {
        "id": "ceval_<field>_<id>",
        "query": "中文问题文本",
        "choices": [
            {"id": "A", "content": "选项A内容"},
            {"id": "B", "content": "选项B内容"},
            {"id": "C", "content": "选项C内容"},
            {"id": "D", "content": "选项D内容"}
        ],
        "answer": {
            "type": "choice",
            "value": "A",
            "explanation": null
        },
        "meta": {
            "task_type": "choice",
            "field": "科学",
            "category": "物理",
            "source": "C-Eval",
            "language": "zh"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化C-Eval数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - split: 数据集分割(dev/test/val)，默认为"test"
                - field: 特定领域，默认为None(全部领域)
        """
        super().__init__(dataset_path, **kwargs)
        
        self.split = kwargs.get('split', 'test')
        self.field = kwargs.get('field', None)
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析C-Eval数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSON文件
        if dataset_path.is_dir():
            # 查找指定分割的文件
            json_file = dataset_path / f"ceval_{self.split}.json"
            if not json_file.exists():
                json_file = dataset_path / f"{self.split}.json"
            
            if json_file.exists():
                data = self._parse_json_file(json_file)
            else:
                logger.warning(f"找不到 {self.split} 数据文件")
        
        # 如果是单个JSON文件
        elif dataset_path.suffix.lower() == '.json':
            data = self._parse_json_file(dataset_path)
        
        # 如果是JSONL文件
        elif dataset_path.suffix.lower() == '.jsonl':
            data = self._parse_jsonl_file(dataset_path)
        
        else:
            logger.error(f"不支持的文件格式: {dataset_path}")
            raise ValueError(f"不支持的文件格式: {dataset_path}")
        
        # 如果指定了特定领域，过滤数据
        if self.field and data:
            data = [sample for sample in data if sample.get("meta", {}).get("field") == self.field]
            logger.info(f"过滤后的 {self.field} 领域样本数量: {len(data)}")
        
        logger.info(f"成功加载 C-Eval 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析C-Eval JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                # C-Eval数据集通常是问题列表
                if isinstance(json_data, list):
                    for problem in json_data:
                        xpert_sample = self._convert_sample(problem)
                        if xpert_sample:
                            data.append(xpert_sample)
                else:
                    logger.warning(f"JSON文件不是列表格式: {file_path}")
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 失败: {e}")
            return []
    
    def _parse_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析JSONL格式的文件
        
        Args:
            file_path: JSONL文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        sample = json.loads(line.strip())
                        # 检查是否已经是XpertFormat
                        if "query" in sample and "choices" in sample:
                            data.append(sample)
                        else:
                            # 尝试转换为XpertFormat
                            xpert_sample = self._convert_sample(sample)
                            if xpert_sample:
                                data.append(xpert_sample)
                    except json.JSONDecodeError:
                        logger.warning(f"跳过无效的JSON行: {line}")
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSONL文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将C-Eval样本转换为XpertFormat格式
        
        Args:
            sample: C-Eval样本
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            question_id = sample.get('id')
            question = sample.get('question')
            options = sample.get('options', [])
            answer = sample.get('answer')
            field = sample.get('field', '未知')
            category = sample.get('category', '未知')
            
            if not question or not options or len(options) < 2:
                logger.warning(f"样本缺少必要字段或选项不足: {sample}")
                return None
            
            # 处理中文特殊字符
            question = self._normalize_chinese_text(question)
            options = [self._normalize_chinese_text(opt) for opt in options]
            
            # 创建选项列表
            choices = []
            option_ids = ["A", "B", "C", "D", "E", "F", "G", "H"]
            for i, option in enumerate(options):
                if i < len(option_ids):
                    choices.append({
                        "id": option_ids[i],
                        "content": option
                    })
            
            # 创建XpertFormat样本
            return {
                "id": f"ceval_{field}_{question_id}" if question_id else f"ceval_{field}_{len(self.data)}",
                "query": question,
                "choices": choices,
                "answer": {
                    "type": "choice",
                    "value": answer,
                    "explanation": None
                },
                "meta": {
                    "task_type": "choice",
                    "field": field,
                    "category": category,
                    "source": "C-Eval",
                    "language": "zh"
                }
            }
            
        except Exception as e:
            logger.warning(f"转换样本失败: {e}")
            return None
    
    def _normalize_chinese_text(self, text: str) -> str:
        """
        处理中文文本中的特殊字符和编码问题
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return text
        
        # 全角转半角
        text = self._full_width_to_half_width(text)
        
        # 统一中文引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # 去除不可见字符
        text = ''.join(c for c in text if c.isprintable())
        
        return text.strip()
    
    def _full_width_to_half_width(self, text: str) -> str:
        """
        将全角字符转换为半角字符
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        result = ""
        for char in text:
            code = ord(char)
            # 全角空格(12288) -> 半角空格(32)
            if code == 0x3000:
                result += chr(0x20)
            # 全角字符(65281-65374) -> 半角字符(33-126)
            elif 0xFF01 <= code <= 0xFF5E:
                result += chr(code - 0xFEE0)
            else:
                result += char
        return result
    
    def convert_to_xpert_format(self, output_path: Optional[str] = None) -> bool:
        """
        将数据集转换为XpertFormat格式并保存
        
        Args:
            output_path: 输出文件路径，如果为None则不保存
            
        Returns:
            布尔值，表示转换是否成功
        """
        if not self.data:
            logger.error("没有数据可供转换")
            return False
        
        # 数据已经是XpertFormat格式，直接保存
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    for sample in self.data:
                        f.write(json.dumps(sample, ensure_ascii=False) + '\n')
                
                logger.info(f"成功将数据集转换并保存到 {output_path}")
                return True
                
            except Exception as e:
                logger.error(f"保存转换后的数据集失败: {e}")
                return False
        
        return True
    
    def __len__(self) -> int:
        """
        返回数据集样本数量
        
        Returns:
            样本数量
        """
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        获取指定索引的样本
        
        Args:
            idx: 样本索引
            
        Returns:
            样本数据
        """
        return self.data[idx]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        Returns:
            统计信息字典
        """
        if not self.data:
            return {"sample_count": 0}
        
        # 统计领域和类别分布
        fields = {}
        categories = {}
        
        for sample in self.data:
            field = sample.get("meta", {}).get("field", "未知")
            category = sample.get("meta", {}).get("category", "未知")
            
            fields[field] = fields.get(field, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "sample_count": len(self.data),
            "task_type": "choice",
            "fields": fields,
            "categories": categories,
            "language": "zh"
        } 