import os
import paddle
from paddlespeech.cli.tts.infer import TTSExecutor
from tts_strategies import TTSStrategy

class PaddleSpeechStrategy(TTSStrategy):
    """
    使用百度PaddleSpeech的本地TTS策略
    """
    def __init__(self, voice='zh-CN', model='fastspeech2'):
        self.tts_executor = TTSExecutor()
        self.voice = voice
        self.model = model
        
    def text_to_speech(self, text: str, lang: str, output_path: str):
        # 自动调整语言设置
        actual_lang = lang if lang.startswith('zh') else 'en-US'
        
        # 执行语音合成
        self.tts_executor(
            text=text,
            output=output_path,
            am=self.model,  # 使用指定的模型
            spk_id=0,
            lang=actual_lang,
            speed=1.0,
            volume=1.0,
            sample_rate=24000,
            save_audio=True,
            save_endpoint=None
        )
        return output_path
        
    @property
    def name(self):
        return 'paddlespeech'