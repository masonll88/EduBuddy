#!/bin/bash

# EduBuddy 卸载脚本
# 用于从树莓派上卸载EduBuddy应用

set -e

# 配置变量
SERVICE_NAME="edubuddy"
SERVICE_USER="mason"
INSTALL_DIR="/opt/edubuddy"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/edubuddy"

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

# 停止并禁用服务
stop_service() {
    log_info "停止EduBuddy服务..."
    
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl stop "$SERVICE_NAME"
        log_success "服务已停止"
    else
        log_warning "服务未运行"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME"
        log_success "服务已禁用"
    else
        log_warning "服务未启用"
    fi
}

# 卸载Python包
uninstall_package() {
    log_info "卸载EduBuddy Python包..."
    
    # 删除虚拟环境
    VENV_DIR="$INSTALL_DIR/venv"
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
        log_success "虚拟环境已删除: $VENV_DIR"
    fi
    
    # 删除启动脚本
    if [ -f "/usr/local/bin/edubuddy" ]; then
        rm -f "/usr/local/bin/edubuddy"
        log_success "启动脚本已删除: /usr/local/bin/edubuddy"
    fi
    
    log_success "Python包卸载完成"
}

# 删除文件
remove_files() {
    log_info "删除文件和目录..."
    
    # 删除systemd服务文件
    if [ -f "$SERVICE_DIR/${SERVICE_NAME}.service" ]; then
        rm -f "$SERVICE_DIR/${SERVICE_NAME}.service"
        log_success "systemd服务文件已删除"
    fi
    
    # 删除安装目录
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        log_success "安装目录已删除: $INSTALL_DIR"
    fi
    
    # 删除日志目录（可选）
    if [ -d "$LOG_DIR" ]; then
        read -p "是否删除日志目录 $LOG_DIR? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$LOG_DIR"
            log_success "日志目录已删除: $LOG_DIR"
        else
            log_info "保留日志目录: $LOG_DIR"
        fi
    fi
    
    # 删除logrotate配置
    if [ -f "/etc/logrotate.d/edubuddy" ]; then
        rm -f "/etc/logrotate.d/edubuddy"
        log_success "logrotate配置已删除"
    fi
}

# 删除用户（可选）
remove_user() {
    if id "$SERVICE_USER" &>/dev/null; then
        read -p "是否删除服务用户 $SERVICE_USER? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            userdel "$SERVICE_USER" 2>/dev/null || log_warning "删除用户失败"
            log_success "服务用户已删除: $SERVICE_USER"
        else
            log_info "保留服务用户: $SERVICE_USER"
        fi
    fi
}

# 重新加载systemd
reload_systemd() {
    log_info "重新加载systemd配置..."
    systemctl daemon-reload
    log_success "systemd配置已重新加载"
}

# 显示卸载信息
show_uninstall_info() {
    log_info "卸载完成信息:"
    echo ""
    echo "已删除的内容:"
    echo "  - EduBuddy Python包"
    echo "  - systemd服务文件"
    echo "  - 安装目录: $INSTALL_DIR"
    echo "  - logrotate配置"
    echo ""
    echo "保留的内容:"
    echo "  - 日志目录: $LOG_DIR (如果选择保留)"
    echo "  - 服务用户: $SERVICE_USER (如果选择保留)"
    echo ""
    echo "如需完全清理，请手动删除上述保留的内容"
    echo ""
}

# 主函数
main() {
    log_info "开始卸载EduBuddy..."
    echo ""
    
    # 检查权限
    check_root
    
    # 停止服务
    stop_service
    
    # 卸载Python包
    uninstall_package
    
    # 删除文件
    remove_files
    
    # 删除用户
    remove_user
    
    # 重新加载systemd
    reload_systemd
    
    # 显示信息
    show_uninstall_info
    
    log_success "EduBuddy卸载完成！"
}

# 运行主函数
main "$@"
