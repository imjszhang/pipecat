# Silero VAD 部署攻略

## 1. 概述

**Silero VAD (Voice Activity Detection)** 是一个基于 ONNX 的高精度语音活动检测模型，在 Pipecat 框架中用于实时检测音频流中的语音活动。它支持 8kHz 和 16kHz 采样率，具有高准确性和低延迟的特点。

## 2. 系统要求

### 2.1 基础要求
- **Python 版本**: 3.10 或更高版本
- **内存**: 至少 1GB 内存
- **CPU**: 支持现代指令集（AVX、AVX2 等）的 CPU

### 2.2 核心依赖
- `onnxruntime~=1.20.1` - ONNX 模型运行时
- `numpy>=1.26.4,<3` - 数值计算
- `loguru~=0.7.3` - 日志记录

## 3. 安装部署

### 3.1 通过 Pipecat 安装（推荐）

```bash
# 安装 Pipecat 及 Silero VAD 扩展
pip install pipecat-ai[silero]

# 或者安装完整的 quickstart 包
pip install pipecat-ai[webrtc,silero,deepgram,openai,cartesia,runner]
```

### 3.2 独立安装 ONNX Runtime

```bash
# 如果需要单独安装 ONNX Runtime
pip install onnxruntime>=1.20.1
```

### 3.3 GPU 支持（可选）

```bash
# 如果需要 GPU 加速（通常 CPU 已足够快）
pip install onnxruntime-gpu>=1.20.1
```

## 4. 代码实现

### 4.1 基础用法

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer

# 创建 Silero VAD 分析器
vad_analyzer = SileroVADAnalyzer()
```

### 4.2 带参数配置的用法

```python
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

# 自定义 VAD 参数
vad_params = VADParams(
    confidence=0.7,      # 语音检测置信度阈值 (0.0-1.0)
    start_secs=0.2,      # 确认语音开始前的等待时间（秒）
    stop_secs=0.8,       # 确认语音结束前的等待时间（秒）
    min_volume=0.6       # 最小音量阈值 (0.0-1.0)
)

# 创建带自定义参数的 VAD 分析器
vad_analyzer = SileroVADAnalyzer(
    sample_rate=16000,   # 采样率（8000 或 16000）
    params=vad_params
)
```

### 4.3 在传输层中使用

#### Daily Transport
```python
from pipecat.transports.services.daily import DailyParams

transport_params = DailyParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    vad_analyzer=SileroVADAnalyzer()
)
```

#### WebRTC Transport
```python
from pipecat.transports.base_transport import TransportParams

transport_params = TransportParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    vad_analyzer=SileroVADAnalyzer()
)
```

#### FastAPI WebSocket Transport
```python
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams

transport_params = FastAPIWebsocketParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    vad_analyzer=SileroVADAnalyzer()
)
```

### 4.4 完整的 Pipeline 示例

```python
import os
from dotenv import load_dotenv
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.transports.base_transport import TransportParams

load_dotenv()

# 配置 VAD 参数
vad_params = VADParams(
    confidence=0.7,      # 调整语音检测敏感度
    start_secs=0.2,      # 语音开始确认时间
    stop_secs=0.8,       # 语音结束确认时间
    min_volume=0.6       # 最小音量阈值
)

# 创建传输参数
transport_params = TransportParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    vad_analyzer=SileroVADAnalyzer(params=vad_params)
)

# 创建服务
stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))
tts = CartesiaTTSService(api_key=os.getenv("CARTESIA_API_KEY"))

# 构建 Pipeline
pipeline = Pipeline([
    transport.input(),
    stt,
    llm,
    tts,
    transport.output()
])
```

## 5. 参数调优指南

### 5.1 默认参数值
```python
VAD_CONFIDENCE = 0.7     # 置信度阈值
VAD_START_SECS = 0.2     # 语音开始确认时间
VAD_STOP_SECS = 0.8      # 语音结束确认时间
VAD_MIN_VOLUME = 0.6     # 最小音量阈值
```

### 5.2 参数调优建议

#### **confidence** (置信度阈值)
- **范围**: 0.0 - 1.0
- **默认值**: 0.7
- **调优建议**:
  - 提高值（0.8-0.9）：减少误检，适用于噪音环境
  - 降低值（0.5-0.6）：提高敏感度，适用于安静环境

#### **start_secs** (语音开始确认时间)
- **范围**: 0.1 - 1.0 秒
- **默认值**: 0.2
- **调优建议**:
  - 减少值（0.1）：更快响应，但可能增加误触发
  - 增加值（0.3-0.5）：更稳定检测，但响应稍慢

#### **stop_secs** (语音结束确认时间)
- **范围**: 0.3 - 2.0 秒
- **默认值**: 0.8
- **调优建议**:
  - 减少值（0.3-0.5）：快速检测语音结束，适用于快节奏对话
  - 增加值（1.0-1.5）：避免错误截断，适用于思考停顿较多的场景

#### **min_volume** (最小音量阈值)
- **范围**: 0.0 - 1.0
- **默认值**: 0.6
- **调优建议**:
  - 提高值（0.7-0.8）：过滤低音量噪音
  - 降低值（0.3-0.5）：检测轻声说话

### 5.3 针对不同场景的参数配置

#### 安静环境配置
```python
quiet_params = VADParams(
    confidence=0.6,
    start_secs=0.15,
    stop_secs=0.6,
    min_volume=0.4
)
```

#### 噪音环境配置
```python
noisy_params = VADParams(
    confidence=0.8,
    start_secs=0.3,
    stop_secs=1.0,
    min_volume=0.7
)
```

#### 快节奏对话配置
```python
fast_conversation_params = VADParams(
    confidence=0.7,
    start_secs=0.1,
    stop_secs=0.4,
    min_volume=0.5
)
```

#### 多模态实时通信配置（如 Gemini）
```python
multimodal_params = VADParams(
    confidence=0.7,
    start_secs=0.2,
    stop_secs=0.5,  # 更快的结束检测以配合实时API
    min_volume=0.6
)
```

## 6. 性能优化

### 6.1 模型状态管理
- Silero VAD 每 5 秒自动重置内部状态，防止内存泄漏
- 模型默认强制使用 CPU 执行（`force_onnx_cpu=True`）

### 6.2 音频处理优化
- 支持的采样率：8000Hz 和 16000Hz
- 所需帧数：
  - 16kHz: 512 帧
  - 8kHz: 256 帧
- 音频格式：16-bit PCM，单声道

### 6.3 线程配置
```python
# ONNX Runtime 线程配置（在 SileroOnnxModel 中）
opts = onnxruntime.SessionOptions()
opts.inter_op_num_threads = 1  # 操作间线程数
opts.intra_op_num_threads = 1  # 操作内线程数
```

## 7. 故障排除

### 7.1 常见错误及解决方案

#### ImportError: No module named 'onnxruntime'
```bash
# 解决方案：安装 ONNX Runtime
pip install pipecat-ai[silero]
```

#### "Input audio chunk is too short" 错误
- **原因**: 音频块太短
- **解决方案**: 确保音频块长度满足最小要求

#### VAD 检测不准确
- **解决方案**: 调整 `confidence` 和 `min_volume` 参数
- **检查**: 音频采样率是否为 8kHz 或 16kHz

### 7.2 调试技巧

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 监控 VAD 状态
@transport.event_handler("on_vad_state_changed")
async def on_vad_state_changed(transport, state):
    print(f"VAD state changed to: {state}")
```

## 8. 最佳实践

### 8.1 部署建议
1. **首次启动**: 首次运行可能需要10秒左右下载模型
2. **生产环境**: 建议预先下载模型文件
3. **监控**: 实施 VAD 状态监控和日志记录
4. **测试**: 在目标环境中充分测试参数配置

### 8.2 集成建议
1. **延迟优化**: VAD 检测延迟约为参数配置的时间
2. **中断处理**: 结合中断策略使用，提供更好的用户体验
3. **错误处理**: 实施适当的错误恢复机制

### 8.3 维护建议
1. **版本管理**: 定期更新到最新版本以获得性能改进
2. **参数调优**: 根据实际使用场景持续优化参数
3. **性能监控**: 监控 CPU 使用率和内存消耗

通过这份详细的部署攻略，您可以成功在 Pipecat 框架中部署和优化 Silero VAD，为您的语音 AI 应用提供高质量的语音活动检测功能。
