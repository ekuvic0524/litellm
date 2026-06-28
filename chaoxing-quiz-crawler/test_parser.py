"""本地测试解析器"""
import json
import sys
sys.path.insert(0, 'F:/litellm/chaoxing-quiz-crawler')

from parser.question_parser import parse_work_page

with open('F:/litellm/work_task.html', 'r', encoding='utf-8') as f:
    html = f.read()

questions = parse_work_page(html, '第16章 糖类 客观题')
print(f'解析到 {len(questions)} 题\n')

# 输出前5题
for q in questions[:5]:
    print(f'--- 第{q["index"]}题 [{q["type"]}] ---')
    # 清理题目中的HTML实体
    print(f'Q: {q["question"][:100]}')
    if q['options']:
        for opt in q['options']:
            print(f'   {opt[:60]}')
    print(f'A: {q["answer"]}')
    if q['analysis']:
        print(f'解析: {q["analysis"][:60]}')
    if q['images']:
        print(f'图片: {q["images"]}')
    print()

# 统计
type_stats = {}
for q in questions:
    t = q['type']
    type_stats[t] = type_stats.get(t, 0) + 1

print('=== 题型统计 ===')
for t, c in sorted(type_stats.items()):
    print(f'  {t}: {c}题')
print(f'  合计: {sum(type_stats.values())}题')

# 检查带图片的题目
img_questions = [q for q in questions if q.get('images')]
print(f'\n含有图片的题目: {len(img_questions)}')
for q in img_questions[:3]:
    print(f'  第{q["index"]}题: {q["images"]}')
