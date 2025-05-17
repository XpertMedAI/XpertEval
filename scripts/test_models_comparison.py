 #!/usr/bin/env python
# coding: utf-8
"""
多模型对比测试脚本

该脚本使用config.yaml配置文件，测试多个大模型的响应，并进行简单对比。
"""

import os
import sys
import yaml
import json
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xperteval.core import invoke_model_api, ApiError
from xperteval.config import load_model_configs

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
CONFIG_EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config_example.yaml")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# 测试问题列表
TEST_QUESTIONS = [
    "你好，请用中文简短地介绍一下你自己",
    "简要介绍一下中医药的特点和优势",
    "脉搏跳动无力，舌苔厚白，是什么症状？",
    "如何缓解工作压力和焦虑情绪？"
]

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

def ensure_results_dir():
    """确保结果目录存在"""
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"已创建结果目录: {RESULTS_DIR}")

def format_time_ms(seconds):
    """将秒数格式化为毫秒"""
    return f"{seconds*1000:.2f}ms"

def test_models_comparison():
    """测试多个模型并进行对比"""
    try:
        # 确保结果目录存在
        ensure_results_dir()
        
        # 加载配置
        config = load_model_configs(CONFIG_PATH)
        models = config['models']
        print(f"成功加载配置文件，共有 {len(models)} 个模型配置")
        
        # 创建结果文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(RESULTS_DIR, f"model_comparison_{timestamp}.md")
        
        # 初始化结果统计
        results = {
            "timestamp": timestamp,
            "models": [],
            "questions": TEST_QUESTIONS,
            "responses": {},
            "performance": {}
        }
        
        for model_config in models:
            model_name = model_config['MODEL_NAME']
            model_api = model_config['OPENAI_API_BASE']
            print(f"\n正在测试模型: {model_name} (API基址: {model_api})")
            
            # 记录模型信息
            results["models"].append({
                "name": model_name,
                "api_base": model_api,
                "type": model_config['MODEL_TYPE'].value if hasattr(model_config['MODEL_TYPE'], 'value') else model_config['MODEL_TYPE'],
                "is_main": model_config.get('MAIN_API', False)
            })
            
            # 初始化该模型的响应
            results["responses"][model_name] = {}
            results["performance"][model_name] = {
                "total_time": 0,
                "total_tokens": 0,
                "avg_time_per_token": 0
            }
            
            # 遍历测试问题
            for i, question in enumerate(TEST_QUESTIONS):
                print(f"  问题 {i+1}/{len(TEST_QUESTIONS)}: {question[:30]}...")
                
                # 构建请求负载
                request_payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                
                # 记录开始时间
                start_time = time.time()
                
                # 调用API
                try:
                    response = invoke_model_api(model_config, request_payload)
                    
                    # 计算耗时
                    elapsed_time = time.time() - start_time
                    results["performance"][model_name]["total_time"] += elapsed_time
                    
                    # 提取答案和Token使用情况
                    answer = "无法提取回答"
                    if 'choices' in response and len(response['choices']) > 0:
                        if 'message' in response['choices'][0]:
                            answer = response['choices'][0]['message'].get('content', '无内容')
                    
                    # 记录Token使用情况
                    tokens_used = 0
                    if 'usage' in response:
                        tokens_used = response['usage'].get('total_tokens', 0)
                        results["performance"][model_name]["total_tokens"] += tokens_used
                    
                    print(f"    ✓ 回答长度: {len(answer)} 字符, 耗时: {format_time_ms(elapsed_time)}, Tokens: {tokens_used}")
                    
                    # 保存响应
                    results["responses"][model_name][f"question_{i+1}"] = {
                        "question": question,
                        "answer": answer,
                        "elapsed_time": elapsed_time,
                        "tokens": tokens_used,
                        "full_response": response
                    }
                    
                except ApiError as e:
                    print(f"    ✗ 调用失败: {e}")
                    results["responses"][model_name][f"question_{i+1}"] = {
                        "question": question,
                        "answer": f"错误: {str(e)}",
                        "elapsed_time": time.time() - start_time,
                        "tokens": 0,
                        "error": str(e)
                    }
            
            # 计算平均值
            total_time = results["performance"][model_name]["total_time"]
            total_tokens = results["performance"][model_name]["total_tokens"]
            if total_tokens > 0:
                avg_time_per_token = total_time / total_tokens
                results["performance"][model_name]["avg_time_per_token"] = avg_time_per_token
                print(f"  总耗时: {total_time:.2f}秒, 总Tokens: {total_tokens}, 平均每Token耗时: {format_time_ms(avg_time_per_token)}")
        
        # 生成结果报告
        with open(result_file, 'w', encoding='utf-8') as f:
            # 写入标题
            f.write(f"# 模型对比测试报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 写入模型信息
            f.write("## 测试模型\n\n")
            f.write("| 模型名称 | API基址 | 类型 | 是否主模型 |\n")
            f.write("|---------|---------|------|------------|\n")
            for model in results["models"]:
                is_main = "是" if model["is_main"] else "否"
                f.write(f"| {model['name']} | {model['api_base']} | {model['type']} | {is_main} |\n")
            
            # 写入性能统计
            f.write("\n## 性能统计\n\n")
            f.write("| 模型名称 | 总耗时(秒) | 总Tokens | 平均每Token耗时(ms) |\n")
            f.write("|---------|------------|----------|--------------------|\n")
            for model_name, perf in results["performance"].items():
                avg_time = perf.get("avg_time_per_token", 0) * 1000  # 转换为毫秒
                f.write(f"| {model_name} | {perf['total_time']:.2f} | {perf['total_tokens']} | {avg_time:.2f} |\n")
            
            # 写入每个问题的对比
            for i, question in enumerate(TEST_QUESTIONS):
                f.write(f"\n## 问题 {i+1}: {question}\n\n")
                
                for model_name in [m["name"] for m in results["models"]]:
                    response_data = results["responses"][model_name].get(f"question_{i+1}", {})
                    answer = response_data.get("answer", "未获取到回答")
                    elapsed_time = response_data.get("elapsed_time", 0)
                    tokens = response_data.get("tokens", 0)
                    
                    f.write(f"### {model_name}\n\n")
                    f.write(f"**耗时**: {elapsed_time:.2f}秒 | **Tokens**: {tokens}\n\n")
                    f.write(f"**回答**:\n\n{answer}\n\n")
        
        # 保存完整JSON结果
        json_result_file = os.path.join(RESULTS_DIR, f"model_comparison_{timestamp}.json")
        with open(json_result_file, 'w', encoding='utf-8') as f:
            # 对于无法序列化的对象，需要进行处理
            cleaned_results = results.copy()
            for model_name in cleaned_results["responses"]:
                for q_id in cleaned_results["responses"][model_name]:
                    # 确保可以序列化
                    if "full_response" in cleaned_results["responses"][model_name][q_id]:
                        try:
                            # 尝试将full_response转为JSON字符串，然后再还原为dict
                            json_str = json.dumps(cleaned_results["responses"][model_name][q_id]["full_response"])
                            cleaned_results["responses"][model_name][q_id]["full_response"] = json.loads(json_str)
                        except:
                            # 如果失败，则移除无法序列化的部分
                            del cleaned_results["responses"][model_name][q_id]["full_response"]
            
            json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试完成!")
        print(f"Markdown报告已保存至: {result_file}")
        print(f"JSON数据已保存至: {json_result_file}")
        
        return True
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("===== XpertEval 多模型对比测试 =====")
    
    if not ensure_config_exists():
        sys.exit(1)
    
    print("\n正在开始多模型对比测试...")
    if test_models_comparison():
        print("\n✅ 测试完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)