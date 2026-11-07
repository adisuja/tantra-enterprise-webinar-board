#!/usr/bin/env python3
"""WhatsApp group-message replicas for the registration page's proof section (Adi, 2026-11-07).

Design: iOS WhatsApp, dark mode, an incoming group message, measured from Adi's iPhone screenshots
(1284 px wide at 3x, so 1 CSS px here is 1 iOS point and the page renders at device scale 3).
Wallpaper: WhatsApp's own chat doodle tile. Avatars: generated faces of people who do not exist.
Content: messages.json (placeholders until Adi sends real client screenshots).

usage: python3 build.py [--messages messages.json] [--out ../src/assets/img/proof] [--only N]
outputs: messages.html (all replicas on one page, for review) and one cropped webp per message.
"""
import argparse, base64, html, json, pathlib, random, re
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
W = 428  # iPhone Pro Max width in points, the size of Adi's screenshots

CSS = r"""
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #0b0b0b; }
body { width: 428px; font-family: -apple-system, 'SF Pro Text', system-ui, sans-serif; -webkit-font-smoothing: antialiased; color: #fff; }
.shot { position: relative; width: 428px; padding: 10px 0 12px; overflow: hidden; background: #0b0b0b; }
.shot::before { content: ''; position: absolute; inset: 0; background: url(WALL) 0 0 / 430px auto repeat; opacity: .04; }
.shot > * { position: relative; }
.date { display: table; margin: 2px auto 12px; padding: 3px 9px 4px; border-radius: 9px; background: #161717; color: #a8acac;
  font-size: 12.5px; font-weight: 600; letter-spacing: .1px; }
.row { position: relative; padding-left: 44px; padding-right: 60px; }
.av { position: absolute; left: -36px; bottom: -1px; width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.bub { position: relative; display: inline-block; max-width: 324px; min-width: 120px; padding: 4px 11px 4.6px; border-radius: 8px 8px 8px 0;
  background: #232626; box-shadow: 0 1px 1.5px rgba(0, 0, 0, .35); }
.tail { position: absolute; left: -6px; bottom: 0; width: 7px; height: 13px; }
.hd { display: flex; align-items: baseline; justify-content: space-between; gap: 14px; height: 16px; line-height: 16px; }
.nm { font-size: 13px; font-weight: 600; letter-spacing: -.1px; white-space: nowrap; }
.nm .tl { margin-right: 2px; }
.ph { font-size: 10.8px; color: #919393; white-space: nowrap; }
.ph i { font-style: normal; filter: blur(2.2px); }
.tx { font-size: 15.4px; line-height: 20px; letter-spacing: -.2px; padding-top: 1.2px; word-wrap: break-word; }
.tx .sp { display: inline-block; width: 56px; height: 1px; }
.tm { position: absolute; right: 10.7px; bottom: 5.5px; font-size: 10.2px; color: #919393; letter-spacing: 0; }
.rx { position: relative; display: inline-flex; align-items: center; gap: 2.2px; margin: -7.2px 0 0 11px; height: 24px; padding: 0 7px 0 6.5px;
  border-radius: 12px; background: #242626; box-shadow: 0 0 0 1px #0a0a0a; }
.rx b { font-weight: 400; font-size: 17px; line-height: 1; }
.rx span { font-size: 14.2px; color: #949696; margin-left: 4.5px; }
.tx .e { font-size: 1.25em; line-height: 0; vertical-align: -1px; }
"""

TAIL = '<svg class="tail" viewBox="0 0 7 13" aria-hidden="true"><path d="M7 0 V13 H0.6 C0.1 13 -0.1 12.4 0.3 12.1 C3.6 9.9 6.4 6.2 7 0 Z" fill="#232626"/></svg>'


EMOJI = re.compile('([\U0001F000-\U0001FAFF\u2600-\u27BF](?:\uFE0F)?(?:\u200D[\U0001F000-\U0001FAFF\u2600-\u27BF]\uFE0F?)*)')


def emoji(t):
    # iOS draws emoji inside a message about a quarter larger than the text around them.
    return EMOJI.sub(r'<span class="e">\1</span>', t)


def masked(rng):
    # The rest of the number is blurred, as in Adi's screenshots: random digits, never a real number.
    return f'{rng.randint(200, 989)}-{rng.randint(1000, 9999)}'


def message_html(m, i, avatars):
    rng = random.Random(f'wa-{i}')
    who = (f'<span class="nm" style="color:{m["color"]}"><span class="tl">~</span>{html.escape(m["name"])}</span>'
           f'<span class="ph">{html.escape(m["phone"])} <i>{masked(rng)}</i></span>') if m.get('name') else \
          f'<span class="nm" style="color:{m["color"]}">{html.escape(m["phone"])} <i style="font-style:normal;filter:blur(2.4px)">{masked(rng)}</i></span>'
    rx = ''
    if m.get('reactions'):
        rx = '<div class="rx">' + ''.join(f'<b>{e}</b>' for e in m['reactions']) + (f'<span>{m["count"]}</span>' if m.get('count', 0) > 1 else '') + '</div>'
    date = f'<div class="date">{html.escape(m["date"])}</div>' if m.get('date') else ''
    return (f'<section class="shot" id="m{i}">{date}<div class="row{" has-rx" if rx else ""}">'
            f'<div class="bub"><img class="av" src="{avatars[m["avatar"]]}" alt="">{TAIL}<div class="hd">{who}</div>'
            f'<div class="tx">{emoji(html.escape(m["text"].replace("\'", "\u2019")))}<span class="sp"></span></div><span class="tm">{html.escape(m["time"])}</span></div>'
            f'{"<br>" + rx if rx else ""}</div></section>')


def page(msgs):
    wall = 'data:image/webp;base64,' + base64.b64encode((HERE / 'assets' / 'chat-wallpaper.webp').read_bytes()).decode()
    avatars = {p.stem: 'data:image/jpeg;base64,' + base64.b64encode(p.read_bytes()).decode() for p in (HERE / 'avatars').glob('*.jpg')}
    body = '\n'.join(message_html(m, i, avatars) for i, m in enumerate(msgs))
    return (f'<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>WhatsApp replicas</title>'
            f'<style>{CSS.replace("WALL", wall)}</style></head><body>{body}</body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--messages', default=str(HERE / 'messages.json'))
    ap.add_argument('--out', default=str(HERE.parent / 'src' / 'assets' / 'img' / 'proof'))
    ap.add_argument('--html', default=str(HERE / 'messages.html'))
    ap.add_argument('--scale', type=float, default=3)
    a = ap.parse_args()
    msgs = json.loads(pathlib.Path(a.messages).read_text())['messages']
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    doc = pathlib.Path(a.html); doc.write_text(page(msgs))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': 900}, device_scale_factor=a.scale)
        pg.goto(doc.resolve().as_uri(), wait_until='load'); pg.wait_for_timeout(500)
        sizes = []
        for i in range(len(msgs)):
            el = pg.locator(f'#m{i}')
            f = out / f'wa-{i + 1:02d}.webp'
            png = el.screenshot()
            from PIL import Image
            import io
            im = Image.open(io.BytesIO(png)).convert('RGB')
            im.save(f, 'WEBP', quality=90, method=6)
            m = msgs[i]
            sizes.append({'file': f.name, 'w': im.size[0], 'h': im.size[1],
                          'alt': f'WhatsApp message from {m.get("name") or "a client"}: {m["text"]}'})
        b.close()
    (HERE / 'manifest.json').write_text(json.dumps(sizes, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps([s['file'] for s in sizes]))


if __name__ == '__main__':
    main()
