#!/usr/bin/env python
# coding: utf-8
"""
配置加载模块的单元测试
"""

import os
import unittest
import sys

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from xperteval.config import load_model_configs, ConfigError, ModelType

class TestConfigLoader(unittest.TestCase):
    """测试配置加载模块"""

    def setUp(self):
        """设置测试环境"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.valid_yaml_config = os.path.join(self.test_data_dir, 'valid_config.yaml')
        self.valid_json_config = os.path.join(self.test_data_dir, 'valid_config.json')
        self.invalid_missing_fields_config = os.path.join(self.test_data_dir, 'invalid_config_missing_fields.yaml')
        self.invalid_wrong_model_type_config = os.path.join(self.test_data_dir, 'invalid_config_wrong_model_type.yaml')
        self.valid_multiple_main_api_config = os.path.join(self.test_data_dir, 'valid_config_multiple_main_api.yaml')
        self.valid_no_main_api_config = os.path.join(self.test_data_dir, 'valid_config_no_main_api.yaml')
        self.invalid_param_config = os.path.join(self.test_data_dir, 'invalid_config_invalid_param.yaml')

    def test_load_valid_yaml_config(self):
        """测试加载有效的YAML配置文件"""
        config = load_model_configs(self.valid_yaml_config)
        
        # 验证全局默认参数
        self.assertIn('default_params', config)
        self.assertEqual(config['default_params']['MAX_TOKENS'], 4096)
        self.assertEqual(config['default_params']['TEMPERATURE'], 0.7)
        
        # 验证模型列表
        self.assertIn('models', config)
        self.assertEqual(len(config['models']), 2)
        
        # 验证第一个模型（主API）
        model1 = config['models'][0]
        self.assertEqual(model1['OPENAI_API_BASE'], "https://api.openai.com/v1")
        self.assertEqual(model1['MODEL_NAME'], "gpt-4")
        self.assertEqual(model1['MODEL_TYPE'], ModelType.TEXT)
        self.assertTrue(model1['MAIN_API'])
        
        # 验证第二个模型（参数合并覆盖）
        model2 = config['models'][1]
        self.assertEqual(model2['OPENAI_API_BASE'], "https://api.company.com/v1")
        self.assertEqual(model2['MODEL_TYPE'], ModelType.MLLM)
        self.assertEqual(model2['TEMPERATURE'], 0.8)  # 覆盖默认值0.7
        self.assertFalse(model2['MAIN_API'])

    def test_load_valid_json_config(self):
        """测试加载有效的JSON配置文件"""
        config = load_model_configs(self.valid_json_config)
        
        # 验证基本结构
        self.assertIn('default_params', config)
        self.assertIn('models', config)
        self.assertEqual(len(config['models']), 2)
        
        # 验证JSON解析正确
        model1 = config['models'][0]
        self.assertEqual(model1['OPENAI_API_BASE'], "https://api.openai.com/v1")
        self.assertTrue(model1['MAIN_API'])

    def test_missing_required_fields(self):
        """测试缺少必需字段时抛出异常"""
        with self.assertRaises(ConfigError) as context:
            load_model_configs(self.invalid_missing_fields_config)
        
        # 验证错误信息包含缺失字段的信息
        error_msg = str(context.exception)
        self.assertIn("缺少必需字段", error_msg)

    def test_invalid_model_type(self):
        """测试无效的MODEL_TYPE时抛出异常"""
        with self.assertRaises(ConfigError) as context:
            load_model_configs(self.invalid_wrong_model_type_config)
        
        # 验证错误信息包含MODEL_TYPE的信息
        error_msg = str(context.exception)
        self.assertIn("无效的MODEL_TYPE", error_msg)
        self.assertIn("invalid_type", error_msg)

    def test_multiple_main_api(self):
        """测试多个MAIN_API设置为True的情况"""
        config = load_model_configs(self.valid_multiple_main_api_config)
        
        # 验证只有第一个模型的MAIN_API为True
        self.assertTrue(config['models'][0]['MAIN_API'])
        self.assertFalse(config['models'][1]['MAIN_API'])
        self.assertFalse(config['models'][2]['MAIN_API'])

    def test_no_main_api(self):
        """测试没有设置MAIN_API的情况"""
        config = load_model_configs(self.valid_no_main_api_config)
        
        # 验证默认第一个模型的MAIN_API为True
        self.assertTrue(config['models'][0]['MAIN_API'])
        self.assertFalse(config['models'][1]['MAIN_API'])

    def test_invalid_parameter_value(self):
        """测试参数值无效的情况"""
        with self.assertRaises(ConfigError) as context:
            load_model_configs(self.invalid_param_config)
        
        # 验证错误信息包含参数值的信息
        error_msg = str(context.exception)
        self.assertTrue("TEMPERATURE必须在0到2之间" in error_msg or "MAX_TOKENS必须大于0" in error_msg)

    def test_nonexistent_file(self):
        """测试不存在的配置文件"""
        with self.assertRaises(ConfigError) as context:
            load_model_configs("nonexistent_file.yaml")
        
        # 验证错误信息包含文件不存在的信息
        self.assertIn("配置文件不存在", str(context.exception))

if __name__ == "__main__":
    unittest.main() 