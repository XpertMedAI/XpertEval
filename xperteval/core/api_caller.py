# coding: utf-8
"""
API调用模块

本模块负责封装与OpenAI兼容API接口的HTTP通信，
处理请求发送、响应解析和错误处理。
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List, Union

# 导入日志模块
from ..utils import get_logger

# 配置日志记录
logger = get_logger(__name__)

class ApiError(Exception):
    """API调用异常类"""
    def __init__(self, message: str, status_code: Optional[int] = None, 
                response_text: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        self.details = details
        super().__init__(self.message)
        
    def __str__(self):
        error_msg = self.message
        if self.status_code:
            error_msg += f" (状态码: {self.status_code})"
        if self.details:
            error_msg += f"\n详细信息: {json.dumps(self.details, ensure_ascii=False)}"
        return error_msg

def invoke_model_api(model_config: Dict[str, Any], request_payload: Dict[str, Any], 
                    endpoint: str = "/chat/completions", max_retries: int = 3, 
                    retry_delay: float = 1.0) -> Dict[str, Any]:
    """
    调用模型API
    
    Args:
        model_config: 模型配置字典，包含API基址、密钥等
        request_payload: 请求负载，符合OpenAI API请求格式
        endpoint: API端点路径，默认为"/chat/completions"
        max_retries: 最大重试次数，默认为3
        retry_delay: 重试间隔（秒），默认为1.0
        
    Returns:
        Dict: API响应的JSON内容
        
    Raises:
        ApiError: 当API调用失败时抛出
    """
    # 提取API基础信息
    api_base = model_config.get('OPENAI_API_BASE', '').rstrip('/')
    api_key = model_config.get('OPENAI_API_KEY', '')
    timeout = float(model_config.get('REQUEST_TIMEOUT', 120))
    model_name = model_config.get('MODEL_NAME', 'unknown_model')
    
    # 验证必需参数
    if not api_base:
        logger.error("API基址(OPENAI_API_BASE)不能为空")
        raise ApiError("API基址(OPENAI_API_BASE)不能为空")
    if not api_key:
        logger.error("API密钥(OPENAI_API_KEY)不能为空")
        raise ApiError("API密钥(OPENAI_API_KEY)不能为空")
    
    # 构造完整URL
    url = f"{api_base}{endpoint}"
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 尝试发送请求，最多重试max_retries次
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        try:
            # 记录请求信息（排除敏感信息）
            logger.debug(f"准备调用模型API: {model_name}, 端点: {endpoint}")
            request_log = {
                "url": url,
                "method": "POST",
                "timeout": timeout,
                "model": model_name,
                "payload_keys": list(request_payload.keys()) if isinstance(request_payload, dict) else None
            }
            logger.debug(f"发送API请求: {json.dumps(request_log, ensure_ascii=False)}")
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                url=url,
                headers=headers,
                json=request_payload,
                timeout=timeout
            )
            elapsed_time = time.time() - start_time
            
            # 检查响应状态码
            if response.status_code == 200:
                # 请求成功
                logger.info(f"API请求成功 (模型: {model_name}, 耗时: {elapsed_time:.2f}秒)")
                try:
                    result = response.json()
                    return result
                except json.JSONDecodeError:
                    error_msg = "API响应格式错误，无法解析JSON"
                    logger.error(f"{error_msg}, 响应内容: {response.text[:200]}...")
                    raise ApiError(
                        message=error_msg,
                        status_code=response.status_code,
                        response_text=response.text
                    )
            else:
                # 请求失败但有响应
                logger.warning(f"API请求失败，模型: {model_name}, 状态码: {response.status_code}")
                error_details = {}
                
                # 尝试解析错误响应
                try:
                    error_details = response.json()
                except (json.JSONDecodeError, ValueError):
                    error_details = {"raw_text": response.text[:500]}
                
                logger.debug(f"错误详情: {json.dumps(error_details, ensure_ascii=False)}")
                
                # 根据不同状态码处理错误
                if response.status_code == 429:  # 速率限制
                    retry_after = response.headers.get('Retry-After', retry_delay)
                    try:
                        retry_after = float(retry_after)
                    except (ValueError, TypeError):
                        retry_after = retry_delay
                        
                    if attempt < max_retries:
                        logger.info(f"触发速率限制，将在{retry_after}秒后重试 (尝试 {attempt+1}/{max_retries})")
                        time.sleep(retry_after)
                        attempt += 1
                        continue
                    else:
                        error_msg = "API速率限制，已达到最大重试次数"
                        logger.error(error_msg)
                        raise ApiError(
                            message=error_msg,
                            status_code=response.status_code, 
                            details=error_details
                        )
                elif 500 <= response.status_code < 600:  # 服务器错误
                    if attempt < max_retries:
                        logger.info(f"服务器错误，{retry_delay}秒后重试 (尝试 {attempt+1}/{max_retries})")
                        time.sleep(retry_delay)
                        attempt += 1
                        continue
                    else:
                        error_msg = "API服务器错误，已达到最大重试次数"
                        logger.error(error_msg)
                        raise ApiError(
                            message=error_msg, 
                            status_code=response.status_code, 
                            details=error_details
                        )
                else:  # 其他错误（如认证错误、参数错误等）
                    error_msg = f"API请求失败: {error_details.get('error', {}).get('message', '未知错误')}"
                    logger.error(error_msg)
                    raise ApiError(
                        message=error_msg, 
                        status_code=response.status_code, 
                        details=error_details
                    )
                
        except requests.RequestException as e:
            # 请求异常（网络问题、超时等）
            last_error = e
            logger.warning(f"请求异常 (模型: {model_name}): {str(e)}")
            
            # 仅对超时或连接错误进行重试
            if isinstance(e, (requests.Timeout, requests.ConnectionError)) and attempt < max_retries:
                logger.info(f"连接异常，{retry_delay}秒后重试 (尝试 {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                attempt += 1
                continue
            else:
                error_msg = f"API请求异常: {str(e)}"
                logger.error(error_msg)
                raise ApiError(error_msg)
        
        # 如果没有触发continue，则跳出循环
        break
    
    # 如果到达这里，说明已经达到最大重试次数
    if last_error:
        error_msg = f"API请求失败，已达到最大重试次数: {str(last_error)}"
        logger.error(error_msg)
        raise ApiError(error_msg)
    
    # 这行代码理论上不会被执行，因为上面的循环要么返回结果，要么抛出异常
    return {} 