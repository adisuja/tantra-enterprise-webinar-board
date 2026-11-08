#!/usr/bin/env node
// Builds the static review site from funnel-config.json.
// usage: node build.mjs [--config <path to funnel-config.json>] [--out <dir>] [--version <asset cache key>]
// Default config: ../_shared/funnel-config.json. Default output: ./site
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { makeCtx, icsFile } from './src/lib.mjs';
import * as registration from './src/pages/registration.mjs';
import * as registrationB from './src/pages/registration-b.mjs';
import * as thankYou from './src/pages/thank-you.mjs';
import * as vip from './src/pages/vip.mjs';
import * as confirmed from './src/pages/confirmed.mjs';
import * as calculator from './src/pages/calculator.mjs';
import * as watch from './src/pages/watch.mjs';
import * as recording from './src/pages/recording.mjs';
import * as dd from './src/pages/due-diligence.mjs';
import * as privacy from './src/pages/privacy-policy.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => (process.argv.includes(k) ? path.resolve(process.argv[process.argv.indexOf(k) + 1]) : d);
const cfgPath = arg('--config', path.join(here, '..', '_shared', 'funnel-config.json'));
const out = arg('--out', path.join(here, 'site'));
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
// --version pins the ?v= asset cache key, so a rebuild can be diffed byte for byte against the last one.
// Default: a hash of the assets and the config, so an unchanged build is byte for byte the same on every machine (no noise in team pull requests).
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));
const contentHash = () => { const h = crypto.createHash('sha256'); for (const f of walk(path.join(here, 'src'))) h.update(fs.readFileSync(f)); h.update(JSON.stringify(cfg)); return h.digest('hex').slice(0, 10); };
const version = process.argv.includes('--version') ? process.argv[process.argv.indexOf('--version') + 1] : contentHash();

fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
fs.cpSync(path.join(here, 'src', 'assets'), path.join(out, 'assets'), { recursive: true });

const pages = [registration, registrationB, thankYou, vip, confirmed, calculator, watch, recording, ...dd.pages, privacy];
let ics = null;
for (const page of pages) {
  const ctx = makeCtx(cfg, page.route);
  ctx.version = version;
  // The only values the browser needs. No keys, no personal data.
  ctx.client = {
    webinar_date: ctx.known('webinar.first_date') ? ctx.get('webinar.first_date') : null,
    // Live, the form posts to the register Worker (item 17), never to the CRM directly.
    register_worker_url: ctx.known('integrations.register_worker_url') ? ctx.get('integrations.register_worker_url') : null,
    // LIVE mode only when both the Worker URL and the Turnstile site key are filled; otherwise the review stub.
    live: ctx.known('integrations.register_worker_url') && ctx.known('integrations.turnstile_site_key'),
    thank_you_path: `${ctx.rel}thank-you/`,
    cal_namespace: ctx.known('booking.embed_namespace') ? ctx.get('booking.embed_namespace') : null,
    // The thank-you flow after registration: survey (/thank-you/), the Tantra RevOps OS upsell (/funnelos/), confirmed (/confirmed/), plan (/calculator/).
    flow: { vip_path: `${ctx.rel}funnelos/`, confirmed_path: `${ctx.rel}confirmed/`, calculator_path: `${ctx.rel}calculator/`, vip_checkout_url: ctx.known('offer.vip_checkout_url') ? ctx.get('offer.vip_checkout_url') : null },
  };
  ics = ics || icsFile(ctx);
  const dir = path.join(out, page.route);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), page.render(ctx));
  console.log('built', page.route);
}
if (ics) fs.writeFileSync(path.join(out, 'assets', 'webinar.ics'), ics);
fs.writeFileSync(path.join(out, 'robots.txt'), 'User-agent: *\nDisallow: /\n');
fs.writeFileSync(path.join(out, '.nojekyll'), '');
// The upsell page moved from /vip/ to /funnelos/ (Adi 2026-11-08). Old links keep working, query string included.
fs.mkdirSync(path.join(out, 'vip'), { recursive: true });
fs.writeFileSync(path.join(out, 'vip', 'index.html'), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>Moved | Tantra</title><link rel="canonical" href="../funnelos/"><script>location.replace('../funnelos/' + location.search + location.hash)</script><meta http-equiv="refresh" content="0;url=../funnelos/"></head><body><p><a href="../funnelos/">Continue to the next step</a></p></body></html>\n`);
fs.writeFileSync(path.join(out, '404.html'), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Page not found | Tantra</title><link rel="stylesheet" href="/tantra-enterprise-webinar-pages/assets/site.css"></head><body><main class="light"><div class="wrap center"><h1 class="caps">Page Not Found</h1><p>This page does not exist. <a href="/tantra-enterprise-webinar-pages/">Go to the registration page</a>.</p></div></main></body></html>\n`);
console.log(`site written to ${out}${ics ? ' (with webinar.ics)' : ' (no .ics: date, time or time zone still FILL)'}`);
