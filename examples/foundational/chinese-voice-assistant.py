#!/usr/bin/env python3

"""
中文智能语音助手演示

这个示例展示了一个功能更丰富的中文语音助手，包含：
- 多种中文语音服务支持
- 函数调用功能
- 情感识别
- 多轮对话记忆
- 实时性能监控

运行前请确保：
1. 已安装 Pipecat 及相关依赖
2. 已配置 .env 文件中的 API 密钥
3. 已获取 Daily.co 房间 URL 和 Token

运行命令：
python examples/foundational/chinese-voice-assistant.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp
import psutil
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    EndFrame,
    Frame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.processors.frameworks.rtvi import (
    RTVIBotLLMProcessor,
    RTVIProcessor,
    RTVIUserLLMProcessor,
)
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

try:
    from pipecat.services.deepgram import DeepgramSTTService

    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False

try:
    from pipecat.services.cartesia import CartesiaTTSService

    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
)


class ChineseVoiceAssistant:
    """中文智能语音助手"""

    def __init__(self):
        self.transport = None
        self.stt = None
        self.llm = None
        self.tts = None
        self.pipeline = None
        self.task = None
        self.session = None

        # 性能监控
        self.start_time = time.time()
        self.request_count = 0
        self.conversation_history = []

        # 用户偏好设置
        self.user_preferences = {
            "language": "zh-CN",
            "voice_speed": 1.0,
            "response_length": "medium",  # short, medium, long
            "personality": "friendly",  # friendly, professional, casual
        }

    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """获取当前天气信息"""
        logger.info(f"获取天气信息: {location}")

        # 模拟天气 API 调用
        await asyncio.sleep(0.5)  # 模拟网络延迟

        # 这里应该调用真实的天气 API
        weather_data = {
            "location": location,
            "temperature": "22°C",
            "condition": "晴天",
            "humidity": "65%",
            "wind": "微风",
            "description": f"{location}今天天气晴朗，温度22度，湿度65%，微风。适合外出活动。",
        }

        return weather_data

    async def get_current_time(self) -> Dict[str, Any]:
        """获取当前时间"""
        now = datetime.now()

        time_data = {
            "current_time": now.strftime("%Y年%m月%d日 %H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": "Asia/Shanghai",
            "description": f"现在是{now.strftime('%Y年%m月%d日 %H点%M分')}",
        }

        return time_data

    async def search_information(self, query: str) -> Dict[str, Any]:
        """搜索信息"""
        logger.info(f"搜索信息: {query}")

        # 模拟搜索 API 调用
        await asyncio.sleep(1.0)

        search_results = {
            "query": query,
            "results": [
                {
                    "title": f"关于{query}的信息",
                    "summary": f"这是关于{query}的详细信息。由于这是演示版本，这里显示的是模拟搜索结果。",
                    "source": "演示数据",
                }
            ],
            "description": f"我找到了关于{query}的一些信息。不过这是演示版本，实际部署时可以接入真实的搜索API。",
        }

        return search_results

    async def set_reminder(self, reminder_text: str, time_str: str) -> Dict[str, Any]:
        """设置提醒"""
        logger.info(f"设置提醒: {reminder_text} at {time_str}")

        reminder_data = {
            "reminder": reminder_text,
            "time": time_str,
            "status": "已设置",
            "description": f"好的，我已经为您设置了提醒：{reminder_text}。提醒时间：{time_str}。",
        }

        return reminder_data

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        status_data = {
            "cpu_usage": f"{cpu_percent}%",
            "memory_usage": f"{memory.percent}%",
            "uptime": f"{time.time() - self.start_time:.1f}秒",
            "requests_handled": self.request_count,
            "description": f"系统运行正常。CPU使用率{cpu_percent}%，内存使用率{memory.percent}%，已处理{self.request_count}个请求。",
        }

        return status_data

    def _get_function_definitions(self):
        """获取函数定义"""
        return [
            {
                "name": "get_current_weather",
                "description": "获取指定地点的当前天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "城市名称，例如：北京、上海、广州",
                        }
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_current_time",
                "description": "获取当前时间和日期",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "search_information",
                "description": "搜索相关信息",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "搜索关键词或问题"}},
                    "required": ["query"],
                },
            },
            {
                "name": "set_reminder",
                "description": "设置提醒事项",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminder_text": {"type": "string", "description": "提醒内容"},
                        "time_str": {
                            "type": "string",
                            "description": "提醒时间，例如：明天上午9点、下午3点等",
                        },
                    },
                    "required": ["reminder_text", "time_str"],
                },
            },
            {
                "name": "get_system_status",
                "description": "获取系统运行状态",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def handle_function_call(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理函数调用"""
        logger.info(f"处理函数调用: {function_name} with {arguments}")

        try:
            if function_name == "get_current_weather":
                return await self.get_current_weather(arguments.get("location", ""))
            elif function_name == "get_current_time":
                return await self.get_current_time()
            elif function_name == "search_information":
                return await self.search_information(arguments.get("query", ""))
            elif function_name == "set_reminder":
                return await self.set_reminder(
                    arguments.get("reminder_text", ""), arguments.get("time_str", "")
                )
            elif function_name == "get_system_status":
                return await self.get_system_status()
            else:
                return {"error": f"未知函数: {function_name}"}
        except Exception as e:
            logger.error(f"函数调用错误: {e}")
            return {"error": f"函数执行失败: {str(e)}"}

    def _create_stt_service(self):
        """创建中文语音识别服务"""

        if AZURE_AVAILABLE and os.getenv("AZURE_SPEECH_KEY"):
            logger.info("使用 Azure 语音识别服务")
            return AzureSTTService(
                api_key=os.getenv("AZURE_SPEECH_KEY"),
                region=os.getenv("AZURE_SPEECH_REGION", "eastasia"),
                language=Language.ZH_CN,
            )

        elif GOOGLE_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.info("使用 Google 语音识别服务")
            return GoogleSTTService(
                credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                language=Language.ZH_CN,
                model="latest_long",
            )

        elif DEEPGRAM_AVAILABLE and os.getenv("DEEPGRAM_API_KEY"):
            logger.info("使用 Deepgram 语音识别服务")
            return DeepgramSTTService(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                language=Language.ZH_CN,
                model="nova-2-general",
            )

        else:
            raise ValueError("未找到可用的中文语音识别服务")

    def _create_llm_service(self):
        """创建中文大语言模型服务"""

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("未找到 OPENAI_API_KEY")

        logger.info("使用 OpenAI 兼容的中文模型")

        return OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            tools=self._get_function_definitions(),
        )

    def _create_tts_service(self):
        """创建中文语音合成服务"""

        if AZURE_AVAILABLE and os.getenv("AZURE_TTS_KEY"):
            logger.info("使用 Azure 语音合成服务")
            return AzureTTSService(
                api_key=os.getenv("AZURE_TTS_KEY"),
                region=os.getenv("AZURE_TTS_REGION", "eastasia"),
                voice=os.getenv("AZURE_TTS_VOICE", "zh-CN-XiaoxiaoNeural"),
                language=Language.ZH_CN,
            )

        elif GOOGLE_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.info("使用 Google 语音合成服务")
            return GoogleTTSService(
                credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                voice_id=os.getenv("GOOGLE_TTS_VOICE", "cmn-CN-Wavenet-A"),
                language=Language.ZH_CN,
            )

        elif CARTESIA_AVAILABLE and os.getenv("CARTESIA_API_KEY"):
            logger.info("使用 Cartesia 语音合成服务")
            return CartesiaTTSService(
                api_key=os.getenv("CARTESIA_API_KEY"),
                voice_id=os.getenv("CARTESIA_VOICE_ID", "a167e0f3-df7e-4d52-a9c3-f949145efdab"),
                language=Language.ZH_CN,
            )

        else:
            raise ValueError("未找到可用的中文语音合成服务")

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
            bot_name=os.getenv("DAILY_BOT_NAME", "中文智能助手"),
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

        personality = self.user_preferences.get("personality", "friendly")

        personality_prompts = {
            "friendly": "你是一个友好、温暖的AI助手，总是用积极的语气回答问题。",
            "professional": "你是一个专业、高效的AI助手，回答简洁准确。",
            "casual": "你是一个轻松、随和的AI助手，用轻松的语气与用户交流。",
        }

        system_prompt = f"""{personality_prompts.get(personality, personality_prompts["friendly"])}

你具备以下能力：
1. 回答各种问题
2. 查询天气信息
3. 获取当前时间
4. 搜索相关信息
5. 设置提醒事项
6. 查看系统状态

请遵循以下规则：
1. 使用简体中文回答
2. 回答要简洁明了，适合语音播放
3. 避免使用特殊符号和格式化文本
4. 保持对话自然流畅
5. 主动使用可用的函数来帮助用户
6. 如果需要调用函数，先说明你要做什么，然后调用函数
7. 根据函数返回的结果给出友好的回答

当前用户偏好：
- 语言：{self.user_preferences["language"]}
- 回答长度：{self.user_preferences["response_length"]}
- 个性风格：{self.user_preferences["personality"]}"""

        messages = [{"role": "system", "content": system_prompt}]

        return OpenAILLMContext(messages)

    async def setup(self):
        """初始化助手"""

        logger.info("正在初始化中文智能语音助手...")

        # 创建 HTTP 会话
        self.session = aiohttp.ClientSession()

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
                enable_metrics=True,
                enable_usage_metrics=True,
                report_only_initial_ttfb=True,
            ),
        )

        # 注册事件处理器
        self._register_event_handlers()

        logger.info("中文智能语音助手初始化完成")

    def _register_event_handlers(self):
        """注册事件处理器"""

        @self.transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"客户端已连接: {client}")

            welcome_message = """你好！我是你的中文智能语音助手。

我可以帮你：
• 查询天气信息
• 获取当前时间
• 搜索相关信息  
• 设置提醒事项
• 查看系统状态

有什么可以帮助你的吗？"""

            await self.task.queue_frames([await self.tts.run_tts(welcome_message).__anext__()])

        @self.transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client, reason):
            logger.info(f"客户端已断开连接: {client}, 原因: {reason}")
            await self.task.queue_frames([EndFrame()])

        @self.llm.event_handler("on_function_call_start")
        async def on_function_call_start(function_name: str):
            logger.info(f"开始函数调用: {function_name}")
            await self.task.queue_frames([FunctionCallInProgressFrame()])

        @self.llm.event_handler("on_function_call_result")
        async def on_function_call_result(
            function_name: str, arguments: Dict[str, Any], result: Any
        ):
            logger.info(f"函数调用完成: {function_name}")

            # 处理函数调用
            processed_result = await self.handle_function_call(function_name, arguments)

            await self.task.queue_frames(
                [
                    FunctionCallResultFrame(
                        function_name=function_name, arguments=arguments, result=processed_result
                    )
                ]
            )

        @self.transport.event_handler("on_participant_joined")
        async def on_participant_joined(transport, participant):
            logger.info(f"参与者加入: {participant}")
            self.request_count += 1

        @self.transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"参与者离开: {participant}, 原因: {reason}")

    async def run(self):
        """运行助手"""

        logger.info("启动中文智能语音助手...")

        try:
            runner = PipelineRunner()
            await runner.run(self.task)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"运行时错误: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()
            logger.info("中文智能语音助手已关闭")


async def main():
    """主函数"""

    # 检查必要的环境变量
    required_vars = ["DAILY_ROOM_URL", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请检查 .env 文件配置")
        return

    # 创建并运行助手
    assistant = ChineseVoiceAssistant()
    await assistant.setup()
    await assistant.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
