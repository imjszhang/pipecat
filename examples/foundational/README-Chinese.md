# Pipecat 中文优化示例

本目录包含了专为中文用户优化的 Pipecat 示例代码，展示了如何构建高质量的中文语音对话系统。

## 📁 文件说明

### 配置文件
- `chinese.env.example` - 中文优化配置模板
- `README-Chinese.md` - 本说明文件

### 演示脚本
- `chinese-basic-conversation.py` - 基础中文对话机器人
- `chinese-voice-assistant.py` - 中文智能语音助手
- `chinese-multi-dialect.py` - 多方言支持演示

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/pipecat-ai/pipecat.git
cd pipecat

# 安装依赖
pip install -e .

# 复制配置文件
cp examples/foundational/chinese.env.example .env
```

### 2. 配置 API 密钥

编辑 `.env` 文件，添加你的 API 密钥：

```env
# 必需配置
DAILY_ROOM_URL=your_daily_room_url
OPENAI_API_KEY=your_openai_api_key

# 中文语音服务（选择其一）
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastasia
AZURE_TTS_KEY=your_azure_tts_key
AZURE_TTS_REGION=eastasia
```

### 3. 运行演示

```bash
# 基础对话机器人
python examples/foundational/chinese-basic-conversation.py

# 智能语音助手
python examples/foundational/chinese-voice-assistant.py

# 多方言支持
python examples/foundational/chinese-multi-dialect.py
```

## 📋 示例详解

### 基础中文对话机器人 (`chinese-basic-conversation.py`)

**功能特性：**
- 中文语音识别 (STT)
- 中文大语言模型 (LLM)
- 中文语音合成 (TTS)
- 实时语音对话

**支持的服务：**
- STT: Azure, Google, Deepgram
- LLM: OpenAI 兼容模型
- TTS: Azure, Google, Cartesia

**使用场景：**
- 客服机器人
- 语音助手
- 教育应用
- 娱乐对话

### 中文智能语音助手 (`chinese-voice-assistant.py`)

**功能特性：**
- 函数调用能力
- 天气查询
- 时间获取
- 信息搜索
- 提醒设置
- 系统状态监控

**高级功能：**
- 性能监控
- 错误处理
- 用户偏好设置
- 对话历史记录

**使用场景：**
- 智能家居控制
- 办公助手
- 个人助理
- 信息查询系统

### 多方言支持演示 (`chinese-multi-dialect.py`)

**支持方言：**
- 普通话 (zh-CN)
- 粤语 (yue-CN)
- 上海话 (wuu-CN)
- 台湾国语 (zh-TW)
- 香港粤语 (zh-HK)

**核心功能：**
- 自动方言检测
- 动态服务切换
- 方言特色回复
- 跨方言理解

**使用场景：**
- 多地区服务
- 文化传承应用
- 旅游助手
- 教育工具

## 🔧 配置说明

### 语音识别 (STT) 服务

#### Azure Speech Services（推荐）
```python
from pipecat.services.azure import AzureSTTService

stt = AzureSTTService(
    api_key=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION"),
    language=Language.ZH_CN,
)
```

#### Google Cloud Speech
```python
from pipecat.services.google import GoogleSTTService

stt = GoogleSTTService(
    credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    language=Language.ZH_CN,
    model="latest_long",
)
```

#### Deepgram
```python
from pipecat.services.deepgram import DeepgramSTTService

stt = DeepgramSTTService(
    api_key=os.getenv("DEEPGRAM_API_KEY"),
    language=Language.ZH_CN,
    model="nova-2-general",
)
```

### 大语言模型 (LLM) 服务

#### OpenAI 兼容模型
```python
from pipecat.services.openai import OpenAILLMService

llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    base_url=os.getenv("OPENAI_BASE_URL"),  # 支持自定义端点
)
```

### 语音合成 (TTS) 服务

#### Azure Text-to-Speech（推荐）
```python
from pipecat.services.azure import AzureTTSService

tts = AzureTTSService(
    api_key=os.getenv("AZURE_TTS_KEY"),
    region=os.getenv("AZURE_TTS_REGION"),
    voice="zh-CN-XiaoxiaoNeural",  # 中文女声
    language=Language.ZH_CN,
)
```

**可选声音：**
- `zh-CN-XiaoxiaoNeural` - 女声，温柔
- `zh-CN-YunxiNeural` - 男声，成熟
- `zh-CN-YunyangNeural` - 男声，新闻播报
- `zh-CN-XiaochenNeural` - 女声，客服
- `zh-CN-XiaohanNeural` - 女声，温柔

#### Google Text-to-Speech
```python
from pipecat.services.google import GoogleTTSService

tts = GoogleTTSService(
    credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    voice_id="cmn-CN-Wavenet-A",
    language=Language.ZH_CN,
)
```

#### Cartesia
```python
from pipecat.services.cartesia import CartesiaTTSService

tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="a167e0f3-df7e-4d52-a9c3-f949145efdab",
    language=Language.ZH_CN,
)
```

## 🌟 高级功能

### 1. 函数调用

```python
# 定义函数
async def get_weather(location: str) -> Dict[str, Any]:
    # 实现天气查询逻辑
    return {"temperature": "22°C", "condition": "晴天"}

# 配置 LLM
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    tools=[{
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名称"}
            },
            "required": ["location"]
        }
    }]
)
```

### 2. 方言检测

```python
class DialectDetector:
    def detect_dialect(self, text: str) -> Language:
        # 实现方言检测逻辑
        if "乜嘢" in text or "点解" in text:
            return Language.YUE_CN  # 粤语
        elif "侬好" in text or "哪能" in text:
            return Language.WUU_CN  # 上海话
        else:
            return Language.ZH_CN   # 普通话
```

### 3. 性能监控

```python
import psutil
import time

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
    
    async def log_metrics(self):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        logger.info(f"CPU: {cpu_percent}%, 内存: {memory.percent}%")
        logger.info(f"运行时间: {time.time() - self.start_time:.1f}秒")
        logger.info(f"处理请求: {self.request_count}个")
```

## 🔍 故障排除

### 常见问题

#### 1. 语音识别准确率低
**解决方案：**
- 检查音频质量，确保清晰无噪音
- 调整 VAD 参数
- 使用专门的中文 STT 服务
- 添加自定义词汇表

#### 2. 语音合成不自然
**解决方案：**
- 尝试不同的声音模型
- 调整语速和音调参数
- 使用情感语音合成
- 优化文本预处理

#### 3. 响应延迟高
**解决方案：**
- 使用本地模型
- 启用结果缓存
- 优化网络连接
- 调整批处理参数

#### 4. 方言识别错误
**解决方案：**
- 完善方言特征词库
- 调整检测权重
- 增加上下文分析
- 提供手动切换选项

### 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 保存音频文件
```env
SAVE_AUDIO_FILES=true
AUDIO_SAVE_PATH=./debug/audio/
```

#### 3. 记录对话历史
```env
SAVE_CONVERSATIONS=true
CONVERSATION_SAVE_PATH=./debug/conversations/
```

## 📚 相关资源

### 文档
- [Pipecat 中文优化部署指南](../../docs/guide/chinese-optimized-deployment-guide.md)
- [Pipecat 官方文档](https://docs.pipecat.ai)

### API 服务
- [Azure 语音服务](https://azure.microsoft.com/zh-cn/services/cognitive-services/speech-services/)
- [Google Cloud Speech](https://cloud.google.com/speech-to-text)
- [Deepgram](https://deepgram.com/)
- [OpenAI API](https://openai.com/api/)

### 开源项目
- [Kokoro TTS 中文版](https://github.com/DOTATONG/kokoro-zh)
- [Whisper 中文优化](https://github.com/openai/whisper)
- [XTTS 中文支持](https://github.com/coqui-ai/TTS)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进中文支持功能：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目遵循 [BSD 2-Clause License](../../LICENSE)。

---

*如有问题或建议，请提交 Issue 或联系维护者。*
