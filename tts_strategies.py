import os
import subprocess
import asyncio
from gtts import gTTS
import edge_tts  # 新增导入 Microsoft Edge TTS 库

class TTSStrategy:
    """
    TTS 策略抽象类，所有具体的 TTS 类都需要实现这个接口。
    """
    def text_to_speech(self, text: str, lang: str, output_path: str):
        """
        将文本转换为语音音频文件。
        
        参数:
            text (str): 要转换成语音的文本。
            lang (str): 文本的语言代码。
            output_path (str): 音频文件保存路径。
        """
        raise NotImplementedError("Subclasses should implement this!")

class GTTSStrategy(TTSStrategy):
    """
    使用 gTTS 的具体策略实现。
    """
    def text_to_speech(self, text: str, lang: str, output_path: str):
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)  # 保存音频文件到指定路径
        return output_path

    @property
    def name(self):
        return 'gtts'  # 提供模型名称用于日志

class MacSayStrategy(TTSStrategy):
    """
    macOS 原生 say 命令策略。
    """
    def text_to_speech(self, text: str, lang: str, output_path: str):
        # 使用临时 aiff 文件再转换为 wav
        temp_aiff = output_path.replace('.wav', '.aiff')

        # 根据语言选择合适的语音
        if lang.startswith('zh'):
            voice_name = 'Tingting'  # 系统中唯一支持的中文语音
        else:
            voice_name = 'Samantha'  # 默认英文语音

        # 先生成 .aiff 音频
        cmd_aiff = ['say', '-v', voice_name, '-o', temp_aiff, text]
        try:
            subprocess.run(cmd_aiff, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"生成 AIFF 失败: {e.stderr}")
            raise

        # 使用 afconvert 将 .aiff 转换为 .wav
        cmd_wav = ['afconvert', '-f', 'WAVE', '-d', 'LEI16', temp_aiff, output_path]
        try:
            subprocess.run(cmd_wav, check=True, capture_output=True, text=True)
            os.remove(temp_aiff)  # 删除临时文件
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"转换音频格式失败: {e.stderr}")
            raise RuntimeError(f"语音合成失败，请检查系统语音设置") from e

    @property
    def name(self):
        return 'macsay'  # 提供模型名称用于日志

class EdgeTTSStrategy(TTSStrategy):
    """
    使用 Microsoft Edge TTS 的策略实现
    """

    def __init__(self, voice='zh-CN-XiaoxiaoNeural'):
        self.voice = voice

    async def text_to_speech(self, text: str, lang: str, output_path: str):
        try:
            from edge_tts import Communicate
            print(f"[EdgeTTSStrategy] 正在尝试合成语音: 文本='{text}', 语言='{lang}', 输出路径='{output_path}'")  # 添加详细调试信息
            
            if not text or text.strip() == "":
                raise ValueError("文本内容为空，无法合成语音")

            communicate = Communicate(text=text, voice=self.voice)
            await communicate.save(output_path)
            print(f"[EdgeTTSStrategy] 音频文件已成功保存到: {output_path}")  # 添加成功保存提示
            return output_path
        except Exception as e:
            print(f"[EdgeTTSStrategy] 合成失败: {str(e)}")  # 更清晰的错误输出
            raise

    @property
    def name(self):
        return 'edgetts'  # 提供模型名称用于日志

# 默认策略设置为 gTTS
DEFAULT_TTS_STRATEGY = GTTSStrategy()