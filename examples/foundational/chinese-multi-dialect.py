#!/usr/bin/env python3

"""
中文多方言支持演示

这个示例展示了如何在 Pipecat 中支持多种中文方言：
- 普通话 (zh-CN)
- 粤语 (yue-CN)
- 上海话 (wuu-CN)
- 台湾国语 (zh-TW)
- 香港粤语 (zh-HK)

功能特性：
- 自动方言检测
- 动态服务切换
- 方言特色回复
- 跨方言理解

运行前请确保：
1. 已安装 Pipecat 及相关依赖
2. 已配置 .env 文件中的 API 密钥
3. 已获取 Daily.co 房间 URL 和 Token

运行命令：
python examples/foundational/chinese-multi-dialect.py
"""

import asyncio
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, Frame, TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.filters.frame_filter import FrameFilter
from pipecat.services.openai import OpenAILLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.services.daily import DailyParams, DailyTransport

# 导入服务
try:
    from pipecat.services.azure import AzureSTTService, AzureTTSService

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    from pipecat.services.google import GoogleSTTService, GoogleTTSService

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
)


@dataclass
class DialectConfig:
    """方言配置"""

    language_code: Language
    stt_voice: str
    tts_voice: str
    greeting: str
    personality: str
    keywords: List[str]


class DialectDetector:
    """方言检测器"""

    def __init__(self):
        # 定义各方言的特征词汇和表达
        self.dialect_patterns = {
            Language.ZH_CN: {  # 普通话
                "keywords": ["你好", "谢谢", "再见", "什么", "怎么", "为什么", "哪里"],
                "patterns": [r"什么时候", r"怎么样", r"为什么", r"在哪里"],
                "weight": 1.0,
            },
            Language.YUE_CN: {  # 粤语
                "keywords": ["你好", "唔该", "拜拜", "乜嘢", "点解", "边度", "几时"],
                "patterns": [r"乜嘢", r"点解", r"边度", r"几时", r"唔该", r"冇问题"],
                "weight": 2.0,  # 粤语特征词权重更高
            },
            Language.WUU_CN: {  # 上海话
                "keywords": ["侬好", "谢谢侬", "再会", "啥", "哪能", "为啥", "啥地方"],
                "patterns": [r"侬好", r"哪能", r"为啥", r"啥地方", r"谢谢侬"],
                "weight": 2.0,
            },
            Language.ZH_TW: {  # 台湾国语
                "keywords": ["你好", "謝謝", "再見", "什麼", "怎麼", "為什麼", "哪裡"],
                "patterns": [r"什麼時候", r"怎麼樣", r"為什麼", r"在哪裡", r"沒關係"],
                "weight": 1.5,
            },
            Language.ZH_HK: {  # 香港粤语
                "keywords": ["你好", "唔該", "拜拜", "乜嘢", "點解", "邊度", "幾時"],
                "patterns": [r"乜嘢", r"點解", r"邊度", r"幾時", r"唔該", r"冇問題"],
                "weight": 2.0,
            },
        }

    def detect_dialect(self, text: str) -> Language:
        """检测文本的方言"""
        if not text:
            return Language.ZH_CN  # 默认普通话

        scores = {}

        for dialect, config in self.dialect_patterns.items():
            score = 0

            # 检查关键词
            for keyword in config["keywords"]:
                if keyword in text:
                    score += config["weight"]

            # 检查模式
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    score += config["weight"] * 1.5

            scores[dialect] = score

        # 返回得分最高的方言
        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 0:
                logger.info(f"检测到方言: {detected} (得分: {scores[detected]})")
                return detected

        return Language.ZH_CN  # 默认普通话


class DialectManager:
    """方言管理器"""

    def __init__(self):
        self.detector = DialectDetector()
        self.current_dialect = Language.ZH_CN

        # 配置各方言
        self.dialect_configs = {
            Language.ZH_CN: DialectConfig(
                language_code=Language.ZH_CN,
                stt_voice="zh-CN",
                tts_voice="zh-CN-XiaoxiaoNeural",
                greeting="你好！我是你的AI助手，很高兴为您服务。",
                personality="标准普通话，正式友好",
                keywords=["普通话", "标准", "正式"],
            ),
            Language.YUE_CN: DialectConfig(
                language_code=Language.YUE_CN,
                stt_voice="yue-CN",
                tts_voice="zh-HK-HiuMaanNeural",
                greeting="你好！我係你嘅AI助手，好高兴为你服务。",
                personality="粤语表达，亲切随和",
                keywords=["粤语", "广东话", "香港"],
            ),
            Language.WUU_CN: DialectConfig(
                language_code=Language.WUU_CN,
                stt_voice="wuu-CN",
                tts_voice="zh-CN-YunyeNeural",
                greeting="侬好！我是侬个AI助手，老开心为侬服务个。",
                personality="上海话表达，温和亲近",
                keywords=["上海话", "沪语", "上海"],
            ),
            Language.ZH_TW: DialectConfig(
                language_code=Language.ZH_TW,
                stt_voice="zh-TW",
                tts_voice="zh-TW-HsiaoChenNeural",
                greeting="您好！我是您的AI助手，很高興為您服務。",
                personality="台湾国语，礼貌温和",
                keywords=["台湾", "国语", "繁体"],
            ),
            Language.ZH_HK: DialectConfig(
                language_code=Language.ZH_HK,
                stt_voice="zh-HK",
                tts_voice="zh-HK-HiuGaaiNeural",
                greeting="你好！我係你嘅AI助手，好開心為你服務。",
                personality="香港粤语，热情友好",
                keywords=["香港", "粤语", "港式"],
            ),
        }

    def get_current_config(self) -> DialectConfig:
        """获取当前方言配置"""
        return self.dialect_configs.get(self.current_dialect, self.dialect_configs[Language.ZH_CN])

    def switch_dialect(self, new_dialect: Language) -> bool:
        """切换方言"""
        if new_dialect in self.dialect_configs:
            old_dialect = self.current_dialect
            self.current_dialect = new_dialect
            logger.info(f"方言切换: {old_dialect} -> {new_dialect}")
            return True
        return False

    def detect_and_switch(self, text: str) -> bool:
        """检测并切换方言"""
        detected_dialect = self.detector.detect_dialect(text)
        if detected_dialect != self.current_dialect:
            return self.switch_dialect(detected_dialect)
        return False


class DialectFilter(FrameFilter):
    """方言过滤器"""

    def __init__(self, dialect_manager: DialectManager):
        super().__init__()
        self.dialect_manager = dialect_manager

    async def process_frame(self, frame: Frame, direction) -> Frame:
        """处理帧"""
        if isinstance(frame, TextFrame):
            # 检测方言并可能切换
            if self.dialect_manager.detect_and_switch(frame.text):
                logger.info(f"检测到方言切换，当前方言: {self.dialect_manager.current_dialect}")

        return frame


class ChineseMultiDialectBot:
    """中文多方言机器人"""

    def __init__(self):
        self.transport = None
        self.stt_services = {}
        self.tts_services = {}
        self.llm = None
        self.pipeline = None
        self.task = None

        self.dialect_manager = DialectManager()
        self.dialect_filter = DialectFilter(self.dialect_manager)

    def _create_stt_services(self):
        """创建多方言STT服务"""

        if not AZURE_AVAILABLE or not os.getenv("AZURE_SPEECH_KEY"):
            raise ValueError("需要 Azure 语音服务支持多方言")

        logger.info("创建多方言STT服务")

        for dialect, config in self.dialect_manager.dialect_configs.items():
            try:
                stt = AzureSTTService(
                    api_key=os.getenv("AZURE_SPEECH_KEY"),
                    region=os.getenv("AZURE_SPEECH_REGION", "eastasia"),
                    language=config.language_code,
                )
                self.stt_services[dialect] = stt
                logger.info(f"创建STT服务: {dialect}")
            except Exception as e:
                logger.warning(f"无法创建STT服务 {dialect}: {e}")

        if not self.stt_services:
            raise ValueError("未能创建任何STT服务")

    def _create_tts_services(self):
        """创建多方言TTS服务"""

        if not AZURE_AVAILABLE or not os.getenv("AZURE_TTS_KEY"):
            raise ValueError("需要 Azure 语音服务支持多方言")

        logger.info("创建多方言TTS服务")

        for dialect, config in self.dialect_manager.dialect_configs.items():
            try:
                tts = AzureTTSService(
                    api_key=os.getenv("AZURE_TTS_KEY"),
                    region=os.getenv("AZURE_TTS_REGION", "eastasia"),
                    voice=config.tts_voice,
                    language=config.language_code,
                )
                self.tts_services[dialect] = tts
                logger.info(f"创建TTS服务: {dialect} - {config.tts_voice}")
            except Exception as e:
                logger.warning(f"无法创建TTS服务 {dialect}: {e}")

        if not self.tts_services:
            raise ValueError("未能创建任何TTS服务")

    def _create_llm_service(self):
        """创建支持多方言的LLM服务"""

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("未找到 OPENAI_API_KEY")

        logger.info("创建多方言LLM服务")

        return OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )

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
            bot_name=os.getenv("DAILY_BOT_NAME", "多方言AI助手"),
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
        """创建多方言对话上下文"""

        system_prompt = """你是一个支持多种中文方言的AI助手。你能理解和使用以下方言：

1. 普通话 (zh-CN) - 标准中文
2. 粤语 (yue-CN) - 广东话
3. 上海话 (wuu-CN) - 沪语
4. 台湾国语 (zh-TW) - 繁体中文
5. 香港粤语 (zh-HK) - 港式粤语

请遵循以下规则：
1. 根据用户使用的方言来回应
2. 如果用户说普通话，用标准普通话回答
3. 如果用户说粤语，用粤语表达回答
4. 如果用户说上海话，用上海话风格回答
5. 如果用户说台湾国语，用台湾表达习惯回答
6. 保持回答简洁，适合语音播放
7. 体现不同方言的文化特色
8. 避免使用特殊符号和格式化文本

当前支持的方言特色：
- 普通话：正式、标准
- 粤语：亲切、生动
- 上海话：温和、亲近
- 台湾国语：礼貌、温和
- 香港粤语：热情、直接

如果不确定用户的方言，默认使用普通话回答。"""

        messages = [{"role": "system", "content": system_prompt}]

        return OpenAILLMContext(messages)

    def get_current_stt(self):
        """获取当前方言的STT服务"""
        current_dialect = self.dialect_manager.current_dialect
        return self.stt_services.get(current_dialect, self.stt_services[Language.ZH_CN])

    def get_current_tts(self):
        """获取当前方言的TTS服务"""
        current_dialect = self.dialect_manager.current_dialect
        return self.tts_services.get(current_dialect, self.tts_services[Language.ZH_CN])

    async def setup(self):
        """初始化机器人"""

        logger.info("正在初始化中文多方言机器人...")

        # 创建服务
        self.transport = self._create_transport()
        self._create_stt_services()
        self._create_tts_services()
        self.llm = self._create_llm_service()

        # 创建上下文聚合器
        context = self._create_context()
        context_aggregator = self.llm.create_context_aggregator(context)

        # 构建处理管道
        self.pipeline = Pipeline(
            [
                self.transport.input(),  # 接收用户音频输入
                self.get_current_stt(),  # 当前方言STT
                self.dialect_filter,  # 方言检测过滤器
                context_aggregator.user(),  # 用户消息聚合
                self.llm,  # 大语言模型处理
                self.get_current_tts(),  # 当前方言TTS
                self.transport.output(),  # 输出音频响应
                context_aggregator.assistant(),  # 助手消息聚合
            ]
        )

        # 创建任务
        self.task = PipelineTask(
            self.pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
                report_only_initial_ttfb=True,
            ),
        )

        # 注册事件处理器
        self._register_event_handlers()

        logger.info("中文多方言机器人初始化完成")

    def _register_event_handlers(self):
        """注册事件处理器"""

        @self.transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"客户端已连接: {client}")

            welcome_message = """你好！我是多方言AI助手。

我支持以下中文方言：
• 普通话 - 标准中文
• 粤语 - 广东话  
• 上海话 - 沪语
• 台湾国语 - 繁体中文
• 香港粤语 - 港式粤语

请用你习惯的方言与我对话，我会自动识别并用相应的方言回答你。

有什么可以帮助你的吗？"""

            # 使用当前方言的TTS
            current_tts = self.get_current_tts()
            await self.task.queue_frames([await current_tts.run_tts(welcome_message).__anext__()])

        @self.transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client, reason):
            logger.info(f"客户端已断开连接: {client}, 原因: {reason}")
            await self.task.queue_frames([EndFrame()])

        @self.transport.event_handler("on_participant_joined")
        async def on_participant_joined(transport, participant):
            logger.info(f"参与者加入: {participant}")

            # 根据当前方言发送欢迎消息
            config = self.dialect_manager.get_current_config()
            current_tts = self.get_current_tts()

            await self.task.queue_frames([await current_tts.run_tts(config.greeting).__anext__()])

        @self.transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"参与者离开: {participant}, 原因: {reason}")

    async def run(self):
        """运行机器人"""

        logger.info("启动中文多方言机器人...")

        try:
            runner = PipelineRunner()
            await runner.run(self.task)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"运行时错误: {e}")
            raise
        finally:
            logger.info("中文多方言机器人已关闭")


async def main():
    """主函数"""

    # 检查必要的环境变量
    required_vars = ["DAILY_ROOM_URL", "OPENAI_API_KEY", "AZURE_SPEECH_KEY", "AZURE_TTS_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("多方言支持需要 Azure 语音服务，请配置相关 API 密钥")
        return

    # 创建并运行机器人
    bot = ChineseMultiDialectBot()
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
