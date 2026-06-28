"""Markdown输出模块"""
import os


def write_questions_md(all_questions, filepath):
    """
    将所有题目写入Markdown文件（便于人工阅读）。

    Args:
        all_questions: list[dict] 所有题目
        filepath: 输出文件路径
    """
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('# 有机化学 客观题题库\n\n')
        f.write(f'> 共 {len(all_questions)} 题\n\n')
        f.write('---\n\n')

        # 按章节分组
        chapters = {}
        for q in all_questions:
            ch = q.get('sourceChapter', q.get('chapter', '未知章节'))
            chapters.setdefault(ch, []).append(q)

        for ch_title, qs in chapters.items():
            f.write(f'## {ch_title}（{len(qs)}题）\n\n')

            for q in qs:
                f.write(f'### {q["index"]}. [{q["type"]}] {q["question"]}\n\n')

                if q['options']:
                    for opt in q['options']:
                        f.write(f'- {opt}\n')
                    f.write('\n')

                f.write(f'**答案：** {q["answer"]}\n\n')

                if q.get('analysis'):
                    f.write(f'**解析：** {q["analysis"]}\n\n')

                if q.get('images'):
                    for img in q['images']:
                        f.write(f'![图片]({img})\n\n')

                f.write('---\n\n')

    print(f'[MD] 已写入 {len(all_questions)} 题到 {filepath}')
