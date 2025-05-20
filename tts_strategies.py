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
import re
from ciku_gen.pinyin_map import get_hanzi_from_pinyin
from ciku_gen.pinyin_map import replace_custom_pinyin

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
        text = replace_custom_pinyin(text)
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
        text = replace_custom_pinyin(text)
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
        text = replace_custom_pinyin(text)
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            logging.error(f"Edge-TTS 合成失败: {str(e)}")
            return False

def convert_to_pinyin(text):
    """将英文单词转换为中文拼音格式"""
    # 常见英文单词到拼音的映射
    pinyin_map = {
        'run': 'rùn',
        'book': 'bù kè',
        'hello': 'hā lóu',
        'world': 'wò ér dé',
        'good': 'gǔ dé',
        'morning': 'mò níng',
        'afternoon': 'ā fú tè nǔn',
        'evening': 'yī wén níng',
        'night': 'nài tè',
        'thank': 'sān kè',
        'you': 'yōu',
        'welcome': 'wèi ér kè mǔ',
        'sorry': 'sāo ruì',
        'please': 'pǔ lì sī',
        'yes': 'yè sī',
        'no': 'nòu',
        'ok': 'ōu kèi',
        'bye': 'bài',
        'goodbye': 'gǔ dé bài',
        'see': 'xī',
        'you': 'yōu',
        'later': 'lèi tè',
        'tomorrow': 'tè mò róu',
        'today': 'tè déi',
        'yesterday': 'yè sī tè déi',
        'now': 'nào',
        'time': 'tài mǔ',
        'name': 'nèi mǔ',
        'what': 'wò tè',
        'where': 'wèi ér',
        'when': 'wèn',
        'why': 'wài',
        'how': 'hào',
        'who': 'hū',
        'which': 'wèi qí',
        'this': 'dì sī',
        'that': 'dà tè',
        'these': 'dì zī',
        'those': 'dòu zī',
        'here': 'hèi ér',
        'there': 'dèi ér',
        'come': 'kǎ mǔ',
        'go': 'gòu',
        'walk': 'wò kè',
        'run': 'rùn',
        'jump': 'zhāng pǔ',
        'eat': 'yī tè',
        'drink': 'zhuī kè',
        'sleep': 'sī lì pǔ',
        'wake': 'wèi kè',
        'work': 'wò kè',
        'play': 'pǔ lèi',
        'study': 'sī dǎ dì',
        'read': 'rì dé',
        'write': 'rài tè',
        'speak': 'sī pī kè',
        'listen': 'lì sēn',
        'watch': 'wò qí',
        'look': 'lù kè',
        'see': 'xī',
        'hear': 'hèi ér',
        'smell': 'sī mài ér',
        'taste': 'tèi sī tè',
        'touch': 'tǎ qí',
        'feel': 'fī ér',
        'think': 'sī yīng kè',
        'know': 'nòu',
        'understand': 'ān dé sī tǎn dé',
        'remember': 'rì mèn bèi ér',
        'forget': 'fò gèi tè',
        'learn': 'lèi én',
        'teach': 'tī qí',
        'help': 'hài ér pǔ',
        'need': 'nī dé',
        'want': 'wàng tè',
        'like': 'lài kè',
        'love': 'lǎ wǔ',
        'hate': 'hèi tè',
        'hope': 'hòu pǔ',
        'wish': 'wèi shì',
        'dream': 'zhuī mǔ',
        'believe': 'bì lì wǔ',
        'trust': 'tè rǎ sī tè',
        'doubt': 'dào tè',
        'fear': 'fī ér',
        'worry': 'wǎ rì',
        'cry': 'kè rài',
        'laugh': 'lā fū',
        'smile': 'sī mài ér',
        'happy': 'hā pī',
        'sad': 'sāi dé',
        'angry': 'ān gèi rì',
        'tired': 'tài ér dé',
        'hungry': 'hāng gèi rì',
        'thirsty': 'sè sī tè rì',
        'hot': 'hò tè',
        'cold': 'kòu dé',
        'warm': 'wò mǔ',
        'cool': 'kù ér',
        'big': 'bì gè',
        'small': 'sī mò ér',
        'tall': 'tò ér',
        'short': 'shò tè',
        'long': 'lóng',
        'wide': 'wài dé',
        'narrow': 'nā róu',
        'high': 'hài',
        'low': 'lòu',
        'deep': 'dī pǔ',
        'shallow': 'shā lòu',
        'heavy': 'hāi wèi',
        'light': 'lài tè',
        'fast': 'fā sī tè',
        'slow': 'sī lòu',
        'early': 'è lì',
        'late': 'lèi tè',
        'new': 'niū',
        'old': 'òu dé',
        'young': 'yāng',
        'beautiful': 'biū tè fū',
        'ugly': 'ā gèi lì',
        'good': 'gǔ dé',
        'bad': 'bāi dé',
        'right': 'rài tè',
        'wrong': 'ròng',
        'true': 'tè rū',
        'false': 'fò ér sī',
        'easy': 'yī zī',
        'difficult': 'dī fī kè tè',
        'simple': 'sī mǔ pǔ',
        'complex': 'kāng pǔ lèi kè sī',
        'possible': 'pò sī bō',
        'impossible': 'yī mò pò sī bō',
        'necessary': 'nèi sī sè rì',
        'unnecessary': 'ān nèi sī sè rì',
        'important': 'yī mò pò tè nèi tè',
        'unimportant': 'ān yī mò pò tè nèi tè',
        'interesting': 'yīn tè rèi sī tīng',
        'boring': 'bò rīng',
        'funny': 'fā nī',
        'serious': 'sī rì è sī',
        'dangerous': 'dèi zhā rèi sī',
        'safe': 'sèi fū',
        'clean': 'kè līn',
        'dirty': 'dè tì',
        'rich': 'rì qí',
        'poor': 'pù ér',
        'strong': 'sī zhuāng',
        'weak': 'wī kè',
        'hard': 'hā dé',
        'soft': 'sò fū tè',
        'smooth': 'sī mū sī',
        'rough': 'rā fū',
        'wet': 'wèi tè',
        'dry': 'dè rài',
        'full': 'fū ér',
        'empty': 'āi mò pèi tì',
        'open': 'ōu pèn',
        'close': 'kè lòu sī',
        'start': 'sī dā tè',
        'stop': 'sī dò pǔ',
        'begin': 'bì gèi yīn',
        'end': 'ān dé',
        'continue': 'kāng tè niū',
        'break': 'bù rèi kè',
        'finish': 'fī nī shì',
        'complete': 'kāng pǔ lì tè',
        'succeed': 'sā kè sī dé',
        'fail': 'fèi ér',
        'win': 'wīn',
        'lose': 'lū zī',
        'pass': 'pā sī',
        'fail': 'fèi ér',
        'try': 'tè rài',
        'attempt': 'ā tè mò pǔ tè',
        'succeed': 'sā kè sī dé',
        'fail': 'fèi ér',
        'win': 'wīn',
        'lose': 'lū zī',
        'pass': 'pā sī',
        'fail': 'fèi ér',
        'try': 'tè rài',
        'attempt': 'ā tè mò pǔ tè'
    }
    
    # 将文本转换为小写并去除空格
    text = text.lower().strip()
    
    # 如果文本在映射中，返回对应的拼音
    if text in pinyin_map:
        return pinyin_map[text]
    
    # 如果文本不在映射中，尝试按字母拆分并转换
    if text.isalpha():
        # 将每个字母转换为对应的拼音
        pinyin_parts = []
        for char in text:
            if char in pinyin_map:
                pinyin_parts.append(pinyin_map[char])
            else:
                # 如果字母没有对应的拼音，保持原样
                pinyin_parts.append(char)
        return ' '.join(pinyin_parts)
    
    # 如果既不是单词也不是纯字母，返回原文本
    return text

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
        logging.info("[PaddleSpeech] 检查 docker 命令可用性...")
        if not shutil.which('docker'):
            logging.warning("[PaddleSpeech] Docker 未安装或未在 PATH 中，将使用 Edge-TTS 作为备选")
            return False
        logging.info("[PaddleSpeech] docker 命令可用")
        return True
    
    def _ensure_container_running(self):
        """确保 Docker 容器正在运行"""
        logging.info("[PaddleSpeech] 检查并启动容器流程开始...")
        if not self._check_docker_installation():
            logging.error("[PaddleSpeech] _check_docker_installation 返回 False")
            return False
        logging.info("[PaddleSpeech] _check_docker_installation 返回 True，继续检查容器状态...")
        try:
            # 检查容器是否存在
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={self.container_name}'],
                capture_output=True,
                text=True
            )
            logging.info(f"[PaddleSpeech] docker ps -a 输出: {result.stdout}")
            
            if self.container_name not in result.stdout:
                # 容器不存在，创建并启动
                logging.info(f"[PaddleSpeech] 容器 {self.container_name} 不存在，尝试创建并启动...")
                print(f"正在启动 PaddleSpeech Docker 容器...")
                subprocess.run([
                    'docker', 'run', '-d',
                    '--name', self.container_name,
                    '-p', f'{self.port}:8000',
                    'paddlepaddle/paddlespeech:latest'
                ], check=True)
                # 等待容器启动
                time.sleep(10)
                logging.info(f"[PaddleSpeech] 容器 {self.container_name} 已创建并启动，等待10秒...")
            elif 'Up' not in result.stdout:
                # 容器存在但未运行，启动它
                logging.info(f"[PaddleSpeech] 容器 {self.container_name} 存在但未运行，尝试启动...")
                print(f"正在启动已存在的 PaddleSpeech 容器...")
                subprocess.run(['docker', 'start', self.container_name], check=True)
                time.sleep(5)
                logging.info(f"[PaddleSpeech] 容器 {self.container_name} 已启动，等待5秒...")
            else:
                logging.info(f"[PaddleSpeech] 容器 {self.container_name} 已经在运行状态")
            print("PaddleSpeech 容器已就绪")
            logging.info("[PaddleSpeech] PaddleSpeech 容器已就绪")
            return True
        except Exception as e:
            logging.error(f"[PaddleSpeech] Docker 容器管理失败: {str(e)}")
            return False
    
    async def text_to_speech(self, text, lang='zh-cn', output_path=None):
        text = replace_custom_pinyin(text)
        # 如果 Docker 未安装或容器启动失败，使用备选策略
        if not self._check_docker_installation() or not self._ensure_container_running():
            logging.info("使用 Edge-TTS 作为备选策略")
            print("[PaddleSpeech] 使用 Edge-TTS 作为备选策略")
            return await self.fallback_strategy.text_to_speech(text, lang, output_path)
        try:
            hanzi = get_hanzi_from_pinyin(text)
            log1 = f"[PaddleSpeech] 原始输入: {text}"
            log2 = f"[PaddleSpeech] 查到的汉字: {hanzi}"
            if hanzi and hanzi != text:
                tts_text = hanzi
            else:
                tts_text = text
            log3 = f"[PaddleSpeech] 最终送入TTS的文本: {tts_text}"
            logging.info(log1)
            logging.info(log2)
            logging.info(log3)
            print(log1)
            print(log2)
            print(log3)
            data = {
                'text': tts_text,
                'lang': 'zh',
                'am': 'fastspeech2_csmsc',
                'voc': 'hifigan_csmsc',
                'spk_id': 0,
                'speed': 1.0,
                'volume': 1.0,
                'sample_rate': 24000,
                'format': self.audio_format,
                'use_onnx': True,
                'use_gpu': False,
                'use_phn': True,
                'use_lexicon': True
            }
            response = requests.post(
                f'http://localhost:{self.port}/tts',
                json=data,
                headers={'Content-Type': 'application/json'},
                stream=True
            )
            if response.status_code != 200:
                error_msg = f"PaddleSpeech API 返回错误: {response.status_code} - {response.text}"
                logging.error(error_msg)
                print(error_msg)
                raise Exception(error_msg)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                err = "生成的音频文件无效"
                print(err)
                raise Exception(err)
            print(f"成功生成音频文件: {output_path}")
            return True
        except Exception as e:
            logging.error(f"PaddleSpeech Docker 合成失败: {str(e)}")
            print(f"PaddleSpeech Docker 合成失败: {str(e)}")
            logging.info("切换到 Edge-TTS 作为备选策略")
            print("切换到 Edge-TTS 作为备选策略")
            return await self.fallback_strategy.text_to_speech(text, lang, output_path)

# 根据操作系统选择合适的默认策略
def get_default_strategy():
    if platform.system() == 'Darwin':  # macOS
        return MacSayStrategy()
    else:
        return EdgeTTSStrategy()  # 其他系统默认使用 Edge-TTS