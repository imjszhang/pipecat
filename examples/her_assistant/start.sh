#!/bin/bash

# 《Her》风格AI助手启动脚本
# 自动检查和启动所有必需的服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 等待服务启动
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "等待 $name 服务启动..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$name 服务已启动"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$name 服务启动超时"
    return 1
}

# 主函数
main() {
    print_header "🎬 《Her》风格AI助手启动脚本"
    echo
    
    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
    else
        print_warning "未知操作系统: $OSTYPE"
        OS="Unknown"
    fi
    
    print_status "检测到操作系统: $OS"
    
    # 检查 Python
    if ! command_exists python3; then
        print_error "Python 3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_success "Python 版本: $python_version"
    
    # 检查虚拟环境
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "未检测到虚拟环境"
        if [[ -d ".venv" ]]; then
            print_status "发现 .venv 目录，尝试激活..."
            source .venv/bin/activate
            print_success "虚拟环境已激活"
        else
            print_status "创建虚拟环境..."
            python3 -m venv .venv
            source .venv/bin/activate
            print_success "虚拟环境已创建并激活"
        fi
    else
        print_success "虚拟环境已激活: $VIRTUAL_ENV"
    fi
    
    # 检查依赖
    print_status "检查 Python 依赖..."
    if ! python -c "import pipecat" 2>/dev/null; then
        print_warning "Pipecat 未安装，正在安装..."
        pip install -e ../../
        pip install "pipecat-ai[whisper,silero,local-smart-turn,ollama,piper,webrtc,runner]"
        print_success "依赖安装完成"
    else
        print_success "Pipecat 已安装"
    fi
    
    # 检查 .env 文件
    if [[ ! -f ".env" ]]; then
        print_warning ".env 文件不存在，从模板创建..."
        cp env.example .env
        print_success ".env 文件已创建"
    else
        print_success ".env 文件存在"
    fi
    
    # 加载环境变量
    if [[ -f ".env" ]]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # 检查 Ollama
    print_status "检查 Ollama 服务..."
    
    if ! command_exists ollama; then
        print_error "Ollama 未安装"
        print_status "正在安装 Ollama..."
        
        if [[ "$OS" == "macOS" ]]; then
            if command_exists brew; then
                brew install ollama
            else
                curl -fsSL https://ollama.ai/install.sh | sh
            fi
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
        
        print_success "Ollama 安装完成"
    else
        print_success "Ollama 已安装"
    fi
    
    # 启动 Ollama 服务
    ollama_url=${OLLAMA_BASE_URL:-"http://localhost:11434"}
    if ! curl -s "$ollama_url/api/tags" >/dev/null 2>&1; then
        print_status "启动 Ollama 服务..."
        
        # 在后台启动 Ollama
        if [[ "$OS" == "macOS" ]]; then
            # macOS 使用 launchctl
            ollama serve &
        else
            # Linux 使用 systemd 或直接启动
            if systemctl is-active --quiet ollama 2>/dev/null; then
                systemctl start ollama
            else
                ollama serve &
            fi
        fi
        
        # 等待服务启动
        if wait_for_service "$ollama_url/api/tags" "Ollama"; then
            print_success "Ollama 服务已启动"
        else
            print_error "Ollama 服务启动失败"
            exit 1
        fi
    else
        print_success "Ollama 服务已运行"
    fi
    
    # 检查模型
    model_name=${OLLAMA_MODEL:-"gemma3:4b"}
    print_status "检查模型: $model_name"
    
    if ! ollama list | grep -q "$model_name"; then
        print_warning "模型 $model_name 未安装，正在下载..."
        ollama pull "$model_name"
        print_success "模型下载完成"
    else
        print_success "模型 $model_name 已安装"
    fi
    
    # 检查 TTS 服务（可选）
    piper_url=${PIPER_BASE_URL:-"http://localhost:8001"}
    # Kokoro TTS 已被 Piper TTS 替代
    
    tts_available=false
    
    # 检查 Piper TTS
    if curl -s "$piper_url/health" >/dev/null 2>&1; then
        print_success "Piper TTS 服务已运行"
        tts_available=true
    elif command_exists piper; then
        print_status "启动 Piper TTS 服务..."
        python -m piper.http_server --host 0.0.0.0 --port 8001 &
        if wait_for_service "$piper_url/health" "Piper TTS"; then
            tts_available=true
        fi
    fi
    
    # Kokoro TTS 已被 Piper TTS 替代，不再检查
    
    # 检查备用 Google TTS
    if ! $tts_available && [[ -n "${GOOGLE_API_KEY:-}" ]]; then
        print_success "将使用 Google TTS 作为备用"
        tts_available=true
    fi
    
    if ! $tts_available; then
        print_warning "没有可用的 TTS 服务，请手动启动 Piper TTS 或配置 Google TTS"
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    # 最终检查
    print_status "执行最终检查..."
    
    # 检查端口 7860
    if check_port 7860; then
        print_warning "端口 7860 已被占用，可能有其他服务在运行"
    fi
    
    # 显示系统信息
    echo
    print_header "📊 系统信息"
    echo "操作系统: $OS"
    echo "Python: $python_version"
    echo "虚拟环境: ${VIRTUAL_ENV:-"未激活"}"
    echo "Ollama URL: $ollama_url"
    echo "模型: $model_name"
    echo "TTS 可用: $tts_available"
    echo
    
    # 启动助手
    print_header "🚀 启动《Her》风格AI助手"
    print_status "启动中..."
    echo
    
    # 设置环境变量
    export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
    
    # 启动机器人
    python bot.py
}

# 信号处理
cleanup() {
    print_status "正在清理..."
    # 这里可以添加清理逻辑
    exit 0
}

trap cleanup SIGINT SIGTERM

# 运行主函数
main "$@"
