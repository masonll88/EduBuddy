#!/bin/bash

# EduBuddy 安装脚本
# 用于在远程树莓派上安装和配置项目

set -e

echo "🚀 开始安装 EduBuddy..."

# 检查Python版本
echo "📋 检查Python版本..."
python3 --version

# 安装uv（如果未安装）
if ! command -v uv &> /dev/null; then
    echo "📦 安装uv包管理器..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv已安装"
fi

# 同步依赖（包括开发依赖）
echo "📦 安装项目依赖..."
uv sync --extra dev

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装项目
echo "📦 安装EduBuddy..."
uv pip install -e .

# 运行测试
echo "🧪 运行测试..."
python -m pytest tests/ -v

echo "✅ 安装完成！"
echo ""
echo "使用方法："
echo "  source .venv/bin/activate"
echo "  edubuddy --help"
echo "  edubuddy start-logger"
echo ""
