#!/bin/bash

# EduBuddy 部署脚本
# 用于在树莓派上部署EduBuddy应用

set -e

# 配置变量
SERVICE_NAME="edubuddy"
SERVICE_USER="mason"
SERVICE_GROUP="mason"
INSTALL_DIR="/opt/edubuddy"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/edubuddy"

# 从配置文件读取参数
DEPLOY_CONFIG_FILE="scripts/deploy.conf"
if [ -f "$DEPLOY_CONFIG_FILE" ]; then
    source "$DEPLOY_CONFIG_FILE"
else
    # 默认配置
    LOG_INTERVAL=2.0
    LOG_FORMAT="%Y-%m-%d %H:%M:%S"
    LOG_LEVEL="INFO"
    MAX_MEMORY="256M"
    MAX_CPU="50%"
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用sudo运行此脚本"
        exit 1
    fi
}

# 检查系统
check_system() {
    log_info "检查系统环境..."
    
    # 检查是否为树莓派
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warning "未检测到树莓派系统，继续执行..."
    fi
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
    
    # 检查uv
    # 在sudo环境下，需要检查多个可能的uv安装路径
    UV_PATHS=(
        "/home/mason/.local/bin/uv"
        "/home/mason/.cargo/bin/uv"
        "/usr/local/bin/uv"
        "/usr/bin/uv"
    )
    
    UV_FOUND=""
    for path in "${UV_PATHS[@]}"; do
        if [ -x "$path" ]; then
            UV_FOUND="$path"
            break
        fi
    done
    
    if [ -n "$UV_FOUND" ]; then
        log_success "找到uv: $UV_FOUND"
        export PATH="$(dirname "$UV_FOUND"):$PATH"
    else
        log_info "安装uv包管理器..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        
        # 验证uv安装
        if ! command -v uv &> /dev/null; then
            log_error "uv安装失败"
            exit 1
        fi
        log_success "uv安装成功"
    fi
}

# 创建用户和目录
setup_directories() {
    log_info "创建目录和用户..."
    
    # 创建安装目录
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    
    # 创建服务用户（如果不存在）
    if ! id "$SERVICE_USER" &>/dev/null; then
        log_info "创建服务用户: $SERVICE_USER"
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    fi
    
    # 设置目录权限
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"
}

# 安装wheel包
install_package() {
    log_info "安装EduBuddy包..."
    
    # 查找最新的wheel文件
    WHEEL_FILE=$(find dist/ -name "*.whl" -type f | sort -V | tail -n 1)
    
    if [ -z "$WHEEL_FILE" ]; then
        log_error "未找到wheel文件，请先运行构建脚本"
        exit 1
    fi
    
    log_info "安装文件: $WHEEL_FILE"
    
    # 创建虚拟环境
    VENV_DIR="$INSTALL_DIR/venv"
    log_info "创建虚拟环境: $VENV_DIR"
    uv venv "$VENV_DIR"
    
    # 激活虚拟环境并安装包
    source "$VENV_DIR/bin/activate"
    uv pip install --upgrade "$WHEEL_FILE"
    
    # 创建全局可访问的启动脚本
    create_launcher_script
    
    # 验证安装
    if [ -f "$VENV_DIR/bin/edubuddy" ]; then
        log_success "EduBuddy安装成功"
        "$VENV_DIR/bin/edubuddy" --version
    else
        log_error "EduBuddy安装失败"
        exit 1
    fi
}

# 创建启动脚本
create_launcher_script() {
    log_info "创建启动脚本..."
    
    VENV_DIR="$INSTALL_DIR/venv"
    
    # 创建全局可访问的启动脚本
    cat > "/usr/local/bin/edubuddy" << EOF
#!/bin/bash
# EduBuddy 启动脚本
# 自动激活虚拟环境并运行edubuddy

VENV_DIR="$VENV_DIR"

if [ ! -d "\$VENV_DIR" ]; then
    echo "错误: 虚拟环境不存在: \$VENV_DIR"
    exit 1
fi

if [ ! -f "\$VENV_DIR/bin/edubuddy" ]; then
    echo "错误: edubuddy可执行文件不存在: \$VENV_DIR/bin/edubuddy"
    exit 1
fi

# 激活虚拟环境并运行edubuddy
source "\$VENV_DIR/bin/activate"
exec "\$VENV_DIR/bin/edubuddy" "\$@"
EOF

    chmod +x "/usr/local/bin/edubuddy"
    log_success "启动脚本已创建: /usr/local/bin/edubuddy"
}

# 创建systemd服务文件
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > "$SERVICE_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=EduBuddy - 教育助手应用
Documentation=https://github.com/mason/edubuddy
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/local/bin/edubuddy start-logger --interval $LOG_INTERVAL
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=edubuddy

# 环境变量
Environment=PYTHONPATH=$INSTALL_DIR/venv/lib/python*/site-packages
Environment=PYTHONUNBUFFERED=1

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $INSTALL_DIR

# 资源限制
LimitNOFILE=65536
MemoryMax=$MAX_MEMORY

[Install]
WantedBy=multi-user.target
EOF

    log_success "systemd服务文件已创建"
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    cat > "$INSTALL_DIR/edubuddy.conf" << EOF
# EduBuddy 配置文件

# 日志设置
LOG_LEVEL=$LOG_LEVEL
LOG_INTERVAL=$LOG_INTERVAL
LOG_FORMAT=$LOG_FORMAT

# 服务设置
AUTO_START=true
RESTART_ON_FAILURE=true

# 性能设置
MAX_MEMORY=$MAX_MEMORY
MAX_CPU=$MAX_CPU
EOF

    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/edubuddy.conf"
    chmod 644 "$INSTALL_DIR/edubuddy.conf"
    
    log_success "配置文件已创建"
}

# 创建日志轮转配置
create_logrotate() {
    log_info "创建日志轮转配置..."
    
    cat > "/etc/logrotate.d/edubuddy" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

    log_success "日志轮转配置已创建"
}

# 启动服务
start_service() {
    log_info "启动EduBuddy服务..."
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable "$SERVICE_NAME"
    
    # 启动服务
    systemctl start "$SERVICE_NAME"
    
    # 检查服务状态
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "EduBuddy服务启动成功"
    else
        log_error "EduBuddy服务启动失败"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    log_info "服务信息:"
    echo ""
    echo "服务状态:"
    systemctl status "$SERVICE_NAME" --no-pager
    echo ""
    echo "服务日志:"
    echo "  journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "管理命令:"
    echo "  启动服务: sudo systemctl start $SERVICE_NAME"
    echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
    echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
    echo "  查看状态: sudo systemctl status $SERVICE_NAME"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "  禁用自启: sudo systemctl disable $SERVICE_NAME"
    echo "  启用自启: sudo systemctl enable $SERVICE_NAME"
    echo ""
    echo "配置文件:"
    echo "  服务配置: $SERVICE_DIR/${SERVICE_NAME}.service"
    echo "  应用配置: $INSTALL_DIR/edubuddy.conf"
    echo "  日志目录: $LOG_DIR"
    echo ""
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    log_info "开始部署EduBuddy..."
    echo ""
    
    # 检查权限
    check_root
    
    # 检查系统
    check_system
    
    # 创建目录和用户
    setup_directories
    
    # 安装包
    install_package
    
    # 创建配置文件
    create_config
    
    # 创建systemd服务
    create_systemd_service
    
    # 创建日志轮转
    create_logrotate
    
    # 启动服务
    start_service
    
    # 显示信息
    show_service_info
    
    log_success "EduBuddy部署完成！"
    echo ""
    log_info "服务将在系统启动时自动启动"
    log_info "使用 'sudo journalctl -u $SERVICE_NAME -f' 查看实时日志"
}

# 信号处理
trap cleanup EXIT

# 运行主函数
main "$@"
