# coding: utf-8
"""
LLaVA-Bench 数据集解析器

负责解析和转换LLaVA-Bench格式的数据集到XpertFormat格式。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ..base_dataset import BaseDataset
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

class LLaVABenchDataset(BaseDataset):
    """
    LLaVA-Bench数据集解析器
    
    LLaVA-Bench是一个对话式视觉-语言评测数据集，用于评估模型在多轮对话中理解和回答
    关于图像的问题的能力。
    
    原始格式:
    JSON文件，每个样本包含图像路径和对话历史
    {
        "id": "样本ID",
        "image": "image_path.jpg",
        "conversations": [
            {"role": "human", "content": "问题文本"},
            {"role": "assistant", "content": "参考答案"}
        ],
        "category": "图像描述"
    }
    
    转换后的XpertFormat:
    {
        "id": "llava_bench_<id>",
        "query": "问题文本",
        "response": "参考答案",
        "history": [
            {"role": "human", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"}
        ],
        "files": [
            {"path": "image_path.jpg", "type": "image"}
        ],
        "answer": {
            "type": "text",
            "value": "参考答案",
            "explanation": null
        },
        "meta": {
            "task_type": "vision",
            "category": "图像描述",
            "source": "LLaVA-Bench"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化LLaVA-Bench数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - image_dir: 图像文件目录，默认为数据集文件所在目录
                - split: 数据集分割(dev/test)，默认为"test"
        """
        super().__init__(dataset_path, **kwargs)
        
        self.image_dir = kwargs.get('image_dir', None)
        if not self.image_dir:
            # 默认使用数据集文件所在目录
            self.image_dir = str(Path(dataset_path).parent / "images")
        
        self.split = kwargs.get('split', 'test')
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析LLaVA-Bench数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSON文件
        if dataset_path.is_dir():
            # 尝试按照命名规则查找文件
            file_patterns = [
                f"llava_bench_{self.split}.json",
                f"{self.split}.json",
                "llava_bench.json",
                "conversations.json"
            ]
            
            found_file = False
            for pattern in file_patterns:
                file_path = dataset_path / pattern
                if file_path.exists():
                    data = self._parse_json_file(file_path)
                    found_file = True
                    break
            
            if not found_file:
                logger.warning(f"在目录 {dataset_path} 中找不到匹配的LLaVA-Bench数据文件")
        
        # 如果是单个文件
        elif dataset_path.exists() and dataset_path.suffix.lower() == '.json':
            data = self._parse_json_file(dataset_path)
        
        else:
            logger.error(f"数据集路径不存在或不是有效的JSON文件: {dataset_path}")
            raise FileNotFoundError(f"数据集路径不存在或不是有效的JSON文件: {dataset_path}")
        
        logger.info(f"成功加载 LLaVA-Bench 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析LLaVA-Bench JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                # 判断是否为列表
                if isinstance(json_data, list):
                    for sample in json_data:
                        xpert_samples = self._convert_sample(sample)
                        data.extend(xpert_samples)
                else:
                    # 可能是字典，包含数据列表
                    for key, items in json_data.items():
                        if isinstance(items, list):
                            for sample in items:
                                xpert_samples = self._convert_sample(sample)
                                data.extend(xpert_samples)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将LLaVA-Bench样本转换为XpertFormat格式
        由于LLaVA-Bench可能包含多轮对话，每轮对话生成一个样本
        
        Args:
            sample: LLaVA-Bench样本
            
        Returns:
            转换后的XpertFormat样本列表
        """
        xpert_samples = []
        
        try:
            # 提取必要字段
            sample_id = sample.get('id', f"unknown_{len(self.data)}")
            image_path = sample.get('image')
            conversations = sample.get('conversations', [])
            category = sample.get('category', '未知')
            
            # 验证必要字段
            if not image_path or not conversations:
                logger.warning(f"样本 {sample_id} 缺少图像路径或对话内容")
                return []
            
            # 处理图像路径
            image_full_path = self._resolve_image_path(image_path)
            
            # 处理对话
            # 如果是多轮对话，为每一轮创建一个样本
            history = []
            for i in range(0, len(conversations), 2):
                if i + 1 >= len(conversations):
                    # 如果没有回复，跳过这轮
                    continue
                
                human_msg = conversations[i]
                assistant_msg = conversations[i + 1]
                
                # 验证角色
                if human_msg.get('role') != 'human' or assistant_msg.get('role') != 'assistant':
                    logger.warning(f"样本 {sample_id} 对话角色不匹配: {human_msg.get('role')}, {assistant_msg.get('role')}")
                    continue
                
                query = human_msg.get('content', '')
                response = assistant_msg.get('content', '')
                
                # 创建XpertFormat样本
                xpert_sample = {
                    "id": f"llava_bench_{sample_id}_{i//2}",
                    "query": query,
                    "response": response,
                    "files": [
                        {"path": image_full_path, "type": "image"}
                    ],
                    "answer": {
                        "type": "text",
                        "value": response,
                        "explanation": None
                    },
                    "meta": {
                        "task_type": "vision",
                        "category": category,
                        "source": "LLaVA-Bench",
                        "turn_idx": i // 2
                    }
                }
                
                # 添加历史对话（如果有）
                if history:
                    xpert_sample["history"] = history.copy()
                
                xpert_samples.append(xpert_sample)
                
                # 更新历史对话
                history.append({"role": "human", "content": query})
                history.append({"role": "assistant", "content": response})
            
            return xpert_samples
            
        except Exception as e:
            logger.warning(f"转换样本失败: {e}")
            return []
    
    def _resolve_image_path(self, image_path: str) -> str:
        """
        解析图像路径，返回完整路径
        
        Args:
            image_path: 原始图像路径
            
        Returns:
            完整的图像路径
        """
        # 如果是绝对路径或URL，直接返回
        if image_path.startswith(('http://', 'https://', '/')):
            return image_path
        
        # 否则，拼接image_dir和image_path
        image_full_path = os.path.join(self.image_dir, image_path)
        
        # 检查文件是否存在
        if not os.path.exists(image_full_path):
            logger.warning(f"图像文件不存在: {image_full_path}")
        
        return image_full_path
    
    def verify_images(self) -> Tuple[int, int]:
        """
        验证所有图像文件是否存在
        
        Returns:
            元组 (有效图像数, 总图像数)
        """
        if not self.data:
            return (0, 0)
        
        # 使用集合去重，因为多个样本可能使用同一张图片
        image_paths = set()
        for sample in self.data:
            files = sample.get('files', [])
            for file_info in files:
                if file_info.get('type') == 'image':
                    image_paths.add(file_info.get('path', ''))
        
        total_count = len(image_paths)
        valid_count = sum(1 for path in image_paths if os.path.exists(path))
        
        logger.info(f"图像验证结果: {valid_count}/{total_count} 有效")
        return (valid_count, total_count)
    
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
        
        # 统计类别分布和对话轮次
        categories = {}
        turn_counts = {}
        
        for sample in self.data:
            meta = sample.get("meta", {})
            category = meta.get("category", "未知")
            turn_idx = meta.get("turn_idx", 0)
            
            categories[category] = categories.get(category, 0) + 1
            turn_counts[turn_idx] = turn_counts.get(turn_idx, 0) + 1
        
        # 计算多轮对话样本比例
        multi_turn_count = sum(count for turn, count in turn_counts.items() if turn > 0)
        multi_turn_ratio = multi_turn_count / len(self.data) if self.data else 0
        
        # 验证图像
        valid_images, total_images = self.verify_images()
        
        return {
            "sample_count": len(self.data),
            "task_type": "vision",
            "categories": categories,
            "turn_counts": turn_counts,
            "multi_turn_ratio": multi_turn_ratio,
            "image_stats": {
                "valid": valid_images,
                "total": total_images,
                "valid_ratio": valid_images / total_images if total_images > 0 else 0
            }
        } 