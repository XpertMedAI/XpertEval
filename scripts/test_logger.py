#!/usr/bin/env python
# coding: utf-8
"""
日志功能测试脚本

测试日志模块的各种功能，包括：
1. 彩色控制台输出
2. 日志级别
3. 文件记录
4. 不同日志器实例
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xperteval.utils import get_logger, setup_logger

def test_basic_logging():
    """测试基本日志功能"""
    print("1. 测试基本日志功能（默认配置）:")
    
    # 获取默认日志器
    logger = get_logger("test_basic")
    
    # 测试不同级别的日志
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
    
    print("\n日志已输出到控制台和 logs/xperteval.log 文件\n")

def test_different_loggers():
    """测试不同日志器实例"""
    print("2. 测试不同日志器实例:")
    
    # 创建两个不同的日志器
    logger1 = get_logger("test_module1")
    logger2 = get_logger("test_module2")
    
    # 输出日志
    logger1.info("这条日志来自test_module1")
    logger2.info("这条日志来自test_module2")
    
    print("\n两个不同日志器的日志已显示\n")

def test_log_levels():
    """测试日志级别过滤"""
    print("3. 测试日志级别过滤:")
    
    # 创建一个DEBUG级别的日志器
    debug_logger = setup_logger("test_debug", level=10)  # DEBUG=10
    
    # 创建一个WARNING级别的日志器
    warning_logger = setup_logger("test_warning", level=30)  # WARNING=30
    
    # 输出不同级别的日志
    print("DEBUG级别的日志器应该显示所有日志:")
    debug_logger.debug("DEBUG消息")
    debug_logger.info("INFO消息")
    debug_logger.warning("WARNING消息")
    
    print("\nWARNING级别的日志器应该只显示WARNING及以上级别的日志:")
    warning_logger.debug("DEBUG消息 - 不应显示")
    warning_logger.info("INFO消息 - 不应显示")
    warning_logger.warning("WARNING消息 - 应该显示")
    warning_logger.error("ERROR消息 - 应该显示")
    
    print("\n日志级别测试完成\n")

def test_file_rotation():
    """测试日志文件轮转（实际上这需要等待一天才能看到效果）"""
    print("4. 设置了日志文件轮转 (每天午夜轮转):")
    
    log_dir = "logs/test_rotation"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    rotation_logger = setup_logger(
        "test_rotation", 
        log_dir=log_dir, 
        log_file="rotation_test.log"
    )
    
    rotation_logger.info(f"这条日志应该写入到 {log_dir}/rotation_test.log 文件")
    rotation_logger.info("每天午夜，日志文件将会轮转，备份文件名格式为: rotation_test.YYYYMMDD.log")
    
    print(f"\n日志文件已创建在 {os.path.abspath(log_dir)}/rotation_test.log\n")

def test_exception_logging():
    """测试异常日志"""
    print("5. 测试异常日志记录:")
    
    exception_logger = get_logger("test_exception")
    
    try:
        # 制造一个除以零错误
        result = 1 / 0
    except Exception as e:
        # 记录异常及堆栈跟踪
        exception_logger.error("发生了一个错误", exc_info=True)
        # 更简洁的写法
        exception_logger.exception("使用exception()方法记录异常")
    
    print("\n异常日志测试完成，请查看日志文件了解完整堆栈跟踪\n")

if __name__ == "__main__":
    print("===== XpertEval 日志功能测试 =====\n")
    
    # 执行测试
    test_basic_logging()
    test_different_loggers()
    test_log_levels()
    test_file_rotation()
    test_exception_logging()
    
    print("所有日志功能测试完成!")
    print("请检查控制台输出的颜色是否正确，以及logs目录下的日志文件") 