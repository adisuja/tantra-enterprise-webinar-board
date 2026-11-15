"""Design fixes, round 5: elements that were placed by hand instead of from the content they decorate."""
import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src'

def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:100]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

# 1. slide 7: a real strike through every line of the words, not a bar at half the card height
sub('slides/a.html', [
    ('<div class="card nope" data-a="rise" data-d=".6"><span class="vk">How to use more AI tools</span>', '<div class="card nope" data-a="rise" data-d=".6"><span class="vk sk">How to use more AI tools</span>'),
    ('<svg class="lgi"><use href="#lg-googlegemini"/></svg></span><i class="strike"></i></div>', '<svg class="lgi"><use href="#lg-googlegemini"/></svg></span></div>'),
    ('<div class="card nope" data-a="rise" data-d=".75"><span class="vk">How to automate your content</span><i class="strike"></i></div>', '<div class="card nope" data-a="rise" data-d=".75"><span class="vk sk">How to automate your content</span></div>'),
    # 2. slide 5: wires measured from the boxes they join
    ('<section class="slide" id="s-now" data-title="AI can now do what took large teams" data-bg="converge 1430 640 40" data-reel="6">', '<section class="slide" id="s-now" data-title="AI can now do what took large teams" data-bg="converge 1430 640 40" data-fx="wires" data-reel="6">'),
    ('<svg class="wires" viewBox="0 0 1640 500" width="1640" height="500" data-a="draw" data-d=".8" data-dur="1.3">', '<svg class="wires" viewBox="0 0 1640 540" width="1640" height="540" data-a="draw" data-d=".8" data-dur="1.3">'),
])
sub('js/fx.js', [
    ("""  FX.not = {
    enter(slide, tl) {
      $$('.nope', slide).forEach((n, k) => {
        tl.fromTo($('.strike', n), { scaleX: 0 }, { scaleX: 1, duration: .6, ease: 'power3.inOut' }, 1.4 + k * .25);
      });
    }
  };""", """  FX.not = {
    enter(slide, tl) { $$('.nope', slide).forEach((n, k) => tl.call(() => n.classList.add('struck'), null, 1.4 + k * .25)); },
    leave(slide) { $$('.nope', slide).forEach(n => n.classList.remove('struck')); }
  };

  /* connectors measured from layout (offset positions ignore the entrance transforms) */
  const lay = (e, root) => { let x = 0, y = 0, n = e; while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; } return { x, y, w: e.offsetWidth, h: e.offsetHeight }; };
  const svgAt = (svg, root) => { const p = lay(svg.parentElement, root), cs = getComputedStyle(svg); return { x: p.x + (parseFloat(cs.left) || 0), y: p.y + (parseFloat(cs.top) || 0) }; };
  const wireUp = (slide, svg, froms, to, gap) => {
    const o = svgAt(svg, slide), t = lay(to, slide), paths = $$('path', svg);
    froms.forEach((f, k) => {
      const r = lay(f, slide), x1 = r.x + r.w + gap - o.x, y1 = r.y + r.h / 2 - o.y, x2 = t.x - gap - o.x, y2 = t.y + t.h / 2 - o.y, mx = (x2 - x1) * .55;
      if (paths[k]) paths[k].setAttribute('d', 'M' + x1.toFixed(1) + ' ' + y1.toFixed(1) + ' C ' + (x1 + mx).toFixed(1) + ' ' + y1.toFixed(1) + ', ' + (x2 - mx).toFixed(1) + ' ' + y2.toFixed(1) + ', ' + x2.toFixed(1) + ' ' + y2.toFixed(1));
    });
  };
  FX.wires = { enter(slide) { wireUp(slide, $('.wires', slide), $$('.job', slide), $('.core', slide), 18); } };"""),
    ("""      $('#mp-n', slide).textContent = '0'; $('#mp-lbl', slide).textContent = 'buyers in your market';""",
     """      $('#mp-n', slide).textContent = '0'; $('#mp-lbl', slide).textContent = 'buyers in your market';
      wireUp(slide, $('.mwires', slide), $$('.msrc .lchip', slide), $('.mpanel', slide), 14);"""),
])
sub('v3.css', [
    # chain arrows level with the numbers, not with the number plus its label
    ('.chain { position: absolute; left: 700px; right: 140px; top: 420px; display: flex; align-items: center; justify-content: space-between; }',
     '.chain { position: absolute; left: 700px; right: 140px; top: 420px; display: flex; align-items: flex-start; justify-content: space-between; }'),
    ('.chain .arr { width: 46px; height: 4px; background: var(--iris); position: relative; }',
     '.chain .arr { width: 46px; height: 4px; margin-top: 40px; flex: none; background: var(--iris); position: relative; }'),
    # bar labels on one line
    ('.sh-bars .wb { grid-template-columns: 300px 1fr; gap: 26px; }', '.sh-bars .wb { grid-template-columns: 340px 1fr; gap: 24px; }\n.sh-bars .wb .vk { white-space: nowrap; }'),
])
css = open(f'{S}/v3.css').read()
css += '''
/* round 5 */
.nope .vk.sk { text-decoration-line: line-through; text-decoration-thickness: 6px; text-decoration-color: rgba(240,112,63,0); text-decoration-skip-ink: none; transition: text-decoration-color .5s ease; }
.nope.struck .vk.sk { text-decoration-color: var(--ember); }
@media (prefers-reduced-motion: reduce) { .nope .vk.sk { text-decoration-color: var(--ember); } }
.pf-photo::after, .host-photo::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 320px; background: linear-gradient(0deg, rgba(10,11,18,.94), rgba(10,11,18,0)); pointer-events: none; }
.pf-who { z-index: 1; }
'''
open(f'{S}/v3.css', 'w').write(css)
# 3. slide 58: the three loop labels sit exactly on the ring (centre 280, radius 230)
sub('slides/d.html', [
    ('<span class="lp-node vk" style="left:50%;top:-6px">Detect</span><span class="lp-node vk" style="left:96%;top:76%">Fix</span><span class="lp-node vk" style="left:4%;top:76%">Re-run</span>',
     '<span class="lp-node vk" style="left:50%;top:8.93%">Detect</span><span class="lp-node vk" style="left:85.57%;top:70.54%">Fix</span><span class="lp-node vk" style="left:14.43%;top:70.54%">Re-run</span>'),
])
print('round 5 fixes applied')
