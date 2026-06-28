"""深度分析章节页面内嵌JS中的工作/题目逻辑"""
import re
import json

with open('chapter_study.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 找到所有内嵌脚本
scripts = re.findall(r'<script[^>]*>([\s\S]{100,}?)</script>', html)
scripts.sort(key=len, reverse=True)
main_script = scripts[0]

print('=== 搜索工作/题目/测验等关键词 ===')
keywords = ['work', 'exam', 'quiz', 'question', 'job', 'topic', '选择', '判断', '填空',
            'practice', 'exercise', 'test', 'homework', 'TiMu', 'WorkId', 'JobId',
            'QuestionId', 'workId', 'jobId', 'questionId', 'homeworkId']

for kw in keywords:
    positions = [m.start() for m in re.finditer(kw, main_script, re.IGNORECASE)]
    if positions:
        print(f'\n--- "{kw}" ({len(positions)}次) ---')
        for pos in positions[:5]:
            context = main_script[max(0,pos-50):pos+100]
            print(f'  ...{context}...')

print('\n\n=== 搜索mainid内容加载逻辑 ===')
# 找mainid或main相关的代码
main_refs = re.finditer(r'[^.]main[^.\'\"]{0,20}', main_script)
for m in main_refs:
    ctx = main_script[max(0,m.start()-30):m.end()+80]
    if 'main' in ctx:
        print(f'  ...{ctx}...')

print('\n\n=== 搜索iframe/embed/frame相关 ===')
frame_refs = re.finditer(r'(?:iframe|frame|embed|contentFrame)', main_script)
for m in frame_refs:
    ctx = main_script[max(0,m.start()-50):m.end()+100]
    print(f'  ...{ctx}...')

# 找ajax URL拼接模式
print('\n\n=== 搜索URL拼接模式 ===')
url_patterns = re.finditer(r'(?:url|path|link|src)\s*[\+:=]\s*[\'"]([^\'"]*)[\'"]', main_script)
for m in url_patterns:
    ctx = main_script[max(0,m.start()-60):m.end()+120]
    print(f'  ...{ctx}...')
