"""
EduBuddy - 教育助手应用

一个功能丰富的教育助手应用，包含日志记录、时间管理等功能。
"""

__version__ = "0.1.0"
__author__ = "Mason"
__email__ = "mason@example.com"

from .logger import logger
from .time_service import TimeService, create_time_service
from .version import get_version_info

__all__ = ["logger", "TimeService", "create_time_service", "get_version_info"]
