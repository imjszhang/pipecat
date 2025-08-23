#!/usr/bin/env python3

"""
《Her》风格AI助手 - 系统验证脚本
检查所有依赖和服务是否正确配置
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


# 颜色定义
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def print_status(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def print_header(message: str):
    print(f"\n{Colors.PURPLE}{message}{Colors.NC}")
    print("=" * len(message))


class SystemVerifier:
    """系统验证器"""

    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

        # 加载环境变量
        self.load_env()

    def load_env(self):
        """加载环境变量"""
        env_file = Path(".env")
        if env_file.exists():
            from dotenv import load_dotenv

            load_dotenv()
            print_success("环境变量已加载")
        else:
            print_warning(".env 文件不存在")

    def check_python_version(self) -> bool:
        """检查 Python 版本"""
        print_header("🐍 Python 环境检查")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version.major >= 3 and version.minor >= 10:
            print_success(f"Python 版本: {version_str} ✓")
            return True
        else:
            self.issues.append(f"Python 版本过低: {version_str}，需要 3.10+")
            return False

    def check_virtual_env(self) -> bool:
        """检查虚拟环境"""
        venv = os.getenv("VIRTUAL_ENV")
        if venv:
            print_success(f"虚拟环境: {venv} ✓")
            return True
        else:
            self.warnings.append("未检测到虚拟环境，建议使用虚拟环境")
            return False

    def check_dependencies(self) -> bool:
        """检查 Python 依赖"""
        print_header("📦 依赖检查")

        required_packages = [
            "pipecat",
            "torch",
            "transformers",
            "whisper",
            "requests",
            "dotenv",
            "loguru",
        ]

        optional_packages = [
            "pyaudio",
            "soundfile",
            "onnxruntime",
        ]

        all_good = True

        # 检查必需包
        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                print_success(f"{package} ✓")
            except ImportError:
                self.issues.append(f"缺少必需包: {package}")
                all_good = False

        # 检查可选包
        for package in optional_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                print_success(f"{package} ✓ (可选)")
            except ImportError:
                self.warnings.append(f"缺少可选包: {package}")

        return all_good

    def check_ollama_service(self) -> bool:
        """检查 Ollama 服务"""
        print_header("🧠 Ollama 服务检查")

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("OLLAMA_MODEL", "gemma3:4b")

        try:
            # 检查服务状态
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print_success(f"Ollama 服务运行正常: {base_url} ✓")

                # 检查模型
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]

                if any(model_name in name for name in model_names):
                    print_success(f"模型 {model_name} 已安装 ✓")
                    return True
                else:
                    self.issues.append(
                        f"模型 {model_name} 未安装，请运行: ollama pull {model_name}"
                    )
                    print_error(f"可用模型: {', '.join(model_names)}")
                    return False
            else:
                self.issues.append(f"Ollama 服务响应异常: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            self.issues.append(f"无法连接到 Ollama 服务: {base_url}")
            self.issues.append("请确保 Ollama 服务正在运行: ollama serve")
            return False
        except Exception as e:
            self.issues.append(f"Ollama 服务检查失败: {e}")
            return False

    def check_tts_services(self) -> bool:
        """检查 TTS 服务"""
        print_header("🗣️  TTS 服务检查")

        tts_available = False

        # 检查 Piper TTS
        piper_url = os.getenv("PIPER_BASE_URL", "http://localhost:8001")
        try:
            response = requests.get(f"{piper_url}/health", timeout=3)
            if response.status_code == 200:
                print_success(f"Piper TTS 服务运行正常: {piper_url} ✓")
                tts_available = True
        except:
            print_warning(f"Piper TTS 服务未运行: {piper_url}")

        # Kokoro TTS 已被 Piper TTS 替代，不再检查

        # 检查 Google TTS API
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            print_success("Google TTS API 密钥已配置 ✓")
            tts_available = True
        else:
            print_warning("Google TTS API 密钥未配置")

        if not tts_available:
            self.issues.append("没有可用的 TTS 服务，请启动 Piper TTS 或配置 Google TTS")
            return False

        return True

    def check_audio_system(self) -> bool:
        """检查音频系统"""
        print_header("🎵 音频系统检查")

        try:
            import pyaudio

            p = pyaudio.PyAudio()

            # 检查输入设备
            input_devices = []
            output_devices = []

            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    input_devices.append(info["name"])
                if info["maxOutputChannels"] > 0:
                    output_devices.append(info["name"])

            p.terminate()

            if input_devices:
                print_success(f"找到 {len(input_devices)} 个输入设备 ✓")
            else:
                self.issues.append("未找到音频输入设备")

            if output_devices:
                print_success(f"找到 {len(output_devices)} 个输出设备 ✓")
            else:
                self.issues.append("未找到音频输出设备")

            return len(input_devices) > 0 and len(output_devices) > 0

        except ImportError:
            self.warnings.append("PyAudio 未安装，无法检查音频设备")
            return True  # 不阻止运行
        except Exception as e:
            self.warnings.append(f"音频系统检查失败: {e}")
            return True  # 不阻止运行

    def check_system_resources(self) -> bool:
        """检查系统资源"""
        print_header("💻 系统资源检查")

        try:
            import psutil

            # 检查内存
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)

            if memory_gb >= 16:
                print_success(f"系统内存: {memory_gb:.1f}GB ✓")
            elif memory_gb >= 8:
                print_warning(f"系统内存: {memory_gb:.1f}GB (推荐16GB+)")
            else:
                self.issues.append(f"系统内存不足: {memory_gb:.1f}GB (最低8GB)")

            # 检查磁盘空间
            disk = psutil.disk_usage(".")
            disk_free_gb = disk.free / (1024**3)

            if disk_free_gb >= 50:
                print_success(f"可用磁盘空间: {disk_free_gb:.1f}GB ✓")
            elif disk_free_gb >= 20:
                print_warning(f"可用磁盘空间: {disk_free_gb:.1f}GB (推荐50GB+)")
            else:
                self.issues.append(f"磁盘空间不足: {disk_free_gb:.1f}GB (最低20GB)")

            # 检查 CPU
            cpu_count = psutil.cpu_count()
            print_success(f"CPU 核心数: {cpu_count} ✓")

            return memory_gb >= 8 and disk_free_gb >= 20

        except ImportError:
            self.warnings.append("psutil 未安装，无法检查系统资源")
            return True
        except Exception as e:
            self.warnings.append(f"系统资源检查失败: {e}")
            return True

    def check_gpu_support(self) -> bool:
        """检查 GPU 支持"""
        print_header("🚀 GPU 支持检查")

        try:
            import torch

            # 检查 CUDA
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                print_success(f"CUDA 可用: {gpu_count} GPU(s), {gpu_name} ✓")

                # 检查 GPU 内存
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                print_success(f"GPU 内存: {gpu_memory:.1f}GB ✓")

                return True

            # 检查 Apple Silicon MPS
            elif torch.backends.mps.is_available():
                print_success("Apple Silicon MPS 可用 ✓")
                return True

            else:
                print_warning("GPU 加速不可用，将使用 CPU")
                return True  # CPU 也可以工作

        except Exception as e:
            self.warnings.append(f"GPU 检查失败: {e}")
            return True

    def check_network_connectivity(self) -> bool:
        """检查网络连接"""
        print_header("🌐 网络连接检查")

        test_urls = [
            ("HuggingFace", "https://huggingface.co"),
            ("GitHub", "https://github.com"),
        ]

        # 检查 HuggingFace 镜像
        hf_endpoint = os.getenv("HF_ENDPOINT")
        if hf_endpoint:
            test_urls.append(("HF Mirror", hf_endpoint))

        all_good = True
        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_success(f"{name} 连接正常 ✓")
                else:
                    print_warning(f"{name} 连接异常: {response.status_code}")
            except Exception as e:
                print_warning(f"{name} 连接失败: {e}")
                # 网络问题不阻止本地运行

        return True

    def check_configuration(self) -> bool:
        """检查配置文件"""
        print_header("⚙️  配置检查")

        env_file = Path(".env")
        if not env_file.exists():
            self.issues.append(".env 文件不存在，请从 env.example 复制")
            return False

        print_success(".env 文件存在 ✓")

        # 检查关键配置
        required_configs = [
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            "WHISPER_MODEL",
        ]

        for config in required_configs:
            value = os.getenv(config)
            if value:
                print_success(f"{config}: {value} ✓")
            else:
                self.warnings.append(f"配置项 {config} 未设置，将使用默认值")

        return True

    def run_verification(self) -> bool:
        """运行完整验证"""
        print_header("🔍 《Her》风格AI助手系统验证")

        checks = [
            ("Python 版本", self.check_python_version),
            ("虚拟环境", self.check_virtual_env),
            ("依赖包", self.check_dependencies),
            ("配置文件", self.check_configuration),
            ("Ollama 服务", self.check_ollama_service),
            ("TTS 服务", self.check_tts_services),
            ("音频系统", self.check_audio_system),
            ("系统资源", self.check_system_resources),
            ("GPU 支持", self.check_gpu_support),
            ("网络连接", self.check_network_connectivity),
        ]

        results = {}
        for name, check_func in checks:
            try:
                results[name] = check_func()
            except Exception as e:
                print_error(f"{name} 检查失败: {e}")
                results[name] = False
                self.issues.append(f"{name} 检查异常: {e}")

        # 显示总结
        self.show_summary(results)

        # 返回是否可以运行
        critical_checks = ["Python 版本", "依赖包", "Ollama 服务", "TTS 服务"]
        return all(results.get(check, False) for check in critical_checks)

    def show_summary(self, results: Dict[str, bool]):
        """显示验证总结"""
        print_header("📊 验证总结")

        # 显示检查结果
        for name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {name}")

        # 显示问题
        if self.issues:
            print_header("❌ 需要解决的问题")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")

        # 显示警告
        if self.warnings:
            print_header("⚠️  警告")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")

        # 显示建议
        print_header("💡 建议")
        if not self.issues:
            print_success("🎉 所有关键检查都通过了！可以启动《Her》助手")
            print("运行命令: python bot.py")
        else:
            print_error("请先解决上述问题，然后重新运行验证")
            print("解决问题后运行: python verify.py")


def main():
    """主函数"""
    verifier = SystemVerifier()

    try:
        success = verifier.run_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"验证过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
