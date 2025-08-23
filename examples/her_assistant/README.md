# 《Her》风格AI助手 - 完全本地版

> 基于 Pipecat 框架构建的完全本地化语音AI助手，灵感来自电影《Her》中的 Samantha

## 🎯 项目特色

- **🏠 完全本地化**: 所有AI处理都在本地完成，无需外部API
- **🔒 隐私保护**: 数据不离开本地设备，保护用户隐私
- **⚡ 低延迟**: 本地处理，实时对话体验
- **🎭 《Her》风格**: 温暖、智慧、具有同理心的对话风格
- **🧠 智能对话**: 支持深度对话，不仅仅是问答

## 🏗️ 技术架构

### 核心技术栈
- **Silero VAD** - 语音活动检测（本地）
- **Whisper Large v3 Turbo** - 语音转文本（本地）
- **Smart Turn v2** - 智能轮换检测（本地）
- **Ollama + Gemma 3 4B** - 大语言模型（本地）
- **Piper TTS** - 文本转语音（本地）

### 数据流程
```
用户语音 → VAD检测 → Whisper STT → Smart Turn → Gemma 3 4B → Piper TTS → 用户听到回复
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd /Volumes/home_x/github/fork/pipecat/examples/her_assistant

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ../../
pip install "pipecat-ai[whisper,silero,local-smart-turn,ollama,piper,webrtc,runner]"
```

### 2. 启动本地服务

#### 启动 Ollama（必需）
```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动服务
ollama serve &

# 拉取 Gemma 3 4B 模型
ollama pull gemma3:4b

# 验证安装
ollama list
```

#### 启动 Piper TTS（推荐）
```bash
# 安装 Piper TTS
pip install piper-tts

# 启动服务（在单独终端）
python -m piper.http_server --host 0.0.0.0 --port 8001
```

#### Piper TTS 安装说明
```bash
# 如果 Piper TTS 未安装，可通过以下方式安装：
pip install piper-tts

# 或下载预编译版本（推荐）
# 访问: https://github.com/rhasspy/piper/releases
```

### 3. 配置环境

```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件（可选，默认配置已优化）
nano .env
```

### 4. 启动助手

```bash
# 启动《Her》助手
python bot.py

# 或使用详细日志
LOG_LEVEL=DEBUG python bot.py
```

### 5. 开始对话

1. 打开浏览器访问 `http://localhost:7860`
2. 允许麦克风权限
3. 点击连接按钮
4. 开始与AI助手对话

## ⚙️ 配置说明

### 核心配置

```env
# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Whisper 配置
WHISPER_MODEL=large-v3-turbo
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=int8

# TTS 配置
PIPER_BASE_URL=http://localhost:8001
PIPER_VOICE=en_US-lessac-medium
```

### 性能优化

```env
# 内存优化（16GB 系统）
TORCH_DTYPE=float16
CPU_THREADS=4
CUDA_MEMORY_FRACTION=0.8

# 模型缓存
MODEL_CACHE_DIR=./models
HF_HOME=./models/huggingface
```

### 《Her》风格配置

```env
# 系统提示词
SYSTEM_PROMPT="你是一个温暖、智慧且具有同理心的AI助手，就像电影《Her》中的Samantha一样..."

# VAD 敏感度
VAD_CONFIDENCE=0.7
VAD_START_SECS=0.2
VAD_STOP_SECS=0.8
```

## 🎛️ 硬件优化

### Apple Silicon (M1/M2/M3)
```env
WHISPER_DEVICE=mps
SMART_TURN_DEVICE=mps
MPS_AVAILABLE=true
```

### NVIDIA GPU
```env
WHISPER_DEVICE=cuda
SMART_TURN_DEVICE=cuda
CUDA_MEMORY_FRACTION=0.8
```

### CPU 优化（16GB 内存）
```env
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
CPU_THREADS=4
```

## 🔧 故障排除

### 常见问题

#### 1. Ollama 连接失败
```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 重启服务
pkill ollama
ollama serve &
```

#### 2. 模型未找到
```bash
# 检查已安装模型
ollama list

# 重新拉取模型
ollama pull gemma3:4b
```

#### 3. 内存不足
```bash
# 检查内存使用
free -h  # Linux
vm_stat | grep free  # macOS

# 优化配置
export TORCH_DTYPE=float16
export WHISPER_COMPUTE_TYPE=int8
```

#### 4. 音频设备问题
```bash
# 检查音频设备
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}')
p.terminate()
"
```

### 日志调试

```bash
# 启用详细日志
LOG_LEVEL=DEBUG python bot.py

# 查看日志文件
tail -f logs/her_assistant.log
```

## 📊 性能指标

### 系统要求
- **最低内存**: 16GB RAM
- **推荐内存**: 32GB RAM
- **存储空间**: 50GB 可用空间
- **处理器**: Intel i5/AMD Ryzen 5 或更好

### 性能表现
- **首次启动**: 30-60秒（模型加载）
- **后续启动**: <5秒
- **响应延迟**: <1秒
- **内存使用**: 8-12GB（16GB 系统）

## 🌟 高级功能

### 多语言支持
```env
# 中文配置
WHISPER_LANGUAGE=zh
PIPER_VOICE=zh_CN-huayan-medium
SYSTEM_PROMPT="你是一个说中文的智能助手..."
```

### 自定义声音
```env
# 更换 TTS 声音
PIPER_VOICE=en_US-amy-medium  # 女性声音
PIPER_VOICE=en_US-ryan-medium # 男性声音
```

### 实验性功能
```env
# 启用实验功能
EXPERIMENTAL_FEATURES=true
ENABLE_EMOTION_DETECTION=true
```

## 🤝 贡献和支持

### 获取帮助
- **Pipecat 文档**: [docs.pipecat.ai](https://docs.pipecat.ai)
- **GitHub Issues**: [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)
- **Discord 社区**: [discord.gg/pipecat](https://discord.gg/pipecat)

### 相关项目
- **Ollama**: [ollama.ai](https://ollama.ai)
- **Whisper**: [openai.com/whisper](https://openai.com/whisper)
- **Piper TTS**: [github.com/rhasspy/piper](https://github.com/rhasspy/piper)

## 📄 许可证

本项目基于 BSD 2-Clause License 开源。

---

**享受与《Her》风格AI助手的对话吧！🎬✨**
