// Render EVERY state of EVERY slide at full size and run geometry checks.
// usage: node qa-all.js <deckDir> <outDir> [fromSlide] [toSlide]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const deck = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
const VW = +(process.argv[4] || 1440), VH = +(process.argv[5] || 900);
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
  const boxes = [...sl.querySelectorAll('.card, img, .lgi, .qr-wrap')].filter(e => vis(e) && !e.closest('.hero,.mq-track,.notes,.bt-img') && !e.classList.contains('bt-img')).filter(e => { let op = 1, a = e; while (a && a !== sl) { op *= +getComputedStyle(a).opacity; a = a.parentElement; } return op > .2; }).map(e => ({ e, ...toS(e.getBoundingClientRect()) }));
  for (const it of items) for (const b of boxes) {
    if (b.e.contains(it.el) || it.el.contains(b.e)) continue;
    const ix = Math.min(it.x1, b.x1) - Math.max(it.x0, b.x0), iy = Math.min(it.y1, b.y1) - Math.max(it.y0, b.y0);
    if (ix > 6 && iy > 6) bad.push(`COVER "${it.t}" x ${b.e.tagName.toLowerCase()}.${(b.e.className.baseVal ?? b.e.className).toString().split(' ').join('.')} (${Math.round(ix)}x${Math.round(iy)})`);
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const A = boxes[i], B = boxes[j]; if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
    const ix = Math.min(A.x1, B.x1) - Math.max(A.x0, B.x0), iy = Math.min(A.y1, B.y1) - Math.max(A.y0, B.y0);
    if (ix > 6 && iy > 6) bad.push(`BOXES ${A.e.tagName.toLowerCase()}.${(A.e.className.baseVal ?? A.e.className).toString().split(' ')[0]} x ${B.e.tagName.toLowerCase()}.${(B.e.className.baseVal ?? B.e.className).toString().split(' ')[0]} (${Math.round(ix)}x${Math.round(iy)})`);
  }
  return [...new Set(bad)].slice(0, 30);
};
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push('[pageerror] ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') errs.push('[error] ' + m.text()); });
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:8769/', { waitUntil: 'load', timeout: 30000 });
  await pg.waitForTimeout(3000);
  const report = [];
  const total = await pg.evaluate(() => DECK.slides.reduce((a, s) => a + 1 + +(s.dataset.steps || 0), 0));
  for (let k = 0; k < total; k++) {
    const st = await pg.evaluate(() => ({ i: DECK.cur, s: DECK.step, id: DECK.slides[DECK.cur].id, n: DECK.slides.length }));
    const bad = await pg.evaluate(CHECK);
    const name = String(k).padStart(3, '0') + `-s${String(st.i + 1).padStart(2, '0')}-${st.s}`;
    await pg.screenshot({ path: path.join(out, name + '.png') });
    report.push(name + ' ' + st.id + (bad.length ? '\n   ' + bad.join('\n   ') : ''));
    await pg.keyboard.press('ArrowRight');
    await pg.waitForTimeout(2800);
  }
  fs.writeFileSync(path.join(out, 'report.txt'), report.join('\n') + '\nERRORS: ' + (errs.length ? [...new Set(errs)].join('\n') : 'none') + '\n');
  console.log('frames', report.length, 'ERRORS:', errs.length ? [...new Set(errs)].join('\n') : 'none');
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); }).then(() => process.exit(0));
