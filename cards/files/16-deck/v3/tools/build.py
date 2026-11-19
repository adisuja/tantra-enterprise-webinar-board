"""Assemble the V3 deck: deck/index.html with Inter, Instrument Serif and the platform logo sprite inlined, QR codes, a copy lint,
and deck/files.json listing every image the page references (for publishing)."""
import base64, json, os, re
import segno

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT, TOOLS = ROOT + '/src', ROOT + '/deck', ROOT + '/tools'
BOOK = 'https://crm.usetantra.com/book/tantra/ai-revops-strategy-consultation?utm_source=webinar_deck'
# The link printed on the CTA slides. Swap in the short link once it exists, e.g. 'sellwithtantra.com/call'.
BOOK_SHOW = 'crm.usetantra.com/book/tantra/<br>ai-revops-strategy-consultation'
PARTS = ('a0', 'a', 'b', 'c', 'd', 'e')

def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode()

def fonts():
    # Light theme (round 9): Inter for everything, Instrument Serif italic for the accent words, as on usetantra.com/salesmaster
    return ('@font-face{font-family:"Inter";src:url(data:font/woff2;base64,%s) format("woff2");font-weight:100 900;font-style:normal;font-display:block}\n'
            '@font-face{font-family:"Instrument Serif";src:url(data:font/woff2;base64,%s) format("woff2");font-weight:400;font-style:italic;font-display:block}'
            % (b64(f'{TOOLS}/inter-latin-var.woff2'), b64(f'{TOOLS}/instrument-serif-latin-italic.woff2')))

# The living logo (head, branches and the signal layer that js/logo.js draws over them)
LOGO = ('<span class="tl2" aria-hidden="true"><span class="tl2-aura"></span><img class="tl2-head" src="assets/logo/head2.webp" alt="">'
        '<img class="tl2-br" src="assets/logo/branches2.webp" alt=""></span>')

def qr_block():
    q = segno.make(BOOK, error='m')
    m = q.matrix
    n = len(m)
    d = ''.join(f'M{x} {y}h1v1h-1z' for y, row in enumerate(m) for x, v in enumerate(row) if v)
    b = 2
    return ('<div class="qr-wrap" data-a="zoom" data-d=".5"><div class="qr-corners"><i></i><i></i><i></i><i></i></div>'
            f'<svg viewBox="{-b} {-b} {n + 2 * b} {n + 2 * b}" shape-rendering="crispEdges" role="img" aria-label="QR code to book your AI RevOps Strategy Consultation">'
            f'<rect x="{-b}" y="{-b}" width="{n + 2 * b}" height="{n + 2 * b}" fill="#f6f5fc"/><path d="{d}" fill="#14121f"/></svg>'
            '<span class="qr-lbl">Scan to book your call</span><div class="qr-scan"></div></div>')

BANNED = ['unlock', 'leverage', 'seamless', 'game-changer', 'game changer', 'delve', 'elevate', 'supercharge', 'revolutioniz', 'harness', 'robust',
          'cutting-edge', 'empower', 'synergy', 'holistic', 'transformative', "in today's", 'paradigm', 'unleash', 'skyrocket', 'next-level',
          'world-class', 'effortless', 'tapestry', 'embark', 'testament', 'guarantee', 'no pitch', '100% free', '$50m']

def lint(page):
    text = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', ' ', page, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    out = [f'{n} found {page.count(c)}x' for c, n in (('–', 'en dash'), ('—', 'em dash')) if c in page]
    low = text.lower()
    for w in BANNED:
        for m in re.finditer(re.escape(w), low):
            i = m.start()
            out.append(f'banned "{w}": ...{text[max(0, i - 60):i + 60]}...')
    return out

def main():
    import subprocess, sys
    subprocess.run([sys.executable, TOOLS + '/logo3.py'], check=True); subprocess.run([sys.executable, TOOLS + '/r10.py'], check=True)
    css = '\n'.join(open(f'{SRC}/{f}').read() for f in ('style.css', 'slides.css', 'v3.css', 'light.css', 'r10.css', 'premium.css', 'ios.css'))
    slides = ''.join(open(f'{SRC}/slides/{p}.html').read() for p in PARTS)
    slides = slides.replace('{{BOOK_SHOW}}', BOOK_SHOW).replace('{{BOOK}}', BOOK).replace('{{QR}}', qr_block()).replace('{{LOGO}}', LOGO)
    n = slides.count('<section class="slide')
    sprite = open(SRC + '/logos.svg').read()
    js = '\n'.join(open(f'{SRC}/js/{f}.js').read() for f in ('field', 'gl', 'fx', 'flow', 'engine', 'logo', 'logo3'))
    routes = open(SRC + '/logo-routes.json').read().strip()
    page = f'''<title>Tantra Enterprise Webinar Deck</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="How 400+ brands use AI funnels to generate $100K to $300K monthly: the live workshop deck.">
<style>
{fonts()}
{css}
</style>
{sprite}
<div id="app">
  <div id="stage" aria-roledescription="slide deck" aria-label="How 400+ brands use AI funnels">
    <canvas id="field" aria-hidden="true"></canvas>
{slides}
    <div id="sweep" aria-hidden="true"></div>
    <div id="hud" aria-hidden="true">
      <span class="hudlogo"><img class="mk" src="assets/logo/tantra-logo.webp" alt=""><span class="wd">Tantra</span></span>
      <span class="pos"><span class="pos-mark"><svg viewBox="0 0 24 24"><path d="M12 3l1.8 5.6L19.5 10l-5.7 1.6L12 17l-1.8-5.4L4.5 10l5.7-1.4z"/></svg></span><span class="pos-a">The world's first</span><span class="pos-b">End-to-end AI RevOps orchestration system</span></span>
      <span class="count">1</span>
    </div>
    <div id="grain" aria-hidden="true"></div>
  </div>
  <nav id="ui" aria-label="Deck controls">
    <button id="b-prev" type="button" aria-label="Previous"><svg viewBox="0 0 24 24"><polyline points="15,5 8,12 15,19"/></svg></button>
    <span class="ct" aria-live="polite">1 / {n}</span>
    <button id="b-next" type="button" aria-label="Next"><svg viewBox="0 0 24 24"><polyline points="9,5 16,12 9,19"/></svg></button>
    <button id="b-notes" type="button" aria-pressed="false"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg><span class="lb">Notes</span></button>
    <button id="b-grid" type="button" aria-pressed="false"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg><span class="lb">Slides</span></button>
    <button id="b-reel" type="button" aria-pressed="false"><svg viewBox="0 0 24 24"><polygon points="7,4 20,12 7,20"/></svg><span class="lb">Reel</span></button>
    <button id="b-full" type="button"><svg viewBox="0 0 24 24"><polyline points="4,9 4,4 9,4"/><polyline points="15,4 20,4 20,9"/><polyline points="20,15 20,20 15,20"/><polyline points="9,20 4,20 4,15"/></svg><span class="lb">Full screen</span></button>
  </nav>
  <section id="notes" hidden aria-label="Speaker notes"></section>
  <section id="grid" hidden aria-label="All slides"><h3>All {n} slides</h3><ol></ol></section>
  <div id="help" hidden><b>Right arrow, Space</b> next · <b>Left arrow</b> back<br><b>N</b> notes · <b>G</b> all slides<br><b>R</b> reel · <b>F</b> full screen<br><b>B</b> black screen · <b>H</b> help</div>
  <div id="black" hidden></div>
</div>
<script type="application/json" id="tl-routes">{routes}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script>
{js}
</script>
'''
    probs = lint(page)
    open(OUT + '/index.html', 'w').write(page)
    refs = sorted(set(re.findall(r'(?:src|data-gl)="((?:img|assets)/[^"]+)"', page)))
    missing = [r for r in refs if not os.path.exists(OUT + '/' + r)]
    json.dump({r: r for r in refs if r not in missing}, open(OUT + '/files.json', 'w'), indent=0)
    tot = sum(os.path.getsize(OUT + '/' + r) for r in refs if r not in missing)
    print(f'slides: {n} | page: {len(page) / 1024:.0f} KB | files: {len(refs)} ({tot / 1024 / 1024:.1f} MB) | builds: {sum(int(x) for x in re.findall(chr(100) + "ata-steps=.(\\d+)", page))}')
    for m in missing: print('MISSING', m)
    for p in probs: print('LINT', p)

if __name__ == '__main__':
    main()
