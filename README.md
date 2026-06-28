# Litellm — 超星学习通题库采集 + 复习材料生成

## 工作流

```
main.py               → 采集题目 → questions.json
bundle_chapters.py     → 下载图片 + 打包 → chapterXX_bundle.zip  
generate_review.py     → 生成复习 .md → output/reviews/
                          ↓ git push
                    GitHub Actions → Notion API
                          ↓
                      自动写入 Notion 数据库
```

## 快速开始

### 1. 采集题目

编辑 `config.py` 填入 Cookie，然后：

```bash
python chaoxing-quiz-crawler/main.py
```

可选参数：`--force` 忽略断点重新采集。

### 2. 下载图片 + 打包

```bash
python chaoxing-quiz-crawler/bundle_chapters.py --all
```

生成每章独立的 `chapterXX_bundle.zip`（含 JSON + 图片）。

### 3. 生成复习文档

```bash
python chaoxing-quiz-crawler/generate_review.py
```

产出 `output/reviews/` 目录，每章一个 .md，不含图片题（标记为需看图）。

### 4. 推送到 GitHub（自动同步到 Notion）

```bash
git add .
git commit -m "更新复习材料"
git push
```

`git push` 后 GitHub Actions 自动触发，把 .md 写到你的 Notion 数据库。

---

## Notion 同步配置（第一次使用）

### Step A: 获取 Notion API Key

1. 打开 https://www.notion.so/my-integrations
2. 点击 **+ New integration**
3. 名称填 `Litellm Sync`，关联你的工作空间
4. 提交后复制 **Internal Integration Secret**（以 `ntn_` 开头）

### Step B: 创建 Notion Database

1. 在 Notion 中新建一个 **Database**（建议用 Table 视图）
2. Database 至少包含一个 `标题` 列（默认就有）
3. 点击右上角 **Share** → **Add connections** → 选择 `Litellm Sync`

### Step C: 获取 Database ID

1. 打开 Database 页面
2. 从 URL 中复制 32 位十六进制 ID：
   ```
   https://www.notion.so/workspace/abc123def456abc123def456abc123def?v=xxx
                                          └─ Database ID ─┘
   ```

### Step D: 配置 GitHub Secrets

1. 在 GitHub 仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 添加两个 Secret：

| Secret | 值 |
|--------|---|
| `NOTION_TOKEN` | 你的 Integration Secret（`ntn_...`）|
| `NOTION_DATABASE_ID` | 32 位 Database ID |

搞定。下次 `git push` 后自动同步。

---

## 目录结构

```
litellm/
├── .github/
│   ├── workflows/sync-to-notion.yml   # GitHub Actions 自动同步
│   └── scripts/sync_to_notion.py      # Notion 同步脚本
├── chaoxing-quiz-crawler/
│   ├── main.py                        # 采集入口
│   ├── config.py                      # Cookie 配置
│   ├── bundle_chapters.py             # 图片下载 + ZIP 打包
│   ├── generate_review.py             # 复习材料生成
│   ├── workflow.md                    # 工作流说明
│   ├── crawler/                       # 爬虫模块
│   ├── parser/                        # 解析模块
│   └── output/
│       ├── questions.json             # 全量数据
│       ├── chapterXX_bundle.zip       # 每章 ZIP
│       └── reviews/                   # 复习 .md (推送到 GitHub 的文件)
│           ├── chapter01_第1章.md
│           ├── chapter04_第4章.md
│           ├── ...
│           └── 图片题索引.md
├── .gitignore
└── README.md
```
