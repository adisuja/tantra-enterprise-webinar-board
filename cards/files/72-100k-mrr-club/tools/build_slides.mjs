// Build the course slides: plain white, black text, Inter only (Adi 2026-11-13).
// Reads every scripts/V*.md, takes the "## Slides" section ("### <heading>" then "- <pointer>" lines),
// writes one HTML deck per video to slides/<id>.html, an index at slides/index.html,
// and 1920x1080 PNGs to site/slides-png/<id>/ for the video editor (site/ is never mirrored to the board).
// usage: node tools/build_slides.mjs [--no-png]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SCRIPTS = path.join(ROOT, 'scripts');
const OUT = path.join(ROOT, 'slides');
const PNG = path.join(ROOT, 'site', 'slides-png');
const wantPng = !process.argv.includes('--no-png');

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function parse(file) {
  const text = fs.readFileSync(file, 'utf8');
  const id = path.basename(file, '.md').split('-')[0];
  const title = (text.match(/^# (.+)$/m) || [, id])[1].trim();
  const mod = (text.match(/^- Module: (.+)$/m) || [, ''])[1].trim();
  const sec = text.split(/^## /m).find(s => s.startsWith('Slides')) || '';
  const slides = [];
  for (const block of sec.split(/^### /m).slice(1)) {
    const lines = block.split('\n');
    const heading = lines[0].replace(/^Slide \d+:\s*/, '').trim();
    const points = lines.slice(1).filter(l => /^- /.test(l)).map(l => l.slice(2).trim());
    slides.push({ heading, points });
  }
  return { id, title, mod, slides, file: path.basename(file) };
}

const CSS = `@font-face{font-family:Inter;src:local('Inter')}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#fff;color:#000;font-family:Inter,system-ui,sans-serif}
.slide{width:1920px;height:1080px;padding:140px 180px;display:flex;flex-direction:column;justify-content:center;background:#fff;border-bottom:1px solid #eee;position:relative}
.slide h1{font-size:84px;font-weight:700;line-height:1.1;letter-spacing:-1.5px;max-width:1500px}
.slide ul{list-style:none;margin-top:64px}
.slide li{font-size:46px;line-height:1.35;margin:0 0 26px;padding-left:44px;position:relative;max-width:1450px}
.slide li:before{content:'';position:absolute;left:0;top:24px;width:14px;height:14px;background:#000}
.slide .tag{position:absolute;left:180px;bottom:80px;font-size:26px;color:#000;opacity:.45}
.slide .n{position:absolute;right:180px;bottom:80px;font-size:26px;opacity:.45}
.slide.cover h1{font-size:104px}
.slide.cover .sub{font-size:40px;margin-top:40px;opacity:.6}
@media screen and (max-width:1920px){body{zoom:.5}}`;

function deck(v) {
  const all = [{ cover: true, heading: v.title, points: [] }, ...v.slides];
  const body = all.map((s, i) => s.cover
    ? `<section class="slide cover"><h1>${esc(v.title.replace(/^V\d+:\s*/, ''))}</h1><p class="sub">${esc(v.mod)}</p><span class="tag">Tantra Academy · The 100K MRR Club</span><span class="n">${esc(v.id)}</span></section>`
    : `<section class="slide"><h1>${esc(s.heading)}</h1>${s.points.length ? '<ul>' + s.points.map(p => `<li>${esc(p)}</li>`).join('') + '</ul>' : ''}<span class="tag">${esc(v.id)} · ${esc(v.title.replace(/^V\d+:\s*/, ''))}</span><span class="n">${i}/${all.length - 1}</span></section>`).join('\n');
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${esc(v.id)} slides</title><style>${CSS}</style></head><body>${body}</body></html>`;
}

const files = fs.readdirSync(SCRIPTS).filter(f => /^V\d+.*\.md$/.test(f)).sort();
const vids = files.map(f => parse(path.join(SCRIPTS, f)));
fs.mkdirSync(OUT, { recursive: true });
for (const v of vids) fs.writeFileSync(path.join(OUT, `${v.id}.html`), deck(v));
const idx = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Course slides</title><style>body{font-family:Inter,system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 16px;color:#000;background:#fff}li{margin:6px 0}</style></head><body><h1>The 100K MRR Club: course slides</h1><p>${vids.length} videos, ${vids.reduce((a, v) => a + v.slides.length + 1, 0)} slides. White background, black text, Inter.</p><ol>${vids.map(v => `<li><a href="${v.id}.html">${esc(v.title)}</a> (${v.slides.length + 1} slides)</li>`).join('')}</ol></body></html>`;
fs.writeFileSync(path.join(OUT, 'index.html'), idx);
console.log(`decks: ${vids.length}, slides: ${vids.reduce((a, v) => a + v.slides.length + 1, 0)}`);
const empty = vids.filter(v => !v.slides.length).map(v => v.id);
if (empty.length) { console.error('no slides in: ' + empty.join(', ')); process.exitCode = 1; }

function require_global() { return path.join(process.execPath, '..', '..', 'lib', 'node_modules', 'playwright'); }

if (wantPng) {
  // Global Playwright install: ESM import cannot see it, require can (PLAYWRIGHT_FROM overrides).
  const { createRequire } = await import('node:module');
  const req = createRequire(process.env.PLAYWRIGHT_FROM || import.meta.url);
  let pw; try { pw = req('playwright'); } catch { pw = req(require_global()); }
  const { chromium } = pw;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  let n = 0;
  for (const v of vids) {
    const dir = path.join(PNG, v.id);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    await page.setContent(deck(v).replace('@media screen and (max-width:1920px){body{zoom:.5}}', ''));
    const els = await page.$$('section.slide');
    for (let i = 0; i < els.length; i++) {
      await els[i].screenshot({ path: path.join(dir, `${String(i).padStart(2, '0')}.png`) });
      n++;
    }
  }
  await browser.close();
  console.log(`png: ${n} in ${path.relative(ROOT, PNG)}`);
}
