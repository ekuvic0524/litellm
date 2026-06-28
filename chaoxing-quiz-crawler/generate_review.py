"""
生成有机化学复习材料 + 图片题索引
用法: python generate_review.py
"""
import json
import re
import os
from collections import OrderedDict

OUTPUT_DIR = 'chaoxing-quiz-crawler/output/reviews'
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open('chaoxing-quiz-crawler/output/questions.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)

def clean(s):
    """清洗HTML实体"""
    s = s.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def chapter_number(title):
    CN_MAP = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
              '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18}
    m = re.search(r'第\s*(\d+)\s*章', title)
    if m: return int(m.group(1))
    m = re.search(r'第\s*([一二三四五六七八九十]+)\s*章', title)
    if m: return CN_MAP.get(m.group(1), 99)
    return 99

def has_image(q):
    return q.get('hasImage', False) or bool(q.get('images'))

def is_option_pure_image(opt_text):
    t = clean(opt_text).rstrip('.')
    return len(t) <= 2

# ======= 各章节知识点聚类规则 =======
# 格式: (关键词列表, 知识点名称)
KNOWLEDGE_CLUSTERS = {
    '第一章': [
        (['轨道', '杂化', 'sp', 'σ', 'π', '共价键', '键角', '键能', '分子轨道', '电子云', '杂化轨道'], '杂化轨道与共价键'),
        (['异构', '构型', '顺反', '对映', '手性', '旋光', 'R/S', 'E/Z'], '异构现象'),
        (['诱导', '共轭', '超共轭', '电子效应'], '电子效应'),
        (['酸碱', 'pH', 'pKa', '质子', '亲核'], '酸碱性与亲核性'),
        (['命名', 'IUPAC'], '命名规则'),
    ],
    '第4章': [
        (['环己烷', '构象', '船式', '椅式', '平伏', '直立', 'a键', 'e键', '环烷烃', '张力'], '环烷烃构象'),
        (['顺反', '异构', '构型', 'R/S', 'E/Z', '对映', '手性', '旋光', '外消旋'], '顺反异构与对映异构'),
        (['稳定性', '燃烧热', '张力能'], '环烷烃稳定性'),
        (['加成', '取代', '氧化'], '环烷烃化学反应'),
    ],
    '第5章': [
        (['SN1', 'SN2', '亲核取代', '取代反应', 'Walden', '瓦尔登'], '亲核取代反应(SN1/SN2)'),
        (['卤代烃', '卤素', 'R-X', '格氏试剂', 'Grignard', '格林尼亚'], '卤代烃'),
        (['E1', 'E2', '消除', 'Saytzeff', '扎伊采夫', 'Hofmann', '霍夫曼'], '消除反应(E1/E2)'),
        (['活性', '反应速率', '速率常数', '动力学'], '反应活性与动力学'),
    ],
    '第6章': [
        (['亲核取代', 'SN1', 'SN2', '消除', 'E1', 'E2', '竞争'], 'SN1/SN2与E1/E2竞争'),
        (['活性', '离去', '溶剂', '极性', '质子性'], '反应活性与溶剂效应'),
        (['动力学', '速率', '一级反应', '二级反应'], '反应动力学'),
    ],
    '第8章': [
        (['SN1', 'SN2', '亲核取代', '取代反应'], '亲核取代反应(SN1/SN2)'),
        (['E1', 'E2', '消除', '消除反应', 'Saytzeff', '扎伊采夫', 'Hofmann', '霍夫曼'], '消除反应(E1/E2)'),
        (['SN', 'E', '竞争', 'vs'], '取代与消除的竞争'),
        (['格氏试剂', 'Grignard', '格林尼亚', '有机金属'], '格氏试剂'),
        (['卤代烃', '卤素', 'F', 'Cl', 'Br', 'I', '活性', '反应活性'], '卤代烃反应活性'),
        (['SN', 'E', '机理', '离子对', '碳正离子', '中间体'], '反应机理'),
    ],
    '第9章': [
        (['醇', '酚', '羟基', '—OH', '硫醇', '巯基', '—SH'], '醇酚硫醇概述'),
        (['酸性', '碱性', 'pKa', '解离'], '酸碱性'),
        (['氧化', '还原', '脱氢'], '氧化还原反应'),
        (['脱水', '消除', '烯烃', '分子内', '分子间'], '脱水反应'),
        (['酯化', '醚', 'Williamson', '威廉姆森'], '酯化与成醚'),
        (['鉴别', '区分', '检测', '卢卡斯', 'Lucas', 'FeCl', '三氯化铁'], '鉴别反应'),
        (['氢键', '沸点', '溶解度'], '物理性质'),
    ],
    '第11章': [
        (['胺', '氨基', '—NH'], '胺的分类与结构'),
        (['碱性', 'pKa', '酸性', '碱性强弱'], '碱性强弱比较'),
        (['重氮', '偶氮', '亚硝基', 'N-亚硝基', '亚硝酸'], '重氮化与亚硝基反应'),
        (['酰基化', 'Hinsberg', '兴斯堡', '磺酰氯', '苯磺酰'], '酰基化(Hinsberg反应)'),
        (['鉴别', '区分', '检测', '分离'], '鉴别与分离'),
        (['季铵', '霍夫曼', 'Hofmann', '彻底甲基化'], '季铵盐与Hofmann消除'),
        (['生物碱', '提取', '沉淀'], '生物碱'),
    ],
    '第12章': [
        (['醛', '酮', '羰基', 'C=O'], '醛酮结构与命名'),
        (['亲核加成', '加成', 'HCN', 'NaHSO', '亚硫酸氢钠', 'Grignard', '格氏试剂', '醇', '半缩醛', '缩醛', '水合'], '亲核加成反应'),
        (['氧化', '还原', 'Tollens', '斐林', 'Fehling', 'Benedict', '本尼迪特', '银镜'], '氧化还原反应'),
        (['碘仿', '卤仿', '甲基酮'], '碘仿反应(甲基酮鉴别)'),
        (['鉴别', '区分', '检测'], '鉴别反应'),
        (['Aldol', '羟醛缩合', '康尼查罗', 'Cannizzaro', 'Perkin', '珀金'], '缩合反应'),
        (['活性', '反应性', '空间位阻', '电子效应'], '羰基反应活性'),
    ],
    '第13章': [
        (['羧酸', '—COOH', '羧基', '脂肪酸'], '羧酸结构与命名'),
        (['酸性', 'pKa', '酸性强弱', '取代羧酸'], '羧酸酸碱性'),
        (['酯化', 'Fischer', '费歇尔', '酸酐', '酰氯', '酰卤', '酰胺'], '羧酸衍生物'),
        (['还原', '氧化', '脱羧'], '氧化还原与脱羧'),
        (['氨基酸', 'α-氨基酸', '两性', '等电点', 'pI', '茚三酮'], '氨基酸(两性/等电点/显色)'),
        (['肽', '肽键', '二肽', '多肽'], '肽与肽键'),
        (['鉴别', '区分', '检测'], '鉴别反应'),
    ],
    '第16章': [
        (['单糖', '葡萄糖', '果糖', '核糖', '甘露糖', '半乳糖'], '单糖结构与分类'),
        (['苷', '苷键', '糖苷'], '糖苷'),
        (['还原性', '还原糖', '非还原糖', 'Tollens', '斐林', 'Fehling', '银镜'], '还原糖与非还原糖'),
        (['变旋', '差向', '异构', '端基', '异头'], '变旋与差向异构'),
        (['双糖', '蔗糖', '麦芽糖', '乳糖', '纤维二糖'], '双糖'),
        (['多糖', '淀粉', '纤维素', '糖原'], '多糖'),
        (['鉴别', '区分', '检测'], '鉴别反应'),
    ],
}

# 默认聚类
FALLBACK_KEY = '其他'

def cluster_question(q, chapter_title):
    """将题目归入知识点，模糊匹配章节名"""
    text = clean(q.get('question', ''))
    options = ' '.join(clean(o) for o in q.get('options', []))
    analysis = clean(q.get('analysis', ''))
    full = text + ' ' + options + ' ' + analysis

    # 模糊匹配章节名（chapter_title是完整版如"第8章 卤代烃 客观题"）
    matched_clusters = []
    for ch_key, clusters in KNOWLEDGE_CLUSTERS.items():
        if ch_key in chapter_title or chapter_title.startswith(ch_key):
            matched_clusters = clusters
            break

    if not matched_clusters:
        print(f'  [调试] 未匹配到聚类规则: {chapter_title}')
        return FALLBACK_KEY

    best_label = FALLBACK_KEY
    best_score = 0
    for keywords, label in matched_clusters:
        score = sum(1 for kw in keywords if kw in full)
        if score > best_score:
            best_score = score
            best_label = label
    if best_score < 1:
        best_label = FALLBACK_KEY
    return best_label


# ======= 按章节分组 =======
groups = OrderedDict()
for q in all_data:
    ch = q.get('sourceChapter', '未知章节')
    if ch not in groups:
        groups[ch] = []
    groups[ch].append(q)

sorted_ch = sorted(groups.items(), key=lambda x: chapter_number(x[0]))

all_img_questions = []

for ch_title, qs in sorted_ch:
    ch_num = chapter_number(ch_title)
    short_name = f'第{ch_num}章' if ch_num < 99 else ch_title

    # 跳过第2章(立体化学)
    if ch_num == 2:
        continue

    text_qs = [q for q in qs if not has_image(q)]
    img_qs = [q for q in qs if has_image(q)]
    all_img_questions.extend(img_qs)

    if not text_qs:
        continue

    # 按知识点聚类
    clustered = OrderedDict()
    for q in text_qs:
        label = cluster_question(q, ch_title)
        if label not in clustered:
            clustered[label] = []
        clustered[label].append(q)

    # 生成MD
    lines = []
    ch_num = chapter_number(ch_title)
    short_name = f'第{ch_num}章'
    lines.append(f'# {short_name} — 复习')
    lines.append(f'')
    lines.append(f'> {ch_title} | 纯文本题 {len(text_qs)}道 | 图片题 {len(img_qs)}道（见图片题索引）')
    lines.append(f'')
    lines.append(f'---')
    lines.append(f'')

    # 总览
    lines.append(f'## 知识点速览')
    lines.append(f'')
    for label, cqs in clustered.items():
        lines.append(f'- **{label}**: {len(cqs)}题')
    if FALLBACK_KEY in clustered:
        lines.append(f'  > ⚠️ 部分题目无法自动分类，已归入"其他"')
    lines.append(f'')
    lines.append(f'---')
    lines.append(f'')

    # 逐知识点
    for label, cqs in clustered.items():
        lines.append(f'## {label}')
        lines.append(f'')
        lines.append(f'共 {len(cqs)} 题')
        lines.append(f'')

        for i, q in enumerate(cqs, 1):
            idx = q.get('index', '?')
            qtype = q.get('type', '?')
            question = clean(q.get('question', ''))
            options = [clean(o) for o in q.get('options', [])]
            answer = clean(q.get('answer', ''))
            analysis = clean(q.get('analysis', ''))

            lines.append(f'### {idx}. {question}')
            lines.append(f'')
            lines.append(f'**题型**: {qtype}')
            lines.append(f'')
            for opt in options:
                if opt:
                    lines.append(f'- {opt}')
            lines.append(f'')
            if analysis:
                lines.append(f'**解析**: {analysis}')
                lines.append(f'')
            lines.append(f'**答案**: ||{answer}||')
            lines.append(f'')
            lines.append(f'---')
            lines.append(f'')

    # 答案汇总
    lines.append(f'## 答案汇总')
    lines.append(f'')
    lines.append(f'| 题号 | 答案 | 知识点 |')
    lines.append(f'|------|------|--------|')
    for label, cqs in clustered.items():
        for q in cqs:
            idx = q.get('index', '?')
            answer = clean(q.get('answer', ''))
            lines.append(f'| {idx} | {answer} | {label} |')
    lines.append(f'')

    # 打印聚类分布
    for label, cqs in clustered.items():
        print(f'    {label}: {len(cqs)}题')
    if FALLBACK_KEY in clustered:
        print(f'    ⚠️ {clustered[FALLBACK_KEY][0].get("question","")[:50]}...')

    # 写文件
    safe_name = f'chapter{str(ch_num).zfill(2)}_{short_name}'
    safe_name = re.sub(r'[\\/:*?"<>|]', '', safe_name)
    filepath = os.path.join(OUTPUT_DIR, f'{safe_name}.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'✓ {safe_name}.md  ({len(text_qs)}题, {len(clustered)}个知识点)')

# ======= 图片题索引 =======
img_lines = []
img_lines.append(f'# 图片题索引')
img_lines.append(f'')
img_lines.append(f'> 共 {len(all_img_questions)} 题包含结构图/反应式，需看图作答')
img_lines.append(f'')
img_lines.append(f'---')
img_lines.append(f'')

# 按章节分组显示
img_by_ch = OrderedDict()
for q in all_img_questions:
    ch = q.get('sourceChapter', '未知章节')
    if ch not in img_by_ch:
        img_by_ch[ch] = []
    img_by_ch[ch].append(q)

for ch_title, qs in img_by_ch.items():
    img_lines.append(f'## {ch_title}（{len(qs)}题）')
    img_lines.append(f'')
    for q in qs:
        idx = q.get('index', '?')
        qtype = q.get('type', '?')
        question = clean(q.get('question', ''))
        images = q.get('images', [])
        if images and isinstance(images[0], dict):
            img_list = [img.get('source', '') for img in images if img.get('source')]
        else:
            img_list = [str(img) for img in images if isinstance(img, str)]

        img_lines.append(f'### 第{idx}题 ({qtype})')
        img_lines.append(f'')
        img_lines.append(f'{question}')
        img_lines.append(f'')
        if img_list:
            img_lines.append(f'图片:')
            for u in img_list:
                img_lines.append(f'- {u}')
        img_lines.append(f'')

    img_lines.append(f'---')
    img_lines.append(f'')

# 按题型统计
from collections import Counter
type_count = Counter(q.get('type', '?') for q in all_img_questions)
img_lines.append(f'## 图片题题型分布')
img_lines.append(f'')
for t, c in type_count.most_common():
    img_lines.append(f'- {t}: {c}题')
img_lines.append(f'')

# 按章节统计
img_lines.append(f'## 图片题章节分布')
img_lines.append(f'')
for ch_title, qs in img_by_ch.items():
    img_lines.append(f'- {ch_title}: {len(qs)}题')
img_lines.append(f'')

img_path = os.path.join(OUTPUT_DIR, '图片题索引.md')
with open(img_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(img_lines))
print(f'\n✓ 图片题索引.md  ({len(all_img_questions)}题)')
print(f'\n所有文件已保存到: {OUTPUT_DIR}')
