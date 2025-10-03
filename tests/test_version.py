"""
版本管理测试模块
"""

import importlib.metadata
import sys
from unittest.mock import MagicMock, patch

import pytest

from edubuddy.version import (
    VersionManager,
    get_version,
    get_version_info,
    print_version_info,
)


class TestVersionFunctions:
    """版本函数测试类"""

    @patch("edubuddy.version.importlib.metadata.version")
    def test_get_version_from_metadata(self, mock_version):
        """测试从元数据获取版本"""
        mock_version.return_value = "1.2.3"
        version = get_version()
        assert version == "1.2.3"

    @patch("edubuddy.version.importlib.metadata.version")
    @patch("edubuddy.version.__version__", "0.1.0")
    def test_get_version_fallback(self, mock_version):
        """测试版本获取回退机制"""
        mock_version.side_effect = importlib.metadata.PackageNotFoundError()

        with patch("edubuddy.version.__version__", "0.1.0"):
            version = get_version()
            assert version == "0.1.0"

    def test_get_version_info(self):
        """测试获取版本信息"""
        info = get_version_info()

        assert "version" in info
        assert "package_name" in info
        assert "python_version" in info
        assert "python_implementation" in info
        assert "project_root" in info
        assert "package_path" in info
        assert "platform" in info

        assert info["package_name"] == "edubuddy"
        assert info["python_implementation"] == sys.implementation.name
        assert info["platform"] == sys.platform

    @patch("builtins.print")
    def test_print_version_info(self, mock_print):
        """测试打印版本信息"""
        print_version_info()

        # 验证print被调用
        assert mock_print.called

        # 检查打印的内容
        calls = mock_print.call_args_list
        printed_text = "".join([call[0][0] for call in calls])

        assert "EduBuddy 版本信息" in printed_text
        assert "版本号:" in printed_text
        assert "包名:" in printed_text
        assert "Python版本:" in printed_text


class TestVersionManager:
    """版本管理器测试类"""

    def test_init(self):
        """测试初始化"""
        manager = VersionManager()
        assert manager.current_version is not None
        assert isinstance(manager.version_history, list)

    def test_get_current_version(self):
        """测试获取当前版本"""
        manager = VersionManager()
        version = manager.get_current_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_compare_versions(self):
        """测试版本比较"""
        manager = VersionManager()

        # 测试相等
        assert manager.compare_versions("1.0.0", "1.0.0") == 0

        # 测试小于
        assert manager.compare_versions("1.0.0", "1.0.1") == -1
        assert manager.compare_versions("1.0.0", "1.1.0") == -1
        assert manager.compare_versions("1.0.0", "2.0.0") == -1

        # 测试大于
        assert manager.compare_versions("1.0.1", "1.0.0") == 1
        assert manager.compare_versions("1.1.0", "1.0.0") == 1
        assert manager.compare_versions("2.0.0", "1.0.0") == 1

    def test_is_newer_version(self):
        """测试检查新版本"""
        manager = VersionManager()

        # 假设当前版本是0.1.0
        with patch.object(manager, "current_version", "0.1.0"):
            assert manager.is_newer_version("0.2.0") is True
            assert manager.is_newer_version("1.0.0") is True
            assert manager.is_newer_version("0.1.0") is False
            assert manager.is_newer_version("0.0.9") is False

    def test_get_version_changelog(self):
        """测试获取版本更新日志"""
        manager = VersionManager()
        changelog = manager.get_version_changelog()

        assert isinstance(changelog, dict)
        assert "0.1.0" in changelog
        assert "初始版本" in changelog["0.1.0"]
