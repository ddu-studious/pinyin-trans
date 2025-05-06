from flask import Flask, request, send_from_directory, render_template, jsonify
from gtts import gTTS
import os

# 从独立文件中导入拼音映射
from pinyin_map import pinyin_to_hanzi

app = Flask(__name__)
AUDIO_DIR = 'static/audio'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_audio', methods=['POST'])
def get_audio():
    pinyin = request.form['pinyin']
    hanzi = pinyin_to_hanzi.get(pinyin, pinyin)
    audio_file = f'{pinyin}.mp3'
    audio_path = os.path.join(AUDIO_DIR, audio_file)

    if not os.path.exists(audio_path):
        tts = gTTS(text=hanzi, lang='zh-cn')
        tts.save(audio_path)

    audio_url = f'/audio/{audio_file}'
    return jsonify({'audio_url': audio_url})  # 返回 JSON 格式

@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)