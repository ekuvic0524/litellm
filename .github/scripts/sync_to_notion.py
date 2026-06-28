"""
将复习 .md 文件同步到 Notion 数据库
通过 GitHub Actions 自动触发，只需配好以下 Secrets：
  NOTION_TOKEN       - Notion Integration 的 Internal Integration Secret
  NOTION_DATABASE_ID - 目标 Database 的 ID（URL 中 32位 字符串）

使用前需在 Notion 侧：
  1. https://www.notion.so/my-integrations → 新建 Integration → 复制 Secret
  2. 在 Notion 创建 Database → Share → 添加上一步的 Integration
  3. 从 Database URL 中复制 ID（32位 hex）
"""
import os
import json
import hashlib
import re

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

REVIEWS_DIR = "chaoxing-quiz-crawler/output/reviews"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def req(method, path, body=None):
    import requests
    url = f"https://api.notion.com/v1/{path.lstrip('/')}"
    r = requests.request(method, url, headers=HEADERS, json=body)
    if r.status_code not in (200, 201):
        print(f"  [Notion API Error] {method} {path} -> {r.status_code}: {r.text[:200]}")
    r.raise_for_status()
    return r.json()


def page_id_by_title(target_title):
    """查询 Database 中是否已有同名页面，返回 page_id"""
    resp = req("POST", f"databases/{DATABASE_ID}/query", {
        "filter": {
            "property": "标题",
            "title": {"equals": target_title},
        },
    })
    results = resp.get("results", [])
    return results[0]["id"] if results else None


def md_to_blocks(lines):
    """将 .md 内容转换为 Notion block 列表"""
    blocks = []
    i = 0
    heading_counters = {"heading_1": 0, "heading_2": 0, "heading_3": 0}

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 空行跳过
        if not stripped:
            i += 1
            continue

        # 标题 H1: # xxx
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:].strip()
            heading_counters["heading_1"] += 1
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            })
            i += 1
            continue

        # 标题 H2: ## xxx
        if stripped.startswith("## "):
            text = stripped[3:].strip()
            heading_counters["heading_2"] += 1
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            })
            i += 1
            continue

        # 标题 H3: ### xxx
        if stripped.startswith("### "):
            text = stripped[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            })
            i += 1
            continue

        # 无序列表: - xxx
        if stripped.startswith("- "):
            text = stripped[2:].strip()
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                },
            })
            i += 1
            continue

        # 分隔符 ---
        if stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # 表格: | xxx | yyy | (暂不处理完整表格，当普通文本)
        if stripped.startswith("|") and stripped.endswith("|"):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stripped}}]
                },
            })
            i += 1
            continue

        # 普通段落 (合并相邻文本行)
        para_lines = []
        while i < len(lines) and lines[i].strip():
            para_lines.append(lines[i].strip())
            i += 1
        content = " ".join(para_lines)
        # 跳过纯数字行（表格的|---|那种）
        if re.match(r'^[\s\|\:\-\s]+$', content):
            continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
            },
        })

    return blocks


def sync_file(filepath):
    """读取一个 .md 文件，创建/更新 Notion 页面"""
    basename = os.path.basename(filepath)
    title = os.path.splitext(basename)[0]

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    name_line = ""
    for line in lines:
        if line.startswith("# ") or line.startswith("#"):
            name_line = line.lstrip("#").strip()
            break
    page_title = name_line or title

    blocks = md_to_blocks(lines)
    if not blocks:
        print(f"  ⏭️  {title}: 空内容，跳过")
        return

    existing_id = page_id_by_title(page_title)

    if existing_id:
        # 更新已有页面：先删旧子 block，再追加新 block
        children = req("GET", f"blocks/{existing_id}/children")
        for child in children.get("results", []):
            req("DELETE", f"blocks/{child['id']}")
        req("PATCH", f"blocks/{existing_id}/children", {"children": blocks})
        print(f"  ✓ {title}: 已更新")
    else:
        # 新建页面
        body = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "标题": {
                    "title": [{"type": "text", "text": {"content": page_title}}]
                }
            },
            "children": blocks,
        }
        req("POST", "pages", body)
        print(f"  ✓ {title}: 已创建")


def main():
    if not NOTION_TOKEN or not DATABASE_ID:
        print("错误: 请设置 NOTION_TOKEN 和 NOTION_DATABASE_ID 环境变量")
        print("在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加")
        exit(1)

    if not os.path.isdir(REVIEWS_DIR):
        print(f"未找到目录: {REVIEWS_DIR}")
        exit(0)

    mds = sorted(f for f in os.listdir(REVIEWS_DIR) if f.endswith(".md"))
    if not mds:
        print(f"{REVIEWS_DIR} 中没有 .md 文件")
        return

    print(f"发现 {len(mds)} 个文件，开始同步到 Notion...\n")
    for md_file in mds:
        print(f"处理: {md_file}")
        try:
            sync_file(os.path.join(REVIEWS_DIR, md_file))
        except Exception as e:
            print(f"  ✗ 失败: {e}")

    print(f"\n同步完成！")


if __name__ == "__main__":
    main()
