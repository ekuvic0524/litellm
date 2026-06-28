"""检查第一二章的图片字段"""
import json

d = json.load(open('chaoxing-quiz-crawler/output/questions.json', 'r', encoding='utf-8'))

for ch_name in ['第一章', '第2章']:
    ch_qs = [q for q in d if ch_name in q.get('sourceChapter', '')]
    has_img = [q for q in ch_qs if q.get('images') and len(q.get('images', [])) > 0]
    print(f'{ch_name}: {len(ch_qs)}题, {len(has_img)}题有图')
    for q in has_img[:3]:
        raw = q['images'][0]
        print(f'  第{q["index"]}题 images[0] type={type(raw).__name__}: {str(raw)[:100]}')
