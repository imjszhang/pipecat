# 《Her》风格AI助手 - 快速启动指南

> 5分钟内启动你的本地AI助手！🚀

## 🎯 一键启动

```bash
# 进入目录
cd /Volumes/home_x/github/fork/pipecat/examples/her_assistant

# 运行自动启动脚本
./start.sh
```

这个脚本会自动：
- ✅ 检查和安装依赖
- ✅ 启动 Ollama 服务
- ✅ 下载 Gemma 3 4B 模型
- ✅ 配置环境变量
- ✅ 启动《Her》助手

## 🔧 手动启动（如果自动脚本失败）

### 1. 准备环境
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ../../
pip install "pipecat-ai[whisper,silero,local-smart-turn,ollama,piper,webrtc,runner]"
```

### 2. 启动 Ollama
```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动服务
ollama serve &

# 下载模型
ollama pull gemma3:4b
```

### 3. 配置环境
```bash
# 复制配置文件
cp env.example .env

# 可选：编辑配置
nano .env
```

### 4. 启动助手
```bash
python bot.py
```

## 🌐 开始对话

1. 打开浏览器访问 `http://localhost:7860`
2. 允许麦克风权限
3. 点击连接按钮
4. 开始与AI助手对话

## 🔍 故障排除

### 运行验证脚本
```bash
python verify.py
```

### 常见问题

#### Ollama 连接失败
```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 重启服务
pkill ollama
ollama serve &
```

#### 模型未找到
```bash
# 检查已安装模型
ollama list

# 重新下载
ollama pull gemma3:4b
```

#### 端口被占用
```bash
# 检查端口使用
lsof -i :7860
lsof -i :11434

# 杀死占用进程
kill -9 <PID>
```

## 📊 系统要求

- **内存**: 16GB+ RAM
- **存储**: 50GB+ 可用空间
- **Python**: 3.10+
- **网络**: 首次下载模型需要网络

## 🎭 《Her》风格特色

- 🤗 **温暖对话**: 像朋友一样的交流方式
- 🧠 **深度理解**: 能够理解情感和上下文
- 🔒 **隐私保护**: 完全本地运行，数据不外传
- ⚡ **实时响应**: 低延迟的自然对话

## 💡 提示

- 首次启动需要下载模型，大约需要5-10分钟
- 后续启动只需要几秒钟
- 可以通过修改 `.env` 文件自定义配置
- 支持中英文对话（修改配置即可）

## 🆘 获取帮助

- 查看详细文档: `README.md`
- 运行系统检查: `python verify.py`
- 查看日志: `tail -f logs/her_assistant.log`

---

**享受与《Her》风格AI助手的对话吧！🎬✨**
