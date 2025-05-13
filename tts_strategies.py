import os
import edge_tts
import asyncio
from gtts import gTTS
import platform
import subprocess
import logging
import json
import requests
import time
import shutil

class TTSStrategy:
    """
    TTS 策略抽象类，所有具体的 TTS 类都需要实现这个接口。
    """
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        """
        将文本转换为语音音频文件。
        
        参数:
            text (str): 要转换成语音的文本。
            lang (str): 文本的语言代码。
            output_path (str): 音频文件保存路径。
        """
        raise NotImplementedError

class GTTSStrategy(TTSStrategy):
    """
    使用 gTTS 的具体策略实现。
    """
    def __init__(self):
        self.name = 'gtts'
    
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(output_path)
            return True
        except Exception as e:
            logging.error(f"gTTS 合成失败: {str(e)}")
            return False

class MacSayStrategy(TTSStrategy):
    """
    macOS 原生 say 命令策略。
    """
    def __init__(self):
        self.name = 'macsay'
    
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        try:
            # 使用系统自带的 say 命令
            subprocess.run(['say', '-v', 'Ting-Ting', text, '-o', output_path], check=True)
            return True
        except Exception as e:
            logging.error(f"MacSay 合成失败: {str(e)}")
            return False

class EdgeTTSStrategy(TTSStrategy):
    """
    使用 Microsoft Edge TTS 的策略实现
    """
    def __init__(self, voice='zh-CN-XiaoxiaoNeural'):
        self.name = 'edgetts'
        self.voice = voice
    
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            logging.error(f"Edge-TTS 合成失败: {str(e)}")
            return False

class DockerPaddleSpeechStrategy(TTSStrategy):
    def __init__(self, container_name='paddlespeech-tts', port=8000, audio_format='wav'):
        self.name = 'paddlespeech'
        self.container_name = container_name
        self.port = port
        self.audio_format = audio_format  # 支持 wav, mp3, pcm 等格式
        self.fallback_strategy = EdgeTTSStrategy()  # 使用 Edge-TTS 作为备选
        self._check_docker_installation()
    
    def _check_docker_installation(self):
        """检查 Docker 是否已安装"""
        if not shutil.which('docker'):
            logging.warning("Docker 未安装，将使用 Edge-TTS 作为备选")
            return False
        return True
    
    def _ensure_container_running(self):
        """确保 Docker 容器正在运行"""
        if not self._check_docker_installation():
            return False
            
        try:
            # 检查容器是否存在
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={self.container_name}'],
                capture_output=True,
                text=True
            )
            
            if self.container_name not in result.stdout:
                # 容器不存在，创建并启动
                print(f"正在启动 PaddleSpeech Docker 容器...")
                subprocess.run([
                    'docker', 'run', '-d',
                    '--name', self.container_name,
                    '-p', f'{self.port}:8000',
                    'paddlepaddle/paddlespeech:latest'
                ], check=True)
                # 等待容器启动
                time.sleep(10)
            elif 'Up' not in result.stdout:
                # 容器存在但未运行，启动它
                print(f"正在启动已存在的 PaddleSpeech 容器...")
                subprocess.run(['docker', 'start', self.container_name], check=True)
                time.sleep(5)
            
            print("PaddleSpeech 容器已就绪")
            return True
        except Exception as e:
            logging.error(f"Docker 容器管理失败: {str(e)}")
            return False
    
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        """异步版本的文本转语音方法"""
        # 如果 Docker 未安装或容器启动失败，使用备选策略
        if not self._check_docker_installation() or not self._ensure_container_running():
            logging.info("使用 Edge-TTS 作为备选策略")
            return await self.fallback_strategy.text_to_speech(text, lang, output_path)
            
        try:
            # 准备请求数据
            data = {
                'text': text,
                'lang': 'zh' if lang.startswith('zh') else 'en',
                'am': 'fastspeech2_csmsc' if lang.startswith('zh') else 'fastspeech2_ljspeech',
                'voc': 'hifigan_csmsc' if lang.startswith('zh') else 'hifigan_ljspeech',
                'format': self.audio_format  # 指定音频格式
            }
            
            # 发送请求到容器
            response = requests.post(
                f'http://localhost:{self.port}/tts',
                json=data,
                stream=True
            )
            response.raise_for_status()
            
            # 保存音频文件
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            logging.error(f"PaddleSpeech Docker 合成失败: {str(e)}")
            logging.info("切换到 Edge-TTS 作为备选策略")
            return await self.fallback_strategy.text_to_speech(text, lang, output_path)

# 根据操作系统选择合适的默认策略
def get_default_strategy():
    if platform.system() == 'Darwin':  # macOS
        return MacSayStrategy()
    else:
        return EdgeTTSStrategy()  # 其他系统默认使用 Edge-TTS