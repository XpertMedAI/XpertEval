# coding: utf-8
"""
数据集处理与加载 - ms-swift 格式数据集解析器
解析 ms-swift 标准数据集格式

MS-SWIFT格式是一种包含结构化的多模态对话数据的格式，通常存储为JSONL文件，
每一行是一个独立的JSON对象，包含单轮或多轮对话样本。
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

class MsSwiftDataset(BaseDataset):
    """
    MS-SWIFT格式数据集解析器
    
    MS-SWIFT是一种广泛使用的多模态对话数据集格式，支持图像、音频等多模态内容引用。
    该类负责将MS-SWIFT格式的数据加载为统一的内部表示，以便于模型评测使用。
    """
    
    def __init__(self, dataset_path: str, media_dir: Optional[str] = None, **kwargs):
        """
        初始化MS-SWIFT数据集
        
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
        加载并解析MS-SWIFT格式的数据集
        
        MS-SWIFT格式中，每行是一个JSON对象，可能包含以下字段:
        - id: 样本唯一标识符
        - query: 当前轮次的用户问题
        - response: 模型回复
        - history: (可选) 历史对话轮次
        - files: (可选) 引用的多模态文件列表
        """
        logger.info(f"开始加载MS-SWIFT数据集: {self.dataset_path}")
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    try:
                        # 解析JSON行
                        sample = json.loads(line.strip())
                        
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
    
    def _process_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个数据样本，将其转换为标准格式
        
        Args:
            sample: 原始数据样本字典
            
        Returns:
            处理后的样本字典，如果样本无效则返回None
        """
        # 检查必需字段
        if "query" not in sample:
            logger.warning(f"样本缺少必需字段'query': {sample.get('id', '未知ID')}")
            return None
        
        # 创建标准化样本
        processed = {
            "id": sample.get("id", f"sample_{len(self.data)}"),
            "query": sample["query"],
            "response": sample.get("response", ""),  # response可能在某些测试集中不存在
            "is_multimodal": False,  # 默认为非多模态，后续检查是否包含文件
        }
        
        # 处理历史对话
        if "history" in sample and isinstance(sample["history"], list):
            processed["history"] = sample["history"]
            processed["is_multi_turn"] = True
        else:
            processed["history"] = []
            processed["is_multi_turn"] = False
        
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
                        })
                    else:
                        logger.warning(f"文件不存在: {absolute_path}")
            
            if processed_files:
                processed["files"] = processed_files
                processed["is_multimodal"] = True
        
        # 处理额外的元数据字段(按需保留)
        for extra_key in ["meta", "category", "task_type", "difficulty"]:
            if extra_key in sample:
                processed[extra_key] = sample[extra_key]
        
        return processed
    
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
        return "ms-swift" 