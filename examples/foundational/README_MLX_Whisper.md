# Apple MLX Whisper Large v3 Turbo 部署指南

## 📋 概述

这些示例展示如何在 Apple Silicon Mac 上部署 MLX 优化的 Whisper Large v3 Turbo 语音转文本服务。

## 🍎 系统要求

- **设备**: MacBook Pro/Air with M1/M2/M3/M4 芯片
- **系统**: macOS 12.0 或更高版本
- **内存**: 至少 8GB RAM (推荐 16GB+)
- **存储**: 至少 5GB 可用空间

## 🚀 快速开始

### 1. 安装依赖

```bash
# 确保已安装 MLX Whisper 支持
uv add mlx-whisper

# 或使用 pip
pip install mlx-whisper
```

### 2. 基础使用

运行基础示例：

```bash
python apple_mlx_whisper_example.py
```

### 3. 高级使用

1. 复制配置文件：
```bash
cp mlx_whisper.env .env
```

2. 根据需要修改 `.env` 文件中的配置

3. 运行高级示例：
```bash
python apple_mlx_whisper_advanced.py
```

## 📁 文件说明

| 文件 | 描述 |
|------|------|
| `apple_mlx_whisper_example.py` | 基础示例，最简单的 MLX Whisper 部署 |
| `apple_mlx_whisper_advanced.py` | 高级示例，包含完整配置和错误处理 |
| `mlx_whisper.env` | 环境变量配置模板 |
| `README_MLX_Whisper.md` | 本说明文档 |

## ⚙️ 配置选项

### 模型选择

- `large-v3-turbo` (推荐): 最新的 v3 Turbo 版本，速度最快
- `large-v3-turbo-q4`: 4位量化版本，更省内存

### VAD (语音活动检测) 配置

- `VAD_CONFIDENCE`: 置信度阈值 (0.0-1.0)
- `VAD_START_SECS`: 语音开始检测时间
- `VAD_STOP_SECS`: 语音结束检测时间
- `VAD_MIN_VOLUME`: 最小音量阈值

### 性能配置

- `ENABLE_METRICS`: 启用性能监控
- `ENABLE_USAGE_METRICS`: 启用使用统计
- `REPORT_ONLY_INITIAL_TTFB`: 仅报告首次响应时间

## 🔧 使用技巧

### 1. 优化性能

- 使用 `large-v3-turbo` 模型获得最佳速度
- 调整 VAD 参数减少延迟
- 在安静环境中使用以提高精度

### 2. 内存优化

- 对于 8GB 内存设备，使用 `large-v3-turbo-q4` 量化模型
- 关闭不必要的性能监控
- 调小音频缓冲区大小

### 3. 多语言支持

- 留空 `TRANSCRIPTION_LANGUAGE` 启用自动检测
- 设置特定语言代码（如 `zh`, `en`）提高特定语言精度

## 📊 性能特点

| 指标 | Apple MLX |
|------|-----------|
| **转录延迟** | 300-600ms |
| **首字延迟** | 150-300ms |
| **内存占用** | ~3GB |
| **CPU 使用率** | 低 (GPU 加速) |
| **功耗** | 很低 |

## 🛠 故障排除

### 常见问题

#### 1. 导入错误
```
ImportError: No module named 'mlx_whisper'
```
**解决方案**: 确保安装了 MLX Whisper
```bash
uv add mlx-whisper
```

#### 2. 设备不兼容
```
错误: 此示例仅支持 macOS 系统
```
**解决方案**: 此示例专为 Apple Silicon Mac 设计，在其他设备上请使用其他部署方案

#### 3. 内存不足
```
MLX 模型加载失败
```
**解决方案**: 
- 使用量化模型 `large-v3-turbo-q4`
- 关闭其他占用内存的应用
- 确保有足够的可用内存

#### 4. 音频权限问题
```
音频输入设备访问被拒绝
```
**解决方案**: 
- 在系统偏好设置中授予麦克风权限
- 重启终端应用

### 性能调优

#### 降低延迟
```env
VAD_START_SECS=0.1
VAD_STOP_SECS=1.0
VAD_CONFIDENCE=0.8
```

#### 提高准确性
```env
VAD_CONFIDENCE=0.6
VAD_MIN_VOLUME=0.4
TRANSCRIPTION_TEMPERATURE=0.0
```

#### 省内存配置
```env
MLX_WHISPER_MODEL=large-v3-turbo-q4
AUDIO_BUFFER_SIZE=2048
ENABLE_METRICS=false
```

## 🔍 调试技巧

### 启用详细日志
```env
LOG_LEVEL=DEBUG
SHOW_TIMESTAMP=true
SHOW_TRANSCRIPTION_COUNT=true
```

### 监控性能
```env
ENABLE_METRICS=true
ENABLE_USAGE_METRICS=true
```

## 📚 相关资源

- [Pipecat 官方文档](https://docs.pipecat.ai/)
- [MLX 官方仓库](https://github.com/ml-explore/mlx)
- [MLX Whisper GitHub](https://github.com/ml-explore/mlx-examples/tree/main/whisper)
- [OpenAI Whisper 官方文档](https://openai.com/research/whisper)

## 💡 最佳实践

1. **环境准备**: 在安静环境中测试，确保音频质量
2. **配置调优**: 根据具体需求调整 VAD 和模型参数
3. **性能监控**: 启用指标监控以优化性能
4. **错误处理**: 使用高级示例中的错误处理机制
5. **资源管理**: 及时清理资源，避免内存泄漏

## 🤝 支持

如有问题或需要帮助：
- [Pipecat Discord 社区](https://discord.gg/pipecat)
- [GitHub Issues](https://github.com/pipecat-ai/pipecat/issues)

---

**创建时间**: 2024年12月
**适用版本**: Pipecat latest, MLX Whisper 0.4.2+
