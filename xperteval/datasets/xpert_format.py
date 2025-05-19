# coding: utf-8
"""
数据集处理与加载 - XpertFormat 格式数据集解析器
解析 XpertFormat 统一数据集格式

XpertFormat是一种灵活的统一数据格式，支持多种评测任务类型，包括选择题、开放式问答、
代码生成、数学问题以及多模态任务。它基于MS-SWIFT格式扩展而来，增加了更多结构化字段。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple
import logging
from ..utils import get_logger
from .base_dataset import BaseDataset

# 配置日志
logger = get_logger(__name__)

class XpertFormatDataset(BaseDataset):
    """
    XpertFormat格式数据集解析器
    
    XpertFormat是一种统一的评测数据格式，支持多种任务类型，包括选择题、开放式问答、
    代码生成、数学问题和多模态任务等。该类负责将XpertFormat格式的数据加载为统一的
    内部表示，以便于模型评测使用。
    """
    
    def __init__(self, dataset_path: str, media_dir: Optional[str] = None, **kwargs):
        """
        初始化XpertFormat数据集
        
        Args:
            dataset_path: JSONL格式的数据集文件路径
            media_dir: 多媒体文件存储目录，如果提供，则相对路径会基于此目录解析
            **kwargs: 其他参数
        """
        super().__init__(dataset_path, **kwargs)
        self.media_dir = Path(media_dir) if media_dir else None
        self.data = []  # 存储解析后的数据样本
        self.load_data()  # 初始化时加载数据
        
    def __len__(self) -> int:
        """返回数据集大小"""
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """获取指定索引的数据样本"""
        if idx < 0 or idx >= len(self.data):
            raise IndexError(f"索引 {idx} 超出数据集范围 [0, {len(self.data) - 1}]")
        return self.data[idx]
    
    def load_data(self) -> None:
        """
        加载并解析XpertFormat格式的数据集
        
        XpertFormat格式中，每行是一个JSON对象，可能包含以下字段:
        - id: 样本唯一标识符
        - query: 问题文本
        - response: 参考答案或标准答案
        - history: (可选) 历史对话轮次
        - files: (可选) 引用的多模态文件列表
        - choices: (可选) 选择题选项列表
        - answer: 统一的答案字段，包含类型、值和可选的解释
        - meta: 元数据，包含任务类型、类别、难度等信息
        - evaluation: (可选) 评估相关信息
        """
        logger.info(f"开始加载XpertFormat数据集: {self.dataset_path}")
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    try:
                        # 解析JSON行
                        sample = json.loads(line.strip())
                        
                        # 验证格式
                        if not self.validate_format(sample):
                            logger.warning(f"第{line_number}行数据格式不符合XpertFormat规范，已跳过")
                            continue
                        
                        # 处理并标准化样本数据
                        processed_sample = self._process_sample(sample)
                        if processed_sample:
                            self.data.append(processed_sample)
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"第{line_number}行解析JSON失败: {e}")
                    except Exception as e:
                        logger.warning(f"处理第{line_number}行时出错: {e}")
            
            logger.info(f"成功加载{len(self.data)}个样本")
            
        except FileNotFoundError:
            logger.error(f"数据集文件不存在: {self.dataset_path}")
            raise
        except Exception as e:
            logger.error(f"加载数据集时发生错误: {e}")
            raise
    
    def validate_format(self, sample: Dict[str, Any]) -> bool:
        """
        验证数据样本是否符合XpertFormat规范
        
        Args:
            sample: 待验证的数据样本
            
        Returns:
            布尔值，表示数据是否有效
        """
        # 检查必需字段
        if "query" not in sample:
            return False
        
        # 检查answer字段的格式(如果存在)
        if "answer" in sample:
            if not isinstance(sample["answer"], dict):
                return False
            if "type" not in sample["answer"] or "value" not in sample["answer"]:
                return False
        
        # 检查choices字段的格式(如果存在)
        if "choices" in sample and not isinstance(sample["choices"], list):
            return False
        
        # 检查files字段的格式(如果存在)
        if "files" in sample and not isinstance(sample["files"], list):
            return False
        
        # 检查history字段的格式(如果存在)
        if "history" in sample and not isinstance(sample["history"], list):
            return False
        
        return True
    
    def _process_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个数据样本，将其转换为标准格式
        
        Args:
            sample: 原始数据样本字典
            
        Returns:
            处理后的样本字典，如果样本无效则返回None
        """
        # 创建标准化样本
        processed = {
            "id": sample.get("id", f"sample_{len(self.data)}"),
            "query": sample["query"],
            "response": sample.get("response", ""),
            "is_multimodal": False,  # 默认为非多模态，后续检查是否包含文件
            "is_multi_turn": False,  # 默认为单轮，后续检查是否包含历史对话
            "is_choice": False,      # 默认为非选择题，后续检查是否包含选项
        }
        
        # 处理历史对话
        if "history" in sample and isinstance(sample["history"], list):
            processed["history"] = sample["history"]
            processed["is_multi_turn"] = True
        else:
            processed["history"] = []
        
        # 处理选择题选项
        if "choices" in sample and isinstance(sample["choices"], list):
            processed["choices"] = sample["choices"]
            processed["is_choice"] = True
        
        # 处理答案字段
        if "answer" in sample and isinstance(sample["answer"], dict):
            processed["answer"] = {
                "type": sample["answer"].get("type", "text"),
                "value": sample["answer"].get("value", ""),
                "explanation": sample["answer"].get("explanation", "")
            }
        else:
            # 如果没有结构化的answer字段，尝试构造一个
            answer_type = "choice" if processed["is_choice"] else "text"
            processed["answer"] = {
                "type": answer_type,
                "value": sample.get("response", ""),
                "explanation": ""
            }
        
        # 处理多模态文件
        if "files" in sample and isinstance(sample["files"], list):
            processed_files = []
            for file_info in sample["files"]:
                if isinstance(file_info, dict) and "path" in file_info:
                    # 处理文件路径
                    file_path = file_info["path"]
                    if self.media_dir:
                        absolute_path = self.media_dir / file_path
                    else:
                        # 如果未提供media_dir，则假设路径已经是相对于数据集文件的
                        dataset_dir = self.dataset_path.parent
                        absolute_path = dataset_dir / file_path
                    
                    # 检查文件是否存在
                    if os.path.exists(absolute_path):
                        file_type = file_info.get("type", self._guess_file_type(file_path))
                        processed_files.append({
                            "path": str(absolute_path),
                            "type": file_type,
                            "original_path": file_path,
                            "description": file_info.get("description", "")
                        })
                    else:
                        logger.warning(f"文件不存在: {absolute_path}")
            
            if processed_files:
                processed["files"] = processed_files
                processed["is_multimodal"] = True
        
        # 处理元数据
        if "meta" in sample and isinstance(sample["meta"], dict):
            processed["meta"] = sample["meta"]
        else:
            # 构造基本元数据
            processed["meta"] = {
                "task_type": self._infer_task_type(processed),
                "category": sample.get("category", ""),
                "difficulty": sample.get("difficulty", "")
            }
        
        # 处理评估信息
        if "evaluation" in sample and isinstance(sample["evaluation"], dict):
            processed["evaluation"] = sample["evaluation"]
        
        return processed
    
    def _infer_task_type(self, processed_sample: Dict[str, Any]) -> str:
        """
        根据样本特征推断任务类型
        
        Args:
            processed_sample: 已处理的样本数据
            
        Returns:
            任务类型字符串
        """
        # 如果元数据中已有任务类型，则直接使用
        if "meta" in processed_sample and "task_type" in processed_sample["meta"]:
            return processed_sample["meta"]["task_type"]
        
        # 根据样本特征推断
        if processed_sample["is_multimodal"]:
            # 检查多模态文件类型
            if "files" in processed_sample:
                file_types = [f["type"] for f in processed_sample["files"]]
                if "image" in file_types:
                    return "vision"
                elif "audio" in file_types:
                    return "audio"
                elif "video" in file_types:
                    return "video"
                else:
                    return "multi"
        
        if processed_sample["is_choice"]:
            return "choice"
        
        # 检查答案类型
        if "answer" in processed_sample:
            answer_type = processed_sample["answer"].get("type", "")
            if answer_type == "code":
                return "code"
            elif answer_type == "step_by_step":
                return "math"
        
        # 默认为普通问答
        return "qa"
    
    def _guess_file_type(self, file_path: str) -> str:
        """
        根据文件扩展名猜测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型字符串: "image", "audio", "video", 或 "unknown"
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # 图片格式
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return "image"
        # 音频格式
        elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']:
            return "audio"
        # 视频格式
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return "video"
        # 其他格式
        else:
            return "unknown"
    
    def get_format_name(self) -> str:
        """返回数据集格式名称"""
        return "xpert-format"
    
    def get_task_types(self) -> List[str]:
        """
        获取数据集中包含的所有任务类型
        
        Returns:
            任务类型列表
        """
        task_types = set()
        for sample in self.data:
            if "meta" in sample and "task_type" in sample["meta"]:
                task_types.add(sample["meta"]["task_type"])
        return list(task_types)
    
    def filter_by_task_type(self, task_type: str) -> List[Dict[str, Any]]:
        """
        按任务类型筛选样本
        
        Args:
            task_type: 要筛选的任务类型
            
        Returns:
            符合条件的样本列表
        """
        return [sample for sample in self.data 
                if "meta" in sample and sample["meta"].get("task_type") == task_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        Returns:
            包含统计信息的字典
        """
        stats = {
            "total_samples": len(self.data),
            "multimodal_samples": sum(1 for s in self.data if s.get("is_multimodal", False)),
            "multi_turn_samples": sum(1 for s in self.data if s.get("is_multi_turn", False)),
            "choice_samples": sum(1 for s in self.data if s.get("is_choice", False)),
            "task_types": {}
        }
        
        # 按任务类型统计
        for sample in self.data:
            task_type = sample.get("meta", {}).get("task_type", "unknown")
            if task_type not in stats["task_types"]:
                stats["task_types"][task_type] = 0
            stats["task_types"][task_type] += 1
        
        return stats 