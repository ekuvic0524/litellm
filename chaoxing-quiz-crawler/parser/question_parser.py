"""题目HTML解析器：解析作业页面中的单选题、多选题、判断题、填空题"""
import re


def parse_work_page(html, chapter_title):
    """
    解析单个作业页面，返回题目列表。

    Args:
        html: 作业页面的HTML字符串
        chapter_title: 章节标题（如"第16章 糖类 客观题"）

    Returns:
        list[dict]: 题目字典列表
    """
    questions = []
    # 按题型分割页面
    sections = re.split(r'(<h2 class="type_tit"[^>]*>[^<]+</h2>)', html)

    current_type = ''
    for i, part in enumerate(sections):
        # 检查是否是题型标题
        type_match = re.search(
            r'<h2 class="type_tit"[^>]*>([^<]+)</h2>',
            part
        )
        if type_match:
            current_type = _normalize_type(type_match.group(1))
            continue

        # 跳过无内容段
        if 'questionLi singleQuesId' not in part:
            continue

        # 提取该题型下所有题目
        q_blocks = re.findall(
            r'<div class="marBom60 questionLi singleQuesId"[^>]*>'
            r'([\s\S]{0,5000}?)</div>\s*<!--',
            part
        )
        # fallback: 如果没有找到<!--结尾，尝试其他结尾方式
        if not q_blocks:
            q_blocks = re.findall(
                r'(<div class="marBom60 questionLi singleQuesId"[^>]*>'
                r'[\s\S]{0,5000}?</div>)',
                part
            )

        for q_html in q_blocks:
            q = _parse_single_question(q_html, current_type, chapter_title)
            if q:
                questions.append(q)

    return questions


def _normalize_type(type_str):
    """标准化题型名称"""
    type_str = re.sub(r'<[^>]+>', '', type_str).strip()
    if '单选' in type_str:
        return '单选题'
    if '多选' in type_str:
        return '多选题'
    if '判断' in type_str:
        return '判断题'
    if '填空' in type_str:
        return '填空题'
    if '简答' in type_str or '问答' in type_str:
        return '简答题'
    return type_str


def _parse_single_question(q_html, default_type, chapter_title):
    """解析单个题目HTML"""
    # 1) 提取题号
    index = 0
    idx_match = re.search(
        r'<h3[^>]*>\s*(\d+)\s*\.',
        q_html
    )
    if idx_match:
        index = int(idx_match.group(1))

    # 2) 提取题型
    q_type = default_type
    type_match = re.search(
        r'<span class="colorShallow"[^>]*>\((\w+)\)</span>',
        q_html
    )
    if type_match:
        parsed = type_match.group(1)
        if '单选' in parsed:
            q_type = '单选题'
        elif '多选' in parsed:
            q_type = '多选题'
        elif '判断' in parsed:
            q_type = '判断题'
        elif '填空' in parsed:
            q_type = '填空题'

    # 3) 提取题目内容（保留图片）
    question_text = ''
    text_match = re.search(
        r'<span class="qtContent workTextWrap">([\s\S]{0,1000}?)</span>',
        q_html
    )
    if text_match:
        question_text = text_match.group(1).strip()

    # 提取题目中的图片
    images = _extract_images(q_html)

    # 4) 提取选项
    options = []
    opt_matches = re.findall(
        r'<li[^>]*>([\s\S]{0,500}?)</li>',
        q_html
    )
    for opt_html in opt_matches:
        opt_text = _clean_html(opt_html)
        opt_text = re.sub(r'\s+', ' ', opt_text).strip()
        if opt_text:
            options.append(opt_text)

    # 5) 提取答案
    answer = ''
    analysis = ''

    # a) 从 stuAnswerContent 提取答案
    ans_match = re.search(
        r'stuAnswerContent[^>]*>([^<]+)',
        q_html
    )
    if ans_match:
        answer = ans_match.group(1).strip()

    # b) 填空题答案在 answer_span stuAnswerContent
    fill_match = re.search(
        r'answer_span[^>]*>[\s\S]{0,200}?<p>([\s\S]{0,200}?)</p>',
        q_html
    )
    if fill_match:
        answer = _clean_html(fill_match.group(1)).strip()

    # c) 从 element-invisible-hidden 提取解析
    analysis_match = re.search(
        r'element-invisible-hidden[^>]*>\s*-\s*([^<]+)',
        q_html
    )
    if analysis_match:
        analysis = analysis_match.group(1).strip()

    # 如果analysis为空，尝试从答案后面的文本提取
    if not analysis and answer:
        # 填空题：答案本身可能就是解析
        if q_type == '填空题':
            analysis = answer

    return {
        'chapter': _clean_chapter_title(chapter_title),
        'index': index,
        'type': q_type,
        'question': question_text,
        'options': options,
        'answer': answer,
        'analysis': analysis,
        'sourceChapter': _clean_chapter_title(chapter_title),
        'images': images,
    }


def _extract_images(html):
    """提取HTML中的所有图片URL"""
    urls = re.findall(
        r'<img[^>]+src=[\'"]([^\'"]+)[\'"]',
        html,
        re.IGNORECASE
    )
    # 过滤掉图标类小图
    valid = []
    for url in urls:
        if any(skip in url for skip in ['/popClose', '/icon', '/loading']):
            continue
        # 补全协议
        if url.startswith('//'):
            url = 'https:' + url
        valid.append(url)
    return valid


def _clean_html(html):
    """去除HTML标签，保留文本"""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    return text


def _clean_chapter_title(title):
    """清理章节标题"""
    title = title.replace('&nbsp;', ' ').strip()
    title = re.sub(r'\s+', ' ', title)
    return title
