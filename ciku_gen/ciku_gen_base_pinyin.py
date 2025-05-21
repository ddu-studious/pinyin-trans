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

# 生成基础 special_words 映射
special_words = {}
for py in valid_pinyin_set:
    # 用拼音首字母对应的常用汉字或占位符
    if py == 'ü' or py == 'v':
        hanzi = '玉'
    elif py == 'i':
        hanzi = '衣'
    elif py == 'u':
        hanzi = '乌'
    elif py == 'a':
        hanzi = '阿'
    elif py == 'e':
        hanzi = '鹅'
    elif py == 'o':
        hanzi = '哦'
    else:
        hanzi = py
    special_words[py] = hanzi

# 生成 CUSTOM_PINYIN_MAP（带声调）
CUSTOM_PINYIN_MAP = {}
for py, hanzi in special_words.items():
    try:
        py_tone = pinyin(hanzi, style=Style.TONE, strict=False)[0][0]
        CUSTOM_PINYIN_MAP[py] = py_tone
    except Exception:
        CUSTOM_PINYIN_MAP[py] = py

# 增量合并到 pinyin_map.py
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

# 合并并去重
special_words_merged = {**special_words_old, **special_words}  # 新的覆盖旧的
custom_pinyin_map_merged = {**custom_pinyin_map_old, **CUSTOM_PINYIN_MAP}

# 写回 pinyin_map.py
save_dict_to_py(pinyin_map_path, 'special_words', special_words_merged)
save_dict_to_py(pinyin_map_path, 'CUSTOM_PINYIN_MAP', custom_pinyin_map_merged)

print('基础拼音词库已增量合并到 pinyin_map.py，可用于丰富拼音校验和发音！') 