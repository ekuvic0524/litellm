"""作业列表与题目页面采集器"""
import os
import sys
import time
import re
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    COOKIE, COURSE_ID, CLASS_ID, CPI, WORK_ENC,
    WORK_LIST_URL, WORK_TASK_URL, MAX_RETRIES, RETRY_DELAY
)


def _make_session():
    session = requests.Session()
    for item in COOKIE.split('; '):
        if '=' in item:
            k, v = item.split('=', 1)
            session.cookies.set(k, v)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    return session


def fetch_work_list():
    """获取作业列表，返回 [{title, status, url}]"""
    session = _make_session()
    params = {
        'courseId': COURSE_ID,
        'classId': CLASS_ID,
        'cpi': CPI,
        'enc': WORK_ENC,
        'v': '2',
    }
    r = session.get(WORK_LIST_URL, params=params, timeout=15)
    r.encoding = 'utf-8'

    if '无权限' in r.text or r.status_code != 200:
        raise RuntimeError(f'获取作业列表失败: 无权限或状态码 {r.status_code}')

    works = []
    for m in re.finditer(
        r'data="([^"]*)"[^>]*aria-label="([^"]*)"[^>]*>',
        r.text
    ):
        task_url = m.group(1)
        aria_label = m.group(2)
        parts = [p.strip() for p in aria_label.split(';')]
        title = parts[0] if parts else ''
        status = parts[1] if len(parts) > 1 else ''
        works.append({'title': title, 'status': status, 'url': task_url})

    return works


def fetch_work_task(url):
    """获取单个作业的题目页面HTML"""
    session = _make_session()
    session.headers.update({
        'Accept': 'text/html,*/*',
        'Referer': f'{WORK_LIST_URL}?courseId={COURSE_ID}&classId={CLASS_ID}&cpi={CPI}',
    })

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code == 200 and '无权限' not in r.text:
                return r.text
            raise RuntimeError(f'状态码 {r.status_code}, 含无权限标记')
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
            continue

    raise RuntimeError(f'获取作业失败(重试{MAX_RETRIES}次): {last_err}')
