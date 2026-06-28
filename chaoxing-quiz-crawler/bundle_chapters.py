"""
按章节整理、下载图片、打包ZIP
用法:
  python bundle_chapters.py               # 从第一章开始处理，完成后暂停
  python bundle_chapters.py --chapter N   # 从指定章节开始
  python bundle_chapters.py --all          # 处理所有章节（不暂停）
"""
import os
import sys
import json
import hashlib
import zipfile
import re
import time
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import COOKIE

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
JSON_PATH = os.path.join(OUTPUT_DIR, 'questions.json')
ERROR_LOG = os.path.join(OUTPUT_DIR, 'error.log')
IMAGE_CACHE = os.path.join(OUTPUT_DIR, '.image_cache')


def _make_session():
    session = requests.Session()
    for item in COOKIE.split('; '):
        if '=' in item:
            k, v = item.split('=', 1)
            session.cookies.set(k, v)
    session.headers.update({
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'),
    })
    return session


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


def download_image(session, url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200 and len(r.content) > 100:
                return r.content, None
            return None, f'HTTP {r.status_code}, size={len(r.content)}'
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1)
                continue
            return None, str(e)


def extract_url(img):
    """从任意格式中提取图片URL字符串"""
    if isinstance(img, str):
        return img
    if isinstance(img, dict):
        src = img.get('source') or img.get('url') or ''
        if isinstance(src, dict):
            return extract_url(src)
        return src
    return str(img)


def log_error(msg):
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {msg}\n')
    print(f'  [ERROR] {msg}')


def get_global_image(content):
    """将图片存入全局缓存（单份），返回 (hash, ext)"""
    os.makedirs(IMAGE_CACHE, exist_ok=True)
    h = sha256_of(content)
    ext_map = {
        b'\xff\xd8\xff': '.jpg',
        b'\x89PNG': '.png',
        b'GIF8': '.gif',
        b'RIFF': '.webp',
    }
    ext = '.gif'
    for sig, e in ext_map.items():
        if content[:len(sig)] == sig:
            ext = e
            break
    fname = f'{h}{ext}'
    dest = os.path.join(IMAGE_CACHE, fname)
    if not os.path.exists(dest):
        with open(dest, 'wb') as f:
            f.write(content)
    return h, ext


CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
           '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18}


def chapter_number(title):
    m = re.search(r'第\s*(\d+)\s*章', title)
    if m:
        return int(m.group(1))
    m = re.search(r'第\s*([一二三四五六七八九十]+)\s*章', title)
    if m:
        return CN_NUM.get(m.group(1), 99)
    return 99


def process_chapter(chapter_title, questions, session):
    m = chapter_number(chapter_title)
    chapter_num = str(m).zfill(2) if m else '00'
    chapter_dir = f'chapter{chapter_num}'
    chapter_path = os.path.join(OUTPUT_DIR, chapter_dir)
    images_dir = os.path.join(chapter_path, 'images')
    os.makedirs(images_dir, exist_ok=True)

    total = len(questions)
    img_questions = 0
    download_ok = 0
    download_fail = 0
    total_img_count = 0
    updated_questions = []

    for q in questions:
        raw_images = q.get('images', [])
        old_urls = [extract_url(img) for img in raw_images if extract_url(img)]
        orig_count = len(old_urls)
        old_urls = list(dict.fromkeys(old_urls))

        if not old_urls:
            q['hasImage'] = False
            q['imageCount'] = 0
            q['images'] = []
            updated_questions.append(q)
            continue

        img_questions += 1
        new_images = []
        for img_url in old_urls:
            content, err = download_image(session, img_url)
            if content:
                h, ext = get_global_image(content)
                cache_src = os.path.join(IMAGE_CACHE, f'{h}{ext}')
                local_fname = f'{h}{ext}'
                local_dest = os.path.join(images_dir, local_fname)
                if not os.path.exists(local_dest):
                    try:
                        os.link(cache_src, local_dest)
                    except (OSError, AttributeError):
                        import shutil
                        shutil.copy2(cache_src, local_dest)
                download_ok += 1
                new_images.append({
                    'local': f'images/{local_fname}',
                    'source': img_url,
                })
            else:
                download_fail += 1
                log_error(f'下载失败 [{chapter_title}] {img_url}: {err}')
                new_images.append({
                    'local': '',
                    'source': img_url,
                    'error': err,
                })

        q['hasImage'] = True
        q['imageCount'] = orig_count
        total_img_count += orig_count
        q['images'] = new_images
        updated_questions.append(q)

    chapter_json_path = os.path.join(chapter_path, f'{chapter_dir}.json')
    with open(chapter_json_path, 'w', encoding='utf-8') as f:
        json.dump(updated_questions, f, ensure_ascii=False, indent=2)

    zip_name = f'{chapter_dir}_bundle.zip'
    zip_path = os.path.join(OUTPUT_DIR, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(chapter_json_path, f'{chapter_dir}.json')
        if os.path.isdir(images_dir):
            for fn in sorted(os.listdir(images_dir)):
                fp = os.path.join(images_dir, fn)
                if os.path.isfile(fp):
                    zf.write(fp, f'images/{fn}')

    report = OrderedDict([
        ('章节', chapter_title),
        ('目录', chapter_dir),
        ('总题数', total),
        ('图片题数', img_questions),
        ('图片总数', total_img_count),
        ('下载成功', download_ok),
        ('下载失败', download_fail),
        ('ZIP路径', os.path.relpath(zip_path, OUTPUT_DIR)),
    ])
    return report, updated_questions


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)

    chapter_groups = OrderedDict()
    for q in all_questions:
        ch = q.get('sourceChapter', '未知章节')
        if ch not in chapter_groups:
            chapter_groups[ch] = []
        chapter_groups[ch].append(q)

    start_chapter = 1
    run_all = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--all':
            run_all = True
        elif args[i] == '--chapter' and i + 1 < len(args):
            start_chapter = int(args[i + 1])
            i += 1
        elif args[i].startswith('--chapter='):
            start_chapter = int(args[i].split('=')[1])
        i += 1

    chapter_list = list(chapter_groups.items())

    def sort_key(item):
        return chapter_number(item[0])
    chapter_list.sort(key=sort_key)

    total_chapters = len(chapter_list)
    all_urls = sum(len(q.get('images', [])) for q in all_questions)
    print(f'共 {total_chapters} 个章节，{len(all_questions)} 题，{all_urls} 张图\n')

    with open(ERROR_LOG, 'w', encoding='utf-8') as f:
        f.write('')

    session = _make_session()

    start_idx = 0
    if not run_all and start_chapter > 1:
        for idx, (title, _) in enumerate(chapter_list):
            if chapter_number(title) >= start_chapter:
                start_idx = idx
                break

    for idx, (ch_title, ch_questions) in enumerate(chapter_list):
        if idx < start_idx:
            continue

        print(f'\n{"="*60}')
        print(f'[{idx+1}/{total_chapters}] 处理: {ch_title}')
        print(f'{"="*60}')

        try:
            report, updated = process_chapter(ch_title, ch_questions, session)
        except Exception as e:
            log_error(f'章节处理失败 [{ch_title}]: {e}')
            print(f'  [失败] {e}')
            continue

        print(f'\n--- 完成报告 ---')
        for k, v in report.items():
            print(f'  {k}: {v}')

        for orig_q, new_q in zip(ch_questions, updated):
            for key, val in new_q.items():
                orig_q[key] = val

        if not run_all:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(all_questions, f, ensure_ascii=False, indent=2)
            next_ch = ''
            for n_title, _ in chapter_list[idx+1:idx+2]:
                if chapter_number(n_title):
                    next_ch = str(chapter_number(n_title))
            print(f'\n{"="*60}')
            print(f'第{chapter_number(ch_title)}章 处理完成 ✓')
            if next_ch:
                print(f'继续下一章: python bundle_chapters.py --chapter={next_ch}')
                print(f'全部处理:   python bundle_chapters.py --all')
            print(f'{"="*60}')
            break

    if run_all:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        print(f'\n全部完成！已更新 {JSON_PATH}')


if __name__ == '__main__':
    main()
