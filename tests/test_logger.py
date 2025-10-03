"""
测试日志模块

测试Logger单例模式和TimeService功能。
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from edubuddy.logger import Logger
from edubuddy.time_service import TimeService, create_time_service


class TestLogger:
    """Logger单例测试类"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_logger_methods(self):
        """测试日志方法"""
        logger = Logger()

        # 测试所有日志级别方法存在
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "critical")

        # 测试方法可调用
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)
        assert callable(logger.debug)
        assert callable(logger.critical)


class TestTimeService:
    """时间服务测试类"""

    def test_init(self):
        """测试初始化"""
        service = TimeService(interval=2.0, format_str="%H:%M:%S")
        assert service.interval == 2.0
        assert service.format_str == "%H:%M:%S"
        assert not service.is_time_logging_running()

    def test_default_init(self):
        """测试默认初始化"""
        service = TimeService()
        assert service.interval == 4.0
        assert service.format_str == "%Y-%m-%d %H:%M:%S"
        assert not service.is_time_logging_running()

    def test_start_stop_logging(self):
        """测试启动和停止日志记录"""
        service = TimeService(interval=0.1)
        service.start_time_logging()
        assert service.is_time_logging_running()

        time.sleep(0.2)
        service.stop_time_logging()
        assert not service.is_time_logging_running()

    def test_set_interval(self):
        """测试设置间隔"""
        service = TimeService()
        service.set_interval(2.5)
        assert service.interval == 2.5

    def test_set_interval_invalid(self):
        """测试设置无效间隔"""
        service = TimeService()
        with pytest.raises(ValueError):
            service.set_interval(0)
        with pytest.raises(ValueError):
            service.set_interval(-1)

    def test_set_format(self):
        """测试设置格式"""
        service = TimeService()
        new_format = "%H:%M:%S"
        service.set_format(new_format)
        assert service.format_str == new_format

    @patch("edubuddy.time_service.logger")
    def test_log_time_format(self, mock_logger):
        """测试时间格式"""
        service = TimeService(interval=0.1)
        service.start_time_logging()
        time.sleep(0.2)
        service.stop_time_logging()

        # 验证日志被调用
        assert mock_logger.info.called

    def test_double_start(self):
        """测试重复启动"""
        service = TimeService(interval=0.1)
        service.start_time_logging()
        assert service.is_time_logging_running()

        # 再次启动应该显示警告
        with patch("edubuddy.time_service.logger") as mock_logger:
            service.start_time_logging()
            mock_logger.warning.assert_called_with("时间服务已经在运行中")

        service.stop_time_logging()

    def test_stop_when_not_running(self):
        """测试在未运行时停止"""
        service = TimeService()

        with patch("edubuddy.time_service.logger") as mock_logger:
            service.stop_time_logging()
            mock_logger.warning.assert_called_with("时间服务未在运行")

    def test_create_time_service(self):
        """测试创建时间服务工厂函数"""
        service = create_time_service(interval=3.0, format_str="%H:%M:%S")
        assert isinstance(service, TimeService)
        assert service.interval == 3.0
        assert service.format_str == "%H:%M:%S"
