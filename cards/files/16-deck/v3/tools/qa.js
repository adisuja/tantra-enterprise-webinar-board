// Render every slide at its final build, collect console errors and out-of-bounds elements, save screenshots.
// usage: node qa.js <deckDir> <outDir> [fromSlide] [toSlide]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const deck = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
const from = +(process.argv[4] || 1), to = +(process.argv[5] || 60);
const GSAP = path.join(__dirname, 'node/node_modules/gsap/dist/gsap.min.js');
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.css': 'text/css' };
const srv = http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html';
  const f = path.join(deck, p);
  if (!f.startsWith(deck) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  let body = fs.readFileSync(f);
  if (p === '/index.html') body = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + body + '</body></html>';
  r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); r.end(body);
}).listen(8767);
(async () => {
  const b = await chromium.launch(process.env.QAGL ? { args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] } : {});
  const pg = await b.newPage({ viewport: { width: 1952, height: 1080 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(`[${m.type()}] ${m.text()}`); });
  pg.on('pageerror', e => errs.push('[pageerror] ' + e.message));
  pg.on('crash', () => { errs.push('[CRASH]'); console.error('CRASH at', Date.now()); });
  b.on('disconnected', () => console.error('browser disconnected'));
  pg.on('close', () => console.error('page closed'));
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:8767/?qa=' + (process.env.QAGL ? '0' : '1') + '#slide-' + from, { waitUntil: 'load', timeout: 30000 });
  await pg.waitForTimeout(1500);
  console.error('loaded', await pg.evaluate(() => ({ n: DECK.N, gsap: !!window.gsap })));
  const report = [];
  for (let i = from; i <= to; i++) {
    await pg.evaluate(k => { gsap.globalTimeline.timeScale(1); if (DECK.cur !== k - 1) DECK.go(k - 1, { step: 'max' }); else { while (DECK.step < +(DECK.slides[k - 1].dataset.steps || 0)) DECK.next(); } }, i);
    console.error('slide', i, 'set'); await pg.waitForTimeout(250);
    await pg.evaluate(() => { gsap.globalTimeline.timeScale(6); }); console.error('timescale ok');
    await pg.waitForTimeout(1500);
    const info = await pg.evaluate(() => {
      const st = document.getElementById('stage'), sr = st.getBoundingClientRect(), sc = sr.width / 1920;
      const sl = DECK.slides[DECK.cur];
      const bad = [];
      sl.querySelectorAll('*').forEach(e => { if (e.closest(".hero,.notes,canvas,.div-num,.pipe,.mosaic,.pf-photo")) return;
        if (e.closest('svg') && e.tagName !== 'svg') return;
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return;
        const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
        const x0 = (r.left - sr.left) / sc, y0 = (r.top - sr.top) / sc, x1 = (r.right - sr.left) / sc, y1 = (r.bottom - sr.top) / sc;
        if (x1 > 1900 || y1 > 1062 || x0 < 20 || y0 < 20) bad.push(`${e.tagName.toLowerCase()}.${(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) || ''} [${Math.round(x0)},${Math.round(y0)} to ${Math.round(x1)},${Math.round(y1)}] "${(e.textContent || '').trim().slice(0, 40)}"`);
        if ((cs.overflow === 'hidden' || cs.overflowY === 'hidden') && e.scrollHeight > e.clientHeight + 4 && !e.classList.contains('w') && e.children.length) bad.push(`clipped ${e.tagName.toLowerCase()}.${e.className} ${e.scrollHeight}>${e.clientHeight}`);
      });
      return { id: sl.id, bad: bad.slice(0, 8) };
    });
    await pg.screenshot({ path: path.join(out, `s${String(i).padStart(2, '0')}.png`), clip: { x: 16, y: 0, width: 1920, height: 1080 } });
    report.push(`${String(i).padStart(2, '0')} ${info.id}${info.bad.length ? '\n   ' + info.bad.join('\n   ') : ''}`);
  }
  console.log(report.join('\n'));
  console.log('ERRORS:\n' + (errs.length ? [...new Set(errs)].slice(0, 30).join('\n') : 'none'));
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); }).then(() => process.exit(0));
