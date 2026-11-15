// Render every build state of every slide that has builds. usage: node qa-steps.js <deckDir> <outDir> [onlyIds,comma]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const deck = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
const only = (process.argv[4] || '').split(',').filter(Boolean);
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
}).listen(8768);
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1952, height: 1080 }, deviceScaleFactor: 1 });
  const errs = [];
  pg.on('pageerror', e => errs.push('[pageerror] ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') errs.push('[error] ' + m.text()); });
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:8768/?qa=1#slide-1', { waitUntil: 'load', timeout: 30000 });
  await pg.waitForTimeout(1200);
  const list = await pg.evaluate(() => DECK.slides.map((s, i) => ({ i, id: s.id, n: +(s.dataset.steps || 0) })).filter(s => s.n > 0));
  for (const s of list) {
    if (only.length && !only.includes(s.id)) continue;
    await pg.evaluate(k => { gsap.globalTimeline.timeScale(1); DECK.go(k, { step: 0, force: true }); }, s.i);
    for (let k = 0; k <= s.n; k++) {
      if (k > 0) await pg.evaluate(() => { gsap.globalTimeline.timeScale(1); DECK.next(); });
      await pg.waitForTimeout(200);
      await pg.evaluate(() => { gsap.globalTimeline.timeScale(6); });
      await pg.waitForTimeout(1300);
      await pg.screenshot({ path: path.join(out, `${String(s.i + 1).padStart(2, '0')}-${k}.png`), clip: { x: 16, y: 0, width: 1920, height: 1080 } });
    }
    console.log(s.i + 1, s.id, 'states', s.n + 1);
  }
  console.log('ERRORS:', errs.length ? [...new Set(errs)].join('\n') : 'none');
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); }).then(() => process.exit(0));
