// Item 29 v2 to Tantra Brand: post the rendered images and their layout to each Brand project, for the runner Mac.
// build.mjs writes assets/<name>.layout.json next to each image (text, logo chips, caption box, safe zone); Tantra's
// image checks read that layout (POST /api/branding/projects/:id/assets, meta). Images are fetched by Tantra from the
// published team pack (PACK_URL) and stored in its own R2, so nothing is uploaded from this Mac.
//
//   node post-assets.mjs                 dry run: the plan, nothing posted
//   node post-assets.mjs --send          post (TANTRA_API_KEY, a team key; KEY_FILE works too)
//   ONLY=scott,conor node post-assets.mjs --send
//   Verified projects (live on LinkedIn and matching the spec) are skipped unless FORCE=1.
//
// A person's cover and photo need their AI avatar consent in their project first: Tantra answers 409 without it, and
// this script reports that person as waiting on consent. It never touches LinkedIn.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ASSETS = path.join(HERE, 'assets');
const env = process.env;
const API = (env.TANTRA_API_URL || 'https://crm-api.usetantra.com').replace(/\/$/, '');
const PACK = (env.PACK_URL || 'https://adisuja.github.io/tantra-enterprise-webinar-pages/linkedin-profiles/v2/assets').replace(/\/$/, '');
const SEND = process.argv.includes('--send');
const ONLY = env.ONLY ? new Set(env.ONLY.split(',')) : null;
const KEY = env.TANTRA_API_KEY || (env.KEY_FILE ? fs.readFileSync(env.KEY_FILE, 'utf8').trim() : '');
const COMPANY_COVER = env.COMPANY_COVER || 'tantra-company-cover-strips-violet'; // A2, chosen by Adi on 13 Nov

const layout = (name) => { try { return JSON.parse(fs.readFileSync(path.join(ASSETS, `${name}.layout.json`), 'utf8')); } catch { return null; } };
const exists = (file) => fs.existsSync(path.join(ASSETS, file));

/** person_key, element, image file, layout name, size. */
function plan() {
  const rows = [];
  for (const f of fs.readdirSync(ASSETS)) {
    const m = /^([a-z]+)-cover-1584x396\.png$/.exec(f);
    if (m) rows.push({ person_key: m[1], element: 'cover', file: f, layout: `${m[1]}-cover-1584x396`, width: 1584, height: 396 });
    const ph = /^([a-z]+)-photo-1200\.png$/.exec(f);
    // photos.mjs draws no text and no logos: the layout says so.
    if (ph) rows.push({ person_key: ph[1], element: 'photo', file: f, meta: { text: [], logos: [] }, width: 1200, height: 1200 });
  }
  if (exists(`${COMPANY_COVER}-4200x700.png`)) rows.push({ person_key: 'tantra', element: 'cover', file: `${COMPANY_COVER}-4200x700.png`, layout: `${COMPANY_COVER}-1200x200`, width: 4200, height: 700 });
  // Featured images: the same two on every profile; their copy and links stay as approved, only the image is posted.
  return rows.filter((r) => !ONLY || ONLY.has(r.person_key)).sort((a, b) => a.person_key.localeCompare(b.person_key));
}

async function api(method, p, body) {
  const r = await fetch(API + p, { method, headers: { authorization: `Bearer ${KEY}`, 'content-type': 'application/json', 'user-agent': 'tantra-branding-render/1.0' }, body: body ? JSON.stringify(body) : undefined });
  const text = await r.text();
  let json = null; try { json = JSON.parse(text); } catch { /* text */ }
  return { status: r.status, body: json ?? text };
}

const rows = plan();
if (!SEND) {
  for (const r of rows) {
    const meta = r.meta ?? layout(r.layout);
    console.log(`${r.person_key.padEnd(8)} ${r.element.padEnd(6)} ${PACK}/${r.file}  layout: ${meta ? `${meta.text.length} text lines, ${meta.logos.length} logos${meta.caption ? ', caption' : ''}` : 'MISSING (run build.mjs)'}`);
  }
  console.log(`\nDry run: ${rows.length} images. Add --send to post them (TANTRA_API_KEY).`);
  process.exit(0);
}
if (!KEY) { console.error('Set TANTRA_API_KEY (or KEY_FILE) to a team key'); process.exit(1); }
const projects = (await api('GET', '/api/branding/projects')).body?.projects ?? [];
const byKey = new Map(projects.map((p) => [`${p.kind === 'page' ? 'page' : 'profile'}:${p.person_key}`, p]));
let posted = 0;
for (const r of rows) {
  const p = byKey.get(`${r.person_key === 'tantra' ? 'page' : 'profile'}:${r.person_key}`);
  if (!p) { console.log(`skip ${r.person_key} ${r.element}: no Brand project`); continue; }
  // A verified project matches LinkedIn live; a posted image would reopen it as a proposal.
  if (p.status === 'verified' && env.FORCE !== '1') { console.log(`skip ${r.person_key} ${r.element}: verified (live matches the spec); FORCE=1 to post anyway`); continue; }
  const meta = r.meta ?? layout(r.layout);
  if (!meta) { console.log(`skip ${r.person_key} ${r.element}: no layout, run build.mjs first`); continue; }
  const res = await api('POST', `/api/branding/projects/${p.id}/assets`, { element: r.element, url: `${PACK}/${r.file}`, meta, source: 'render', width: r.width, height: r.height });
  if (res.status === 409) console.log(`wait ${r.person_key} ${r.element}: ${res.body?.error ?? 'needs AI avatar consent in the intake'}`);
  else if (res.status >= 300) console.log(`FAIL ${r.person_key} ${r.element}: ${res.status} ${JSON.stringify(res.body).slice(0, 200)}`);
  else { posted++; console.log(`ok   ${r.person_key} ${r.element}: ${res.body?.asset?.id ?? ''}`); }
}
console.log(`\nPosted ${posted} of ${rows.length}.`);
