import os
import json
import re
import ast
from pypinyin import pinyin, Style

# 合法拼音音节词库（可根据需要扩展）
valid_pinyin_set = set([
    # 单韵母
    'a', 'o', 'e', 'i', 'u', 'ü',
    # 常见音节
    'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 'üe', 'er',
    'an', 'en', 'in', 'un', 'ün', 'ang', 'eng', 'ing', 'ong',
    # 声母+韵母组合
    'ba', 'bai', 'ban', 'bang', 'bao', 'bei', 'ben', 'beng', 'bi', 'bian', 'biao', 'bie', 'bin', 'bing', 'bo', 'bu',
    'ca', 'cai', 'can', 'cang', 'cao', 'ce', 'cen', 'ceng', 'cha', 'chai', 'chan', 'chang', 'chao', 'che', 'chen', 'cheng', 'chi', 'chong', 'chou', 'chu', 'chua', 'chuai', 'chuan', 'chuang', 'chui', 'chun', 'chuo', 'ci', 'cong', 'cou', 'cu', 'cuan', 'cui', 'cun', 'cuo',
    'da', 'dai', 'dan', 'dang', 'dao', 'de', 'dei', 'den', 'deng', 'di', 'dia', 'dian', 'diao', 'die', 'ding', 'diu', 'dong', 'dou', 'du', 'duan', 'dui', 'dun', 'duo',
    'fa', 'fan', 'fang', 'fei', 'fen', 'feng', 'fo', 'fou', 'fu',
    'ga', 'gai', 'gan', 'gang', 'gao', 'ge', 'gei', 'gen', 'geng', 'gong', 'gou', 'gu', 'gua', 'guai', 'guan', 'guang', 'gui', 'gun', 'guo',
    'ha', 'hai', 'han', 'hang', 'hao', 'he', 'hei', 'hen', 'heng', 'hong', 'hou', 'hu', 'hua', 'huai', 'huan', 'huang', 'hui', 'hun', 'huo',
    'ji', 'jia', 'jian', 'jiang', 'jiao', 'jie', 'jin', 'jing', 'jiong', 'jiu', 'ju', 'juan', 'jue', 'jun',
    'ka', 'kai', 'kan', 'kang', 'kao', 'ke', 'ken', 'keng', 'kong', 'kou', 'ku', 'kua', 'kuai', 'kuan', 'kuang', 'kui', 'kun', 'kuo',
    'la', 'lai', 'lan', 'lang', 'lao', 'le', 'lei', 'leng', 'li', 'lia', 'lian', 'liang', 'liao', 'lie', 'lin', 'ling', 'liu', 'lo', 'long', 'lou', 'lu', 'luan', 'lue', 'lun', 'luo', 'lü', 'lüe', 'ma', 'mai', 'man', 'mang', 'mao', 'me', 'mei', 'men', 'meng', 'mi', 'mian', 'miao', 'mie', 'min', 'ming', 'miu', 'mo', 'mou', 'mu',
    'na', 'nai', 'nan', 'nang', 'nao', 'ne', 'nei', 'nen', 'neng', 'ni', 'nian', 'niang', 'niao', 'nie', 'nin', 'ning', 'niu', 'nong', 'nou', 'nu', 'nuan', 'nue', 'nuo', 'nü', 'nüe',
    'o', 'ou',
    'pa', 'pai', 'pan', 'pang', 'pao', 'pei', 'pen', 'peng', 'pi', 'pian', 'piao', 'pie', 'pin', 'ping', 'po', 'pou', 'pu',
    'qi', 'qia', 'qian', 'qiang', 'qiao', 'qie', 'qin', 'qing', 'qiong', 'qiu', 'qu', 'quan', 'que', 'qun',
    'ran', 'rang', 'rao', 're', 'ren', 'reng', 'ri', 'rong', 'rou', 'ru', 'ruan', 'rui', 'run', 'ruo',
    'sa', 'sai', 'san', 'sang', 'sao', 'se', 'sen', 'seng', 'sha', 'shai', 'shan', 'shang', 'shao', 'she', 'shen', 'sheng', 'shi', 'shou', 'shu', 'shua', 'shuai', 'shuan', 'shuang', 'shui', 'shun', 'shuo', 'si', 'song', 'sou', 'su', 'suan', 'sui', 'sun', 'suo',
    'ta', 'tai', 'tan', 'tang', 'tao', 'te', 'teng', 'ti', 'tian', 'tiao', 'tie', 'ting', 'tong', 'tou', 'tu', 'tuan', 'tui', 'tun', 'tuo',
    'wa', 'wai', 'wan', 'wang', 'wei', 'wen', 'weng', 'wo', 'wu',
    'xi', 'xia', 'xian', 'xiang', 'xiao', 'xie', 'xin', 'xing', 'xiong', 'xiu', 'xu', 'xuan', 'xue', 'xun',
    'ya', 'yan', 'yang', 'yao', 'ye', 'yi', 'yin', 'ying', 'yo', 'yong', 'you', 'yu', 'yuan', 'yue', 'yun',
    'za', 'zai', 'zan', 'zang', 'zao', 'ze', 'zei', 'zen', 'zeng', 'zha', 'zhai', 'zhan', 'zhang', 'zhao', 'zhe', 'zhen', 'zheng', 'zhi', 'zhong', 'zhou', 'zhu', 'zhua', 'zhuai', 'zhuan', 'zhuang', 'zhui', 'zhun', 'zhuo', 'zi', 'zong', 'zou', 'zu', 'zuan', 'zui', 'zun', 'zuo',
])

# 拼音到常用汉字的基础映射表（可根据需要补充）
pinyin_to_hanzi = {
    'a': '阿', 'ai': '哎', 'an': '安', 'ang': '昂', 'ao': '奥',
    'ba': '八', 'bai': '白', 'ban': '班', 'bang': '帮', 'bao': '包',
    'bei': '北', 'ben': '本', 'beng': '崩', 'bi': '比', 'bian': '变',
    'biao': '表', 'bie': '别', 'bin': '宾', 'bing': '冰', 'bo': '波', 'bu': '不',
    'ca': '擦', 'cai': '才', 'can': '参', 'cang': '仓', 'cao': '草',
    'ce': '测', 'cen': '岑', 'ceng': '层', 'cha': '查', 'chai': '柴',
    'chan': '产', 'chang': '长', 'chao': '超', 'che': '车', 'chen': '陈',
    'cheng': '成', 'chi': '吃', 'chong': '虫', 'chou': '丑', 'chu': '出',
    'chua': '欻', 'chuai': '揣', 'chuan': '船', 'chuang': '窗', 'chui': '吹',
    'chun': '春', 'chuo': '戳', 'ci': '词', 'cong': '从', 'cou': '凑',
    'cu': '粗', 'cuan': '窜', 'cui': '催', 'cun': '村', 'cuo': '错',
    'da': '大', 'dai': '带', 'dan': '单', 'dang': '当', 'dao': '到',
    'de': '的', 'dei': '得', 'den': '扽', 'deng': '等', 'di': '地',
    'dia': '嗲', 'dian': '点', 'diao': '掉', 'die': '爹', 'ding': '丁',
    'diu': '丢', 'dong': '东', 'dou': '豆', 'du': '都', 'duan': '短',
    'dui': '对', 'dun': '顿', 'duo': '多',
    'e': '鹅', 'ei': '诶', 'en': '恩', 'er': '儿',
    'fa': '发', 'fan': '翻', 'fang': '方', 'fei': '飞', 'fen': '分',
    'feng': '风', 'fo': '佛', 'fou': '否', 'fu': '福',
    'ga': '嘎', 'gai': '该', 'gan': '干', 'gang': '刚', 'gao': '高',
    'ge': '哥', 'gei': '给', 'gen': '根', 'geng': '更', 'gong': '工',
    'gou': '狗', 'gu': '古', 'gua': '瓜', 'guai': '怪', 'guan': '关',
    'guang': '光', 'gui': '归', 'gun': '滚', 'guo': '国',
    'ha': '哈', 'hai': '海', 'han': '汉', 'hang': '航', 'hao': '好',
    'he': '和', 'hei': '黑', 'hen': '很', 'heng': '横', 'hong': '红',
    'hou': '后', 'hu': '湖', 'hua': '花', 'huai': '坏', 'huan': '欢',
    'huang': '黄', 'hui': '会', 'hun': '婚', 'huo': '火',
    'ji': '机', 'jia': '家', 'jian': '间', 'jiang': '江', 'jiao': '交',
    'jie': '接', 'jin': '金', 'jing': '经', 'jiong': '窘', 'jiu': '九',
    'ju': '居', 'juan': '卷', 'jue': '决', 'jun': '军',
    'ka': '卡', 'kai': '开', 'kan': '看', 'kang': '康', 'kao': '考',
    'ke': '可', 'ken': '肯', 'keng': '坑', 'kong': '空', 'kou': '口',
    'ku': '苦', 'kua': '夸', 'kuai': '快', 'kuan': '宽', 'kuang': '狂',
    'kui': '亏', 'kun': '困', 'kuo': '扩',
    'la': '拉', 'lai': '来', 'lan': '蓝', 'lang': '浪', 'lao': '老',
    'le': '了', 'lei': '雷', 'leng': '冷', 'li': '里', 'lia': '俩',
    'lian': '连', 'liang': '两', 'liao': '料', 'lie': '列', 'lin': '林',
    'ling': '零', 'liu': '六', 'long': '龙', 'lou': '楼', 'lu': '路',
    'luan': '乱', 'lun': '论', 'luo': '落', 'lü': '绿', 'lüe': '略',
    'ma': '马', 'mai': '买', 'man': '满', 'mang': '忙', 'mao': '毛',
    'me': '么', 'mei': '没', 'men': '们', 'meng': '梦', 'mi': '米',
    'mian': '面', 'miao': '苗', 'mie': '灭', 'min': '民', 'ming': '明',
    'miu': '谬', 'mo': '模', 'mou': '某', 'mu': '木',
    'na': '那', 'nai': '奶', 'nan': '男', 'nang': '囊', 'nao': '脑',
    'ne': '呢', 'nei': '内', 'nen': '嫩', 'neng': '能', 'ni': '你',
    'nian': '年', 'niang': '娘', 'niao': '鸟', 'nie': '捏', 'nin': '您',
    'ning': '宁', 'niu': '牛', 'nong': '农', 'nou': '耨', 'nu': '努',
    'nuan': '暖', 'nue': '虐', 'nuo': '挪', 'nü': '女', 'nüe': '虐',
    'o': '哦', 'ou': '欧',
    'pa': '怕', 'pai': '排', 'pan': '盘', 'pang': '旁', 'pao': '跑',
    'pei': '配', 'pen': '喷', 'peng': '朋', 'pi': '皮', 'pian': '片',
    'piao': '票', 'pie': '撇', 'pin': '品', 'ping': '平', 'po': '破',
    'pou': '剖', 'pu': '普',
    'qi': '七', 'qia': '恰', 'qian': '千', 'qiang': '强', 'qiao': '桥',
    'qie': '切', 'qin': '亲', 'qing': '青', 'qiong': '穷', 'qiu': '秋',
    'qu': '去', 'quan': '全', 'que': '却', 'qun': '群',
    'ran': '然', 'rang': '让', 'rao': '绕', 're': '热', 'ren': '人',
    'reng': '扔', 'ri': '日', 'rong': '容', 'rou': '肉', 'ru': '如',
    'ruan': '软', 'rui': '瑞', 'run': '润', 'ruo': '若',
    'sa': '撒', 'sai': '赛', 'san': '三', 'sang': '桑', 'sao': '扫',
    'se': '色', 'sen': '森', 'seng': '僧', 'sha': '杀', 'shai': '晒',
    'shan': '山', 'shang': '上', 'shao': '少', 'she': '社', 'shen': '深',
    'sheng': '生', 'shi': '是', 'shou': '手', 'shu': '书', 'shua': '刷',
    'shuai': '帅', 'shuan': '栓', 'shuang': '双', 'shui': '水', 'shun': '顺',
    'shuo': '说', 'si': '四', 'song': '送', 'sou': '搜', 'su': '苏',
    'suan': '算', 'sui': '岁', 'sun': '孙', 'suo': '所',
    'ta': '他', 'tai': '太', 'tan': '谈', 'tang': '糖', 'tao': '套',
    'te': '特', 'teng': '疼', 'ti': '题', 'tian': '天', 'tiao': '条',
    'tie': '铁', 'ting': '听', 'tong': '同', 'tou': '头', 'tu': '图',
    'tuan': '团', 'tui': '推', 'tun': '吞', 'tuo': '脱',
    'wa': '瓦', 'wai': '外', 'wan': '完', 'wang': '网', 'wei': '为',
    'wen': '文', 'weng': '翁', 'wo': '我', 'wu': '五',
    'xi': '西', 'xia': '下', 'xian': '先', 'xiang': '向', 'xiao': '小',
    'xie': '写', 'xin': '新', 'xing': '星', 'xiong': '雄', 'xiu': '修',
    'xu': '许', 'xuan': '选', 'xue': '学', 'xun': '寻',
    'ya': '牙', 'yan': '眼', 'yang': '羊', 'yao': '要', 'ye': '也',
    'yi': '一', 'yin': '音', 'ying': '应', 'yo': '哟', 'yong': '用',
    'you': '有', 'yu': '鱼', 'yuan': '元', 'yue': '月', 'yun': '云',
    'za': '杂', 'zai': '在', 'zan': '咱', 'zang': '脏', 'zao': '早',
    'ze': '则', 'zei': '贼', 'zen': '怎', 'zeng': '增', 'zha': '扎',
    'zhai': '摘', 'zhan': '站', 'zhang': '张', 'zhao': '找', 'zhe': '这',
    'zhen': '真', 'zheng': '正', 'zhi': '只', 'zhong': '中', 'zhou': '周',
    'zhu': '主', 'zhua': '抓', 'zhuai': '拽', 'zhuan': '转', 'zhuang': '装',
    'zhui': '追', 'zhun': '准', 'zhuo': '桌', 'zi': '字', 'zong': '总',
    'zou': '走', 'zu': '组', 'zuan': '钻', 'zui': '最', 'zun': '尊',
    'zuo': '做',
}

# 合并拼音、汉字、带声调拼音为一个变量，格式如 'di 地 dì'
pinyin_hanzi_tone = {}
for py in valid_pinyin_set:
    hanzi = pinyin_to_hanzi.get(py)
    if hanzi:
        try:
            py_tone = pinyin(hanzi, style=Style.TONE, strict=False)[0][0]
            if py_tone != py:
                pinyin_hanzi_tone[py] = f"{py} {hanzi} {py_tone}"
        except Exception:
            pass

# 由 pinyin_hanzi_tone 生成 special_words 和 CUSTOM_PINYIN_MAP
special_words = {}
CUSTOM_PINYIN_MAP = {}
for py, value in pinyin_hanzi_tone.items():
    parts = value.split()
    if len(parts) == 3:
        _, hanzi, py_tone = parts
        special_words[py] = hanzi
        CUSTOM_PINYIN_MAP[py] = py_tone

# 增量合并到 pinyin_map.py（只添加原本不存在的 key）
pinyin_map_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pinyin_map.py'))

def load_dict_from_py(file_path, var_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(rf'{var_name}\s*=\s*{{(.*?)}}', content, re.DOTALL)
    if not match:
        return {}
    dict_str = '{' + match.group(1) + '}'
    return ast.literal_eval(dict_str)

def save_dict_to_py(file_path, var_name, new_dict):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    start = end = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{var_name} = {{'):
            start = i
        elif start is not None and line.strip().startswith('}'):
            end = i
            break
    if start is not None and end is not None:
        new_lines = lines[:start+1]
        for k, v in sorted(new_dict.items()):
            new_lines.append(f"    '{k}': '{v}',\n")
        new_lines.append('}\n')
        new_lines += lines[end+1:]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'已合并并写回 {var_name} 到 {file_path}')
    else:
        print(f'未找到 {var_name}，未写回 {file_path}')

# 读取已有 special_words 和 CUSTOM_PINYIN_MAP
special_words_old = load_dict_from_py(pinyin_map_path, 'special_words')
custom_pinyin_map_old = load_dict_from_py(pinyin_map_path, 'CUSTOM_PINYIN_MAP')

# 只添加原本不存在的 key
special_words_merged = dict(special_words_old)
for k, v in special_words.items():
    if k not in special_words_merged:
        special_words_merged[k] = v
custom_pinyin_map_merged = dict(custom_pinyin_map_old)
for k, v in CUSTOM_PINYIN_MAP.items():
    if k not in custom_pinyin_map_merged:
        custom_pinyin_map_merged[k] = v

print("special_words_merged", special_words_merged)
print("custom_pinyin_map_merged", custom_pinyin_map_merged)

# 写回 pinyin_map.py
save_dict_to_py(pinyin_map_path, 'special_words', special_words_merged)
save_dict_to_py(pinyin_map_path, 'CUSTOM_PINYIN_MAP', custom_pinyin_map_merged)

print('基础拼音词库已增量合并到 pinyin_map.py（仅补充新key，已存在的不变）！') 