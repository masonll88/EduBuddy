"""
命令行接口模块

提供EduBuddy的命令行界面。
"""

import signal
import sys
import time
from typing import Optional

import click

from .logger import logger
from .time_service import TimeService, create_time_service
from .version import VersionManager, get_version_info, print_version_info


@click.group()
@click.version_option(version=get_version_info()["version"], prog_name="EduBuddy")
def main() -> None:
    """EduBuddy - 教育助手应用"""
    pass


@main.command()
@click.option(
    "--interval", "-i", type=float, default=4.0, help="日志打印间隔（秒），默认4秒"
)
@click.option(
    "--format",
    "-f",
    type=str,
    default="%Y-%m-%d %H:%M:%S",
    help="时间格式字符串，默认ISO格式",
)
@click.option("--duration", "-d", type=int, help="运行持续时间（秒），不指定则持续运行")
def start_logger(interval: float, format: str, duration: Optional[int]) -> None:
    """启动时间日志记录器"""
    try:
        # 创建时间服务
        time_service = create_time_service(interval=interval, format_str=format)

        # 设置信号处理器，用于优雅退出
        def signal_handler(signum: int, frame: object) -> None:
            logger.info("接收到退出信号，正在停止...")
            time_service.stop_time_logging()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 启动时间日志记录
        time_service.start_time_logging()

        if duration:
            # 如果指定了持续时间，则运行指定时间后停止
            logger.info(f"将运行 {duration} 秒后自动停止")
            time.sleep(duration)
            time_service.stop_time_logging()
        else:
            # 持续运行直到用户中断
            logger.info("时间日志记录器正在运行，按 Ctrl+C 停止")
            try:
                while time_service.is_time_logging_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("用户中断，正在停止...")
                time_service.stop_time_logging()

    except Exception as e:
        logger.error(f"启动时间日志记录器时发生错误: {e}")
        sys.exit(1)


@main.command()
def version() -> None:
    """显示版本信息"""
    print_version_info()


@main.command()
@click.option("--check-updates", "-c", is_flag=True, help="检查是否有新版本")
def info(check_updates: bool) -> None:
    """显示应用信息"""
    version_info = get_version_info()

    print(f"EduBuddy v{version_info['version']}")
    print(
        f"Python {version_info['python_version']} ({version_info['python_implementation']})"
    )
    print(f"平台: {version_info['platform']}")

    if check_updates:
        version_manager = VersionManager()
        changelog = version_manager.get_version_changelog()

        print("\n版本更新日志:")
        for ver, desc in changelog.items():
            print(f"  {ver}: {desc}")


@main.command()
@click.option(
    "--test-duration", "-t", type=int, default=5, help="测试运行时间（秒），默认5秒"
)
def test(test_duration: int) -> None:
    """测试时间日志记录功能"""
    logger.info(f"开始测试，将运行 {test_duration} 秒")

    try:
        time_service = create_time_service(interval=0.5, format_str="%H:%M:%S")
        time_service.start_time_logging()
        time.sleep(test_duration)
        time_service.stop_time_logging()
        logger.info("测试完成")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
