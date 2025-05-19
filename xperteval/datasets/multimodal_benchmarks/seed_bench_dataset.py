# coding: utf-8
"""
SEED-Bench 数据集解析器

负责解析和转换SEED-Bench格式的数据集到XpertFormat格式。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set

from ..base_dataset import BaseDataset
from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

class SEEDBenchDataset(BaseDataset):
    """
    SEED-Bench数据集解析器
    
    SEED-Bench是一个综合性的多模态评测数据集，包含图像和视频理解任务，
    测试模型对视觉内容的多方面理解能力。
    
    原始格式:
    JSONL文件，每个样本可能包含多个图像或视频
    {
        "sample_id": "unique_id",
        "image_paths": ["image1.jpg", "image2.jpg"],  // 可能包含多个图像
        "video_path": "video.mp4",  // 可选的视频路径
        "question": "关于图像或视频的问题",
        "choices": ["选项A", "选项B", "选项C", "选项D"],
        "answer": 0,  // 正确选项的索引
        "task_type": "图像理解"
    }
    
    转换后的XpertFormat:
    {
        "id": "seed_bench_<sample_id>",
        "query": "关于图像或视频的问题",
        "files": [
            {"path": "image1.jpg", "type": "image"},
            {"path": "image2.jpg", "type": "image"},
            {"path": "video.mp4", "type": "video"}
        ],
        "choices": [
            {"id": "A", "content": "选项A"},
            {"id": "B", "content": "选项B"},
            {"id": "C", "content": "选项C"},
            {"id": "D", "content": "选项D"}
        ],
        "answer": {
            "type": "choice",
            "value": "A",  // 索引转换为选项ID
            "explanation": null
        },
        "meta": {
            "task_type": "vision",  // 或 "video" 如果包含视频
            "category": "图像理解",
            "source": "SEED-Bench"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化SEED-Bench数据集
        
        Args:
            dataset_path: 数据集文件或目录路径
            **kwargs: 额外参数
                - media_dir: 媒体文件目录，默认为数据集文件所在目录
                - split: 数据集分割(dev/test)，默认为"test"
                - verify_media: 是否验证媒体文件存在，默认为True
        """
        super().__init__(dataset_path, **kwargs)
        
        self.media_dir = kwargs.get('media_dir', None)
        if not self.media_dir:
            # 默认使用数据集文件所在目录
            self.media_dir = str(Path(dataset_path).parent / "media")
        
        self.split = kwargs.get('split', 'test')
        self.verify_media = kwargs.get('verify_media', True)
        
        # 加载数据
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """
        加载并解析SEED-Bench数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSONL/JSON文件
        if dataset_path.is_dir():
            # 尝试按照命名规则查找文件
            file_patterns = [
                f"seed_bench_{self.split}.jsonl",
                f"{self.split}.jsonl",
                "seed_bench.jsonl",
                f"seed_bench_{self.split}.json",
                f"{self.split}.json",
                "seed_bench.json"
            ]
            
            found_file = False
            for pattern in file_patterns:
                file_path = dataset_path / pattern
                if file_path.exists():
                    data = self._parse_file(file_path)
                    found_file = True
                    break
            
            if not found_file:
                logger.warning(f"在目录 {dataset_path} 中找不到匹配的SEED-Bench数据文件")
        
        # 如果是单个文件
        elif dataset_path.exists():
            data = self._parse_file(dataset_path)
        
        else:
            logger.error(f"数据集路径不存在: {dataset_path}")
            raise FileNotFoundError(f"数据集路径不存在: {dataset_path}")
        
        logger.info(f"成功加载 SEED-Bench 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析SEED-Bench数据文件
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            解析后的数据列表
        """
        data = []
        
        try:
            # 根据文件扩展名选择解析方法
            if file_path.suffix.lower() == '.jsonl':
                # JSONL格式，逐行解析
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            sample = json.loads(line.strip())
                            xpert_sample = self._convert_sample(sample)
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
                        for sample in json_data:
                            xpert_sample = self._convert_sample(sample)
                            if xpert_sample:
                                data.append(xpert_sample)
                    else:
                        # 可能是字典，包含数据列表
                        for key, items in json_data.items():
                            if isinstance(items, list):
                                for sample in items:
                                    xpert_sample = self._convert_sample(sample)
                                    if xpert_sample:
                                        data.append(xpert_sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将SEED-Bench样本转换为XpertFormat格式
        
        Args:
            sample: SEED-Bench样本
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            # 提取必要字段
            sample_id = sample.get('sample_id', sample.get('id', f"unknown_{len(self.data)}"))
            question = sample.get('question')
            choices = sample.get('choices', sample.get('options'))
            answer_idx = sample.get('answer')
            task_type = sample.get('task_type', '图像理解')
            
            # 验证必要字段
            if not question or choices is None or answer_idx is None:
                logger.warning(f"样本 {sample_id} 缺少问题、选项或答案")
                return None
            
            # 处理媒体文件
            files = []
            
            # 处理图像路径
            image_paths = sample.get('image_paths', [])
            if isinstance(image_paths, str):
                image_paths = [image_paths]  # 转换单个路径为列表
            
            for image_path in image_paths:
                if image_path:
                    image_full_path = self._resolve_media_path(image_path, "image")
                    files.append({"path": image_full_path, "type": "image"})
            
            # 处理视频路径
            video_path = sample.get('video_path')
            if video_path:
                video_full_path = self._resolve_media_path(video_path, "video")
                files.append({"path": video_full_path, "type": "video"})
            
            # 如果没有任何媒体文件
            if not files:
                logger.warning(f"样本 {sample_id} 没有有效的媒体文件")
                return None
            
            # 处理选项
            choice_objects = []
            if isinstance(choices, list):
                for i, choice in enumerate(choices):
                    choice_id = chr(65 + i)  # A, B, C, D...
                    choice_objects.append({
                        "id": choice_id,
                        "content": choice
                    })
            
            # 将索引转换为选项ID
            answer_value = chr(65 + answer_idx) if isinstance(answer_idx, int) and 0 <= answer_idx < len(choices) else str(answer_idx)
            
            # 确定任务类型
            meta_task_type = "video" if any(f["type"] == "video" for f in files) else "vision"
            
            # 构建XpertFormat样本
            xpert_sample = {
                "id": f"seed_bench_{sample_id}",
                "query": question,
                "files": files,
                "choices": choice_objects,
                "answer": {
                    "type": "choice",
                    "value": answer_value,
                    "explanation": None
                },
                "meta": {
                    "task_type": meta_task_type,
                    "category": task_type,
                    "source": "SEED-Bench"
                }
            }
            
            return xpert_sample
            
        except Exception as e:
            logger.warning(f"转换样本失败: {e}")
            return None
    
    def _resolve_media_path(self, media_path: str, media_type: str) -> str:
        """
        解析媒体文件路径，返回完整路径
        
        Args:
            media_path: 原始媒体文件路径
            media_type: 媒体类型 ("image" 或 "video")
            
        Returns:
            完整的媒体文件路径
        """
        # 如果是绝对路径或URL，直接返回
        if media_path.startswith(('http://', 'https://', '/')):
            return media_path
        
        # 否则，拼接media_dir和media_path
        media_full_path = os.path.join(self.media_dir, media_path)
        
        # 检查文件是否存在
        if self.verify_media and not os.path.exists(media_full_path):
            logger.warning(f"{media_type.capitalize()}文件不存在: {media_full_path}")
        
        return media_full_path
    
    def verify_media_files(self) -> Dict[str, Tuple[int, int]]:
        """
        验证所有媒体文件是否存在
        
        Returns:
            字典，包含各类型媒体文件的验证结果 {"image": (valid_count, total_count), "video": (valid_count, total_count)}
        """
        if not self.data:
            return {"image": (0, 0), "video": (0, 0)}
        
        # 使用集合去重，因为多个样本可能使用同一个媒体文件
        image_paths: Set[str] = set()
        video_paths: Set[str] = set()
        
        for sample in self.data:
            files = sample.get('files', [])
            for file_info in files:
                path = file_info.get('path', '')
                if file_info.get('type') == 'image':
                    image_paths.add(path)
                elif file_info.get('type') == 'video':
                    video_paths.add(path)
        
        # 验证图像文件
        image_total = len(image_paths)
        image_valid = sum(1 for path in image_paths if os.path.exists(path))
        
        # 验证视频文件
        video_total = len(video_paths)
        video_valid = sum(1 for path in video_paths if os.path.exists(path))
        
        logger.info(f"图像验证结果: {image_valid}/{image_total} 有效")
        logger.info(f"视频验证结果: {video_valid}/{video_total} 有效")
        
        return {
            "image": (image_valid, image_total),
            "video": (video_valid, video_total)
        }
    
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
        
        # 统计任务类型和媒体类型分布
        categories = {}
        media_types = {"image_only": 0, "video_only": 0, "image_and_video": 0}
        
        for sample in self.data:
            meta = sample.get("meta", {})
            category = meta.get("category", "未知")
            categories[category] = categories.get(category, 0) + 1
            
            # 统计媒体类型
            has_image = False
            has_video = False
            for file_info in sample.get("files", []):
                if file_info.get("type") == "image":
                    has_image = True
                elif file_info.get("type") == "video":
                    has_video = True
            
            if has_image and has_video:
                media_types["image_and_video"] += 1
            elif has_image:
                media_types["image_only"] += 1
            elif has_video:
                media_types["video_only"] += 1
        
        # 验证媒体文件
        media_stats = self.verify_media_files()
        
        return {
            "sample_count": len(self.data),
            "categories": categories,
            "media_types": media_types,
            "media_stats": {
                "image": {
                    "valid": media_stats["image"][0],
                    "total": media_stats["image"][1],
                    "valid_ratio": media_stats["image"][0] / media_stats["image"][1] if media_stats["image"][1] > 0 else 0
                },
                "video": {
                    "valid": media_stats["video"][0],
                    "total": media_stats["video"][1],
                    "valid_ratio": media_stats["video"][0] / media_stats["video"][1] if media_stats["video"][1] > 0 else 0
                }
            }
        } 