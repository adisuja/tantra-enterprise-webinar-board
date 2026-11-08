"""Capture real client pages as anonymised, scrollable screenshots for the library.

For each page in _work/pages.json: load it in Chromium (live URL or a Wayback 'if_' snapshot), scroll to load
everything, then in the page itself replace every brand, person and client name with a placeholder (the same lists the
text anonymiser uses), blank out emails, phone numbers and URLs, and blur logos and brand imagery (header, footer, logo
strips, images whose name says logo or brand). Then take full-page screenshots at desktop and mobile width, blur any
face OpenCV finds, and cut each into 2,400 px tall WebP segments.

Output (PRIVATE until reviewed): _work/media/pages/<id>/{desktop,mobile}-NN.webp and _work/media/pages/index.json
usage: python3 tools/capture_pages.py [page_id ...]
"""
import json, pathlib, re, sys
import cv2, numpy as np
from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / '_work'
sys.path.insert(0, str(ROOT / 'tools'))
import anonymise  # noqa: E402

FACE = cv2.CascadeClassifier(str(W / 'models' / 'face.xml'))
SEG = 2400
EXTRA = [('Databricks', '[Data Platform]'), ('Snowflake', '[Alternative Platform]'), ('Photon', '[Premium Engine]')]

def sub_list():
    out = []
    for rx, label, find in anonymise.compile_subs():
        out.append({'p': rx.pattern, 'f': 'gi' if rx.flags & re.I else 'g', 'l': label})
    for find, label in EXTRA:   # niche platform names that point to the client (same rule as the element fix pass)
        out.append({'p': r'(?<![A-Za-z0-9])' + re.escape(find) + r'(?![A-Za-z0-9])', 'f': 'gi', 'l': label})
    return out

ANON_JS = r"""
(subs) => {
  const rx = subs.map(s => [new RegExp(s.p.replace(/\(\?<!\[A-Za-z0-9\]\)/g, '(?<![A-Za-z0-9])').replace(/\(\?!\[A-Za-z0-9\]\)/g, '(?![A-Za-z0-9])'), s.f), s.l]);
  const extra = [[/[\w.+-]+@[\w-]+(\.[\w-]+)+/g, '[Email]'], [/\+?\d[\d ()-]{8,}\d/g, '[Phone]'], [/\b(?:https?:\/\/|www\.)\S+/gi, '[Link]']];
  const fix = (t) => { for (const [r, l] of rx) t = t.replace(r, l); for (const [r, l] of extra) t = t.replace(r, l); return t; };
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) { const v = fix(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; }
  document.querySelectorAll('input,textarea').forEach(e => { if (e.placeholder) e.placeholder = fix(e.placeholder); if (e.value) e.value = fix(e.value); });
  document.title = fix(document.title);
  // blur brand imagery: header/nav/footer graphics, logo strips, anything named logo/brand/partner/client
  const css = document.createElement('style');
  css.textContent = '.__anon_blur{filter:blur(14px)!important}';
  document.head.appendChild(css);
  const isLogo = (el) => /logo|brand|partner|client|award|badge|press|featured|trust/i.test([el.alt, el.src, el.className, el.id, el.getAttribute('aria-label') || ''].join(' '));
  document.querySelectorAll('img,svg,picture,video,iframe').forEach(el => {
    const r = el.getBoundingClientRect(); const inChrome = el.closest('header,nav,footer,[class*=header],[class*=footer],[class*=logo],[class*=brand]');
    const small = r.height > 0 && r.height < 140 && r.width / Math.max(1, r.height) > 1.6;
    if (inChrome || isLogo(el) || small || el.tagName === 'IFRAME' || el.tagName === 'VIDEO') el.classList.add('__anon_blur');
  });
  document.querySelectorAll('[style*="background-image"]').forEach(el => { if (isLogo(el) || el.closest('header,nav,footer')) el.classList.add('__anon_blur'); });
  // cookie banners and chat widgets hide the page
  document.querySelectorAll('[id*=cookie],[class*=cookie],[id*=consent],[class*=consent],[id*=intercom],[class*=chat-widget],#wm-ipp-base,#wm-ipp,#donato').forEach(e => e.remove());
  return document.body.innerText.length;
}
"""

def blur_faces(img):
    a = cv2.cvtColor(np.array(img.convert('RGB')), cv2.COLOR_RGB2GRAY)
    faces = FACE.detectMultiScale(a, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
    for (x, y, w, h) in faces:
        pad = int(0.35 * max(w, h)); box = (max(0, x - pad), max(0, y - pad), min(img.width, x + w + pad), min(img.height, y + h + pad))
        img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(18)), box[:2])
    return img, len(faces)

def capture(page_def, browser):
    out = W / 'media' / 'pages' / page_def['id']; out.mkdir(parents=True, exist_ok=True)
    res = {'id': page_def['id'], 'segments': {}, 'faces': 0}
    for mode, vp in (('desktop', {'width': 1440, 'height': 900}), ('mobile', {'width': 390, 'height': 844})):
        ctx = browser.new_context(viewport=vp, device_scale_factor=1, is_mobile=(mode == 'mobile'), user_agent=None)
        pg = ctx.new_page()
        pg.goto(page_def['url'], wait_until='domcontentloaded', timeout=90000)
        pg.wait_for_timeout(3500)
        h = pg.evaluate('document.body.scrollHeight')
        for y in range(0, h, 700):
            pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(120)
        pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(800)
        pg.evaluate(ANON_JS, SUBS)
        pg.wait_for_timeout(400)
        shot = out / f'{mode}-full.png'
        pg.screenshot(path=str(shot), full_page=True)
        ctx.close()
        img = Image.open(shot)
        img, nf = blur_faces(img); res['faces'] += nf
        segs = []
        for i, top in enumerate(range(0, img.height, SEG)):
            part = img.crop((0, top, img.width, min(img.height, top + SEG)))
            f = out / f'{mode}-{i + 1:02d}.webp'; part.save(f, 'WEBP', quality=78); segs.append(f.name)
        shot.unlink()
        res['segments'][mode] = segs; res[mode + '_size'] = [img.width, img.height]
    return res

if __name__ == '__main__':
    pages = json.loads((W / 'pages.json').read_text())
    only = set(sys.argv[1:])
    SUBS = sub_list()
    idx_f = W / 'media' / 'pages' / 'index.json'
    idx = json.loads(idx_f.read_text()) if idx_f.exists() else {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for pd in pages:
            if only and pd['id'] not in only: continue
            try:
                r = capture(pd, b); idx[pd['id']] = {**pd, **r}
                print(pd['id'], {k: len(v) for k, v in r['segments'].items()}, 'faces', r['faces'])
            except Exception as e:
                print('FAIL', pd['id'], e)
        b.close()
    idx_f.parent.mkdir(parents=True, exist_ok=True)
    idx_f.write_text(json.dumps(idx, indent=1))
