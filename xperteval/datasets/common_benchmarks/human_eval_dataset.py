# coding: utf-8
"""
HumanEval 数据集解析器

负责解析和转换HumanEval格式的数据集到XpertFormat格式。
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

class HumanEvalDataset(BaseDataset):
    """
    HumanEval数据集解析器
    
    HumanEval是一个代码生成任务数据集，需要根据描述生成完整可运行的函数，并通过测试用例。
    
    原始格式:
    JSON文件，每个样本包含函数签名、描述、标准答案和测试代码
    {
        "task_id": "HumanEval/1",
        "prompt": "函数签名和描述，可能包含示例",
        "entry_point": "function_name",
        "canonical_solution": "标准答案代码",
        "test": "测试代码",
        "language": "python"
    }
    
    转换后的XpertFormat:
    {
        "id": "human_eval_1",
        "query": "函数签名和描述，可能包含示例",
        "response": "标准答案代码",
        "answer": {
            "type": "code",
            "value": "标准答案代码",
            "explanation": null
        },
        "meta": {
            "task_type": "code",
            "language": "python",
            "entry_point": "function_name",
            "test": "测试代码",
            "source": "HumanEval"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化HumanEval数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - language: 编程语言，默认为"python"
        """
        super().__init__(dataset_path, **kwargs)
        
        self.language = kwargs.get('language', 'python')
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析HumanEval数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是单个JSON文件
        if dataset_path.suffix.lower() == '.json':
            data = self._parse_json_file(dataset_path)
        
        # 如果是JSONL文件（可能是已转换的格式）
        elif dataset_path.suffix.lower() == '.jsonl':
            data = self._parse_jsonl_file(dataset_path)
        
        # 如果是目录，则查找相关JSON文件
        elif dataset_path.is_dir():
            for file_path in dataset_path.glob("*.json*"):
                if file_path.suffix.lower() == '.json':
                    file_data = self._parse_json_file(file_path)
                elif file_path.suffix.lower() == '.jsonl':
                    file_data = self._parse_jsonl_file(file_path)
                else:
                    continue
                
                data.extend(file_data)
        
        else:
            logger.error(f"不支持的文件格式: {dataset_path}")
            raise ValueError(f"不支持的文件格式: {dataset_path}")
        
        logger.info(f"成功加载 HumanEval 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析HumanEval JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                # HumanEval数据集可能是单个问题或问题列表
                if isinstance(json_data, list):
                    for problem in json_data:
                        xpert_sample = self._convert_sample(problem)
                        if xpert_sample:
                            data.append(xpert_sample)
                elif isinstance(json_data, dict):
                    # 检查是否为包含多个任务的字典
                    if all(key.startswith("HumanEval/") for key in json_data.keys()):
                        # 每个键是一个任务ID，值是任务数据
                        for task_id, problem in json_data.items():
                            if isinstance(problem, dict):
                                problem["task_id"] = task_id  # 确保任务ID存在
                                xpert_sample = self._convert_sample(problem)
                                if xpert_sample:
                                    data.append(xpert_sample)
                    else:
                        # 单个问题
                        xpert_sample = self._convert_sample(json_data)
                        if xpert_sample:
                            data.append(xpert_sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 失败: {e}")
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
                    try:
                        sample = json.loads(line.strip())
                        # 检查是否已经是XpertFormat
                        if "query" in sample and "answer" in sample:
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
        将HumanEval样本转换为XpertFormat格式
        
        Args:
            sample: HumanEval样本
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            task_id = sample.get('task_id')
            prompt = sample.get('prompt')
            entry_point = sample.get('entry_point')
            canonical_solution = sample.get('canonical_solution')
            test = sample.get('test')
            language = sample.get('language', self.language)
            
            if not task_id or not prompt or not canonical_solution:
                logger.warning(f"样本缺少必要字段: {sample}")
                return None
            
            # 从task_id提取数字部分作为ID
            id_match = re.search(r'(\d+)', task_id)
            id_number = id_match.group(1) if id_match else "unknown"
            
            return {
                "id": f"human_eval_{id_number}",
                "query": prompt,
                "response": canonical_solution,
                "answer": {
                    "type": "code",
                    "value": canonical_solution,
                    "explanation": None
                },
                "meta": {
                    "task_type": "code",
                    "language": language,
                    "entry_point": entry_point,
                    "test": test,
                    "source": "HumanEval",
                    "original_id": task_id
                }
            }
            
        except Exception as e:
            logger.warning(f"转换样本失败: {e}")
            return None
    
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
        
        # 统计编程语言分布
        languages = {}
        prompt_lengths = []
        solution_lengths = []
        
        for sample in self.data:
            language = sample.get("meta", {}).get("language", "未知")
            languages[language] = languages.get(language, 0) + 1
            
            # 统计提示和解决方案的长度
            prompt = sample.get("query", "")
            solution = sample.get("response", "")
            
            prompt_lengths.append(len(prompt))
            solution_lengths.append(len(solution))
        
        # 计算平均长度
        avg_prompt_length = sum(prompt_lengths) / len(prompt_lengths) if prompt_lengths else 0
        avg_solution_length = sum(solution_lengths) / len(solution_lengths) if solution_lengths else 0
        
        return {
            "sample_count": len(self.data),
            "task_type": "code",
            "languages": languages,
            "avg_prompt_length": avg_prompt_length,
            "avg_solution_length": avg_solution_length
        } 