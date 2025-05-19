# coding: utf-8
"""
MM-Vet 数据集解析器

负责解析和转换MM-Vet格式的数据集到XpertFormat格式。
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

class MMVetDataset(BaseDataset):
    """
    MM-Vet数据集解析器
    
    MM-Vet是一个专注于复杂视觉推理任务的多模态评测数据集，
    包括图表理解、视觉常识推理等高难度任务。
    
    原始格式:
    JSON文件，每个样本包含问题、图像路径和答案
    {
        "id": "样本ID",
        "image": "image_path.jpg",
        "question": "复杂的多模态任务描述",
        "answer": "参考答案",
        "category": "视觉推理",
        "difficulty": "专家级"
    }
    
    转换后的XpertFormat:
    {
        "id": "mm_vet_<id>",
        "query": "复杂的多模态任务描述",
        "response": "参考答案",
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
            "category": "视觉推理",
            "difficulty": "专家级",
            "source": "MM-Vet"
        }
    }
    """
    
    def __init__(self, dataset_path: str, **kwargs):
        """
        初始化MM-Vet数据集
        
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
        加载并解析MM-Vet数据集
        
        Returns:
            解析后的数据列表
        """
        dataset_path = Path(self.dataset_path)
        data = []
        
        # 如果是目录，则查找相关JSON文件
        if dataset_path.is_dir():
            # 尝试按照命名规则查找文件
            file_patterns = [
                f"mm_vet_{self.split}.json",
                f"{self.split}.json",
                "mm_vet.json",
                "questions.json"
            ]
            
            found_file = False
            for pattern in file_patterns:
                file_path = dataset_path / pattern
                if file_path.exists():
                    data = self._parse_json_file(file_path)
                    found_file = True
                    break
            
            if not found_file:
                logger.warning(f"在目录 {dataset_path} 中找不到匹配的MM-Vet数据文件")
        
        # 如果是单个文件
        elif dataset_path.exists() and dataset_path.suffix.lower() == '.json':
            data = self._parse_json_file(dataset_path)
        
        else:
            logger.error(f"数据集路径不存在或不是有效的JSON文件: {dataset_path}")
            raise FileNotFoundError(f"数据集路径不存在或不是有效的JSON文件: {dataset_path}")
        
        logger.info(f"成功加载 MM-Vet 数据集，共 {len(data)} 个样本")
        return data
    
    def _parse_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析MM-Vet JSON文件
        
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
                        xpert_sample = self._convert_sample(sample)
                        if xpert_sample:
                            data.append(xpert_sample)
                else:
                    # 可能是字典，包含数据列表或直接是样本集合
                    if "data" in json_data and isinstance(json_data["data"], list):
                        for sample in json_data["data"]:
                            xpert_sample = self._convert_sample(sample)
                            if xpert_sample:
                                data.append(xpert_sample)
                    else:
                        # 尝试将整个字典作为样本集合处理
                        for key, sample in json_data.items():
                            if isinstance(sample, dict):
                                # 如果样本没有ID，使用键作为ID
                                if "id" not in sample:
                                    sample["id"] = key
                                xpert_sample = self._convert_sample(sample)
                                if xpert_sample:
                                    data.append(xpert_sample)
            
            logger.info(f"从 {file_path} 加载了 {len(data)} 个样本")
            return data
            
        except Exception as e:
            logger.error(f"解析JSON文件 {file_path} 失败: {e}")
            return []
    
    def _convert_sample(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将MM-Vet样本转换为XpertFormat格式
        
        Args:
            sample: MM-Vet样本
            
        Returns:
            转换后的XpertFormat样本，如果转换失败则返回None
        """
        try:
            # 提取必要字段
            sample_id = sample.get('id', f"unknown_{len(self.data)}")
            question = sample.get('question')
            answer = sample.get('answer', sample.get('reference', ''))
            image_path = sample.get('image', sample.get('image_path', ''))
            category = sample.get('category', sample.get('type', '视觉推理'))
            difficulty = sample.get('difficulty', '专家级')
            
            # 验证必要字段
            if not question or not image_path:
                logger.warning(f"样本 {sample_id} 缺少问题或图像路径")
                return None
            
            # 处理图像路径
            image_full_path = self._resolve_image_path(image_path)
            
            # 处理选项（如果有）
            choices = sample.get('choices', sample.get('options'))
            choice_objects = []
            answer_type = "text"
            
            if choices:
                answer_type = "choice"
                # 如果选项是列表
                if isinstance(choices, list):
                    for i, choice in enumerate(choices):
                        choice_id = chr(65 + i)  # A, B, C, D...
                        choice_objects.append({
                            "id": choice_id,
                            "content": choice
                        })
                # 如果选项是字典
                elif isinstance(choices, dict):
                    for choice_id, content in choices.items():
                        choice_objects.append({
                            "id": choice_id,
                            "content": content
                        })
            
            # 构建XpertFormat样本
            xpert_sample = {
                "id": f"mm_vet_{sample_id}",
                "query": question,
                "response": answer,
                "files": [
                    {"path": image_full_path, "type": "image"}
                ],
                "meta": {
                    "task_type": "vision",
                    "category": category,
                    "difficulty": difficulty,
                    "source": "MM-Vet"
                }
            }
            
            # 添加选项和答案
            if choice_objects:
                xpert_sample["choices"] = choice_objects
                xpert_sample["answer"] = {
                    "type": "choice",
                    "value": answer,
                    "explanation": None
                }
            else:
                # 如果没有选项，则为开放式问题
                xpert_sample["answer"] = {
                    "type": "text",
                    "value": answer,
                    "explanation": None
                }
            
            return xpert_sample
            
        except Exception as e:
            logger.warning(f"转换样本失败: {e}")
            return None
    
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
        
        # 统计类别分布和难度分布
        categories = {}
        difficulties = {}
        answer_types = {"choice": 0, "text": 0}
        
        for sample in self.data:
            meta = sample.get("meta", {})
            category = meta.get("category", "未知")
            difficulty = meta.get("difficulty", "未知")
            
            categories[category] = categories.get(category, 0) + 1
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
            
            # 统计答案类型
            answer = sample.get("answer", {})
            answer_type = answer.get("type", "text")
            answer_types[answer_type] = answer_types.get(answer_type, 0) + 1
        
        # 验证图像
        valid_images, total_images = self.verify_images()
        
        return {
            "sample_count": len(self.data),
            "task_type": "vision",
            "categories": categories,
            "difficulties": difficulties,
            "answer_types": answer_types,
            "image_stats": {
                "valid": valid_images,
                "total": total_images,
                "valid_ratio": valid_images / total_images if total_images > 0 else 0
            }
        } 