from flask import Flask, request, send_from_directory, render_template, jsonify
import os
import platform
import logging
import pwd  # 获取当前用户信息
import asyncio

# 全局定义音频目录
AUDIO_DIR = 'static/audio'

# 定义默认TTS策略
DEFAULT_TTS_STRATEGY = 'gtts'  # 设置默认TTS策略为gtts

# 确保音频目录存在
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_current_user():
    return pwd.getpwuid(os.getuid()).pw_name

# 创建日志过滤器来拦截unknown模型日志
class ModelLogFilter(logging.Filter):
    def filter(self, record):
        # 增强调试信息输出
        if getattr(record, 'model', None) == 'unknown':
            print(f"[DEBUG] 阻止打印unknown日志，来源: {record.name}:{record.lineno}")
            return False
        return True

# 设置日志格式
class TTSLogFormatter(logging.Formatter):
    def format(self, record):
        # 强制移除所有'model'属性并设置默认值
        if not hasattr(record, 'model'):
            record.model = 'unknown'
        
        # 清理特殊属性防止格式化错误
        if record.model == 'unknown':
            record.model = ''  # 设置为空字符串避免显示
        
        try:
            return super().format(record)
        except ValueError as e:
            if 'model' in str(e):
                return record.getMessage()
            raise

formatter = TTSLogFormatter('[%(asctime)s] 使用模型: %(model)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.addFilter(ModelLogFilter())  # 添加过滤器

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def create_app():
    app = Flask(__name__)
    global AUDIO_DIR

    # 导入 TTS 策略模块
    from tts_strategies import GTTSStrategy, MacSayStrategy, EdgeTTSStrategy

    # 创建 TTS 策略实例
    try:
        tts_strategies = {
            'gtts': GTTSStrategy(),
            'macsay': MacSayStrategy(),
            'edgetts': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural')  # 使用有效的中文语音模型
        }
    except Exception as e:
        print(f"初始化 TTS 策略时出错: {str(e)}")
        tts_strategies = {
            'gtts': GTTSStrategy(),
            'macsay': MacSayStrategy(),
            'edgetts': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural')  # 使用默认中文语音模型
        }

    # 记录上一次生成的音频文件
    last_audio_url = None

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/get_audio', methods=['POST'])
    async def get_audio():
        global last_audio_url
        pinyin = request.form['pinyin']
        hanzi = pinyin_to_hanzi.get(pinyin, pinyin)
        
        # 获取用户选择的 TTS 引擎，默认为 gtts
        tts_engine = request.form.get('tts', 'gtts').lower()
        
        # 显式设置当前模型名称
        model_name = tts_engine if tts_engine != 'unknown' else 'gtts'
        
        strategy = tts_strategies.get(tts_engine, DEFAULT_TTS_STRATEGY)
        
        # 修改音频文件扩展名为 .wav（macsay 使用 wav 格式）
        if tts_engine == 'macsay':
            audio_file = f'{pinyin}.wav'
        elif tts_engine == 'edgetts':
            audio_file = f'{pinyin}.mp3'  # Edge-TTS 默认输出 mp3
        else:
            audio_file = f'{pinyin}.mp3'  # 默认使用 mp3

        audio_path = os.path.join(AUDIO_DIR, audio_file)

        if not os.path.exists(audio_path):
            # 使用策略模式生成音频
            try:
                model_name = getattr(strategy, 'name', tts_engine)
                print(f"正在使用 {model_name} 合成语音: '{hanzi}'")  # 添加调试信息
                if asyncio.iscoroutinefunction(strategy.text_to_speech):
                    await strategy.text_to_speech(text=hanzi, lang='zh-cn', output_path=audio_path)
                else:
                    strategy.text_to_speech(text=hanzi, lang='zh-cn', output_path=audio_path)
            except Exception as e:
                print(f"音频合成错误: {str(e)}")
                return jsonify({'error': f'音频合成失败: {str(e)}'}), 500

        audio_url = f'/audio/{audio_file}'
        last_audio_url = audio_url
        
        # 记录 TTS 模型使用情况
        model_name = getattr(strategy, 'name', tts_engine)
        logger.info(f'请求生成音频: {pinyin} -> {model_name}', extra={'model': model_name})

        return jsonify({'audio_url': audio_url})  # 返回 JSON 格式

    @app.route('/play_last_audio')
    def play_last_audio():
        global last_audio_url
        if last_audio_url:
            # 记录播放上次音频时使用的模型
            logger.info('播放上次音频', extra={'model': 'last_playback'})
            return jsonify({'audio_url': last_audio_url})
        else:
            return jsonify({'error': '没有可播放的音频'}), 400

    @app.route('/audio/<filename>')
    def audio(filename):
        # 记录播放具体音频时使用的模型（从文件名中提取）
        model_name = filename.split('_')[0] if '_' in filename else 'unknown'
        logger.info(f'播放音频: {filename}', extra={'model': model_name})
        return send_from_directory(AUDIO_DIR, filename)

    return app

# 创建Flask应用实例（必须在日志配置之前）
app = Flask(__name__)

# 配置日志系统
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器并设置级别
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器并应用过滤器
formatter = TTSLogFormatter('[%(asctime)s] 使用模型: %(model)s')
console_handler.setFormatter(formatter)
console_handler.addFilter(ModelLogFilter())

# 添加处理器到记录器
logger.addHandler(console_handler)

# 将Flask日志与自定义配置整合
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.disabled = True
app.logger = logger  # 将Flask内置日志替换为自定义配置

# 添加调试信息
print(f"当前运行用户: {get_current_user()}")
print(f"当前工作目录: {os.getcwd()}")
print(f"音频输出目录: {AUDIO_DIR}")
print(f"音频输出目录状态: {'可写' if os.access(AUDIO_DIR, os.W_OK) else '不可写'}")

# 设置全局日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG)

# 完全禁用werkzeug日志
logging.getLogger('werkzeug').disabled = True

# 完全重构日志系统配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器并设置级别
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器并应用过滤器
formatter = TTSLogFormatter('[%(asctime)s] 使用模型: %(model)s')
console_handler.setFormatter(formatter)
console_handler.addFilter(ModelLogFilter())

# 添加处理器到记录器
logger.addHandler(console_handler)

# 替换全局日志配置
logging.getLogger().handlers = [console_handler]
logging.getLogger().setLevel(logging.INFO)

# 导入拼音映射
from pinyin_map import pinyin_to_hanzi

# 设置日志格式
class TTSLogFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'model'):
            record.model = 'unknown'
        return super().format(record)

# 临时修改日志格式包含更多调试信息
formatter = TTSLogFormatter('[%(asctime)s] 使用模型: %(model)s [%(name)s:%(lineno)d]')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 确保所有日志记录器都应用过滤器
for handler in logging.getLogger().handlers:
    handler.addFilter(ModelLogFilter())

# 可选：写入日志文件
# file_handler = logging.FileHandler('tts_usage.log')
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)

if __name__ == '__main__':
    # 确保应用实例正确运行
    app_instance = create_app()
    app_instance.run(debug=True, port=5000)
