"""分析各章节纯文本题 vs 图片题分布"""
import json

with open('chaoxing-quiz-crawler/output/questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

from collections import OrderedDict
import re

CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
           '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18}

def chapter_number(title):
    m = re.search(r'第\s*(\d+)\s*章', title)
    if m: return int(m.group(1))
    m = re.search(r'第\s*([一二三四五六七八九十]+)\s*章', title)
    if m: return CN_NUM.get(m.group(1), 99)
    return 99

groups = OrderedDict()
for q in data:
    ch = q.get('sourceChapter', '未知')
    if ch not in groups: groups[ch] = []
    groups[ch].append(q)

sorted_ch = sorted(groups.items(), key=lambda x: chapter_number(x[0]))

for ch_title, qs in sorted_ch:
    total = len(qs)
    has_img = sum(1 for q in qs if q.get('hasImage') or q.get('images'))
    text_only = total - has_img
    short_opts = sum(1 for q in qs if q.get('options') and any(
        len(o.strip().rstrip('.')) <= 2 for o in q['options']
    ))
    print(f'{ch_title:30s}  {total:3d}题  纯文本:{text_only:2d}  有图:{has_img:2d}  选项过短(疑似纯图):{short_opts:2d}')
