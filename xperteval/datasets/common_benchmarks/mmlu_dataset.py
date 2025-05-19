# coding: utf-8
"""
MMLU (Massive Multitask Language Understanding) 数据集解析器

负责解析和转换MMLU格式的数据集到XpertFormat格式。
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

class MMLUDataset(BaseDataset):
    """
    MMLU数据集解析器
    
    MMLU (Massive Multitask Language Understanding) 是一个包含57个学科领域的多选题评测集，
    用于测试模型的知识广度。
    
    原始格式:
    CSV文件，每行包含问题、选项和答案
    
    转换后的XpertFormat:
    {
        "id": "mmlu_<subject>_<index>",
        "query": "问题文本",
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
            "subject": "数学",
            "difficulty": "中等",
            "source": "MMLU"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化MMLU数据集
        
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
        加载并解析MMLU数据集
        
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
        
        logger.info(f"成功加载 MMLU 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_csv_file(self, file_path: Path, subject: str) -> List[Dict[str, Any]]:
        """
        解析MMLU CSV文件
        
        Args:
            file_path: CSV文件路径
            subject: 学科名称
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if len(row) < 5:  # 问题 + 4个选项 + 答案
                        logger.warning(f"跳过格式不正确的行 {i+1}: {row}")
                        continue
                    
                    question = row[0]
                    options = row[1:5]  # 四个选项
                    answer = row[5] if len(row) > 5 else None
                    
                    # 转换为XpertFormat
                    sample = {
                        "id": f"mmlu_{subject}_{i}",
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
                            "source": "MMLU"
                        }
                    }
                    
                    data.append(sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析CSV文件 {file_path} 失败: {e}")
            return []
    
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
            "subjects": subjects
        } 