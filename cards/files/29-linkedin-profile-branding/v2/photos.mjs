// Item 29 v2: Tantra company page logo variants and the six branded profile photos, plus a feed-size preview sheet.
// Logo: the current circuit tree mark (src/tantra-mark-white.png, tantra-mark-ink.png) on brand grounds, no new monogram.
// Photos: each person's Kie.ai AI avatar cutout (src/cutouts) on the same violet ground as the covers, framed for
// LinkedIn's circle crop, with a thin violet to gold ring and the Tantra mark as a small badge.
// Run: node deliverables/29-linkedin-profile-branding/v2/photos.mjs
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_FROM || 'playwright');
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(HERE, 'src');
const OUT = path.join(HERE, 'assets');
const SHOTS = path.join(HERE, 'shots');
const BRAND = '/Users/adithyamurali/tantra-content/content/brand/assets';
const u = (p) => 'file://' + (p.startsWith('/') ? p : path.join(SRC, p));
const S = 800; // design size; rendered at 1.5x = 1200 px

const ground = `background:radial-gradient(circle at 50% 46%,#4a2fd0 0%,#2a1a7a 30%,#120c33 58%,#05060a 82%)`;
const grid = `<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:40px 40px;-webkit-mask-image:radial-gradient(circle at 50% 50%,#000 20%,transparent 70%)"></div>`;

const LOGOS = {
  // A: white mark on deep violet, glow behind the head. Strongest on both light and dark feeds.
  a: `<div class="c" style="${ground}">${grid}
    <div style="position:absolute;left:50%;top:60%;width:420px;height:420px;transform:translate(-50%,-50%);background:radial-gradient(circle,rgba(255,236,200,.38),transparent 65%)"></div>
    <img src="${u(BRAND + '/tantra-mark-white.png')}" style="position:absolute;left:50%;top:50%;width:700px;transform:translate(-50%,-50%);filter:drop-shadow(0 0 18px rgba(167,139,250,.45)) saturate(1.25) brightness(1.08)"></div>`,
  // B: white mark on a brighter violet to indigo gradient, for maximum colour in the feed.
  b: `<div class="c" style="background:linear-gradient(135deg,#7d5cff 0%,#5a3bf0 45%,#2a1c8f 100%)">
    <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 62%,rgba(255,255,255,.28),transparent 45%)"></div>
    <img src="${u(BRAND + '/tantra-mark-white.png')}" style="position:absolute;left:50%;top:50%;width:700px;transform:translate(-50%,-50%);filter:drop-shadow(0 6px 22px rgba(10,6,40,.55)) saturate(1.3) brightness(1.1)"></div>`,
  // C: ink mark on warm white with a soft violet halo, the light option.
  c: `<div class="c" style="background:radial-gradient(circle at 50% 45%,#ffffff 0%,#f4f1ff 55%,#e4ddff 100%)">
    <img src="${u(BRAND + '/tantra-mark-ink.png')}" style="position:absolute;left:50%;top:50%;width:720px;transform:translate(-50%,-50%);filter:saturate(1.2) contrast(1.05)"></div>`,
};

// Custom logos from the newest mark (usetantra.com /brand/tantra-mark-hub.webp, 968 x 872), Adi 2026-11-13.
const HUB = u('tantra-mark-hub.webp');
const glowMark = (w, top, extra = '') => `<img src="${HUB}" style="position:absolute;left:50%;top:${top}px;width:${w}px;transform:translateX(-50%);filter:saturate(1.4) brightness(.96) contrast(1.12) drop-shadow(0 0 4px rgba(255,214,150,.45)) drop-shadow(0 0 16px rgba(139,108,255,.45))${extra}">`;
LOGOS.d = `<div class="c" style="background:radial-gradient(circle at 50% 70%,#3a22a8 0%,#1a1056 34%,#0a0820 62%,#05060a 100%)">
  <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 72%,rgba(255,226,180,.10),transparent 26%)"></div>
  ${glowMark(820, 40)}
  <div style="position:absolute;inset:0;box-shadow:inset 0 0 120px rgba(0,0,0,.65)"></div></div>`;
LOGOS.e = `<div class="c" style="background:linear-gradient(160deg,#141033 0%,#05060a 70%)">
  <div style="position:absolute;left:60px;top:60px;width:680px;height:680px;border-radius:50%;background:radial-gradient(circle at 50% 68%,#4b2fd6 0%,#24168a 40%,#0c0a2a 75%);box-shadow:0 0 0 6px rgba(245,199,107,.0),0 30px 80px rgba(0,0,0,.6),inset 0 0 60px rgba(0,0,0,.55)"></div>
  <div style="position:absolute;left:60px;top:60px;width:680px;height:680px;border-radius:50%;padding:6px;background:conic-gradient(from 210deg,#8b6cff,#c4b5fd,#f5c76b,#8b6cff);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor"></div>
  <div style="position:absolute;left:60px;top:60px;width:680px;height:680px;border-radius:50%;overflow:hidden">${glowMark(640, 70)}</div></div>`;
LOGOS.f = `<div class="c" style="background:linear-gradient(135deg,#6d4aff 0%,#3b22c4 38%,#140c4a 78%,#07061a 100%)">
  <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 72%,rgba(255,236,200,.10),transparent 26%)"></div>
  <div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:50px 50px;-webkit-mask-image:radial-gradient(circle at 50% 60%,#000,transparent 70%)"></div>
  ${glowMark(820, 40)}</div>`;
const PEOPLE = ['adi', 'bhaskar', 'aquila', 'bharath', 'ben', 'nelbin'];
const dims = Object.fromEntries(PEOPLE.map((k) => { const b = fs.readFileSync(path.join(SRC, `cutouts/${k}.png`)); return [k, { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }]; }));
// Head width in each cutout (px at native size, measured from the alpha mask) so every face lands at the same size.
const HEAD = { adi: 280, aquila: 300, ben: 310, bharath: 265, nelbin: 370, bhaskar: 325 };
function photo(k) {
  const sc = 330 / HEAD[k], w = dims[k].w * sc;
  return `<div class="c" style="${ground}">${grid}
    <div style="position:absolute;left:50%;top:44%;width:620px;height:620px;transform:translate(-50%,-50%);background:radial-gradient(circle,rgba(139,108,255,.55),transparent 62%)"></div>
    <img src="${u(`cutouts/${k}.png`)}" style="position:absolute;left:${(S - w) / 2}px;top:118px;width:${w}px;filter:drop-shadow(0 0 30px rgba(109,74,255,.45))">
    <div style="position:absolute;inset:14px;border-radius:50%;padding:7px;background:conic-gradient(from 200deg,#8b6cff,#c4b5fd,#f5c76b,#8b6cff);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude"></div>
    <div style="position:absolute;left:574px;top:574px;width:118px;height:118px;border-radius:50%;background:#05060a;border:5px solid #8b6cff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 26px rgba(0,0,0,.5)"><img src="${u(BRAND + '/tantra-mark-white.png')}" style="width:96px"></div></div>`;
}

const CSS = `*{margin:0;padding:0;box-sizing:border-box}html,body{background:transparent}.c{position:relative;width:${S}px;height:${S}px;overflow:hidden}`;
const browser = await chromium.launch();
async function render(name, body, dsf = 1.5) {
  const page = await browser.newPage({ viewport: { width: S, height: S }, deviceScaleFactor: dsf });
  const tmp = path.join(HERE, '.build', `${name}.html`); fs.mkdirSync(path.dirname(tmp), { recursive: true });
  fs.writeFileSync(tmp, `<!doctype html><html><head><style>${CSS}</style></head><body>${body}</body></html>`);
  await page.goto('file://' + tmp, { waitUntil: 'load' });
  const broken = await page.evaluate(() => [...document.images].filter((i) => !i.naturalWidth).map((i) => i.src));
  if (broken.length) throw new Error(`${name}: missing ${broken}`);
  await page.locator('.c').screenshot({ path: path.join(OUT, `${name}.png`) });
  await page.close();
}
for (const [v, body] of Object.entries(LOGOS)) await render(`tantra-logo-${v}-1200`, body);
for (const k of PEOPLE) await render(`${k}-photo-1200`, photo(k));

// Preview sheet: logos at page size (128), feed size (48) on light and dark feeds; photos as LinkedIn circles at 200 and 48.
const img = (f) => 'file://' + path.join(OUT, f);
const sheet = `<div id="s" style="width:1500px;padding:30px;font-family:-apple-system,sans-serif;background:#f3f2ef">
  <div style="display:flex;gap:40px">${['d', 'e', 'f'].map((v) => `<div style="text-align:center"><div style="font:600 18px sans-serif;margin-bottom:8px">Logo ${v.toUpperCase()}</div>
    <img src="${img(`tantra-logo-${v}-1200.png`)}" style="width:200px;border-radius:8px;display:block;margin:auto">
    <div style="display:flex;gap:14px;align-items:center;justify-content:center;margin-top:12px;background:#fff;padding:10px;border-radius:8px"><img src="${img(`tantra-logo-${v}-1200.png`)}" style="width:48px;border-radius:4px"><span style="font:600 15px sans-serif">Tantra</span></div>
    <div style="display:flex;gap:14px;align-items:center;justify-content:center;margin-top:8px;background:#1b1f23;color:#fff;padding:10px;border-radius:8px"><img src="${img(`tantra-logo-${v}-1200.png`)}" style="width:48px;border-radius:4px"><span style="font:600 15px sans-serif">Tantra</span></div></div>`).join('')}</div>
  <div style="display:flex;gap:26px;margin-top:34px;flex-wrap:wrap">${PEOPLE.map((k) => `<div style="text-align:center"><img src="${img(`${k}-photo-1200.png`)}" style="width:200px;height:200px;border-radius:50%;display:block">
    <div style="display:flex;gap:10px;align-items:center;justify-content:center;margin-top:10px;background:#fff;padding:8px;border-radius:8px"><img src="${img(`${k}-photo-1200.png`)}" style="width:48px;height:48px;border-radius:50%"><span style="font:600 14px sans-serif">${k[0].toUpperCase() + k.slice(1)}</span></div></div>`).join('')}</div></div>`;
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
fs.writeFileSync(path.join(HERE, '.build', 'sheet.html'), `<!doctype html><html><body style="margin:0">${sheet}</body></html>`);
await page.goto('file://' + path.join(HERE, '.build', 'sheet.html'), { waitUntil: 'load' });
await page.locator('#s').screenshot({ path: path.join(SHOTS, 'logo-and-photos-preview.png') });
await browser.close();
console.log('ok: 3 logos, 6 photos, preview sheet');
