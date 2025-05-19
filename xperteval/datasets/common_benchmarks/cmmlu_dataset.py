# coding: utf-8
"""
CMMLU (Chinese Massive Multitask Language Understanding) 数据集解析器

负责解析和转换CMMLU格式的数据集到XpertFormat格式。
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

class CMMLUDataset(BaseDataset):
    """
    CMMLU数据集解析器
    
    CMMLU (Chinese Massive Multitask Language Understanding) 是一个专注于中文知识评测的数据集，
    涵盖67个中文学科领域。
    
    原始格式:
    CSV文件，每行包含问题、选项和答案
    
    转换后的XpertFormat:
    {
        "id": "cmmlu_<subject>_<index>",
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
            "subject": "中国历史",
            "difficulty": "困难",
            "source": "CMMLU",
            "language": "zh"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化CMMLU数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - split: 数据集分割(dev/test/val)，默认为"test"
                - subject: 特定学科，默认为None(全部学科)
        """
        super().__init__(dataset_path, **kwargs)
        
        self.split = kwargs.get('split', 'test')
        self.subject = kwargs.get('subject', None)
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析CMMLU数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找所有相关CSV文件
        if dataset_path.is_dir():
            csv_files = []
            
            # 如果指定了特定学科，只处理该学科
            if self.subject:
                subject_file = dataset_path / f"{self.subject}_{self.split}.csv"
                if subject_file.exists():
                    csv_files.append((self.subject, subject_file))
                else:
                    logger.warning(f"找不到学科 {self.subject} 的 {self.split} 数据文件")
            else:
                # 处理所有学科
                for file_path in dataset_path.glob(f"*_{self.split}.csv"):
                    subject = file_path.name.replace(f"_{self.split}.csv", "")
                    csv_files.append((subject, file_path))
            
            # 处理每个CSV文件
            for subject, file_path in csv_files:
                subject_data = self._parse_csv_file(file_path, subject)
                data.extend(subject_data)
        
        # 如果是单个CSV文件
        elif dataset_path.suffix.lower() == '.csv':
            subject = dataset_path.stem.replace(f"_{self.split}", "")
            data = self._parse_csv_file(dataset_path, subject)
        
        # 如果是JSONL文件（可能是已转换的格式）
        elif dataset_path.suffix.lower() == '.jsonl':
            data = self._parse_jsonl_file(dataset_path)
        
        else:
            logger.error(f"不支持的文件格式: {dataset_path}")
            raise ValueError(f"不支持的文件格式: {dataset_path}")
        
        logger.info(f"成功加载 CMMLU 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_csv_file(self, file_path: Path, subject: str) -> List[Dict[str, Any]]:
        """
        解析CMMLU CSV文件
        
        Args:
            file_path: CSV文件路径
            subject: 学科名称
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            # 使用utf-8-sig编码处理带BOM的UTF-8文件
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if len(row) < 5:  # 问题 + 4个选项 + 答案
                        logger.warning(f"跳过格式不正确的行 {i+1}: {row}")
                        continue
                    
                    question = row[0]
                    options = row[1:5]  # 四个选项
                    answer = row[5] if len(row) > 5 else None
                    
                    # 处理中文特殊字符
                    question = self._normalize_chinese_text(question)
                    options = [self._normalize_chinese_text(opt) for opt in options]
                    
                    # 转换为XpertFormat
                    sample = {
                        "id": f"cmmlu_{subject}_{i}",
                        "query": question,
                        "choices": [
                            {"id": "A", "content": options[0]},
                            {"id": "B", "content": options[1]},
                            {"id": "C", "content": options[2]},
                            {"id": "D", "content": options[3]}
                        ],
                        "answer": {
                            "type": "choice",
                            "value": answer,
                            "explanation": None
                        },
                        "meta": {
                            "task_type": "choice",
                            "subject": subject,
                            "source": "CMMLU",
                            "language": "zh"
                        }
                    }
                    
                    data.append(sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析CSV文件 {file_path} 失败: {e}")
            return []
    
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
    
    def _parse_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析JSONL格式的文件（可能是已转换的格式）
        
        Args:
            file_path: JSONL文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    sample = json.loads(line.strip())
                    data.append(sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSONL文件 {file_path} 失败: {e}")
            return []
    
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
        
        # 统计学科分布
        subjects = {}
        for sample in self.data:
            subject = sample.get("meta", {}).get("subject", "未知")
            subjects[subject] = subjects.get(subject, 0) + 1
        
        return {
            "sample_count": len(self.data),
            "task_type": "choice",
            "subjects": subjects,
            "language": "zh"
        } 