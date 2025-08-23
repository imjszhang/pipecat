# Gemma 3:4b 本地部署攻略

> 📅 创建日期：2025年8月23日  
> 🎯 目标：在 Pipecat 项目中本地部署 Google Gemma 3:4b 模型  
> 🔧 适用平台：macOS、Linux、Windows  

## 📋 目录

- [系统要求](#系统要求)
- [安装 Ollama](#安装-ollama)
- [部署 Gemma 3:4b 模型](#部署-gemma-34b-模型)
- [在 Pipecat 中集成使用](#在-pipecat-中集成使用)
- [完整示例代码](#完整示例代码)
- [性能优化](#性能优化)
- [故障排除](#故障排除)
- [常见问题](#常见问题)

## 🖥️ 系统要求

### 最低配置
- **内存**：8GB RAM（推荐 16GB+）
- **存储**：10GB 可用空间
- **CPU**：支持 AVX2 指令集的现代处理器
- **操作系统**：
  - macOS 11.0+ (Big Sur)
  - Ubuntu 18.04+ / Debian 10+
  - Windows 10+ (WSL2 推荐)

### 推荐配置
- **内存**：16GB+ RAM
- **GPU**：支持 CUDA 的 NVIDIA GPU（可选，用于加速）
- **存储**：SSD 硬盘，20GB+ 可用空间

## 🚀 安装 Ollama

Ollama 是运行本地大语言模型的最佳工具，支持 Gemma 3:4b 模型。

### macOS 安装

```bash
# 方法 1：使用官方安装脚本（推荐）
curl -fsSL https://ollama.ai/install.sh | sh

# 方法 2：使用 Homebrew
brew install ollama
```

### Linux 安装

```bash
# Ubuntu/Debian
curl -fsSL https://ollama.ai/install.sh | sh

# 或者手动安装
sudo apt update
sudo apt install curl
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows 安装

1. 访问 [Ollama 官网](https://ollama.ai/download)
2. 下载 Windows 安装包
3. 运行安装程序并按提示完成安装

或者在 WSL2 中使用 Linux 安装方法。

### 验证安装

```bash
# 检查 Ollama 版本
ollama --version

# 启动 Ollama 服务
ollama serve
```

## 🤖 部署 Gemma 3:4b 模型

### 启动 Ollama 服务

```bash
# 在后台启动 Ollama 服务
ollama serve &

# 或者在新终端窗口中启动
ollama serve
```

服务默认运行在 `http://localhost:11434`

### 下载 Gemma 3:4b 模型

```bash
# 拉取 Gemma 3:4b 模型（约 2.6GB）
ollama pull gemma2:2b

# 如果需要 4B 版本（当可用时）
ollama pull gemma2:4b

# 查看已安装的模型
ollama list
```

### 测试模型

```bash
# 直接与模型对话测试
ollama run gemma2:2b

# 在对话中输入测试内容
>>> 你好，请介绍一下你自己
>>> /bye  # 退出对话
```

## 🔧 在 Pipecat 中集成使用

### 1. 安装 Pipecat 依赖

确保已安装 Pipecat 及其 Ollama 支持：

```bash
# 进入项目目录
cd /Volumes/home_x/github/fork/pipecat

# 安装依赖（如果使用 uv）
uv pip install -e ".[ollama]"

# 或使用 pip
pip install -e ".[ollama]"
```

### 2. 基础配置

创建 `.env` 文件（如果不存在）：

```bash
# .env 文件内容
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:2b

# 其他可选配置
DEEPGRAM_API_KEY=your_deepgram_key  # 用于语音识别
CARTESIA_API_KEY=your_cartesia_key  # 用于语音合成
```

### 3. Python 代码集成

```python
import os
from dotenv import load_dotenv
from pipecat.services.ollama.llm import OLLamaLLMService

load_dotenv()

# 创建 Ollama LLM 服务实例
llm = OLLamaLLMService(
    base_url="http://localhost:11434",
    model="gemma2:2b",  # 或 gemma2:4b
    # 可选参数
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
)
```

## 📱 完整示例代码

### 基础对话机器人

创建 `gemma_chatbot.py`：

```python
#!/usr/bin/env python3
"""
Gemma 3:4b 本地对话机器人示例
使用 Pipecat + Ollama 实现
"""

import asyncio
import os
import sys
from typing import AsyncGenerator

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# 加载环境变量
load_dotenv()

async def main():
    """主函数"""
    
    # 检查 Ollama 服务是否运行
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            logger.error("Ollama 服务未运行，请先启动：ollama serve")
            return
    except Exception as e:
        logger.error(f"无法连接到 Ollama 服务：{e}")
        return

    # 配置传输层（Daily.co WebRTC）
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="Gemma助手",
        params=DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    # 配置语音识别（STT）
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        model="nova-2",
        language="zh",  # 支持中文
    )

    # 配置 Gemma 3:4b 模型
    llm = OLLamaLLMService(
        base_url="http://localhost:11434",
        model="gemma2:2b",  # 根据实际下载的模型调整
        temperature=0.7,
        max_tokens=500,
    )

    # 配置语音合成（TTS）
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # 英文女声
        # 如需中文声音，使用：
        # voice_id="zh-CN-XiaoxiaoNeural",
    )

    # 设置对话上下文
    messages = [
        {
            "role": "system",
            "content": """你是一个友好、有帮助的AI助手，基于Google的Gemma模型。
            
请遵循以下规则：
1. 用简洁、自然的语言回答问题
2. 避免使用特殊符号，因为回答会被转换为语音
3. 保持对话友好和有帮助
4. 如果不确定答案，请诚实说明
5. 回答长度控制在1-2句话内，适合语音播放"""
        }
    ]

    # 创建上下文管理器
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # 构建处理管道
    pipeline = Pipeline([
        transport.input(),      # 音频输入
        stt,                   # 语音转文字
        context_aggregator.user(),  # 用户消息聚合
        llm,                   # Gemma 模型处理
        tts,                   # 文字转语音
        transport.output(),    # 音频输出
        context_aggregator.assistant(),  # 助手消息聚合
    ])

    # 创建任务
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # 事件处理
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("客户端已连接")
        # 发送欢迎消息
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("客户端已断开连接")
        await task.cancel()

    # 运行管道
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
```

### 简化版本（仅文本对话）

创建 `simple_gemma_chat.py`：

```python
#!/usr/bin/env python3
"""
简化版 Gemma 对话示例
仅支持文本输入输出
"""

import asyncio
from pipecat.services.ollama.llm import OLLamaLLMService

async def simple_chat():
    """简单的文本对话"""
    
    # 创建 Gemma 服务
    llm = OLLamaLLMService(
        base_url="http://localhost:11434",
        model="gemma2:2b",
        temperature=0.7,
    )
    
    print("🤖 Gemma 助手已启动！输入 'quit' 退出对话。")
    print("-" * 50)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
                
            if not user_input:
                continue
            
            print("🤖 Gemma: ", end="", flush=True)
            
            # 发送消息到模型（这里需要根据实际 API 调整）
            # 注意：这是简化示例，实际使用需要配合完整的 Pipecat 管道
            response = f"收到您的消息：{user_input}（这是示例回复）"
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")

if __name__ == "__main__":
    asyncio.run(simple_chat())
```

## ⚡ 性能优化

### 1. 内存优化

```bash
# 设置 Ollama 内存限制
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_MAX_QUEUE=512

# 重启 Ollama 服务
ollama serve
```

### 2. GPU 加速（如果有 NVIDIA GPU）

```bash
# 检查 GPU 支持
nvidia-smi

# Ollama 会自动检测并使用 GPU
# 确保安装了 CUDA 驱动
```

### 3. 模型量化

```bash
# 使用量化版本的模型（更小、更快）
ollama pull gemma2:2b-q4_0  # 4位量化版本
ollama pull gemma2:2b-q8_0  # 8位量化版本
```

### 4. 并发设置

```python
# 在 OLLamaLLMService 中设置
llm = OLLamaLLMService(
    base_url="http://localhost:11434",
    model="gemma2:2b",
    # 性能参数
    temperature=0.7,
    max_tokens=300,  # 减少最大令牌数
    top_p=0.9,
    num_predict=256,  # Ollama 特定参数
)
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. Ollama 服务无法启动

```bash
# 检查端口占用
lsof -i :11434

# 杀死占用进程
kill -9 <PID>

# 重新启动
ollama serve
```

#### 2. 模型下载失败

```bash
# 检查网络连接
ping ollama.ai

# 使用代理（如果需要）
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# 重新下载
ollama pull gemma2:2b
```

#### 3. 内存不足

```bash
# 检查系统内存
free -h  # Linux
vm_stat  # macOS

# 使用更小的模型
ollama pull gemma2:2b-q4_0
```

#### 4. Pipecat 集成问题

```python
# 检查 Ollama 连接
import requests
try:
    response = requests.get("http://localhost:11434/api/tags")
    print("Ollama 状态:", response.status_code)
    print("可用模型:", response.json())
except Exception as e:
    print("连接错误:", e)
```

### 日志调试

```bash
# 启用详细日志
export OLLAMA_DEBUG=1
ollama serve

# 查看 Pipecat 日志
export PYTHONPATH=/path/to/pipecat
python -m loguru.logger DEBUG your_script.py
```

## ❓ 常见问题

### Q: Gemma 3:4b 和 Gemma 2:2b 有什么区别？

A: 
- **Gemma 2:2b**：20亿参数，更快，内存需求更低（约4GB）
- **Gemma 3:4b**：40亿参数，更智能，内存需求更高（约8GB）
- 目前 Ollama 主要支持 Gemma 2 系列，Gemma 3 支持正在开发中

### Q: 如何切换不同的模型？

```bash
# 查看可用模型
ollama list

# 拉取其他模型
ollama pull llama3.2:3b
ollama pull qwen2.5:7b

# 在代码中切换
llm = OLLamaLLMService(model="llama3.2:3b")
```

### Q: 支持中文吗？

A: 是的，Gemma 模型支持中文，但建议：
1. 使用中文优化的模型（如 Qwen）
2. 在系统提示中指定使用中文
3. 配置中文语音识别和合成

### Q: 如何提高响应速度？

1. 使用量化模型（q4_0, q8_0）
2. 减少 max_tokens 参数
3. 使用 GPU 加速
4. 优化系统提示长度

### Q: 可以离线使用吗？

A: 是的！一旦模型下载完成，Gemma + Ollama 可以完全离线运行，无需网络连接。

## 📚 参考资源

- [Ollama 官方文档](https://ollama.ai/docs)
- [Gemma 模型介绍](https://ai.google.dev/gemma)
- [Pipecat 文档](https://docs.pipecat.ai)
- [Daily.co WebRTC 平台](https://daily.co)

## 🤝 贡献

如果您在使用过程中遇到问题或有改进建议，欢迎：

1. 提交 Issue
2. 发起 Pull Request
3. 分享使用经验

---

**最后更新**：2025年8月23日  
**版本**：v1.0  
**作者**：Pipecat 社区
