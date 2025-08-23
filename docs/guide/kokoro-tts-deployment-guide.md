# Kokoro TTS 部署指南

*最后更新: 2025年8月23日*

## 📖 概述

Kokoro TTS 是一款高效的开源文本转语音（TTS）模型，具有仅 8200 万参数的紧凑架构，能够在 CPU 上实现近乎实时的语音生成，在 GPU 上速度更可提升至 50 倍实时。本指南将详细介绍如何部署 Kokoro TTS 并与 Pipecat 项目集成。

## 🎯 主要特性

- **轻量级模型**: 仅 82M 参数，资源占用低
- **高性能**: CPU 近实时，GPU 可达 50x 实时速度
- **多语言支持**: 支持英文、中文等多种语言
- **开源免费**: 完全开源，可自由部署和定制
- **API 兼容**: 支持 HTTP API 调用

## 📋 系统要求

### 最低配置
- **操作系统**: Windows 10/11、Linux 或 macOS
- **Python**: 3.9 或更高版本
- **内存**: 8GB 以上
- **存储**: 5GB 可用空间（用于模型文件）

### 推荐配置
- **内存**: 16GB 以上
- **GPU**: NVIDIA GPU（支持 CUDA）
- **存储**: SSD 硬盘
- **网络**: 稳定的互联网连接（首次下载模型）

## 🚀 部署方法

### 方法一：基础部署（推荐新手）

```bash
# 1. 克隆 Kokoro 官方项目
git clone https://github.com/hexgrad/kokoro
cd kokoro

# 2. 创建虚拟环境（推荐）
python -m venv kokoro-env
source kokoro-env/bin/activate  # Linux/macOS
# 或者 kokoro-env\Scripts\activate  # Windows

# 3. 安装基础依赖
pip install torch torchaudio numpy scipy
pip install -r requirements.txt

# 4. 启动 TTS 服务
python serve.py --host 0.0.0.0 --port 8000
```

### 方法二：Web 界面部署（推荐生产环境）

```bash
# 1. 克隆带 Web 界面的增强版本
git clone https://github.com/jianchang512/kokoro-uiapi
cd kokoro-uiapi

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或者 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 启动服务
python3 app.py
```

**访问地址**: `http://127.0.0.1:5066`

**功能特性**:
- Web 界面操作
- 兼容 OpenAI API
- 多语言配音支持
- 批量处理功能

### 方法三：中文优化版本（推荐中文用户）

```bash
# 1. 克隆中文优化版本
git clone https://github.com/DOTATONG/kokoro-zh
cd kokoro-zh

# 2. 配置 Hugging Face 镜像（国内用户必需）
export HF_ENDPOINT=https://hf-mirror.com

# 3. 安装 Kokoro
pip install kokoro -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 运行 Web 界面
python web.py
```

## 🔧 GPU 加速配置

### CUDA 环境安装

```bash
# 1. 检查 CUDA 版本
nvidia-smi

# 2. 安装对应版本的 PyTorch（以 CUDA 11.8 为例）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 验证 GPU 可用性
python -c "import torch; print(torch.cuda.is_available())"
```

### 性能对比

| 设备类型 | 推理速度 | 内存占用 | 适用场景 |
|---------|---------|---------|---------|
| CPU | 1x 实时 | ~2GB | 开发测试 |
| GPU (RTX 3080) | 50x 实时 | ~4GB | 生产环境 |
| GPU (RTX 4090) | 80x 实时 | ~6GB | 高并发场景 |

## 🔗 与 Pipecat 集成

### 环境配置

在 Pipecat 项目的 `.env` 文件中添加：

```bash
# Kokoro TTS 服务配置
KOKORO_BASE_URL=http://localhost:8000
KOKORO_API_KEY=your_api_key_if_needed
```

### 自定义 TTS 服务实现

创建 `src/pipecat/services/kokoro/tts.py`:

```python
#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Kokoro TTS service implementation.

This module provides integration with Kokoro TTS server for
high-quality text-to-speech synthesis.
"""

import asyncio
from typing import AsyncGenerator, Optional

import aiohttp
from loguru import logger
from pydantic import BaseModel

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    StartFrame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.services.tts_service import TTSService
from pipecat.transcriptions.language import Language
from pipecat.utils.tracing.service_decorators import traced_tts


class KokoroTTSService(TTSService):
    """Kokoro TTS service for high-quality speech synthesis.
    
    This service integrates with a locally deployed Kokoro TTS server
    to provide fast, high-quality text-to-speech synthesis.
    """

    class InputParams(BaseModel):
        """Input parameters for Kokoro TTS synthesis."""
        speed: Optional[float] = 1.0
        pitch: Optional[float] = 1.0
        volume: Optional[float] = 1.0

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        aiohttp_session: aiohttp.ClientSession,
        voice_id: str = "default",
        language: Language = Language.EN,
        params: InputParams = InputParams(),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._base_url = base_url
        self._aiohttp_session = aiohttp_session
        self._voice_id = voice_id
        self._language = language
        self._params = params

    async def start(self, frame: StartFrame):
        await super().start(frame)
        # 检查服务连接
        try:
            async with self._aiohttp_session.get(f"{self._base_url}/health") as response:
                if response.status != 200:
                    logger.error(f"Kokoro TTS service not available at {self._base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Kokoro TTS: {e}")

    @traced_tts
    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech from text using Kokoro TTS.

        Args:
            text: The text to synthesize into speech.

        Yields:
            Frame: Audio frames containing the synthesized speech.
        """
        logger.debug(f"{self}: Generating TTS [{text}]")

        try:
            await self.start_ttfb_metrics()

            payload = {
                "text": text,
                "voice_id": self._voice_id,
                "language": self._language.value,
                "speed": self._params.speed,
                "pitch": self._params.pitch,
                "volume": self._params.volume,
            }

            url = f"{self._base_url}/tts"

            async with self._aiohttp_session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Kokoro TTS error: {error_text}")
                    yield ErrorFrame(f"TTS error: {error_text}")
                    return

                await self.start_tts_usage_metrics(text)
                yield TTSStartedFrame()

                # 流式读取音频数据
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        yield TTSAudioRawFrame(
                            audio=chunk,
                            sample_rate=self.sample_rate,
                            num_channels=1
                        )

                yield TTSStoppedFrame()

        except Exception as e:
            logger.error(f"Kokoro TTS synthesis error: {e}")
            yield ErrorFrame(f"TTS synthesis failed: {str(e)}")
```

### 使用示例

```python
import asyncio
import aiohttp
from pipecat.services.kokoro.tts import KokoroTTSService
from pipecat.transcriptions.language import Language

async def main():
    async with aiohttp.ClientSession() as session:
        # 创建 Kokoro TTS 服务
        tts = KokoroTTSService(
            base_url="http://localhost:8000",
            aiohttp_session=session,
            voice_id="female_voice",
            language=Language.EN,
            params=KokoroTTSService.InputParams(
                speed=1.0,
                pitch=1.0,
                volume=0.8
            )
        )
        
        # 生成语音
        async for frame in tts.run_tts("Hello, this is Kokoro TTS!"):
            # 处理音频帧
            print(f"Received frame: {type(frame)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎛️ 高级配置

### 服务器配置优化

```python
# serve.py 启动参数优化
python serve.py \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --max-requests 1000 \
    --timeout 30 \
    --gpu-memory-fraction 0.8
```

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 克隆项目
RUN git clone https://github.com/hexgrad/kokoro .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["python", "serve.py", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建和运行 Docker 容器
docker build -t kokoro-tts .
docker run -d -p 8000:8000 --name kokoro-tts kokoro-tts
```

### 负载均衡配置

```nginx
# nginx.conf
upstream kokoro_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    location /tts {
        proxy_pass http://kokoro_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_timeout 60s;
    }
}
```

## 🔍 故障排除

### 常见问题

#### 1. 模型下载失败

```bash
# 解决方案：配置镜像源
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_CACHE=/path/to/cache
```

#### 2. CUDA 内存不足

```python
# 在启动脚本中添加
import torch
torch.cuda.empty_cache()

# 或者减少批处理大小
--batch-size 1
```

#### 3. 音频质量问题

```python
# 调整采样率和比特率
tts = KokoroTTSService(
    sample_rate=24000,  # 提高采样率
    params=KokoroTTSService.InputParams(
        speed=0.9,      # 稍微放慢语速
        pitch=1.0,      # 保持原始音调
        volume=0.8      # 适中音量
    )
)
```

#### 4. 服务连接超时

```python
# 增加超时时间
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60)
) as session:
    # 使用 session
```

### 性能监控

```python
import psutil
import time
from loguru import logger

def monitor_system_resources():
    """监控系统资源使用情况"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    logger.info(f"CPU 使用率: {cpu_percent}%")
    logger.info(f"内存使用率: {memory.percent}%")
    logger.info(f"可用内存: {memory.available / 1024**3:.2f}GB")
    
    # GPU 监控（如果可用）
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            logger.info(f"GPU {gpu.id}: {gpu.load*100:.1f}% | 内存: {gpu.memoryUtil*100:.1f}%")
    except ImportError:
        pass

# 在主循环中定期调用
```

## 📊 性能基准测试

### 测试脚本

```python
import time
import asyncio
import statistics
from typing import List

async def benchmark_tts(tts_service, test_texts: List[str], iterations: int = 10):
    """TTS 性能基准测试"""
    results = []
    
    for text in test_texts:
        text_times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            frames = []
            async for frame in tts_service.run_tts(text):
                frames.append(frame)
            
            end_time = time.time()
            text_times.append(end_time - start_time)
        
        avg_time = statistics.mean(text_times)
        std_time = statistics.stdev(text_times)
        
        results.append({
            'text': text[:50] + '...' if len(text) > 50 else text,
            'avg_time': avg_time,
            'std_time': std_time,
            'chars_per_sec': len(text) / avg_time
        })
    
    return results

# 使用示例
test_texts = [
    "Hello, world!",
    "This is a longer sentence to test the performance of Kokoro TTS.",
    "人工智能技术正在快速发展，语音合成是其中的重要应用领域。"
]

# results = await benchmark_tts(tts_service, test_texts)
```

## 🌟 最佳实践

### 1. 生产环境部署建议

- **使用 Docker 容器化部署**
- **配置负载均衡和健康检查**
- **设置适当的资源限制**
- **启用日志记录和监控**
- **定期备份模型文件**

### 2. 性能优化建议

- **使用 GPU 加速（如果可用）**
- **合理设置批处理大小**
- **启用模型量化（减少内存占用）**
- **使用连接池管理 HTTP 连接**
- **缓存常用文本的音频结果**

### 3. 安全考虑

- **限制 API 访问频率**
- **验证输入文本长度和内容**
- **使用 HTTPS 加密传输**
- **设置防火墙规则**
- **定期更新依赖包**

## 📚 相关资源

### 官方资源
- **Kokoro 官方项目**: [github.com/hexgrad/kokoro](https://github.com/hexgrad/kokoro)
- **官方文档**: 查看项目 README 和 Wiki

### 社区资源
- **Web 界面版本**: [github.com/jianchang512/kokoro-uiapi](https://github.com/jianchang512/kokoro-uiapi)
- **中文优化版本**: [github.com/DOTATONG/kokoro-zh](https://github.com/DOTATONG/kokoro-zh)

### 相关工具
- **Pipecat 框架**: [github.com/pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)
- **PyTorch**: [pytorch.org](https://pytorch.org)
- **Hugging Face**: [huggingface.co](https://huggingface.co)

## 🤝 贡献和支持

如果您在使用过程中遇到问题或有改进建议，欢迎：

1. **提交 Issue**: 在相应的 GitHub 项目中报告问题
2. **贡献代码**: 提交 Pull Request 改进项目
3. **分享经验**: 在社区中分享部署和使用经验
4. **文档改进**: 帮助完善文档和教程

---

*本指南将持续更新，以反映最新的技术发展和最佳实践。*
