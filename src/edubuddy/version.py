"""
版本管理模块

提供版本信息和版本管理功能。
"""

import importlib.metadata
import sys
from pathlib import Path
from typing import Any, Dict, Optional

__version__ = "0.1.3"


def get_version() -> str:
    """获取当前版本号"""
    try:
        return importlib.metadata.version("edubuddy")
    except importlib.metadata.PackageNotFoundError:
        # 如果包未安装，从__init__.py中获取版本
        try:
            from . import __version__

            return __version__
        except ImportError:
            return "0.1.0"


def get_version_info() -> Dict[str, Any]:
    """
    获取详细的版本信息

    Returns:
        包含版本信息的字典
    """
    version = get_version()

    # 获取Python版本信息
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # 获取项目路径信息
    project_root = Path(__file__).parent.parent.parent.parent
    package_path = Path(__file__).parent.parent

    return {
        "version": version,
        "package_name": "edubuddy",
        "python_version": python_version,
        "python_implementation": sys.implementation.name,
        "project_root": str(project_root),
        "package_path": str(package_path),
        "platform": sys.platform,
    }


def print_version_info() -> None:
    """打印版本信息到控制台"""
    info = get_version_info()

    print("=" * 50)
    print("EduBuddy 版本信息")
    print("=" * 50)
    print(f"版本号: {info['version']}")
    print(f"包名: {info['package_name']}")
    print(f"Python版本: {info['python_version']}")
    print(f"Python实现: {info['python_implementation']}")
    print(f"平台: {info['platform']}")
    print(f"项目根目录: {info['project_root']}")
    print(f"包路径: {info['package_path']}")
    print("=" * 50)


class VersionManager:
    """版本管理器类"""

    def __init__(self) -> None:
        self.current_version = get_version()
        self.version_history: list = []

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.current_version

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号

        Args:
            version1: 第一个版本号
            version2: 第二个版本号

        Returns:
            -1: version1 < version2
             0: version1 == version2
             1: version1 > version2
        """

        def version_tuple(v: str) -> tuple[int, ...]:
            return tuple(map(int, v.split(".")))

        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)

        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0

    def is_newer_version(self, version: str) -> bool:
        """
        检查指定版本是否比当前版本更新

        Args:
            version: 要检查的版本号

        Returns:
            如果指定版本更新则返回True
        """
        return self.compare_versions(version, self.current_version) > 0

    def get_version_changelog(self) -> Dict[str, str]:
        """
        获取版本更新日志

        Returns:
            版本更新日志字典
        """
        return {
            "0.1.0": "初始版本 - 实现基础时间日志记录功能",
            # 未来版本可以在这里添加
        }
