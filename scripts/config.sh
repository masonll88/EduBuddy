#!/bin/bash

# EduBuddy 配置管理脚本
# 用于管理部署配置参数

set -e

# 配置文件路径
CONFIG_FILE="scripts/deploy.conf"

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
    echo "EduBuddy 配置管理脚本"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  show                   显示当前配置"
    echo "  set <key> <value>      设置配置项"
    echo "  get <key>              获取配置项值"
    echo "  edit                   编辑配置文件"
    echo "  reset                  重置为默认配置"
    echo "  help                   显示此帮助信息"
    echo ""
    echo "配置项:"
    echo "  LOG_INTERVAL           日志打印间隔（秒）"
    echo "  LOG_FORMAT             时间格式字符串"
    echo "  LOG_LEVEL              日志级别"
    echo "  MAX_MEMORY             最大内存限制"
    echo "  MAX_CPU                最大CPU限制"
    echo ""
    echo "示例:"
    echo "  $0 show"
    echo "  $0 set LOG_INTERVAL 3.0"
    echo "  $0 get LOG_INTERVAL"
    echo "  $0 edit"
}

# 检查配置文件是否存在
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi
}

# 显示当前配置
show_config() {
    log_info "当前部署配置:"
    echo ""
    if [ -f "$CONFIG_FILE" ]; then
        cat "$CONFIG_FILE" | grep -v "^#" | grep -v "^$" | while read line; do
            if [ -n "$line" ]; then
                echo "  $line"
            fi
        done
    else
        log_warning "配置文件不存在，使用默认配置"
    fi
    echo ""
}

# 获取配置项值
get_config() {
    local key="$1"
    if [ -z "$key" ]; then
        log_error "请指定配置项名称"
        exit 1
    fi
    
    if [ -f "$CONFIG_FILE" ]; then
        local value=$(grep "^${key}=" "$CONFIG_FILE" | cut -d'=' -f2- | tr -d '"')
        if [ -n "$value" ]; then
            echo "$value"
        else
            log_warning "配置项 $key 不存在"
            exit 1
        fi
    else
        log_error "配置文件不存在"
        exit 1
    fi
}

# 设置配置项
set_config() {
    local key="$1"
    local value="$2"
    
    if [ -z "$key" ] || [ -z "$value" ]; then
        log_error "用法: $0 set <key> <value>"
        exit 1
    fi
    
    # 创建配置文件（如果不存在）
    if [ ! -f "$CONFIG_FILE" ]; then
        log_info "创建配置文件: $CONFIG_FILE"
        cat > "$CONFIG_FILE" << EOF
# EduBuddy 部署配置文件
# 此文件包含部署时的配置参数

# 日志设置
LOG_INTERVAL=2.0
LOG_FORMAT="%Y-%m-%d %H:%M:%S"
LOG_LEVEL="INFO"

# 性能设置
MAX_MEMORY="256M"
MAX_CPU="50%"

# 服务设置
AUTO_START=true
RESTART_ON_FAILURE=true

# 安全设置
NO_NEW_PRIVILEGES=true
PRIVATE_TMP=true
PROTECT_SYSTEM="strict"
PROTECT_HOME=true

# 资源限制
LIMIT_NOFILE=65536
EOF
    fi
    
    # 检查配置项是否存在
    if grep -q "^${key}=" "$CONFIG_FILE"; then
        # 更新现有配置项
        sed -i "s|^${key}=.*|${key}=${value}|" "$CONFIG_FILE"
        log_success "配置项 $key 已更新为: $value"
    else
        # 添加新配置项
        echo "${key}=${value}" >> "$CONFIG_FILE"
        log_success "配置项 $key 已添加: $value"
    fi
}

# 编辑配置文件
edit_config() {
    if [ -z "$EDITOR" ]; then
        EDITOR="nano"
    fi
    
    log_info "使用 $EDITOR 编辑配置文件: $CONFIG_FILE"
    $EDITOR "$CONFIG_FILE"
}

# 重置为默认配置
reset_config() {
    log_info "重置为默认配置..."
    
    cat > "$CONFIG_FILE" << EOF
# EduBuddy 部署配置文件
# 此文件包含部署时的配置参数

# 日志设置
LOG_INTERVAL=2.0
LOG_FORMAT="%Y-%m-%d %H:%M:%S"
LOG_LEVEL="INFO"

# 性能设置
MAX_MEMORY="256M"
MAX_CPU="50%"

# 服务设置
AUTO_START=true
RESTART_ON_FAILURE=true

# 安全设置
NO_NEW_PRIVILEGES=true
PRIVATE_TMP=true
PROTECT_SYSTEM="strict"
PROTECT_HOME=true

# 资源限制
LIMIT_NOFILE=65536
EOF

    log_success "配置已重置为默认值"
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
    
    case "$1" in
        show)
            show_config
            ;;
        get)
            get_config "$2"
            ;;
        set)
            set_config "$2" "$3"
            ;;
        edit)
            edit_config
            ;;
        reset)
            reset_config
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
