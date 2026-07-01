#!/usr/bin/env python3
"""
局部解剖学 题库聚类复习生成器
从7个超星HTML文件中提取题目 → 去重 → 聚类 → 重点命中判断 → 生成Markdown复习文档
完全离线运行，不依赖图片下载，不涉及有机化学
"""

import re
import json
import os
from collections import defaultdict

# ============================================================
# 1. 考试重点数据（来自局解重点.doc）
# ============================================================

EXAM_KEY_POINTS = {
    "chapter01": {
        "name": "头部",
        "points": [
            {"id": "1.1", "text": "颅顶区的层次", "keywords": ["颅顶", "颅顶区", "颅顶部", "危险区", "腱膜下", "帽状腱膜", "浅筋膜", "颞区", "颞筋膜"]},
            {"id": "1.2", "text": "面部浅层", "keywords": ["面部", "面动脉", "面静脉", "面部浅层", "面神经", "表情肌"]},
            {"id": "1.3", "text": "腮腺咬肌区", "keywords": ["腮腺", "咬肌", "腮腺咬肌区", "腮腺管", "面神经", "腮腺手术"]},
            {"id": "1.4", "text": "腮腺床", "keywords": ["腮腺床", "茎突", "颈内动脉", "舌咽神经", "迷走神经", "副神经", "舌下神经"]},
            {"id": "1.5", "text": "面侧深区", "keywords": ["面侧深区", "翼内肌", "翼外肌", "翼丛", "上颌动脉", "下颌神经"]},
            {"id": "1.6", "text": "咬肌间隙和翼下颌间隙", "keywords": ["咬肌间隙", "翼下颌间隙", "咬肌", "下颌支"]},
            {"id": "1.7", "text": "脑膜中动脉", "keywords": ["脑膜中动脉", "上颌动脉", "硬膜外血肿"]},
            {"id": "1.8", "text": "面部危险三角", "keywords": ["危险三角", "面静脉", "眼上静脉", "海绵窦"]},
        ]
    },
    "chapter02": {
        "name": "颈部",
        "points": [
            {"id": "2.1", "text": "颈部的层次", "keywords": ["颈部", "颈筋膜", "颈阔肌", "颈深筋膜", "气管前层", "椎前层"]},
            {"id": "2.2", "text": "颈动脉三角", "keywords": ["颈动脉三角", "颈总动脉", "颈内动脉", "颈外动脉", "颈动脉鞘", "舌下神经"]},
            {"id": "2.3", "text": "肌三角", "keywords": ["肌三角", "甲状腺", "甲状旁腺", "喉返神经", "甲状腺下动脉"]},
            {"id": "2.4", "text": "颈动脉鞘", "keywords": ["颈动脉鞘", "颈总动脉", "颈内静脉", "迷走神经"]},
            {"id": "2.5", "text": "枕三角", "keywords": ["枕三角", "副神经", "斜方肌"]},
            {"id": "2.6", "text": "下颌下三角", "keywords": ["下颌下三角", "下颌下腺", "舌下神经", "舌神经"]},
            {"id": "2.7", "text": "胸膜顶的位置与毗邻", "keywords": ["胸膜顶", "锁骨上", "肺尖"]},
        ]
    },
    "chapter03": {
        "name": "胸部和脊柱区",
        "points": [
            {"id": "3.1", "text": "胸前外侧壁的层次", "keywords": ["胸前", "胸壁", "胸肌", "胸大肌", "胸小肌", "锁骨下肌"]},
            {"id": "3.2", "text": "胸神经前支的分布规律", "keywords": ["胸神经", "肋间神经", "皮支", "节段性", "T2", "T4", "T6", "T8", "T10"]},
            {"id": "3.3", "text": "肋间血管神经", "keywords": ["肋间血管", "肋间神经", "肋间后动脉", "肋间"]},
            {"id": "3.4", "text": "纵隔的侧面观及分区", "keywords": ["纵隔", "前纵隔", "中纵隔", "后纵隔", "上纵隔", "下纵隔"]},
            {"id": "3.5", "text": "乳腺的位置、构造与淋巴回流", "keywords": ["乳腺", "乳房", "淋巴回流", "胸骨旁", "腋窝", "淋巴"]},
            {"id": "3.6", "text": "心包穿刺的应用", "keywords": ["心包", "心包穿刺", "剑突", "胸骨旁"]},
            {"id": "3.7", "text": "锁胸筋膜", "keywords": ["锁胸筋膜", "锁骨下肌", "胸小肌"]},
            {"id": "3.8", "text": "动脉导管三角", "keywords": ["动脉导管三角", "动脉韧带", "喉返神经"]},
            {"id": "3.9", "text": "听诊三角", "keywords": ["听诊三角", "斜方肌", "背阔肌", "肩胛骨"]},
            {"id": "3.10", "text": "腰上三角", "keywords": ["腰上三角", "竖脊肌", "腹内斜肌", "下后锯肌"]},
            {"id": "3.11", "text": "腰下三角", "keywords": ["腰下三角", "背阔肌", "腹外斜肌", "髂嵴"]},
            {"id": "3.12", "text": "腰穿的位置及经过的层次", "keywords": ["腰穿", "腰椎穿刺", "蛛网膜下", "硬膜外", "棘突"]},
            {"id": "3.13", "text": "椎管的解剖", "keywords": ["椎管", "硬膜外隙", "蛛网膜下隙", "终池", "脊髓"]},
        ]
    },
    "chapter04": {
        "name": "腹部",
        "points": [
            {"id": "4.1", "text": "腹前外侧壁的层次", "keywords": ["腹前外侧壁", "腹直肌", "腹直肌鞘", "腹外斜肌", "腹内斜肌", "腹横肌", "腹白线"]},
            {"id": "4.2", "text": "腹股沟管的位置与构成", "keywords": ["腹股沟管", "腹股沟", "精索", "子宫圆韧带"]},
            {"id": "4.3", "text": "腹股沟三角", "keywords": ["腹股沟三角", "海氏三角", "腹壁下动脉", "直疝"]},
            {"id": "4.4", "text": "网膜囊", "keywords": ["网膜囊", "小网膜", "大网膜", "网膜孔", "Winslow"]},
            {"id": "4.5", "text": "肝十二指肠韧带", "keywords": ["肝十二指肠韧带", "胆总管", "肝固有动脉", "门静脉"]},
            {"id": "4.6", "text": "胰腺的形态位置与毗邻", "keywords": ["胰腺", "胰头", "胰体", "胰尾", "十二指肠"]},
            {"id": "4.7", "text": "肝外胆道及胆汁排放", "keywords": ["胆道", "胆囊", "胆总管", "胆汁", "胆囊三角", "Calot"]},
            {"id": "4.8", "text": "胃的神经支配", "keywords": ["胃", "迷走神经", "腹腔神经", "胃的神经"]},
            {"id": "4.9", "text": "阑尾的位置及体表投影", "keywords": ["阑尾", "麦氏点", "McBurney", "结肠带"]},
            {"id": "4.10", "text": "左右结肠旁沟", "keywords": ["结肠旁沟", "结肠"]},
            {"id": "4.11", "text": "左右肠系膜窦", "keywords": ["肠系膜窦", "肠系膜"]},
            {"id": "4.12", "text": "肾的位置与毗邻", "keywords": ["肾", "肾脏", "肾盂", "肾窦"]},
            {"id": "4.13", "text": "肾门", "keywords": ["肾门", "肾动脉", "肾静脉", "肾盂"]},
            {"id": "4.14", "text": "肾区的层次", "keywords": ["肾区", "肾筋膜", "肾脂肪囊"]},
            {"id": "4.15", "text": "输尿管的位置与分段", "keywords": ["输尿管", "输尿管分段", "输尿管狭窄"]},
            {"id": "4.16", "text": "肾结石的位置及排出体外经过的路径", "keywords": ["肾结石", "结石", "输尿管", "膀胱", "尿道"]},
        ]
    },
    "chapter05": {
        "name": "盆部及会阴",
        "points": [
            {"id": "5.1", "text": "盆部", "keywords": ["盆腔", "盆部", "盆膈"]},
            {"id": "5.2", "text": "男女性盆腔器官的位置与毗邻", "keywords": ["膀胱", "直肠", "子宫", "卵巢", "输卵管", "前列腺", "精囊"]},
            {"id": "5.3", "text": "坐骨肛门窝", "keywords": ["坐骨肛门窝", "坐骨直肠窝", "阴部内动脉", "阴部神经"]},
            {"id": "5.4", "text": "阴部管", "keywords": ["阴部管", "Alcock", "阴部神经"]},
            {"id": "5.5", "text": "会阴浅隙", "keywords": ["会阴浅隙", "尿生殖膈", "会阴"]},
            {"id": "5.6", "text": "会阴深隙", "keywords": ["会阴深隙", "尿道括约肌"]},
            {"id": "5.7", "text": "狭义会阴", "keywords": ["狭义会阴", "会阴"]},
        ]
    },
    "chapter06": {
        "name": "上肢",
        "points": [
            {"id": "6.1", "text": "上肢的血管神经的分布", "keywords": ["上肢血管", "上肢神经", "腋动脉", "肱动脉", "桡动脉", "尺动脉", "正中神经", "桡神经", "尺神经"]},
            {"id": "6.2", "text": "肩袖", "keywords": ["肩袖", "冈上肌", "冈下肌", "小圆肌", "肩胛下肌"]},
            {"id": "6.3", "text": "三边孔", "keywords": ["三边孔", "旋肩胛动脉"]},
            {"id": "6.4", "text": "四边孔", "keywords": ["四边孔", "腋神经", "旋肱后动脉"]},
            {"id": "6.5", "text": "腋窝", "keywords": ["腋窝", "腋淋巴结", "臂丛"]},
            {"id": "6.6", "text": "肘窝", "keywords": ["肘窝", "肱二头肌腱", "肱动脉", "正中神经"]},
            {"id": "6.7", "text": "腕管", "keywords": ["腕管", "正中神经", "屈肌支持带"]},
            {"id": "6.8", "text": "手掌的层次", "keywords": ["手掌", "掌腱膜", "掌浅弓", "掌深弓", "指腱鞘"]},
        ]
    },
    "chapter07": {
        "name": "下肢",
        "points": [
            {"id": "7.1", "text": "下肢的血管神经的分布", "keywords": ["下肢血管", "下肢神经", "股动脉", "腘动脉", "胫前动脉", "胫后动脉"]},
            {"id": "7.2", "text": "肌腔隙", "keywords": ["肌腔隙", "髂腰肌", "股神经"]},
            {"id": "7.3", "text": "血管腔隙", "keywords": ["血管腔隙", "股动脉", "股静脉"]},
            {"id": "7.4", "text": "股三角", "keywords": ["股三角", "股神经", "股动脉", "股静脉", "股管"]},
            {"id": "7.5", "text": "收肌管", "keywords": ["收肌管", "Hunter", "股动脉", "隐神经"]},
            {"id": "7.6", "text": "腘窝", "keywords": ["腘窝", "腘动脉", "腘静脉", "胫神经"]},
            {"id": "7.7", "text": "踝管", "keywords": ["踝管", "胫后动脉", "胫神经", "屈肌支持带"]},
            {"id": "7.8", "text": "坐骨神经", "keywords": ["坐骨神经", "梨状肌"]},
            {"id": "7.9", "text": "胫神经", "keywords": ["胫神经", "胫神经损伤"]},
            {"id": "7.10", "text": "腓总神经", "keywords": ["腓总神经", "腓总神经损伤", "足下垂", "腓骨颈"]},
            {"id": "7.11", "text": "胫神经和腓总神经损伤的表现", "keywords": ["神经损伤", "足下垂", "钩状足", "足内翻", "足外翻"]},
        ]
    }
}

# 章节文件映射
CHAPTER_FILES = [
    ("chapter01", "F:/litellm/局部解剖学/1.局解头部.html", 0),
    ("chapter02", "F:/litellm/局部解剖学/2.颈部.html", 0),
    ("chapter03", "F:/litellm/局部解剖学/3.胸部和脊柱区.html", 0),
    ("chapter04", "F:/litellm/局部解剖学/4.腹部.html", 0),
    ("chapter05", "F:/litellm/局部解剖学/5.盆部及会阴.html", 0),
    ("chapter06", "F:/litellm/局部解剖学/6局解上肢.html", 0),
    ("chapter07", "F:/litellm/局部解剖学/7.下肢.html", 0),
]

OUTPUT_DIR = "F:/litellm/局部解剖学"

# ============================================================
# 2. HTML 解析器
# ============================================================

class QuestionParser:
    """解析超星HTML题目"""

    @staticmethod
    def clean_html(text):
        """清理HTML标签"""
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<p[^>]*>', '', text)
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<span[^>]*>', '', text)
        text = re.sub(r'</span>', '', text)
        text = re.sub(r'<div[^>]*>', '', text)
        text = re.sub(r'</div>', '', text)
        text = re.sub(r'<ul[^>]*>', '', text)
        text = re.sub(r'</ul>', '', text)
        text = re.sub(r'<li[^>]*>', '', text)
        text = re.sub(r'</li>', '', text)
        text = re.sub(r'<u[^>]*>', '', text)
        text = re.sub(r'</u>', '', text)
        text = re.sub(r'<strong[^>]*>', '', text)
        text = re.sub(r'</strong>', '', text)
        text = re.sub(r'<em[^>]*>', '', text)
        text = re.sub(r'</em>', '', text)
        text = re.sub(r'<i[^>]*>', '', text)
        text = re.sub(r'</i>', '', text)
        text = re.sub(r'<ins[^>]*>', '', text)
        text = re.sub(r'</ins>', '', text)
        text = re.sub(r'<del[^>]*>', '', text)
        text = re.sub(r'</del>', '', text)
        text = re.sub(r'<img[^>]*>', '[图片]', text)
        text = re.sub(r'<a[^>]*>', '', text)
        text = re.sub(r'</a>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        # Remove &nbsp;
        text = text.replace('&nbsp;', ' ')
        text = text.replace(' ', ' ')
        # Collapse multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    @staticmethod
    def extract_question_text(q_div):
        """提取题干"""
        m = re.search(r'<h3[^>]*class="mark_name[^"]*"[^>]*>.*?<span class="qtContent[^"]*"[^>]*>(.*?)</span>', q_div, re.DOTALL)
        if m:
            return QuestionParser.clean_html(m.group(1))
        return ""

    @staticmethod
    def extract_options(q_div):
        """提取选项"""
        options = []
        opt_pattern = re.findall(r'<li[^>]*class="workTextWrap"[^>]*>([A-Z])\.\s*(.*?)</li>', q_div, re.DOTALL)
        if not opt_pattern:
            # Try alternative pattern
            opt_section = re.search(r'<ul[^>]*class="mark_letter[^"]*"[^>]*>(.*?)</ul>', q_div, re.DOTALL)
            if opt_section:
                opts = re.findall(r'<li[^>]*>(.*?)</li>', opt_section.group(1), re.DOTALL)
                for opt in opts:
                    opt = QuestionParser.clean_html(opt)
                    if opt:
                        options.append(opt)
        else:
            for letter, text in opt_pattern:
                text = QuestionParser.clean_html(text)
                options.append(f"{letter}. {text}")
        return options

    @staticmethod
    def extract_answer(q_div):
        """提取正确答案"""
        m = re.search(r'<span class="rightAnswerContent[^"]*"[^>]*>(.*?)</span>', q_div, re.DOTALL)
        if m:
            return QuestionParser.clean_html(m.group(1))

        # Try the hidden text
        m = re.search(r'element-invisible-hidden[^>]*>[^:]*:\s*(.*?);', q_div, re.DOTALL)
        return ""

    @staticmethod
    def extract_number(q_div):
        """提取题号"""
        m = re.search(r'<h3[^>]*>(\d+)\.', q_div)
        if m:
            return int(m.group(1))
        return 0

    @staticmethod
    def extract_question_id(q_div):
        """提取题目ID"""
        m = re.search(r'id="question(\d+)"', q_div)
        if m:
            return m.group(1)
        return ""


def parse_html_file(filepath):
    """解析单个HTML文件，返回题目列表"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    questions = []

    # Split by question div start — this is the most reliable method
    marker = '<div class="marBom60 questionLi singleQuesId"'
    sections = content.split(marker)

    for sec in sections[1:]:  # skip the first part (before any question)
        # Extract question ID
        qid_m = re.search(r'id="question(\d+)"', sec)
        qid = qid_m.group(1) if qid_m else ""

        # Extract question number and text
        # h3 like: <h3 class="mark_name colorDeep" ...>1. <span class="colorShallow">(单选题)</span><span class="qtContent workTextWrap">xxx</span></h3>
        num_m = re.search(r'<h3[^>]*>\s*(\d+)\.', sec)
        qnum = int(num_m.group(1)) if num_m else 0

        # Question text from qtContent span
        qtext_m = re.search(r'<span class="qtContent[^"]*"[^>]*>(.*?)</span>', sec, re.DOTALL)
        qtext = QuestionParser.clean_html(qtext_m.group(1)) if qtext_m else ""
        # Strip embedded type markers like "【单选题】", "(单选题)" from question text
        qtext = re.sub(r'^[【(][^】)）]+[】)）]\s*', '', qtext).strip()

        # Options from mark_letter ul
        opt_section = re.search(r'<ul[^>]*class="mark_letter[^"]*"[^>]*>(.*?)</ul>', sec, re.DOTALL)
        options = []
        if opt_section:
            opts = re.findall(r'<li[^>]*class="workTextWrap"[^>]*>([A-Z])\.\s*(.*?)</li>', opt_section.group(1), re.DOTALL)
            if opts:
                for letter, text in opts:
                    text = QuestionParser.clean_html(text)
                    options.append(f"{letter}. {text}")
            else:
                # Try alternative: just get all li text
                opts2 = re.findall(r'<li[^>]*>(.*?)</li>', opt_section.group(1), re.DOTALL)
                for opt in opts2:
                    opt = QuestionParser.clean_html(opt)
                    if opt and not opt.startswith('<'):
                        options.append(opt)

        # Answer from rightAnswerContent span
        ans_m = re.search(r'<span class="rightAnswerContent[^"]*"[^>]*>(.*?)</span>', sec, re.DOTALL)
        answer = QuestionParser.clean_html(ans_m.group(1)) if ans_m else ""

        # Also get student answer and hidden answer text for completeness
        stu_m = re.search(r'<span class="stuAnswerContent[^"]*"[^>]*>(.*?)</span>', sec, re.DOTALL)
        stu_answer = QuestionParser.clean_html(stu_m.group(1)) if stu_m else ""

        # Try to get the answer text from the hidden span
        hidden_m = re.search(r'element-invisible-hidden[^>]*>:(.*?);', sec, re.DOTALL)
        if not answer and hidden_m:
            answer = QuestionParser.clean_html(hidden_m.group(1))

        questions.append({
            'id': qid,
            'number': qnum,
            'text': qtext,
            'options': options,
            'answer': answer,
        })

    return questions


def parse_all_files():
    """解析所有HTML文件"""
    all_questions = {}
    total = 0

    for ch_id, filepath, _ in CHAPTER_FILES:
        print(f"  解析 {filepath.split('/')[-1]}...")
        try:
            qs = parse_html_file(filepath)
            all_questions[ch_id] = qs
            print(f"    → 提取到 {len(qs)} 题")
            total += len(qs)
        except Exception as e:
            print(f"    ✗ 解析失败: {e}")
            all_questions[ch_id] = []

    print(f"\n  共提取 {total} 题")
    return all_questions


# ============================================================
# 3. 聚类引擎
# ============================================================

# 聚类关键词映射
CLUSTER_RULES = {
    "层次题": {
        "keywords": ["层次", "分层", "浅筋膜", "深筋膜", "皮肤", "皮下", "浅层", "深层",
                    "颅顶", "胸壁", "腹壁", "腹前外侧壁", "胸前外侧壁", "手掌的层次",
                    "肾区", "肾区层次", "腰穿", "椎管", "会阴浅", "会阴深", "会阴隙",
                    "颈部层次", "颈部的层次", "颅顶区", "颅顶部的"],
        "sub_keywords": {
            "颅顶层次": ["颅顶", "帽状腱膜", "腱膜下", "颅顶区", "危险区", "颞区", "颞筋膜", "额顶枕"],
            "面部浅层": ["面部浅层", "面动脉", "面静脉", "表情肌"],
            "颈部层次": ["颈部层次", "颈筋膜", "颈阔肌", "颈深筋膜", "气管前", "椎前"],
            "胸前壁层次": ["胸前", "胸壁层次", "胸肌", "胸大肌", "胸小肌", "锁胸筋膜"],
            "腹壁层次": ["腹壁", "腹直肌鞘", "腹白线", "腹外斜肌", "腹内斜肌", "腹横肌", "腹前外侧壁"],
            "肾区层次": ["肾区", "肾筋膜", "肾脂肪囊", "肾的被膜"],
            "腰穿层次": ["腰穿", "腰椎穿刺", "硬膜外", "蛛网膜下", "棘突"],
            "手掌层次": ["手掌", "掌腱膜", "掌浅弓", "掌深弓"],
        }
    },
    "三角/管/窝/隙题": {
        "keywords": ["三角", "管", "窝", "隙", "腔隙", "间隙", "孔", "沟", "窦", "池"],
        "sub_keywords": {
            "颈动脉三角": ["颈动脉三角", "颈总动脉"],
            "肌三角": ["肌三角", "甲状腺"],
            "枕三角": ["枕三角", "副神经"],
            "下颌下三角": ["下颌下三角", "下颌下腺"],
            "听诊三角": ["听诊三角"],
            "腰上三角": ["腰上三角"],
            "腰下三角": ["腰下三角"],
            "腹股沟管": ["腹股沟管", "腹股沟", "精索", "子宫圆韧带"],
            "腹股沟三角": ["腹股沟三角", "海氏三角", "直疝"],
            "股三角": ["股三角", "股神经", "股动脉", "股静脉", "股管"],
            "收肌管": ["收肌管", "Hunter"],
            "腘窝": ["腘窝", "腘动脉", "腘静脉"],
            "肘窝": ["肘窝", "肱二头肌腱"],
            "腕管": ["腕管", "屈肌支持带"],
            "踝管": ["踝管", "屈肌支持带", "踝"],
            "腋窝": ["腋窝", "腋淋巴结", "臂丛"],
            "三边孔": ["三边孔", "旋肩胛"],
            "四边孔": ["四边孔", "腋神经", "旋肱后"],
            "咬肌间隙": ["咬肌间隙", "翼下颌间隙", "咬肌", "下颌支"],
            "面侧深区": ["面侧深区", "翼内肌", "翼外肌", "翼丛"],
            "腮腺咬肌区": ["腮腺", "咬肌", "腮腺咬肌", "腮腺管", "腮腺床"],
            "坐骨肛门窝": ["坐骨肛门窝", "坐骨直肠窝"],
            "阴部管": ["阴部管", "Alcock"],
            "会阴浅隙": ["会阴浅隙"],
            "会阴深隙": ["会阴深隙"],
            "网膜囊": ["网膜囊", "小网膜", "大网膜", "网膜孔", "Winslow"],
            "胆囊三角": ["胆囊三角", "Calot", "肝十二指肠韧带"],
            "动脉导管三角": ["动脉导管三角", "动脉韧带"],
            "肌腔隙": ["肌腔隙", "髂腰肌"],
            "血管腔隙": ["血管腔隙", "股动脉", "股静脉"],
        }
    },
    "血管神经题": {
        "keywords": ["动脉", "静脉", "神经", "血管", "淋巴", "血供", "回流", "分布",
                    "分支", "走行", "体表投影"],
        "sub_keywords": {
            "脑膜中动脉": ["脑膜中动脉", "上颌动脉"],
            "面神经": ["面神经", "面神经分支", "下颌缘支", "颧支", "颊支", "颈支"],
            "颈动脉鞘": ["颈动脉鞘"],
            "胸神经前支": ["胸神经", "肋间神经", "节段性", "T2", "T4", "T6"],
            "肋间血管神经": ["肋间血管", "肋间后动脉"],
            "上肢血管神经": ["上肢", "腋动脉", "肱动脉", "桡动脉", "尺动脉", "正中神经", "桡神经", "尺神经"],
            "下肢血管神经": ["下肢", "股动脉", "腘动脉", "胫前动脉", "胫后动脉", "股神经"],
            "坐骨神经": ["坐骨神经", "梨状肌"],
            "胫神经": ["胫神经损伤", "胫神经"],
            "腓总神经": ["腓总神经", "足下垂", "腓骨颈", "腓总神"],
            "神经损伤": ["神经损伤", "损伤表现", "钩状足", "足内翻", "足外翻"],
            "淋巴回流": ["淋巴回流", "淋巴", "胸骨旁淋巴", "腋淋巴"],
            "乳腺淋巴": ["乳腺", "乳房", "淋巴", "胸骨旁", "腋窝"],
        }
    },
    "毗邻题": {
        "keywords": ["毗邻", "相邻", "位置与", "位于", "后方", "前方", "上方", "下方",
                    "外侧", "内侧", "周围", "关系", "邻接"],
        "sub_keywords": {
            "腮腺床": ["腮腺床", "茎突", "颈内动脉"],
            "胰腺": ["胰腺", "胰头", "胰体", "胰尾", "十二指肠"],
            "肾": ["肾的位置", "肾与", "肾脏", "肾盂", "肾窦"],
            "盆腔器官": ["膀胱", "直肠", "子宫", "卵巢", "输卵管", "前列腺"],
            "胸膜顶": ["胸膜顶", "锁骨上", "肺尖"],
            "纵隔": ["纵隔", "前纵隔", "中纵隔", "后纵隔", "上纵隔"],
            "肝外胆道": ["胆道", "胆囊", "胆总管", "肝外胆"],
        }
    },
    "临床路径题": {
        "keywords": ["穿刺", "手术", "切口", "损伤", "切开", "麻醉", "阻滞",
                    "结石", "排出", "疝", "骨折", "体表投影", "投影", "引流",
                    "切除", "修补"],
        "sub_keywords": {
            "心包穿刺": ["心包穿刺", "心包"],
            "腰穿路径": ["腰穿", "腰椎穿刺"],
            "肾结石路径": ["肾结石", "结石", "排出"],
            "阑尾炎": ["阑尾", "麦氏点", "McBurney"],
            "腹股沟疝": ["腹股沟疝", "直疝", "斜疝", "疝"],
            "神经损伤表现": ["神经损伤", "损伤表现", "足下垂", "钩状足"],
            "体表投影": ["体表投影", "投影"],
            "面部切口": ["切口", "面部", "面动脉", "腮腺手术"],
        }
    }
}

def detect_clusters(question_text, options_text, answer_text):
    """检测题目的聚类——精确匹配，避免误触发"""
    # 题干文本（带权重的关键词匹配）
    q_lower = question_text.lower()
    # 全文本（题干+选项+答案）
    combined = (question_text + " " + options_text + " " + answer_text).lower()

    primary = "其他低优先级题"
    secondary = ""

    # 给每个聚类打分，但题干匹配权重更高
    scores = {}

    for p_cluster, rules in CLUSTER_RULES.items():
        # 题干匹配分（权重3）
        q_score = sum(3 for kw in rules["keywords"] if kw.lower() in q_lower)
        # 全文本匹配分（权重1）
        c_score = sum(1 for kw in rules["keywords"] if kw.lower() in combined)
        total = q_score + c_score
        if total > 0:
            scores[p_cluster] = total

    if scores:
        # 找出最高分的主聚类（需要至少2分才生效）
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            primary = best

    if primary != "其他低优先级题" and primary in CLUSTER_RULES:
        sub_rules = CLUSTER_RULES[primary].get("sub_keywords", {})
        sub_scores = {}
        for s_cluster, s_kws in sub_rules.items():
            q_score = sum(3 for kw in s_kws if kw.lower() in q_lower)
            c_score = sum(1 for kw in s_kws if kw.lower() in combined)
            total = q_score + c_score
            if total > 0:
                sub_scores[s_cluster] = total

        if sub_scores:
            best_sub = max(sub_scores, key=sub_scores.get)
            if sub_scores[best_sub] >= 2:
                secondary = best_sub
                # If primary was defaulted to 层次题 due to shallow match, re-check
                # Example: 管理头面部皮肤感觉的神经是 → should be 血管神经题, not 层次题

    # Secondary fallback: if no secondary but primary is set, check all sub-categories
    if not secondary and primary != "其他低优先级题":
        # Check all sub_keywords across ALL categories for a better match
        all_subs = {}
        for p_cluster, rules in CLUSTER_RULES.items():
            for s_cluster, s_kws in rules.get("sub_keywords", {}).items():
                q_score = sum(3 for kw in s_kws if kw.lower() in q_lower)
                if q_score > 0:
                    all_subs[s_cluster] = q_score

        if all_subs:
            # Find which primary cluster this sub belongs to
            best_sub = max(all_subs, key=all_subs.get)
            for p_cluster, rules in CLUSTER_RULES.items():
                if best_sub in rules.get("sub_keywords", {}):
                    if p_cluster != primary:
                        # Re-assign to the correct cluster
                        primary = p_cluster
                    secondary = best_sub
                    break

    return primary, secondary


# ============================================================
# 4. 重点命中判断和优先级
# ============================================================

def match_key_points(question_text, options_text, answer_text, chapter_id):
    """判断题目是否命中考试重点"""
    combined = (question_text + " " + options_text + " " + answer_text).lower()

    chapter_points = EXAM_KEY_POINTS.get(chapter_id, {}).get("points", [])

    matched_points = []
    max_score = 0

    for point in chapter_points:
        kws = [kw.lower() for kw in point["keywords"]]
        match_count = sum(1 for kw in kws if kw in combined)
        if match_count > 0:
            score = match_count / len(kws)  # 命中率
            if score > max_score:
                max_score = score
            matched_points.append({
                "point": point,
                "score": score,
                "match_count": match_count
            })

    # Sort by score
    matched_points.sort(key=lambda x: x["score"], reverse=True)

    return matched_points


def determine_priority(question_text, options_text, answer_text, chapter_id):
    """确定优先级 S/A/B/C（严格的评分标准）"""
    q_lower = question_text.lower()

    # S级高收益概念词（只检查题干）
    s_concepts = [
        "层次", "三角", "内容物", "境界", "走行", "分布", "神经损伤", "损伤表现",
        "穿刺", "路径", "排出", "体表投影", "淋巴回流", "腹股沟疝", "直疝", "斜疝",
        "管", "窝", "隙", "腔隙",
    ]

    matched = match_key_points(question_text, options_text, answer_text, chapter_id)

    has_s_concept = any(kw in q_lower for kw in s_concepts)

    if matched:
        best = matched[0]
        mc = best["match_count"]

        # S级：命中2个以上重点关键词 + S级概念
        if mc >= 2 and has_s_concept:
            return "S"
        # A级：命中2个以上重点关键词
        elif mc >= 2:
            return "A"
        # A级：只命中1个但题干有S概念（如"三角的内容物"）
        elif mc == 1 and has_s_concept:
            return "A"
        # B级：弱命中1个关键词
        elif mc == 1:
            return "B"
        else:
            return "C"
    else:
        return "C"


def determine_hit_status(priority, matched_points):
    """判断命中状态"""
    if priority in ("S", "A"):
        return "重点命中"
    elif priority == "B":
        if matched_points:
            return "弱相关"
        return "弱相关"
    else:
        return "未命中"


# ============================================================
# 5. 题眼和最小答案句提取
# ============================================================

def extract_question_eye(question_text):
    """提取题眼"""
    # Remove common prefixes
    text = question_text
    # Remove question markers
    text = re.sub(r'^.*?是指', '', text)
    text = re.sub(r'^.*?包括', '', text)
    text = re.sub(r'^.*?位于', '', text)
    text = re.sub(r'^.*?关于', '', text)

    # The key is usually the main subject
    # Try to extract the core structure name
    core_patterns = [
        r'(危险区|腮腺床|肩袖|腕管|踝管|肘窝|腘窝|股三角|收肌管|肌腔隙|血管腔隙|三边孔|四边孔|坐骨肛门窝|阴部管|会阴浅隙|会阴深隙|腹股沟管|腹股沟三角|胆囊三角|动脉导管三角|听诊三角|腰上三角|腰下三角|颈动脉三角|肌三角|枕三角|下颌下三角|咬肌间隙|翼下颌间隙|面侧深区|网膜囊|锁胸筋膜|掌浅弓|掌深弓)',
        r'(面神经|脑膜中动脉|上颌动脉|腓总神经|胫神经|坐骨神经|肋间神经|胸神经|正中神经|桡神经|尺神经|腋神经|副神经|迷走神经|舌下神经|喉返神经)',
        r'(腹股沟疝|直疝|斜疝|肾结石|心包穿刺|腰穿|麦氏点)',
        r'(淋巴回流|体表投影|神经损伤|血管分布)',
    ]

    for pattern_list in core_patterns:
        m = re.search(pattern_list, question_text)
        if m:
            return m.group(1)

    # Fallback: just the first meaningful phrase
    m = re.search(r'(.{4,20})', text)
    if m:
        return m.group(1).strip()

    return question_text[:30]


def extract_min_answer(answer_text, question_text):
    """提取最小答案句"""
    # Just clean and return the answer (these are MCQs, so the answer is usually short)
    return answer_text.strip()


# ============================================================
# 6. 去重引擎
# ============================================================

def normalize_text(text):
    """归一化文本用于去重比较"""
    text = re.sub(r'\s+', '', text)
    text = text.replace('，', ',').replace('。', '.').replace('；', ';').replace('：', ':')
    text = text.lower()
    return text


def deduplicate_questions(all_questions_by_chapter):
    """去重，返回去重后的题目列表和重复信息"""
    all_flat = []
    for ch_id, questions in all_questions_by_chapter.items():
        for q in questions:
            q['chapter'] = ch_id
            all_flat.append(q)

    # Sort by chapter order then number
    chapter_order = {ch: i for i, (ch, _, _) in enumerate(CHAPTER_FILES)}
    all_flat.sort(key=lambda q: (chapter_order.get(q.get('chapter', ''), 99), q.get('number', 0)))

    deduped = []
    seen_texts = {}  # normalized text -> group_id
    dup_group_counter = [0]

    for q in all_flat:
        normalized = normalize_text(q.get('text', ''))
        # Also skip empty questions
        if not normalized:
            continue

        # Check if it's an image-only question
        if '[图片]' in q.get('text', '') and not any(c > '一' and c < '鿿' for c in q.get('text', '')):
            q['is_image_only'] = True
        else:
            q['is_image_only'] = False

        # Check for duplicate
        found_dup = False
        for seen_text, seen_info in seen_texts.items():
            # Exact match
            if normalized == seen_info['normalized']:
                q['is_duplicate'] = True
                q['dup_group_id'] = seen_info['group_id']
                seen_info['numbers'].append(q.get('number', 0))
                seen_info['chapters'].append(q.get('chapter', ''))
                found_dup = True
                break

            # Similarity check (short circuit for long texts)
            if len(normalized) > 10 and len(seen_text) > 10:
                # Check if one contains the other or very high overlap
                if normalized == seen_text or seen_text == normalized:
                    q['is_duplicate'] = True
                    q['dup_group_id'] = seen_info['group_id']
                    seen_info['numbers'].append(q.get('number', 0))
                    seen_info['chapters'].append(q.get('chapter', ''))
                    found_dup = True
                    break

        if not found_dup:
            dup_group_counter[0] += 1
            q['is_duplicate'] = False
            q['dup_group_id'] = dup_group_counter[0]
            seen_texts[normalized] = {
                'normalized': normalized,
                'group_id': dup_group_counter[0],
                'numbers': [q.get('number', 0)],
                'chapters': [q.get('chapter', '')],
            }
            deduped.append(q)
        else:
            # Keep track but don't add to main list
            pass

    # Collect dup info for each group
    dup_groups = defaultdict(list)
    for q in all_flat:
        if q.get('is_duplicate', False):
            dup_groups[q['dup_group_id']].append(q)

    # Mark which main questions have duplicates
    dup_group_members = defaultdict(list)
    for q in all_flat:
        if q.get('is_duplicate', False):
            dup_group_members[q['dup_group_id']].append(q)

    # Annotate deduped questions with their duplicate siblings
    for q in deduped:
        q['dup_siblings'] = []
        for dq in all_flat:
            if dq.get('dup_group_id') == q['dup_group_id'] and dq is not q:
                q['dup_siblings'].append(dq)

    return deduped, dup_groups


# ============================================================
# 7. Markdown 生成器
# ============================================================

def generate_chapter_review(chapter_id, chapter_name, questions):
    """生成单章复习文档"""
    lines = []
    lines.append(f"# 第{list(EXAM_KEY_POINTS.keys()).index(chapter_id)+1}章 {chapter_name} 局解题库聚类复习")
    lines.append("")

    # Statistics
    stats = {"S": 0, "A": 0, "B": 0, "C": 0, "重点命中": 0, "重复组": 0}
    priority_order = {"S": "⭐【必拿】", "A": "✅【高频】", "B": "👀【扫读】", "C": "🗑【低优先级】"}

    for q in questions:
        p = q.get('priority', 'C')
        stats[p] = stats.get(p, 0) + 1
        if q.get('hit_status') == "重点命中":
            stats["重点命中"] += 1
        if q.get('dup_siblings'):
            stats["重复组"] += 1

    lines.append("## 本章优先级统计")
    lines.append(f"- S级：{stats['S']}题")
    lines.append(f"- A级：{stats['A']}题")
    lines.append(f"- B级：{stats['B']}题")
    lines.append(f"- C级：{stats['C']}题")
    lines.append(f"- 重点命中：{stats['重点命中']}题")
    lines.append(f"- 去重后总题数：{len(questions)}题")
    lines.append(f"- 重复题组：{stats['重复组']}组")
    lines.append("")

    # Group by primary cluster
    primary_order = ["层次题", "三角/管/窝/隙题", "血管神经题", "毗邻题", "临床路径题", "其他低优先级题"]
    primary_labels = {
        "层次题": "1. 层次题",
        "三角/管/窝/隙题": "2. 三角/管/窝/隙题",
        "血管神经题": "3. 血管神经题",
        "毗邻题": "4. 毗邻题",
        "临床路径题": "5. 临床路径题",
    }
    clustered = defaultdict(lambda: defaultdict(list))

    for q in questions:
        p_cluster = q.get('primary_cluster', '其他低优先级题')
        s_cluster = q.get('secondary_cluster', '')
        if not s_cluster:
            s_cluster = "其他"
        clustered[p_cluster][s_cluster].append(q)

    # C级题单独收集
    c_questions = [q for q in questions if q.get('priority') == 'C']

    for idx, p_cluster in enumerate(primary_order, 1):
        if p_cluster == "其他低优先级题":
            continue
        if p_cluster not in clustered:
            continue

        lines.append(f"## {idx}. {p_cluster}")
        lines.append("")

        sub_clusters = clustered[p_cluster]
        for s_cluster in sorted(sub_clusters.keys()):
            qs = sub_clusters[s_cluster]
            # Filter out C-level questions (shown in section 6 only)
            qs = [q for q in qs if q.get('priority', 'C') != 'C']
            if not qs:
                continue
            # Sort by priority: S, A, B then by number
            qs.sort(key=lambda q: ({"S": 0, "A": 1, "B": 2, "C": 3}.get(q.get('priority', 'C'), 4), q.get('number', 0)))

            lines.append(f"### {s_cluster}")
            lines.append("")

            for q in qs:
                pri = q.get('priority', 'C')
                hit = q.get('hit_status', '')
                marker = priority_order.get(pri, "🗑【低优先级】")
                num = q.get('number', '?')

                # Title line
                title = f"#### {marker} 题号{num}"
                lines.append(title)

                # Fields
                lines.append(f"- **题干**：{q.get('text', '')}")

                if q.get('options'):
                    lines.append(f"- **选项**：{' | '.join(q['options'][:6])}")

                lines.append(f"- **答案**：{q.get('answer', '')}")

                if q.get('eye'):
                    lines.append(f"- **题眼**：{q['eye']}")
                if q.get('min_answer') and q.get('min_answer') != q.get('answer', ''):
                    lines.append(f"- **最小答案句**：{q['min_answer']}")
                if q.get('matched_point'):
                    lines.append(f"- **对应重点**：{q['matched_point']}")
                if q.get('dup_siblings'):
                    sibling_info = []
                    for sib in q['dup_siblings']:
                        ch_idx = list(EXAM_KEY_POINTS.keys()).index(sib.get('chapter','')) + 1
                        sibling_info.append(f"第{ch_idx}章 第{sib.get('number','?')}题")
                    lines.append(f"- **重复题号**：{'；'.join(sibling_info)}")
                if hit == "重点命中":
                    lines.append(f"- **命中状态**：🔥重点命中")

                lines.append("")

    # C-level: low priority section
    if c_questions:
        lines.append("## 6. 其他低优先级题")
        lines.append("")
        lines.append("> 以下题目为低优先级复习内容，仅列题号、题干、答案。")
        lines.append("")
        for q in c_questions:
            num = q.get('number', '?')
            text = q.get('text', '')
            ans = q.get('answer', '')
            lines.append(f"- **题号{num}**：{text} → 答案：{ans}")
        lines.append("")

    return "\n".join(lines)


def generate_all_high_priority(all_deduped):
    """生成all_high_priority.md"""
    lines = []
    lines.append("# 全部重点必拿题汇总（S级 + A级）")
    lines.append("")
    lines.append("> 按老师重点顺序排列")
    lines.append("")

    high_pri = [q for q in all_deduped if q.get('priority') in ('S', 'A')]
    high_pri.sort(key=lambda q: (
        list(EXAM_KEY_POINTS.keys()).index(q.get('chapter', 'chapter99')) if q.get('chapter') in EXAM_KEY_POINTS else 99,
        q.get('number', 0)
    ))

    lines.append(f"共 {len(high_pri)} 题（S级：{sum(1 for q in high_pri if q['priority']=='S')}题，A级：{sum(1 for q in high_pri if q['priority']=='A')}题）")
    lines.append("")

    current_chapter = ""
    for q in high_pri:
        ch = q.get('chapter', '')
        ch_name = EXAM_KEY_POINTS.get(ch, {}).get('name', ch)
        ch_num = list(EXAM_KEY_POINTS.keys()).index(ch) + 1 if ch in EXAM_KEY_POINTS else "?"

        chapter_header = f"第{ch_num}章 {ch_name}"
        if chapter_header != current_chapter:
            current_chapter = chapter_header
            lines.append(f"## {chapter_header}")
            lines.append("")

        marker = "⭐【必拿】" if q['priority'] == 'S' else "✅【高频】"
        lines.append(f"### {marker} 题号{q.get('number', '?')}")
        lines.append(f"- 题眼：{q.get('eye', '')}")
        lines.append(f"- 最小答案句：{q.get('min_answer', '')}")
        lines.append(f"- 答案：{q.get('answer', '')}")
        lines.append(f"- 对应重点：{q.get('matched_point', '')}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# 8. 主流程
# ============================================================

def main():
    print("=" * 60)
    print("局部解剖学 题库聚类复习生成器")
    print("=" * 60)

    # Step 1: Parse all HTML files
    print("\n[1/5] 解析HTML题目文件...")
    all_raw = parse_all_files()

    # Step 2: Fix chapter number offsets (each HTML's internal numbering starts at 1)
    print("\n[2/5] 聚类分析 & 重点命中判断...")

    all_processed = {}
    for ch_id, questions in all_raw.items():
        ch_name = EXAM_KEY_POINTS.get(ch_id, {}).get("name", ch_id)
        ch_num = list(EXAM_KEY_POINTS.keys()).index(ch_id) + 1
        print(f"  处理第{ch_num}章 {ch_name} ({len(questions)}题)...")

        for q in questions:
            qtext = q.get('text', '')
            optext = ' '.join(q.get('options', []))
            anstext = q.get('answer', '')

            # Skip image-only questions
            if q.get('is_image_only', False):
                q['primary_cluster'] = "其他低优先级题"
                q['secondary_cluster'] = "图片题"
                q['priority'] = "C"
                q['hit_status'] = "未命中"
                q['eye'] = "[图片题已跳过]"
                q['min_answer'] = ""
                q['matched_point'] = ""
                continue

            # Cluster
            primary, secondary = detect_clusters(qtext, optext, anstext)
            q['primary_cluster'] = primary
            q['secondary_cluster'] = secondary

            # Determine priority
            matched_points = match_key_points(qtext, optext, anstext, ch_id)
            priority = determine_priority(qtext, optext, anstext, ch_id)
            q['priority'] = priority
            q['matched_points'] = matched_points
            q['hit_status'] = determine_hit_status(priority, matched_points)

            # Matched point text
            if matched_points:
                q['matched_point'] = matched_points[0]['point']['text']

            # Eye and min answer
            q['eye'] = extract_question_eye(qtext)
            q['min_answer'] = extract_min_answer(anstext, qtext)

        all_processed[ch_id] = questions

    # Step 3: Deduplicate
    print("\n[3/5] 去重处理...")
    deduped_list, dup_groups = deduplicate_questions(all_processed)
    print(f"  去重前：{sum(len(v) for v in all_processed.values())}题")
    print(f"  去重后：{len(deduped_list)}题")
    print(f"  重复题组：{len(dup_groups)}组")

    # Step 4: Group by chapter for output
    print("\n[4/5] 生成Markdown复习文档...")
    chapter_questions = defaultdict(list)
    for q in deduped_list:
        chapter_questions[q.get('chapter', '')].append(q)

    # Generate per-chapter files
    for ch_id, fp, _ in CHAPTER_FILES:
        ch_name = EXAM_KEY_POINTS.get(ch_id, {}).get("name", ch_id)
        ch_num = list(EXAM_KEY_POINTS.keys()).index(ch_id) + 1
        qs = chapter_questions.get(ch_id, [])

        md_content = generate_chapter_review(ch_id, ch_name, qs)

        output_file = os.path.join(OUTPUT_DIR, f"chapter{ch_num:02d}_review.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  已生成 {output_file} ({len(qs)}题)")

    # Generate all_high_priority.md
    print("\n[5/5] 生成重点汇总文档...")
    hp_content = generate_all_high_priority(deduped_list)
    hp_file = os.path.join(OUTPUT_DIR, "all_high_priority.md")
    with open(hp_file, 'w', encoding='utf-8') as f:
        f.write(hp_content)
    print(f"  已生成 {hp_file}")

    # Summary
    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    s_count = sum(1 for q in deduped_list if q['priority'] == 'S')
    a_count = sum(1 for q in deduped_list if q['priority'] == 'A')
    b_count = sum(1 for q in deduped_list if q['priority'] == 'B')
    c_count = sum(1 for q in deduped_list if q['priority'] == 'C')
    hit_count = sum(1 for q in deduped_list if q['hit_status'] == '重点命中')
    print(f"S级（必拿）：{s_count}题")
    print(f"A级（高频）：{a_count}题")
    print(f"B级（扫读）：{b_count}题")
    print(f"C级（低优）：{c_count}题")
    print(f"重点命中：{hit_count}题")
    print(f"去重后总计：{len(deduped_list)}题")


if __name__ == "__main__":
    main()
