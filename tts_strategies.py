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

class PaddleSpeechTTSStrategy(TTSStrategy):
    """
    使用 PaddleSpeech 的策略实现
    """
    def __init__(self, voice='zh-CN', model_path=None):
        self.voice = voice
        self.model_path = model_path if model_path else os.getenv('PADDLE_SPEECH_MODEL_PATH')
        self._initialized = False
        self._model = None
        # 显式声明支持的语音模型
        self.supported_voices = {
            'zh-CN': 'zh_CN',  # 更新为正确的模型标识符
            'en-US': 'en_US'
        }
        
        # 设置环境变量禁用PaddleSpeech自动下载
        models_home = os.path.dirname(os.path.dirname(self.model_path)) if self.model_path else os.getcwd()
        os.environ['PRETRAINED_MODELS_HOME'] = models_home
        os.environ['PPNLP_HOME'] = models_home
        os.environ['PADDLESPEECH_HOME'] = models_home
        # 添加禁用自动下载的环境变量
        os.environ['PADDLESPEECH_DISABLE_DOWNLOAD'] = '1'
        os.environ['PPNLP_DISABLE_DOWNLOAD'] = '1'
        
        # 设置 G2P 模型路径
        g2p_zip_path = os.path.join(models_home, 'paddlespeech', 'G2PWModel_1.1.zip')
        g2p_model_dir = os.path.join(models_home, 'paddlespeech', 'G2PWModel')
        
        # 如果模型目录不存在，尝试下载并解压
        if not os.path.exists(g2p_model_dir):
            print(f"[PaddleSpeech] G2P模型目录不存在，尝试下载...")
            import requests
            import hashlib
            
            # 使用新的 CDN URL
            g2p_url = 'https://paddlespeech.cdn.bcebos.com/Parakeet/released_models/g2p/new/G2PWModel_1.1.zip'
            expected_md5 = 'f8b60501770bff92ed6ce90860a610e6'
            
            try:
                # 下载文件
                print(f"[PaddleSpeech] 正在从 {g2p_url} 下载模型...")
                print(f"[PaddleSpeech] 下载目标路径: {g2p_zip_path}")
                
                response = requests.get(g2p_url, stream=True)
                response.raise_for_status()
                
                # 获取文件大小用于显示进度
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024  # 1 KB
                downloaded = 0
                
                # 显示下载进度
                print("[PaddleSpeech] 下载进度:")
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        downloaded += len(chunk)
                        progress = int(50 * downloaded / total_size)
                        print(f"\r[{'=' * progress}{' ' * (50-progress)}] {downloaded}/{total_size} bytes", end='')
                print("\n[PaddleSpeech] 下载完成")
                
                # 保存文件
                with open(g2p_zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 验证 MD5
                with open(g2p_zip_path, 'rb') as f:
                    file_md5 = hashlib.md5(f.read()).hexdigest()
                
                if file_md5 != expected_md5:
                    raise ValueError(f"MD5校验失败: 期望 {expected_md5}, 实际 {file_md5}")
                
                print(f"[PaddleSpeech] 模型下载完成，正在解压...")
                import zipfile
                with zipfile.ZipFile(g2p_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.path.dirname(g2p_model_dir))
                print(f"[PaddleSpeech] G2P模型解压完成")
                
            except Exception as e:
                print(f"[PaddleSpeech] 模型下载或解压失败: {str(e)}")
                raise
        
        # 设置解压后的模型路径
        os.environ['G2P_MODEL_PATH'] = g2p_model_dir
        
        # 打印环境变量设置情况
        print(f"[PaddleSpeech] 设置模型目录: {models_home}")
        print(f"[PaddleSpeech] 本地模型路径: {self.model_path}")
        print(f"[PaddleSpeech] G2P模型目录: {g2p_model_dir}")
        print(f"[PaddleSpeech] G2P模型目录存在: {os.path.exists(g2p_model_dir)}")
        print(f"[PaddleSpeech] 禁用自动下载: {os.environ.get('PADDLESPEECH_DISABLE_DOWNLOAD')}")

    def _initialize_model(self):
        """延迟加载模型以提高启动速度"""
        try:
            # 检查NumPy版本兼容性
            import numpy as np
            numpy_version = np.__version__
            print(f"[PaddleSpeech] 当前NumPy版本: {numpy_version}")
            
            # 尝试导入PaddleSpeech
            try:
                # 更新导入路径，适配 PaddleSpeech 1.4.1/1.4.2
                from paddlespeech.cli.tts.infer import TTSExecutor
                from paddlespeech.resource import pretrained_models
                
                # 直接修改 PaddleSpeech 的模型配置
                g2p_model_dir = os.environ.get('G2P_MODEL_PATH')
                if hasattr(pretrained_models, 'G2PWModel'):
                    # 修改模型配置，使用本地路径
                    pretrained_models.G2PWModel = {
                        '1.1': {
                            'url': g2p_model_dir,  # 使用本地路径
                            'md5': 'f8b60501770bff92ed6ce90860a610e6',
                        }
                    }
                    print(f"[PaddleSpeech] 设置G2P模型路径: {g2p_model_dir}")
                
                # 禁用自动下载
                if hasattr(pretrained_models, 'download_and_decompress'):
                    def no_download(*args, **kwargs):
                        raise RuntimeError("自动下载已被禁用，请使用本地模型")
                    pretrained_models.download_and_decompress = no_download
                
                self._model = TTSExecutor()
                print("[PaddleSpeech] 模型初始化成功")
                self._initialized = True
            except ImportError as e:
                if "Numba needs NumPy" in str(e):
                    error_msg = f"NumPy版本不兼容: {str(e)}，请考虑使用其他TTS引擎"
                else:
                    error_msg = "PaddleSpeech模块导入失败: " + str(e)
                print(f"[ERROR] {error_msg}")
                raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"PaddleSpeech模型初始化异常: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise

    def text_to_speech(self, text: str, lang: str, output_path: str):
        if not self._initialized:
            self._initialize_model()
            
        try:
            # 更新 API 调用方式，适配 PaddleSpeech 1.4.1
            lang_code = 'zh' if lang.startswith('zh') else 'en'
            result = self._model(
                text=text,
                output=output_path,
                am='fastspeech2_csmsc' if lang_code == 'zh' else 'fastspeech2_ljspeech',
                voc='hifigan_csmsc' if lang_code == 'zh' else 'hifigan_ljspeech'
            )
            print(f"[PaddleSpeech] 音频文件已成功保存到: {output_path}")
            return output_path
        except Exception as e:
            print(f"[PaddleSpeech] 合成失败: {str(e)}")
            raise

    @property
    def name(self):
        return 'paddlespeech'  # 提供模型名称用于日志

# 默认策略设置为 gTTS
DEFAULT_TTS_STRATEGY = GTTSStrategy()