"""Round 8: real-speed browser walk. Text and art never share space; crowded layouts get room."""
import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src'
def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:100]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

sub('slides/a.html', [
    ('<p class="b" style="top:540px;width:820px" data-only="0" data-a="rise" data-d=".6">', '<p class="b" style="top:540px;width:640px" data-only="0" data-a="rise" data-d=".6">'),
])
sub('slides/e.html', [
    ('<h2 class="t c" style="top:30%" data-a="words" data-d=".3">', '<h2 class="t" style="top:300px;width:860px" data-a="words" data-d=".3">'),
    ('<p class="b" style="top:700px;left:140px;right:140px;width:auto;text-align:center" data-a="rise" data-d="1.4">', '<p class="b" style="top:620px;width:760px" data-a="rise" data-d="1.4">'),
    ('<div class="gift-mini" style="top:870px"', '<div class="gift-mini" style="top:858px"'),
])
css = open(f'{S}/v3.css').read()
css += '''
/* ---------- round 8: checked in a real browser at real speed ---------- */
/* the art sits in the right part of the slide, faded in, so no text lies on top of it */
#s-cover .hero, #s-feast .hero, #s-nodial .hero, #s-offer .hero, #s-fan .hero, #s-craft .hero, #s-journey .hero, #s-gpt .hero, #s-wait .hero {
  left: var(--hl, 50%); background: none; -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 24%); mask-image: linear-gradient(90deg, transparent 0, #000 24%); }
#s-cover .hero { --hl: 63%; } #s-feast .hero { --hl: 58%; } #s-nodial .hero { --hl: 52%; } #s-offer .hero { --hl: 54%; }
#s-fan .hero { --hl: 52%; } #s-craft .hero { --hl: 56%; } #s-journey .hero { --hl: 56%; } #s-gpt .hero { --hl: 54%; } #s-wait .hero { --hl: 40%; }
#s-feast .hero.shift img, #s-nodial .hero.shift img { left: 0; width: 100%; }
#s-feast .hero.shift::before, #s-nodial .hero.shift::before { display: none; }
#s-cover .hero .shade, #s-feast .hero .shade, #s-nodial .hero .shade, #s-offer .hero .shade, #s-fan .hero .shade, #s-craft .hero .shade, #s-journey .hero .shade, #s-gpt .hero .shade, #s-wait .hero .shade { display: none; }
#s-fan .b.w4 { width: 860px; }
#s-craft .b.w4 { width: 900px; }
#s-craft .card { max-width: 900px; }
#s-brain .mosaic { -webkit-mask-image: linear-gradient(90deg, transparent 0, transparent 42%, #000 72%); mask-image: linear-gradient(90deg, transparent 0, transparent 42%, #000 72%); }
/* slide 11: subtitle, tiles and labels each get their own band */
.gifts { top: 440px; }
.g-img { height: 320px; }
.gift .vk { font-size: 40px; }
/* slide 15: title clear of the image row, labels clear of the footer */
.camps { top: 370px; }
.c-img { height: 330px; }
/* slide 28: count, sample site and footnote each have room */
.mpanel { top: 345px; height: 585px; }
.mp-grid { max-height: 136px; overflow: hidden; }
.mp-site .br-bar { height: 52px; }
.mp-site.cut-state .ms-h { font-size: 36px; }
.mp-site.cut-state .verdict { padding: 16px 24px; margin-top: 10px; }
.mp-site { top: 208px; bottom: 26px; }
.mp-site .ms-h { font-size: 40px; }
.mp-site .ms-body { height: auto; padding: 24px 32px; gap: 12px; }
.mp-site .ms-p { font-size: 34px; }
.mp-grid { gap: 6px; }
.mp-site.cut-state .ms-p { display: none; }
.mp-site.cut-state .verdict { position: relative; left: auto; right: auto; bottom: auto; margin: 18px 26px 0; }
.mp-own { bottom: 30px; padding: 24px 32px; }
/* slide 34: the numbers sit under the quote, not on it */
.tq2-q { font-size: 34px; }
.rmets { top: 800px; }
/* slide 56: count label clear of the seat grid */
.room-g { margin-top: 26px; }
/* slide 58: text column ends before the loop */
.loop-left { width: 800px; }
/* slide 68: last month label inside the frame */
.yr-axis span:last-child { transform: translateX(-70%); }
/* slide 23: KPI pills on one line */
.s6c .s6-k { white-space: nowrap; font-size: 25px; padding: 6px 10px; }
/* slide 73: bonus strip clear of the footer */
.gift-mini img { height: 100px; }
'''
open(f'{S}/v3.css', 'w').write(css)
print('round 8 applied')
