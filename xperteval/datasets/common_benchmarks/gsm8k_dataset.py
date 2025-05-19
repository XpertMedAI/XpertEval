# coding: utf-8
"""
GSM8K (Grade School Math 8K) 数据集解析器

负责解析和转换GSM8K格式的数据集到XpertFormat格式。
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ..base_dataset import BaseDataset
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

class GSM8KDataset(BaseDataset):
    """
    GSM8K数据集解析器
    
    GSM8K (Grade School Math 8K) 是一个包含小学数学应用题的数据集，
    需要多步推理才能解决。
    
    原始格式:
    JSON文件，每个样本包含问题和带步骤的答案
    {
        "question": "数学问题描述",
        "answer": "解题步骤\n最终答案: 42"
    }
    
    转换后的XpertFormat:
    {
        "id": "gsm8k_<index>",
        "query": "数学问题描述",
        "response": "解题步骤\n最终答案: 42",
        "answer": {
            "type": "step_by_step",
            "value": "42",
            "explanation": "解题步骤"
        },
        "meta": {
            "task_type": "math",
            "source": "GSM8K"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化GSM8K数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - split: 数据集分割(train/test)，默认为"test"
        """
        super().__init__(dataset_path, **kwargs)
        
        self.split = kwargs.get('split', 'test')
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析GSM8K数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSON文件
        if dataset_path.is_dir():
            json_file = dataset_path / f"{self.split}.jsonl"
            if not json_file.exists():
                json_file = dataset_path / f"{self.split}.json"
            
            if json_file.exists():
                data = self._parse_json_file(json_file)
            else:
                logger.warning(f"找不到 {self.split} 数据文件")
        
        # 如果是单个JSON文件
        elif dataset_path.suffix.lower() in ['.json', '.jsonl']:
            data = self._parse_json_file(dataset_path)
        
        else:
            logger.error(f"不支持的文件格式: {dataset_path}")
            raise ValueError(f"不支持的文件格式: {dataset_path}")
        
        logger.info(f"成功加载 GSM8K 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析GSM8K JSON/JSONL文件
        
        Args:
            file_path: JSON/JSONL文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            # 判断是JSON还是JSONL
            if file_path.suffix.lower() == '.jsonl':
                # JSONL格式，逐行解析
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        try:
                            sample = json.loads(line.strip())
                            xpert_sample = self._convert_sample(sample, i)
                            if xpert_sample:
                                data.append(xpert_sample)
                        except json.JSONDecodeError:
                            logger.warning(f"跳过无效的JSON行: {line}")
            else:
                # JSON格式，整体解析
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                    # 判断是否为列表
                    if isinstance(json_data, list):
                        for i, sample in enumerate(json_data):
                            xpert_sample = self._convert_sample(sample, i)
                            if xpert_sample:
                                data.append(xpert_sample)
                    else:
                        logger.warning(f"JSON文件不是列表格式: {file_path}")
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """
        将GSM8K样本转换为XpertFormat格式
        
        Args:
            sample: GSM8K样本
            index: 样本索引
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            question = sample.get('question')
            answer_text = sample.get('answer')
            
            if not question or not answer_text:
                logger.warning(f"样本 {index} 缺少问题或答案")
                return None
            
            # 提取最终答案和解题步骤
            final_answer, explanation = self._extract_answer_and_steps(answer_text)
            
            return {
                "id": f"gsm8k_{index}",
                "query": question,
                "response": answer_text,
                "answer": {
                    "type": "step_by_step",
                    "value": final_answer,
                    "explanation": explanation
                },
                "meta": {
                    "task_type": "math",
                    "source": "GSM8K"
                }
            }
            
        except Exception as e:
            logger.warning(f"转换样本 {index} 失败: {e}")
            return None
    
    def _extract_answer_and_steps(self, answer_text: str) -> Tuple[str, str]:
        """
        从答案文本中提取最终答案和解题步骤
        
        Args:
            answer_text: 完整答案文本
            
        Returns:
            元组 (最终答案, 解题步骤)
        """
        # 尝试使用正则表达式匹配最终答案
        # GSM8K通常使用 "answer: X" 或 "答案是 X" 或 "= X" 的格式
        answer_patterns = [
            r'答案是\s*[：:]\s*(\d+(?:\.\d+)?)',
            r'答案是\s*(\d+(?:\.\d+)?)',
            r'答案\s*[：:]\s*(\d+(?:\.\d+)?)',
            r'answer\s*[：:]\s*(\d+(?:\.\d+)?)',
            r'answer is\s*(\d+(?:\.\d+)?)',
            r'= (\d+(?:\.\d+)?)$',
            r'最终答案\s*[：:]\s*(\d+(?:\.\d+)?)',
            r'最终答案是\s*(\d+(?:\.\d+)?)',
            r'结果是\s*(\d+(?:\.\d+)?)',
            r'结果\s*[：:]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)$'  # 最后一行的数字
        ]
        
        final_answer = None
        for pattern in answer_patterns:
            match = re.search(pattern, answer_text, re.IGNORECASE)
            if match:
                final_answer = match.group(1)
                break
        
        # 如果没有找到最终答案，使用最后一个数字
        if not final_answer:
            numbers = re.findall(r'(\d+(?:\.\d+)?)', answer_text)
            if numbers:
                final_answer = numbers[-1]
            else:
                final_answer = "未知"
                logger.warning(f"无法从答案文本中提取最终答案: {answer_text}")
        
        # 解题步骤就是完整的答案文本
        explanation = answer_text
        
        return final_answer, explanation
    
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
        
        # 统计答案长度分布
        answer_lengths = []
        for sample in self.data:
            answer_value = sample.get("answer", {}).get("value", "")
            answer_lengths.append(len(str(answer_value)))
        
        # 计算平均答案长度
        avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        
        return {
            "sample_count": len(self.data),
            "task_type": "math",
            "avg_answer_length": avg_answer_length
        } 