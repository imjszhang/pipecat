#!/usr/bin/env python3
"""
Gemma 2:2b 本地对话机器人示例
使用 Ollama API 直接调用，简单易用

运行方式:
1. 确保 Ollama 服务运行: ollama serve
2. 确保已下载模型: ollama pull gemma2:2b
3. 运行脚本: python examples/gemma_local_bot.py
"""

import asyncio
import json
import sys

import requests
from loguru import logger


class GemmaChat:
    """Gemma 对话管理器"""

    def __init__(self, base_url="http://localhost:11434", model="gemma2:2b"):
        self.base_url = base_url
        self.model = model
        self.conversation_history = []

    def add_system_message(self, content):
        """添加系统消息"""
        self.conversation_history.append({"role": "system", "content": content})

    def add_user_message(self, content):
        """添加用户消息"""
        self.conversation_history.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        """添加助手消息"""
        self.conversation_history.append({"role": "assistant", "content": content})

    async def get_response(self, user_input):
        """获取模型响应"""
        try:
            # 添加用户消息到历史
            self.add_user_message(user_input)

            # 构建提示词（包含对话历史）
            prompt = self._build_prompt()

            # 调用 Ollama API
            url = f"{self.base_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 300,
                },
            }

            response = requests.post(url, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "").strip()

                # 添加助手响应到历史
                self.add_assistant_message(assistant_response)

                return assistant_response
            else:
                logger.error(f"API 请求失败: {response.status_code}")
                return "抱歉，我遇到了一些问题，请重试。"

        except Exception as e:
            logger.error(f"获取响应时出错: {e}")
            return "抱歉，我遇到了一些问题，请重试。"

    def _build_prompt(self):
        """构建包含对话历史的提示词"""
        prompt_parts = []

        for message in self.conversation_history:
            role = message["role"]
            content = message["content"]

            if role == "system":
                prompt_parts.append(f"系统: {content}")
            elif role == "user":
                prompt_parts.append(f"用户: {content}")
            elif role == "assistant":
                prompt_parts.append(f"助手: {content}")

        prompt_parts.append("助手: ")  # 提示模型生成助手回复

        return "\n".join(prompt_parts)


async def main():
    """主函数"""

    print("🚀 Gemma 2:2b 本地对话机器人启动中...")
    print("=" * 60)

    # 检查 Ollama 服务
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Ollama 服务未运行，请先启动：ollama serve")
            return

        models = response.json().get("models", [])
        model_names = [model["name"] for model in models]

        if "gemma2:2b" not in model_names:
            logger.error("❌ Gemma2:2b 模型未找到，请先下载：ollama pull gemma2:2b")
            return

        logger.info("✅ Ollama 服务和模型检查通过")

    except Exception as e:
        logger.error(f"❌ 无法连接到 Ollama 服务：{e}")
        logger.error("请确保运行：ollama serve")
        return

    # 创建 Gemma 对话管理器
    chat = GemmaChat()

    # 设置系统提示
    chat.add_system_message("""你是一个友好、有帮助的AI助手，基于Google的Gemma模型。

请遵循以下规则：
1. 用简洁、自然的中文回答问题
2. 保持对话友好和有帮助
3. 回答长度控制在1-3句话内
4. 如果不确定答案，请诚实说明
5. 可以进行日常对话、回答问题、提供建议等

你现在正在本地运行，完全离线工作。""")

    print("🤖 Gemma 助手已准备就绪！")
    print("💡 输入 'quit'、'exit' 或 '退出' 来结束对话")
    print("=" * 60)

    # 启动对话循环
    try:
        while True:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()

            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "退出", "bye"]:
                break

            if not user_input:
                continue

            # 获取模型响应
            print("🤖 Gemma: ", end="", flush=True)
            response = await chat.get_response(user_input)
            print(response)

    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        print("\n👋 再见！感谢使用 Gemma 本地助手！")


async def simple_test():
    """简单的测试函数"""
    print("🧪 运行简单测试...")

    # 创建 Gemma 对话管理器
    chat = GemmaChat()

    try:
        # 发送测试消息
        print("📤 发送测试消息: 你好，请简单介绍一下你自己")
        response = await chat.get_response("你好，请简单介绍一下你自己")
        print(f"📥 收到响应: {response}")
        return True

    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 运行简单测试
        asyncio.run(simple_test())
    else:
        # 运行完整对话
        asyncio.run(main())
