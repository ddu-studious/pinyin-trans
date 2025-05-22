from flask import Flask, request, send_from_directory, render_template, jsonify, send_file
import os
import platform
import logging
import pwd  # 获取当前用户信息
import asyncio
from ciku_gen.pinyin_map import has_valid_pinyin_value

# 全局定义音频目录
AUDIO_DIR = 'static/audio'

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
    from tts_strategies import (
        GTTSStrategy, 
        MacSayStrategy, 
        EdgeTTSStrategy, 
        DockerPaddleSpeechStrategy,
        get_default_strategy
    )

    # 创建 TTS 策略实例
    try:
        # 初始化基本策略
        tts_strategies = {
            'gtts': GTTSStrategy(),
            'macsay': MacSayStrategy(),
            'edgetts': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural', rate='-60%', volume='+20%'),
            'edgetts_normal': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural', rate='+10%', volume='+50%'),
            'paddlespeech': DockerPaddleSpeechStrategy(audio_format='wav')  # 默认使用 wav 格式
        }
        
        # 设置默认策略
        default_strategy = get_default_strategy()
        print(f"使用默认TTS策略: {default_strategy.name}")
        
    except Exception as e:
        print(f"初始化 TTS 策略时出错: {str(e)}")
        tts_strategies = {
            'gtts': GTTSStrategy(),
            'macsay': MacSayStrategy(),
            'edgetts': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural'),
            'edgetts_normal': EdgeTTSStrategy(voice='zh-CN-XiaoxiaoNeural', rate='+10%', volume='+50%')
        }
        default_strategy = GTTSStrategy()

    # 记录上一次生成的音频文件
    last_audio_url = None

    # 特殊韵母自动映射
    special_pinyin_map = {
        'i': 'yi',
        'u': 'wu',
        'v': 'yu',
    }

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/get_audio', methods=['POST'])
    async def get_audio():
        global last_audio_url
        pinyin = request.form['pinyin']
        hanzi = pinyin_to_hanzi.get(pinyin, pinyin)
        # === 拼音有效性校验 ===
        if not has_valid_pinyin_value(pinyin):
            return jsonify({'error': f'拼音"{pinyin}"无有效发音映射，请输入完整拼音音节或检查词库。'}), 400
        tts_engine = request.form.get('tts', default_strategy.name).lower()
        model_name = tts_engine if tts_engine != 'unknown' else default_strategy.name
        strategy = tts_strategies.get(tts_engine, default_strategy)
        if tts_engine == 'macsay':
            audio_file = f'{pinyin}.wav'
        elif tts_engine == 'edgetts':
            audio_file = f'{pinyin}.mp3'
        elif tts_engine == 'paddlespeech':
            audio_format = getattr(strategy, 'audio_format', 'wav')
            audio_file = f'{pinyin}.{audio_format}'
        else:
            audio_file = f'{pinyin}.mp3'
        audio_path = os.path.join(AUDIO_DIR, audio_file)
        # === 缓存逻辑：如果音频已存在直接返回 ===
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            audio_url = f'/audio/{audio_file}'
            last_audio_url = audio_url
            model_name = getattr(strategy, 'name', tts_engine)
            logger.info(f'缓存命中: {pinyin} -> {model_name}', extra={'model': model_name})
            return jsonify({'audio_url': audio_url})
        # === 生成音频 ===
        try:
            model_name = getattr(strategy, 'name', tts_engine)
            print(f"正在使用 {model_name} 合成语音: '{hanzi}'")
            # 特殊韵母自动映射
            tts_input = special_pinyin_map.get(pinyin, hanzi)
            if tts_engine == 'paddlespeech':
                tts_input = replace_custom_pinyin(tts_input)
            success = await strategy.text_to_speech(text=tts_input, lang='zh-cn', output_path=audio_path)
            if not success:
                raise Exception("语音合成失败")
        except Exception as e:
            print(f"音频合成错误: {str(e)}")
            return jsonify({'error': f'音频合成失败: {str(e)}'}), 500
        audio_url = f'/audio/{audio_file}'
        last_audio_url = audio_url
        model_name = getattr(strategy, 'name', tts_engine)
        logger.info(f'请求生成音频: {pinyin} -> {model_name}', extra={'model': model_name})
        return jsonify({'audio_url': audio_url})

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

    @app.route('/stream_audio', methods=['POST'])
    async def stream_audio():
        global last_audio_url
        pinyin = request.form['pinyin']
        hanzi = pinyin_to_hanzi.get(pinyin, pinyin)
        print(f"pinyin: {pinyin}, hanzi: {hanzi}")
        # === 拼音有效性校验 ===
        if not has_valid_pinyin_value(pinyin):
            return jsonify({'error': f'拼音"{pinyin}"无有效发音映射，请输入完整拼音音节或检查词库。'}), 400
        tts_engine = request.form.get('tts', default_strategy.name).lower()
        strategy = tts_strategies.get(tts_engine, default_strategy)
        if tts_engine == 'macsay':
            audio_file = f'{pinyin}.wav'
        elif tts_engine == 'edgetts':
            audio_file = f'{pinyin}.mp3'
        elif tts_engine == 'paddlespeech':
            audio_format = getattr(strategy, 'audio_format', 'wav')
            audio_file = f'{pinyin}.{audio_format}'
        else:
            audio_file = f'{pinyin}.mp3'
        audio_path = os.path.join(AUDIO_DIR, audio_file)
        # === 缓存逻辑：如果音频已存在直接返回 ===
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            last_audio_url = f'/audio/{audio_file}'
            return send_file(
                audio_path,
                mimetype='audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg',
                as_attachment=False,
                download_name=audio_file
            )
        # === 生成音频 ===
        # 特殊韵母自动映射
        tts_input = special_pinyin_map.get(pinyin, hanzi)
        if tts_engine == 'paddlespeech':
            tts_input = replace_custom_pinyin(tts_input)
        try:
            success = await strategy.text_to_speech(text=tts_input, lang='zh-cn', output_path=audio_path)
            if not success:
                raise Exception("语音合成失败")
            last_audio_url = f'/audio/{audio_file}'
            return send_file(
                audio_path,
                mimetype='audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg',
                as_attachment=False,
                download_name=audio_file
            )
        except Exception as e:
            print(f"音频流生成错误: {str(e)}")
            return jsonify({'error': f'音频生成失败: {str(e)}'}), 500

    @app.route('/stream_chinese_audio', methods=['POST'])
    async def stream_chinese_audio():
        global last_audio_url
        text = request.form['text']  # 接收中文文本
        tts_engine = request.form.get('tts', default_strategy.name).lower()
        strategy = tts_strategies.get(tts_engine+'_normal', default_strategy)

        # 根据不同引擎设置音频文件格式
        if tts_engine == 'macsay':
            audio_format = 'wav'
        elif tts_engine == 'paddlespeech':
            audio_format = getattr(strategy, 'audio_format', 'wav')
        else:
            audio_format = 'mp3'

        # 使用文本的前10个字符（如果不足10个字符则使用全部）作为文件名
        text_prefix = text[:10]
        audio_file = f'{text_prefix}_{tts_engine}.{audio_format}'
        audio_path = os.path.join(AUDIO_DIR, audio_file)

        # === 缓存逻辑：如果音频已存在直接返回 ===
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            last_audio_url = f'/audio/{audio_file}'
            return send_file(
                audio_path,
                mimetype='audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg',
                as_attachment=False,
                download_name=audio_file
            )

        # === 生成音频 ===
        try:
            success = await strategy.text_to_speech(text=text, lang='zh-cn', output_path=audio_path)
            if not success:
                raise Exception("语音合成失败")
            last_audio_url = f'/audio/{audio_file}'
            return send_file(
                audio_path,
                mimetype='audio/wav' if audio_file.endswith('.wav') else 'audio/mpeg',
                as_attachment=False,
                download_name=audio_file
            )
        except Exception as e:
            print(f"音频流生成错误: {str(e)}")
            return jsonify({'error': f'音频生成失败: {str(e)}'}), 500

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
from ciku_gen.pinyin_map import pinyin_to_hanzi
# 导入自动替换函数
from ciku_gen.pinyin_map import replace_custom_pinyin

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

if __name__ == '__main__':
    # 确保应用实例正确运行
    app_instance = create_app()
    app_instance.run(debug=True, port=5000)
