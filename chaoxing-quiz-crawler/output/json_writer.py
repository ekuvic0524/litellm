"""JSON输出模块"""
import json
import os


def write_questions_json(all_questions, filepath):
    """
    将所有题目写入JSON文件。

    Args:
        all_questions: list[dict] 所有题目
        filepath: 输出文件路径
    """
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f'[JSON] 已写入 {len(all_questions)} 题到 {filepath}')


def write_checkpoint(processed_titles, filepath):
    """写入断点续采信息"""
    data = {'processed': list(processed_titles)}
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_checkpoint(filepath):
    """读取断点续采信息"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('processed', []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
