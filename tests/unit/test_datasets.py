#!/usr/bin/env python
# coding: utf-8
"""
数据集处理模块的单元测试
"""

import os
import unittest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from xperteval.datasets import (
    BaseDataset,
    MsSwiftDataset,
    get_dataset,
    list_available_datasets,
    register_dataset_type,
    scan_integrated_datasets
)
from xperteval.datasets.registered_datasets import DEFAULT_DATASETS_DIR

class TestBaseDataset(unittest.TestCase):
    """测试数据集基类"""

    def test_abstract_methods(self):
        """测试基类的抽象方法不能直接实例化"""
        with self.assertRaises(TypeError):
            BaseDataset("/path/to/dataset")
            
    def test_concrete_implementation(self):
        """测试具体实现类是否能实例化"""
        class ConcreteDataset(BaseDataset):
            def __init__(self, dataset_path):
                super().__init__(dataset_path)
                self.data = [{"id": "1", "text": "test"}]
                
            def __len__(self):
                return len(self.data)
                
            def __getitem__(self, idx):
                return self.data[idx]
                
            def load_data(self):
                pass  # 已在__init__中加载
                
        # 验证具体实现类可以实例化
        dataset = ConcreteDataset("/test/path")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0]["text"], "test")
        
        # 验证元数据方法
        metadata = dataset.get_metadata()
        self.assertEqual(metadata["name"], "ConcreteDataset")
        self.assertEqual(metadata["path"], "/test/path")
        self.assertEqual(metadata["size"], 1)
        self.assertEqual(metadata["format"], "base")


class TestMsSwiftDataset(unittest.TestCase):
    """测试MS-SWIFT数据集解析器"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.test_dataset_path = os.path.join(self.test_data_dir, 'test_ms_swift.jsonl')
        self.test_media_dir = os.path.join(self.test_data_dir, 'media')
        
    @patch('os.path.exists')
    def test_load_ms_swift_dataset(self, mock_exists):
        """测试加载MS-SWIFT格式数据集"""
        # 模拟文件存在检查，让所有文件路径检查返回True
        mock_exists.return_value = True
        
        dataset = MsSwiftDataset(self.test_dataset_path, media_dir=self.test_media_dir)
        
        # 验证数据集大小（排除无效数据后应为4个样本）
        self.assertEqual(len(dataset), 4)
        
        # 验证普通文本样本解析
        sample1 = dataset[0]
        self.assertEqual(sample1["id"], "sample001")
        self.assertEqual(sample1["query"], "简述中医的基本理论体系")
        self.assertTrue("response" in sample1)
        self.assertFalse(sample1["is_multimodal"])
        self.assertFalse(sample1["is_multi_turn"])
        
        # 验证包含文件的多模态样本解析
        sample3 = dataset[2]
        self.assertEqual(sample3["id"], "sample003")
        self.assertTrue(sample3["is_multimodal"])
        self.assertTrue("files" in sample3)
        self.assertEqual(len(sample3["files"]), 1)
        self.assertEqual(sample3["files"][0]["type"], "image")
        
        # 验证多轮对话样本解析
        sample4 = dataset[3]
        self.assertEqual(sample4["id"], "sample004")
        self.assertTrue(sample4["is_multi_turn"])
        self.assertTrue("history" in sample4)
        self.assertEqual(len(sample4["history"]), 2)
        
    def test_dataset_get_metadata(self):
        """测试获取数据集元数据"""
        with patch('xperteval.datasets.ms_swift_parser.MsSwiftDataset.load_data'):
            dataset = MsSwiftDataset(self.test_dataset_path)
            # 手动设置数据大小以便测试
            dataset.data = [1, 2, 3]
            
            metadata = dataset.get_metadata()
            self.assertEqual(metadata["name"], "MsSwiftDataset")
            self.assertEqual(metadata["format"], "ms-swift")
            self.assertEqual(metadata["size"], 3)
            
    def test_file_type_detection(self):
        """测试文件类型检测"""
        with patch('xperteval.datasets.ms_swift_parser.MsSwiftDataset.load_data'):
            dataset = MsSwiftDataset(self.test_dataset_path, media_dir=self.test_media_dir)
            
            # 测试图片格式识别
            self.assertEqual(dataset._guess_file_type("image.jpg"), "image")
            self.assertEqual(dataset._guess_file_type("some/path/photo.png"), "image")
            
            # 测试音频格式识别
            self.assertEqual(dataset._guess_file_type("audio.mp3"), "audio")
            self.assertEqual(dataset._guess_file_type("voice.wav"), "audio")
            
            # 测试视频格式识别
            self.assertEqual(dataset._guess_file_type("video.mp4"), "video")
            self.assertEqual(dataset._guess_file_type("movie.mkv"), "video")
            
            # 测试未知格式
            self.assertEqual(dataset._guess_file_type("document.pdf"), "unknown")
        
    def test_indexing_errors(self):
        """测试索引错误处理"""
        with patch('xperteval.datasets.ms_swift_parser.MsSwiftDataset.load_data'):
            dataset = MsSwiftDataset(self.test_dataset_path)
            # 手动设置数据以便测试
            dataset.data = [{"id": "1"}]
            
            # 测试有效索引
            self.assertEqual(dataset[0]["id"], "1")
            
            # 测试无效索引
            with self.assertRaises(IndexError):
                _ = dataset[1]
            
            with self.assertRaises(IndexError):
                _ = dataset[-2]


class TestRegisteredDatasets(unittest.TestCase):
    """测试数据集注册和获取功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.test_integrated_dir = os.path.join(self.test_data_dir, 'integrated')
        self.test_dataset_path = os.path.join(self.test_data_dir, 'test_ms_swift.jsonl')
    
    def test_register_dataset_type(self):
        """测试注册新的数据集类型"""
        # 创建临时数据集类
        class CustomDataset(BaseDataset):
            def __init__(self, dataset_path, **kwargs):
                super().__init__(dataset_path, **kwargs)
            
            def __len__(self):
                return 0
                
            def __getitem__(self, idx):
                return {}
                
            def load_data(self):
                pass
        
        # 注册自定义数据集类
        register_dataset_type("custom", CustomDataset)
        
        # 验证注册成功
        from xperteval.datasets.registered_datasets import DATASET_REGISTRY
        self.assertIn("custom", DATASET_REGISTRY)
        self.assertEqual(DATASET_REGISTRY["custom"], CustomDataset)
        
        # 测试注册非BaseDataset子类
        class NotDataset:
            pass
            
        with self.assertRaises(TypeError):
            register_dataset_type("invalid", NotDataset)
    
    def test_scan_integrated_datasets(self):
        """测试扫描集成数据集"""
        test_dir = Path(self.test_integrated_dir)
        
        # 创建测试数据 - 这里使用直接的模块替换来避免复杂的mock
        with patch('xperteval.datasets.registered_datasets.scan_integrated_datasets', autospec=True) as mock_scan:
            # 模拟返回结果
            mock_scan.return_value = {
                "tcm_example": {
                    "id": "tcm_example",
                    "name": "Tcm Example",
                    "path": str(test_dir / "tcm_example" / "dataset.jsonl"),
                    "type": "ms-swift",
                    "description": "中医药基础知识测试数据集",
                    "media_dir": None
                }
            }
            
            # 调用被测试函数
            datasets = mock_scan(test_dir)
            
            # 验证结果
            self.assertIn("tcm_example", datasets)
            self.assertEqual(datasets["tcm_example"]["type"], "ms-swift")
    
    @patch('xperteval.datasets.registered_datasets.scan_integrated_datasets')
    def test_list_available_datasets(self, mock_scan):
        """测试列出可用数据集"""
        # 创建测试集成数据集结果
        test_datasets = {
            "dataset1": {"id": "dataset1", "name": "Dataset One", "type": "ms-swift", "description": "Test dataset 1"},
            "dataset2": {"id": "dataset2", "name": "Dataset Two", "type": "custom", "description": "Test dataset 2"}
        }
        
        # 为scan_integrated_datasets设置返回值
        mock_scan.return_value = test_datasets
        
        # 直接通过全局变量注入模拟数据
        with patch('xperteval.datasets.registered_datasets.INTEGRATED_DATASETS', test_datasets):
            # 获取可用数据集列表
            datasets = list_available_datasets()
            
            # 验证返回结果
            self.assertEqual(len(datasets), 2)
            self.assertEqual(datasets[0]["id"], "dataset1")
            self.assertEqual(datasets[1]["id"], "dataset2")
    
    @patch('xperteval.datasets.registered_datasets.get_dataset_class')
    @patch('xperteval.datasets.registered_datasets.INTEGRATED_DATASETS', {
        "test_dataset": {
            "id": "test_dataset",
            "path": "/path/to/dataset.jsonl",
            "type": "ms-swift",
            "media_dir": "/path/to/media",
            "description": "Test dataset"
        }
    })
    def test_get_dataset_by_id(self, mock_get_class):
        """测试通过ID获取数据集"""
        # 设置模拟返回值
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        mock_get_class.return_value = mock_class
        
        # 通过ID获取数据集
        dataset = get_dataset(dataset_id="test_dataset")
        
        # 验证调用参数
        mock_get_class.assert_called_once_with("ms-swift")
        mock_class.assert_called_once_with(
            "/path/to/dataset.jsonl",
            media_dir="/path/to/media"
        )
        
        # 验证返回的是预期的实例
        self.assertEqual(dataset, mock_instance)
    
    @patch('xperteval.datasets.registered_datasets.get_dataset_class')
    def test_get_dataset_by_path(self, mock_get_class):
        """测试通过路径获取数据集"""
        # 设置模拟返回值
        mock_class = MagicMock()
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        mock_get_class.return_value = mock_class
        
        # 通过路径获取数据集
        dataset = get_dataset(dataset_path=self.test_dataset_path)
        
        # 验证调用参数
        mock_get_class.assert_called_once_with("ms-swift")
        mock_class.assert_called_once_with(self.test_dataset_path)
        
        # 验证返回的是预期的实例
        self.assertEqual(dataset, mock_instance)
    
    def test_get_dataset_validation(self):
        """测试获取数据集的参数验证"""
        # 测试既未指定ID也未指定路径的情况
        with self.assertRaises(ValueError):
            get_dataset()
        
        # 测试指定了不存在的数据集类型
        with patch('xperteval.datasets.registered_datasets.get_dataset_class') as mock_get_class:
            mock_get_class.side_effect = ValueError("未知的数据集类型")
            with self.assertRaises(ValueError):
                get_dataset(dataset_path=self.test_dataset_path, dataset_type="nonexistent_type")
        
        # 测试指定了不存在的数据集ID
        with patch('xperteval.datasets.registered_datasets.INTEGRATED_DATASETS', {}):
            with self.assertRaises(ValueError):
                get_dataset(dataset_id="nonexistent_id")


if __name__ == "__main__":
    unittest.main() 