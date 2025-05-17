#!/usr/bin/env python
# coding: utf-8
"""
API调用实际测试脚本

该脚本使用config.yaml配置文件，测试大模型API的实际调用和响应。
"""

import os
import sys
import yaml
import json
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xperteval.core import invoke_model_api, ApiError
from xperteval.config import load_model_configs

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
CONFIG_EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config_example.yaml")

def ensure_config_exists():
    """确保配置文件存在，如果不存在则从示例配置创建"""
    if not os.path.exists(CONFIG_PATH):
        if os.path.exists(CONFIG_EXAMPLE_PATH):
            print(f"配置文件 {CONFIG_PATH} 不存在，正在从示例配置创建...")
            with open(CONFIG_EXAMPLE_PATH, 'r', encoding='utf-8') as f_example:
                example_content = f_example.read()
            
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f_config:
                f_config.write(example_content)
            
            print(f"配置文件已创建。请编辑 {CONFIG_PATH} 并填入您的API密钥")
            print("然后再次运行此脚本")
            return False
        else:
            print(f"错误：示例配置文件 {CONFIG_EXAMPLE_PATH} 不存在")
            return False
    return True

def test_api_call():
    """测试API调用"""
    try:
        # 加载配置
        config = load_model_configs(CONFIG_PATH)
        print(f"成功加载配置文件，共有 {len(config['models'])} 个模型配置")
        
        # 获取主API模型
        main_model = None
        for model in config['models']:
            if model.get('MAIN_API', False):
                main_model = model
                break
        
        if not main_model:
            print("警告：未找到标记为MAIN_API的模型，使用第一个模型")
            main_model = config['models'][0]
        
        print(f"使用模型: {main_model['MODEL_NAME']} (API基址: {main_model['OPENAI_API_BASE']})")
        
        # 构建请求负载
        request_payload = {
            "model": main_model['MODEL_NAME'],
            "messages": [
                {"role": "user", "content": "你好，请用中文简短地介绍一下你自己"}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        # 调用API
        print("正在调用API...")
        response = invoke_model_api(main_model, request_payload)
        
        # 打印响应
        print("\n=== API响应 ===")
        if 'choices' in response and len(response['choices']) > 0:
            if 'message' in response['choices'][0]:
                content = response['choices'][0]['message'].get('content', '')
                print(f"模型回答: {content}")
            else:
                print("响应格式异常，无法提取内容")
        
        print("\n=== 完整响应 ===")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
        # 打印Token使用情况
        if 'usage' in response:
            usage = response['usage']
            print(f"\nToken使用情况:")
            print(f"  - 提示词tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  - 回答tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  - 总tokens: {usage.get('total_tokens', 'N/A')}")
        
        return True
    
    except ApiError as e:
        print(f"API调用错误: {e}")
        return False
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("===== XpertEval API调用测试 =====")
    
    if not ensure_config_exists():
        sys.exit(1)
    
    print("\n正在测试API调用...")
    if test_api_call():
        print("\n✅ 测试完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1) 