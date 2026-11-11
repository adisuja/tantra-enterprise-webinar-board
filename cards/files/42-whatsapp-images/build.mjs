// WhatsApp preview images (card 42): images.json + art/*.png -> out/<key>.jpg (1600 x 838, 1.91:1, Meta's image-header ratio).
// Each card is an HTML page rendered by headless Chrome at 2x, then saved as JPEG (WhatsApp limit 5 MB; ours are ~200 KB).
// usage: node build.mjs [key ...]   then copy out/*.jpg to the CRM worker's public/media/wa/ (see README.md).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const { images } = JSON.parse(fs.readFileSync(path.join(HERE, 'images.json'), 'utf8'));
const TITLE = 'How 400+ Brands Use AI Funnels to Generate $100K to $300K Monthly';
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const only = process.argv.slice(2);
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const hl = (s) => esc(s).replace(/\[(.+?)\]/g, '<em>$1</em>');

const css = `
@font-face { font-family: Inter; src: url(../src/inter-var.woff2) format('woff2'); font-weight: 100 900; }
* { box-sizing: border-box; margin: 0; }
html, body { width: 1200px; height: 628px; overflow: hidden; background: #0b0d12; }
body { font-family: Inter, sans-serif; color: #fff; -webkit-font-smoothing: antialiased; font-feature-settings: 'ss01', 'cv11'; }
.card { position: relative; width: 1200px; height: 628px; overflow: hidden; }
.art { position: absolute; inset: 0; background-size: cover; background-position: right center; }
.veil { position: absolute; inset: 0; background: linear-gradient(90deg, #0b0d12 0%, rgba(11,13,18,.92) 34%, rgba(11,13,18,.35) 62%, rgba(11,13,18,0) 80%); }
.grain { position: absolute; inset: 0; background: radial-gradient(60% 80% at 0% 100%, rgba(109,74,255,.22), transparent 70%); }
.rim { position: absolute; inset: 0; border-radius: 0; box-shadow: inset 0 0 0 1px rgba(255,255,255,.06); }
.in { position: absolute; left: 72px; top: 60px; bottom: 56px; width: 1060px; display: flex; flex-direction: column; }
.logo { display: flex; align-items: center; gap: 12px; }
.logo .m { height: 44px; } .logo .w { height: 22px; opacity: .96; }
.mid { margin-top: auto; margin-bottom: auto; padding-top: 8px; }
.eyebrow { display: inline-flex; align-items: center; gap: 10px; padding: 8px 16px 8px 14px; border-radius: 999px; background: rgba(109,74,255,.18); box-shadow: inset 0 0 0 1px rgba(167,139,250,.45); color: #d9d0ff; font-size: 17px; font-weight: 600; letter-spacing: .02em; }
.eyebrow i { width: 8px; height: 8px; border-radius: 50%; background: #a78bfa; box-shadow: 0 0 12px #a78bfa; }
.live .eyebrow { background: rgba(255,59,92,.16); box-shadow: inset 0 0 0 1px rgba(255,90,110,.55); color: #ffd6dc; text-transform: uppercase; letter-spacing: .14em; font-weight: 700; }
.live .eyebrow i { background: #ff3b5c; box-shadow: 0 0 0 5px rgba(255,59,92,.22), 0 0 16px #ff3b5c; }
.amber .eyebrow { background: rgba(251,191,36,.14); box-shadow: inset 0 0 0 1px rgba(251,191,36,.5); color: #fde9b0; }
.amber .eyebrow i { background: #fbbf24; box-shadow: 0 0 12px #fbbf24; }
h1 { max-width: 560px; margin-top: 26px; font-size: 76px; line-height: 1.02; font-weight: 800; letter-spacing: -.045em; text-wrap: balance; }
h1 em { font-style: normal; background: linear-gradient(95deg, #c4b5fd 0%, #8b6cff 55%, #6d4aff 100%); -webkit-background-clip: text; background-clip: text; color: transparent; padding-right: .04em; }
.amber h1 em, .amber .num { background-image: linear-gradient(95deg, #fde68a 0%, #fbbf24 60%, #f59e0b 100%); }
.cd { margin-top: 18px; display: flex; align-items: baseline; gap: 22px; }
.num { font-size: 184px; line-height: .86; font-weight: 850; letter-spacing: -.06em; font-variant-numeric: tabular-nums; background: linear-gradient(180deg, #ffffff 0%, #c4b5fd 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.unit { font-size: 46px; font-weight: 750; letter-spacing: -.035em; line-height: 1.05; white-space: nowrap; padding-bottom: 14px; }
.sub { margin-top: 22px; font-size: 25px; line-height: 1.35; color: #c9cede; font-weight: 500; letter-spacing: -.01em; max-width: 30ch; }
.foot { white-space: nowrap; display: flex; align-items: center; gap: 12px; font-size: 16px; color: #9aa2b4; font-weight: 500; letter-spacing: .005em; }
.foot b { color: #e7e9ef; font-weight: 650; }
.foot .bar { width: 28px; height: 2px; background: linear-gradient(90deg, #6d4aff, #a78bfa); border-radius: 2px; }
`;

const page = (im) => `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>
<div class="card ${im.accent ?? ''}">
  <div class="art" style="background-image:url(../art/${im.art}.png)"></div><div class="veil"></div><div class="grain"></div><div class="rim"></div>
  <div class="in">
    <div class="logo"><img class="m" src="../src/tantra-mark-white.png" alt=""><img class="w" src="../src/tantra-word-white.png" alt="Tantra"></div>
    <div class="mid">
      <span class="eyebrow"><i></i>${esc(im.eyebrow)}</span>
      ${im.count ? `<div class="cd"><span class="num">${esc(im.count)}</span><span class="unit">${esc(im.unit)}</span></div>` : `<h1>${hl(im.big)}</h1>`}
      <p class="sub">${esc(im.sub)}</p>
    </div>
    <div class="foot"><span class="bar"></span>${im.foot === 'title' ? `<span>Live session · <b>${esc(TITLE)}</b></span>` : '<span><b>usetantra.com</b></span>'}</div>
  </div>
</div></body></html>`;

fs.mkdirSync(path.join(HERE, 'html'), { recursive: true });
fs.mkdirSync(path.join(HERE, 'out'), { recursive: true });
for (const im of images) {
  if (only.length && !only.includes(im.key)) continue;
  const html = path.join(HERE, 'html', `${im.key}.html`);
  fs.writeFileSync(html, page(im));
  const png = path.join(HERE, 'html', `${im.key}.png`);
  execFileSync(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2', '--window-size=1200,628', '--virtual-time-budget=3000', '--allow-file-access-from-files', `--screenshot=${png}`, `file://${html}`], { stdio: 'ignore' });
  const jpg = path.join(HERE, 'out', `${im.key}.jpg`);
  execFileSync('sips', ['-s', 'format', 'jpeg', '-s', 'formatOptions', '86', '-Z', '1600', png, '--out', jpg], { stdio: 'ignore' });
  fs.rmSync(png);
  console.log(im.key, `${Math.round(fs.statSync(jpg).size / 1024)} KB`);
}
