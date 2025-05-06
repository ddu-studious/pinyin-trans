from flask import Flask, request, send_from_directory, render_template, jsonify
from gtts import gTTS
import os

app = Flask(__name__)
AUDIO_DIR = 'static/audio'

# 声母映射
initials = {
    'b': '波',
    'p': '坡',
    'm': '么',
    'f': '佛',
    'd': '的',
    't': '特',
    'n': '呢',
    'l': '了',
    'g': '哥',
    'k': '科',
    'h': '喝',
    'j': '鸡',
    'q': '七',
    'x': '西',
    'zh': '知',
    'ch': '吃',
    'sh': '诗',
    'r': '日',
    'z': '资',
    'c': '刺',
    's': '思',
    'y': '衣',
    'w': '屋',
}

# 韵母映射（按拼音标准顺序排列）
finals = {
    # 单韵母
    'a': '啊',
    'o': '哦',
    'e': '饿',
    'i': '一',
    'u': '乌',
    'v': '愚',

    # 复韵母
    'ai': '挨',
    'ei': '诶',
    'ui': '威',
    'ao': '奥',
    'ou': '欧',
    'iu': '优',
    'ie': '也',
    've': '约',

    # 鼻韵母
    'an': '安',
    'en': '恩',
    'in': '因',
    'un': '温',
    'vn': '晕',  # 实际中写作 ün

    'ang': '昂',
    'eng': '鞥',
    'ing': '英',
    'ong': '翁',

    # 特殊韵母
    'er': '儿',

    # 带 i 的组合
    'ia': '呀',
    'ian': '烟',
    'iang': '央',
    'iao': '要',
    'iong': '拥',
    'iu': '优',

    # 带 u 的组合
    'ua': '蛙',
    'uai': '歪',
    'uan': '弯',
    'uang': '王',
    'ue': '约',
    'uo': '窝',
    'van': '冤',
}

# 整体认读音节
whole_readings = {
    'chi': '吃',
    'shi': '师',
    'ri': '日',
    'zi': '资',
    'ci': '佌',
    'si': '丝',
    'yi': '一',
    'wu': '屋',
    'yu': '愚',
    'ye': '椰',
    'yue': '约',
    'yuan': '渊',
    'ying': '英',
}

# 特殊字的读音
special_words = {
    'an': '安',
    'ba': '把',
    'bai': '百',
    'bao': '抱',
    'bei': '贝',
    'bi': '笔',
    'bian': '边',
    'cai': '采',
    'cao': '草',
    'ce': '册',
    'chan': '产',
    'chang': '唱',
    'che': '车',
    'chi': '池',
    'chuang': '床',
    'chui': '吹',
    'chun': '春',
    'cong': '从',
    'cun': '寸',
    'da': '打',
    'dang': '当',
    'dao': '到',
    'de': '的',
    'deng': '灯',
    'di': '地',
    'dian': '点',
    'ding': '丁',
    'dong': '动',
    'dou': '都',
    'dui': '对',
    'duo': '朵',
    'fang': '放',
    'fei': '飞',
    'fen': '分',
    'fu': '父',
    'gan': '赶',
    'gao': '高',
    'gong': '共',
    'gu': '故',
    'gua': '瓜',
    'guang': '广',
    'guo': '过',
    'hai': '还',
    'hao': '好',
    'he': '河',
    'hong': '红',
    'hou': '后',
    'hu': '户',
    'hua': '画',
    'huan': '欢',
    'hui': '回',
    'ji': '机',
    'jia': '家',
    'jian': '尖',
    'jiang': '讲',
    'jiao': '交',
    'jie': '节',
    'jin': '巾',
    'jing': '京',
    'jiu': '久',
    'ka': '卡',
    'kan': '看',
    'ke': '课',
    'kong': '空',
    'kuai': '快',
    'lao': '老',
    'le': '乐',
    'lei': '泪',
    'lin': '林',
    'mao': '毛',
    'me': '么',
    'mei': '没',
    'men': '们',
    'mi': '米',
    'mian': '面',
    'miao': '苗',
    'ming': '明',
    'pa': '怕',
    'pao': '跑',
    'pi': '皮',
    'pian': '片',
    'ping': '平',
    'qi': '气',
    'qian': '前',
    'qing': '请',
    'rang': '让',
    'ren': '认',
    'rou': '肉',
    'ru': '入',
    'san': '伞',
    'se': '色',
    'sha': '沙',
    'shen': '身',
    'sheng': '生',
    'shi': '时',
    'shou': '首',
    'shu': '书',
    'shuang': '双',
    'shuo': '说',
    'si': '思',
    'ta': '她',
    'tai': '台',
    'ting': '听',
    'tu': '兔',
    'wan': '玩',
    'wang': '往',
    'wei': '为',
    'wen': '问',
    'wu': '物',
    'xi': '洗',
    'xia': '吓',
    'xiang': '向',
    'xiao': '笑',
    'xie': '写',
    'xing': '行',
    'xue': '学',
    'yan': '眼',
    'yang': '样',
    'ye': '页',
    'yi': '义',
    'yu': '鱼',
    'yuan': '远',
    'yun': '运',
    'zai': '再',
    'zao': '早',
    'zhan': '站',
    'zhao': '找',
    'zhe': '着',
    'zhi': '知',
    'zhu': '住',
    'zi': '自',
    'zou': '走',
    'zu': '足',
    'zuo': '坐'
}

# 合并所有映射
pinyin_to_hanzi = {
    **initials,
    **finals,
    **whole_readings,
    **special_words,
}

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