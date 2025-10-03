"""
时间服务模块

实现时间相关的业务逻辑，整合周期性日志记录功能。
"""

import threading
import time
from datetime import datetime
from typing import Callable, Optional

from .logger import logger


class TimeService:
    """时间服务类 - 整合周期性日志记录功能"""

    def __init__(self, interval: float = 4.0, format_str: Optional[str] = None):
        """
        初始化时间服务

        Args:
            interval: 时间日志间隔（秒），默认4秒
            format_str: 时间格式字符串，默认使用ISO格式
        """
        self.interval = interval
        self.format_str = format_str or "%Y-%m-%d %H:%M:%S"
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _get_current_time_message(self) -> str:
        """获取当前时间消息"""
        current_time = datetime.now().strftime(self.format_str)
        return f"当前时间: {current_time}"

    def _log_worker(self) -> None:
        """日志工作线程"""
        while not self._stop_event.is_set():
            try:
                log_message = self._get_current_time_message()
                logger.info(log_message)
            except Exception as e:
                logger.error(f"时间日志记录错误: {e}")

            # 等待指定间隔或直到停止事件被设置
            if self._stop_event.wait(self.interval):
                break

    def start_time_logging(self) -> None:
        """开始时间日志记录"""
        if self._running:
            logger.warning("时间服务已经在运行中")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._log_worker, daemon=True)
        self._thread.start()
        logger.info(f"时间服务已启动，间隔: {self.interval}秒")

    def stop_time_logging(self) -> None:
        """停止时间日志记录"""
        if not self._running:
            logger.warning("时间服务未在运行")
            return

        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._running = False
        logger.info("时间服务已停止")

    def is_time_logging_running(self) -> bool:
        """检查时间日志记录是否正在运行"""
        return self._running

    def set_interval(self, interval: float) -> None:
        """
        设置时间日志间隔

        Args:
            interval: 新的间隔时间（秒）
        """
        if interval <= 0:
            raise ValueError("间隔时间必须大于0")

        self.interval = interval
        logger.info(f"时间日志间隔已更新为: {interval}秒")

    def set_format(self, format_str: str) -> None:
        """
        设置时间格式

        Args:
            format_str: 新的时间格式字符串
        """
        self.format_str = format_str
        logger.info(f"时间格式已更新为: {format_str}")


def create_time_service(
    interval: float = 4.0, format_str: Optional[str] = None
) -> TimeService:
    """
    创建时间服务的工厂函数

    Args:
        interval: 时间日志间隔（秒）
        format_str: 时间格式字符串

    Returns:
        TimeService实例
    """
    return TimeService(interval=interval, format_str=format_str)
