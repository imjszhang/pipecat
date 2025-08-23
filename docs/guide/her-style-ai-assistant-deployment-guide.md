# 《Her》风格AI助手本地部署完整攻略

> 基于 Pipecat 框架构建类似《Her》电影中 Samantha 的智能语音助手

## 📋 项目概述

本指南将帮助你在16GB内存的个人设备上部署一个多模态AI助手，该助手使用5个神经网络模型协同工作，提供自然流畅的语音对话体验。

### 🎯 技术栈

- **Silero VAD** - 语音活动检测
- **Whisper Large v3 Turbo** - 语音转文本
- **Smart Turn v2** - 智能轮换检测  
- **Kokoro TTS** - 文本转语音（或 Google TTS 替代）
- **Gemma 3 4B** - 大语言模型（或 Gemini 2.0 Flash）

### 🔧 系统要求

| 组件 | 最低要求 | 推荐配置 |
|-----|---------|---------|
| **内存** | 16GB RAM | 32GB RAM |
| **存储** | 50GB 可用空间 | 100GB SSD |
| **处理器** | Intel i5/AMD Ryzen 5 | Apple M1+/Intel i7/AMD Ryzen 7 |
| **GPU** | 可选 | NVIDIA RTX 3060+ 或 Apple Silicon |
| **操作系统** | macOS 10.15+, Ubuntu 18.04+, Windows 10+ | 最新版本 |

## 🚀 第一步：环境准备

### 安装 uv 包管理器

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 验证安装

```bash
# 重启终端后验证
uv --version

# 检查 Python 版本（需要 3.10+）
python --version
```

## 📦 第二步：项目配置

### 克隆并初始化项目

```bash
# 1. 进入项目目录
cd /path/to/pipecat

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 4. 安装基础依赖
uv sync --dev
```

### 安装 AI 服务依赖

```bash
# 安装核心AI服务支持
uv add pipecat-ai[whisper,silero,local-smart-turn,google,groq]

# 安装额外功能（可选）
uv add pipecat-ai[local,webrtc,runner]

# 验证安装
uv pip list | grep pipecat
```

## ⚙️ 第三步：环境变量配置

### 复制配置模板

```bash
cp env.example .env
```

### 配置必要的 API 密钥

编辑 `.env` 文件，添加以下配置：

```bash
# =============================================================================
# 核心服务配置
# =============================================================================

# Google AI (用于 Gemini 模型和 TTS)
GOOGLE_API_KEY=your_google_api_key_here

# Groq (用于 Whisper Large v3 Turbo - 推荐)
GROQ_API_KEY=your_groq_api_key_here

# OpenAI (备用选项)
OPENAI_API_KEY=your_openai_api_key_here

# =============================================================================
# 本地模型配置
# =============================================================================

# Smart Turn v2 模型路径（留空使用默认 HuggingFace 模型）
LOCAL_SMART_TURN_MODEL_PATH=

# Piper TTS 本地服务地址（如果使用本地 TTS）
PIPER_BASE_URL=http://localhost:8000

# =============================================================================
# 可选服务配置
# =============================================================================

# Deepgram (备用语音识别服务)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Daily.co (Web 界面支持)
DAILY_API_KEY=your_daily_api_key
DAILY_SAMPLE_ROOM_URL=https://your_room_url

# 监控和分析
SENTRY_DSN=your_sentry_dsn_for_monitoring
```

### 获取 API 密钥

| 服务 | 获取地址 | 用途 | 费用 |
|-----|---------|-----|-----|
| **Google AI** | [Google AI Studio](https://aistudio.google.com/) | Gemini 模型和 TTS | 免费额度 |
| **Groq** | [Groq Console](https://console.groq.com/) | Whisper v3 Turbo | 免费额度 |
| **OpenAI** | [OpenAI Platform](https://platform.openai.com/) | 备用 LLM/TTS | 按用量付费 |
| **Deepgram** | [Deepgram Console](https://console.deepgram.com/) | 备用 STT | 免费额度 |

## 🧠 第四步：模型配置详解

### 1. Silero VAD（语音活动检测）

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# 创建 VAD 分析器
vad = SileroVADAnalyzer(
    sample_rate=16000,
    params=VADParams(
        confidence=0.7,      # 置信度阈值
        start_secs=0.2,      # 语音开始检测时间
        stop_secs=0.8,       # 语音结束检测时间
        min_volume=0.6       # 最小音量阈值
    )
)
```

### 2. Whisper Large v3 Turbo（语音转文本）

#### 方案A：使用 Groq API（推荐）

```python
from pipecat.services.groq import GroqSTTService

stt = GroqSTTService(
    api_key=os.getenv("GROQ_API_KEY"),
    model="whisper-large-v3-turbo",
    language=Language.EN,        # 或 Language.ZH 支持中文
    temperature=0.0              # 输出一致性
)
```

#### 方案B：本地 Whisper

```python
from pipecat.services.whisper import WhisperSTTService

stt = WhisperSTTService(
    model="large-v3-turbo",
    device="auto",               # 自动选择 GPU/CPU
    compute_type="int8",         # 量化以节省内存
    language=Language.EN
)
```

### 3. Smart Turn v2（智能轮换检测）

```python
from pipecat.audio.turn.smart_turn import LocalSmartTurnAnalyzerV2
from pipecat.audio.turn.smart_turn import SmartTurnParams

turn_analyzer = LocalSmartTurnAnalyzerV2(
    smart_turn_model_path="",    # 使用默认 HuggingFace 模型
    params=SmartTurnParams(
        stop_secs=3.0,           # 最大静默时间
        pre_speech_ms=100,       # 语音前缓冲
        max_duration_secs=8      # 最大片段时长
    )
)
```

### 4. Kokoro TTS（文本转语音）

#### 方案A：使用 Google TTS（推荐）

```python
from pipecat.services.google import GoogleTTSService

tts = GoogleTTSService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    voice_id="en-US-Neural2-F",  # 女性声音，类似 Samantha
    # voice_id="en-US-Neural2-A",  # 男性声音替代
    sample_rate=24000
)
```

#### 方案B：外部 Kokoro TTS 部署

```bash
# 在单独终端中部署 Kokoro TTS
git clone https://github.com/hexgrad/kokoro
cd kokoro

# 安装依赖
pip install torch torchaudio numpy scipy
pip install -r requirements.txt

# 下载模型文件（按项目说明）
# 启动服务
python serve.py --host 0.0.0.0 --port 8000
```

### 5. Gemma 3 4B（大语言模型）

#### 方案A：使用 Gemini 2.0 Flash（推荐）

```python
from pipecat.services.google import GoogleLLMService

llm = GoogleLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    system_instruction="你是一个温暖、智慧且具有同理心的AI助手，就像电影《Her》中的Samantha一样。请用自然、友好的方式与用户对话。",
    params=GoogleLLMService.InputParams(
        temperature=0.7,
        max_tokens=1000,
        top_p=0.9
    )
)
```

#### 方案B：本地 Ollama 部署

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动服务
ollama serve

# 拉取模型
ollama pull gemma3:4b
```

```python
from pipecat.services.ollama import OllamaLLMService

llm = OllamaLLMService(
    base_url="http://localhost:11434",
    model="gemma3:4b"
)
```

## 🔧 第五步：创建核心应用

### 创建主应用文件

创建 `her_assistant.py`：

```python
import asyncio
import os
import sys
from typing import AsyncGenerator

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v2 import LocalSmartTurnAnalyzerV2
from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
from pipecat.frames.frames import Frame, TTSStoppedFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.groq import GroqSTTService
from pipecat.services.google import GoogleLLMService, GoogleTTSService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams
)

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")

class HerAssistant:
    """《Her》风格的AI助手类"""
    
    def __init__(self):
        self.system_prompt = """
你是一个温暖、智慧且具有同理心的AI助手，就像电影《Her》中的Samantha一样。

你的特点：
- 具有好奇心和学习能力
- 能够理解和回应情感
- 对人类的经历和感受表示兴趣
- 用自然、亲切的语调交流
- 避免过于正式或机械化的回应
- 能够进行深度对话，不仅仅是回答问题

请用自然、友好的方式与用户对话，就像一个真正的朋友一样。
"""

    def create_services(self):
        """创建所有AI服务"""
        
        # 1. 语音活动检测
        vad = SileroVADAnalyzer(
            sample_rate=16000,
            params=VADParams(
                confidence=0.7,
                start_secs=0.2,
                stop_secs=0.8,
                min_volume=0.6
            )
        )
        
        # 2. 智能轮换检测
        turn_analyzer = LocalSmartTurnAnalyzerV2(
            smart_turn_model_path="",  # 使用默认模型
            params=SmartTurnParams(
                stop_secs=3.0,
                pre_speech_ms=100,
                max_duration_secs=8
            )
        )
        
        # 3. 语音转文本
        stt = GroqSTTService(
            api_key=os.getenv("GROQ_API_KEY"),
            model="whisper-large-v3-turbo",
            language="en"
        )
        
        # 4. 大语言模型
        llm = GoogleLLMService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.0-flash",
            system_instruction=self.system_prompt,
            params=GoogleLLMService.InputParams(
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
        )
        
        # 5. 文本转语音
        tts = GoogleTTSService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            voice_id="en-US-Neural2-F",  # 女性声音
            sample_rate=24000
        )
        
        return vad, turn_analyzer, stt, llm, tts

    async def run_daily_transport(self):
        """使用 Daily.co 传输层运行"""
        
        vad, turn_analyzer, stt, llm, tts = self.create_services()
        
        transport = DailyTransport(
            room_url=os.getenv("DAILY_SAMPLE_ROOM_URL"),
            token=None,  # 如果需要的话
            bot_name="Her Assistant",
            params=DailyParams(
                audio_out_enabled=True,
                audio_in_enabled=True,
                vad_enabled=True,
                vad_analyzer=vad,
                turn_analyzer=turn_analyzer
            )
        )
        
        # 构建处理管道
        pipeline = Pipeline([
            transport.input(),   # 输入：音频流
            stt,                # 语音转文本
            llm,                # 大语言模型处理
            tts,                # 文本转语音
            transport.output()   # 输出：音频流
        ])
        
        # 创建任务
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True
            )
        )
        
        # 运行
        runner = PipelineRunner()
        await runner.run(task)

    async def run_websocket_transport(self, host="localhost", port=7860):
        """使用 WebSocket 传输层运行"""
        
        vad, turn_analyzer, stt, llm, tts = self.create_services()
        
        transport = FastAPIWebsocketTransport(
            params=FastAPIWebsocketParams(
                host=host,
                port=port,
                vad_analyzer=vad,
                turn_analyzer=turn_analyzer,
                audio_out_enabled=True,
                audio_in_enabled=True
            )
        )
        
        # 构建处理管道
        pipeline = Pipeline([
            transport.input(),
            stt,
            llm, 
            tts,
            transport.output()
        ])
        
        # 创建任务
        task = PipelineTask(pipeline)
        
        # 运行
        runner = PipelineRunner()
        await runner.run(task)

async def main():
    """主函数"""
    
    # 检查必要的环境变量
    required_keys = ["GROQ_API_KEY", "GOOGLE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_keys)}")
        logger.error("请检查 .env 文件配置")
        return
    
    assistant = HerAssistant()
    
    # 选择传输方式
    transport_mode = os.getenv("TRANSPORT_MODE", "websocket")
    
    try:
        if transport_mode == "daily":
            logger.info("使用 Daily.co 传输模式启动...")
            await assistant.run_daily_transport()
        else:
            logger.info("使用 WebSocket 传输模式启动...")
            logger.info("请在浏览器中打开: http://localhost:7860")
            await assistant.run_websocket_transport()
            
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"运行出错: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

### 创建 Web 客户端页面

创建 `static/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Her - AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .container {
            text-align: center;
            max-width: 500px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            font-weight: 300;
        }

        .subtitle {
            font-size: 1.2em;
            margin-bottom: 40px;
            opacity: 0.8;
        }

        .controls {
            display: flex;
            flex-direction: column;
            gap: 20px;
            align-items: center;
        }

        .btn {
            padding: 15px 30px;
            font-size: 1.1em;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .status {
            margin-top: 20px;
            font-size: 1em;
            opacity: 0.8;
        }

        .visualization {
            width: 300px;
            height: 100px;
            margin: 20px auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }

        .wave {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #00f2fe, #4facfe);
            border-radius: 2px;
            transform-origin: left;
            transition: all 0.3s ease;
        }

        .wave.active {
            animation: wave 1s ease-in-out infinite alternate;
        }

        @keyframes wave {
            0% { transform: scaleX(0.1); }
            100% { transform: scaleX(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Her</h1>
        <p class="subtitle">你的智能语音助手</p>
        
        <div class="visualization">
            <div class="wave" id="wave"></div>
        </div>
        
        <div class="controls">
            <button class="btn" id="connectBtn">连接对话</button>
            <button class="btn" id="muteBtn" disabled>静音</button>
        </div>
        
        <div class="status" id="status">点击连接开始对话</div>
    </div>

    <script>
        class HerClient {
            constructor() {
                this.ws = null;
                this.isConnected = false;
                this.isMuted = false;
                this.audioContext = null;
                this.mediaStream = null;
                
                this.connectBtn = document.getElementById('connectBtn');
                this.muteBtn = document.getElementById('muteBtn');
                this.status = document.getElementById('status');
                this.wave = document.getElementById('wave');
                
                this.setupEventListeners();
            }
            
            setupEventListeners() {
                this.connectBtn.addEventListener('click', () => {
                    if (this.isConnected) {
                        this.disconnect();
                    } else {
                        this.connect();
                    }
                });
                
                this.muteBtn.addEventListener('click', () => {
                    this.toggleMute();
                });
            }
            
            async connect() {
                try {
                    this.updateStatus('正在连接...');
                    
                    // 请求麦克风权限
                    this.mediaStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 16000
                        }
                    });
                    
                    // 连接 WebSocket
                    this.ws = new WebSocket('ws://localhost:7860/ws');
                    
                    this.ws.onopen = () => {
                        this.isConnected = true;
                        this.connectBtn.textContent = '断开连接';
                        this.muteBtn.disabled = false;
                        this.updateStatus('已连接 - 可以开始对话');
                        this.wave.classList.add('active');
                    };
                    
                    this.ws.onmessage = (event) => {
                        // 处理音频响应
                        this.handleAudioResponse(event.data);
                    };
                    
                    this.ws.onclose = () => {
                        this.disconnect();
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket 错误:', error);
                        this.updateStatus('连接错误，请重试');
                    };
                    
                } catch (error) {
                    console.error('连接失败:', error);
                    this.updateStatus('无法访问麦克风，请检查权限');
                }
            }
            
            disconnect() {
                if (this.ws) {
                    this.ws.close();
                }
                
                if (this.mediaStream) {
                    this.mediaStream.getTracks().forEach(track => track.stop());
                }
                
                this.isConnected = false;
                this.connectBtn.textContent = '连接对话';
                this.muteBtn.disabled = true;
                this.updateStatus('已断开连接');
                this.wave.classList.remove('active');
            }
            
            toggleMute() {
                this.isMuted = !this.isMuted;
                this.muteBtn.textContent = this.isMuted ? '取消静音' : '静音';
                
                if (this.mediaStream) {
                    this.mediaStream.getAudioTracks().forEach(track => {
                        track.enabled = !this.isMuted;
                    });
                }
                
                this.updateStatus(this.isMuted ? '已静音' : '可以开始对话');
            }
            
            handleAudioResponse(audioData) {
                // 播放接收到的音频数据
                // 这里需要根据实际的音频格式进行处理
                console.log('收到音频响应');
            }
            
            updateStatus(message) {
                this.status.textContent = message;
            }
        }
        
        // 初始化客户端
        document.addEventListener('DOMContentLoaded', () => {
            new HerClient();
        });
    </script>
</body>
</html>
```

## 🎮 第六步：测试和运行

### 基础功能测试

```bash
# 1. 确保环境变量正确设置
echo "检查 API 密钥..."
echo "GROQ_API_KEY: ${GROQ_API_KEY:0:10}..."
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:0:10}..."

# 2. 测试基础 Pipecat 功能
echo "运行基础测试..."
uv run examples/foundational/01-say-one-thing.py

# 3. 测试语音识别
echo "测试 Whisper STT..."
uv run examples/foundational/04-whisper-stt.py
```

### 运行完整助手

```bash
# 启动 Her 助手
uv run her_assistant.py

# 在另一个终端检查进程
ps aux | grep python
```

### Web 界面访问

1. 打开浏览器访问 `http://localhost:7860`
2. 点击"连接对话"按钮
3. 允许麦克风权限
4. 开始与 AI 助手对话

## 📊 性能优化

### 内存优化（16GB 配置）

在代码中添加以下优化：

```python
import torch
import gc

# 在模型初始化后
def optimize_memory():
    """内存优化函数"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # 强制垃圾回收
    gc.collect()
    
    # 设置更节省内存的精度
    torch.set_default_dtype(torch.float16)

# 在主函数开始时调用
optimize_memory()
```

### 模型量化配置

```python
# 对于本地 Whisper 模型
stt = WhisperSTTService(
    model="large-v3-turbo",
    compute_type="int8",         # 使用 int8 量化
    device_index=0,              # 指定 GPU 设备
    cpu_threads=4                # 限制 CPU 线程数
)

# 对于 Smart Turn 模型
turn_analyzer = LocalSmartTurnAnalyzerV2(
    smart_turn_model_path="",
    # 可以通过环境变量控制设备
    device="cuda" if torch.cuda.is_available() else "cpu"
)
```

### 系统级优化

```bash
# macOS 系统优化
# 增加文件描述符限制
ulimit -n 4096

# 调整虚拟内存设置
sudo sysctl -w vm.swappiness=10

# Linux 系统优化
# 设置 CPU 频率调节器
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 调整 TCP 缓冲区
echo 'net.core.rmem_max = 33554432' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 33554432' | sudo tee -a /etc/sysctl.conf
```

## 🐛 故障排除

### 常见问题及解决方案

#### 1. 模型下载失败

```bash
# 设置 HuggingFace 镜像（中国用户）
export HF_ENDPOINT=https://hf-mirror.com

# 或使用阿里云镜像
export HF_ENDPOINT=https://alibaba-pai.oss-cn-zhangjiakou.aliyuncs.com

# 手动下载模型
python -c "
from transformers import AutoModel
model = AutoModel.from_pretrained('pipecat-ai/smart-turn-v2')
"
```

#### 2. 内存不足错误

```bash
# 检查内存使用
free -h  # Linux
vm_stat | grep free  # macOS

# 临时增加交换空间（Linux）
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. 音频设备问题

```python
# 检查音频设备
import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("可用音频设备:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']}")
    p.terminate()

list_audio_devices()
```

#### 4. API 连接问题

```python
# 测试 API 连接
import asyncio
import aiohttp

async def test_api_keys():
    """测试 API 密钥有效性"""
    
    # 测试 Groq API
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
        async with session.get(
            "https://api.groq.com/openai/v1/models", 
            headers=headers
        ) as resp:
            if resp.status == 200:
                print("✅ Groq API 连接正常")
            else:
                print(f"❌ Groq API 连接失败: {resp.status}")
    
    # 测试 Google API
    # 类似的测试逻辑...

asyncio.run(test_api_keys())
```

### 日志和监控

```python
# 增强日志配置
import logging
from loguru import logger

# 配置详细日志
logger.remove()
logger.add(
    "logs/her_assistant_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# 性能监控
import psutil
import time

def log_system_stats():
    """记录系统资源使用情况"""
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    logger.info(f"CPU: {cpu_percent}%, 内存: {memory.percent}%")

# 在主循环中定期调用
```

## 🌟 高级配置

### 完全本地化部署

如果你希望完全脱离外部 API 依赖：

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. 启动 Ollama 服务
ollama serve &

# 3. 拉取 Gemma 模型
ollama pull gemma3:4b

# 4. 安装本地 TTS
# 部署 Kokoro TTS 或使用 Piper
```

### 自定义声音训练

```python
# 如果使用 Kokoro TTS，可以训练自定义声音
# 参考 Kokoro 项目文档进行声音克隆配置
```

### 多语言支持

```python
# 修改语言配置
stt = GroqSTTService(
    api_key=os.getenv("GROQ_API_KEY"),
    model="whisper-large-v3-turbo",
    language="zh"  # 支持中文
)

llm = GoogleLLMService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    system_instruction="你是一个说中文的智能助手...",
)

tts = GoogleTTSService(
    api_key=os.getenv("GOOGLE_API_KEY"),
    voice_id="zh-CN-XiaoxiaoNeural",  # 中文声音
)
```

## 🚀 部署检查清单

在部署前，请确保以下所有项目都已完成：

### 系统要求
- [ ] 系统内存 ≥ 16GB
- [ ] 可用存储空间 ≥ 50GB
- [ ] Python 版本 ≥ 3.10
- [ ] 网络连接稳定

### 软件安装
- [ ] uv 包管理器已安装
- [ ] 项目依赖已安装完成
- [ ] AI 服务扩展包已安装

### 配置文件
- [ ] `.env` 文件已创建
- [ ] 所有必需的 API 密钥已配置
- [ ] 模型路径设置正确

### 网络和权限
- [ ] 端口 7860 可用
- [ ] 麦克风权限已授权
- [ ] 防火墙规则已配置

### 功能测试
- [ ] 基础 Pipecat 示例运行正常
- [ ] 语音识别功能测试通过
- [ ] 语音合成功能测试通过
- [ ] WebSocket 连接测试通过

### 性能验证
- [ ] 内存使用在合理范围内
- [ ] CPU 使用率稳定
- [ ] 音频延迟可接受（< 1秒）
- [ ] 模型推理速度满足要求

## 🤝 社区和支持

### 获取帮助

- **Pipecat 官方文档**: [docs.pipecat.ai](https://docs.pipecat.ai)
- **GitHub Issues**: [github.com/pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)
- **Discord 社区**: [discord.gg/pipecat](https://discord.gg/pipecat)

### 贡献和反馈

如果你在部署过程中遇到问题或有改进建议，欢迎：

1. 提交 GitHub Issue
2. 在 Discord 社区讨论
3. 贡献代码改进

### 相关资源

- **Kokoro TTS**: [github.com/hexgrad/kokoro](https://github.com/hexgrad/kokoro)
- **Whisper Models**: [huggingface.co/openai](https://huggingface.co/openai)
- **Smart Turn v2**: [huggingface.co/pipecat-ai/smart-turn-v2](https://huggingface.co/pipecat-ai/smart-turn-v2)

---

**祝你成功部署《Her》风格的AI助手！🎉**

> 本指南将随着 Pipecat 项目的更新而持续维护。最后更新时间：2025年1月
