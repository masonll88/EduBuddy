#!/bin/bash

# EduBuddy 服务管理脚本
# 用于管理EduBuddy的systemd服务

set -e

# 配置变量
SERVICE_NAME="edubuddy"

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

# 显示帮助信息
show_help() {
    echo "EduBuddy 服务管理脚本"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  follow    实时查看日志"
    echo "  enable    启用自启动"
    echo "  disable   禁用自启动"
    echo "  reload    重新加载配置"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
    echo "  $0 follow"
}

# 检查服务是否存在
check_service() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        log_error "服务 $SERVICE_NAME 不存在，请先运行部署脚本"
        exit 1
    fi
}

# 启动服务
start_service() {
    log_info "启动 $SERVICE_NAME 服务..."
    sudo systemctl start "$SERVICE_NAME"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止 $SERVICE_NAME 服务..."
    sudo systemctl stop "$SERVICE_NAME"
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "服务停止成功"
    else
        log_error "服务停止失败"
        exit 1
    fi
}

# 重启服务
restart_service() {
    log_info "重启 $SERVICE_NAME 服务..."
    sudo systemctl restart "$SERVICE_NAME"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "服务重启成功"
    else
        log_error "服务重启失败"
        systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

# 查看服务状态
show_status() {
    log_info "查看 $SERVICE_NAME 服务状态..."
    systemctl status "$SERVICE_NAME" --no-pager
}

# 查看服务日志
show_logs() {
    log_info "查看 $SERVICE_NAME 服务日志..."
    sudo journalctl -u "$SERVICE_NAME" --no-pager
}

# 实时查看日志
follow_logs() {
    log_info "实时查看 $SERVICE_NAME 服务日志 (按 Ctrl+C 退出)..."
    sudo journalctl -u "$SERVICE_NAME" -f
}

# 启用自启动
enable_service() {
    log_info "启用 $SERVICE_NAME 自启动..."
    sudo systemctl enable "$SERVICE_NAME"
    log_success "自启动已启用"
}

# 禁用自启动
disable_service() {
    log_info "禁用 $SERVICE_NAME 自启动..."
    sudo systemctl disable "$SERVICE_NAME"
    log_success "自启动已禁用"
}

# 重新加载配置
reload_service() {
    log_info "重新加载 $SERVICE_NAME 配置..."
    sudo systemctl daemon-reload
    sudo systemctl reload "$SERVICE_NAME" 2>/dev/null || log_warning "服务不支持reload，请使用restart"
    log_success "配置已重新加载"
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    # 检查服务是否存在
    check_service
    
    # 根据命令执行相应操作
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        follow)
            follow_logs
            ;;
        enable)
            enable_service
            ;;
        disable)
            disable_service
            ;;
        reload)
            reload_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
