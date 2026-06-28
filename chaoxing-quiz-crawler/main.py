"""
学习通有机化学 客观题题库采集器
============================
工作流：
  1. 获取作业列表（所有章节客观题）
  2. 逐个下载作业页面
  3. 解析HTML提取题目
  4. 输出 questions.json + questions.md
  5. 支持断点续采、错误重试

用法：
  python main.py              # 全量采集
  python main.py --force      # 忽略checkpoint，重新采集所有
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.work_crawler import fetch_work_list, fetch_work_task
from parser.question_parser import parse_work_page
from output.json_writer import (
    write_questions_json, write_checkpoint, read_checkpoint
)
from output.md_writer import write_questions_md
from config import OUTPUT_DIR


def main(force=False):
    checkpoint_path = os.path.join(OUTPUT_DIR, 'checkpoint.json')
    json_path = os.path.join(OUTPUT_DIR, 'questions.json')
    md_path = os.path.join(OUTPUT_DIR, 'questions.md')

    # 读取断点
    processed = set() if force else read_checkpoint(checkpoint_path)

    # ---- Step 1: 获取作业列表 ----
    print('=' * 60)
    print('Step 1: 获取作业列表')
    print('=' * 60)
    works = fetch_work_list()
    works = [w for w in works if '客观题' in w['title']]
    print(f'找到 {len(works)} 个客观题作业\n')

    if not works:
        print('没有找到任何客观题作业，退出。')
        return

    for w in works:
        print(f'  [{w["status"]}] {w["title"]}')

    to_process = [w for w in works if w['title'] not in processed]
    print(f'\n已处理: {len(processed)}, 待处理: {len(to_process)}')

    # 加载已有数据
    all_questions = []
    if not force and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            print(f'已加载 {len(all_questions)} 条已有数据')
        except Exception:
            all_questions = []

    # ---- Step 2-3: 逐个下载 & 解析 ----
    print('\n' + '=' * 60)
    print('Step 2-3: 下载作业 & 解析题目')
    print('=' * 60)

    for i, work in enumerate(to_process):
        title = work['title']
        url = work['url']

        print(f'\n[{i + 1}/{len(to_process)}] {title} ({work["status"]})')

        try:
            html = fetch_work_task(url)
        except Exception as e:
            print(f'  [失败] 下载失败: {e}')
            continue

        print(f'  页面大小: {len(html)} bytes')

        try:
            questions = parse_work_page(html, title)
        except Exception as e:
            print(f'  [失败] 解析失败: {e}')
            continue

        print(f'  解析到 {len(questions)} 题')

        if not questions:
            print('  [警告] 未解析到任何题目，跳过')
            continue

        all_questions.extend(questions)
        processed.add(title)

        write_checkpoint(processed, checkpoint_path)
        write_questions_json(all_questions, json_path)

        if i < len(to_process) - 1:
            time.sleep(1)

    # ---- Step 4: 输出 ----
    print('\n' + '=' * 60)
    print('Step 4: 输出结果')
    print('=' * 60)

    if all_questions:
        all_questions.sort(key=lambda q: (q.get('sourceChapter', ''), q.get('index', 0)))
        write_questions_json(all_questions, json_path)
        write_questions_md(all_questions, md_path)

        type_stats = {}
        for q in all_questions:
            t = q.get('type', '未知')
            type_stats[t] = type_stats.get(t, 0) + 1

        print(f'\n=== 题型统计 ===')
        for t, c in sorted(type_stats.items()):
            print(f'  {t}: {c}题')
        print(f'  合计: {sum(type_stats.values())}题')
    else:
        print('没有采集到任何题目。')

    print('\n完成！')


if __name__ == '__main__':
    force = '--force' in sys.argv
    main(force=force)
