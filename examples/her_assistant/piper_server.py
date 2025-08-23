#!/usr/bin/env python3
"""
简单的 Piper TTS HTTP 服务器
为《Her》助手提供本地 TTS 服务
"""

import io
import os
import subprocess
import tempfile

from flask import Flask, jsonify, request, send_file
from loguru import logger

app = Flask(__name__)

# 配置
PIPER_MODEL_DIR = "./models"
DEFAULT_VOICE = "zh_CN-huayan-medium"


def get_model_path(voice_name):
    """获取语音模型路径"""
    model_file = f"{voice_name}.onnx"
    model_path = os.path.join(PIPER_MODEL_DIR, model_file)

    if os.path.exists(model_path):
        return model_path

    # 尝试其他可能的路径
    alt_paths = [
        os.path.expanduser(f"~/.local/share/piper/voices/{model_file}"),
        f"/usr/local/share/piper/voices/{model_file}",
    ]

    for path in alt_paths:
        if os.path.exists(path):
            return path

    return None


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "ok", "service": "piper-tts"})


@app.route("/", methods=["POST"])
def synthesize():
    """语音合成端点"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400

        text = data["text"]
        voice = data.get("voice", DEFAULT_VOICE)

        logger.info(f"合成语音: '{text}' 使用声音: {voice}")

        # 获取模型路径
        model_path = get_model_path(voice)
        if not model_path:
            return jsonify({"error": f"Voice model not found: {voice}"}), 404

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 调用 Piper 命令行工具
            cmd = ["piper", "--model", model_path, "--output_file", temp_path]

            # 运行 Piper
            process = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=30)

            if process.returncode != 0:
                logger.error(f"Piper 错误: {process.stderr}")
                return jsonify({"error": "TTS synthesis failed"}), 500

            # 返回音频文件
            return send_file(temp_path, mimetype="audio/wav", as_attachment=False)

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"语音合成错误: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/voices", methods=["GET"])
def list_voices():
    """列出可用的语音"""
    voices = []

    if os.path.exists(PIPER_MODEL_DIR):
        for file in os.listdir(PIPER_MODEL_DIR):
            if file.endswith(".onnx"):
                voice_name = file[:-5]  # 移除 .onnx 扩展名
                voices.append(voice_name)

    return jsonify({"voices": voices})


if __name__ == "__main__":
    logger.info("🗣️ 启动 Piper TTS HTTP 服务器...")
    logger.info(f"📁 模型目录: {PIPER_MODEL_DIR}")
    logger.info(f"🎵 默认声音: {DEFAULT_VOICE}")

    # 检查模型是否存在
    if not os.path.exists(PIPER_MODEL_DIR):
        logger.warning(f"⚠️ 模型目录不存在: {PIPER_MODEL_DIR}")

    app.run(host="0.0.0.0", port=8001, debug=False)
