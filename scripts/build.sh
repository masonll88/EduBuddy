#!/bin/bash

# EduBuddy 构建脚本
# 用于构建和打包项目

set -e

# 检查参数
BUMP_VERSION=""
if [ "$1" = "--bump-patch" ]; then
    BUMP_VERSION="patch"
elif [ "$1" = "--bump-minor" ]; then
    BUMP_VERSION="minor"
elif [ "$1" = "--bump-major" ]; then
    BUMP_VERSION="major"
fi

echo "🔨 开始构建 EduBuddy..."

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv未安装，请先运行 install.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 版本管理
if [ -n "$BUMP_VERSION" ]; then
    echo "📈 增加版本号 ($BUMP_VERSION)..."
    python scripts/version.py bump $BUMP_VERSION
fi

# 显示当前版本
echo "📋 当前版本: $(python scripts/version.py show | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')"

# 清理之前的构建
echo "🧹 清理之前的构建..."
rm -rf dist/ build/ *.egg-info/

# 运行测试
echo "🧪 运行测试..."
python -m pytest tests/ -v

# 代码格式化
echo "🎨 格式化代码..."
black src/ tests/
isort src/ tests/

# 类型检查
echo "🔍 类型检查..."
mypy src/

# 构建包
echo "📦 构建包..."
uv build

echo "✅ 构建完成！"
echo ""
echo "构建产物："
ls -la dist/
echo ""
echo "安装构建的包："
echo "  pip install dist/edubuddy-*.whl"
echo ""
echo "版本管理："
echo "  ./scripts/version.py show          # 显示当前版本"
echo "  ./scripts/version.py set 1.2.3     # 设置版本号"
echo "  ./scripts/version.py bump patch    # 增加补丁版本"
echo "  ./scripts/version.py bump minor    # 增加次版本"
echo "  ./scripts/version.py bump major    # 增加主版本"
echo ""
echo "构建时自动增加版本："
echo "  ./scripts/build.sh --bump-patch    # 构建时增加补丁版本"
echo "  ./scripts/build.sh --bump-minor    # 构建时增加次版本"
echo "  ./scripts/build.sh --bump-major    # 构建时增加主版本"
echo ""

