import re
import os
import json
import ast

def remove_pinyin_tones_and_normalize(pinyin_with_tones):
    """Removes tone marks from a Pinyin string and normalizes 'ü' to 'v'."""
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
        'ü': 'v' 
    }
    normalized_pinyin = ""
    for char_py in pinyin_with_tones:
        normalized_pinyin += tone_map.get(char_py, char_py)
    # Remove any characters that are not basic Latin letters
    cleaned_pinyin = re.sub(r'[^a-zA-Z]', '', normalized_pinyin)
    return cleaned_pinyin

# 手动转录的文本数据（可替换为实际 OCR/文本数据）
transcribed_texts_combined = """
天 tiān 地 dì 人 rén 你 nǐ 我 wǒ 他 tā
一 yī 二 èr 三 sān 四 sì 五 wǔ 上 shàng 下 xià
口 kǒu 耳 ěr 目 mù 手 shǒu 足 zú 站 zhàn 坐 zuò
日 rì 月 yuè 水 shuǐ 火 huǒ 山 shān 石 shí 田 tián 禾 hé
对 duì 云 yún 雨 yǔ 风 fēng 花 huā 鸟 niǎo 虫 chóng
六 liù 七 qī 八 bā 九 jiǔ 十 shí
爸 bà 妈 mā
马 mǎ 土 tǔ 不 bù
画 huà 打 dǎ
棋 qí 鸡 jī
字 zì 词 cí 语 yǔ 句 jù 子 zǐ
桌 zhuō 纸 zhǐ
文 wén 数 shù 学 xué 音 yīn 乐 yuè
妹 mèi 奶 nǎi
小 xiǎo 桥 qiáo 台 tái
雪 xuě 儿 ér
白 bái 草 cǎo 家 jiā 是 shì
车 chē 路 lù 灯 dēng 走 zǒu
秋 qiū 气 qì 了 le 树 shù 叶 yè 片 piàn 大 dà 飞 fēi 会 huì 个 gè
的 de 船 chuán 两 liǎng 头 tóu 云 yún 里 lǐ 看 kàn 见 jiàn 闪 shǎn 星 xīng
江 jiāng 南 nán 可 kě 采 cǎi 莲 lián 鱼 yú 东 dōng 西 xī 北 běi
尖 jiān 说 shuō 春 chūn 青 qīng 蛙 wā 夏 xià 弯 wān 皮 pí 地 de 冬 dōng
男 nán 女 nǚ 开 kāi 关 guān 正 zhèng 反 fǎn
远 yuǎn 有 yǒu 色 sè 近 jìn 听 tīng 无 wú 声 shēng 去 qù 还 hái 来 lái
多 duō 少 shǎo 黄 huáng 牛 niú 羊 yáng 只 zhī 猫 māo 边 biān 狗 gǒu 苹 píng 果 guǒ 杏 xìng 桃 táo
书 shū 包 bāo 尺 chǐ 作 zuò 业 yè 本 běn 笔 bǐ 刀 dāo 课 kè 早 zǎo 校 xiào
明 míng 力 lì 尘 chén 从 cóng 双 shuāng 木 mù 林 lín 森 sēn 条 tiáo 心 xīn
升 shēng 国 guó 旗 qí 中 zhōng 红 hóng 歌 gē 起 qǐ 么 me 美 měi 丽 lì 立 lì
午 wǔ 晚 wǎn 昨 zuó 今 jīn 年 nián
影 yǐng 前 qián 后 hòu 黑 hēi 狗 gǒu 左 zuǒ 右 yòu 它 tā 好 hǎo 朋 péng 友 yǒu
比 bǐ 尾 wěi 巴 ba 谁 shuí 长 cháng 短 duǎn 把 bǎ 伞 sǎn 猴 hóu 最 zuì 公 gōng
写 xiě 诗 shī 点 diǎn 要 yào 过 guò 当 dāng 事 shì 们 men 以 yǐ 成 chéng
数 shǔ 色 cǎi 半 bàn 空 kōng 问 wèn 到 dào 方 fāng 没 méi 更 gèng 绿 lǜ 出 chū 长 zhǎng
睡 shuì 那 nà 海 hǎi 真 zhēn 老 lǎo 师 shī 吗 ma 同 tóng 什 shén 才 cái 亮 liàng
蓝 lán 又 yòu 笑 xiào 着 zhe 向 xiàng 和 hé 贝 bèi 鞋 xié 挂 guà 活 huó 全 quán
哥 gē 弟 dì 姐 jiě 叔 shū 爷 yé
群 qún 竹 zhú 牙 yá 用 yòng 几 jǐ 步 bù 为 wèi 参 cān 加 jiā 洞 dòng 着 zhe
鸟 niǎo 鸡 jī 鸭 yā 处 chù 找 zhǎo 办 bàn 法 fǎ 放 fàng 高 gāo
住 zhù 孩 hái 玩 wán 吧 ba 发 fā 芽 yá 草 cǎo 房 fáng 飘 piāo 回 huí 全 quán 变 biàn
工 gōng 厂 chǎng 医 yī 院 yuàn 生 shēng
一 yī 二 èr 三 sān 上 shàng
口 kǒu 目 mù 耳 ěr 手 shǒu
日 rì 田 tián 禾 hé 火 huǒ
虫 chóng 云 yún 山 shān
八 bā 十 shí
了 le 子 zǐ 人 rén 大 dà
月 yuè 儿 ér 头 tóu 里 lǐ
可 kě 东 dōng 西 xī
天 tiān 四 sì 是 shì
女 nǚ 开 kāi
水 shuǐ 去 qù 来 lái 不 bù
小 xiǎo 少 shǎo 牛 niú 果 guǒ 鸟 niǎo
早 zǎo 刀 dāo 尺 chǐ 本 běn
木 mù 林 lín 土 tǔ 力 lì 心 xīn
中 zhōng 五 wǔ 立 lì 正 zhèng
在 zài 后 hòu 我 wǒ 好 hǎo
长 cháng 比 bǐ 巴 ba 把 bǎ
下 xià 个 gè 雨 yǔ 们 men
问 wèn 有 yǒu 半 bàn 从 cóng 你 nǐ
才 cái 明 míng 同 tóng 学 xué
自 zì 己 jǐ 门 mén 衣 yī
白 bái 的 de 又 yòu 和 hé
竹 zhú 牙 yá 马 mǎ 用 yòng 几 jǐ
只 zhī 石 shí 出 chū 见 jiàn
对 duì 妈 mā 全 quán 回 huí
工 gōng 厂 chǎng
"""

special_words = {}

lines = transcribed_texts_combined.strip().split('\n')
for line in lines:
    parts = line.strip().split()
    if not parts:
        continue
    i = 0
    while i < len(parts) - 1:
        character_token = parts[i]
        pinyin_token = parts[i+1]
        is_valid_char = len(character_token) == 1 and '\u4e00' <= character_token[0] <= '\u9fff'
        is_valid_pinyin_start = pinyin_token and pinyin_token[0].islower()
        if is_valid_char and is_valid_pinyin_start:
            pinyin_no_tone = remove_pinyin_tones_and_normalize(pinyin_token)
            if pinyin_no_tone:
                special_words[pinyin_no_tone] = character_token
            i += 2
        else:
            i += 1

# 输出 special_words 到 json
output_dir = os.path.dirname(__file__)
with open(os.path.join(output_dir, 'special_words.json'), 'w', encoding='utf-8') as f:
    json.dump(special_words, f, ensure_ascii=False, indent=2)
print('已生成 special_words.json')

# 生成 CUSTOM_PINYIN_MAP
CUSTOM_PINYIN_MAP = {}
for py, hanzi in special_words.items():
    # 保留原始拼音和带声调拼音
    CUSTOM_PINYIN_MAP[py] = py  # 默认无声调
    # 如果有声调，替换为带声调
    # 这里假设原始 pinyin_token 就是带声调的
    # 实际可用 pypinyin 进一步处理

# 用 pypinyin 生成带声调拼音
try:
    from pypinyin import pinyin, Style
    for py, hanzi in special_words.items():
        py_tone = pinyin(hanzi, style=Style.TONE, strict=False)[0][0]
        CUSTOM_PINYIN_MAP[py] = py_tone
except ImportError:
    print('未安装 pypinyin，CUSTOM_PINYIN_MAP 只保留无声调拼音')

with open(os.path.join(output_dir, 'custom_pinyin_map.json'), 'w', encoding='utf-8') as f:
    json.dump(CUSTOM_PINYIN_MAP, f, ensure_ascii=False, indent=2)
print('已生成 custom_pinyin_map.json')

# === 自动同步 special_words 到 pinyin_map.py ===
# 修正路径
output_dir = os.path.dirname(__file__)
_map_path = os.path.abspath(os.path.join(output_dir, 'pinyin_map.py'))

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

# 1. 读取已有 special_words 和 CUSTOM_PINYIN_MAP
pinyin_map_path = _map_path
special_words_old = load_dict_from_py(pinyin_map_path, 'special_words')
custom_pinyin_map_old = load_dict_from_py(pinyin_map_path, 'CUSTOM_PINYIN_MAP')

# 2. 合并并去重
special_words_merged = {**special_words_old, **special_words}  # 新的覆盖旧的
custom_pinyin_map_merged = {**custom_pinyin_map_old}

try:
    from pypinyin import pinyin, Style
    for py, hanzi in special_words_merged.items():
        py_tone = pinyin(hanzi, style=Style.TONE, strict=False)[0][0]
        custom_pinyin_map_merged[py] = py_tone
except ImportError:
    for py in special_words_merged:
        custom_pinyin_map_merged[py] = py

# 3. 写回 pinyin_map.py
save_dict_to_py(pinyin_map_path, 'special_words', special_words_merged)
save_dict_to_py(pinyin_map_path, 'CUSTOM_PINYIN_MAP', custom_pinyin_map_merged) 