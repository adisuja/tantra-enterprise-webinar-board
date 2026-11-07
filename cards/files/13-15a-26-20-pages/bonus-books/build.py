#!/usr/bin/env python3
"""Cover pages for the two live workshop bonuses (Adi, 2026-11-08).

Each cover is a full page (1600 x 2400, a 2:3 book page): Kie.ai artwork (art/, generated with no text; prompts in
gen_art.py) under HTML type, so the titles are exact. One cover per book per palette: 'a' is the original purple page,
'b' the new palette.

usage: python3 build.py
outputs: covers.html (all four, for review) and ../src/assets/img/bonus/<book>-<palette>.webp (800 x 1200) plus the full 1600 x 2400 page in bonus/full/
"""
import pathlib
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
IMG = HERE.parent / 'src' / 'assets' / 'img'
OUT = IMG / 'bonus'
W, H = 1600, 2400

BOOKS = {
    'playbook': {'no': '01', 'kicker': 'The $1MN+', 'title': ['B2B RevOps', 'Playbook'],
                 'sub': 'The exact blueprint we use to build high-converting RevOps processes & funnels.'},
    'prompts': {'no': '02', 'kicker': 'The $1MN+', 'title': ['AI Funnel', 'Prompt', 'Library'],
                'sub': 'The prompts we use to engineer over 100+ RevOps funnel elements using AI.'},
}
# accent: kicker box and rule; ink: text on the kicker box
PAL = {
    ('playbook', 'a'): {'accent': '#a78bfa', 'ink': '#0b0d12', 'glow': 'rgba(109,74,255,.55)'},
    ('prompts', 'a'): {'accent': '#ffffff', 'ink': '#2a1a7a', 'glow': 'rgba(201,188,252,.5)'},
    ('playbook', 'b'): {'accent': '#0297de', 'ink': '#02070a', 'glow': 'rgba(2,151,222,.5)'},
    ('prompts', 'b'): {'accent': '#fc734d', 'ink': '#02070a', 'glow': 'rgba(252,115,77,.5)'},
}

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #222; }
.cv { position: relative; width: 1600px; height: 2400px; overflow: hidden; color: #fff; font-family: 'Inter', sans-serif; background: #000 center / cover no-repeat; }
.cv::before { content: ''; position: absolute; inset: 0; background:
  linear-gradient(180deg, rgba(0,0,0,.42) 0%, rgba(0,0,0,0) 48%, rgba(0,0,0,0) 78%, rgba(0,0,0,.5) 100%),
  radial-gradient(120% 80% at 50% 50%, transparent 60%, rgba(0,0,0,.35) 100%); }
.cv::after { content: ''; position: absolute; inset: 64px; border: 2px solid rgba(255,255,255,.16); border-radius: 18px; }
.in { position: absolute; inset: 64px; padding: 96px 104px; display: flex; flex-direction: column; z-index: 1; }
.top { display: flex; justify-content: space-between; align-items: center; }
.no { font: 600 34px/1 'JetBrains Mono', monospace; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.78); }
.no b { color: var(--accent); font-weight: 700; }
.logo { display: flex; align-items: center; gap: 16px; }
.logo img:first-child { height: 84px; } .logo img:nth-child(2) { height: 46px; }
.logo sup { font: 500 34px/1 'Inter', sans-serif; color: rgba(255,255,255,.85); margin-left: 2px; align-self: flex-start; margin-top: 6px; }
.kick { display: inline-block; margin-top: 190px; padding: 10px 26px 14px; background: var(--accent); color: var(--ink); border-radius: 12px;
  font: 800 92px/1 'Archivo', sans-serif; font-stretch: 75%; letter-spacing: .01em; text-transform: uppercase; align-self: flex-start;
  box-shadow: 0 20px 60px -10px var(--glow); }
h1 { margin-top: 34px; font: 900 238px/.86 'Archivo', sans-serif; font-stretch: 72%; letter-spacing: -.012em; text-transform: uppercase;
  text-shadow: 0 10px 60px rgba(0,0,0,.45); }
h1 span { display: block; }
.rule { width: 160px; height: 8px; border-radius: 4px; background: var(--accent); margin-top: 56px; box-shadow: 0 0 30px var(--glow); }
.sub { margin-top: 40px; max-width: 980px; font: 500 46px/1.32 'Inter', sans-serif; letter-spacing: -.01em; color: rgba(255,255,255,.86); }
.cv--long .kick { margin-top: 120px; }
.cv--long h1 { font-size: 214px; margin-top: 28px; }
.cv--long .rule { margin-top: 44px; }
.cv--long .sub { margin-top: 32px; }
.sub { text-shadow: 0 2px 24px rgba(0,0,0,.6); }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; font: 600 30px/1 'JetBrains Mono', monospace;
  letter-spacing: .12em; text-transform: uppercase; color: rgba(255,255,255,.7); }
"""


def cover(book, pal):
    b, c = BOOKS[book], PAL[(book, pal)]
    art = f'art/{book}-{pal}.webp'
    mark, word = '../src/assets/img/tantra-mark-white.png', '../src/assets/img/tantra-word-white.png'
    return f"""<section class="cv{' cv--long' if len(b['title']) > 2 else ''}" id="{book}-{pal}" style="background-image:url({art});--accent:{c['accent']};--ink:{c['ink']};--glow:{c['glow']}">
  <div class="in">
    <div class="top"><p class="no">Bonus <b>{b['no']}</b></p><p class="logo"><img src="{mark}" alt=""><img src="{word}" alt="Tantra"><sup>&copy;</sup></p></div>
    <p class="kick">{b['kicker']}</p>
    <h1>{''.join(f'<span>{t}</span>' for t in b['title'])}</h1>
    <div class="rule"></div>
    <p class="sub">{b['sub'].replace('&', '&amp;')}</p>
    <div class="foot"><span>usetantra.com</span><span>&copy; 2026 Tantra</span></div>
  </div>
</section>"""


def main():
    ids = [(bk, p) for p in ('a', 'b') for bk in BOOKS]
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Bonus covers</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,700..900&family=Inter:wght@500;600;800&family=JetBrains+Mono:wght@600;700&display=swap">'
            f'<style>{CSS}</style></head><body>' + '\n'.join(cover(*i) for i in ids) + '</body></html>')
    doc = HERE / 'covers.html'; doc.write_text(html)
    (OUT / 'full').mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto(doc.resolve().as_uri(), wait_until='networkidle'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(600)
        for bk, pl in ids:
            import io
            im = Image.open(io.BytesIO(pg.locator(f'#{bk}-{pl}').screenshot())).convert('RGB')
            im.save(OUT / 'full' / f'{bk}-{pl}.webp', 'WEBP', quality=92, method=6)  # the full page, 1600 x 2400
            im.resize((800, 1200), Image.LANCZOS).save(OUT / f'{bk}-{pl}.webp', 'WEBP', quality=90, method=6)
        b.close()
    print('wrote', [f'{bk}-{pl}' for bk, pl in ids])


if __name__ == '__main__':
    main()
