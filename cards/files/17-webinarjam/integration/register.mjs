// Registration bridge: our registration page -> WebinarJam /register (personal join link) + CRM webinar.registered.
//
// Runs two ways:
//   1. As a Cloudflare Worker (export default.fetch) at integrations.register_worker_url. The registration page
//      POSTs its CRM_CONTRACT body plus a top-level `turnstile_token`. Secrets live in the Worker's environment only:
//        WEBINARJAM_API_KEY     WebinarJam API key (Webinars, Advanced, API custom integration)
//        CRM_SHARED_SECRET      the CRM web app's ?k= secret (deliverables/23-crm, Script Properties)
//        TURNSTILE_SECRET_KEY   Cloudflare Turnstile secret for the registration page's widget
//        DRY_RUN=1              print every request instead of sending it (also allows the review site origin)
//   2. From the command line (Node 18+), dry run unless --live:
//        node register.mjs --body file.json [--fixture webinar.json] [--now ISO]
//        node register.mjs --bulk rsvps.csv --source calendar_manual|calendar_auto          (SOP step 21)
//        node register.mjs --reconcile --date YYYY-MM-DD --crm-csv webinar-tab.csv          (WebinarJam vs CRM)
//
// Everything else reads from deliverables/_shared/funnel-config.json.

import config from '../../_shared/funnel-config.json' with { type: 'json' };
import { isFill, isEmail, isoZ, zonedToUtc, localDate, parseCsv, findColumn, sleep } from './lib.mjs';

const WJ_API = 'https://api.webinarjam.com/webinarjam';
const TURNSTILE_VERIFY = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
// webinar.registered data fields in CRM_CONTRACT.md (utm_* handled separately).
const CONTRACT_DATA_KEYS = ['first_name', 'last_name', 'company', 'phone', 'whatsapp_opt_in', 'call_opt_in', 'newsletter_opt_in', 'timezone', 'join_url', 'revenue_band', 'invest_12m'];
const BOOL_KEYS = ['whatsapp_opt_in', 'call_opt_in', 'newsletter_opt_in'];
const MAX_LEN = { email: 254, first_name: 60, last_name: 60, company: 120, phone: 32, timezone: 64, revenue_band: 60, invest_12m: 10, utm: 200 };
const WEB_SOURCES = ['registration_page'];
const CLI_SOURCES = ['calendar_manual', 'calendar_auto'];

// WebinarJam's /register needs timezone_id for registrants in Texas: 2 = Mountain, 3 = Central (help article 15370151).
// We only know the browser's IANA zone, so US Central and Mountain zones send the matching id; others send none.
const TZ_ID = {
  'America/Chicago': 3, 'America/Indiana/Knox': 3, 'America/Indiana/Tell_City': 3, 'America/Menominee': 3,
  'America/North_Dakota/Center': 3, 'America/North_Dakota/New_Salem': 3, 'America/North_Dakota/Beulah': 3,
  'America/Denver': 2, 'America/Boise': 2, 'America/Phoenix': 2,
};

const originOf = (v) => { try { return isFill(v) ? '' : new URL(/^https?:\/\//.test(v) ? v : `https://${v}`).origin; } catch { return ''; } };

export function settings(env = {}) {
  const i = config.integrations || {};
  const d = config.domains || {};
  const webinarId = !isFill(i.webinarjam_webinar_id) ? i.webinarjam_webinar_id : env.WEBINARJAM_WEBINAR_ID;
  const funnel = originOf(d.funnel_domain);
  const dryRun = env.DRY_RUN === '1';
  return {
    apiKey: env.WEBINARJAM_API_KEY,
    webinarId: isFill(webinarId) ? null : String(webinarId),
    crmUrl: isFill(i.crm_webhook_url) ? null : i.crm_webhook_url,
    crmSecret: env.CRM_SHARED_SECRET,
    turnstileSecret: env.TURNSTILE_SECRET_KEY,
    funnelHost: funnel ? new URL(funnel).hostname : '',
    durationMin: Number(config.webinar.duration_minutes) || 60,
    thankYou: funnel + (d.paths?.thank_you || '/thank-you/'),
    // Production accepts the funnel domain only. The review site is allowed in dry run, never live.
    origins: [funnel, dryRun ? originOf(d.review_site) : ''].filter(Boolean),
    dryRun,
  };
}

// The session a new registrant belongs to: the first one that has not ended yet, so people who
// register during the live hour still land in tonight's room.
export function pickSchedule(webinar, nowMs, durationMin) {
  const tz = webinar.timezone;
  const list = (webinar.schedules || [])
    .map((s) => ({ id: s.schedule, local: s.date, startMs: zonedToUtc(s.date, tz) }))
    .sort((a, b) => a.startMs - b.startMs);
  const next = list.find((s) => s.startMs + durationMin * 60000 > nowMs);
  if (!next) throw new Error('No upcoming session in WebinarJam. Add next week\'s date under Schedules.');
  return { schedule: next.id, startMs: next.startMs, webinar_date: localDate(next.startMs, tz), timezone: tz };
}

// Fallback when WebinarJam cannot be reached: the next session from the config's weekly cadence.
export function nextSessionFromConfig(nowMs, w = config.webinar) {
  if ([w.day_of_week, w.start_time_local, w.timezone].some(isFill) || !/^\d{1,2}:\d{2}$/.test(w.start_time_local)) return null;
  const want = String(w.day_of_week).trim().toLowerCase();
  const dayName = (ms) => new Intl.DateTimeFormat('en-US', { timeZone: w.timezone, weekday: 'long' }).format(new Date(ms)).toLowerCase();
  const dur = (Number(w.duration_minutes) || 60) * 60000;
  if (!isFill(w.first_date) && zonedToUtc(`${w.first_date} ${w.start_time_local}`, w.timezone) + dur > nowMs) return w.first_date;
  for (let d = 0; d <= 8; d++) {
    const at = nowMs + d * 86400000;
    const date = localDate(at, w.timezone);
    if (dayName(at) === want && zonedToUtc(`${date} ${w.start_time_local}`, w.timezone) + dur > nowMs) return date;
  }
  return null;
}

export function wjRegisterForm(s, webinarId, schedule, body) {
  const d = body.data || {};
  const form = { api_key: s.apiKey || '<WEBINARJAM_API_KEY>', webinar_id: webinarId, schedule, first_name: String(d.first_name || '').trim() || 'there', email: body.email };
  if (d.last_name) form.last_name = String(d.last_name).trim();
  if (TZ_ID[d.timezone]) form.timezone_id = TZ_ID[d.timezone];
  return form;
}

export function crmBody(body, webinarDate, joinUrl) {
  const data = {};
  for (const [k, v] of Object.entries(body.data || {})) if ((CONTRACT_DATA_KEYS.includes(k) || /^utm_/.test(k)) && v !== undefined && v !== '' && v !== null) data[k] = v;
  if (joinUrl) data.join_url = joinUrl;
  return { event: 'webinar.registered', email: String(body.email).trim().toLowerCase(), ts: body.ts || isoZ(Date.now()), source: body.source || 'registration_page', webinar_date: webinarDate, data };
}

// Checks a body from the open internet. Returns { body } (cleaned) or { error }.
export function validateWebBody(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return { error: 'body must be a JSON object' };
  if (raw.event !== undefined && raw.event !== 'webinar.registered') return { error: 'only webinar.registered' };
  const source = raw.source === undefined ? 'registration_page' : raw.source;
  if (!WEB_SOURCES.includes(source)) return { error: 'source not allowed' };
  const email = String(raw.email ?? '').trim().toLowerCase();
  if (!isEmail(email) || email.length > MAX_LEN.email) return { error: 'invalid email' };
  const src = raw.data === undefined ? {} : raw.data;
  if (!src || typeof src !== 'object' || Array.isArray(src)) return { error: 'data must be an object' };
  const data = {};
  for (const [k, v] of Object.entries(src)) {
    if (k === 'join_url') continue; // only the Worker sets it
    if (BOOL_KEYS.includes(k)) { data[k] = v === true || v === 'on' || v === 'yes' || v === 'true'; continue; }
    const isUtm = /^utm_[a-z]+$/.test(k);
    const limit = isUtm ? MAX_LEN.utm : CONTRACT_DATA_KEYS.includes(k) ? MAX_LEN[k] : 0;
    if (!limit) continue; // not a contract field: dropped
    if (typeof v !== 'string' && typeof v !== 'number') return { error: `${k} must be text` };
    const str = String(v).trim();
    if (str.length > limit) return { error: `${k} is too long` };
    if (str) data[k] = str;
  }
  return { body: { event: 'webinar.registered', email, ts: isoZ(Date.now()), source, webinar_date: null, data } };
}

const redactForm = (f) => ({ ...f, api_key: '<WEBINARJAM_API_KEY from env>' });

// Network layer. In dry run it prints and returns canned answers.
// fixtures: { webinar: /webinar response, registrants: /registrants response }
export function client(s, { fixtures = {}, log = console.log } = {}) {
  async function wj(path, form) {
    if (s.dryRun) {
      log(`[dry-run] POST ${WJ_API}/${path} (application/x-www-form-urlencoded)\n${JSON.stringify(redactForm(form), null, 2)}`);
      if (path === 'webinar') return fixtures.webinar || sampleWebinar(s);
      if (path === 'registrants') return fixtures.registrants || { status: 'success', registrants: [] };
      return { status: 'success', user: { live_room_url: 'https://event.webinarjam.com/go/live/DRY-RUN', schedule: form.schedule } };
    }
    if (!s.apiKey) throw new Error('WEBINARJAM_API_KEY is not set in this environment');
    for (let attempt = 0; ; attempt++) {
      const r = await fetch(`${WJ_API}/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams(form) });
      if ((r.status === 429 || r.status >= 500) && attempt < 2) { await sleep(1000 * (attempt + 1)); continue; }
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.status !== 'success') throw new Error(`WebinarJam ${path} ${r.status}: ${j.message || JSON.stringify(j).slice(0, 200)}`);
      return j;
    }
  }
  async function crm(body) {
    const shown = s.crmUrl ? `${s.crmUrl}?k=<CRM_SHARED_SECRET>` : '<integrations.crm_webhook_url>?k=<CRM_SHARED_SECRET>';
    if (s.dryRun) { log(`[dry-run] POST ${shown} (application/json)\n${JSON.stringify(body, null, 2)}`); return { ok: true }; }
    if (!s.crmUrl || !s.crmSecret) throw new Error('crm_webhook_url (funnel-config) or CRM_SHARED_SECRET (env) is missing');
    const r = await fetch(`${s.crmUrl}?k=${encodeURIComponent(s.crmSecret)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), redirect: 'follow' });
    const j = await r.json().catch(() => ({}));
    if (!j.ok) throw new Error(`CRM ${r.status}: ${j.error || 'no ok in reply'}`);
    return j;
  }
  async function turnstile(token, ip) {
    if (s.dryRun) { log(`[dry-run] POST ${TURNSTILE_VERIFY} (secret=<TURNSTILE_SECRET_KEY>, response=<token ${token ? 'present' : 'missing'}>)`); return { ok: true }; }
    if (!s.turnstileSecret) return { ok: false, status: 503, error: 'TURNSTILE_SECRET_KEY is not set' };
    if (!token || String(token).length > 2048) return { ok: false, status: 403, error: 'captcha missing' };
    const form = { secret: s.turnstileSecret, response: String(token) };
    if (ip) form.remoteip = ip;
    const r = await fetch(TURNSTILE_VERIFY, { method: 'POST', body: new URLSearchParams(form) });
    const j = await r.json().catch(() => ({}));
    const ok = j.success === true && (!s.funnelHost || j.hostname === s.funnelHost);
    return ok ? { ok: true } : { ok: false, status: 403, error: 'captcha failed' };
  }
  return { wj, crm, turnstile };
}

function sampleWebinar(s) {
  const day = new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10);
  return { status: 'success', webinar: { webinar_id: s.webinarId || 'FILL', timezone: 'UTC', schedules: [{ date: `${day} 15:00`, schedule: 'DRY-RUN-SCHEDULE', comment: 'dry-run sample session' }] } };
}

let cache = { at: 0, webinar: null };
export const resetCache = () => { cache = { at: 0, webinar: null }; };
async function getWebinar(s, c, nowMs, webinarId) {
  if (cache.webinar && Math.abs(nowMs - cache.at) < 10 * 60000) return cache.webinar;
  const j = await c.wj('webinar', { api_key: s.apiKey || '<WEBINARJAM_API_KEY>', webinar_id: webinarId });
  cache = { at: nowMs, webinar: j.webinar };
  return j.webinar;
}

// Registers one person in WebinarJam and/or the CRM. Returns { ok, webinar_date, join_url, warnings[] }.
// sides: { wj: true, crm: true }. ok means at least one requested side saved the person.
export async function registerOne(body, s, c, nowMs = Date.now(), sides = { wj: true, crm: true }) {
  if (!isEmail(body.email)) return { ok: false, error: 'invalid email' };
  if (sides.wj && !s.webinarId && !s.dryRun) return { ok: false, error: 'webinarjam_webinar_id is not set (funnel-config) and WEBINARJAM_WEBINAR_ID is empty' };
  const webinarId = s.webinarId || 'FILL_WEBINARJAM_WEBINAR_ID';
  const warnings = [];
  let saved = 0;
  let webinarDate = null;
  let joinUrl = body.data?.join_url || null;
  if (sides.wj) {
    try {
      const w = await getWebinar(s, c, nowMs, webinarId);
      const pick = pickSchedule(w, nowMs, s.durationMin);
      webinarDate = pick.webinar_date;
      const r = await c.wj('register', wjRegisterForm(s, webinarId, pick.schedule, body));
      joinUrl = r.user?.live_room_url || null;
      saved++;
    } catch (e) { warnings.push(`webinarjam: ${e.message}`); }
  }
  if (!webinarDate) webinarDate = body.webinar_date || nextSessionFromConfig(nowMs) || null;
  if (sides.crm) {
    try { await c.crm(crmBody(body, webinarDate, joinUrl)); saved++; } catch (e) { warnings.push(`crm: ${e.message}`); }
  }
  if (warnings.length) console.error('[register]', warnings.join(' | ')); // no email in logs
  return { ok: saved > 0, webinar_date: webinarDate, join_url: joinUrl, warnings };
}

// ---------- Reconcile: WebinarJam registrants vs CRM rows for one session ----------
function registrantRows(j) {
  const r = j.registrants ?? j.data ?? j;
  if (Array.isArray(r)) return r;
  if (r && Array.isArray(r.data)) return r.data;
  return [];
}

// Every WebinarJam registrant for the session on `date` (local date in the webinar's time zone).
export async function wjRegistrants(s, c, date, nowMs = Date.now()) {
  const webinarId = s.webinarId || 'FILL_WEBINARJAM_WEBINAR_ID';
  const w = await getWebinar(s, c, nowMs, webinarId);
  const sch = (w.schedules || []).find((x) => localDate(zonedToUtc(x.date, w.timezone), w.timezone) === date);
  if (!sch) throw new Error(`No WebinarJam session on ${date}`);
  const out = new Map();
  for (let page = 1; page <= 200; page++) {
    const j = await c.wj('registrants', { api_key: s.apiKey || '<WEBINARJAM_API_KEY>', webinar_id: webinarId, schedule_id: sch.schedule, page });
    const rows = registrantRows(j);
    let added = 0;
    for (const r of rows) {
      const email = String(r.email || '').trim().toLowerCase();
      if (isEmail(email) && !out.has(email)) { out.set(email, r); added++; }
    }
    const last = j.registrants?.last_page ?? j.last_page;
    if (!added || (last && page >= last)) break;
  }
  return out;
}

// crmEmails: Set of emails the CRM has for the date. Returns who each side is missing.
export function reconcilePlan(wjMap, crmEmails) {
  const toWj = [...crmEmails].filter((e) => !wjMap.has(e));
  const toCrm = [...wjMap.keys()].filter((e) => !crmEmails.has(e));
  return { toWj, toCrm };
}

// ---------- Worker ----------
export default {
  async fetch(req, env) {
    const s = settings(env);
    const origin = req.headers.get('Origin') || '';
    const allowed = s.origins.includes(origin);
    const h = { 'Content-Type': 'application/json', Vary: 'Origin' };
    if (allowed) Object.assign(h, { 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
    const reply = (status, obj) => new Response(obj === null ? null : JSON.stringify(obj), { status, headers: h });
    if (!allowed) return reply(403, { ok: false, error: 'origin not allowed' });
    if (req.method === 'OPTIONS') return reply(204, null);
    if (req.method !== 'POST') return reply(405, { ok: false, error: 'POST only' });
    let raw;
    try { raw = await req.json(); } catch { return reply(400, { ok: false, error: 'body is not JSON' }); }
    try {
      const v = validateWebBody(raw);
      if (v.error) return reply(400, { ok: false, error: v.error });
      const c = client(s);
      const t = await c.turnstile(raw.turnstile_token, req.headers.get('CF-Connecting-IP'));
      if (!t.ok) return reply(t.status, { ok: false, error: t.error });
      const res = await registerOne(v.body, s, c);
      return res.ok ? reply(200, { ok: true, redirect: s.thankYou }) : reply(502, { ok: false, error: 'could not save your seat' });
    } catch (e) {
      console.error('[register] unexpected', e && e.message);
      return reply(500, { ok: false, error: 'server error' });
    }
  },
};

// ---------- CLI ----------
async function cli(argv) {
  const { readFileSync } = await import('node:fs');
  const arg = (k) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
  const live = argv.includes('--live');
  const s = settings({ ...process.env, DRY_RUN: live ? '0' : '1' });
  const fixtures = {};
  if (arg('--fixture')) fixtures.webinar = JSON.parse(readFileSync(arg('--fixture'), 'utf8'));
  if (arg('--registrants-fixture')) fixtures.registrants = JSON.parse(readFileSync(arg('--registrants-fixture'), 'utf8'));
  const now = arg('--now') ? Date.parse(arg('--now')) : Date.now();
  const c = client(s, { fixtures });
  console.log(live ? '[live] sending' : '[dry-run] nothing is sent; add --live to send');
  const pace = () => sleep(live ? 200 : 0); // 5 people a second, under WebinarJam's 20 calls a second (help article 15370144)

  if (arg('--body')) {
    console.log(JSON.stringify(await registerOne(JSON.parse(readFileSync(arg('--body'), 'utf8')), s, c, now), null, 2));
    return;
  }

  if (argv.includes('--reconcile')) {
    const date = arg('--date');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date || '') || !arg('--crm-csv')) throw new Error('usage: --reconcile --date YYYY-MM-DD --crm-csv webinar-tab.csv');
    const rows = parseCsv(readFileSync(arg('--crm-csv'), 'utf8'));
    const head = rows.shift() || [];
    const ce = findColumn(head, ['email']), cd = findColumn(head, ['webinar_date', 'webinar date']);
    const cf = findColumn(head, ['first_name', 'first name']), cl = findColumn(head, ['last_name', 'last name']);
    if (ce < 0) throw new Error('No email column in the CRM CSV');
    const crm = new Map();
    for (const r of rows) {
      const e = String(r[ce] || '').trim().toLowerCase();
      if (isEmail(e) && (cd < 0 || String(r[cd]).slice(0, 10) === date)) crm.set(e, { first_name: cf >= 0 ? r[cf].trim() : '', last_name: cl >= 0 ? r[cl].trim() : '' });
    }
    const wjMap = await wjRegistrants(s, c, date, now);
    const plan = reconcilePlan(wjMap, new Set(crm.keys()));
    console.log(`reconcile ${date}: WebinarJam ${wjMap.size}, CRM ${crm.size}; ${plan.toWj.length} missing in WebinarJam, ${plan.toCrm.length} missing in the CRM`);
    for (const email of plan.toWj) { // WebinarJam only: the CRM already has their webinar.registered
      const p = crm.get(email);
      await registerOne({ email, source: 'registration_page', data: { first_name: p.first_name, last_name: p.last_name } }, s, c, now, { wj: true, crm: false });
      await pace();
    }
    for (const email of plan.toCrm) { // CRM only: WebinarJam already has them and their link
      const r = wjMap.get(email);
      await registerOne({ email, source: 'webinarjam_reconcile', webinar_date: date, data: { first_name: r.first_name || '', last_name: r.last_name || '', join_url: r.live_room || '' } }, s, c, now, { wj: false, crm: true });
      await pace();
    }
    return;
  }

  if (arg('--bulk')) {
    const source = arg('--source');
    if (!CLI_SOURCES.includes(source)) throw new Error(`--source must be one of ${CLI_SOURCES.join(', ')}`);
    const rows = parseCsv(readFileSync(arg('--bulk'), 'utf8'));
    const head = rows.shift() || [];
    const col = { first: findColumn(head, ['first_name', 'first name']), last: findColumn(head, ['last_name', 'last name']), email: findColumn(head, ['email', 'email address']), company: findColumn(head, ['company', 'company name']) };
    if (col.email < 0) throw new Error('No email column in the CSV');
    const seen = new Set(); let ok = 0, bad = 0, failed = 0;
    for (const r of rows) {
      const email = String(r[col.email] || '').trim().toLowerCase();
      if (!isEmail(email) || seen.has(email)) { bad++; continue; }
      seen.add(email);
      const data = source.startsWith('calendar_') ? { utm_source: 'calendar', utm_medium: source } : {};
      if (col.first >= 0 && r[col.first].trim()) data.first_name = r[col.first].trim();
      if (col.last >= 0 && r[col.last].trim() && r[col.last].trim() !== '.') data.last_name = r[col.last].trim();
      if (col.company >= 0 && r[col.company].trim()) data.company = r[col.company].trim();
      const res = await registerOne({ event: 'webinar.registered', email, ts: isoZ(now), source, data }, s, c, now);
      if (res.ok && !res.warnings.length) ok++; else failed++;
      await pace();
    }
    console.log(`bulk: ${ok} registered, ${failed} with a warning, ${bad} skipped (bad or duplicate email)`);
    return;
  }
  console.log('usage: node register.mjs --body file.json | --bulk rsvps.csv --source calendar_manual|calendar_auto | --reconcile --date YYYY-MM-DD --crm-csv file.csv  [--fixture webinar.json] [--registrants-fixture r.json] [--now ISO] [--live]');
}

if (typeof process !== 'undefined' && process.argv?.[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  cli(process.argv.slice(2)).catch((e) => { console.error(e.message); process.exit(1); });
}
