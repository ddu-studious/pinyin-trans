# tts_strategies.py

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
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)  # 保存音频文件到指定路径
        return output_path

# 默认策略设置为 gTTS
DEFAULT_TTS_STRATEGY = GTTSStrategy()