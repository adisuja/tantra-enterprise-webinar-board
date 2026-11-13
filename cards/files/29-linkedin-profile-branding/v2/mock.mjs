// Visual check: each cover inside LinkedIn-sized top cards (desktop 804 px column, phone 390 px), photo where LinkedIn puts it.
import { createRequire } from 'node:module';
import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_FROM || 'playwright');
const HERE = path.dirname(fileURLToPath(import.meta.url)); const A = (f) => 'file://' + path.join(HERE, f);
const PHOTO = { adi: 'src/adi-avatar-headshot.jpg' };
const card = (cover, w, ratio, ph, phx, phTop, name, round = true, photo) => `<div style="width:${w}px;background:#fff;border-radius:${w > 500 ? 8 : 0}px;overflow:hidden;font-family:Inter,Arial;box-shadow:0 0 0 1px #ddd;margin-bottom:24px">
 <div style="position:relative;width:${w}px;height:${w / ratio}px;background:url(${A(cover)}) center/cover"></div>
 <div style="position:relative;height:${ph - (w / ratio - phTop) + 90}px;padding:0 ${phx}px">
  <div style="position:absolute;left:${phx}px;top:${phTop - w / ratio}px;width:${ph}px;height:${ph}px;border-radius:${round ? '50%' : '6px'};border:4px solid #fff;background:${photo ? `url(${A(photo)}) center/cover` : '#cfd5dd'};box-sizing:border-box"></div>
  <div style="position:absolute;left:${phx}px;bottom:24px;font-size:${w > 500 ? 24 : 20}px;font-weight:700;color:#191919">${name}</div></div></div>`;
const ppl = { adi: 'Adithya Murali', aquila: 'Aquila Eldho', ben: 'Ben Basil Tomy', bharath: 'Bharath', nelbin: 'Nelbin', bhaskar: 'Bhaskar' };
const b = await chromium.launch(); fs.mkdirSync(path.join(HERE, 'shots'), { recursive: true });
for (const [k, n] of Object.entries(ppl)) {
  const html = `<body style="margin:24px;background:#f4f2ee"><div style="display:flex;gap:28px;align-items:flex-start">
   ${card(`assets/${k}-cover-1584x396.png`, 804, 4, 160, 24, 89, n, true, PHOTO[k] || `src/cutouts/${k}.png`)}
   ${card(`assets/${k}-cover-1584x396.png`, 390, 4, 112, 16, 40, n, true, PHOTO[k] || `src/cutouts/${k}.png`)}</div></body>`;
  const p = await b.newPage({ viewport: { width: 1290, height: 470 } }); await p.setContent(html);
  fs.writeFileSync(path.join(HERE, '.build', 'mock.html'), html); await p.goto(A('.build/mock.html'));
  await p.screenshot({ path: path.join(HERE, `shots/mock-${k}.png`) }); await p.close();
}
const html = `<body style="margin:24px;background:#f4f2ee"><div style="display:flex;gap:28px;align-items:flex-start">
 ${card('assets/tantra-company-cover-strips-violet-4200x700.png', 804, 6, 104, 24, 92, 'Tantra', false, 'src/tantra-mark-white.png')}
 ${card('assets/tantra-company-cover-strips-violet-4200x700.png', 390, 6, 72, 16, 40, 'Tantra', false, 'src/tantra-mark-white.png')}</div></body>`;
fs.writeFileSync(path.join(HERE, '.build', 'mock.html'), html);
const p = await b.newPage({ viewport: { width: 1290, height: 360 } }); await p.goto(A('.build/mock.html'));
await p.screenshot({ path: path.join(HERE, 'shots/mock-company.png') }); await b.close(); console.log('mocks ok');
