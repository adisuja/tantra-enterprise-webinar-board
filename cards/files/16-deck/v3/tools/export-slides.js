// One image per slide (final build state) plus all on-screen text across its steps.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const deck = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
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
}).listen(8771);
const TEXT = () => {
  const sl = DECK.slides[DECK.cur];
  return sl.innerText.split('\n').map(t => t.replace(/\s+/g, ' ').trim()).filter(Boolean);
};
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1952, height: 1080 } });
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto('http://127.0.0.1:8771/?qa=1#slide-1', { waitUntil: 'load' });
  await pg.waitForTimeout(1500);
  const list = await pg.evaluate(() => DECK.slides.map((s, i) => ({ i, title: s.dataset.title, n: +(s.dataset.steps || 0) })));
  const res = [];
  for (const s of list) { console.log("slide", s.i + 1);
    await pg.evaluate(k => { gsap.globalTimeline.timeScale(1); DECK.go(k, { step: 0, force: true }); }, s.i);
    const seen = [];
    for (let k = 0; k <= s.n; k++) {
      if (k > 0) await pg.evaluate(() => { gsap.globalTimeline.timeScale(1); DECK.next(); });
      await pg.waitForTimeout(150); await pg.evaluate(() => gsap.globalTimeline.timeScale(6)); await pg.waitForTimeout(1300);
      for (const l of await pg.evaluate(TEXT)) if (!seen.includes(l)) seen.push(l);
      if (k === s.n) await pg.screenshot({ path: path.join(out, `slide-${String(s.i + 1).padStart(2, '0')}.jpg`), clip: { x: 16, y: 0, width: 1920, height: 1080 }, type: 'jpeg', quality: 82 });
    }
    res.push({ n: s.i + 1, title: s.title, steps: s.n + 1, text: seen.filter(t => !/^\d+$/.test(t) || t.length > 2).filter(t => t !== 'TANTRA') });
  }
  fs.writeFileSync(path.join(out, 'slides.json'), JSON.stringify(res, null, 1));
  console.log('slides', res.length); await b.close(); srv.close(); process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
