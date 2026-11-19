// Screenshot every slide in its final build state, headless. Works without a GPU (unlike export-slides.js, which can
// stall there). usage: node tools/qa-shots.js deck <outdir> <path to gsap.min.js> [first] [last]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const deck = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]); fs.mkdirSync(out, { recursive: true });
const GSAP = process.argv[4], first = +(process.argv[5] || 1), last = +(process.argv[6] || 999);
const port = 8800 + Math.floor(Math.random() * 100);
http.createServer((q, r) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html'; const f = path.join(deck, p);
  if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); } let body = fs.readFileSync(f);
  if (p === '/index.html') body = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + body + '</body></html>';
  r.writeHead(200, { 'content-type': p.endsWith('.html') ? 'text/html' : 'image/webp' }); r.end(body); }).listen(port);
const T = (p, ms, what) => Promise.race([p, new Promise((_, j) => setTimeout(() => j(new Error('timeout ' + what)), ms))]);
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1952, height: 1080 } });
  pg.on('pageerror', e => console.log('ERR', e.message));
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:' + port + '/?qa=1#slide-1', { waitUntil: 'load' }); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { gsap.globalTimeline.timeScale(5); document.querySelector('#ui').style.display = 'none'; });
  const list = await pg.evaluate(() => DECK.slides.map(s => +(s.dataset.steps || 0)));
  for (let i = first - 1; i < Math.min(list.length, last); i++) {
    try {
      await T(pg.evaluate(k => DECK.go(k, { step: 0, force: true }), i), 15000, 'go');
      await pg.waitForTimeout(700);
      for (let k = 0; k < list[i]; k++) { await T(pg.evaluate(() => DECK.next()), 15000, 'next'); await pg.waitForTimeout(600); }
      await pg.waitForTimeout(900);
      await T(pg.screenshot({ path: path.join(out, 'slide-' + String(i + 1).padStart(2, '0') + '.jpg'), clip: { x: 16, y: 0, width: 1920, height: 1080 }, type: 'jpeg', quality: 80 }), 30000, 'shot');
      console.log('slide', i + 1);
    } catch (e) { console.log('slide', i + 1, 'FAILED', e.message); }
  }
  console.log('done'); process.exit(0);
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
