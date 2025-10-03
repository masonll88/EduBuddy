# EduBuddy

一个功能丰富的教育助手应用，使用Python开发，遵循最佳实践。

## 功能特性

- ⏰ **时间日志记录**: 每秒打印当前时间，支持自定义间隔和格式
- 📦 **版本管理**: 完整的版本信息管理和更新日志
- 🚀 **打包支持**: 使用现代Python打包工具，支持pip安装
- 🧪 **测试覆盖**: 完整的单元测试和集成测试
- 📝 **日志系统**: 使用loguru提供强大的日志功能
- 🎯 **CLI界面**: 友好的命令行界面

## 安装

### 使用uv（推荐）

```bash
# 安装uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd EduBuddy

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 使用pip

```bash
# 克隆项目
git clone <repository-url>
cd EduBuddy

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 显示帮助信息
edubuddy --help

# 启动时间日志记录器（默认1秒间隔）
edubuddy start-logger

# 自定义间隔和格式
edubuddy start-logger --interval 2.0 --format "%H:%M:%S"

# 运行指定时间后自动停止
edubuddy start-logger --duration 10

# 显示版本信息
edubuddy version

# 显示应用信息
edubuddy info

# 检查更新
edubuddy info --check-updates

# 测试功能
edubuddy test --test-duration 5
```

### Python API使用

```python
from edubuddy import TimeLogger, get_version_info

# 创建时间日志记录器
logger = TimeLogger(interval=1.0, format_str="%Y-%m-%d %H:%M:%S")

# 启动日志记录
logger.start()

# 运行一段时间...
import time
time.sleep(10)

# 停止日志记录
logger.stop()

# 获取版本信息
version_info = get_version_info()
print(f"当前版本: {version_info['version']}")
```

## 项目结构

```
EduBuddy/
├── src/
│   └── edubuddy/
│       ├── __init__.py          # 包初始化
│       ├── cli.py               # 命令行接口
│       ├── logger.py            # 时间日志记录器
│       └── version.py           # 版本管理
├── tests/
│   ├── __init__.py
│   ├── test_logger.py           # 日志记录器测试
│   └── test_version.py          # 版本管理测试
├── docs/                        # 文档目录
├── pyproject.toml               # 项目配置
└── README.md                    # 项目说明
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_logger.py

# 运行测试并显示覆盖率
pytest --cov=edubuddy
```

### 代码格式化

```bash
# 格式化代码
black src/ tests/

# 排序导入
isort src/ tests/

# 类型检查
mypy src/
```

### 构建和发布

```bash
# 构建包
uv build

# 发布到PyPI（需要配置认证）
uv publish
```

## 配置

项目使用`pyproject.toml`进行配置，包括：

- 项目元数据
- 依赖管理
- 构建配置
- 开发工具配置（black, isort, mypy, pytest）

## 依赖

### 运行时依赖

- `loguru>=0.7.0`: 强大的日志库
- `click>=8.0.0`: 命令行界面框架

### 开发依赖

- `pytest>=7.0.0`: 测试框架
- `black>=23.0.0`: 代码格式化
- `isort>=5.12.0`: 导入排序
- `flake8>=6.0.0`: 代码检查
- `mypy>=1.0.0`: 类型检查

## 部署

### 开发环境安装

1. SSH 连接到树莓派：
```bash
ssh mason@192.168.8.114
# 输入密码: lvle1988
```

2. 运行安装脚本：
```bash
cd /home/mason/EduBuddy
./scripts/install.sh
```

3. 使用应用：
```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动时间日志记录器
edubuddy start-logger

# 查看版本信息
edubuddy version

# 运行测试
edubuddy test
```

### 生产环境部署

1. 构建应用：
```bash
# 构建并增加版本号
./scripts/build.sh --bump-patch

# 或手动设置版本号
python scripts/version.py set 1.0.0
./scripts/build.sh
```

2. 部署到系统：
```bash
# 部署为systemd服务
sudo ./scripts/deploy.sh
```

3. 管理服务：
```bash
# 使用服务管理脚本
./scripts/service.sh start    # 启动服务
./scripts/service.sh stop     # 停止服务
./scripts/service.sh status   # 查看状态
./scripts/service.sh logs     # 查看日志
./scripts/service.sh follow   # 实时日志

# 或直接使用systemctl
sudo systemctl start edubuddy
sudo systemctl status edubuddy
sudo journalctl -u edubuddy -f
```

4. 卸载应用：
```bash
# 完全卸载
sudo ./scripts/uninstall.sh
```

## 版本历史

- **0.1.1**: 增加版本管理和部署功能
- **0.1.0**: 初始版本 - 实现基础时间日志记录功能

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 作者

Mason - mason@example.com

