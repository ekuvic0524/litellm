"""
中国近现代史纲要 — 百度OCR流水线
用法: python baidu_ocr_shigang.py
"""
import os, sys, json, time, base64, io, re, urllib.request, urllib.parse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import fitz
except ImportError:
    fitz = None

# ============ 配置 ============
API_KEY = "nQsyjGgNMeqDfbJ1VkcuDMrP"
SECRET_KEY = "DekBB85xIU5vvzfXZ1BoERYAtNwuSyh0"
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
# 使用 accurate_basic 效果更好
OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"

PDF_PATH = "F:/litellm/中国近现代史纲要(2023年版) (《中国近现代史纲要(2023年版)》编写组) (z-libr.pdf"
OUT_DIR = "F:/litellm/中国近现代史纲要"
OCR_OUTPUT = os.path.join(OUT_DIR, "中国近现代史纲要_OCR全文.txt")

# ============ 百度OCR API ============
def get_token():
    url = f"{TOKEN_URL}?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
    resp = urllib.request.urlopen(url, timeout=15)
    return json.loads(resp.read())["access_token"]

def ocr_image(img, token, retry=3):
    """调用百度OCR识别一张图片"""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    data = urllib.parse.urlencode({"image": img_base64}).encode()
    req = urllib.request.Request(f"{OCR_URL}?access_token={token}", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    for attempt in range(retry):
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            if "words_result" in result:
                return "\n".join(item["words"] for item in result["words_result"])
            elif result.get("error_code") == 17:  # 额度用完
                print(f"\n[!] 每日免费额度已用完! {result}")
                return None
            elif result.get("error_code") == 18:  # QPS超限
                time.sleep(2)
                continue
            else:
                print(f"\n[!] API错误: {result}")
                return ""
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"\n[!] 请求失败: {e}")
            return ""

# ============ OCR全本 ============
def ocr_entire_book(token, dpi=200, delay=1.0):
    if fitz is None:
        print("[错误] 需要pymupdf: pip install PyMuPDF")
        sys.exit(1)
    if Image is None:
        print("[错误] 需要Pillow: pip install Pillow")
        sys.exit(1)

    doc = fitz.open(PDF_PATH)
    total = doc.page_count
    print(f"[PDF] 共{total}页，开始OCR...")

    # 断点续传：读取已有结果
    existing = {}
    if os.path.exists(OCR_OUTPUT):
        with open(OCR_OUTPUT, "r", encoding="utf-8") as f:
            content = f.read()
        for block in content.split("\n--- 第"):
            if block.strip():
                m = re.search(r"(\d+)页 ---", block)
                if m:
                    existing[int(m.group(1))] = block
        print(f"[续传] 已识别 {len(existing)} 页")

    all_text = []
    # 先把已有结果按页号排好
    if existing:
        for i in range(1, max(existing.keys()) + 1):
            if i in existing:
                all_text.append(f"--- 第{i}页 ---\n{existing[i].split('---', 1)[1].strip()}")

    success = len(existing)
    fail = 0
    empty_count = 0

    for i in range(total):
        page_num = i + 1
        if page_num in existing:
            continue

        page = doc[i]
        # 先检查内置文字
        text = page.get_text().strip()
        if text and len(text) > 50:
            all_text.append(f"--- 第{page_num}页 ---\n{text}")
            print(f"  第{page_num}页 [文字] {len(text)}字")
            success += 1
            continue

        # OCR
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        sys.stdout.write(f"  第{page_num}页 [OCR]")
        sys.stdout.flush()

        result = ocr_image(img, token)
        if result is None:  # 额度用完
            print(" -> 额度不足，暂停")
            # 保存已识别的
            if all_text:
                with open(OCR_OUTPUT, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(all_text))
                print(f"  已保存 {success} 页到 {OCR_OUTPUT}")
            break

        if result:
            all_text.append(f"--- 第{page_num}页 ---\n{result}")
            print(f" {len(result)}字")
            success += 1
            empty_count = 0
        else:
            print(" [空页]")
            empty_count += 1

        # 每20页自动保存
        if (page_num) % 20 == 0:
            with open(OCR_OUTPUT, "w", encoding="utf-8") as f:
                f.write("\n\n".join(all_text))
            print(f"\n[进度] {page_num}/{total}页 | 成功{success} | 空{fail}")
            print(f"[保存] 已写入 {OCR_OUTPUT}")

        time.sleep(delay)

    doc.close()

    # 最终保存
    if all_text:
        with open(OCR_OUTPUT, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_text))
    print(f"\n{'='*50}")
    print(f"[完成] {success}页成功, {fail}页空")
    print(f"[输出] {OCR_OUTPUT}")

    total_chars = sum(len(t.split("---", 1)[-1].strip()) if "---" in t else len(t) for t in all_text)
    print(f"[字数] 约 {total_chars} 字")
    return "\n\n".join(all_text)

# ============ 主流程 ============
def main():
    print("=" * 50)
    print("中国近现代史纲要  OCR 流水线")
    print("=" * 50)

    print("\n[1/2] 获取百度OCR Token...")
    token = get_token()
    print(f"  Token获取成功 ({token[:20]}...)")

    print("\n[2/2] 开始OCR识别...")
    print(f"  PDF: {PDF_PATH}")
    print(f"  输出: {OCR_OUTPUT}")
    ocr_entire_book(token, dpi=200, delay=1.0)

if __name__ == "__main__":
    main()
