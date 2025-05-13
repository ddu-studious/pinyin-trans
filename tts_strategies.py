import os
import subprocess
import asyncio
from gtts import gTTS
import edge_tts  # 新增导入 Microsoft Edge TTS 库
import logging  # 确保日志模块可用
from logging import Filter
import nltk
import ssl

# 解决 NLTK SSL 证书验证失败问题
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 下载 NLTK 数据（使用本地证书）
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('cmudict', quiet=True)


class ModelLogFilter(Filter):
    """自定义日志过滤器，拦截unknown模型日志"""
    def filter(self, record):
        if getattr(record, 'model', None) == 'unknown':
            return False
        return True

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

# 新增PaddleSpeech支持
try:
    import paddle
    from paddlespeech.cli.tts.infer import TTSExecutor
    from paddlespeech.t2s.models.transformer_tts import TransformerTTSExecutor
    
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
            
except ImportError as e:
    if 'paddlespeech' in str(e):
        class PaddleSpeechStrategy(TTSStrategy):
            """
            占位类，当PaddleSpeech未安装时返回提示
            """
            def text_to_speech(self, text: str, lang: str, output_path: str):
                raise NotImplementedError(
                    "PaddleSpeech未安装，请先运行: pip install paddlepaddle paddlespeech")
    else:
        raise

def setup_logger_filters():
    """
    配置日志过滤器以控制输出
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 为所有处理器添加模型过滤器
    for handler in root_logger.handlers:
        handler.addFilter(ModelLogFilter())
        
    # 设置日志级别
    root_logger.setLevel(logging.INFO)
    return True

# 初始化TTS策略（保持原有函数定义）
def init_tts_strategies(app):
    """
    初始化所有TTS策略
    """
    global tts_strategies, DEFAULT_TTS_STRATEGY
    
    # 初始化策略字典
    tts_strategies = {
        'gtts': GTTSStrategy(),
        'macsay': MacSayStrategy(),
        'edgetts': EdgeTTSStrategy()
    }
    
    # 尝试加载PaddleSpeech支持
    try:
        from paddlespeech_strategies import PaddleSpeechStrategy
        tts_strategies['paddlespeech'] = PaddleSpeechStrategy()
    except (ImportError, NotImplementedError) as e:
        print("PaddleSpeech不可用:", str(e))
        
    # 设置默认策略
    DEFAULT_TTS_STRATEGY = tts_strategies.get('gtts', GTTSStrategy())
    
    # 注册日志过滤器
    try:
        setup_logger_filters()
    except Exception as e:
        print("日志过滤器初始化失败:", str(e))
    
    return True

# 默认策略设置为 gTTS
DEFAULT_TTS_STRATEGY = GTTSStrategy()