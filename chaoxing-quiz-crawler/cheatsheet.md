# Litellm 完整工作流

## 一、采集题库

```bash
# 1. 编辑 config.py，填入 Cookie
# 2. 开始采集
python chaoxing-quiz-crawler/main.py
# 可选：python chaoxing-quiz-crawler/main.py --force
```

**产出**: `output/questions.json` + `questions.md`

---

## 二、下载图片 + 打包 ZIP

```bash
python chaoxing-quiz-crawler/bundle_chapters.py --all
```

**产出**: 每章一个 `chapterXX_bundle.zip`（内含 JSON + 图片）

---

## 三、生成复习文档

```bash
python chaoxing-quiz-crawler/generate_review.py
```

**产出**: `output/reviews/` 每章一个 `.md`（纯文本题 + 知识点聚类）+ `图片题索引.md`

---

## 四、同步到 GitHub（可选）

```bash
git add .
git commit -m "更新复习材料"
git push
```

---

## 五、自动同步到 Notion（可选，需提前配置）

push 后 GitHub Actions 自动跑，把 `.md` 写到你的 Notion 页面下。
每章一个子页面，新建的自动创建，已有的自动更新。

### 首次配置 Notion

```
1. https://www.notion.so/my-integrations → + New integration → 复制 ntn_...
2. 在 Notion 新建一个空白页面 → Share → 添加该 Integration
3. 从页面 URL 复制 32 位 ID → 设为 GitHub Secret: NOTION_PAGE_ID
4. 把 ntn_... 设为 GitHub Secret: NOTION_TOKEN
```

Secrets 设置页面: `https://github.com/ekuvic0524/litellm/settings/secrets/actions`

---

## 文件索引

| 文件 | 作用 |
|------|------|
| `config.py` | Cookie + 课程参数配置 |
| `main.py` | 采集入口（断点续采） |
| `bundle_chapters.py` | 图片下载 + 章节打包 |
| `generate_review.py` | 复习材料生成 + 知识点聚类 |
| `workflow.md` | 本文件 |

**仓库**: https://github.com/ekuvic0524/litellm
