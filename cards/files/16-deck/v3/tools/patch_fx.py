"""Add the V3 motion handlers to src/js/fx.js (run once)."""
import os
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src/js/fx.js'
s = open(P).read()
if 'FX.market' in s:
    raise SystemExit('already patched')

s = s.replace("lines = ['How to fill my calendar', 'Proof it works for agencies', 'What AI should run', 'How the invites work']",
              "lines = ['More sales calls without more ads', 'How the calendar invites work', 'Does this work for consultants?', 'What should AI run, and what should I?']")
s = s.replace("""  FX.fields = {
    step(slide, n, tl) {
      if (n !== 2) return;""", """  FX.fields = {
    step(slide, n, tl) {
      if (n !== +(slide.dataset.steps || 2)) return;""")
s = s.replace("""  FX.send = {
    step(slide, n) {
      if (n !== 1) return;""", """  FX.send = {
    step(slide, n, tl) {
      if (n !== 1) return;
      const en = $('#eng-n', slide), o = { v: 0 };
      if (en && tl) tl.fromTo(o, { v: 0 }, { v: 98000, duration: 2.6, ease: 'expo.out', onUpdate: () => { en.textContent = Math.round(o.v).toLocaleString('en-US'); }, onComplete: () => { en.textContent = '98,000'; } }, .3);""")
s = s.replace("""    leave(slide) { $('#morph-n', slide).textContent = '321'; }""",
              """    leave(slide) { const m = $('#morph-n', slide); if (m) m.textContent = '321'; }""")

ADD = r'''
  /* V3: your entire market (6 states) */
  FX.market = {
    enter(slide, tl) {
      const g = $('#mp-grid', slide);
      once(g, 'built', () => { for (let k = 0; k < 154; k++) g.appendChild(document.createElement('i')); });
      $$('i', g).forEach(x => { x.className = ''; });
      $('#mp-n', slide).textContent = '0'; $('#mp-lbl', slide).textContent = 'buyers in your market';
      field('merge', { src: [[420, 400], [420, 540], [420, 680], [420, 820]], to: [1300, 620] });
    },
    step(slide, n, tl) {
      const dots = $$('#mp-grid i', slide), num = $('#mp-n', slide), lbl = $('#mp-lbl', slide);
      if (n === 1) {
        const o = { v: 0 };
        tl.call(() => { lbl.textContent = 'people reached for one webinar'; field('converge', { x: 1340, y: 600, r: 60 }); }, null, 0);
        tl.fromTo(o, { v: 0 }, { v: 99859, duration: 2.4, ease: 'expo.out', onUpdate: () => { num.textContent = Math.round(o.v).toLocaleString('en-US'); }, onComplete: () => { num.textContent = '99,859'; } }, .2);
        dots.forEach((d, k) => tl.call(() => d.classList.add('on'), null, .25 + (k % 22) * .03 + Math.floor(k / 22) * .05));
      }
      if (n === 2) {
        tl.call(() => field('dim'), null, 0);
        const sc = $('#scanline', slide);
        if (sc) { tl.fromTo(sc, { top: -100, opacity: 1 }, { top: 260, duration: 1.3, ease: 'power1.inOut', repeat: 1 }, .6); tl.to(sc, { opacity: 0, duration: .3 }, 3.3); }
      }
      if (n === 3) tl.fromTo($('.cut-state .cut', slide), { scale: 2.4, opacity: 0, rotate: -18 }, { scale: 1, opacity: 1, rotate: -6, duration: .45, ease: 'back.out(2.6)' }, .6);
      if (n === 4) {
        tl.call(() => { lbl.textContent = 'real buyers stay'; }, null, 0);
        dots.forEach((d, k) => tl.call(() => { d.classList.remove('on'); d.classList.add((k * 7) % 10 < 4 ? 'gone' : 'ok'); }, null, .3 + (k % 22) * .02));
      }
    },
    leave(slide) { $$('#mp-grid i', slide).forEach(x => { x.className = ''; }); const m = $('#mp-n', slide); if (m) m.textContent = '0'; }
  };

  /* V3: shaped to your business (4 states) */
  const WS1 = { hook: 34, prob: 94, meth: 30, proof: 46, offer: 36 }, WS2 = { hook: 30, prob: 38, meth: 92, proof: 88, offer: 34 };
  const BIZ0 = ['Business coaches', '$3,000 programme', '12-week group coaching'], BIZ1 = ['Enterprise IT and security', '$90,000 a year', 'Security platform'];
  const setBiz = (slide, v) => { $('#biz-m', slide).textContent = v[0]; $('#biz-p', slide).textContent = v[1]; $('#biz-o', slide).textContent = v[2]; };
  FX.shaped = {
    enter(slide) { $$('.w-fill', slide).forEach(f => { f.style.width = '0%'; }); setBiz(slide, BIZ0); },
    step(slide, n, tl) {
      const fill = w => $$('.wb', slide).forEach(b => tl.to($('.w-fill', b), { width: w[b.dataset.k] + '%', duration: 1.1, ease: 'expo.inOut' }, .5));
      if (n === 1) { const w = $('#bw1', slide); if (w) tl.fromTo(w, { strokeDashoffset: 40 }, { strokeDashoffset: 0, duration: .8, repeat: 2, ease: 'none' }, .2); }
      if (n === 2) fill(WS1);
      if (n === 3) { tl.call(() => setBiz(slide, BIZ1), null, .15); tl.fromTo($('.biz', slide), { scale: .96 }, { scale: 1, duration: .5, ease: 'back.out(2)' }, .15); fill(WS2); }
    },
    leave(slide) { $$('.w-fill', slide).forEach(f => { f.style.width = '0%'; }); setBiz(slide, BIZ0); }
  };

  /* V3: fill the room (a registrants grid with about 16% lit) and run the show */
  FX.room = {
    enter(slide, tl) {
      const g = $('#room-g', slide);
      once(g, 'built', () => { for (let k = 0; k < 96; k++) g.appendChild(document.createElement('i')); });
      const cells = $$('i', g); cells.forEach(c => c.classList.remove('on'));
      const lit = [3, 9, 14, 20, 27, 31, 38, 44, 50, 57, 61, 68, 75, 82, 90];
      lit.forEach((p, k) => tl.call(() => cells[p].classList.add('on'), null, 1.6 + k * .12));
    },
    step(slide, n, tl) {
      if (n !== 1) return;
      tl.call(() => field('rise'), null, 0);
      const e2 = $('#lv-n', slide), o = { v: 0 };
      tl.fromTo(o, { v: 0 }, { v: 25, duration: 2.2, ease: 'power2.out', onUpdate: () => { e2.textContent = Math.round(o.v); }, onComplete: () => { e2.textContent = '25'; } }, .6);
    },
    leave(slide) { $$('#room-g i', slide).forEach(c => c.classList.remove('on')); const l = $('#lv-n', slide); if (l) l.textContent = '25'; }
  };

  /* V3: what we do, the integrations orbit */
  FX.built = {
    step(slide, n) {
      if (n !== 4) return;
      const sp = $$('#orb-ring span', slide);
      D().loop(slide, t => {
        sp.forEach((s2, k) => {
          const a = (k * 30 + t * 9) * Math.PI / 180, x = Math.cos(a) * 640, y = Math.sin(a) * 235;
          s2.style.transform = 'translate(' + x + 'px, ' + y + 'px) scale(' + (.82 + (Math.sin(a) + 1) * .14) + ')';
          s2.style.zIndex = y > 0 ? 3 : 1;
        });
      });
    },
    leave(slide) { $$('#orb-ring span', slide).forEach(s2 => { s2.style.transform = ''; }); }
  };
'''
s = s.rstrip()
assert s.endswith('})();')
s = s[:-len('})();')] + ADD + '})();\n'
open(P, 'w').write(s)
print('patched', s.count('FX.'))
