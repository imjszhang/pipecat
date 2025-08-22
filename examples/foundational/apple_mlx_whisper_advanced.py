#!/usr/bin/env python3

"""
Apple MLX Whisper Large v3 Turbo 高级部署示例

这个高级示例展示如何在 Apple Silicon Mac 上部署一个完整的
MLX Whisper 语音转文本服务，包含:
- 环境变量配置
- 性能监控
- 错误处理
- 优雅退出
- 多语言支持

使用方法:
1. 复制 mlx_whisper.env 为 .env
2. 根据需要修改配置
3. 运行: python apple_mlx_whisper_advanced.py
"""

import asyncio
import os
import signal
import sys
import time
from typing import Optional

# 尝试导入 python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("📋 提示: 未安装 python-dotenv，将使用系统环境变量")

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

# 全局停止标志
_stop_event = asyncio.Event()


def signal_handler(signum, frame):
    """处理系统信号"""
    print(f"\n⚠️  接收到信号 {signum}，正在优雅停止...")
    _stop_event.set()


# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class MLXWhisperConfig:
    """MLX Whisper 配置类"""

    def __init__(self):
        # MLX 模型配置
        self.model = os.getenv("MLX_WHISPER_MODEL", "large-v3-turbo")
        self.device = os.getenv("MLX_DEVICE", "auto")

        # VAD 配置
        self.vad_confidence = float(os.getenv("VAD_CONFIDENCE", "0.7"))
        self.vad_start_secs = float(os.getenv("VAD_START_SECS", "0.2"))
        self.vad_stop_secs = float(os.getenv("VAD_STOP_SECS", "2.0"))
        self.vad_min_volume = float(os.getenv("VAD_MIN_VOLUME", "0.6"))

        # 音频配置
        self.sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
        self.channels = int(os.getenv("AUDIO_CHANNELS", "1"))
        self.buffer_size = int(os.getenv("AUDIO_BUFFER_SIZE", "4096"))

        # 转录配置
        self.language = os.getenv("TRANSCRIPTION_LANGUAGE", "")
        self.temperature = float(os.getenv("TRANSCRIPTION_TEMPERATURE", "0.0"))
        self.no_speech_threshold = float(os.getenv("NO_SPEECH_THRESHOLD", "0.4"))

        # 性能监控
        self.enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.enable_usage_metrics = os.getenv("ENABLE_USAGE_METRICS", "true").lower() == "true"
        self.report_only_initial_ttfb = (
            os.getenv("REPORT_ONLY_INITIAL_TTFB", "true").lower() == "true"
        )

        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.show_count = os.getenv("SHOW_TRANSCRIPTION_COUNT", "true").lower() == "true"
        self.show_timestamp = os.getenv("SHOW_TIMESTAMP", "false").lower() == "true"

    def print_config(self):
        """打印配置信息"""
        print("🔧 当前配置:")
        print(f"  📦 模型: {self.model}")
        print(f"  💻 设备: {self.device}")
        print(f"  🎤 VAD 置信度: {self.vad_confidence}")
        print(f"  🕐 语音开始: {self.vad_start_secs}s")
        print(f"  🕑 语音结束: {self.vad_stop_secs}s")
        print(f"  🔊 最小音量: {self.vad_min_volume}")
        print(f"  🌍 语言: {self.language if self.language else '自动检测'}")
        print(f"  📊 性能监控: {'开启' if self.enable_metrics else '关闭'}")


class AdvancedMLXTranscriptionLogger(FrameProcessor):
    """高级 MLX 转录记录器"""

    def __init__(self, config: MLXWhisperConfig):
        super().__init__()
        self.config = config
        self.transcription_count = 0
        self.start_time = time.time()
        self.last_transcription_time = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            self.transcription_count += 1
            current_time = time.time()

            # 构建输出消息
            message_parts = []

            # 添加时间戳
            if self.config.show_timestamp:
                elapsed = current_time - self.start_time
                message_parts.append(f"[{elapsed:.1f}s]")

            # 添加计数
            if self.config.show_count:
                message_parts.append(f"#{self.transcription_count}")

            # 添加转录内容
            message_parts.append(f"🍎 {frame.text}")

            # 输出完整消息
            print(" ".join(message_parts))

            # 计算延迟
            if self.last_transcription_time > 0:
                latency = current_time - self.last_transcription_time
                if latency < 5:  # 只显示合理的延迟
                    print(f"   ⚡ 延迟: {latency:.3f}s")

            self.last_transcription_time = current_time

            # 检查退出命令
            text_lower = frame.text.lower()
            if any(cmd in text_lower for cmd in ["退出", "quit", "stop", "结束"]):
                print("👋 检测到退出命令，正在停止...")
                _stop_event.set()


def check_system_requirements():
    """检查系统要求"""
    import platform

    # 检查操作系统
    if platform.system() != "Darwin":
        print("❌ 错误: 此示例仅支持 macOS 系统")
        return False

    # 检查处理器架构
    machine = platform.machine()
    if not machine.startswith("arm"):
        print("⚠️  警告: 此示例针对 Apple Silicon Mac (M1/M2/M3/M4) 优化")
        print(f"   当前处理器架构: {machine}")
        response = input("   是否继续运行? (y/N): ")
        if response.lower() != "y":
            return False

    # 检查 macOS 版本
    mac_version = platform.mac_ver()[0]
    major_version = int(mac_version.split(".")[0])
    if major_version < 12:
        print(f"⚠️  警告: 当前 macOS 版本 {mac_version} 可能不完全支持 MLX")
        print("   推荐 macOS 12.0 或更高版本")

    return True


async def main():
    """主函数"""
    print("🍎 Apple MLX Whisper Large v3 Turbo 高级部署")
    print("=" * 55)

    # 检查系统要求
    if not check_system_requirements():
        sys.exit(1)

    # 加载配置
    config = MLXWhisperConfig()
    config.print_config()

    print("\n📥 正在加载组件...")

    try:
        # 检查并导入 MLX Whisper
        try:
            from pipecat.services.whisper.stt import MLXModel, WhisperSTTServiceMLX
        except ImportError:
            print("❌ 错误: 未找到 MLX Whisper 依赖")
            print("请运行: uv add mlx-whisper")
            sys.exit(1)

        # 解析模型名称
        model_map = {
            "large-v3-turbo": MLXModel.LARGE_V3_TURBO,
            "large-v3-turbo-q4": MLXModel.LARGE_V3_TURBO_Q4,
            # 可以添加更多模型映射
        }

        mlx_model = model_map.get(config.model)
        if mlx_model is None:
            print(f"⚠️  未知模型: {config.model}，使用默认模型")
            mlx_model = MLXModel.LARGE_V3_TURBO

        # 创建 MLX Whisper 服务
        print(f"🧠 加载 MLX 模型: {config.model}")
        stt = WhisperSTTServiceMLX(model=mlx_model)
        print("✅ MLX Whisper 服务创建成功")

        # 创建 VAD 分析器
        vad = SileroVADAnalyzer(
            params=VADParams(
                confidence=config.vad_confidence,
                start_secs=config.vad_start_secs,
                stop_secs=config.vad_stop_secs,
                min_volume=config.vad_min_volume,
            )
        )
        print("✅ 语音活动检测器配置完成")

        # 创建音频传输
        transport = LocalAudioTransport(
            LocalAudioTransportParams(
                audio_in_enabled=True, audio_out_enabled=False, vad_analyzer=vad
            )
        )
        print("✅ 音频传输配置完成")

        # 创建转录记录器
        logger = AdvancedMLXTranscriptionLogger(config)

        # 构建管道
        pipeline = Pipeline([transport.input(), stt, logger])
        print("✅ 处理管道创建完成")

        # 创建任务
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=config.enable_metrics,
                enable_usage_metrics=config.enable_usage_metrics,
                report_only_initial_ttfb=config.report_only_initial_ttfb,
            ),
        )

        # 创建运行器
        runner = PipelineRunner()

        print("\n🚀 MLX Whisper 服务已启动!")
        print("-" * 40)
        print("📋 使用说明:")
        print("  • 开始说话进行实时转录")
        print("  • 支持多语言自动识别")
        print("  • 说'退出'、'quit'或'stop'停止")
        print("  • 使用 Ctrl+C 强制退出")
        print("-" * 40)
        print("🎤 开始转录...\n")

        # 启动异步任务
        runner_task = asyncio.create_task(runner.run(task))
        stop_task = asyncio.create_task(_stop_event.wait())

        # 等待任务完成或停止信号
        done, pending = await asyncio.wait(
            [runner_task, stop_task], return_when=asyncio.FIRST_COMPLETED
        )

        # 取消未完成的任务
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except KeyboardInterrupt:
        print("\n👋 用户手动停止程序")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n🔄 正在清理资源...")
        print("✅ 程序已安全退出")

        # 显示统计信息
        if "logger" in locals():
            elapsed = time.time() - logger.start_time
            print(f"📊 会话统计:")
            print(f"   总时长: {elapsed:.1f}s")
            print(f"   转录次数: {logger.transcription_count}")
            if logger.transcription_count > 0:
                avg_interval = elapsed / logger.transcription_count
                print(f"   平均间隔: {avg_interval:.1f}s")


if __name__ == "__main__":
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        sys.exit(1)
