# coding: utf-8
"""
模型配置加载与验证模块

本模块负责加载和验证模型API配置文件（YAML或JSON格式），
包括解析模型API信息、全局默认参数，以及进行配置有效性校验。
"""

import os
import json
import yaml
from typing import Dict, List, Union, Optional
from enum import Enum

class ModelType(Enum):
    """模型类型枚举"""
    TEXT = "text"      # 纯文本模型
    VISION = "vision"  # 视觉模型
    AUDIO = "audio"    # 音频模型
    MLLM = "mllm"      # 多模态语言模型

class ConfigError(Exception):
    """配置错误异常类"""
    pass

def load_model_configs(config_path: str) -> Dict:
    """
    加载并验证模型配置文件
    
    Args:
        config_path: 配置文件路径（支持.yaml/.yml或.json格式）
        
    Returns:
        Dict: 包含模型配置和全局默认参数的字典
        
    Raises:
        ConfigError: 当配置文件不存在、格式错误或配置无效时抛出
    """
    # 检查文件是否存在
    if not os.path.exists(config_path):
        raise ConfigError(f"配置文件不存在: {config_path}")
    
    # 根据文件扩展名选择加载方式
    try:
        if config_path.endswith(('.yaml', '.yml')):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif config_path.endswith('.json'):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            raise ConfigError(f"不支持的配置文件格式: {config_path}，仅支持.yaml/.yml或.json格式")
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ConfigError(f"配置文件格式错误: {str(e)}")
    
    # 验证配置结构
    validate_config(config)
    
    # 处理全局默认参数
    default_params = config.get('default_params', {})
    
    # 处理模型配置
    models = config.get('models', [])
    if not isinstance(models, list) or len(models) < 2:
        raise ConfigError("配置文件中必须包含至少两个模型配置")
    
    # 处理MAIN_API标记
    main_api_found = False
    for i, model in enumerate(models):
        # 合并全局默认参数
        model = {**default_params, **model}
        
        # 验证必需字段
        required_fields = ['OPENAI_API_BASE', 'OPENAI_API_KEY', 'MODEL_NAME', 'MODEL_TYPE']
        missing_fields = [field for field in required_fields if field not in model]
        if missing_fields:
            raise ConfigError(f"模型配置缺少必需字段: {', '.join(missing_fields)}")
        
        # 验证MODEL_TYPE
        try:
            model['MODEL_TYPE'] = ModelType(model['MODEL_TYPE'].lower())
        except ValueError:
            raise ConfigError(f"无效的MODEL_TYPE: {model['MODEL_TYPE']}，必须是以下之一: {', '.join(t.value for t in ModelType)}")
        
        # 处理MAIN_API
        is_main_api = model.get('MAIN_API', False)
        if is_main_api and not main_api_found:
            main_api_found = True
            model['MAIN_API'] = True
        else:
            model['MAIN_API'] = False
        
        # 验证可选参数
        validate_optional_params(model)
        
        # 更新模型配置
        models[i] = model
    
    # 如果没有找到MAIN_API，将第一个模型设为主API
    if not main_api_found and models:
        models[0]['MAIN_API'] = True
    
    return {
        'default_params': default_params,
        'models': models
    }

def validate_config(config: Dict) -> None:
    """
    验证配置字典的基本结构
    
    Args:
        config: 配置字典
        
    Raises:
        ConfigError: 当配置结构无效时抛出
    """
    if not isinstance(config, dict):
        raise ConfigError("配置文件必须是字典格式")
    
    if 'models' not in config:
        raise ConfigError("配置文件中缺少'models'字段")
    
    if not isinstance(config['models'], list):
        raise ConfigError("'models'字段必须是列表格式")

def validate_optional_params(model: Dict) -> None:
    """
    验证模型配置中的可选参数
    
    Args:
        model: 单个模型的配置字典
        
    Raises:
        ConfigError: 当可选参数无效时抛出
    """
    # 验证MAX_TOKENS
    if 'MAX_TOKENS' in model:
        try:
            max_tokens = int(model['MAX_TOKENS'])
            if max_tokens <= 0:
                raise ConfigError("MAX_TOKENS必须大于0")
        except ValueError:
            raise ConfigError("MAX_TOKENS必须是整数")
    
    # 验证TEMPERATURE
    if 'TEMPERATURE' in model:
        try:
            temp = float(model['TEMPERATURE'])
            if not 0 <= temp <= 2:
                raise ConfigError("TEMPERATURE必须在0到2之间")
        except ValueError:
            raise ConfigError("TEMPERATURE必须是浮点数")
    
    # 验证TOP_P
    if 'TOP_P' in model:
        try:
            top_p = float(model['TOP_P'])
            if not 0 <= top_p <= 1:
                raise ConfigError("TOP_P必须在0到1之间")
        except ValueError:
            raise ConfigError("TOP_P必须是浮点数")
    
    # 验证TOP_K
    if 'TOP_K' in model:
        try:
            top_k = float(model['TOP_K'])
            if not 0 <= top_k <= 1:
                raise ConfigError("TOP_K必须在0到1之间")
        except ValueError:
            raise ConfigError("TOP_K必须是浮点数")
    
    # 验证FREQUENCY_PENALTY
    if 'FREQUENCY_PENALTY' in model:
        try:
            freq_penalty = float(model['FREQUENCY_PENALTY'])
            if not -2 <= freq_penalty <= 2:
                raise ConfigError("FREQUENCY_PENALTY必须在-2到2之间")
        except ValueError:
            raise ConfigError("FREQUENCY_PENALTY必须是浮点数")
    
    # 验证PRESENCE_PENALTY
    if 'PRESENCE_PENALTY' in model:
        try:
            pres_penalty = float(model['PRESENCE_PENALTY'])
            if not -2 <= pres_penalty <= 2:
                raise ConfigError("PRESENCE_PENALTY必须在-2到2之间")
        except ValueError:
            raise ConfigError("PRESENCE_PENALTY必须是浮点数")
    
    # 验证REQUEST_TIMEOUT
    if 'REQUEST_TIMEOUT' in model:
        try:
            timeout = float(model['REQUEST_TIMEOUT'])
            if timeout <= 0:
                raise ConfigError("REQUEST_TIMEOUT必须大于0")
        except ValueError:
            raise ConfigError("REQUEST_TIMEOUT必须是浮点数") 