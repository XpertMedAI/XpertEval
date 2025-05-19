# coding: utf-8
"""
数据集处理与加载 - 注册数据集
管理和注册已集成的数据集
"""

import os
from typing import Dict, Any, List, Union, Optional, Callable, Type
from pathlib import Path
import glob

from ..utils import get_logger
from .base_dataset import BaseDataset
from .xpert_format import XpertFormatDataset
from .common_benchmarks import (
    MMLUDataset,
    CMMLUDataset,
    GSM8KDataset,
    MATHDataset,
    HumanEvalDataset,
    CEvalDataset
)
from .multimodal_benchmarks import (
    MMBenchDataset,
    LLaVABenchDataset,
    SEEDBenchDataset,
    MMVetDataset
)

# 配置日志
logger = get_logger(__name__)

# 内置数据集搜索目录
DEFAULT_DATASETS_DIR = Path(__file__).parent.parent.parent / "data" / "integrated"

# 数据集类型注册表：映射数据集类型名称到相应的数据集类
DATASET_REGISTRY = {
    "xpert-format": XpertFormatDataset,
    
    # 通用评测数据集
    "mmlu": MMLUDataset,
    "cmmlu": CMMLUDataset,
    "gsm8k": GSM8KDataset,
    "math": MATHDataset,
    "human_eval": HumanEvalDataset,
    "ceval": CEvalDataset,
    
    # 多模态评测数据集
    "mmbench": MMBenchDataset,
    "llava_bench": LLaVABenchDataset,
    "seed_bench": SEEDBenchDataset,
    "mm_vet": MMVetDataset
}

# 已集成的数据集目录注册表
INTEGRATED_DATASETS = {}  # 将在scan_integrated_datasets函数中填充

# 数据集类型别名，允许使用不同的名称引用同一数据集类型
DATASET_TYPE_ALIASES = {
    "humaneval": "human_eval",
    "mmvet": "mm_vet",
    "llava-bench": "llava_bench",
    "llava": "llava_bench",
    "seed-bench": "seed_bench",
    "seedbench": "seed_bench"
}


def register_dataset_type(name: str, dataset_class: Type[BaseDataset]) -> None:
    """
    注册新的数据集类型
    
    Args:
        name: 数据集类型名称
        dataset_class: 数据集类，必须是BaseDataset的子类
    """
    if not issubclass(dataset_class, BaseDataset):
        raise TypeError(f"数据集类 {dataset_class.__name__} 必须是BaseDataset的子类")
    
    if name in DATASET_REGISTRY:
        logger.warning(f"数据集类型 '{name}' 已存在，将被覆盖")
    
    DATASET_REGISTRY[name] = dataset_class
    logger.info(f"数据集类型 '{name}' 已注册")


def get_dataset_class(dataset_type: str) -> Type[BaseDataset]:
    """
    获取指定类型的数据集类
    
    Args:
        dataset_type: 数据集类型名称
    
    Returns:
        对应的数据集类
    
    Raises:
        ValueError: 如果指定类型不存在
    """
    if dataset_type not in DATASET_REGISTRY:
        raise ValueError(f"未知的数据集类型: {dataset_type}，已知类型: {list(DATASET_REGISTRY.keys())}")
    
    return DATASET_REGISTRY[dataset_type]


def scan_integrated_datasets(base_dir: Optional[Union[str, Path]] = None) -> Dict[str, Dict[str, Any]]:
    """
    扫描集成数据集目录，查找可用的数据集
    
    Args:
        base_dir: 数据集基础目录，如未指定则使用默认目录
    
    Returns:
        数据集信息字典，格式为 {数据集ID: {名称, 路径, 类型, 描述}}
    """
    global INTEGRATED_DATASETS
    
    # 使用提供的目录或默认目录
    base_dir = Path(base_dir) if base_dir else DEFAULT_DATASETS_DIR
    
    # 确保目录存在
    if not os.path.exists(base_dir):
        logger.warning(f"数据集目录不存在: {base_dir}")
        return {}
    
    logger.info(f"扫描集成数据集目录: {base_dir}")
    datasets = {}
    
    # 查找所有子目录，每个子目录可能是一个数据集
    for dataset_dir in Path(base_dir).glob("*"):
        if not dataset_dir.is_dir():
            continue
        
        dataset_id = dataset_dir.name
        description = "无描述"
        dataset_type = "xpert-format"  # 默认类型
        dataset_file = None
        media_dir = None
        splits = []
        
        # 查找README.md文件以获取描述
        readme_path = dataset_dir / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        description = first_line.lstrip('# ')
                    
                    # 尝试从README中读取数据集类型
                    for line in f:
                        if line.lower().startswith("type:") or line.lower().startswith("格式:"):
                            dataset_type = line.split(":", 1)[1].strip()
                            break
            except Exception as e:
                logger.warning(f"读取数据集 {dataset_id} 的README.md时出错: {e}")
        
        # 查找配置文件
        config_path = dataset_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                    if "type" in config:
                        dataset_type = config["type"]
                    if "description" in config:
                        description = config["description"]
                    if "splits" in config:
                        splits = config["splits"]
            except Exception as e:
                logger.warning(f"读取数据集 {dataset_id} 的配置文件时出错: {e}")
        
        # 检查是否有媒体目录
        possible_media_dirs = ["media", "images", "videos", "audios"]
        for media_dir_name in possible_media_dirs:
            media_dir_path = dataset_dir / media_dir_name
            if media_dir_path.exists() and media_dir_path.is_dir():
                media_dir = str(media_dir_path)
                break
        
        # 查找主数据集文件
        # 优先级：dataset.jsonl > dataset.json > 任何.jsonl文件 > 任何.json文件
        dataset_files = []
        
        # 首先检查是否有分割数据集文件
        split_files = {}
        for split_name in ["train", "dev", "test", "validation"]:
            for ext in [".jsonl", ".json"]:
                split_file = dataset_dir / f"{split_name}{ext}"
                if split_file.exists():
                    split_files[split_name] = str(split_file)
                    if split_name not in splits:
                        splits.append(split_name)
        
        # 然后查找主数据集文件
        if (dataset_dir / "dataset.jsonl").exists():
            dataset_file = dataset_dir / "dataset.jsonl"
        elif (dataset_dir / "dataset.json").exists():
            dataset_file = dataset_dir / "dataset.json"
        else:
            # 查找任何.jsonl或.json文件
            jsonl_files = list(dataset_dir.glob("*.jsonl"))
            json_files = list(dataset_dir.glob("*.json"))
            
            if jsonl_files:
                dataset_file = jsonl_files[0]
            elif json_files:
                dataset_file = json_files[0]
        
        # 如果找到有效的数据集文件
        if dataset_file or split_files:
            # 规范化数据集类型
            if dataset_type.lower() in DATASET_TYPE_ALIASES:
                dataset_type = DATASET_TYPE_ALIASES[dataset_type.lower()]
            
            datasets[dataset_id] = {
                "id": dataset_id,
                "name": dataset_id.replace('_', ' ').title(),
                "path": str(dataset_file) if dataset_file else split_files.get("test", split_files.get("dev", list(split_files.values())[0])),
                "type": dataset_type,
                "description": description,
                "media_dir": media_dir,
                "splits": splits,
                "split_files": split_files if split_files else None
            }
            
            if dataset_file:
                logger.info(f"发现数据集 '{dataset_id}', 文件: {dataset_file.name}")
            else:
                logger.info(f"发现数据集 '{dataset_id}', 分割文件: {', '.join(split_files.keys())}")
    
    INTEGRATED_DATASETS = datasets
    logger.info(f"共发现 {len(datasets)} 个集成数据集")
    return datasets


def get_dataset(
    dataset_id: Optional[str] = None,
    dataset_path: Optional[str] = None,
    dataset_type: str = "xpert-format",
    split: Optional[str] = None,
    **kwargs
) -> BaseDataset:
    """
    获取数据集实例
    
    可以通过两种方式指定数据集:
    1. 通过dataset_id指定已集成的数据集
    2. 通过dataset_path和dataset_type直接指定数据集文件和类型
    
    Args:
        dataset_id: 已集成数据集的ID，如果指定，将忽略dataset_path和dataset_type
        dataset_path: 数据集文件路径
        dataset_type: 数据集类型，默认为"xpert-format"
        split: 数据集分割，如"train", "dev", "test"，默认为None（使用主数据集文件）
        **kwargs: 传递给数据集构造函数的其他参数
    
    Returns:
        数据集实例
    
    Raises:
        ValueError: 如果参数无效或数据集不存在
    """
    # 如果INTEGRATED_DATASETS为空，先扫描一次
    if not INTEGRATED_DATASETS:
        scan_integrated_datasets()
    
    # 处理已集成数据集
    if dataset_id:
        if dataset_id not in INTEGRATED_DATASETS:
            raise ValueError(f"未知的集成数据集ID: {dataset_id}，可用数据集: {list(INTEGRATED_DATASETS.keys())}")
        
        dataset_info = INTEGRATED_DATASETS[dataset_id]
        dataset_type = dataset_info["type"]
        
        # 处理分割
        if split and dataset_info.get("split_files") and split in dataset_info["split_files"]:
            dataset_path = dataset_info["split_files"][split]
            logger.info(f"使用数据集 {dataset_id} 的 {split} 分割: {dataset_path}")
        else:
            dataset_path = dataset_info["path"]
            if split:
                logger.warning(f"数据集 {dataset_id} 没有 {split} 分割，使用默认数据集文件")
        
        # 如果未在kwargs中指定media_dir，但数据集信息中有，则使用数据集的media_dir
        if "media_dir" not in kwargs and dataset_info.get("media_dir"):
            kwargs["media_dir"] = dataset_info["media_dir"]
    
    # 参数验证
    if not dataset_path:
        raise ValueError("必须指定dataset_id或dataset_path中的一个")
    
    # 获取数据集类并实例化
    try:
        # 处理数据集类型别名
        if dataset_type.lower() in DATASET_TYPE_ALIASES:
            dataset_type = DATASET_TYPE_ALIASES[dataset_type.lower()]
        
        # 检查数据集类型是否注册
        if dataset_type not in DATASET_REGISTRY:
            logger.warning(f"未注册的数据集类型: {dataset_type}，将使用默认的XpertFormat解析器")
            dataset_class = XpertFormatDataset
        else:
            dataset_class = get_dataset_class(dataset_type)
        
        return dataset_class(dataset_path, **kwargs)
    except Exception as e:
        logger.error(f"实例化数据集失败: {str(e)}")
        raise ValueError(f"创建数据集实例失败: {str(e)}")


def list_available_datasets() -> List[Dict[str, str]]:
    """
    列出所有可用的已集成数据集
    
    Returns:
        数据集基本信息列表
    """
    # 如果INTEGRATED_DATASETS为空，先扫描一次
    if not INTEGRATED_DATASETS:
        scan_integrated_datasets()
    
    return [
        {
            "id": dataset_id,
            "name": info["name"],
            "type": info["type"],
            "description": info["description"]
        }
        for dataset_id, info in INTEGRATED_DATASETS.items()
    ] 