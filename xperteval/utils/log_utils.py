# coding: utf-8
"""
通用工具函数 - 日志配置与记录
提供统一的日志记录功能，包括彩色控制台输出和日志文件轮转
"""

import os
import sys
import logging
import platform
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


# ANSI颜色代码
class Colors:
    """ANSI颜色代码"""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def use_colors():
        """检查当前环境是否应该使用颜色"""
        # Windows下需要特殊处理
        if platform.system() == "Windows":
            # 检查是否在支持ANSI的终端中运行
            return os.environ.get("TERM") is not None or os.environ.get("WT_SESSION") is not None
        # Unix类系统（Linux/MacOS）一般支持
        return sys.stdout.isatty()


class ColoredFormatter(logging.Formatter):
    """自定义彩色日志格式化器"""
    
    # 根据日志级别定义颜色
    COLORS = {
        logging.DEBUG: Colors.BLUE,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }
    
    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        """初始化格式化器"""
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and Colors.use_colors()
    
    def format(self, record):
        """对日志记录进行格式化，添加颜色标记"""
        # 保存原始消息
        message = record.getMessage()
        levelname = record.levelname
        
        # 如果要使用颜色，且当前环境支持
        if self.use_colors:
            color = self.COLORS.get(record.levelno, Colors.RESET)
            # 只对级别名称添加颜色
            record.levelname = f"{color}{levelname}{Colors.RESET}"
        
        # 使用基类格式化日志
        result = super().format(record)
        
        # 恢复原始记录
        record.message = message
        record.levelname = levelname
        
        return result


def setup_logger(name=None, level=logging.INFO, log_dir="logs", log_file="xperteval.log", 
                console=True, file=True, colored=True, propagate=False):
    """
    设置并返回配置好的logger
    
    Args:
        name: 日志器名称，默认为根日志器
        level: 日志级别，默认为INFO
        log_dir: 日志文件目录，默认为logs
        log_file: 日志文件名，默认为xperteval.log
        console: 是否输出到控制台，默认为True
        file: 是否输出到文件，默认为True
        colored: 是否在控制台使用颜色，默认为True
        propagate: 是否传播到父日志器，默认为False
    
    Returns:
        logging.Logger: 配置好的日志器实例
    """
    # 获取日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate
    
    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger
    
    # 创建格式化器
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 创建控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        if colored:
            console_formatter = ColoredFormatter(log_format, date_format)
        else:
            console_formatter = logging.Formatter(log_format, date_format)
            
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 创建文件处理器
    if file:
        # 确保日志目录存在
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建TimedRotatingFileHandler，按天轮转，保留30天的日志
        file_path = log_path / log_file
        file_handler = TimedRotatingFileHandler(
            filename=file_path,
            when="midnight",
            interval=1,
            backupCount=30
        )
        file_handler.suffix = "%Y%m%d.log"
        file_handler.setLevel(level)
        
        # 文件日志不使用颜色
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None, level=None):
    """
    获取已配置的日志器，如未配置则创建
    
    Args:
        name: 日志器名称，默认为调用者模块名
        level: 日志级别，默认使用环境变量或INFO
    
    Returns:
        logging.Logger: 日志器实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'xperteval')
    
    # 从环境变量获取日志级别，默认为INFO
    if level is None:
        level_name = os.environ.get("XPERTEVAL_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
    
    # 检查是否已有同名日志器
    logger = logging.getLogger(name)
    
    # 如果没有处理器，设置日志器
    if not logger.handlers:
        logger = setup_logger(name, level)
    
    return logger 