# 🗣️ Piper TTS 设置指南

本文档介绍如何为《Her》助手设置和配置 Piper TTS 服务。

## 📋 前提条件

- Python 3.8+ (推荐 3.11+)
- 已激活的虚拟环境
- 网络连接（用于下载语音模型）

## 🚀 快速安装

### 1. 安装 Piper TTS

```bash
# 方法1: 通过 pip 安装（推荐）
pip install piper-tts

# 方法2: 下载预编译版本
# 访问: https://github.com/rhasspy/piper/releases
# 下载适合您系统的版本
```

### 2. 启动 Piper TTS 服务

```bash
# 启动 HTTP 服务器
python -m piper.http_server --host 0.0.0.0 --port 8001

# 或者在后台运行
nohup python -m piper.http_server --host 0.0.0.0 --port 8001 > piper.log 2>&1 &
```

### 3. 验证服务运行

```bash
# 测试服务是否正常
curl http://localhost:8001/health

# 测试语音合成
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}' \
  --output test.wav
```

## 🎵 语音模型配置

### 支持的语音

#### 英语
- `en_US-lessac-medium` (默认) - 美式英语，女声
- `en_US-amy-medium` - 美式英语，女声
- `en_US-ryan-medium` - 美式英语，男声
- `en_GB-alba-medium` - 英式英语，女声

#### 中文
- `zh_CN-huayan-medium` - 中文普通话，女声

### 环境变量配置

在 `.env` 文件中设置：

```bash
# Piper TTS 配置
PIPER_BASE_URL=http://localhost:8001
PIPER_VOICE=en_US-lessac-medium

# 中文语音（可选）
# PIPER_VOICE=zh_CN-huayan-medium
```

## 🔧 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口是否被占用
lsof -i :8001

# 使用其他端口
python -m piper.http_server --host 0.0.0.0 --port 8002
# 记得更新 .env 中的 PIPER_BASE_URL
```

#### 2. 语音模型下载失败
```bash
# 手动下载模型
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices

# 下载英语模型
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# 下载中文模型
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
```

#### 3. 音频质量问题
- 尝试不同的语音模型
- 检查系统音频设置
- 确保音频驱动程序正常

### 性能优化

#### 1. 系统资源
```bash
# 检查系统资源使用
htop
# 或
top
```

#### 2. 模型选择
- `medium` 模型：平衡质量和性能
- `low` 模型：更快，质量稍低
- `high` 模型：最高质量，需要更多资源

## 🧪 测试集成

运行测试脚本验证配置：

```bash
# 测试 Piper TTS 集成
python test_piper.py

# 运行完整验证
python verify.py
```

## 🎯 生产环境部署

### 1. 服务管理

创建 systemd 服务文件 `/etc/systemd/system/piper-tts.service`：

```ini
[Unit]
Description=Piper TTS HTTP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python -m piper.http_server --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable piper-tts
sudo systemctl start piper-tts
```

### 2. 负载均衡

对于高并发场景，可以运行多个 Piper TTS 实例：

```bash
# 启动多个实例
python -m piper.http_server --host 0.0.0.0 --port 8001 &
python -m piper.http_server --host 0.0.0.0 --port 8002 &
python -m piper.http_server --host 0.0.0.0 --port 8003 &
```

## 📊 性能对比

| 特性 | Piper TTS | Kokoro TTS | Google TTS |
|------|-----------|------------|------------|
| 本地运行 | ✅ | ✅ | ❌ |
| 安装难度 | 简单 | 复杂 | 简单 |
| Python 3.13 支持 | ✅ | ❌ | ✅ |
| 中文支持 | ✅ | ✅ | ✅ |
| 语音质量 | 高 | 很高 | 很高 |
| 资源占用 | 低 | 中等 | 低（云端） |
| 隐私保护 | 完全 | 完全 | 有限 |

## 🔗 相关链接

- [Piper TTS 官方仓库](https://github.com/rhasspy/piper)
- [语音模型下载](https://huggingface.co/rhasspy/piper-voices)
- [Pipecat 文档](https://docs.pipecat.ai)
- [Her Assistant 项目](../README.md)

---

**注意**: 本指南基于 Piper TTS 的最新版本编写。如果遇到问题，请检查官方文档获取最新信息。
