# coding: utf-8
"""
评测核心逻辑 - 自动化评测引擎

本模块实现自动化评测引擎，负责协调数据集加载、模型调用、评测指标计算和结果汇总。
"""

import time
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..datasets.base_dataset import BaseDataset
from ..core.base_evaluator import BaseEvaluator
from ..core.api_caller import invoke_model_api, ApiError
from ..utils import get_logger

# 配置日志
logger = get_logger(__name__)


class AutoEvalEngine:
    """
    自动化评测引擎
    
    负责协调数据集加载、模型调用、评测指标计算和结果汇总。
    """
    
    def __init__(
        self, 
        model_configs: List[Dict[str, Any]], 
        dataset: BaseDataset, 
        evaluators: List[BaseEvaluator],
        max_workers: int = 1,
        save_predictions: bool = True,
        output_dir: Optional[str] = None
    ):
        """
        初始化评测引擎
        
        Args:
            model_configs: 模型配置列表，每个配置是一个字典
            dataset: 数据集实例
            evaluators: 评测器实例列表
            max_workers: 最大并行工作线程数（用于并行调用API）
            save_predictions: 是否保存预测结果
            output_dir: 输出目录，如果为None则使用默认目录
        """
        # 验证模型配置
        if not model_configs or len(model_configs) < 2:
            raise ValueError("至少需要提供两个有效的模型配置")
        
        self.model_configs = model_configs
        self.dataset = dataset
        self.evaluators = evaluators
        self.max_workers = max_workers
        self.save_predictions = save_predictions
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("results") / time.strftime("%Y%m%d-%H%M%S")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化结果存储
        self.results = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataset": dataset.get_metadata(),
                "models": [self._get_model_public_info(config) for config in model_configs],
                "evaluators": [evaluator.name for evaluator in evaluators]
            },
            "model_results": {},
            "sample_results": []
        }
        
        logger.info(f"初始化自动化评测引擎完成，将使用{len(evaluators)}个评测器对{len(model_configs)}个模型进行评测")
    
    def _get_model_public_info(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取模型的公开信息（排除敏感信息如API密钥）
        
        Args:
            model_config: 模型配置字典
            
        Returns:
            包含模型公开信息的字典
        """
        return {
            "MODEL_NAME": model_config.get("MODEL_NAME", "unknown"),
            "MODEL_TYPE": model_config.get("MODEL_TYPE", "text"),
            "MAIN_API": model_config.get("MAIN_API", False),
            "OPENAI_API_BASE": model_config.get("OPENAI_API_BASE", "").split("://")[-1].split("/")[0]  # 只保留域名部分
        }
    
    def _construct_request_payload(self, sample: Dict[str, Any], model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据样本内容和模型类型构造API请求负载
        
        Args:
            sample: 数据集样本
            model_config: 模型配置
            
        Returns:
            API请求负载字典
        """
        model_type = model_config.get("MODEL_TYPE", "text")
        model_name = model_config.get("MODEL_NAME", "unknown")
        
        # 基础请求参数
        payload = {
            "model": model_name,
            "max_tokens": int(model_config.get("MAX_TOKENS", 4096)),
            "temperature": float(model_config.get("TEMPERATURE", 0.7)),
            "top_p": float(model_config.get("TOP_P", 0.95)),
            "frequency_penalty": float(model_config.get("FREQUENCY_PENALTY", 0.0)),
            "presence_penalty": float(model_config.get("PRESENCE_PENALTY", 0.0))
        }
        
        # 构造消息内容
        messages = []
        
        # 系统提示（如果存在）
        if "system" in sample:
            messages.append({
                "role": "system",
                "content": sample["system"]
            })
        
        # 处理历史对话（如果存在）
        if "history" in sample and isinstance(sample["history"], list):
            for turn in sample["history"]:
                if isinstance(turn, dict) and "role" in turn and "content" in turn:
                    messages.append(turn)
        
        # 添加当前查询
        content = []
        
        # 处理文本查询
        if "query" in sample:
            content.append({
                "type": "text",
                "text": sample["query"]
            })
        
        # 处理图像（如果存在且模型支持）
        if "image" in sample and model_type in ["vision", "mllm"]:
            image_path = sample.get("image")
            if image_path and isinstance(image_path, str):
                # 这里应该处理图像URL或base64编码
                # 实际实现中可能需要根据API要求进行调整
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_path}
                })
        
        # 处理音频（如果存在且模型支持）
        if "audio" in sample and model_type in ["audio", "mllm"]:
            audio_path = sample.get("audio")
            if audio_path and isinstance(audio_path, str):
                # 这里应该处理音频URL或base64编码
                # 实际实现中可能需要根据API要求进行调整
                content.append({
                    "type": "audio",
                    "audio_url": audio_path
                })
        
        # 如果只有文本内容，简化为字符串
        if len(content) == 1 and content[0]["type"] == "text":
            user_content = content[0]["text"]
        else:
            user_content = content
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        payload["messages"] = messages
        
        return payload
    
    def _call_model_api(self, model_config: Dict[str, Any], sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用模型API并处理响应
        
        Args:
            model_config: 模型配置
            sample: 数据集样本
            
        Returns:
            包含API调用结果的字典
        """
        model_name = model_config.get("MODEL_NAME", "unknown")
        
        try:
            # 构造请求负载
            request_payload = self._construct_request_payload(sample, model_config)
            
            # 记录API调用开始时间
            start_time = time.time()
            
            # 调用API
            response = invoke_model_api(model_config, request_payload)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            # 提取生成的文本
            generated_text = ""
            if "choices" in response and len(response["choices"]) > 0:
                message = response["choices"][0].get("message", {})
                if isinstance(message.get("content"), str):
                    generated_text = message["content"]
            
            # 提取token使用信息
            token_usage = response.get("usage", {})
            
            result = {
                "success": True,
                "prediction": generated_text,
                "elapsed_time": elapsed_time,
                "token_usage": token_usage
            }
            
            logger.debug(f"模型 {model_name} 成功生成回答，长度: {len(generated_text)} 字符")
            
            return result
            
        except ApiError as e:
            logger.error(f"模型 {model_name} API调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prediction": "",
                "elapsed_time": 0,
                "token_usage": {}
            }
        except Exception as e:
            logger.error(f"模型 {model_name} 调用过程中发生未知错误: {str(e)}")
            logger.debug(f"错误详情: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "prediction": "",
                "elapsed_time": 0,
                "token_usage": {}
            }
    
    def _process_sample(self, sample_idx: int) -> Dict[str, Any]:
        """
        处理单个样本的评测
        
        Args:
            sample_idx: 样本索引
            
        Returns:
            样本评测结果字典
        """
        sample = self.dataset[sample_idx]
        sample_id = sample.get("id", str(sample_idx))
        
        logger.info(f"处理样本 {sample_id} ({sample_idx+1}/{len(self.dataset)})")
        
        # 存储该样本的所有模型预测结果
        model_predictions = {}
        
        # 对每个模型进行预测
        for model_config in self.model_configs:
            model_name = model_config.get("MODEL_NAME", "unknown")
            model_predictions[model_name] = self._call_model_api(model_config, sample)
        
        # 检查是否有足够的成功预测结果进行评测
        successful_models = [model_name for model_name, result in model_predictions.items() 
                            if result["success"]]
        
        if len(successful_models) < 2:
            logger.warning(f"样本 {sample_id} 没有足够的成功预测结果进行评测，跳过")
            return {
                "sample_id": sample_id,
                "sample_idx": sample_idx,
                "model_predictions": model_predictions,
                "evaluations": {},
                "skipped": True,
                "reason": "没有足够的成功预测结果"
            }
        
        # 对每个评测器进行评测
        evaluations = {}
        for evaluator in self.evaluators:
            try:
                # 准备预测结果和参考答案
                predictions = []
                references = []
                
                for model_name, result in model_predictions.items():
                    if result["success"]:
                        predictions.append(result["prediction"])
                        references.append(sample)  # 每个模型使用相同的参考答案
                
                # 执行评测
                eval_result = evaluator.evaluate(predictions, references)
                
                # 将评测结果与模型名称关联
                model_scores = {}
                for i, model_name in enumerate(successful_models):
                    model_scores[model_name] = eval_result.get("individual_scores", [])[i] if i < len(eval_result.get("individual_scores", [])) else None
                
                evaluations[evaluator.name] = {
                    "aggregate": eval_result.get("aggregate", {}),
                    "model_scores": model_scores
                }
                
            except Exception as e:
                logger.error(f"评测器 {evaluator.name} 在样本 {sample_id} 上发生错误: {str(e)}")
                logger.debug(f"错误详情: {traceback.format_exc()}")
                evaluations[evaluator.name] = {
                    "error": str(e)
                }
        
        # 返回样本评测结果
        return {
            "sample_id": sample_id,
            "sample_idx": sample_idx,
            "model_predictions": model_predictions,
            "evaluations": evaluations,
            "skipped": False
        }
    
    def run_evaluation(self, sample_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        运行评测流程
        
        Args:
            sample_indices: 要评测的样本索引列表，如果为None则评测所有样本
            
        Returns:
            评测结果字典
        """
        logger.info(f"开始评测，数据集大小: {len(self.dataset)}，模型数量: {len(self.model_configs)}，评测器数量: {len(self.evaluators)}")
        
        # 确定要评测的样本索引
        if sample_indices is None:
            sample_indices = list(range(len(self.dataset)))
        
        total_samples = len(sample_indices)
        logger.info(f"将评测 {total_samples} 个样本")
        
        # 初始化模型结果字典
        for model_config in self.model_configs:
            model_name = model_config.get("MODEL_NAME", "unknown")
            self.results["model_results"][model_name] = {
                "is_main_api": model_config.get("MAIN_API", False),
                "success_count": 0,
                "total_tokens": 0,
                "total_time": 0.0,
                "evaluator_scores": {}
            }
        
        # 评测开始时间
        start_time = time.time()
        
        # 处理每个样本
        if self.max_workers > 1:
            # 并行处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_idx = {executor.submit(self._process_sample, idx): idx for idx in sample_indices}
                for future in as_completed(future_to_idx):
                    sample_result = future.result()
                    self.results["sample_results"].append(sample_result)
                    self._update_model_results(sample_result)
        else:
            # 串行处理
            for idx in sample_indices:
                sample_result = self._process_sample(idx)
                self.results["sample_results"].append(sample_result)
                self._update_model_results(sample_result)
        
        # 计算总评测时间
        total_time = time.time() - start_time
        self.results["metadata"]["total_time"] = total_time
        
        # 计算最终汇总分数
        self._calculate_final_scores()
        
        # 保存结果
        self._save_results()
        
        logger.info(f"评测完成，总耗时: {total_time:.2f}秒")
        
        return self.results
    
    def _update_model_results(self, sample_result: Dict[str, Any]) -> None:
        """
        更新模型结果统计
        
        Args:
            sample_result: 单个样本的评测结果
        """
        if sample_result.get("skipped", False):
            return
        
        # 更新模型统计信息
        model_predictions = sample_result.get("model_predictions", {})
        for model_name, prediction in model_predictions.items():
            if model_name in self.results["model_results"]:
                model_result = self.results["model_results"][model_name]
                
                # 更新成功计数
                if prediction.get("success", False):
                    model_result["success_count"] += 1
                
                # 更新token使用量
                token_usage = prediction.get("token_usage", {})
                total_tokens = token_usage.get("total_tokens", 0)
                model_result["total_tokens"] += total_tokens
                
                # 更新总耗时
                model_result["total_time"] += prediction.get("elapsed_time", 0.0)
        
        # 更新评测器分数
        evaluations = sample_result.get("evaluations", {})
        for evaluator_name, evaluation in evaluations.items():
            model_scores = evaluation.get("model_scores", {})
            
            for model_name, score in model_scores.items():
                if model_name in self.results["model_results"]:
                    model_result = self.results["model_results"][model_name]
                    
                    # 初始化评测器分数列表（如果不存在）
                    if evaluator_name not in model_result["evaluator_scores"]:
                        model_result["evaluator_scores"][evaluator_name] = []
                    
                    # 添加分数（如果有效）
                    if score is not None:
                        model_result["evaluator_scores"][evaluator_name].append(score)
    
    def _calculate_final_scores(self) -> None:
        """
        计算最终汇总分数
        """
        # 对每个模型计算平均分数
        for model_name, model_result in self.results["model_results"].items():
            # 计算每个评测器的平均分数
            final_scores = {}
            for evaluator_name, scores in model_result["evaluator_scores"].items():
                if scores:
                    final_scores[evaluator_name] = {
                        "mean": sum(scores) / len(scores),
                        "min": min(scores),
                        "max": max(scores),
                        "count": len(scores)
                    }
                else:
                    final_scores[evaluator_name] = {
                        "mean": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "count": 0
                    }
            
            model_result["final_scores"] = final_scores
            
            # 计算平均耗时和成功率
            total_samples = len(self.results["sample_results"])
            if total_samples > 0:
                model_result["success_rate"] = model_result["success_count"] / total_samples
                if model_result["success_count"] > 0:
                    model_result["avg_time_per_sample"] = model_result["total_time"] / model_result["success_count"]
                    model_result["avg_tokens_per_sample"] = model_result["total_tokens"] / model_result["success_count"]
    
    def _save_results(self) -> None:
        """
        保存评测结果
        """
        if not self.save_predictions:
            # 如果不保存预测结果，则从结果中移除详细的预测内容
            for sample_result in self.results["sample_results"]:
                for model_name, prediction in sample_result.get("model_predictions", {}).items():
                    if "prediction" in prediction:
                        # 只保留预测长度，不保存完整内容
                        prediction["prediction_length"] = len(prediction["prediction"])
                        del prediction["prediction"]
        
        # 保存结果到JSON文件
        results_file = self.output_dir / "evaluation_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评测结果已保存到: {results_file}")
        
        # 保存简要结果到单独文件（便于快速查看）
        summary = {
            "metadata": self.results["metadata"],
            "model_results": {}
        }
        
        for model_name, model_result in self.results["model_results"].items():
            summary["model_results"][model_name] = {
                "is_main_api": model_result["is_main_api"],
                "success_rate": model_result.get("success_rate", 0),
                "avg_time_per_sample": model_result.get("avg_time_per_sample", 0),
                "avg_tokens_per_sample": model_result.get("avg_tokens_per_sample", 0),
                "final_scores": model_result.get("final_scores", {})
            }
        
        summary_file = self.output_dir / "evaluation_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评测摘要已保存到: {summary_file}") 