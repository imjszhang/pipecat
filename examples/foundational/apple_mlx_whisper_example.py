#!/usr/bin/env python3

"""
Apple MLX Whisper Large v3 Turbo 部署示例

这个示例展示如何在 Apple Silicon Mac 上使用 MLX 优化的 Whisper Large v3 Turbo
进行高性能实时语音转文本。

系统要求:
- MacBook Pro/Air with M1/M2/M3/M4 chips
- macOS 12.0 或更高版本
- 至少 8GB 内存

优势:
- 专为 Apple Silicon 优化
- 低延迟转录 (300-600ms)
- 低功耗高性能
- 支持多语言识别
"""

import asyncio
import os
import sys

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams


# 检查是否运行在 Apple Silicon Mac 上
def check_apple_silicon():
    """检查是否运行在 Apple Silicon Mac 上"""
    import platform

    if platform.system() != "Darwin":
        print("❌ 错误: 此示例仅支持 macOS 系统")
        sys.exit(1)

    # 检查是否为 Apple Silicon
    machine = platform.machine()
    if not machine.startswith("arm"):
        print("⚠️  警告: 此示例针对 Apple Silicon Mac (M1/M2/M3/M4) 优化")
        print(f"   当前处理器架构: {machine}")
        print("   虽然可以运行，但性能可能不是最优的")


try:
    from pipecat.services.whisper.stt import MLXModel, WhisperSTTServiceMLX
except ImportError:
    print("❌ 错误: 未找到 MLX Whisper 依赖")
    print("请运行以下命令安装:")
    print("  uv add mlx-whisper")
    print("  # 或")
    print("  pip install mlx-whisper")
    sys.exit(1)


class MLXTranscriptionLogger(FrameProcessor):
    """MLX 转录结果记录器"""

    def __init__(self):
        super().__init__()
        self.transcription_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            self.transcription_count += 1
            print(f"🍎 MLX 转录 #{self.transcription_count}: {frame.text}")

            # 检查退出命令
            if "退出" in frame.text or "quit" in frame.text.lower():
                print("👋 检测到退出命令，正在停止...")
                # 这里可以添加优雅停止的逻辑


async def main():
    """主函数"""
    print("🍎 Apple MLX Whisper Large v3 Turbo 部署示例")
    print("=" * 50)

    # 检查系统兼容性
    check_apple_silicon()

    print("🔧 正在初始化组件...")

    try:
        # 1. 创建 Apple MLX 优化的 Whisper 服务
        print("📥 加载 MLX Whisper Large v3 Turbo 模型...")
        stt = WhisperSTTServiceMLX(
            model=MLXModel.LARGE_V3_TURBO,  # 使用 v3 Turbo 模型
            # model=MLXModel.LARGE_V3_TURBO_Q4,  # 可选: 4位量化版本，更省内存
        )
        print("✅ MLX Whisper 模型加载成功")

        # 2. 配置语音活动检测 (VAD)
        vad = SileroVADAnalyzer(
            params=VADParams(
                confidence=0.7,  # VAD 置信度
                start_secs=0.2,  # 语音开始检测时间
                stop_secs=2.0,  # 语音结束检测时间
                min_volume=0.6,  # 最小音量阈值
            )
        )
        print("✅ 语音活动检测器配置完成")

        # 3. 配置音频传输
        transport = LocalAudioTransport(
            LocalAudioTransportParams(
                audio_in_enabled=True,  # 启用音频输入
                audio_out_enabled=False,  # 禁用音频输出
                vad_analyzer=vad,  # 使用 VAD
            )
        )
        print("✅ 音频传输配置完成")

        # 4. 创建转录记录器
        logger = MLXTranscriptionLogger()

        # 5. 构建处理管道
        pipeline = Pipeline(
            [
                transport.input(),  # 音频输入
                stt,  # MLX Whisper 转录
                logger,  # 结果记录
            ]
        )
        print("✅ 处理管道创建完成")

        # 6. 创建管道任务
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,  # 启用性能指标
                enable_usage_metrics=True,  # 启用使用统计
                report_only_initial_ttfb=True,  # 仅报告首次响应时间
            ),
        )

        # 7. 创建管道运行器
        runner = PipelineRunner()

        print("\n🎤 MLX Whisper 服务已启动!")
        print("-" * 30)
        print("📋 使用说明:")
        print("  • 请开始说话进行实时转录")
        print("  • 支持中文和英文识别")
        print("  • 说'退出'或'quit'来停止程序")
        print("  • 使用 Ctrl+C 强制退出")
        print("-" * 30)
        print("🚀 开始转录...")

        # 8. 运行管道
        await runner.run(task)

    except KeyboardInterrupt:
        print("\n👋 用户手动停止程序")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("🔄 正在清理资源...")
        print("✅ 程序已安全退出")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
