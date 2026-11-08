"""Apply the media reviews: blur every marked box and every detected face, write web-ready images under anonymous
names into site/library/media/, and write _work/media/media_map.json for build.py.

Inputs: _work/media/review_*.json (MEDIA_BRIEF format), _work/media/pages/index.json (page captures).
usage: python3 tools/apply_media.py
"""
import hashlib, json, pathlib, re
import cv2, numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / '_work'
OUT = ROOT / 'site' / 'library' / 'media'
FACE = cv2.CascadeClassifier(str(W / 'models' / 'face.xml'))
BRAND_OF = lambda b: 'bighammer' if b.startswith('bighammer') else b

def anon_name(path, ext='webp'):
    return hashlib.sha1(('tb1:' + str(path)).encode()).hexdigest()[:16] + '.' + ext

def blur_box(img, box, strength):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 - x0 < 2 or y1 - y0 < 2: return
    region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(strength))
    img.paste(region, (x0, y0))

def process(src, boxes, max_side=1600):
    img = Image.open(src).convert('RGB')
    w, h = img.size
    strength = max(8, int(min(w, h) * 0.02))
    for b in boxes or []:
        blur_box(img, (b[0] * w, b[1] * h, b[2] * w, b[3] * h), strength)
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    for (x, y, fw, fh) in FACE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(36, 36)):
        pad = int(0.35 * max(fw, fh)); blur_box(img, (x - pad, y - pad, x + fw + pad, y + fh + pad), max(strength, 16))
    if max(img.size) > max_side:
        r = max_side / max(img.size); img = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
    return img

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    attach, new_groups, page_boxes = {}, {}, {}
    kept = dropped = 0
    for rf in sorted((W / 'media').glob('review_*.json')):
        items = json.loads(rf.read_text())
        if rf.stem == 'review_pages':
            for it in items: page_boxes[it['file']] = it.get('blur') or []
            continue
        for it in items:
            if not it.get('keep'): dropped += 1; continue
            src = W / it['file']
            if not src.exists(): print('missing', src); continue
            name = anon_name(it['file']); process(src, it.get('blur')).save(OUT / name, 'WEBP', quality=80); kept += 1
            rec = {'src': 'media/' + name, 'caption': it.get('caption', '')}
            brand = BRAND_OF(it.get('brand') or src.parts[src.parts.index('raw') + 1] if 'raw' in src.parts else '')
            if not brand:
                brand = BRAND_OF(rf.stem.replace('review_', ''))
            if it.get('attach_to'):
                attach.setdefault(f"{brand}/{it['attach_to']}", []).append(rec)
            elif it.get('new_element'):
                ne = it['new_element']; key = f"{brand}/{ne.get('key', 'media')}"
                g = new_groups.setdefault(key, {'brand': brand, **{k: ne.get(k, '') for k in ('type', 'subtype', 'title', 'context')}, 'media': []})
                g['media'].append(rec)
    # page captures
    pages = []
    idx_f = W / 'media' / 'pages' / 'index.json'
    for pid, pd in (json.loads(idx_f.read_text()).items() if idx_f.exists() else []):
        segs = {}
        for mode, files in pd['segments'].items():
            segs[mode] = []
            for f in files:
                rel = f'media/pages/{pid}/{f}'
                name = anon_name(rel); process(W / rel, page_boxes.get(rel, []), max_side=99999).save(OUT / name, 'WEBP', quality=78)
                segs[mode].append('media/' + name)
        pages.append({'brand': pd['brand'], 'type': pd['type'], 'subtype': pd['subtype'], 'title': pd['title'],
                      'context': pd.get('context') or 'The real page as it ran, with brand names replaced and logos, names and faces blurred. Scroll it like the live page; switch between desktop and mobile.',
                      'page': segs})
    (W / 'media' / 'media_map.json').write_text(json.dumps({'attach': attach, 'elements': list(new_groups.values()), 'pages': pages}, indent=1))
    print(f'kept {kept}, dropped {dropped}, attached to {len(attach)} elements, {len(new_groups)} new media elements, {len(pages)} pages')

if __name__ == '__main__':
    main()
