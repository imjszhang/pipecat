#!/usr/bin/env python3

"""
Silero VAD Pipeline 集成示例

本示例展示如何在实际的 Pipecat Pipeline 中集成 Silero VAD，
包括与 WebSocket 传输层的完整集成。

运行前请确保：
1. pip install "onnxruntime~=1.20.1"
2. pip install "websockets>=13.1,<15.0"
3. pip install "fastapi>=0.115.6,<0.117.0"
"""

import asyncio
import os
import sys
from typing import Optional

from loguru import logger

# 添加 src 目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import AudioRawFrame, Frame, SystemFrame, TransportMessageFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)


class VADEventLogger(FrameProcessor):
    """VAD 事件日志记录器，监控和记录所有 VAD 相关事件"""

    def __init__(self):
        super().__init__()
        self._vad_state = "unknown"
        self._audio_frame_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """处理帧并记录 VAD 相关事件"""

        # 监控传输消息中的 VAD 状态变化
        if isinstance(frame, TransportMessageFrame):
            if frame.message.get("type") == "vad_state_changed":
                old_state = self._vad_state
                new_state = frame.message.get("state", "unknown")
                self._vad_state = new_state

                # 记录状态变化
                state_emoji = {"listening": "👂", "speaking": "🗣️", "quiet": "🤫", "unknown": "❓"}

                logger.info(
                    f"{state_emoji.get(new_state, '🔄')} VAD 状态变化: {old_state} → {new_state}"
                )

        # 监控音频帧
        elif isinstance(frame, AudioRawFrame):
            self._audio_frame_count += 1
            if self._audio_frame_count % 100 == 0:  # 每100帧记录一次
                logger.debug(
                    f"📊 已处理 {self._audio_frame_count} 个音频帧 "
                    f"(当前 VAD 状态: {self._vad_state})"
                )

        # 监控系统帧
        elif isinstance(frame, SystemFrame):
            logger.debug(f"🔧 系统帧: {type(frame).__name__}")

        # 继续传递帧
        await self.push_frame(frame, direction)


class AudioProcessor(FrameProcessor):
    """音频处理器，模拟实际的音频处理逻辑"""

    def __init__(self):
        super().__init__()
        self._processed_frames = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """处理音频帧"""

        if isinstance(frame, AudioRawFrame):
            self._processed_frames += 1

            # 模拟音频处理
            # 在实际应用中，这里可能是 STT、TTS 或其他音频处理逻辑
            if self._processed_frames % 50 == 0:
                logger.debug(f"🎵 处理音频帧 #{self._processed_frames}")

        # 继续传递帧
        await self.push_frame(frame, direction)


def create_vad_analyzer_for_scenario(scenario: str) -> SileroVADAnalyzer:
    """根据场景创建 VAD 分析器"""

    scenario_configs = {
        "default": VADParams(confidence=0.7, start_secs=0.2, stop_secs=0.8, min_volume=0.6),
        "quiet": VADParams(confidence=0.6, start_secs=0.15, stop_secs=0.6, min_volume=0.4),
        "noisy": VADParams(confidence=0.8, start_secs=0.3, stop_secs=1.0, min_volume=0.7),
        "fast": VADParams(confidence=0.7, start_secs=0.1, stop_secs=0.4, min_volume=0.5),
    }

    params = scenario_configs.get(scenario, scenario_configs["default"])

    logger.info(f"📋 创建 {scenario} 场景的 VAD 分析器")
    logger.info(f"   - 置信度: {params.confidence}")
    logger.info(f"   - 开始时间: {params.start_secs}s")
    logger.info(f"   - 结束时间: {params.stop_secs}s")
    logger.info(f"   - 音量阈值: {params.min_volume}")

    return SileroVADAnalyzer(sample_rate=16000, params=params)


async def create_websocket_pipeline(
    vad_analyzer: SileroVADAnalyzer, host: str = "localhost", port: int = 8765
) -> tuple[Pipeline, PipelineTask]:
    """创建带 VAD 的 WebSocket Pipeline"""

    logger.info(f"🔧 创建 WebSocket Pipeline (VAD 集成)")
    logger.info(f"   - 主机: {host}")
    logger.info(f"   - 端口: {port}")

    # 创建传输参数
    transport_params = FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=vad_analyzer,
        add_wav_header=False,
        audio_in_sample_rate=16000,
        audio_out_sample_rate=16000,
    )

    # 创建传输层
    transport = FastAPIWebsocketTransport(transport_params)

    # 创建处理器
    vad_logger = VADEventLogger()
    audio_processor = AudioProcessor()

    # 构建 Pipeline
    pipeline = Pipeline(
        [
            transport.input(),  # 音频输入
            vad_logger,  # VAD 事件记录
            audio_processor,  # 音频处理
            transport.output(),  # 音频输出
        ]
    )

    # 创建任务
    task = PipelineTask(pipeline)

    logger.info("✅ WebSocket Pipeline 创建完成")

    return pipeline, task


async def run_vad_demo(scenario: str = "default", duration: int = 30):
    """运行 VAD 演示"""

    logger.info(f"🚀 启动 Silero VAD 演示 (场景: {scenario})")
    logger.info("=" * 60)

    try:
        # 1. 创建 VAD 分析器
        vad_analyzer = create_vad_analyzer_for_scenario(scenario)

        # 2. 创建 Pipeline
        pipeline, task = await create_websocket_pipeline(vad_analyzer)

        # 3. 创建演示任务
        async def demo_task():
            """演示任务"""
            logger.info(f"⏱️  演示将运行 {duration} 秒...")
            logger.info("💡 你可以连接到 WebSocket 并发送音频数据进行测试")
            logger.info("   WebSocket URL: ws://localhost:8765")

            # 运行指定时间
            await asyncio.sleep(duration)

            logger.info("⏹️ 演示时间结束，正在停止...")

            # 发送停止帧
            await task.queue_frame(task.get_clock().get_stop_frame())

        # 4. 运行 Pipeline
        runner = PipelineRunner()
        await runner.run(task, demo_task())

        logger.info("✅ VAD 演示运行完成")

    except Exception as e:
        logger.error(f"❌ 演示运行失败: {e}")
        raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Silero VAD Pipeline 集成示例")
    parser.add_argument(
        "--scenario",
        choices=["default", "quiet", "noisy", "fast"],
        default="default",
        help="VAD 配置场景",
    )
    parser.add_argument("--duration", type=int, default=30, help="演示运行时间（秒）")

    args = parser.parse_args()

    # 设置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
    )

    try:
        # 运行演示
        asyncio.run(run_vad_demo(args.scenario, args.duration))

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断，演示结束")
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
