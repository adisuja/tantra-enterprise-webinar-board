// Rapid navigation stress test: hammers the deck with fast forward and back presses (key repeat, clicks, jumps)
// and checks that slides never pile up. Run: node tools/qa-rapid.js deck [gsap.min.js] [rounds]
// Fails (exit 1) if, at any point after input settles, more than one slide or any element of a hidden slide is
// visible, or if during a burst more than one slide is on screen at once (the outgoing one fades out before the
// incoming one fades in, so two never overlap).
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const deck = path.resolve(process.argv[2] || 'deck');
const GSAP = process.argv[3] || path.join(__dirname, 'node/node_modules/gsap/dist/gsap.min.js');
const ROUNDS = +(process.argv[4] || 40);
const port = 8900 + Math.floor(Math.random() * 90);
http.createServer((q, r) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html';
  const f = path.join(deck, p);
  if (!f.startsWith(deck) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  let body = fs.readFileSync(f);
  if (p === '/index.html') body = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + body + '</body></html>';
  r.writeHead(200, { 'content-type': p.endsWith('.html') ? 'text/html' : 'image/webp' }); r.end(body);
}).listen(port);

// What is on screen: slides whose computed visibility is visible and opacity above 0.02, plus any visible element
// inside a slide that is not the current one.
const PROBE = () => {
  const on = [], leaks = [];
  DECK.slides.forEach((s, i) => {
    const cs = getComputedStyle(s);
    if (cs.visibility === 'visible' && +cs.opacity > .02) on.push(i + 1);
    if (i !== DECK.cur && !s.classList.contains('is-leaving')) {
      for (const el of s.querySelectorAll('*')) {
        if (getComputedStyle(el).visibility === 'visible' && el.getClientRects().length) { leaks.push(`${i + 1}:${el.tagName.toLowerCase()}.${el.className && el.className.baseVal == null ? el.className : ''}`); break; }
      }
    }
  });
  return { cur: DECK.cur + 1, on, leaks };
};

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.route('https://cdnjs.cloudflare.com/**', rt => rt.fulfill({ body: fs.readFileSync(GSAP), contentType: 'text/javascript' }));
  await pg.goto(`http://127.0.0.1:${port}/#slide-1`, { waitUntil: 'load' });
  await pg.waitForTimeout(1200);
  const N = await pg.evaluate(() => DECK.slides.length);
  let fail = 0, worstBurst = 0;
  const keys = ['ArrowRight', 'ArrowLeft'];
  for (let r = 0; r < ROUNDS; r++) {
    // a burst: 6 to 30 presses 15 to 70 ms apart, mostly one direction with reversals, sometimes a jump
    const n = 6 + Math.floor(Math.random() * 25), dir = Math.random() < .5 ? 0 : 1;
    for (let k = 0; k < n; k++) {
      const key = Math.random() < .8 ? keys[dir] : keys[1 - dir];
      if (Math.random() < .04) await pg.evaluate(N => DECK.go(Math.floor(Math.random() * N)), N);
      else await pg.keyboard.press(key);
      await pg.waitForTimeout(15 + Math.random() * 55);
      if (k % 3 === 2) { const p = await pg.evaluate(PROBE); worstBurst = Math.max(worstBurst, p.on.length); if (p.on.length > 1) { fail++; console.log(`round ${r + 1}: ${p.on.length} slides on screen mid-burst (${p.on.join(', ')})`); } }
    }
    // settle, then exactly one slide may be visible and nothing may leak from the others
    await pg.waitForTimeout(900);
    const p = await pg.evaluate(PROBE);
    if (p.on.length !== 1 || p.on[0] !== p.cur || p.leaks.length) {
      fail++; console.log(`round ${r + 1}: settled on ${p.cur}, visible slides [${p.on.join(', ')}], leaks [${p.leaks.slice(0, 5).join(' ')}]`);
      await pg.screenshot({ path: `/tmp/qa-rapid-fail-${r + 1}.jpg`, type: 'jpeg', quality: 70 });
    }
  }
  console.log(`${ROUNDS} rounds, most slides on screen mid-burst: ${worstBurst}, failures: ${fail}${errs.length ? ', page errors: ' + errs.slice(0, 3).join(' | ') : ''}`);
  await b.close(); process.exit(fail || errs.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
