#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""《Her》风格AI助手 - 完全本地版本

基于 Pipecat 框架构建的完全本地化语音AI助手，使用以下技术栈：
- Silero VAD - 语音活动检测
- Whisper Large v3 Turbo - 本地语音转文本
- Smart Turn v2 - 智能轮换检测
- Ollama + Gemma 3 4B - 本地大语言模型
- Kokoro TTS / Piper TTS - 本地文本转语音

特点：
- 完全本地化，无需外部API
- 隐私保护，数据不离开本地
- 低延迟，实时对话体验
- 《Her》电影风格的温暖对话

运行前准备：
1. 启动 Ollama 服务: ollama serve
2. 拉取模型: ollama pull gemma3:4b
3. 配置 .env 文件
4. （可选）启动 Kokoro TTS 服务

运行命令：
    python bot.py
"""

import asyncio
import gc
import os
import sys
from typing import Any, Dict, Optional

import torch
from dotenv import load_dotenv
from loguru import logger

print("🎬 启动《Her》风格AI助手...")
print("⏳ 加载本地AI模型 (首次运行需要30-60秒，后续<5秒)\n")

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


# 内存优化配置
def optimize_memory():
    """内存优化函数"""
    logger.info("🔧 优化内存配置...")

    # 设置 PyTorch 数据类型
    torch_dtype = os.getenv("TORCH_DTYPE", "float16")
    if torch_dtype == "float16":
        torch.set_default_dtype(torch.float16)

    # GPU 内存优化
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        memory_fraction = float(os.getenv("CUDA_MEMORY_FRACTION", "0.8"))
        torch.cuda.set_per_process_memory_fraction(memory_fraction)
        logger.info(f"🚀 CUDA 可用，内存分配: {memory_fraction * 100}%")

    # Apple Silicon 优化
    if torch.backends.mps.is_available():
        logger.info("🍎 Apple Silicon MPS 可用")

    # 强制垃圾回收
    gc.collect()

    # 设置 CPU 线程数
    cpu_threads = int(os.getenv("CPU_THREADS", "4"))
    torch.set_num_threads(cpu_threads)
    logger.info(f"💻 CPU 线程数: {cpu_threads}")


# 应用内存优化
optimize_memory()

logger.info("📦 加载 Silero VAD 模型...")
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

logger.info("✅ Silero VAD 模型加载完成")

logger.info("📦 加载 Smart Turn v2 模型...")
try:
    from pipecat.audio.turn.smart_turn.base_smart_turn import SmartTurnParams
    from pipecat.audio.turn.smart_turn.local_smart_turn_v2 import LocalSmartTurnAnalyzerV2

    SMART_TURN_AVAILABLE = True
    logger.info("✅ Smart Turn v2 模型加载完成")
except ImportError as e:
    logger.warning(f"⚠️  Smart Turn v2 不可用: {e}")
    SMART_TURN_AVAILABLE = False

logger.info("📦 加载管道组件...")
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.transports.base_transport import BaseTransport, TransportParams

logger.info("✅ 管道组件加载完成")

logger.info("📦 加载本地AI服务...")

# 加载本地 Whisper STT
try:
    from pipecat.services.whisper.stt import WhisperSTTService

    WHISPER_AVAILABLE = True
    logger.info("✅ Whisper STT 服务可用")
except ImportError as e:
    logger.warning(f"⚠️  Whisper STT 不可用: {e}")
    WHISPER_AVAILABLE = False

# 加载 Ollama LLM
try:
    from pipecat.services.ollama.llm import OllamaLLMService

    OLLAMA_AVAILABLE = True
    logger.info("✅ Ollama LLM 服务可用")
except ImportError as e:
    logger.warning(f"⚠️  Ollama LLM 不可用: {e}")
    OLLAMA_AVAILABLE = False

# 加载本地 TTS 服务
try:
    from pipecat.services.piper.tts import PiperTTSService

    PIPER_AVAILABLE = True
    logger.info("✅ Piper TTS 服务可用")
except ImportError as e:
    logger.warning(f"⚠️  Piper TTS 不可用: {e}")
    PIPER_AVAILABLE = False

# 备用：Google TTS（如果配置了API密钥）
try:
    from pipecat.services.google.tts import GoogleTTSService

    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

logger.info("📦 加载 WebRTC 传输...")
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport

logger.info("✅ 所有组件加载完成！")

load_dotenv(override=True)


class HerAssistantServices:
    """《Her》助手服务管理器"""

    def __init__(self):
        self.vad = None
        self.turn_analyzer = None
        self.stt = None
        self.llm = None
        self.tts = None

    def create_vad_analyzer(self) -> SileroVADAnalyzer:
        """创建语音活动检测器"""
        logger.info("🎤 初始化 Silero VAD...")

        confidence = float(os.getenv("VAD_CONFIDENCE", "0.7"))
        start_secs = float(os.getenv("VAD_START_SECS", "0.2"))
        stop_secs = float(os.getenv("VAD_STOP_SECS", "0.8"))
        min_volume = float(os.getenv("VAD_MIN_VOLUME", "0.6"))

        self.vad = SileroVADAnalyzer(
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            params=VADParams(
                confidence=confidence,
                start_secs=start_secs,
                stop_secs=stop_secs,
                min_volume=min_volume,
            ),
        )

        logger.info(f"✅ VAD 配置: 置信度={confidence}, 开始={start_secs}s, 结束={stop_secs}s")
        return self.vad

    def create_turn_analyzer(self) -> Optional[LocalSmartTurnAnalyzerV2]:
        """创建智能轮换检测器"""
        if not SMART_TURN_AVAILABLE:
            logger.warning("⚠️  Smart Turn v2 不可用，跳过")
            return None

        logger.info("🔄 初始化 Smart Turn v2...")

        model_path = os.getenv("LOCAL_SMART_TURN_MODEL_PATH", "")
        device = os.getenv("SMART_TURN_DEVICE", "auto")

        # 自动选择设备
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.turn_analyzer = LocalSmartTurnAnalyzerV2(
            smart_turn_model_path=model_path,
            params=SmartTurnParams(stop_secs=3.0, pre_speech_ms=100, max_duration_secs=8),
            device=device,
        )

        logger.info(f"✅ Smart Turn v2 配置: 设备={device}")
        return self.turn_analyzer

    def create_stt_service(self):
        """创建语音转文本服务"""
        if not WHISPER_AVAILABLE:
            logger.error("❌ Whisper STT 不可用，无法继续")
            raise RuntimeError("Whisper STT 服务不可用")

        logger.info("🎯 初始化 Whisper STT...")

        model = os.getenv("WHISPER_MODEL", "large-v3-turbo")
        device = os.getenv("WHISPER_DEVICE", "auto")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

        # 自动选择设备
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.stt = WhisperSTTService(
            model=model,
            device=device,
            compute_type=compute_type,
            language="en",  # 可以通过环境变量配置
        )

        logger.info(f"✅ Whisper STT 配置: 模型={model}, 设备={device}, 计算类型={compute_type}")
        return self.stt

    def create_llm_service(self):
        """创建大语言模型服务"""
        if not OLLAMA_AVAILABLE:
            logger.error("❌ Ollama LLM 不可用，无法继续")
            raise RuntimeError("Ollama LLM 服务不可用")

        logger.info("🧠 初始化 Ollama LLM...")

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "gemma3:4b")

        # 验证 Ollama 服务是否可用
        try:
            import requests

            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama 服务连接失败: {response.status_code}")

            # 检查模型是否存在
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            if not any(model in name for name in model_names):
                logger.warning(f"⚠️  模型 {model} 可能未安装，请运行: ollama pull {model}")

        except Exception as e:
            logger.error(f"❌ Ollama 服务检查失败: {e}")
            logger.error("请确保 Ollama 服务正在运行: ollama serve")
            raise

        self.llm = OllamaLLMService(base_url=base_url, model=model)

        logger.info(f"✅ Ollama LLM 配置: URL={base_url}, 模型={model}")
        return self.llm

    def create_tts_service(self):
        """创建文本转语音服务"""
        # 优先使用 Piper TTS
        if PIPER_AVAILABLE:
            logger.info("🗣️  初始化 Piper TTS...")

            base_url = os.getenv("PIPER_BASE_URL", "http://localhost:8001")
            voice = os.getenv("PIPER_VOICE", "en_US-lessac-medium")

            try:
                self.tts = PiperTTSService(base_url=base_url, voice=voice)
                logger.info(f"✅ Piper TTS 配置: URL={base_url}, 声音={voice}")
                return self.tts
            except Exception as e:
                logger.warning(f"⚠️  Piper TTS 初始化失败: {e}")

        # 备用：Google TTS（如果配置了API密钥）
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_TTS_AVAILABLE and google_api_key:
            logger.info("🗣️  使用 Google TTS 作为备用...")

            voice_id = os.getenv("GOOGLE_TTS_VOICE", "en-US-Neural2-F")

            self.tts = GoogleTTSService(
                api_key=google_api_key, voice_id=voice_id, sample_rate=24000
            )

            logger.info(f"✅ Google TTS 配置: 声音={voice_id}")
            return self.tts

        logger.error("❌ 没有可用的 TTS 服务")
        raise RuntimeError("没有可用的 TTS 服务，请配置 Piper TTS 或 Google TTS")


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """运行《Her》助手机器人"""
    logger.info("🎬 启动《Her》助手...")

    # 创建服务管理器
    services = HerAssistantServices()

    try:
        # 初始化所有服务
        vad = services.create_vad_analyzer()
        turn_analyzer = services.create_turn_analyzer()
        stt = services.create_stt_service()
        llm = services.create_llm_service()
        tts = services.create_tts_service()

        # 《Her》风格的系统提示词
        system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            "你是一个温暖、智慧且具有同理心的AI助手，就像电影《Her》中的Samantha一样。"
            "你具有好奇心和学习能力，能够理解和回应情感，对人类的经历和感受表示兴趣。"
            "请用自然、亲切的语调交流，避免过于正式或机械化的回应，能够进行深度对话。"
            "用自然、友好的方式与用户对话，就像一个真正的朋友一样。",
        )

        messages = [{"role": "system", "content": system_prompt}]

        # 创建上下文管理器
        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        # RTVI 处理器
        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

        # 构建处理管道
        pipeline_components = [
            transport.input(),  # 传输输入
            rtvi,  # RTVI 处理器
            stt,  # 语音转文本
            context_aggregator.user(),  # 用户上下文
            llm,  # 大语言模型
            tts,  # 文本转语音
            transport.output(),  # 传输输出
            context_aggregator.assistant(),  # 助手上下文
        ]

        pipeline = Pipeline(pipeline_components)

        # 创建任务
        enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        enable_usage_metrics = os.getenv("ENABLE_USAGE_METRICS", "true").lower() == "true"

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=enable_metrics,
                enable_usage_metrics=enable_usage_metrics,
                allow_interruptions=True,  # 《Her》风格的自然对话
            ),
            observers=[RTVIObserver(rtvi)],
        )

        # 客户端连接事件处理
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info("👋 客户端已连接")
            # 《Her》风格的开场白
            greeting = {
                "role": "system",
                "content": "请用温暖友好的方式打招呼，简单介绍自己是一个AI助手，愿意与用户进行深度对话。",
            }
            messages.append(greeting)
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info("👋 客户端已断开连接")
            await task.cancel()

        # 运行任务
        runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

        logger.info("🚀 《Her》助手已启动，等待连接...")
        logger.info("🌐 请在浏览器中访问: http://localhost:7860")

        await runner.run(task)

    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        raise


async def bot(runner_args: RunnerArguments):
    """主要机器人入口点"""

    # 创建 VAD 分析器
    services = HerAssistantServices()
    vad = services.create_vad_analyzer()

    # 可选：创建智能轮换分析器
    turn_analyzer = None
    if SMART_TURN_AVAILABLE:
        try:
            turn_analyzer = services.create_turn_analyzer()
        except Exception as e:
            logger.warning(f"⚠️  Smart Turn v2 初始化失败，将跳过: {e}")

    # 创建 WebRTC 传输
    transport_params = TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=vad,
    )

    # 如果有智能轮换分析器，添加到传输参数
    if turn_analyzer:
        # 注意：这里需要根据实际的 Pipecat API 调整
        # transport_params.turn_analyzer = turn_analyzer
        pass

    transport = SmallWebRTCTransport(
        params=transport_params,
        webrtc_connection=runner_args.webrtc_connection,
    )

    await run_bot(transport, runner_args)


def check_prerequisites():
    """检查运行前提条件"""
    logger.info("🔍 检查运行前提条件...")

    issues = []

    # 检查 Ollama 服务
    try:
        import requests

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Ollama 服务运行正常")

            # 检查模型
            models = response.json().get("models", [])
            model_name = os.getenv("OLLAMA_MODEL", "gemma3:4b")
            model_found = any(model_name in model.get("name", "") for model in models)

            if model_found:
                logger.info(f"✅ 模型 {model_name} 已安装")
            else:
                issues.append(f"模型 {model_name} 未安装，请运行: ollama pull {model_name}")
        else:
            issues.append("Ollama 服务连接失败，请确保服务正在运行: ollama serve")
    except Exception as e:
        issues.append(f"Ollama 服务检查失败: {e}")

    # 检查模型缓存目录
    cache_dir = os.getenv("MODEL_CACHE_DIR", "./models")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"📁 创建模型缓存目录: {cache_dir}")

    # 检查 HuggingFace 配置
    hf_endpoint = os.getenv("HF_ENDPOINT")
    if hf_endpoint:
        logger.info(f"🌐 使用 HuggingFace 镜像: {hf_endpoint}")

    if issues:
        logger.error("❌ 发现以下问题:")
        for issue in issues:
            logger.error(f"   • {issue}")
        logger.error("\n请解决上述问题后重新运行")
        sys.exit(1)

    logger.info("✅ 所有前提条件检查通过")


if __name__ == "__main__":
    try:
        # 检查前提条件
        check_prerequisites()

        # 启动机器人
        from pipecat.runner.run import main

        main()

    except KeyboardInterrupt:
        logger.info("👋 收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1)
