#!/usr/bin/env python3

"""
Silero VAD 使用示例

本示例展示了如何在 Pipecat 框架中使用 Silero VAD (Voice Activity Detection) 进行语音活动检测。
包括基本用法、参数配置和与传输层的集成示例。

运行前请确保：
1. 已安装 onnxruntime: pip install "onnxruntime~=1.20.1"
2. 有可用的音频输入设备
"""

import asyncio
import os
import sys
from typing import Awaitable

from loguru import logger

# 添加 src 目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import AudioRawFrame, Frame, TransportMessageFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.base_transport import BaseTransport, TransportParams


class VADMonitor(FrameProcessor):
    """VAD 状态监控处理器，用于监控和记录语音活动检测状态变化"""

    def __init__(self):
        super().__init__()
        self._current_state = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # 监控 VAD 状态变化
        if isinstance(frame, TransportMessageFrame):
            if frame.message.get("type") == "vad_state_changed":
                new_state = frame.message.get("state")
                if new_state != self._current_state:
                    self._current_state = new_state
                    logger.info(f"🎤 VAD 状态变化: {new_state}")

        # 监控音频帧
        elif isinstance(frame, AudioRawFrame):
            logger.debug(f"📊 收到音频帧: {len(frame.audio)} 字节")

        # 继续传递帧
        await self.push_frame(frame, direction)


class MockTransport(BaseTransport):
    """模拟传输层，用于演示 VAD 功能"""

    def __init__(self, params: TransportParams, **kwargs):
        super().__init__(params, **kwargs)
        self._running = False

    async def start(self, frame: Frame) -> None:
        """启动传输"""
        self._running = True
        logger.info("🚀 模拟传输层已启动")

    async def stop(self) -> None:
        """停止传输"""
        self._running = False
        logger.info("⏹️ 模拟传输层已停止")

    async def cleanup(self) -> None:
        """清理资源"""
        await self.stop()

    def vad_analyzer(self):
        """返回配置的 VAD 分析器"""
        return self._params.vad_analyzer


def create_basic_vad_analyzer():
    """创建基础的 Silero VAD 分析器"""
    logger.info("📝 创建基础 VAD 分析器")

    # 创建基础 VAD 分析器
    vad_analyzer = SileroVADAnalyzer()
    logger.info("✅ 基础 VAD 分析器创建成功")

    return vad_analyzer


def create_custom_vad_analyzer():
    """创建带自定义参数的 Silero VAD 分析器"""
    logger.info("📝 创建自定义 VAD 分析器")

    # 自定义 VAD 参数
    vad_params = VADParams(
        confidence=0.7,  # 语音检测置信度阈值 (0.0-1.0)
        start_secs=0.2,  # 确认语音开始前的等待时间（秒）
        stop_secs=0.8,  # 确认语音结束前的等待时间（秒）
        min_volume=0.6,  # 最小音量阈值 (0.0-1.0)
    )

    # 创建带自定义参数的 VAD 分析器
    vad_analyzer = SileroVADAnalyzer(
        sample_rate=16000,  # 采样率（8000 或 16000）
        params=vad_params,
    )

    logger.info("✅ 自定义 VAD 分析器创建成功")
    logger.info(f"   - 置信度阈值: {vad_params.confidence}")
    logger.info(f"   - 语音开始确认时间: {vad_params.start_secs}s")
    logger.info(f"   - 语音结束确认时间: {vad_params.stop_secs}s")
    logger.info(f"   - 最小音量阈值: {vad_params.min_volume}")

    return vad_analyzer


def create_scenario_vad_analyzers():
    """创建针对不同场景的 VAD 分析器"""
    logger.info("📝 创建场景化 VAD 分析器")

    # 安静环境配置
    quiet_params = VADParams(confidence=0.6, start_secs=0.15, stop_secs=0.6, min_volume=0.4)

    # 噪音环境配置
    noisy_params = VADParams(confidence=0.8, start_secs=0.3, stop_secs=1.0, min_volume=0.7)

    # 快节奏对话配置
    fast_conversation_params = VADParams(
        confidence=0.7, start_secs=0.1, stop_secs=0.4, min_volume=0.5
    )

    # 多模态实时通信配置
    multimodal_params = VADParams(
        confidence=0.7,
        start_secs=0.2,
        stop_secs=0.5,  # 更快的结束检测以配合实时API
        min_volume=0.6,
    )

    scenarios = {
        "安静环境": SileroVADAnalyzer(sample_rate=16000, params=quiet_params),
        "噪音环境": SileroVADAnalyzer(sample_rate=16000, params=noisy_params),
        "快节奏对话": SileroVADAnalyzer(sample_rate=16000, params=fast_conversation_params),
        "多模态通信": SileroVADAnalyzer(sample_rate=16000, params=multimodal_params),
    }

    for scenario, analyzer in scenarios.items():
        logger.info(f"✅ {scenario} VAD 分析器创建成功")

    return scenarios


async def demonstrate_vad_integration():
    """演示 VAD 与传输层的集成"""
    logger.info("🔧 演示 VAD 与传输层的集成")

    # 创建自定义 VAD 分析器
    vad_analyzer = create_custom_vad_analyzer()

    # 创建传输参数
    transport_params = TransportParams(
        audio_in_enabled=True, audio_out_enabled=True, vad_analyzer=vad_analyzer
    )

    # 创建模拟传输
    transport = MockTransport(transport_params)

    # 创建 VAD 监控器
    vad_monitor = VADMonitor()

    # 创建管道
    pipeline = Pipeline([transport.input(), vad_monitor, transport.output()])

    # 创建任务
    task = PipelineTask(pipeline)

    # 运行演示（短时间）
    logger.info("🎯 开始运行 VAD 集成演示...")

    async def run_demo():
        """运行演示任务"""
        try:
            # 运行 3 秒
            await asyncio.sleep(3)
            logger.info("✅ VAD 集成演示完成")
        except Exception as e:
            logger.error(f"❌ 演示过程中出错: {e}")
        finally:
            await task.queue_frame(task.get_clock().get_stop_frame())

    # 创建并运行任务
    runner = PipelineRunner()
    await runner.run(task, run_demo())


async def main():
    """主函数"""
    logger.info("🎉 Silero VAD 部署示例开始")
    logger.info("=" * 60)

    try:
        # 1. 创建基础 VAD 分析器
        logger.info("\n📋 步骤 1: 创建基础 VAD 分析器")
        basic_vad = create_basic_vad_analyzer()

        # 2. 创建自定义 VAD 分析器
        logger.info("\n📋 步骤 2: 创建自定义 VAD 分析器")
        custom_vad = create_custom_vad_analyzer()

        # 3. 创建场景化 VAD 分析器
        logger.info("\n📋 步骤 3: 创建场景化 VAD 分析器")
        scenario_vads = create_scenario_vad_analyzers()

        # 4. 演示 VAD 集成
        logger.info("\n📋 步骤 4: 演示 VAD 与传输层集成")
        await demonstrate_vad_integration()

        logger.info("\n" + "=" * 60)
        logger.info("🎊 Silero VAD 部署示例运行完成！")

        # 输出使用建议
        logger.info("\n💡 使用建议:")
        logger.info("  1. 根据你的应用场景选择合适的参数配置")
        logger.info("  2. 在生产环境中充分测试参数设置")
        logger.info("  3. 监控 VAD 状态变化以调试和优化")
        logger.info("  4. 结合中断策略使用以提供更好的用户体验")

        logger.info("\n📚 更多信息请参考: docs/guide/silero-vad-deployment-guide.md")

    except Exception as e:
        logger.error(f"❌ 示例运行过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
    )

    # 运行示例
    asyncio.run(main())
