# 超星学习通 客观题采集 + 打包 工作流

## 完整流程

### 第1步：配置 Cookie

编辑 `config.py`，填入最新的 Cookie：

```python
COOKIE = '从浏览器开发者工具复制...'
COURSE_ID = '240635420'       # 课程ID
CLASS_ID = '140119573'        # 班级ID
CPI = '485202988'             # 用户CPI
WORK_ENC = '1556c45bfd...'    # workEnc参数
```

> Cookie 获取：浏览器登录学习通 → F12 → Network → 任意请求 → Request Headers → Cookie

### 第2步：采集题目

```bash
python main.py
```

产出：`output/questions.json` + `output/questions.md`

| 配置项 | 说明 |
|--------|------|
 | `MAX_RETRIES = 3` | 下载重试次数 |
| `RETRY_DELAY = 2` | 重试间隔(秒) |
| `--force` | 忽略断点，重新采集所有 |

### 第3步：下载图片 + 按章节打包

```bash
# 全部自动跑完
python bundle_chapters.py --all

# 或逐章确认
python bundle_chapters.py               # 第1章
python bundle_chapters.py --chapter=2   # 继续第2章
```

产出：11 个 `chapterXX_bundle.zip`

每个 ZIP 内含：
- `chapterXX.json` — 章节题目（含 `hasImage` / `imageCount` / `images[].local` 字段）
- `images/` — 所有图片（SHA256 命名，全局去重）

### 输出文件结构

```
output/
├── questions.json              # 原始全量数据
├── questions.md                # 可读版
├── chapter01_bundle.zip        # 每个章节独立ZIP
├── chapter02_bundle.zip
├── ...
├── error.log                   # 下载失败记录
├── .image_cache/               # 全局图片缓存
│   ├── a1b2c3....png
│   └── ...
├── chapter01/
│   ├── chapter01.json
│   └── images/
├── chapter02/
│   └── ...
└── ...
```

### JSON 字段格式

```json
{
  "chapter": "第X章 客观题",
  "index": 1,
  "type": "单选题",
  "question": "题目文本...",
  "options": ["A. ", "B. ", "C. ", "D. "],
  "answer": "B",
  "analysis": "解析（如有）",
  "sourceChapter": "第X章 客观题",
  "hasImage": true,
  "imageCount": 2,
  "images": [
    {"local": "images/a1b2c3...png", "source": "https://p.ananas.chaoxing.com/..."},
    {"local": "images/d4e5f6...gif", "source": "https://p.ananas.chaoxing.com/..."}
  ]
}
```

> 纯文字题的 `options` 包含完整文本；含化学结构图的题 `options` 只有 "A." "B." 等标签，实际内容在 `images` 里。

### 注意事项

- Cookie 过期后需要重新获取
- `--all` 参数会覆盖已存在的 ZIP 和章节目录
- 图片下载失败不会中断程序，记录到 `error.log`
- 同图 SHA256 去重，跨章节复用
