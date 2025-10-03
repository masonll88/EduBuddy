"""
通用日志工具模块

提供通用的日志记录功能，支持定时任务和自定义日志处理。
封装loguru，为其他模块提供统一的日志接口。
"""

import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

from loguru import logger as _loguru_logger


# 封装loguru，提供统一的日志接口
class Logger:
    """统一的日志接口类 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._setup_logger()
            Logger._initialized = True

    def _setup_logger(self) -> None:
        """设置日志配置"""
        _loguru_logger.remove()  # 移除默认处理器
        _loguru_logger.add(
            sink=lambda msg: print(msg, end=""),  # 直接打印到控制台
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO",
        )

    def info(self, message: str) -> None:
        """记录信息日志"""
        _loguru_logger.info(message)

    def warning(self, message: str) -> None:
        """记录警告日志"""
        _loguru_logger.warning(message)

    def error(self, message: str) -> None:
        """记录错误日志"""
        _loguru_logger.error(message)

    def debug(self, message: str) -> None:
        """记录调试日志"""
        _loguru_logger.debug(message)

    def critical(self, message: str) -> None:
        """记录严重错误日志"""
        _loguru_logger.critical(message)


# 创建全局日志实例（单例）
logger = Logger()
