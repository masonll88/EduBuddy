#!/usr/bin/env python3
"""
版本管理脚本

用于管理EduBuddy的版本号。
"""

import argparse
import re
import sys
from pathlib import Path


def get_current_version() -> str:
    """获取当前版本号"""
    version_file = Path("src/edubuddy/version.py")
    if not version_file.exists():
        return "0.1.0"
    
    content = version_file.read_text()
    match = re.search(r'__version__ = "([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.1.0"


def update_version(new_version: str) -> None:
    """更新版本号"""
    version_file = Path("src/edubuddy/version.py")
    if not version_file.exists():
        print(f"错误: 版本文件 {version_file} 不存在")
        sys.exit(1)
    
    content = version_file.read_text()
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    if new_content == content:
        print(f"警告: 版本号已经是 {new_version}")
        return
    
    version_file.write_text(new_content)
    print(f"版本号已更新为: {new_version}")


def bump_version(version_type: str) -> str:
    """自动增加版本号"""
    current = get_current_version()
    parts = current.split(".")
    
    if len(parts) != 3:
        print(f"错误: 无效的版本号格式: {current}")
        sys.exit(1)
    
    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        print(f"错误: 版本号包含非数字: {current}")
        sys.exit(1)
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        print(f"错误: 无效的版本类型: {version_type}")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"


def main():
    parser = argparse.ArgumentParser(description="EduBuddy 版本管理工具")
    parser.add_argument(
        "action",
        choices=["show", "set", "bump"],
        help="操作类型: show(显示), set(设置), bump(增加)"
    )
    parser.add_argument(
        "value",
        nargs="?",
        help="版本号或版本类型 (major/minor/patch)"
    )
    
    args = parser.parse_args()
    
    if args.action == "show":
        version = get_current_version()
        print(f"当前版本: {version}")
    
    elif args.action == "set":
        if not args.value:
            print("错误: 设置版本号需要指定版本号")
            sys.exit(1)
        
        # 验证版本号格式
        if not re.match(r"^\d+\.\d+\.\d+$", args.value):
            print(f"错误: 无效的版本号格式: {args.value}")
            print("版本号格式应为: major.minor.patch (例如: 1.2.3)")
            sys.exit(1)
        
        update_version(args.value)
    
    elif args.action == "bump":
        if not args.value:
            print("错误: 增加版本号需要指定类型 (major/minor/patch)")
            sys.exit(1)
        
        if args.value not in ["major", "minor", "patch"]:
            print(f"错误: 无效的版本类型: {args.value}")
            print("版本类型应为: major, minor, 或 patch")
            sys.exit(1)
        
        new_version = bump_version(args.value)
        update_version(new_version)


if __name__ == "__main__":
    main()
