"""QA round 2 fixes."""
import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src'

def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:90]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

sub('slides/c.html', [
    ('<div class="rp-head card" style="top:330px" data-only="0"', '<div class="rp-head card" style="top:290px" data-only="0"'),
    ('<div class="vis tags" style="top:540px" data-only="0" data-a="stagger" data-d=".6">', '<div class="vis tags" style="top:480px" data-only="0" data-a="stagger" data-d=".6">'),
])
sub('slides/d.html', [
    ('<div class="hero" data-only="0" data-a="fade"><img src="img/pillar.webp" alt="" class="kb">', '<div class="hero shift" data-only="0" data-a="fade"><img src="img/pillar.webp" alt="" class="kb">'),
    ('<div class="lv-main"><div class="lv-bar"><span class="lv-dot">Live</span><span class="vl s">Webinar</span></div><img src="assets/adi-speaking.webp" alt="">',
     '<div class="lv-main"><div class="lv-bar"><span class="lv-dot">Live</span><span class="vl s">Webinar room</span></div><img src="img/onetomany.webp" alt="">'),
    ('<p>"How many invites a week?"</p><p>"Does it work for consultants?"</p><p>"Just booked a call"</p>', '<p>"Does this work for consultants?"</p><p>"Just booked a call"</p>'),
    ('<div class="tl3"><div class="tl-img"><img src="assets/adi-speaking.webp" alt=""><span class="lv-dot">Live</span></div>',
     '<div class="tl3"><div class="tl-img"><img src="img/stage.webp" alt=""><span class="lv-dot">Live</span><img class="tl-logo" src="assets/l/growth-idea.webp" alt="Growth Idea"></div>'),
    ('<div class="tl3 best"><div class="tl-img"><img src="assets/adi-speaking.webp" alt=""><span class="lv-dot">Live</span>',
     '<div class="tl3 best"><div class="tl-img"><img src="img/onetomany.webp" alt=""><span class="lv-dot">Live</span><img class="tl-logo" src="assets/l/growth-idea.webp" alt="Growth Idea">'),
    ('<div class="craft" data-a="stagger" data-d=".8" data-st=".2">', '<div class="craft" data-only="0" data-a="stagger" data-d=".8" data-st=".2">'),
    ('<p class="b w4" style="top:790px" data-step="1" data-a="rise">Would you trust an all-AI accounting firm <span class="a-e">with your taxes?</span></p>',
     '<p class="b w4" style="top:420px;font-size:72px;line-height:1.25;color:var(--text)" data-only="1" data-a="words">Would you trust an all-AI accounting firm <span class="a-e">with your taxes?</span></p>'),
])
sub('slides/e.html', [
    ('<div class="bt card" data-only="0" data-a="rise" data-d=".5"><span class="n bt-n">01</span>', '<div class="bt card" data-only="0" data-a="rise" data-d=".5"><img class="bt-img" src="img/market.webp" alt=""><span class="n bt-n">01</span>'),
    ('<div class="bt card" data-only="1" data-a="rise"><span class="n bt-n">02</span>', '<div class="bt card" data-only="1" data-a="rise"><img class="bt-img" src="img/engine.webp" alt=""><span class="n bt-n">02</span>'),
    ('<div class="bt card" data-only="2" data-a="rise"><span class="n bt-n">03</span>', '<div class="bt card" data-only="2" data-a="rise"><img class="bt-img" src="img/stage.webp" alt=""><span class="n bt-n">03</span>'),
    ('<div class="bt card" data-only="3" data-a="rise"><span class="n bt-n">04</span>', '<div class="bt card" data-only="3" data-a="rise"><img class="bt-img" src="img/calendar.webp" alt=""><span class="n bt-n">04</span>'),
    ('<section class="slide" id="s-journey" data-title="The journey, in three phases" data-bg="dim" data-steps="2" data-reel="6">', '<section class="slide" id="s-journey" data-title="The journey, in three phases" data-bg="dim" data-fx="journey" data-steps="2" data-reel="6">'),
    ('<span class="js" data-step="1" data-a="none" id="js2">Optimisation</span><i></i><span class="js" data-step="2" data-a="none" id="js3">Full ramp</span>', '<span class="js">Optimisation</span><i></i><span class="js">Full ramp</span>'),
])
sub('js/fx.js', [
    ("  /* V3: what we do, the integrations orbit */", """  /* V3: the journey stepper */
  FX.journey = {
    enter(slide) { $$('.js', slide).forEach((j, k) => j.classList.toggle('on', k === 0)); },
    step(slide, n, tl) { const js = $$('.js', slide); tl.call(() => js.forEach((j, k) => j.classList.toggle('on', k <= n)), null, .1); },
    leave(slide) { $$('.js', slide).forEach((j, k) => j.classList.toggle('on', k === 0)); }
  };

  /* V3: what we do, the integrations orbit */"""),
])
sub('v3.css', [
    ('.bt { position: absolute; left: 140px; right: 140px; top: 360px; padding: 50px 56px; display: flex; flex-direction: column; gap: 26px; }',
     '.bt { position: absolute; left: 140px; right: 140px; top: 330px; height: 600px; padding: 56px 60px; display: flex; flex-direction: column; justify-content: center; gap: 26px; overflow: hidden; }\n.bt > :not(.bt-img) { position: relative; z-index: 1; max-width: 900px; }\n.bt-img { position: absolute; right: 0; top: 0; width: 62%; height: 100%; object-fit: cover; -webkit-mask-image: linear-gradient(90deg, transparent, #000 45%); mask-image: linear-gradient(90deg, transparent, #000 45%); opacity: .9; }'),
    ('.bt .lrow { margin-top: 18px; }', '.bt .lrow { margin-top: 18px; max-width: 1100px; }'),
    ('.lv-side { display: grid; grid-template-rows: 1fr 220px; gap: 30px; min-height: 0; }', '.lv-side { display: grid; grid-template-rows: 1fr 240px; gap: 30px; min-height: 0; }'),
    ('.vis.rp { top: 560px; }', '.vis.rp { top: 540px; }\n.vis.rp.tags { gap: 20px; }\n.vis.rp .tag, #s-invite .tag { padding: 22px 34px; }'),
    ('.tl-img.evg img { object-position: 60% 50%; }', '.tl-img.evg img { object-position: 60% 50%; }\n.tl-img .tl-logo { position: absolute; left: 20px; bottom: 18px; width: auto; height: 46px; object-fit: contain; opacity: .9; }'),
])
print('fixed 2')
