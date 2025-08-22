#!/usr/bin/env python3

"""
Silero VAD 快速开始示例

这是一个最简化的 Silero VAD 使用示例，展示如何快速集成语音活动检测功能。

运行前请确保：
pip install "onnxruntime~=1.20.1"
"""

import os
import sys

# 添加 src 目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams


def main():
    """快速开始示例"""
    print("🎉 Silero VAD 快速开始")
    print("=" * 40)

    # 1. 基础用法
    print("\n📝 1. 基础用法")
    try:
        vad_analyzer = SileroVADAnalyzer()
        print("✅ 基础 VAD 分析器创建成功")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return

    # 2. 自定义参数
    print("\n📝 2. 自定义参数配置")
    try:
        vad_params = VADParams(
            confidence=0.7,  # 置信度阈值
            start_secs=0.2,  # 语音开始确认时间
            stop_secs=0.8,  # 语音结束确认时间
            min_volume=0.6,  # 最小音量阈值
        )

        custom_vad = SileroVADAnalyzer(sample_rate=16000, params=vad_params)
        print("✅ 自定义 VAD 分析器创建成功")
        print(f"   - 采样率: 16000 Hz")
        print(f"   - 置信度阈值: {vad_params.confidence}")
        print(f"   - 语音开始时间: {vad_params.start_secs}s")
        print(f"   - 语音结束时间: {vad_params.stop_secs}s")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return

    # 3. 检查模型信息
    print("\n📝 3. 模型信息")
    print(f"   - 支持的采样率: 8000Hz, 16000Hz")
    print(f"   - 所需帧数 (16kHz): {custom_vad.num_frames_required()}")
    print(f"   - 模型重置周期: 5秒")

    print("\n" + "=" * 40)
    print("🎊 Silero VAD 已成功部署在当前项目！")

    print("\n💡 下一步:")
    print("  1. 在你的传输层中配置 VAD 分析器")
    print("  2. 根据实际场景调整参数")
    print("  3. 参考完整示例: silero_vad_example.py")
    print("  4. 查看部署指南: docs/guide/silero-vad-deployment-guide.md")


if __name__ == "__main__":
    main()
