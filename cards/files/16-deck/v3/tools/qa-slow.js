// Render EVERY state of EVERY slide at full size and run geometry checks.
// usage: node qa-all.js <deckDir> <outDir> [fromSlide] [toSlide]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const deck = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
const from = +(process.argv[4] || 1), to = +(process.argv[5] || 999);
const GSAP = path.join(__dirname, 'node/node_modules/gsap/dist/gsap.min.js');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg' };
const srv = http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html';
  const f = path.join(deck, p);
  if (!f.startsWith(deck) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  let body = fs.readFileSync(f);
  if (p === '/index.html') body = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + body + '</body></html>';
  r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); r.end(body);
}).listen(8769);
const CHECK = () => {
  const st = document.getElementById('stage'), sr = st.getBoundingClientRect(), sc = sr.width / 1920;
  const sl = DECK.slides[DECK.cur];
  const vis = e => e.checkVisibility ? e.checkVisibility({ opacityProperty: true, visibilityProperty: true }) : true;
  const toS = r => ({ x0: (r.left - sr.left) / sc, y0: (r.top - sr.top) / sc, x1: (r.right - sr.left) / sc, y1: (r.bottom - sr.top) / sc });
  const items = [];
  const walker = document.createTreeWalker(sl, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue;
    const el = n.parentElement;
    if (!el || el.closest('.notes,svg,.mq-track') || !vis(el)) continue;
    let op = 1, a = el; while (a && a !== sl) { op *= +getComputedStyle(a).opacity; a = a.parentElement; }
    if (op < .2) continue;
    const rg = document.createRange(); rg.selectNodeContents(n);
    for (const r of rg.getClientRects()) { if (r.width < 2 || r.height < 2) continue; items.push({ el, t: n.textContent.trim().slice(0, 38), ...toS(r), fs: parseFloat(getComputedStyle(el).fontSize) }); }
  }
  const bad = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const A = items[i], B = items[j];
    if (A.el === B.el || A.el.contains(B.el) || B.el.contains(A.el)) continue;
    const ix = Math.min(A.x1, B.x1) - Math.max(A.x0, B.x0), iy = Math.min(A.y1, B.y1) - Math.max(A.y0, B.y0);
    if (ix > 6 && iy > 6) bad.push(`OVERLAP "${A.t}" x "${B.t}" (${Math.round(ix)}x${Math.round(iy)})`);
  }
  const seen = new Set();
  for (const it of items) {
    if (it.fs < 29.5 && !seen.has(it.t)) { seen.add(it.t); bad.push(`SMALL ${it.fs}px "${it.t}"`); }
    if (it.x1 > 1860 || it.x0 < 60 || it.y1 > 1030 || it.y0 < 40) bad.push(`EDGE [${Math.round(it.x0)},${Math.round(it.y0)} ${Math.round(it.x1)},${Math.round(it.y1)}] "${it.t}"`);
  }
  sl.querySelectorAll('*').forEach(e => {
    if (!vis(e) || e.closest('.notes,.mq-row,.hero,.mosaic,.pf-photo,.host-photo,.bnode,.dissolve,.orbit,.brain-img')) return;
    const cs = getComputedStyle(e);
    if ((cs.overflow === 'hidden' || cs.overflowY === 'hidden' || cs.overflowX === 'hidden') && e.textContent.trim() && (e.scrollHeight > e.clientHeight + 3 || e.scrollWidth > e.clientWidth + 3)) bad.push(`CLIP ${e.className} ${e.scrollWidth}x${e.scrollHeight} > ${e.clientWidth}x${e.clientHeight}`);
  });
  return [...new Set(bad)].slice(0, 14);
};
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1952, height: 1080 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push('[pageerror] ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') errs.push('[error] ' + m.text()); });
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:8769/?qa=1#slide-1', { waitUntil: 'load', timeout: 30000 });
  await pg.waitForTimeout(1200);
  const list = await pg.evaluate(() => DECK.slides.map((s, i) => ({ i, id: s.id, n: +(s.dataset.steps || 0) })));
  const report = [];
  for (const s of list) {
    if (s.i + 1 < from || s.i + 1 > to) continue;
    await pg.evaluate(k => { gsap.globalTimeline.timeScale(1); DECK.go(k, { step: 0, force: true }); }, s.i);
    for (let k = 0; k <= s.n; k++) {
      if (k > 0) await pg.evaluate(() => { gsap.globalTimeline.timeScale(1); DECK.next(); });
      await pg.waitForTimeout(200);
      await pg.evaluate(() => { gsap.globalTimeline.timeScale(1); });
      await pg.waitForTimeout(2800);
      const bad = await pg.evaluate(CHECK);
      const name = `${String(s.i + 1).padStart(2, '0')}-${k}`;
      await pg.screenshot({ path: path.join(out, name + '.png'), clip: { x: 16, y: 0, width: 1920, height: 1080 } });
      report.push(name + ' ' + s.id + (bad.length ? '\n   ' + bad.join('\n   ') : ''));
    }
  }
  fs.writeFileSync(path.join(out, 'report.txt'), report.join('\n') + '\nERRORS: ' + (errs.length ? [...new Set(errs)].join('\n') : 'none') + '\n');
  console.log(report.filter(r => r.includes('\n')).join('\n'));
  console.log('ERRORS:', errs.length ? [...new Set(errs)].join('\n') : 'none');
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); }).then(() => process.exit(0));
