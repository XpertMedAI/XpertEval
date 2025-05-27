#!/usr/bin/env python
# coding: utf-8
"""
运行评测器相关的所有测试
"""

import os
import sys
import unittest
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(test_type="all", verbose=False):
    """
    运行评测器相关的测试
    
    Args:
        test_type: 测试类型，可选值为 "unit"（单元测试）, "integration"（集成测试）或 "all"（所有测试）
        verbose: 是否显示详细输出
    
    Returns:
        测试结果，True表示所有测试通过，False表示有测试失败
    """
    verbosity = "-v" if verbose else ""
    success = True
    
    if test_type in ["unit", "all"]:
        # 运行单元测试
        print("运行评测器单元测试...")
        cmd = [sys.executable, "-m", "unittest", verbosity, "tests.unit.test_evaluators"]
        result = subprocess.run(cmd, cwd=str(project_root))
        if result.returncode != 0:
            success = False
    
    if test_type in ["integration", "all"]:
        # 运行集成测试
        print("运行评测器集成测试...")
        cmd = [sys.executable, "-m", "unittest", verbosity, "tests.integration.test_evaluators_integration"]
        result = subprocess.run(cmd, cwd=str(project_root))
        if result.returncode != 0:
            success = False
    
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行评测器相关的测试")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="指定要运行的测试类型: unit（单元测试）, integration（集成测试）或 all（所有测试）"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="显示详细的测试输出"
    )
    
    args = parser.parse_args()
    success = run_tests(test_type=args.type, verbose=args.verbose)
    
    # 根据测试结果设置退出码
    if success:
        print("所有测试通过！")
        sys.exit(0)
    else:
        print("测试失败！")
        sys.exit(1) 