"""QA round 3 fixes."""
import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src'

def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:90]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

sub('v3.css', [
    ('.fan { position: absolute; left: 1100px; top: 200px; width: 760px; height: 760px; }', '.fan { position: absolute; left: 1080px; top: 200px; width: 760px; height: 760px; }'),
    ('.fan img { position: absolute; left: calc(var(--x) * .9); top: calc(var(--y) * 1.6); width: 440px;', '.fan img { position: absolute; left: calc(var(--x) * .75); top: calc(var(--y) * 1.6); width: 420px;'),
    ('.g-img { height: 470px; border-radius: 26px; background: radial-gradient(80% 80% at 50% 40%, rgba(109,74,255,.35), rgba(18,20,29,.95)); border: 1px solid var(--line-2); display: grid; place-items: center; overflow: hidden; }',
     '.g-img { height: 470px; border-radius: 26px; background: radial-gradient(80% 80% at 50% 40%, rgba(109,74,255,.35), rgba(18,20,29,.95)); border: 1px solid var(--line-2); display: flex; align-items: center; justify-content: center; overflow: hidden; }'),
    ('.g-img img { height: 88%; width: auto; border-radius: 10px; box-shadow: 0 24px 60px rgba(0,0,0,.6); }', '.g-img img { height: auto; width: auto; max-height: 88%; max-width: 86%; border-radius: 10px; box-shadow: 0 24px 60px rgba(0,0,0,.6); }'),
    ('.g-img.wide img { width: 100%; height: 100%; object-fit: cover; border-radius: 0; box-shadow: none; }', '.g-img.wide img { width: 100%; height: 100%; max-width: none; max-height: none; object-fit: cover; border-radius: 0; box-shadow: none; }'),
    ('.lvroom { position: absolute; left: 140px; right: 140px; top: 330px; height: 560px; display: grid; grid-template-columns: 1fr 520px; grid-template-rows: 560px; gap: 30px; }',
     '.lvroom { position: absolute; left: 140px; right: 140px; top: 330px; height: 560px; display: grid; grid-template-columns: 1fr 560px; grid-template-rows: 560px; gap: 30px; }'),
    ('.lv-side { display: grid; grid-template-rows: 1fr 240px; gap: 30px; min-height: 0; }', '.lv-side { display: grid; grid-template-rows: 1fr 210px; gap: 30px; min-height: 0; }'),
])
sub('slides/d.html', [
    ('<div class="lv-calls card"><span class="vl s">Calls booked · Growth Idea, best webinar</span>', '<div class="lv-calls card"><span class="vl s">Calls booked, live</span>'),
    ('<span class="cap m" data-only="0" data-a="fade" data-d="1.8">Measured · Growth Idea, best webinar, 28 Aug 2025</span>', '<span class="cap m" data-a="fade" data-d="1.8">Measured · Growth Idea, best webinar, 28 Aug 2025</span>'),
])
print('fixed 3')
