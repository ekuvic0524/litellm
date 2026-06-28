"""验证打包输出"""
import json
import zipfile
import os

BASE = 'chaoxing-quiz-crawler/output'

# 检查 chapter02
with open(f'{BASE}/chapter02/chapter02.json', 'r', encoding='utf-8') as fh:
    d = json.load(fh)
print(f'总题数: {len(d)}')
has_img = [q for q in d if q.get('hasImage')]
print(f'hasImage=True: {len(has_img)}')
total_ic = sum(q.get('imageCount', 0) for q in d)
print(f'imageCount求和: {total_ic}')
img_with_local = sum(1 for q in has_img if q['images'] and q['images'][0].get('local'))
print(f'images含local路径: {img_with_local}')

# 检查ZIP
z = zipfile.ZipFile(f'{BASE}/chapter02_bundle.zip')
names = z.namelist()
print(f'\nZIP条目数: {len(names)}')
img_in_zip = [n for n in names if n.startswith('images/') and not n.endswith('/')]
print(f'ZIP图片数: {len(img_in_zip)}')
# 检查第1个条目的JSON
if names:
    with z.open(names[0]) as f:
        zj = json.load(f)
    print(f'ZIP内JSON题数: {len(zj)}')

# 检查目录结构
print(f'\noutput/ 目录下:')
for fn in sorted(os.listdir(BASE)):
    fp = os.path.join(BASE, fn)
    if os.path.isdir(fp):
        sz = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(fp) for f in fs)
        print(f'  dir  {fn}/  ({sz/1024:.0f} KB)')
    elif fn.endswith('.zip'):
        print(f'  zip  {fn}  ({os.path.getsize(fp)/1024:.0f} KB)')
    elif fn in ('.image_cache',):
        sz = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(fp) for f in fs)
        print(f'  dir  {fn}/  ({sz/1024:.0f} KB)')
