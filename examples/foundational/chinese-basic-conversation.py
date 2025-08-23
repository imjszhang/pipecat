#!/usr/bin/env python3

"""
中文基础对话机器人演示

这个示例展示了如何使用 Pipecat 构建一个支持中文的语音对话机器人。
包含中文语音识别、中文大语言模型和中文语音合成的完整流程。

运行前请确保：
1. 已安装 Pipecat 及相关依赖
2. 已配置 .env 文件中的 API 密钥
3. 已获取 Daily.co 房间 URL 和 Token

运行命令：
python examples/foundational/chinese-basic-conversation.py
"""

import asyncio
import os
import sys
from typing import AsyncGenerator

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, Frame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai import OpenAILLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.services.daily import DailyParams, DailyTransport

# 根据配置选择不同的服务
try:
    # 优先使用 Azure 服务（支持中文方言）
    from pipecat.services.azure import AzureSTTService, AzureTTSService

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure 服务不可用，将使用其他服务")

try:
    # 备选：Google 服务
    from pipecat.services.google import GoogleSTTService, GoogleTTSService

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google 服务不可用")

try:
    # 备选：Deepgram 服务
    from pipecat.services.deepgram import DeepgramSTTService

    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    logger.warning("Deepgram 服务不可用")

try:
    # 备选：Cartesia TTS
    from pipecat.services.cartesia import CartesiaTTSService

    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False
    logger.warning("Cartesia 服务不可用")

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


class ChineseConversationBot:
    """中文对话机器人类"""

    def __init__(self):
        self.transport = None
        self.stt = None
        self.llm = None
        self.tts = None
        self.pipeline = None
        self.task = None

    def _create_stt_service(self):
        """创建中文语音识别服务"""

        # 优先使用 Azure STT（支持中文方言）
        if AZURE_AVAILABLE and os.getenv("AZURE_SPEECH_KEY"):
            logger.info("使用 Azure 语音识别服务")
            return AzureSTTService(
                api_key=os.getenv("AZURE_SPEECH_KEY"),
                region=os.getenv("AZURE_SPEECH_REGION", "eastasia"),
                language=Language.ZH_CN,
            )

        # 备选：Google STT
        elif GOOGLE_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.info("使用 Google 语音识别服务")
            return GoogleSTTService(
                credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                language=Language.ZH_CN,
                model="latest_long",
            )

        # 备选：Deepgram STT
        elif DEEPGRAM_AVAILABLE and os.getenv("DEEPGRAM_API_KEY"):
            logger.info("使用 Deepgram 语音识别服务")
            return DeepgramSTTService(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                language=Language.ZH_CN,
                model="nova-2-general",
            )

        else:
            raise ValueError("未找到可用的中文语音识别服务，请检查配置")

    def _create_llm_service(self):
        """创建中文大语言模型服务"""

        # 使用 OpenAI 兼容的中文模型
        if os.getenv("OPENAI_API_KEY"):
            logger.info("使用 OpenAI 兼容的中文模型")
            return OpenAILLMService(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                base_url=os.getenv("OPENAI_BASE_URL"),  # 支持自定义 API 端点
            )

        else:
            raise ValueError("未找到可用的大语言模型服务，请检查配置")

    def _create_tts_service(self):
        """创建中文语音合成服务"""

        # 优先使用 Azure TTS（支持多种中文声音）
        if AZURE_AVAILABLE and os.getenv("AZURE_TTS_KEY"):
            logger.info("使用 Azure 语音合成服务")
            return AzureTTSService(
                api_key=os.getenv("AZURE_TTS_KEY"),
                region=os.getenv("AZURE_TTS_REGION", "eastasia"),
                voice=os.getenv("AZURE_TTS_VOICE", "zh-CN-XiaoxiaoNeural"),
                language=Language.ZH_CN,
            )

        # 备选：Google TTS
        elif GOOGLE_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.info("使用 Google 语音合成服务")
            return GoogleTTSService(
                credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                voice_id=os.getenv("GOOGLE_TTS_VOICE", "cmn-CN-Wavenet-A"),
                language=Language.ZH_CN,
            )

        # 备选：Cartesia TTS
        elif CARTESIA_AVAILABLE and os.getenv("CARTESIA_API_KEY"):
            logger.info("使用 Cartesia 语音合成服务")
            return CartesiaTTSService(
                api_key=os.getenv("CARTESIA_API_KEY"),
                voice_id=os.getenv("CARTESIA_VOICE_ID", "a167e0f3-df7e-4d52-a9c3-f949145efdab"),
                language=Language.ZH_CN,
            )

        else:
            raise ValueError("未找到可用的中文语音合成服务，请检查配置")

    def _create_transport(self):
        """创建传输层"""

        room_url = os.getenv("DAILY_ROOM_URL")
        token = os.getenv("DAILY_TOKEN")

        if not room_url:
            raise ValueError("请设置 DAILY_ROOM_URL 环境变量")

        logger.info(f"连接到 Daily.co 房间: {room_url}")

        return DailyTransport(
            room_url=room_url,
            token=token,
            bot_name=os.getenv("DAILY_BOT_NAME", "中文AI助手"),
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(
                    confidence=float(os.getenv("VAD_CONFIDENCE", "0.7")),
                    start_secs=float(os.getenv("VAD_START_SECS", "0.2")),
                    stop_secs=float(os.getenv("VAD_STOP_SECS", "2.0")),
                    min_volume=float(os.getenv("VAD_MIN_VOLUME", "0.6")),
                ),
            ),
        )

    def _create_context(self):
        """创建对话上下文"""

        system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            """你是一个友好、专业的中文AI助手。

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
- 协助解决问题

请用温暖、友好的语气与用户交流。""",
        )

        messages = [{"role": "system", "content": system_prompt}]

        return OpenAILLMContext(messages)

    async def setup(self):
        """初始化机器人"""

        logger.info("正在初始化中文对话机器人...")

        # 创建服务
        self.transport = self._create_transport()
        self.stt = self._create_stt_service()
        self.llm = self._create_llm_service()
        self.tts = self._create_tts_service()

        # 创建上下文聚合器
        context = self._create_context()
        context_aggregator = self.llm.create_context_aggregator(context)

        # 构建处理管道
        self.pipeline = Pipeline(
            [
                self.transport.input(),  # 接收用户音频输入
                self.stt,  # 语音转文字
                context_aggregator.user(),  # 用户消息聚合
                self.llm,  # 大语言模型处理
                self.tts,  # 文字转语音
                self.transport.output(),  # 输出音频响应
                context_aggregator.assistant(),  # 助手消息聚合
            ]
        )

        # 创建任务
        self.task = PipelineTask(
            self.pipeline,
            params=PipelineParams(
                enable_metrics=bool(os.getenv("ENABLE_METRICS", "true").lower() == "true"),
                enable_usage_metrics=bool(
                    os.getenv("ENABLE_USAGE_METRICS", "true").lower() == "true"
                ),
                report_only_initial_ttfb=bool(
                    os.getenv("REPORT_ONLY_INITIAL_TTFB", "true").lower() == "true"
                ),
            ),
        )

        # 注册事件处理器
        self._register_event_handlers()

        logger.info("中文对话机器人初始化完成")

    def _register_event_handlers(self):
        """注册事件处理器"""

        @self.transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"客户端已连接: {client}")

            # 发送欢迎消息
            welcome_message = os.getenv(
                "WELCOME_MESSAGE", "你好！我是你的中文AI助手，有什么可以帮助你的吗？"
            )

            await self.task.queue_frames([await self.tts.run_tts(welcome_message).__anext__()])

        @self.transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client, reason):
            logger.info(f"客户端已断开连接: {client}, 原因: {reason}")
            await self.task.queue_frames([EndFrame()])

        @self.transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"通话状态更新: {state}")

        @self.transport.event_handler("on_participant_joined")
        async def on_participant_joined(transport, participant):
            logger.info(f"参与者加入: {participant}")

        @self.transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"参与者离开: {participant}, 原因: {reason}")

    async def run(self):
        """运行机器人"""

        logger.info("启动中文对话机器人...")

        try:
            runner = PipelineRunner()
            await runner.run(self.task)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"运行时错误: {e}")
            raise
        finally:
            logger.info("中文对话机器人已关闭")


async def main():
    """主函数"""

    # 检查必要的环境变量
    required_vars = ["DAILY_ROOM_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请检查 .env 文件配置")
        return

    # 创建并运行机器人
    bot = ChineseConversationBot()
    await bot.setup()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
