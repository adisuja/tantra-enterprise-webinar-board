"""QA round 1 fixes."""
import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src'

def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:80]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

sub('slides/a.html', [
    ('AI can now do what used to take <span class="a">large teams</span> and constant manual effort.', 'AI can now do what used to take <span class="a">large teams.</span>'),
    ('<h2 class="t w4" data-a="words">The problem? Most founders don\'t know <span class="a">how to turn it into a system.</span></h2>',
     '<h2 class="t" style="width:1180px" data-a="words">Most founders don\'t know how to turn it <span class="a">into a system.</span></h2>'),
    ('<p class="b w4" style="top:470px" data-a="rise" data-d=".8">The invite, the page, the WhatsApp reminders, this room.</p>',
     '<p class="b" style="top:470px;width:900px" data-a="rise" data-d=".8">The invite, the page, the WhatsApp reminders, this room.</p>'),
    ('<h2 class="t" style="width:1000px" data-a="words">Higher ticket. Already making revenue.', '<h2 class="t" style="width:930px" data-a="words">Higher ticket. Already making revenue.'),
    ('<section class="slide" id="s-feast" data-title="Feast or famine" data-bg="dim" data-reel="8">\n  <div class="hero"', '<section class="slide" id="s-feast" data-title="Feast or famine" data-bg="dim" data-reel="8">\n  <div class="hero shift"'),
    ('<section class="slide" id="s-trial" data-title="Problem 3: Endless trial and error" data-bg="dim" data-reel="7">\n  <div class="hero"', '<section class="slide" id="s-trial" data-title="Problem 3: Endless trial and error" data-bg="dim" data-reel="7">\n  <div class="hero shift"'),
    ('<section class="slide" id="s-nodial" data-title="Nothing connects, nothing compounds" data-bg="dim" data-reel="8">\n  <div class="hero"', '<section class="slide" id="s-nodial" data-title="Nothing connects, nothing compounds" data-bg="dim" data-reel="8">\n  <div class="hero shift"'),
    ('<p class="b" style="top:480px;width:900px" data-a="rise" data-d=".6">Not enough consistent,', '<p class="b" style="top:480px;width:780px" data-a="rise" data-d=".6">Not enough consistent,'),
    ('<p class="b" style="top:480px;width:900px" data-a="rise" data-d=".6">Even when you get calls,', '<p class="b" style="top:480px;width:780px" data-a="rise" data-d=".6">Even when you get calls,'),
    ('<p class="b" style="top:560px;width:900px" data-a="rise" data-d=".6">Testing random tactics.', '<p class="b" style="top:560px;width:780px" data-a="rise" data-d=".6">Testing random tactics.'),
])
sub('slides/b.html', [
    ('<div class="lrow" style="position:absolute;left:140px;top:500px" data-a="stagger" data-d=".8" data-st=".12">\n    <span class="lchip">', '<div class="lrow" style="position:absolute;left:140px;top:520px" data-a="stagger" data-d=".8" data-st=".12">\n    <span class="lchip big">'),
    ('<span class="lchip"><svg class="lgi"><use href="#lg-linkedin"/></svg>Their LinkedIn</span>', '<span class="lchip big"><svg class="lgi"><use href="#lg-linkedin"/></svg>Their LinkedIn</span>'),
    ('<span class="lchip"><svg class="lgi g" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18"/></svg>Their website</span>', '<span class="lchip big"><svg class="lgi g" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18"/></svg>Their website</span>'),
    ('<p class="b w4" style="top:560px" data-a="rise" data-d="1">If your top of funnel', '<p class="b" style="top:560px;width:860px" data-a="rise" data-d="1">If your top of funnel'),
])
sub('slides/c.html', [
    ('<div class="hero" data-gl="img/blueocean.webp"><img src="img/blueocean.webp" alt="" class="kb"><div class="shade c"></div></div>', '<div class="hero" data-gl="img/blueocean.webp"><img src="img/blueocean.webp" alt="" class="kb"><div class="shade c"></div><div class="shade f"></div></div>'),
    ('data-step="1" data-a="none">Live: how B2B firms fill a pipeline</div>', 'data-step="1" data-a="none">Live: fill your pipeline</div>'),
    ('<div class="rp-head card" style="top:330px" data-a="rise" data-d=".5"><span class="avatar-i">PN</span>', '<div class="rp-head card" style="top:330px" data-only="0" data-a="rise" data-d=".5"><span class="avatar-i">PN</span>'),
    ('<div class="inv-card" data-only="1" data-a="rise">', '<div class="inv-card" style="top:360px" data-only="1" data-a="rise">'),
])
sub('slides/d.html', [
    ('<div class="live" data-only="1" data-a="rise">', '<div class="lvroom" data-only="1" data-a="rise">'),
    ('<div class="lv-calls card"><span class="vl s">Calls booked, live</span>', '<div class="lv-calls card"><span class="vl s">Calls booked · Growth Idea, best webinar</span>'),
    ('<span class="cap m" data-a="fade" data-d="1.8">Measured · Growth Idea, best webinar, 28 Aug 2025</span>\n  <aside class="notes"><p><b>Minute 30.', '<span class="cap m" data-only="0" data-a="fade" data-d="1.8">Measured · Growth Idea, best webinar, 28 Aug 2025</span>\n  <aside class="notes"><p><b>Minute 30.'),
    ('<p class="b w4" style="top:860px" data-step="1" data-a="rise">Would you trust', '<p class="b w4" style="top:790px" data-step="1" data-a="rise">Would you trust'),
    ('<h2 class="t" style="left:700px;width:1080px" data-a="words" data-d=".4">One call an episode <span class="a-s">became a predictable machine.</span></h2>',
     '<h2 class="t" style="left:700px;width:1080px" data-a="words" data-d=".4">From 1 call an episode <span class="a-s">to 9.</span></h2>'),
    ('<span class="cap m" style="left:700px" data-a="fade" data-d="2">Measured · FintechCircle, Mar to Oct 2026; bars are calendar invites per episode</span>',
     '<span class="cap m" style="left:700px" data-a="fade" data-d="2">Measured · FintechCircle · bars: invites per episode</span>'),
])
sub('slides/e.html', [
    ('<p class="b" style="top:350px;width:960px" data-a="rise" data-d=".7">45 minutes. We look at your pipeline, find what\'s breaking and map this system onto your business.</p>',
     '<p class="b" style="top:350px;width:960px" data-a="rise" data-d=".7">45 minutes. We find what\'s breaking and map this onto your business.</p>'),
    ('<a class="book" style="top:640px" href="{{BOOK}}" target="_blank" rel="noopener" data-a="pop" data-d="1.1">Book your call <svg class="ico" viewBox="0 0 24 24"><line x1="3" y1="12" x2="20" y2="12"/><polyline points="14,6 20,12 14,18"/></svg></a>\n  <div class="gift-mini"',
     '<a class="book" style="top:600px" href="{{BOOK}}" target="_blank" rel="noopener" data-a="pop" data-d="1.1">Book your call <svg class="ico" viewBox="0 0 24 24"><line x1="3" y1="12" x2="20" y2="12"/><polyline points="14,6 20,12 14,18"/></svg></a>\n  <div class="gift-mini"'),
])
sub('js/fx.js', [
    ("        tl.call(() => { lbl.textContent = 'real buyers stay'; }, null, 0);\n", ''),
])
sub('v3.css', [
    ('.live { position: absolute; left: 140px; right: 140px; top: 330px; height: 600px; display: grid; grid-template-columns: 1fr 520px; gap: 30px; }',
     '.lvroom { position: absolute; left: 140px; right: 140px; top: 330px; height: 560px; display: grid; grid-template-columns: 1fr 520px; grid-template-rows: 560px; gap: 30px; }'),
    ('.lv-main img { width: 100%; height: 100%; object-fit: cover; object-position: 50% 25%; opacity: .92; }', '.lv-main img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 25%; opacity: .92; }'),
    ('.lv-side { display: grid; grid-template-rows: 1fr 210px; gap: 30px; }', '.lv-side { display: grid; grid-template-rows: 1fr 220px; gap: 30px; min-height: 0; }\n.lv-chat { overflow: hidden; }'),
    ('.gifts { position: absolute; left: 140px; right: 140px; top: 330px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 36px; }',
     '.gifts { position: absolute; left: 140px; right: 140px; top: 330px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 36px; }'),
    ('.fan { position: absolute; left: 1060px; top: 250px; width: 760px; height: 700px; }', '.fan { position: absolute; left: 1100px; top: 200px; width: 760px; height: 760px; }'),
    ('.fan img { position: absolute; left: var(--x); top: var(--y); width: 400px;', '.fan img { position: absolute; left: calc(var(--x) * .9); top: calc(var(--y) * 1.6); width: 440px;'),
    ('.fan img:first-child { width: 300px; }', '.fan img:first-child { width: 330px; }'),
    ('.ff { position: absolute; right: 140px; top: 170px; width: 660px; padding: 40px 44px; }', '.ff { position: absolute; right: 140px; top: 170px; width: 620px; padding: 40px 44px; }'),
    ('.ff-m { display: flex; justify-content: space-between; color: var(--dim); }', '.ff .ff-m { display: flex; width: 100%; justify-content: space-between; color: var(--dim); }'),
    ('.mp-own { position: absolute; left: 40px; right: 40px; bottom: 40px; padding: 30px 36px; border-radius: 22px; background: rgba(52,211,153,.12);',
     '.mp-own { position: absolute; left: 40px; right: 40px; bottom: 40px; padding: 30px 36px; border-radius: 22px; background: #0f2a22;'),
    ('.mosaic { position: absolute; inset: -40px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; padding: 0; opacity: .32; filter: blur(1.5px) saturate(.7); transform: rotate(-4deg) scale(1.08); }',
     '.mosaic { position: absolute; inset: -40px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; padding: 0; filter: blur(1.5px) saturate(.6) brightness(.42); transform: rotate(-4deg) scale(1.08); }'),
    ('#s-brain::before { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(10,11,18,.96) 10%, rgba(10,11,18,.55) 55%, rgba(10,11,18,.2)); z-index: 0; }\n#s-brain > * { z-index: 1; }\n#s-brain .mosaic { z-index: 0; }',
     '#s-brain::before { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(10,11,18,.97) 12%, rgba(10,11,18,.7) 50%, rgba(10,11,18,.25)); z-index: 1; }\n#s-brain > * { z-index: 2; }\n#s-brain > .mosaic { z-index: 0; }'),
    ('.vis.wbars.sh-bars { left: 1180px; right: 140px; top: 360px; width: auto; gap: 26px; }\n.sh-bars .wb { grid-template-columns: 1fr; gap: 10px; }\n.sh-bars .w-track { height: 48px; }',
     '.vis.wbars.sh-bars { left: 1040px; right: 140px; top: 380px; bottom: auto; width: auto; gap: 34px; }\n.sh-bars .wb { grid-template-columns: 300px 1fr; gap: 26px; }\n.sh-bars .w-track { height: 52px; }'),
    ('.biz { position: absolute; left: 140px; top: 330px; width: 600px;', '.biz { position: absolute; left: 140px; top: 330px; width: 560px;'),
    ('.bnode { position: absolute; left: 880px; top: 470px; width: 220px; height: 220px;', '.bnode { position: absolute; left: 790px; top: 500px; width: 190px; height: 190px;'),
    ('.bwire { position: absolute; left: 740px; top: 560px; width: 140px; height: 40px; }', '.bwire { position: absolute; left: 700px; top: 575px; width: 90px; height: 40px; }'),
    ('.craft { position: absolute; left: 140px; top: 400px; width: 1000px;', '.craft { position: absolute; left: 140px; top: 360px; width: 1000px;'),
    ('.fc-bars2 { position: absolute; left: 700px; right: 140px; top: 330px; height: 400px;', '.fc-bars2 { position: absolute; left: 700px; right: 140px; top: 330px; height: 380px;'),
    ('.fc-row { position: absolute; left: 700px; right: 140px; top: 770px;', '.fc-row { position: absolute; left: 700px; right: 140px; top: 740px;'),
    ('.orb-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: .55; }', '.orb-bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: .35; }'),
    ('.vis.rp.manyp { top: 540px; }', '.vis.rp.manyp { top: 540px; }\n.vis.rp.manyp i { height: 46px; }'),
    ('.mc-x { grid-column: 2;', '.mcmp { grid-template-columns: 1fr 300px; }\n.mc-x { grid-column: 2;'),
])
# hero images whose subject sits left of centre: shift the picture right
open(f'{S}/v3.css', 'a').write('\n.hero.shift img { left: 300px; width: calc(100% - 140px); object-position: 60% 50%; }\n.hero.shift::before { content: ""; position: absolute; inset: 0; background: var(--ink); }\n')
print('fixed')
