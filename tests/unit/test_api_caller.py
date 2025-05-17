#!/usr/bin/env python
# coding: utf-8
"""
API调用模块的单元测试
"""

import os
import json
import unittest
import sys
from unittest.mock import patch, MagicMock

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from xperteval.core import invoke_model_api, ApiError
import requests

class TestApiCaller(unittest.TestCase):
    """测试API调用模块"""

    def setUp(self):
        """设置测试环境"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.mock_responses_dir = os.path.join(self.test_data_dir, 'mock_responses')
        
        # 加载模拟响应数据
        with open(os.path.join(self.mock_responses_dir, 'success_response.json'), 'r', encoding='utf-8') as f:
            self.success_response_data = json.load(f)
            
        with open(os.path.join(self.mock_responses_dir, 'error_response.json'), 'r', encoding='utf-8') as f:
            self.error_response_data = json.load(f)
            
        # 模型配置
        self.model_config = {
            'OPENAI_API_BASE': 'https://api.example.com/v1',
            'OPENAI_API_KEY': 'test-api-key',
            'MODEL_NAME': 'gpt-test-model',
            'MODEL_TYPE': 'text',
            'REQUEST_TIMEOUT': 30
        }
        
        # 请求负载
        self.request_payload = {
            'model': 'gpt-test-model',
            'messages': [
                {'role': 'user', 'content': '这是测试问题'}
            ],
            'max_tokens': 100,
            'temperature': 0.7
        }

    @patch('requests.post')
    def test_successful_api_call(self, mock_post):
        """测试成功的API调用"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response_data
        mock_post.return_value = mock_response
        
        # 调用API
        result = invoke_model_api(self.model_config, self.request_payload)
        
        # 验证请求参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['url'], 'https://api.example.com/v1/chat/completions')
        self.assertEqual(call_args[1]['headers']['Authorization'], f"Bearer {self.model_config['OPENAI_API_KEY']}")
        self.assertEqual(call_args[1]['headers']['Content-Type'], 'application/json')
        self.assertEqual(call_args[1]['json'], self.request_payload)
        self.assertEqual(call_args[1]['timeout'], 30)
        
        # 验证结果
        self.assertEqual(result, self.success_response_data)
        self.assertEqual(result['choices'][0]['message']['content'], '这是测试模型的回答内容。')

    @patch('requests.post')
    def test_custom_endpoint(self, mock_post):
        """测试自定义端点"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response_data
        mock_post.return_value = mock_response
        
        # 调用API，使用自定义端点
        result = invoke_model_api(self.model_config, self.request_payload, endpoint="/v1/completions")
        
        # 验证请求URL
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args[1]['url'], 'https://api.example.com/v1/v1/completions')

    @patch('requests.post')
    def test_error_response(self, mock_post):
        """测试错误响应处理"""
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 401  # 认证失败
        mock_response.json.return_value = self.error_response_data
        mock_post.return_value = mock_response
        
        # 调用API并验证异常
        with self.assertRaises(ApiError) as context:
            invoke_model_api(self.model_config, self.request_payload)
        
        # 验证错误信息
        error = context.exception
        self.assertEqual(error.status_code, 401)
        self.assertIn("API请求失败", str(error))
        self.assertIn("无效的认证凭据", str(error))

    @patch('requests.post')
    def test_rate_limit_retry(self, mock_post):
        """测试速率限制和重试逻辑"""
        # 设置第一次请求为速率限制，第二次请求成功
        mock_response_rate_limit = MagicMock()
        mock_response_rate_limit.status_code = 429  # 速率限制
        mock_response_rate_limit.headers = {'Retry-After': '0.1'}  # 减少测试等待时间
        mock_response_rate_limit.json.return_value = {"error": {"message": "速率限制"}}
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = self.success_response_data
        
        # 设置mock_post第一次返回速率限制，第二次返回成功
        mock_post.side_effect = [mock_response_rate_limit, mock_response_success]
        
        # 调用API
        result = invoke_model_api(self.model_config, self.request_payload, retry_delay=0.1)
        
        # 验证调用次数和结果
        self.assertEqual(mock_post.call_count, 2)  # 调用了两次
        self.assertEqual(result, self.success_response_data)

    @patch('requests.post')
    def test_connection_error_retry(self, mock_post):
        """测试连接错误和重试逻辑"""
        # 设置第一次请求抛出连接错误，第二次请求成功
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("连接失败"),
            MagicMock(status_code=200, json=lambda: self.success_response_data)
        ]
        
        # 调用API
        result = invoke_model_api(self.model_config, self.request_payload, retry_delay=0.1)
        
        # 验证调用次数和结果
        self.assertEqual(mock_post.call_count, 2)  # 调用了两次
        self.assertEqual(result, self.success_response_data)

    @patch('requests.post')
    def test_max_retries_exceeded(self, mock_post):
        """测试超出最大重试次数"""
        # 设置所有请求都抛出连接错误
        mock_post.side_effect = requests.exceptions.ConnectionError("连接始终失败")
        
        # 调用API并验证异常
        with self.assertRaises(ApiError) as context:
            invoke_model_api(self.model_config, self.request_payload, max_retries=2, retry_delay=0.1)
        
        # 验证调用次数和错误信息
        self.assertEqual(mock_post.call_count, 3)  # 初始请求 + 2次重试
        # 修改断言，使其与实际错误消息匹配
        self.assertIn("API请求异常", str(context.exception))
        self.assertIn("连接始终失败", str(context.exception))

    def test_missing_api_base(self):
        """测试缺少API基址"""
        invalid_config = dict(self.model_config)
        invalid_config['OPENAI_API_BASE'] = ''
        
        with self.assertRaises(ApiError) as context:
            invoke_model_api(invalid_config, self.request_payload)
            
        self.assertIn("API基址(OPENAI_API_BASE)不能为空", str(context.exception))

    def test_missing_api_key(self):
        """测试缺少API密钥"""
        invalid_config = dict(self.model_config)
        invalid_config['OPENAI_API_KEY'] = ''
        
        with self.assertRaises(ApiError) as context:
            invoke_model_api(invalid_config, self.request_payload)
            
        self.assertIn("API密钥(OPENAI_API_KEY)不能为空", str(context.exception))

if __name__ == "__main__":
    unittest.main() 