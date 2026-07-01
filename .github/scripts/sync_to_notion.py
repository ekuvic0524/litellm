"""
将复习 .md 文件同步到 Notion（以父页面模式）
工作方式：
  1. 在 Notion 创建一个空白页面，Share 给 Integration
  2. 把页面 URL 中 32 位 ID 设到 NOTION_DATABASE_ID
  3. 每次运行：在该页面下创建/更新子页面，每个 .md 一个子页面
"""
import os
import json
import re

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
PAGE_ID = os.environ.get("NOTION_PAGE_ID")

REVIEWS_DIR = "局部解剖学"

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
        print(f"  [Notion API Error] {method} {path} -> {r.status_code}: {r.text[:300]}")
    r.raise_for_status()
    return r.json()


def get_existing_children(page_id):
    """获取父页面下的所有子页面（只查第一层 page）"""
    existing = {}
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = req("GET", f"blocks/{page_id}/children?page_size={params['page_size']}" +
                   (f"&start_cursor={cursor}" if cursor else ""))
        for block in resp.get("results", []):
            if block.get("type") == "child_page":
                title = block["child_page"]["title"]
                existing[title] = block["id"]
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return existing


def parse_inline_bold(text):
    """将 **bold** 标记转为 Notion rich_text 数组"""
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    rich = []
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            rich.append({"type": "text", "text": {"content": p[2:-2]}, "annotations": {"bold": True}})
        else:
            rich.append({"type": "text", "text": {"content": p}})
    return rich if rich else [{"type": "text", "text": {"content": text[:2000]}}]


def text_block(content, bold=False):
    return {"type": "text", "text": {"content": str(content)[:2000]}, "annotations": {"bold": True}} if bold \
        else {"type": "text", "text": {"content": str(content)[:2000]}}


def md_to_blocks(lines):
    """将 .md 内容转换为 Notion block 列表"""
    blocks = []
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [text_block(text)]},
            })
            i += 1
            continue

        if stripped.startswith("## ") and not stripped.startswith("### "):
            text = stripped[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [text_block(text)]},
            })
            i += 1
            continue

        if stripped.startswith("### "):
            text = stripped[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [text_block(text)]},
            })
            i += 1
            continue

        if stripped.startswith("#### "):
            text = stripped[5:].strip()
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [text_block(text, bold=True)]},
            })
            i += 1
            continue

        if stripped.startswith("- "):
            text = stripped[2:].strip()
            rich = parse_inline_bold(text)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rich},
            })
            i += 1
            continue

        if stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # 表格行
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.match(r'^[\s\|\:\-\s]+$', stripped):
                i += 1
                continue
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[:2000]}}]
                },
            })
            i += 1
            continue

        # 答案隐藏块 ||xxx||
        if "||" in stripped:
            ans_clean = stripped.replace("||", "**")
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": ans_clean[:2000]}}]
                },
            })
            i += 1
            continue

        # 普通段落（合并相邻行）
        para_lines = []
        while i < total_lines and lines[i].strip():
            para_lines.append(lines[i].strip())
            i += 1
        content = " ".join(para_lines)
        if not content or re.match(r'^[\s\|\:\-\s]+$', content):
            continue
        rich = parse_inline_bold(content)
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich},
        })

    return blocks


def get_all_children(page_id):
    """获取页面的所有子块（处理分页）"""
    all_blocks = []
    cursor = None
    while True:
        url = f"blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        resp = req("GET", url)
        all_blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return all_blocks


def sync_file(filepath, existing_pages):
    """读取 .md 文件，在 Notion 父页面下创建/更新子页面"""
    basename = os.path.basename(filepath)
    title = os.path.splitext(basename)[0]

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 提取第一行 H1 作为子页面标题（用于匹配 Notion 已有页面）
    page_title = title
    for line in lines:
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            page_title = s[2:].strip()
            break

    # 用中文页面标题匹配已有子页面，而不是用文件名
    match_key = page_title

    blocks = md_to_blocks(lines)
    if not blocks:
        print(f"  ⏭️  {title}: 空内容，跳过")
        return

    # Notion 限制：blocks 每次最多 100 个，分批
    block_chunks = [blocks[i:i+100] for i in range(0, len(blocks), 100)]

    # 统一策略：有则先删再新建，避免块管理问题
    page_id = None
    if match_key in existing_pages:
        page_id = existing_pages[match_key]
        # 先归档删除旧子页面
        req("DELETE", f"blocks/{page_id}")
        print(f"  ~ 删除旧页面: {match_key}")

    # 新建子页面（第一块内联，后续追加）
    page_id = None
    for chunk in block_chunks:
        if page_id is None:
            body = {
                "parent": {"page_id": PAGE_ID},
                "properties": {
                    "title": {"title": [{"type": "text", "text": {"content": page_title}}]}
                },
                "children": chunk,
            }
            resp = req("POST", "pages", body)
            page_id = resp["id"]
        else:
            req("PATCH", f"blocks/{page_id}/children", {"children": chunk})

    action = "已更新" if match_key in existing_pages else "已创建"
    print(f"  ✓ {title}: {action}")


def main():
    if not NOTION_TOKEN or not PAGE_ID:
        print("错误: 请设置 NOTION_TOKEN 和 NOTION_PAGE_ID")
        print("NOTION_PAGE_ID = Notion 页面的 32 位 ID")
        exit(1)

    if not os.path.isdir(REVIEWS_DIR):
        print(f"未找到目录: {REVIEWS_DIR}")
        exit(0)

    mds = sorted(f for f in os.listdir(REVIEWS_DIR) if f.endswith(".md"))
    if not mds:
        print(f"{REVIEWS_DIR} 中没有 .md 文件")
        return

    print(f"发现 {len(mds)} 个文件，开始同步到 Notion...\n")

    # 获取父页面下所有已有子页面
    existing = get_existing_children(PAGE_ID)
    print(f"父页面下已有 {len(existing)} 个子页面\n")

    for md_file in mds:
        print(f"处理: {md_file}")
        try:
            sync_file(os.path.join(REVIEWS_DIR, md_file), existing)
        except Exception as e:
            print(f"  ✗ 失败: {e}")

    print(f"\n同步完成！")


if __name__ == "__main__":
    main()
