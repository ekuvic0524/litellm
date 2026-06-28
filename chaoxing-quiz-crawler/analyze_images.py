"""分析图片分布"""
import json
from collections import Counter

with open('chaoxing-quiz-crawler/output/questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chapters = Counter(q['sourceChapter'] for q in data)
print('=== 章节分布 ===')
for ch, cnt in chapters.most_common():
    img_q = sum(1 for q in data if q['sourceChapter'] == ch and q.get('images'))
    total_imgs = sum(len(q.get('images', [])) for q in data if q['sourceChapter'] == ch)
    print(f'{ch}: {cnt}题, {img_q}题含图, {total_imgs}张图')

print(f'\n总计: {len(data)}题')
print(f'含图题: {sum(1 for q in data if q.get("images"))}')
print(f'图片总数: {sum(len(q.get("images", [])) for q in data)}')
