# coding: utf-8
"""
MATH 数据集解析器

负责解析和转换MATH格式的数据集到XpertFormat格式，处理LaTeX公式。
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

class MATHDataset(BaseDataset):
    """
    MATH数据集解析器
    
    MATH是一个包含高中和大学水平数学问题的数据集，包含复杂公式，需要形式化推理。
    
    原始格式:
    JSON文件，每个样本包含问题、类型、难度和解答
    {
        "problem": "数学问题描述，可能包含LaTeX公式",
        "level": "高中",
        "type": "代数",
        "solution": "详细的解题过程，包含LaTeX公式",
        "answer": "最终答案"
    }
    
    转换后的XpertFormat:
    {
        "id": "math_<type>_<index>",
        "query": "数学问题描述，可能包含LaTeX公式",
        "response": "详细的解题过程，包含LaTeX公式",
        "answer": {
            "type": "step_by_step",
            "value": "最终答案",
            "explanation": "详细的解题过程，包含LaTeX公式"
        },
        "meta": {
            "task_type": "math",
            "subject": "代数",
            "difficulty": "高中",
            "source": "MATH"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化MATH数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - split: 数据集分割(train/test)，默认为"test"
                - math_type: 数学类型(algebra, counting_and_probability, geometry, intermediate_algebra, number_theory, prealgebra, precalculus)
        """
        super().__init__(dataset_path, **kwargs)
        
        self.split = kwargs.get('split', 'test')
        self.math_type = kwargs.get('math_type', None)
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析MATH数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSON文件
        if dataset_path.is_dir():
            # 如果指定了特定数学类型
            if self.math_type:
                type_dir = dataset_path / self.math_type
                if type_dir.exists() and type_dir.is_dir():
                    # 处理该类型下的所有JSON文件
                    for file_path in type_dir.glob("*.json"):
                        file_data = self._parse_json_file(file_path, self.math_type)
                        data.extend(file_data)
                else:
                    logger.warning(f"找不到数学类型目录: {type_dir}")
            else:
                # 处理所有类型
                for type_dir in dataset_path.iterdir():
                    if type_dir.is_dir():
                        math_type = type_dir.name
                        for file_path in type_dir.glob("*.json"):
                            file_data = self._parse_json_file(file_path, math_type)
                            data.extend(file_data)
        
        # 如果是单个JSON文件
        elif dataset_path.suffix.lower() == '.json':
            # 尝试从文件名或路径推断数学类型
            math_type = self.math_type
            if not math_type:
                parent_dir = dataset_path.parent.name
                if parent_dir in ["algebra", "counting_and_probability", "geometry", 
                                 "intermediate_algebra", "number_theory", "prealgebra", 
                                 "precalculus"]:
                    math_type = parent_dir
                else:
                    math_type = "unknown"
            
            data = self._parse_json_file(dataset_path, math_type)
        
        # 如果是JSONL文件（可能是已转换的格式）
        elif dataset_path.suffix.lower() == '.jsonl':
            data = self._parse_jsonl_file(dataset_path)
        
        else:
            logger.error(f"不支持的文件格式: {dataset_path}")
            raise ValueError(f"不支持的文件格式: {dataset_path}")
        
        logger.info(f"成功加载 MATH 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path, math_type: str) -> List[Dict[str, Any]]:
        """
        解析MATH JSON文件
        
        Args:
            file_path: JSON文件路径
            math_type: 数学类型
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                # MATH数据集的JSON文件可能是单个问题或问题列表
                if isinstance(json_data, list):
                    for i, problem in enumerate(json_data):
                        xpert_sample = self._convert_sample(problem, f"{math_type}_{file_path.stem}_{i}")
                        if xpert_sample:
                            data.append(xpert_sample)
                else:
                    xpert_sample = self._convert_sample(json_data, f"{math_type}_{file_path.stem}")
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
                    sample = json.loads(line.strip())
                    data.append(sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSONL文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any], id_prefix: str) -> Optional[Dict[str, Any]]:
        """
        将MATH样本转换为XpertFormat格式
        
        Args:
            sample: MATH样本
            id_prefix: ID前缀
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            problem = sample.get('problem')
            solution = sample.get('solution')
            answer = sample.get('answer')
            level = sample.get('level', '未知')
            math_type = sample.get('type', id_prefix.split('_')[0] if '_' in id_prefix else '未知')
            
            if not problem or not solution:
                logger.warning(f"样本 {id_prefix} 缺少问题或解答")
                return None
            
            # 处理LaTeX公式
            problem = self._process_latex(problem)
            solution = self._process_latex(solution)
            if answer:
                answer = self._process_latex(answer)
            
            return {
                "id": f"math_{id_prefix}",
                "query": problem,
                "response": solution,
                "answer": {
                    "type": "step_by_step",
                    "value": answer or self._extract_final_answer(solution),
                    "explanation": solution
                },
                "meta": {
                    "task_type": "math",
                    "subject": math_type,
                    "difficulty": level,
                    "source": "MATH"
                }
            }
            
        except Exception as e:
            logger.warning(f"转换样本 {id_prefix} 失败: {e}")
            return None
    
    def _process_latex(self, text: str) -> str:
        """
        处理文本中的LaTeX公式，确保其格式正确
        
        Args:
            text: 包含LaTeX公式的文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return text
        
        # 确保行内公式使用 $ 而不是 \( \)
        text = text.replace('\\(', '$').replace('\\)', '$')
        
        # 确保行间公式使用 $$ 而不是 \[ \]
        text = text.replace('\\[', '$$').replace('\\]', '$$')
        
        # 处理一些常见的LaTeX错误
        text = text.replace('\\\\', '\\')  # 双反斜杠可能导致问题
        
        return text
    
    def _extract_final_answer(self, solution: str) -> str:
        """
        从解答中提取最终答案
        
        Args:
            solution: 解答文本
            
        Returns:
            提取的最终答案
        """
        # 尝试查找最终答案的常见模式
        patterns = [
            r'最终答案\s*[：:]\s*(.+?)(?:\n|$)',
            r'答案\s*[：:]\s*(.+?)(?:\n|$)',
            r'答案是\s*(.+?)(?:\n|$)',
            r'answer\s*[：:]\s*(.+?)(?:\n|$)',
            r'answer is\s*(.+?)(?:\n|$)',
            r'结果\s*[：:]\s*(.+?)(?:\n|$)',
            r'结果是\s*(.+?)(?:\n|$)',
            r'所以\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, solution, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 如果没有找到明确的最终答案，返回解答的最后一行
        lines = solution.strip().split('\n')
        if lines:
            return lines[-1].strip()
        
        return "未知"
    
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
        
        # 统计数学类型和难度分布
        types = {}
        difficulties = {}
        
        for sample in self.data:
            math_type = sample.get("meta", {}).get("subject", "未知")
            difficulty = sample.get("meta", {}).get("difficulty", "未知")
            
            types[math_type] = types.get(math_type, 0) + 1
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
        
        return {
            "sample_count": len(self.data),
            "task_type": "math",
            "types": types,
            "difficulties": difficulties
        } 