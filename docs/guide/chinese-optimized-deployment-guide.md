# Pipecat 中文优化版本部署指南

*最后更新: 2025年1月27日*

## 📖 概述

本指南专为中文用户优化，提供了在 Pipecat 项目中部署中文语音对话系统的完整解决方案。包含中文语音识别（STT）、中文大语言模型（LLM）、中文语音合成（TTS）的最佳配置方案。

## 🎯 主要特性

- **中文语音识别**: 支持普通话、方言识别
- **中文大语言模型**: 集成国产优秀 LLM 服务
- **中文语音合成**: 高质量中文 TTS 服务
- **本地化部署**: 支持完全离线的中文语音对话
- **多方言支持**: 支持粤语、四川话等方言
- **实时对话**: 低延迟的中文语音交互

## 📋 系统要求

### 最低配置
- **操作系统**: Linux (Ubuntu 20.04+)、macOS 或 Windows 10/11
- **Python**: 3.10 或更高版本
- **内存**: 16GB 以上
- **存储**: 20GB 可用空间（用于模型文件）
- **网络**: 稳定的互联网连接（首次下载模型）

### 推荐配置
- **内存**: 32GB 以上
- **GPU**: NVIDIA GPU（支持 CUDA）或 Apple Silicon
- **存储**: SSD 硬盘，50GB+ 可用空间
- **CPU**: 8核心以上

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/pipecat-ai/pipecat.git
cd pipecat

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或者 venv\Scripts\activate  # Windows

# 安装基础依赖
pip install -e .
```

### 2. 中文服务配置

创建 `.env` 配置文件：

```bash
# 复制示例配置
cp examples/foundational/chinese.env.example .env
```

编辑 `.env` 文件，添加必要的 API 密钥：

```env
# ===========================================
# 中文语音识别 (STT) 配置
# ===========================================

# 阿里云语音识别
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
ALIBABA_CLOUD_REGION=cn-shanghai

# 腾讯云语音识别
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
TENCENT_REGION=ap-beijing

# 百度语音识别
BAIDU_API_KEY=your_api_key
BAIDU_SECRET_KEY=your_secret_key

# Azure 语音服务（支持中文）
AZURE_SPEECH_KEY=your_speech_key
AZURE_SPEECH_REGION=eastasia

# ===========================================
# 中文大语言模型 (LLM) 配置
# ===========================================

# 通义千问
DASHSCOPE_API_KEY=your_dashscope_api_key

# 文心一言
BAIDU_QIANFAN_ACCESS_KEY=your_access_key
BAIDU_QIANFAN_SECRET_KEY=your_secret_key

# 智谱 AI
ZHIPUAI_API_KEY=your_zhipuai_api_key

# 月之暗面 Kimi
MOONSHOT_API_KEY=your_moonshot_api_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key

# ===========================================
# 中文语音合成 (TTS) 配置
# ===========================================

# 阿里云语音合成
ALIBABA_TTS_ACCESS_KEY_ID=your_access_key_id
ALIBABA_TTS_ACCESS_KEY_SECRET=your_access_key_secret

# 腾讯云语音合成
TENCENT_TTS_SECRET_ID=your_secret_id
TENCENT_TTS_SECRET_KEY=your_secret_key

# 百度语音合成
BAIDU_TTS_API_KEY=your_api_key
BAIDU_TTS_SECRET_KEY=your_secret_key

# Azure 语音合成
AZURE_TTS_KEY=your_tts_key
AZURE_TTS_REGION=eastasia

# ===========================================
# 本地化 TTS 配置
# ===========================================

# Kokoro TTS 中文版本
KOKORO_TTS_MODEL_PATH=./models/kokoro-zh
KOKORO_TTS_VOICE=zh-CN-female

# XTTS 中文配置
XTTS_MODEL_PATH=./models/xtts-zh
XTTS_SPEAKER_WAV=./voices/chinese_speaker.wav

# ===========================================
# 语言和地区设置
# ===========================================

# 默认语言
DEFAULT_LANGUAGE=zh-CN

# 支持的方言
SUPPORTED_DIALECTS=zh-CN,zh-TW,zh-HK,yue-CN,wuu-CN

# 时区设置
TIMEZONE=Asia/Shanghai
```

### 3. 运行中文演示

```bash
# 运行基础中文对话演示
python examples/foundational/chinese-basic-conversation.py

# 运行中文语音助手演示
python examples/foundational/chinese-voice-assistant.py

# 运行多方言支持演示
python examples/foundational/chinese-multi-dialect.py
```

## 🔧 详细配置

### 中文语音识别 (STT) 服务

#### 1. 阿里云语音识别（推荐）

```python
from pipecat.services.alibaba import AlibabaSpeechSTTService
from pipecat.transcriptions.language import Language

stt = AlibabaSpeechSTTService(
    access_key_id=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    region=os.getenv("ALIBABA_CLOUD_REGION", "cn-shanghai"),
    language=Language.ZH_CN,
    model="paraformer-realtime-8k-v1",  # 中文实时识别模型
    enable_punctuation=True,
    enable_inverse_text_normalization=True,
)
```

#### 2. 腾讯云语音识别

```python
from pipecat.services.tencent import TencentSpeechSTTService

stt = TencentSpeechSTTService(
    secret_id=os.getenv("TENCENT_SECRET_ID"),
    secret_key=os.getenv("TENCENT_SECRET_KEY"),
    region=os.getenv("TENCENT_REGION", "ap-beijing"),
    language=Language.ZH_CN,
    engine_model_type="16k_zh",  # 中文通用模型
)
```

#### 3. Azure 语音服务（多方言支持）

```python
from pipecat.services.azure import AzureSTTService

# 普通话
stt_mandarin = AzureSTTService(
    api_key=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION", "eastasia"),
    language=Language.ZH_CN,
)

# 粤语
stt_cantonese = AzureSTTService(
    api_key=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION", "eastasia"),
    language=Language.YUE_CN,
)
```

### 中文大语言模型 (LLM) 服务

#### 1. 通义千问（推荐）

```python
from pipecat.services.qwen import QwenLLMService

llm = QwenLLMService(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen2.5-72b-instruct",  # 或 qwen-max, qwen-plus
    system_instruction="""你是一个友好、专业的中文AI助手。
    
请遵循以下规则：
1. 使用简体中文回答
2. 回答要简洁明了，适合语音播放
3. 避免使用特殊符号和格式化文本
4. 保持对话自然流畅
5. 根据用户的语言习惯调整回答风格""",
    temperature=0.7,
    max_tokens=200,  # 适合语音输出的长度
)
```

#### 2. 文心一言

```python
from pipecat.services.baidu import BaiduQianfanLLMService

llm = BaiduQianfanLLMService(
    api_key=os.getenv("BAIDU_QIANFAN_ACCESS_KEY"),
    secret_key=os.getenv("BAIDU_QIANFAN_SECRET_KEY"),
    model="ernie-4.0-8k",
    system_instruction="你是一个专业的中文AI助手，请用自然、友好的语气回答用户问题。",
)
```

#### 3. 智谱 AI GLM

```python
from pipecat.services.zhipuai import ZhipuAILLMService

llm = ZhipuAILLMService(
    api_key=os.getenv("ZHIPUAI_API_KEY"),
    model="glm-4-plus",
    system_instruction="你是一个智能的中文语音助手，请提供简洁、准确的回答。",
)
```

### 中文语音合成 (TTS) 服务

#### 1. 阿里云语音合成（推荐）

```python
from pipecat.services.alibaba import AlibabaSpeechTTSService

tts = AlibabaSpeechTTSService(
    access_key_id=os.getenv("ALIBABA_TTS_ACCESS_KEY_ID"),
    access_key_secret=os.getenv("ALIBABA_TTS_ACCESS_KEY_SECRET"),
    region="cn-shanghai",
    voice="xiaoyun",  # 中文女声
    # 其他可选声音: xiaogang(男声), ruoxi(温柔女声), siqi(活泼女声)
    format="wav",
    sample_rate=16000,
    volume=50,
    speech_rate=0,  # 语速：-500到500
    pitch_rate=0,   # 音调：-500到500
)
```

#### 2. 腾讯云语音合成

```python
from pipecat.services.tencent import TencentSpeechTTSService

tts = TencentSpeechTTSService(
    secret_id=os.getenv("TENCENT_TTS_SECRET_ID"),
    secret_key=os.getenv("TENCENT_TTS_SECRET_KEY"),
    region="ap-beijing",
    voice_type=101001,  # 中文女声
    # 其他可选: 101002(中文男声), 101003(中文男声2)
    primary_language=1,  # 1-中文，2-英文
    sample_rate=16000,
    speed=0,  # 语速：-2到2
    volume=0,  # 音量：-10到10
)
```

#### 3. Azure 语音合成（多音色支持）

```python
from pipecat.services.azure import AzureTTSService

tts = AzureTTSService(
    api_key=os.getenv("AZURE_TTS_KEY"),
    region=os.getenv("AZURE_TTS_REGION", "eastasia"),
    voice="zh-CN-XiaoxiaoNeural",  # 中文女声
    # 其他可选声音:
    # zh-CN-YunxiNeural (男声)
    # zh-CN-YunyangNeural (男声新闻播报)
    # zh-CN-XiaochenNeural (女声客服)
    # zh-CN-XiaohanNeural (女声温柔)
    language=Language.ZH_CN,
)
```

## 🌟 本地化部署方案

### 1. Kokoro TTS 中文版本

```bash
# 安装 Kokoro 中文优化版本
git clone https://github.com/DOTATONG/kokoro-zh
cd kokoro-zh

# 配置 Hugging Face 镜像（国内用户）
export HF_ENDPOINT=https://hf-mirror.com

# 安装依赖
pip install kokoro -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动服务
python web.py --host 0.0.0.0 --port 8000
```

在 Pipecat 中使用：

```python
from pipecat.services.kokoro import KokoroTTSService

tts = KokoroTTSService(
    base_url="http://localhost:8000",
    voice="zh-CN-female",
    model="kokoro-zh",
    language=Language.ZH_CN,
)
```

### 2. 本地 Whisper 中文识别

```bash
# 安装 Whisper
pip install openai-whisper

# 下载中文优化模型
whisper --model large-v3 --language Chinese --task transcribe
```

```python
from pipecat.services.whisper import WhisperSTTService

stt = WhisperSTTService(
    model="large-v3",
    language=Language.ZH_CN,
    task="transcribe",
    temperature=0.0,
    no_speech_threshold=0.4,
)
```

### 3. 本地 LLM 部署（Ollama）

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve &

# 拉取中文模型
ollama pull qwen2.5:14b
ollama pull glm4:9b
ollama pull baichuan2:13b
```

```python
from pipecat.services.ollama import OllamaLLMService

llm = OllamaLLMService(
    base_url="http://localhost:11434",
    model="qwen2.5:14b",
    system_instruction="你是一个专业的中文AI助手。",
)
```

## 📱 完整示例

### 基础中文对话机器人

```python
import asyncio
import os
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.azure import AzureSTTService, AzureTTSService
from pipecat.services.qwen import QwenLLMService
from pipecat.services.openai import OpenAILLMContext
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transcriptions.language import Language

async def main():
    # 配置传输层
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="中文AI助手",
        params=DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    # 配置中文语音识别
    stt = AzureSTTService(
        api_key=os.getenv("AZURE_SPEECH_KEY"),
        region=os.getenv("AZURE_SPEECH_REGION"),
        language=Language.ZH_CN,
    )

    # 配置中文大语言模型
    llm = QwenLLMService(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        model="qwen2.5-72b-instruct",
        system_instruction="""你是一个友好、专业的中文AI助手。

请遵循以下规则：
1. 使用简体中文回答
2. 回答要简洁明了，适合语音播放
3. 避免使用特殊符号和格式化文本
4. 保持对话自然流畅
5. 如果用户使用方言，可以适当使用相应的表达方式

你可以帮助用户：
- 回答各种问题
- 提供建议和帮助
- 进行日常对话
- 协助解决问题""",
        temperature=0.7,
        max_tokens=200,
    )

    # 配置中文语音合成
    tts = AzureTTSService(
        api_key=os.getenv("AZURE_TTS_KEY"),
        region=os.getenv("AZURE_TTS_REGION"),
        voice="zh-CN-XiaoxiaoNeural",  # 中文女声
        language=Language.ZH_CN,
    )

    # 设置对话上下文
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的中文AI语音助手。请用自然、友好的语气与用户对话。"
        }
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # 构建处理管道
    pipeline = Pipeline([
        transport.input(),           # 接收用户音频输入
        stt,                        # 语音转文字
        context_aggregator.user(),   # 用户消息聚合
        llm,                        # 大语言模型处理
        tts,                        # 文字转语音
        transport.output(),         # 输出音频响应
        context_aggregator.assistant(),  # 助手消息聚合
    ])

    # 创建任务
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            report_only_initial_ttfb=True,
        ),
    )

    # 事件处理
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        print(f"客户端已连接: {client}")
        # 发送欢迎消息
        await task.queue_frames([
            tts.create_synthesis_task("你好！我是你的中文AI助手，有什么可以帮助你的吗？")
        ])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client, reason):
        print(f"客户端已断开连接: {client}, 原因: {reason}")
        await task.queue_frames([EndFrame()])

    # 启动任务
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎛️ 高级配置

### 1. 多方言支持

```python
from pipecat.processors.filters import LanguageDetectionFilter
from pipecat.services.azure import AzureSTTService, AzureTTSService

# 语言检测和切换
class ChineseDialectHandler:
    def __init__(self):
        self.services = {
            "zh-CN": {  # 普通话
                "stt": AzureSTTService(language=Language.ZH_CN),
                "tts": AzureTTSService(voice="zh-CN-XiaoxiaoNeural"),
            },
            "yue-CN": {  # 粤语
                "stt": AzureSTTService(language=Language.YUE_CN),
                "tts": AzureTTSService(voice="zh-HK-HiuMaanNeural"),
            },
            "wuu-CN": {  # 上海话
                "stt": AzureSTTService(language=Language.WUU_CN),
                "tts": AzureTTSService(voice="zh-CN-YunyeNeural"),
            },
        }
    
    async def detect_and_switch(self, audio_frame):
        # 语言检测逻辑
        detected_language = await self.detect_language(audio_frame)
        return self.services.get(detected_language, self.services["zh-CN"])
```

### 2. 情感语音合成

```python
from pipecat.services.azure import AzureTTSService

# 配置情感语音
tts_emotional = AzureTTSService(
    api_key=os.getenv("AZURE_TTS_KEY"),
    region=os.getenv("AZURE_TTS_REGION"),
    voice="zh-CN-XiaoxiaoNeural",
    style="cheerful",  # 可选: sad, angry, excited, friendly
    style_degree=1.5,  # 情感强度 0.01-2.0
    language=Language.ZH_CN,
)
```

### 3. 实时语音克隆

```python
from pipecat.services.xtts import XTTSService

# 使用 XTTS 进行中文语音克隆
tts_clone = XTTSService(
    model_path="./models/xtts-zh",
    speaker_wav="./voices/target_speaker.wav",  # 目标说话人音频
    language=Language.ZH_CN,
    temperature=0.7,
    length_penalty=1.0,
    repetition_penalty=5.0,
)
```

## 🔍 性能优化

### 1. 模型量化

```python
# 使用量化模型减少内存占用
from pipecat.services.whisper import WhisperSTTService

stt_quantized = WhisperSTTService(
    model="large-v3-turbo-q4",  # 4位量化版本
    language=Language.ZH_CN,
    device="cuda",  # 或 "mps" for Apple Silicon
    compute_type="int8",  # 使用 int8 计算
)
```

### 2. 批处理优化

```python
from pipecat.processors.aggregators import SentenceAggregator

# 句子级别聚合，减少 TTS 调用次数
sentence_aggregator = SentenceAggregator()

pipeline = Pipeline([
    transport.input(),
    stt,
    sentence_aggregator,  # 聚合完整句子
    context_aggregator.user(),
    llm,
    tts,
    transport.output(),
    context_aggregator.assistant(),
])
```

### 3. 缓存策略

```python
from pipecat.processors.caching import TTSCache

# TTS 结果缓存
tts_cache = TTSCache(
    max_size=1000,  # 最大缓存条目
    ttl=3600,       # 缓存时间（秒）
)

pipeline = Pipeline([
    transport.input(),
    stt,
    context_aggregator.user(),
    llm,
    tts_cache,  # 添加缓存层
    tts,
    transport.output(),
    context_aggregator.assistant(),
])
```

## 📊 监控和调试

### 1. 性能监控

```python
import psutil
import time
from loguru import logger

class ChinesePerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        
    async def log_metrics(self):
        """记录性能指标"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        logger.info(f"CPU使用率: {cpu_percent}%")
        logger.info(f"内存使用率: {memory.percent}%")
        logger.info(f"处理请求数: {self.request_count}")
        
        # 计算平均响应时间
        avg_response_time = (time.time() - self.start_time) / max(self.request_count, 1)
        logger.info(f"平均响应时间: {avg_response_time:.2f}秒")

# 在管道中添加监控
monitor = ChinesePerformanceMonitor()

@transport.event_handler("on_audio_received")
async def on_audio_received(transport, audio_frame):
    monitor.request_count += 1
    await monitor.log_metrics()
```

### 2. 错误处理

```python
from pipecat.processors.filters import ErrorHandlingFilter

class ChineseErrorHandler(ErrorHandlingFilter):
    async def handle_stt_error(self, error):
        logger.error(f"语音识别错误: {error}")
        return "抱歉，我没有听清楚，请再说一遍。"
    
    async def handle_llm_error(self, error):
        logger.error(f"语言模型错误: {error}")
        return "抱歉，我现在无法处理您的请求，请稍后再试。"
    
    async def handle_tts_error(self, error):
        logger.error(f"语音合成错误: {error}")
        # 返回静默或错误提示音
        return None

# 添加到管道
error_handler = ChineseErrorHandler()
pipeline.add_processor(error_handler)
```

## 🚀 部署检查清单

在部署前，请确保以下所有项目都已完成：

### 系统要求
- [ ] 系统内存 ≥ 16GB
- [ ] 可用存储空间 ≥ 20GB
- [ ] Python 版本 ≥ 3.10
- [ ] 网络连接稳定

### 软件安装
- [ ] Pipecat 核心库已安装
- [ ] 中文服务扩展包已安装
- [ ] 必要的系统依赖已安装

### API 配置
- [ ] `.env` 文件已创建并配置
- [ ] 所有必需的 API 密钥已获取
- [ ] 服务配额和限制已确认

### 语言设置
- [ ] 系统语言环境已设置为中文
- [ ] 时区设置为 Asia/Shanghai
- [ ] 字符编码设置为 UTF-8

### 功能测试
- [ ] 中文语音识别功能测试通过
- [ ] 中文语言模型响应测试通过
- [ ] 中文语音合成功能测试通过
- [ ] 端到端对话测试通过

### 性能验证
- [ ] 内存使用在合理范围内
- [ ] CPU 使用率稳定
- [ ] 音频延迟可接受（< 2秒）
- [ ] 识别准确率满足要求

## 🆘 常见问题

### Q: 中文识别准确率不高怎么办？
A: 
1. 检查音频质量，确保清晰无噪音
2. 调整 VAD 参数，优化语音检测
3. 使用专门的中文 STT 服务
4. 考虑添加自定义词汇表

### Q: 语音合成听起来不自然？
A: 
1. 尝试不同的声音模型
2. 调整语速和音调参数
3. 使用情感语音合成
4. 考虑使用本地 TTS 模型

### Q: 响应延迟太高？
A: 
1. 使用本地模型减少网络延迟
2. 启用结果缓存
3. 优化模型量化
4. 调整批处理参数

### Q: 如何支持多种方言？
A: 
1. 配置多个 STT/TTS 服务
2. 实现语言检测逻辑
3. 动态切换服务配置
4. 使用支持多方言的模型

## 📚 相关资源

- [Pipecat 官方文档](https://docs.pipecat.ai)
- [中文语音服务对比](./chinese-speech-services-comparison.md)
- [本地化部署最佳实践](./chinese-local-deployment-best-practices.md)
- [性能优化指南](./chinese-performance-optimization.md)

## 🤝 社区支持

- **GitHub Issues**: [提交问题和建议](https://github.com/pipecat-ai/pipecat/issues)
- **Discord 社区**: [加入讨论](https://discord.gg/pipecat)
- **中文用户群**: 添加微信群获取中文支持

---

*本指南持续更新中，如有问题或建议，欢迎提交 Issue 或 PR。*
