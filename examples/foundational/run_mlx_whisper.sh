#!/bin/bash

# Apple MLX Whisper 快速启动脚本
# 
# 使用方法:
#   ./run_mlx_whisper.sh         # 运行基础示例
#   ./run_mlx_whisper.sh advanced # 运行高级示例

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查系统要求
check_requirements() {
    print_info "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS 系统"
        exit 1
    fi
    
    # 检查处理器架构
    ARCH=$(uname -m)
    if [[ "$ARCH" != "arm64" ]]; then
        print_warning "当前处理器架构: $ARCH"
        print_warning "此示例针对 Apple Silicon (M1/M2/M3/M4) 优化"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "系统要求检查通过"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 uv
    if ! command -v uv &> /dev/null; then
        print_error "未找到 uv 包管理器"
        print_info "请访问 https://github.com/astral-sh/uv 安装"
        exit 1
    fi
    
    # 检查 Python 模块
    if ! uv run python -c "import mlx_whisper" 2>/dev/null; then
        print_error "MLX Whisper 未安装"
        print_info "正在安装依赖..."
        uv add mlx-whisper
    fi
    
    if ! uv run python -c "import pyaudio" 2>/dev/null; then
        print_error "PyAudio 未安装"
        print_info "请先运行: brew install portaudio"
        exit 1
    fi
    
    print_success "依赖检查通过"
}

# 设置环境
setup_environment() {
    print_info "设置环境..."
    
    # 检查环境配置文件
    if [[ ! -f ".env" ]] && [[ -f "mlx_whisper.env" ]]; then
        print_warning "未找到 .env 文件"
        read -p "是否复制 mlx_whisper.env 为 .env? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_info "将使用默认配置"
        else
            cp mlx_whisper.env .env
            print_success "环境配置文件已创建"
        fi
    fi
    
    print_success "环境设置完成"
}

# 运行示例
run_example() {
    local example_type=${1:-"basic"}
    
    case $example_type in
        "basic")
            print_info "启动基础 MLX Whisper 示例..."
            uv run python apple_mlx_whisper_example.py
            ;;
        "advanced")
            print_info "启动高级 MLX Whisper 示例..."
            uv run python apple_mlx_whisper_advanced.py
            ;;
        *)
            print_error "未知示例类型: $example_type"
            print_info "可用选项: basic, advanced"
            exit 1
            ;;
    esac
}

# 显示帮助信息
show_help() {
    echo "Apple MLX Whisper 快速启动脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  basic     运行基础示例 (默认)"
    echo "  advanced  运行高级示例"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 运行基础示例"
    echo "  $0 advanced     # 运行高级示例"
    echo ""
    echo "系统要求:"
    echo "  - macOS 12.0+"
    echo "  - Apple Silicon Mac (M1/M2/M3/M4)"
    echo "  - 至少 8GB 内存"
}

# 主函数
main() {
    echo "🍎 Apple MLX Whisper Large v3 Turbo 启动器"
    echo "================================================"
    
    # 处理参数
    case ${1:-"basic"} in
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        "basic"|"advanced")
            example_type=$1
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 执行检查和启动流程
    check_requirements
    check_dependencies
    setup_environment
    
    echo ""
    print_info "准备启动 MLX Whisper 服务..."
    print_warning "请确保麦克风权限已授予终端应用"
    echo ""
    
    # 启动示例
    run_example $example_type
}

# 如果脚本被直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
