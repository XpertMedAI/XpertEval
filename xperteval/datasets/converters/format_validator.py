# coding: utf-8
"""
XpertFormat格式验证器

用于验证数据是否符合XpertFormat规范，并提供详细的错误信息和修复建议。
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from ...utils import get_logger

# 配置日志
logger = get_logger(__name__)

# XpertFormat必需字段
REQUIRED_FIELDS = ["id", "query"]

# XpertFormat可选顶层字段
OPTIONAL_FIELDS = ["response", "history", "files", "choices", "answer", "meta"]

# 特定结构的字段验证规则
FIELD_RULES = {
    "history": {
        "type": list,
        "item_fields": ["role", "content"],
        "allowed_roles": ["human", "assistant", "system"]
    },
    "files": {
        "type": list,
        "item_fields": ["path", "type"],
        "allowed_types": ["image", "audio", "video"]
    },
    "choices": {
        "type": list,
        "item_fields": ["id", "content"]
    },
    "answer": {
        "type": dict,
        "fields": ["type", "value"],
        "optional_fields": ["explanation"],
        "allowed_types": ["choice", "text", "code", "step_by_step"]
    },
    "meta": {
        "type": dict,
        "optional_fields": [
            "task_type", "category", "subject", "difficulty", 
            "source", "tags", "language"
        ],
        "allowed_task_types": [
            "qa", "choice", "code", "math", "vision", "audio", "multi"
        ]
    }
}

def validate_xpert_format(data: Union[Dict, List[Dict], str]) -> Tuple[bool, List[str], Optional[Dict]]:
    """
    验证数据是否符合XpertFormat规范
    
    Args:
        data: 要验证的数据，可以是字典、字典列表或JSON字符串
        
    Returns:
        元组 (是否有效, 错误信息列表, 修复后的数据(如果可修复))
    """
    # 如果是字符串，尝试解析为JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            return False, [f"无效的JSON格式: {e}"], None
    
    # 如果是单个样本，转换为列表处理
    samples = data if isinstance(data, list) else [data]
    
    all_valid = True
    all_errors = []
    fixed_samples = []
    
    # 验证每个样本
    for i, sample in enumerate(samples):
        sample_id = sample.get("id", f"样本_{i}")
        valid, errors, fixed_sample = _validate_sample(sample)
        
        if not valid:
            all_valid = False
            all_errors.extend([f"[{sample_id}] {error}" for error in errors])
        
        fixed_samples.append(fixed_sample or sample)
    
    # 返回结果
    if all_valid:
        return True, [], data
    else:
        fixed_data = fixed_samples if isinstance(data, list) else fixed_samples[0]
        return False, all_errors, fixed_data

def _validate_sample(sample: Dict) -> Tuple[bool, List[str], Optional[Dict]]:
    """
    验证单个样本是否符合XpertFormat规范
    
    Args:
        sample: 样本数据字典
        
    Returns:
        元组 (是否有效, 错误信息列表, 修复后的数据(如果可修复))
    """
    if not isinstance(sample, dict):
        return False, ["样本必须是一个字典"], None
    
    errors = []
    fixed_sample = sample.copy()
    
    # 检查必需字段
    for field in REQUIRED_FIELDS:
        if field not in sample:
            errors.append(f"缺少必需字段: {field}")
            fixed_sample[field] = f"缺失的{field}" if field == "id" else ""
    
    # 检查未知字段
    all_allowed_fields = REQUIRED_FIELDS + OPTIONAL_FIELDS
    unknown_fields = [field for field in sample if field not in all_allowed_fields]
    if unknown_fields:
        errors.append(f"包含未知字段: {', '.join(unknown_fields)}")
        for field in unknown_fields:
            if field in fixed_sample:
                del fixed_sample[field]
    
    # 验证特定结构的字段
    for field, rules in FIELD_RULES.items():
        if field in sample:
            field_valid, field_errors, fixed_field = _validate_field(field, sample[field], rules)
            if not field_valid:
                errors.extend([f"{field}: {error}" for error in field_errors])
                fixed_sample[field] = fixed_field
    
    # 检查选择题格式的一致性
    if "choices" in sample and "answer" in sample:
        choices_valid, choices_errors = _validate_choices_and_answer(sample)
        if not choices_valid:
            errors.extend(choices_errors)
    
    # 检查文件路径的有效性
    if "files" in sample:
        files_valid, files_errors = _validate_file_paths(sample["files"])
        if not files_valid:
            errors.extend([f"files: {error}" for error in files_errors])
    
    return len(errors) == 0, errors, fixed_sample

def _validate_field(field_name: str, field_value: Any, rules: Dict) -> Tuple[bool, List[str], Any]:
    """
    验证特定字段的结构
    
    Args:
        field_name: 字段名称
        field_value: 字段值
        rules: 验证规则
        
    Returns:
        元组 (是否有效, 错误信息列表, 修复后的值(如果可修复))
    """
    errors = []
    fixed_value = field_value
    
    # 检查类型
    expected_type = rules.get("type")
    if expected_type and not isinstance(field_value, expected_type):
        errors.append(f"应为 {expected_type.__name__} 类型，但实际是 {type(field_value).__name__}")
        # 尝试修复
        if expected_type == list:
            fixed_value = []
        elif expected_type == dict:
            fixed_value = {}
        else:
            fixed_value = None
    
    # 对列表类型的字段，验证每个项目
    if isinstance(field_value, list) and "item_fields" in rules:
        required_item_fields = rules["item_fields"]
        fixed_items = []
        
        for i, item in enumerate(field_value):
            if not isinstance(item, dict):
                errors.append(f"项目 {i} 应为字典类型")
                continue
            
            fixed_item = item.copy()
            for req_field in required_item_fields:
                if req_field not in item:
                    errors.append(f"项目 {i} 缺少必需字段: {req_field}")
                    fixed_item[req_field] = ""
            
            # 检查特定字段的允许值
            if "role" in item and "allowed_roles" in rules:
                if item["role"] not in rules["allowed_roles"]:
                    errors.append(f"项目 {i} 的 'role' 值无效: {item['role']}，允许的值: {', '.join(rules['allowed_roles'])}")
                    fixed_item["role"] = rules["allowed_roles"][0]
            
            if "type" in item and "allowed_types" in rules:
                if item["type"] not in rules["allowed_types"]:
                    errors.append(f"项目 {i} 的 'type' 值无效: {item['type']}，允许的值: {', '.join(rules['allowed_types'])}")
                    fixed_item["type"] = rules["allowed_types"][0]
            
            fixed_items.append(fixed_item)
        
        fixed_value = fixed_items
    
    # 对字典类型的字段，验证必需字段
    if isinstance(field_value, dict):
        required_fields = rules.get("fields", [])
        optional_fields = rules.get("optional_fields", [])
        fixed_dict = field_value.copy()
        
        # 检查必需字段
        for req_field in required_fields:
            if req_field not in field_value:
                errors.append(f"缺少必需字段: {req_field}")
                fixed_dict[req_field] = ""
        
        # 检查未知字段
        all_allowed_fields = required_fields + optional_fields
        unknown_fields = [f for f in field_value if f not in all_allowed_fields]
        if unknown_fields and all_allowed_fields:  # 只有当定义了允许字段时才检查
            errors.append(f"包含未知字段: {', '.join(unknown_fields)}")
            for f in unknown_fields:
                if f in fixed_dict:
                    del fixed_dict[f]
        
        # 检查特定字段的允许值
        if "type" in field_value and "allowed_types" in rules:
            if field_value["type"] not in rules["allowed_types"]:
                errors.append(f"'type' 值无效: {field_value['type']}，允许的值: {', '.join(rules['allowed_types'])}")
                fixed_dict["type"] = rules["allowed_types"][0]
        
        if "task_type" in field_value and "allowed_task_types" in rules:
            if field_value["task_type"] not in rules["allowed_task_types"]:
                errors.append(f"'task_type' 值无效: {field_value['task_type']}，允许的值: {', '.join(rules['allowed_task_types'])}")
                fixed_dict["task_type"] = rules["allowed_task_types"][0]
        
        fixed_value = fixed_dict
    
    return len(errors) == 0, errors, fixed_value

def _validate_choices_and_answer(sample: Dict) -> Tuple[bool, List[str]]:
    """
    验证选择题格式的一致性
    
    Args:
        sample: 样本数据字典
        
    Returns:
        元组 (是否有效, 错误信息列表)
    """
    errors = []
    
    choices = sample.get("choices", [])
    answer = sample.get("answer", {})
    
    if not choices:
        return True, []  # 没有选项，不进行验证
    
    # 检查answer.type是否为choice
    if answer.get("type") != "choice":
        errors.append("包含'choices'字段但'answer.type'不是'choice'")
    
    # 检查answer.value是否是有效的选项ID
    answer_value = answer.get("value")
    choice_ids = [choice.get("id") for choice in choices if isinstance(choice, dict) and "id" in choice]
    
    if answer_value and choice_ids and answer_value not in choice_ids:
        errors.append(f"'answer.value' ({answer_value}) 不是有效的选项ID，有效选项: {', '.join(choice_ids)}")
    
    return len(errors) == 0, errors

def _validate_file_paths(files: List[Dict]) -> Tuple[bool, List[str]]:
    """
    验证文件路径的有效性
    
    Args:
        files: 文件列表
        
    Returns:
        元组 (是否有效, 错误信息列表)
    """
    errors = []
    
    for i, file_info in enumerate(files):
        if not isinstance(file_info, dict):
            errors.append(f"文件项目 {i} 应为字典类型")
            continue
        
        path = file_info.get("path", "")
        
        # 检查路径是否为空
        if not path:
            errors.append(f"文件项目 {i} 缺少路径")
            continue
        
        # 检查本地文件是否存在（如果不是URL）
        if not path.startswith(("http://", "https://", "/")):
            if not os.path.exists(path):
                errors.append(f"文件不存在: {path}")
    
    return len(errors) == 0, errors

def get_format_guidelines() -> str:
    """
    获取XpertFormat格式指南
    
    Returns:
        格式指南文本
    """
    return """
XpertFormat 格式指南:

1. 必需字段:
   - id: 样本唯一标识符
   - query: 问题文本

2. 可选顶层字段:
   - response: 参考答案或标准答案
   - history: 多轮对话历史
   - files: 多模态文件列表
   - choices: 选择题选项列表
   - answer: 答案信息
   - meta: 元数据

3. 特定字段格式:
   - history: 列表，每项包含 "role" 和 "content"
     - role 可选值: "human", "assistant", "system"
   
   - files: 列表，每项包含 "path" 和 "type"
     - type 可选值: "image", "audio", "video"
   
   - choices: 列表，每项包含 "id" 和 "content"
   
   - answer: 字典，包含 "type", "value" 和可选的 "explanation"
     - type 可选值: "choice", "text", "code", "step_by_step"
   
   - meta: 字典，可包含各种元数据
     - task_type 可选值: "qa", "choice", "code", "math", "vision", "audio", "multi"

4. 示例:
```json
{
  "id": "sample_001",
  "query": "这是一个问题？",
  "response": "这是标准答案",
  "choices": [
    {"id": "A", "content": "选项A"},
    {"id": "B", "content": "选项B"}
  ],
  "answer": {
    "type": "choice",
    "value": "A",
    "explanation": "解释为什么A是正确答案"
  },
  "meta": {
    "task_type": "choice",
    "category": "常识",
    "difficulty": "简单"
  }
}
```
"""

def validate_file(file_path: str, fix: bool = False) -> Tuple[bool, List[str], Optional[str]]:
    """
    验证文件是否符合XpertFormat规范
    
    Args:
        file_path: 文件路径
        fix: 是否修复并保存
        
    Returns:
        元组 (是否有效, 错误信息列表, 修复后的文件路径(如果修复))
    """
    if not os.path.exists(file_path):
        return False, [f"文件不存在: {file_path}"], None
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 判断文件格式（JSON或JSONL）
        is_jsonl = '\n' in content.strip() and content.strip()[0] == '{'
        
        if is_jsonl:
            # JSONL格式，逐行解析
            samples = []
            for i, line in enumerate(content.strip().split('\n')):
                if not line.strip():
                    continue
                try:
                    sample = json.loads(line)
                    samples.append(sample)
                except json.JSONDecodeError as e:
                    return False, [f"第 {i+1} 行解析失败: {e}"], None
            
            # 验证所有样本
            valid, errors, fixed_samples = validate_xpert_format(samples)
        else:
            # JSON格式，整体解析
            try:
                data = json.loads(content)
                valid, errors, fixed_samples = validate_xpert_format(data)
            except json.JSONDecodeError as e:
                return False, [f"JSON解析失败: {e}"], None
        
        # 如果需要修复并保存
        if fix and not valid and fixed_samples:
            fixed_file_path = f"{os.path.splitext(file_path)[0]}_fixed.jsonl"
            
            with open(fixed_file_path, 'w', encoding='utf-8') as f:
                if isinstance(fixed_samples, list):
                    for sample in fixed_samples:
                        f.write(json.dumps(sample, ensure_ascii=False) + '\n')
                else:
                    f.write(json.dumps(fixed_samples, ensure_ascii=False))
            
            logger.info(f"已修复并保存到: {fixed_file_path}")
            return valid, errors, fixed_file_path
        
        return valid, errors, None
    
    except Exception as e:
        return False, [f"验证文件时发生错误: {e}"], None 