// Item 29 v2: LinkedIn covers, company cover and Featured images, composed from separate elements.
// Elements: Kie.ai avatar portrait cutouts (src/cutouts, rembg BiRefNet portrait), Kie.ai side profiles generated from each
// person's own photos (src/side, metrics.json = nose tip and head top), client logos, bonus covers, Inter.
// Text, logos and layout are HTML/CSS, so the words stay sharp and identical on every profile.
// Run: node deliverables/29-linkedin-profile-branding/v2/build.mjs [--guides]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_FROM || 'playwright');
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(HERE, 'src');
const OUT = path.join(HERE, 'assets');
const GUIDES = process.argv.includes('--guides');
const copy = JSON.parse(fs.readFileSync(path.join(HERE, 'copy.json'), 'utf8'));
const side = JSON.parse(fs.readFileSync(path.join(SRC, 'side/metrics.json'), 'utf8'));
const u = (p) => 'file://' + path.join(SRC, p);

// Per person: which part of the cutout to show (fraction of its height, from the head down) and a horizontal nudge.
// Cutouts are the team's Kie.ai avatar portraits (same house prompt, waist-up, arms crossed), background removed.
const PEOPLE = {
  adi: { name: 'Adithya Murali', show: 0.80, dx: 0 },
  aquila: { name: 'Aquila Eldho', show: 0.80, dx: 0 },
  ben: { name: 'Ben Basil Tomy', show: 0.80, dx: 0 },
  bharath: { name: 'Bharath', show: 0.80, dx: 0 },
  nelbin: { name: 'Nelbin', show: 0.80, dx: 0 },
  bhaskar: { name: 'Bhaskar', show: 0.80, dx: 0 },
};
// Logos: the registration page's approved "Brands We've Helped Grow" set (Adi 2026-11-07), imagineGROWTH left out (dead site).
const BIG = ['google', 'amazon', 'techstars', 'upgrad', 'licious', 'leapwork', '91springboard'];
const CLIENTS = ['dataguard', 'merkle-science', 'cavli', 'wxrks', 'coinfirm', 'appster', 'growth-idea', 'fintechcircle'];
const MORE = ['omniance', 'iboson', 'ikrshna', 'salesup', 'wowmakers', 'springup'];
const RATIO = JSON.parse(fs.readFileSync(path.join(SRC, 'logos/ratios.json'), 'utf8'));
const FACES = JSON.parse(fs.readFileSync(path.join(SRC, 'avatars/faces.json'), 'utf8'));
// Optical sizing: every logo gets the same visual area, capped in height, so wide wordmarks and square marks weigh the same.
const logoImg = (l, area, maxH) => { const r = RATIO[l]; let h = Math.min(maxH, Math.sqrt(area / r)); return `<img src="${u(`logos/${l}.png`)}" style="height:${h.toFixed(1)}px;width:${(h * r).toFixed(1)}px">`; };
const logoRow = (ids, area, maxH, gap, extra = '') => `<div class="logos" style="gap:${gap}px;${extra}">${ids.map((l) => logoImg(l, area, maxH)).join('')}</div>`;
// Client logos as glass chips (Adi 2026-11-13: bigger and more stylized): each logo full white in its own rounded chip.
const chips = (ids, cols, w, h, area, maxH, gap, extra = '') => `<div class="chips" style="display:grid;grid-template-columns:repeat(${cols},${w}px);gap:${gap}px;${extra}">${ids.map((l) => { const r = RATIO[l], lh = Math.min(maxH, Math.sqrt(area / r), (w - Math.max(18, w * 0.16)) / r); return `<div class="chip" style="height:${h}px"><img src="${u(`logos/${l}.png`)}" style="height:${lh.toFixed(1)}px;width:${(lh * r).toFixed(1)}px"></div>`; }).join('')}</div>`;
const ASSET = (f) => 'file://' + path.join(OUT, f);

const FONT = `@font-face{font-family:Inter;src:url(${u('inter-var.woff2')}) format('woff2');font-weight:100 900}`;
const BASE = `${FONT}*{box-sizing:border-box;margin:0;padding:0}html,body{background:#05060a;overflow:hidden}
body{font-family:Inter,sans-serif;color:#fff;-webkit-font-smoothing:antialiased}
.fit{position:relative;overflow:hidden;background:#05060a}
.kicker{font-weight:800;text-transform:uppercase;letter-spacing:.18em;color:#a78bfa}
.h{font-weight:850;letter-spacing:-.025em;line-height:1.02}
.h em{font-style:normal;background:linear-gradient(90deg,#c4b5fd,#8b6cff);-webkit-background-clip:text;color:transparent}
.bar{display:inline-block;background:#f5c76b;color:#0b0d12;font-weight:800;border-radius:8px;letter-spacing:-.01em}
.logos{display:flex;align-items:center}
.chip{display:flex;align-items:center;justify-content:center;border-radius:12px;background:linear-gradient(180deg,rgba(255,255,255,.11),rgba(255,255,255,.035));border:1px solid rgba(196,181,253,.30);box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 8px 20px rgba(0,0,0,.35)}
.chip img{filter:brightness(0) invert(1) drop-shadow(0 0 6px rgba(196,181,253,.35));object-fit:contain}
.logos img,.lg img{filter:brightness(0) invert(1);opacity:.82;object-fit:contain}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:44px 44px}
.side{position:absolute;top:0;right:0;bottom:0;overflow:hidden}
.side img{position:absolute;filter:saturate(.9) contrast(1.05)}
.side:before{content:'';position:absolute;inset:0;z-index:2;background:linear-gradient(90deg,#05060a 0%,rgba(5,6,10,0) 28%)}
.person{position:absolute;bottom:0;overflow:hidden;-webkit-mask-image:linear-gradient(180deg,#000 82%,rgba(0,0,0,.35))}
.person img{position:absolute;left:50%;top:0;transform:translateX(-50%);filter:drop-shadow(0 0 28px rgba(109,74,255,.35))}
`;

// Cold traffic: scattered dots converging into one line toward the person. Pure SVG, seeded so every build matches.
function trafficSvg(w, h, tx, ty, n = 46) {
  let s = 7, rnd = () => (s = (s * 16807) % 2147483647) / 2147483647, out = '';
  for (let i = 0; i < n; i++) {
    const x = rnd() * w * 0.78, y = 12 + rnd() * (h - 24), op = (0.18 + rnd() * 0.5).toFixed(2);
    const cx = x + (tx - x) * 0.55, cy = y;
    out += `<path d="M${x.toFixed(1)} ${y.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${tx} ${ty}" stroke="url(#lg)" stroke-width="1" fill="none" opacity="${op}"/>`;
    out += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(1.4 + rnd() * 1.8).toFixed(1)}" fill="#8fa3c8" opacity="${op}"/>`;
  }
  return `<svg width="${w}" height="${h}" style="position:absolute;left:0;top:0"><defs><linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#5b6b8c" stop-opacity=".2"/><stop offset="1" stop-color="#8b6cff"/></linearGradient></defs>${out}</svg>`;
}

// Side profile placed by its own measurements: nose tip at (noseX, noseY), head height scaled to `headPx`.
function sideImg(k, W, H, boxW, noseX, noseY, headPx) {
  const m = side[k];
  const sc = headPx / (m.nose_y - m.top);
  const iw = m.w * sc, ih = m.h * sc;
  const left = noseX - (W - boxW) - m.nose * sc;
  const top = noseY - m.nose_y * sc;
  return `<div class="side" style="width:${boxW}px"><img src="${u(`side/${k}.jpg`)}" style="width:${iw}px;height:${ih}px;left:${left}px;top:${top}px"></div>`;
}

function personImg(k, cx, w, h, headTop) {
  const p = PEOPLE[k];
  const dims = cutDims[k];
  if (p.top && h > 300) headTop = p.top;
  const ih = (h - headTop) / p.show;
  const iw = dims.w * ih / dims.h;
  return `<div class="person" style="left:${cx - w / 2 + p.dx}px;width:${w}px;height:${h}px"><img src="${u(`cutouts/${k}.png`)}" style="height:${ih}px;width:${iw}px;top:${headTop}px"></div>`;
}

// LinkedIn safe zones, measured from the live layout (README): desktop top card 804 x 201 cover, 152 px photo with a
// 4 px ring at left 24, top 89; phone 390 wide cover, 104 px photo at left 16, overlapping the bottom.
const SAFE = {
  cover: [{ x: 47, y: 175, w: 315, h: 221 }, { x: 65, y: 162, w: 424, h: 234 }],
  company: [{ x: 24, y: 118, w: 150, h: 82 }, { x: 16, y: 100, w: 190, h: 100 }],
};
const guide = (zones) => GUIDES ? zones.map((z) => `<div style="position:absolute;left:${z.x}px;top:${z.y}px;width:${z.w}px;height:${z.h}px;border:2px dashed #ff4d4d;border-radius:50% 50% 0 0;z-index:9"></div>`).join('') : '';

function cover(k, cap) {
  const c = { ...copy.cover, ...(cap || {}) }, W = 1584, H = 396;
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px">
  <div class="grid" style="-webkit-mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.6) 40%,transparent 62%)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 420px 300px at 600px 430px,rgba(109,74,255,.55),transparent 70%),radial-gradient(ellipse 520px 260px at 1080px -60px,rgba(109,74,255,.16),transparent 70%)"></div>
  ${trafficSvg(560, H, 600, 300)}
  <img src="${u('tantra-mark-white.png')}" style="position:absolute;left:36px;top:24px;height:72px;filter:drop-shadow(0 0 14px rgba(255,214,150,.35))">
  <img src="${u('tantra-word-white.png')}" style="position:absolute;left:130px;top:46px;height:30px">
  ${personImg(k, 636, 560, H, 22)}
  <div style="position:absolute;left:806px;top:${c.lines ? 44 : 58}px;width:520px">
    ${c.lines ? `<div class="h" style="font-size:${c.size}px;white-space:nowrap;line-height:1.04">${c.lines.join('<br>')}<br><em>${c.em.join('<br>')}</em></div>`
    : `<div class="h" style="font-size:47px;white-space:nowrap">${c.line1}<br><em>${c.line2}</em></div>`}
    ${c.bar ? `<div class="bar" style="font-size:20px;padding:9px 14px;margin-top:20px">${c.bar}</div>` : ''}
    ${chips(['google', 'amazon', 'techstars', 'upgrad', 'licious', 'leapwork', 'dataguard', 'cavli'], 4, 122, 46, 2600, 28, 10, `margin-top:${c.bar ? 22 : 24}px`)}
  </div>
  ${sideImg(k, W, H, 250, W - 222, 244, 232)}
  ${guide(SAFE.cover)}
</div>`;
}

// Evangelists (Scott, Conor; Adi 2026-11-14): no photo yet, so the team's violet face strips stand where the person
// and the side profile go. Same caption block and logo chips as every other cover; the LinkedIn photo zone stays clear.
function evangelistCover(k, cap) {
  const c = { ...copy.cover, ...(cap || {}) }, W = 1584, H = 396;
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px">
  <div class="grid" style="-webkit-mask-image:linear-gradient(90deg,#000 0%,rgba(0,0,0,.6) 30%,transparent 50%)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 520px 300px at 760px 430px,rgba(109,74,255,.45),transparent 70%),radial-gradient(ellipse 520px 260px at 1300px -60px,rgba(109,74,255,.18),transparent 70%)"></div>
  ${trafficSvg(520, H, 520, 300)}
  <img src="${u('tantra-mark-white.png')}" style="position:absolute;left:36px;top:24px;height:72px;filter:drop-shadow(0 0 14px rgba(255,214,150,.35))">
  <img src="${u('tantra-word-white.png')}" style="position:absolute;left:130px;top:46px;height:30px">
  <div style="position:absolute;right:0;top:0;width:640px;height:${H}px;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent 0%,#000 26%)">
    <img src="${ASSET('tantra-collage-strips-violet-1330x700.png')}" style="position:absolute;right:0;top:0;height:${H}px;width:${Math.round(H * 1330 / 700)}px">
  </div>
  <div style="position:absolute;left:520px;top:${c.lines ? 44 : 58}px;width:540px">
    ${c.lines ? `<div class="h" style="font-size:${c.size}px;white-space:nowrap;line-height:1.04">${c.lines.join('<br>')}<br><em>${c.em.join('<br>')}</em></div>`
    : `<div class="h" style="font-size:47px;white-space:nowrap">${c.line1}<br><em>${c.line2}</em></div>`}
    ${c.bar ? `<div class="bar" style="font-size:20px;padding:9px 14px;margin-top:20px">${c.bar}</div>` : ''}
    ${chips(['google', 'amazon', 'techstars', 'upgrad', 'licious', 'leapwork', 'dataguard', 'cavli'], 4, 122, 46, 2600, 28, 10, `margin-top:${c.bar ? 22 : 24}px`)}
  </div>
  ${guide(SAFE.cover)}
</div>`;
}

// Collage A, face strips (Adi's first reference): each strip is a slice of one person's AI avatar face, eyes and smiles aligned.
// grade 'natural' keeps skin tones and darkens toward the edges; 'violet' grades every strip into the brand violet.
function collageStrips(grade) {
  const W = 380, H = 200, order = ['nelbin', 'aquila', 'adi', 'ben', 'bhaskar', 'bharath'];
  const widths = [60, 66, 70, 64, 62, 58], off = [-0.14, 0.12, 0, -0.1, 0.14, -0.12];
  let x = 0, out = '';
  const f0 = grade === 'violet' ? 'grayscale(1) contrast(1.15) brightness(.95)' : 'saturate(.85) brightness(.92) contrast(1.04)';
  order.forEach((k, i) => {
    const f = FACES[k], w = widths[i];
    const sc = (H * 0.92) / f.fh;
    const cx = f.fx + f.fw / 2, cy = f.fy + f.fh * 0.6;
    const left = w / 2 + off[i] * f.fw * sc - cx * sc, top = H * 0.5 - cy * sc;
    out += `<div style="position:absolute;left:${x}px;top:0;width:${w - 1.2}px;height:${H}px;overflow:hidden"><img src="${'file://' + path.join(HERE, f.file)}" style="position:absolute;width:${f.w * sc}px;height:${f.h * sc}px;left:${left}px;top:${top}px;filter:${f0}"></div>`;
    x += w;
  });
  const tint = grade === 'violet' ? `<div style="position:absolute;inset:0;background:linear-gradient(90deg,#6d4aff,#3b2a8c);mix-blend-mode:color;opacity:.85"></div><div style="position:absolute;inset:0;background:#120d2e;mix-blend-mode:multiply;opacity:.35"></div>` : '';
  const fade = `<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,6,10,0) 55%,#05060a 100%),linear-gradient(180deg,rgba(5,6,10,.35) 0%,rgba(5,6,10,0) 22%,rgba(5,6,10,0) 70%,rgba(5,6,10,.85) 100%)"></div>`;
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px;background:#05060a">${out}${tint}${fade}</div>`;
}

// Collage B, side profiles mirrored to face right, faces in front. 'panels': stepped violet panels that darken into the
// background toward the caption; 'glow': no panels, the profiles sit straight on the dark background with a violet glow.
function collagePanels(style) {
  const W = 380, H = 200, order = ['aquila', 'adi', 'ben', 'bhaskar', 'bharath', 'nelbin'];
  const colors = ['#7d5cff', '#6d4aff', '#5a3bd6', '#4a30b0', '#3a2689', '#2a1c63', '#1a1240'];
  const D = 70, noseY = 98, step = 55, first = 80, back = 108;
  const noses = order.map((_, i) => first + i * step);
  let panels = '', people = '';
  const edges = [0, ...noses.map((n) => n - back + step), W];
  if (style === 'panels') for (let i = 0; i < edges.length - 1; i++) {
    panels += `<div style="position:absolute;top:0;bottom:0;left:${edges[i]}px;width:${edges[i + 1] - edges[i] + 1}px;background:linear-gradient(90deg,${colors[i]},${colors[i + 1]});box-shadow:-6px 0 14px rgba(0,0,0,.28)"></div>`;
  }
  else panels = `<div style="position:absolute;inset:0;background:radial-gradient(ellipse 230px 150px at 170px 110px,rgba(109,74,255,.5),transparent 72%)"></div>`;
  order.forEach((k, i) => {
    const m = side[k], sc = D / (m.nose_y - m.top);
    const left = noses[i] - (m.w - m.nose) * sc, top = noseY - m.nose_y * sc;
    const glow = style === 'panels' ? 'drop-shadow(-4px 0 10px rgba(0,0,0,.35))' : 'drop-shadow(0 0 8px rgba(139,108,255,.55))';
    people += `<img src="${u(`sidecut/${k}.png`)}" style="position:absolute;z-index:${20 - i};width:${m.w * sc}px;height:${m.h * sc}px;left:${left}px;top:${top}px;transform:scaleX(-1);filter:brightness(1.25) contrast(1.05) ${glow}">`;
  });
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px;background:#05060a">${panels}${people}<div style="position:absolute;inset:0;z-index:30;background:linear-gradient(90deg,rgba(5,6,10,0) 60%,#05060a 100%),linear-gradient(180deg,rgba(5,6,10,0) 62%,rgba(5,6,10,.95) 100%)"></div></div>`;
}

// Collage B3, side profiles on stacked colour tiles (built by another session on 13 Nov, kept as an alternate).
// src/sidecut/landmarks.json gives eye, nose tip and chin: every face is scaled to the same eye to chin height, eyes on one
// line, noses the same distance inside each tile. Bright gold to blue tiles; does not blend into the background.
function collageTiles() {
  const W = 380, H = 200, order = ['aquila', 'adi', 'ben', 'bhaskar', 'bharath', 'nelbin'];
  const colors = [['#f7c873', '#f2a54a'], ['#ff8f62', '#f2694a'], ['#ff6b97', '#e04882'], ['#b85cf5', '#9a3fe6'], ['#7357ff', '#5a3df0'], ['#2fa4e7', '#1789c9']];
  const LM = JSON.parse(fs.readFileSync(path.join(SRC, 'sidecut/landmarks.json'), 'utf8'));
  const TW = 90, STEP = 58, EYE = 90, FACE = 64, NOSE_IN = 10;
  let tiles = '';
  order.forEach((k, i) => {
    const m = LM[k], sc = FACE / (m.chin_y - m.eye_y), x0 = i * STEP;
    const w = 896 * sc, h = 1200 * sc;
    const left = (TW - NOSE_IN) - (896 - m.nose_x) * sc;
    const top = EYE - m.eye_y * sc;
    const [c1, c2] = colors[i];
    tiles += `<div style="position:absolute;top:0;left:${x0}px;width:${TW}px;height:${H}px;overflow:hidden;z-index:${20 - i};border-radius:0 10px 10px 0;background:linear-gradient(90deg,${c1},${c2});box-shadow:10px 0 22px rgba(0,0,0,.38)">
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,255,255,.10),rgba(255,255,255,0) 40%)"></div>
      <img src="${u(`sidecut/${k}.png`)}" style="position:absolute;width:${w}px;height:${h}px;left:${left}px;top:${top}px;transform:scaleX(-1);filter:brightness(1.32) contrast(1.04)">
      <div style="position:absolute;left:0;right:0;bottom:0;height:46px;background:linear-gradient(180deg,rgba(5,6,10,0),rgba(5,6,10,.55))"></div>
    </div>`;
  });
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px;background:#05060a">${tiles}</div>`;
}

const COMPANY_VARIANTS = { strips: () => collageStrips('natural'), 'strips-violet': () => collageStrips('violet'), panels: () => collagePanels('panels'), glow: () => collagePanels('glow'), tiles: collageTiles };

function companyCover(variant, cap) {
  const c = { ...copy.company_cover, ...(cap || {}) }, W = 1200, H = 200;
  const grid = [...BIG.slice(0, 6), 'dataguard', 'merkle-science', 'cavli', 'wxrks', 'coinfirm', 'appster'];
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px">
  <div class="grid" style="background-size:30px 30px;-webkit-mask-image:linear-gradient(90deg,transparent 30%,#000 60%,transparent)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 360px 170px at 620px 230px,rgba(109,74,255,.45),transparent 70%)"></div>
  <img src="${ASSET(`tantra-collage-${variant}-1330x700.png`)}" style="position:absolute;left:0;top:0;width:380px;height:200px;-webkit-mask-image:linear-gradient(90deg,#000 70%,transparent)">
  <div style="position:absolute;left:408px;top:44px;width:370px">
    <div class="h" style="font-size:32px;white-space:nowrap">${c.line1}<br><em>${c.line2}</em></div>
    <div class="bar" style="font-size:12.5px;padding:5px 9px;margin-top:11px;border-radius:5px">${c.bar}</div>
  </div>
  <div style="position:absolute;left:790px;top:34px;width:358px">
    ${chips(grid, 4, 84, 36, 1250, 21, 7)}
  </div>
  ${guide(SAFE.company)}
</div>`;
}

function workshop() {
  const c = copy.workshop, W = 1200, H = 627;
  const books = ['playbook-a', 'prompts-a', 'calculator-a'];
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px">
  <div class="grid" style="-webkit-mask-image:radial-gradient(ellipse at 30% 40%,#000,transparent 75%)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 520px 380px at 930px 380px,rgba(109,74,255,.55),transparent 70%)"></div>
  <div style="position:absolute;left:64px;top:44px;width:560px">
    <div class="h" style="font-size:58px;margin-top:14px">Watch Cold Traffic Turn Into <em>Booked Calls.</em> Live.</div>
    <div style="font-size:23px;line-height:1.4;color:#c3c7d6;margin-top:22px;font-weight:450">${c.sub}</div>
    <div style="display:inline-flex;align-items:center;gap:12px;margin-top:24px;background:#6d4aff;border-radius:999px;padding:15px 28px;font-weight:750;font-size:22px">${c.cta}<span style="font-size:22px">&#8594;</span></div>
    <div style="display:flex;align-items:center;gap:12px;margin-top:22px">
      <div style="width:52px;height:52px;border-radius:50%;overflow:hidden;background:#1a1640;border:2px solid #6d4aff;position:relative"><img src="${u('avatars/adi-headshot.png')}" style="width:100%;height:100%;object-fit:cover"></div>
      <div style="font-size:17px;color:#c3c7d6;font-weight:600">${c.host}</div></div>
  </div>
  <div style="position:absolute;left:672px;top:48px;width:480px;height:450px">
    ${books.map((b, i) => `<img src="${u(`bonus/${b}.webp`)}" style="position:absolute;width:212px;height:318px;border-radius:10px;box-shadow:0 24px 50px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.08);left:${[18, 134, 250][i]}px;top:${[70, 30, 70][i]}px;transform:rotate(${[-8, 0, 8][i]}deg);z-index:${[1, 3, 2][i]}">`).join('')}
  </div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:78px;background:rgba(255,255,255,.035);border-top:1px solid rgba(255,255,255,.07);display:flex;align-items:center;gap:22px;padding:0 40px;justify-content:center">
    ${chips(['google', 'amazon', 'techstars', 'upgrad', 'licious', 'leapwork', 'dataguard', 'cavli'], 8, 128, 52, 2600, 30, 12)}
  </div>
</div>`;
}

function consult() {
  const c = copy.consult, W = 1200, H = 627;
  const slots = ['10:00', '11:30', '14:00', '16:30'];
  let days = '';
  for (let d = 1; d <= 28; d++) {
    const on = [3, 4, 5, 10, 11, 12, 17, 18, 19, 24, 25].includes(d), sel = d === 11;
    days += `<div style="height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:${on ? 700 : 500};color:${sel ? '#fff' : on ? '#d9d2ff' : '#4b5066'};background:${sel ? '#6d4aff' : on ? 'rgba(109,74,255,.16)' : 'transparent'}">${d}</div>`;
  }
  return `<div class="fit" id="cap" style="width:${W}px;height:${H}px">
  <div class="grid" style="-webkit-mask-image:radial-gradient(ellipse at 30% 40%,#000,transparent 75%)"></div>
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 520px 400px at 920px 330px,rgba(109,74,255,.5),transparent 70%)"></div>
  <div style="position:absolute;left:64px;top:52px;width:560px">
    <div class="h" style="font-size:60px;margin-top:14px">Book an <em>AI Revenue Strategy</em> Consultation</div>
    <div style="font-size:23px;line-height:1.4;color:#c3c7d6;margin-top:22px;font-weight:450">${c.sub}</div>
    <div style="display:inline-flex;align-items:center;gap:12px;margin-top:24px;background:#6d4aff;border-radius:999px;padding:15px 28px;font-weight:750;font-size:22px">${c.cta}<span>&#8594;</span></div>
  </div>
  <div style="position:absolute;left:688px;top:52px;width:450px;background:rgba(18,20,32,.92);border:1px solid rgba(167,139,250,.25);border-radius:22px;padding:24px 26px;box-shadow:0 30px 70px rgba(0,0,0,.55)">
    <div style="display:flex;align-items:center;gap:10px"><img src="${u('tantra-mark-white.png')}" style="height:30px"><div><div style="font-weight:750;font-size:17px">${c.card_title}</div><div style="font-size:13px;color:#8d93a8;margin-top:2px">45 min &#183; Video call</div></div></div>
    <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:20px">${['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d) => `<div style="text-align:center;font-size:11px;color:#6b7086;font-weight:700">${d}</div>`).join('')}${days}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:18px">${slots.map((s, i) => `<div style="border-radius:10px;padding:10px;text-align:center;font-weight:700;font-size:15px;${i === 1 ? 'background:#6d4aff;color:#fff' : 'border:1px solid rgba(167,139,250,.35);color:#d9d2ff'}">${s}</div>`).join('')}</div>
  </div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:78px;background:rgba(255,255,255,.035);border-top:1px solid rgba(255,255,255,.07);display:flex;align-items:center;gap:22px;padding:0 40px;justify-content:center">
    ${chips(['google', 'amazon', 'techstars', 'upgrad', 'licious', 'leapwork', 'dataguard', 'cavli'], 8, 128, 52, 2600, 30, 12)}
  </div>
</div>`;
}

// ---- render ----
const cutDims = {};
{
  // PNG width and height from the IHDR chunk (no image library needed).
  for (const k of Object.keys(PEOPLE)) {
    const b = fs.readFileSync(path.join(SRC, `cutouts/${k}.png`));
    cutDims[k] = { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  }
}
fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
// Caption test (Adi 2026-11-13): each asset carries the caption copy.caption_by_asset names.
const CAP = (k) => copy.captions[copy.caption_by_asset[k]];
const jobs = [
  ...Object.keys(PEOPLE).map((k) => [`${k}-cover-1584x396`, cover(k, CAP(k)), 1584, 396]),
  ...['scott', 'conor'].map((k) => [`${k}-cover-1584x396`, evangelistCover(k, CAP(k)), 1584, 396]),
  ...Object.entries(COMPANY_VARIANTS).map(([v, f]) => [`tantra-collage-${v}`, f(), 380, 200, [[3.5, '-1330x700']]]),
  ...Object.keys(COMPANY_VARIANTS).map((v) => [`tantra-company-cover-${v}`, companyCover(v, CAP('company')), 1200, 200, [[1, '-1200x200'], [3.5, '-4200x700']]]),

  ['featured-workshop-1200x627', workshop(), 1200, 627],
  ['featured-consultation-1200x627', consult(), 1200, 627],
];
const problems = [];
for (const [name, body, w, h, scales] of jobs) {
  for (const [dsf, suffix] of scales || [[1, ''], [2, '@2x']]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dsf });
    const tmp = path.join(HERE, '.build', `${path.basename(name)}.html`);
    fs.mkdirSync(path.dirname(tmp), { recursive: true });
    fs.writeFileSync(tmp, `<!doctype html><html><head><meta charset="utf-8"><style>${BASE}</style></head><body>${body}</body></html>`);
    await page.goto('file://' + tmp, { waitUntil: 'load' });
    const broken = await page.evaluate(() => [...document.images].filter((i) => !i.naturalWidth).map((i) => i.src));
    if (broken.length) problems.push(`${name}: missing image ${broken.join(', ')}`);
    await page.evaluate(() => document.fonts.ready);
    const over = await page.evaluate(() => [...document.querySelectorAll('.h,.bar,.kicker,.logos')].filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.textContent.slice(0, 40)));
    if (over.length) problems.push(`${name}: text overflow ${over.join(' | ')}`);
    fs.mkdirSync(path.dirname(path.join(OUT, name)), { recursive: true });
    await page.locator('#cap').screenshot({ path: path.join(OUT, `${name}${GUIDES ? '-guides' : ''}${suffix}.png`) });
    await page.close();
  }
}
await browser.close();
console.log(problems.length ? problems.join('\n') : `ok: ${jobs.length} images x 2 scales`);
