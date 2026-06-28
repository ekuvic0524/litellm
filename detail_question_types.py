"""详细查看各题型结构，包括填空题和判断题"""
import re

with open('work_task.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 找填空题区域
fill_start = html.find('二. 填空题')
if fill_start > 0:
    # 找到这一整段，直到下一个题型
    next_type = html.find('<h2 class="type_tit"', fill_start + 1)
    if next_type < 0:
        next_type = html.find('</div><!--', fill_start)
    segment = html[fill_start:next_type] if next_type > 0 else html[fill_start:fill_start+5000]

    # 提取填空题的第一个题目
    qli = re.search(r'(<div class="marBom60 questionLi singleQuesId"[^>]*>[\s\S]{0,2000}?</div>)\s*<!--', segment)
    if qli:
        print('=== 填空题第一个题目 ===')
        print(qli.group(1))

    # 提取填空题的第二个题目（如果有）
    qli2 = re.findall(r'<div class="marBom60 questionLi singleQuesId"[^>]*>[\s\S]{0,2000}?</div>', segment)
    if len(qli2) >= 2:
        print(f'\n\n=== 填空题第二个题目 ===')
        print(qli2[1])

# 找判断题区域
judge_start = html.find('四. 判断题')
if judge_start > 0:
    next_type = html.find('<h2 class="type_tit"', judge_start + 1)
    segment = html[judge_start:next_type] if next_type > 0 else html[judge_start:judge_start+5000]

    qli_judge = re.search(r'(<div class="marBom60 questionLi singleQuesId"[^>]*>[\s\S]{0,2000}?</div>)\s*<!--', segment)
    if qli_judge:
        print(f'\n\n=== 判断题第一个题目 ===')
        print(qli_judge.group(1))
