#!/usr/bin/env node
// Card 92: the weekly webinar cycle. One command per job, safe to run any time (every job is idempotent).
//
//   node cycle.mjs plan                  which session is last, next and after (from funnel-config.json)
//   node cycle.mjs check                 every surface for the next session: pages, calendar file, WebinarJam,
//                                        registrations, CRM sequences, templates, senders, AI calling, tracking, dashboard
//   node cycle.mjs roll [--apply]        move the per-session settings to the next session (CRM tracking campaign names);
//                                        without --apply it only prints what it would change
//   node cycle.mjs e2e [--live] [--keep] the fast end-to-end test inside the CRM: a test pipeline with copies of every
//                                        webinar sequence, timings squeezed into about 20 minutes, three test deals
//                                        (attended, missed, rescheduled), then every step and the tracking events checked.
//                                        Dry run unless --live (live sends only to E2E_EMAIL and E2E_PHONE).
//
// Options: --json <file> writes the report as JSON. On GitHub Actions the report also goes to the job summary.
// Credentials: TANTRA_CRM_API_KEY (CRM, X-API-Key) and CLOUDFLARE_API_TOKEN (dashboard and registration databases).
// In a Claude cloud session both are added by the network proxy, so neither variable is needed there.
// No em or en dashes in anything this prints (the team reads it).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../..');
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, 'deliverables/_shared/funnel-config.json'), 'utf8').replace(/,(\s*[}\]])/g, '$1'));
const C = JSON.parse(fs.readFileSync(path.join(HERE, 'config.json'), 'utf8'));
// The WebinarJam webinar the register Worker uses (its vars WJ_WEBINAR_ID, WJ_HASH, WJ_SLUG): one place for a new webinar link.
const WRANGLER = JSON.parse(fs.readFileSync(path.join(ROOT, 'deliverables/46-funnel-domain/worker/wrangler.jsonc'), 'utf8').replace(/^\s*\/\/.*$/gm, ''));
const WJV = WRANGLER.vars || {};
C.webinarjam.form_embed_url = `https://event.webinarjam.com/register/${WJV.WJ_WEBINAR_ID}/${WJV.WJ_HASH}/form-embed?webinar_id=${WJV.WJ_WEBINAR_ID}`;
C.webinarjam.public_url = `https://event.webinarjam.com/${WJV.WJ_SLUG}/register/${WJV.WJ_HASH}`;
const args = process.argv.slice(2);
const cmd = args[0] || 'check';
const flag = (f) => args.includes(f);
const opt = (f) => (args.includes(f) ? args[args.indexOf(f) + 1] : null);

// ---------- sessions ----------
export function zonedToUtc(date, hhmm, tz) {
  const [y, m, d] = date.split('-').map(Number);
  const [h, mi] = hhmm.split(':').map(Number);
  let guess = Date.UTC(y, m - 1, d, h, mi);
  for (let i = 0; i < 2; i++) {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
      .formatToParts(new Date(guess)).map((x) => [x.type, x.value]));
    guess += Date.UTC(y, m - 1, d, h, mi) - Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second);
  }
  return new Date(guess);
}
const W = CFG.webinar;
const EVERY = Number(W.cadence_days) > 0 ? Number(W.cadence_days) : ({ daily: 1, weekly: 7, fortnightly: 14, biweekly: 14 }[String(W.cadence).toLowerCase()] || 7);
const DUR = Number(W.duration_minutes || 60) * 60000;
export function sessions(now = new Date()) {
  const skip = new Set(W.skip_dates || []);
  const [y, m, d] = W.first_date.split('-').map(Number);
  let last = null;
  const upcoming = [];
  for (let i = 0; i < 3000 && upcoming.length < 4; i++) {
    const date = new Date(Date.UTC(y, m - 1, d + i * EVERY)).toISOString().slice(0, 10);
    if (skip.has(date)) continue;
    const start = zonedToUtc(date, W.start_time_local, W.timezone);
    const s = { date, start, end: new Date(start.getTime() + DUR) };
    if (s.end.getTime() <= now.getTime()) last = s; else upcoming.push(s);
  }
  return { last, next: upcoming[0], after: upcoming.slice(1), every: EVERY };
}
const S = sessions(process.env.CYCLE_NOW ? new Date(process.env.CYCLE_NOW) : new Date());
const campaignFor = (date) => `${C.crm.utm_campaign_prefix}${date}`;
const longDate = (date) => new Intl.DateTimeFormat('en-GB', { timeZone: W.timezone, weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(zonedToUtc(date, W.start_time_local, W.timezone));

// ---------- http (curl: works on GitHub runners and through the Claude cloud proxy) ----------
function http(method, url, { body, headers = {}, raw = false, timeout = 30 } = {}) {
  const a = ['-sS', '-L', '--max-time', String(timeout), '-X', method, url, '-w', '\n%{http_code}', '-A', 'tantra-weekly-cycle/1.0'];
  for (const [k, v] of Object.entries(headers)) if (v) a.push('-H', `${k}: ${v}`);
  if (body !== undefined) a.push('-H', 'content-type: application/json', '--data-binary', JSON.stringify(body));
  let out;
  try { out = execFileSync('curl', a, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] }); }
  catch (e) { return { status: 0, error: String(e.stderr || e.message).trim().split('\n').pop() }; }
  const i = out.lastIndexOf('\n');
  const status = Number(out.slice(i + 1));
  const text = out.slice(0, i);
  if (raw) return { status, text };
  try { return { status, json: JSON.parse(text) }; } catch { return { status, text }; }
}
const CRM = C.crm.api;
const crmHeaders = () => (process.env.TANTRA_CRM_API_KEY ? { 'X-API-Key': process.env.TANTRA_CRM_API_KEY } : {});
function crm(method, p, body) {
  const r = http(method, CRM + p, { body, headers: crmHeaders() });
  if (r.status < 200 || r.status >= 300) throw new Error(`CRM ${method} ${p}: ${r.status} ${r.error || JSON.stringify(r.json || r.text).slice(0, 200)}`);
  return r.json;
}
function d1(db, sql, params = []) {
  const h = process.env.CLOUDFLARE_API_TOKEN ? { Authorization: `Bearer ${process.env.CLOUDFLARE_API_TOKEN}` } : {};
  const r = http('POST', `https://api.cloudflare.com/client/v4/accounts/${C.cloudflare.account_id}/d1/database/${db}/query`, { body: { sql, params }, headers: h });
  if (!r.json?.success) throw new Error(`D1: ${r.status} ${JSON.stringify(r.json?.errors || r.error || '').slice(0, 200)}`);
  return r.json.result[0].results;
}

// ---------- report ----------
const results = [];
const add = (area, name, status, detail = '') => results.push({ area, name, status, detail: String(detail) });
const pass = (a, n, d) => add(a, n, 'pass', d), warn = (a, n, d) => add(a, n, 'warn', d), fail = (a, n, d) => add(a, n, 'fail', d);
async function guard(area, name, fn) { try { await fn(); } catch (e) { fail(area, name, e.message); } }
function report(title) {
  const icon = { pass: 'PASS', warn: 'WARN', fail: 'FAIL', info: 'INFO' };
  const counts = results.reduce((a, r) => ({ ...a, [r.status]: (a[r.status] || 0) + 1 }), {});
  const head = `${title}: next session ${longDate(S.next.date)}, ${W.start_time_local} ${W.timezone} (cadence every ${S.every} days)`;
  const lines = [head, `pass ${counts.pass || 0}, warn ${counts.warn || 0}, fail ${counts.fail || 0}`, ''];
  for (const r of results) lines.push(`${icon[r.status].padEnd(4)}  ${r.area.padEnd(13)} ${r.name}${r.detail ? `: ${r.detail}` : ''}`);
  console.log(lines.join('\n'));
  if (process.env.GITHUB_STEP_SUMMARY) {
    const md = [`## ${head}`, '', `**${counts.fail || 0} failed, ${counts.warn || 0} warnings, ${counts.pass || 0} passed** (${new Date().toISOString()})`, '',
      '| | Area | Check | Detail |', '|---|---|---|---|',
      ...results.map((r) => `| ${{ pass: '✅', warn: '⚠️', fail: '❌', info: 'ℹ️' }[r.status]} | ${r.area} | ${r.name} | ${r.detail.replace(/\|/g, '/').replace(/\n/g, ' ')} |`)];
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, md.join('\n') + '\n\n');
  }
  const out = { kind: cmd, at: new Date().toISOString(), next_session: S.next.date, last_session: S.last?.date ?? null, counts, results };
  if (opt('--json')) fs.writeFileSync(opt('--json'), JSON.stringify(out, null, 2));
  // The dashboard's database keeps every run, so dashboard.usetantra.com can show them (table cycle_checks).
  try {
    d1(C.cloudflare.dashboard_db, 'CREATE TABLE IF NOT EXISTS cycle_checks (id INTEGER PRIMARY KEY AUTOINCREMENT, funnel TEXT, kind TEXT, at TEXT, session TEXT, passed INTEGER, warned INTEGER, failed INTEGER, report TEXT)');
    d1(C.cloudflare.dashboard_db, 'INSERT INTO cycle_checks (funnel, kind, at, session, passed, warned, failed, report) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      [C.dashboard_funnel, cmd, out.at, S.next.date, counts.pass || 0, counts.warn || 0, counts.fail || 0, JSON.stringify(results).slice(0, 90000)]);
  } catch (e) { console.log(`(report not saved to the dashboard database: ${e.message})`); }
  return counts.fail ? 1 : 0;
}

// ---------- checks ----------
async function checkPages() {
  const want = S.next.date;
  for (const p of C.pages) {
    await guard('Pages', p, () => {
      const r = http('GET', C.site + p + `?cycle=${Date.now()}`, { raw: true });
      if (r.status !== 200) return fail('Pages', p, `HTTP ${r.status || r.error}`);
      const d = (r.text.match(/"webinar_date":"([^"]+)"/) || [])[1];
      if (d && d !== want) return fail('Pages', p, `shows the session of ${d}, the next session is ${want}. Run Deploy funnel (the build picks the next session)`);
      pass('Pages', p, d ? `session ${d}` : 'up');
    });
  }
  await guard('Pages', 'Registration page date text', () => {
    const r = http('GET', C.site + '/', { raw: true });
    const label = longDate(want).replace(/^(\w+) /, '$1, ');
    r.text.includes(label) ? pass('Pages', 'Registration page date text', label) : fail('Pages', 'Registration page date text', `"${label}" not on the page`);
  });
  await guard('Pages', 'Calendar file (.ics)', () => {
    const r = http('GET', C.site + '/assets/webinar.ics', { raw: true });
    const st = (r.text.match(/DTSTART:(\d{8})/) || [])[1];
    st === want.replace(/-/g, '') ? pass('Pages', 'Calendar file (.ics)', `starts ${want}`) : fail('Pages', 'Calendar file (.ics)', `starts ${st || 'missing'}, should be ${want}`);
  });
  const plans = CFG.tantra_plans || {};
  if (plans.deadline_utc) {
    const dl = new Date(plans.deadline_utc);
    dl < S.next.start ? warn('Offer', 'Tantra Plans deadline and coupon', `deadline ${plans.deadline_label} (${plans.coupon_code}) is before the next session: needs a new Dodo coupon and deadline in funnel-config.json tantra_plans`)
      : pass('Offer', 'Tantra Plans deadline and coupon', `${plans.coupon_code} until ${plans.deadline_label}`);
  }
}
async function checkWebinarJam() {
  await guard('WebinarJam', 'Next sessions open for registration', () => {
    const r = http('GET', C.webinarjam.form_embed_url, { raw: true, headers: { Accept: 'text/html' } });
    if (r.status !== 200) return warn('WebinarJam', 'Next sessions open for registration', `could not read the WebinarJam form (${r.status || r.error}); check by hand in WebinarJam, Schedules`);
    const dates = JSON.parse((r.text.match(/"registrationDates":(\[[^\]]*\])/) || [])[1] || '[]');
    const days = dates.map((x) => new Date(Number(x.ts) * (String(x.ts).length > 10 ? 1 : 1000)).toISOString().slice(0, 10)).filter(Boolean);
    if (!days.length) return fail('WebinarJam', 'Next sessions open for registration', 'WebinarJam lists no future session: registrations will fail. Add sessions in WebinarJam, Schedules');
    if (days[0] !== S.next.date) return fail('WebinarJam', 'Next sessions open for registration', `first open session is ${days[0]}, the funnel says ${S.next.date}`);
    days.length < C.webinarjam.min_future_sessions ? warn('WebinarJam', 'Next sessions open for registration', `only ${days.length} future sessions (${days.join(', ')}); keep ${C.webinarjam.min_future_sessions}`)
      : pass('WebinarJam', 'Next sessions open for registration', days.join(', '));
    // Phone must be a required field on the WebinarJam form too (Adi, 14 Nov).
    const phoneCfg = (r.text.match(/"(?:phone|phone_number|phoneNumber)"\s*:\s*\{[^{}]*\}/i) || [])[0] || '';
    const req = /"(?:required|is_required|mandatory|isRequired)"\s*:\s*(true|1|"1")/i.test(phoneCfg);
    const off = /"(?:enabled|is_enabled|active|visible)"\s*:\s*(false|0|"0")/i.test(phoneCfg);
    if (req && !off) pass('WebinarJam', 'Phone is a required field on the WebinarJam form', 'required');
    else if (phoneCfg) fail('WebinarJam', 'Phone is a required field on the WebinarJam form', `the form has phone ${off ? 'switched off' : 'as optional'}: WebinarJam, Edit, Registration, Registration form fields, Phone, Required`);
    else warn('WebinarJam', 'Phone is a required field on the WebinarJam form', 'could not read the phone setting from the form; check WebinarJam, Edit, Registration, Registration form fields');
  });
  await guard('WebinarJam', 'WebinarJam registration link', () => {
    const r = http('GET', C.webinarjam.public_url, { raw: true, headers: { Accept: 'text/html' } });
    if (r.status !== 200) return warn('WebinarJam', 'WebinarJam registration link', `${C.webinarjam.public_url} answered ${r.status || r.error}`);
    /webinar (?:is )?(?:not found|no longer|has ended|expired)/i.test(r.text) ? fail('WebinarJam', 'WebinarJam registration link', `${C.webinarjam.public_url} says the webinar is closed`) : pass('WebinarJam', 'WebinarJam registration link', C.webinarjam.public_url);
  });
  await guard('WebinarJam', 'Pages and config point at the same WebinarJam webinar', () => {
    const cfgLink = String(CFG.webinar.join_url || '');
    cfgLink.includes(`/register/${WJV.WJ_HASH}`) ? pass('WebinarJam', 'Pages and config point at the same WebinarJam webinar', `${WJV.WJ_SLUG}/${WJV.WJ_HASH}`)
      : fail('WebinarJam', 'Pages and config point at the same WebinarJam webinar', `funnel-config webinar.join_url is ${cfgLink.split(' ')[0]}, the register Worker uses ${C.webinarjam.public_url}`);
  });
  await guard('Registrations', 'Registrations reach WebinarJam and the CRM', () => {
    const since = (S.last ? S.last.end : new Date(Date.now() - 7 * 864e5)).toISOString();
    const rows = d1(C.cloudflare.registrations_db, "SELECT COUNT(*) n, SUM(CASE WHEN wj_status = 'ok' THEN 1 ELSE 0 END) wj_ok, SUM(CASE WHEN wj_status = 'failed' THEN 1 ELSE 0 END) wj_failed, SUM(CASE WHEN crm_status = 'ok' THEN 1 ELSE 0 END) crm_ok, MAX(ts) last FROM events WHERE event = 'webinar.registered' AND ts > ?", [since])[0];
    if (!rows.n) return warn('Registrations', 'Registrations reach WebinarJam and the CRM', `no registrations since the last session ended (${since.slice(0, 16)})`);
    const d = `${rows.n} since the last session: ${rows.wj_ok} with a WebinarJam link, ${rows.crm_ok} in the CRM, last ${String(rows.last).slice(0, 16)}`;
    rows.wj_failed ? fail('Registrations', 'Registrations reach WebinarJam and the CRM', `${rows.wj_failed} failed in WebinarJam. ${d}`) : rows.crm_ok < rows.n ? warn('Registrations', 'Registrations reach WebinarJam and the CRM', d) : pass('Registrations', 'Registrations reach WebinarJam and the CRM', d);
  });
}
async function checkCrm() {
  let seqs = [];
  await guard('CRM', 'Webinar pipeline and stages', () => {
    const p = crm('GET', '/api/pipelines').pipelines.find((x) => x.id === C.crm.pipeline_id);
    if (!p) return fail('CRM', 'Webinar pipeline and stages', 'pipeline missing');
    const names = p.stages.map((s) => s.name);
    const miss = C.crm.stages.filter((n) => !names.includes(n));
    miss.length ? fail('CRM', 'Webinar pipeline and stages', `missing: ${miss.join(', ')}`) : pass('CRM', 'Webinar pipeline and stages', p.stages.map((s) => `${s.name} ${s.deal_count}`).join(', '));
  });
  await guard('CRM', 'Sequences', () => {
    seqs = crm('GET', '/api/automation/sequences').sequences.filter((s) => s.pipeline_id === C.crm.pipeline_id);
    const want = campaignFor(S.next.date);
    for (const [name, exp] of Object.entries(C.crm.sequences)) {
      const s = seqs.find((x) => x.name === name);
      if (!s) { fail('CRM', name, 'sequence missing'); continue; }
      const issues = [];
      if (exp.status && s.status !== exp.status) issues.push(`status ${s.status}, expected ${exp.status}`);
      if (exp.status === 'active' && s.settings.dry_run && !exp.dry_run) issues.push('test mode is on');
      if (exp.weekly && (s.settings.event?.mode !== 'weekly' || s.settings.event?.time !== W.start_time_local)) issues.push(`event ${JSON.stringify(s.settings.event)}`);
      if (exp.campaign && s.settings.utm_campaign !== want) issues.push(`tracking campaign ${s.settings.utm_campaign}, next session wants ${want} (run roll --apply)`);
      issues.length ? (issues.some((i) => /status|test mode|event/.test(i)) ? fail : warn)('CRM', name, issues.join('; ')) : pass('CRM', name, `${s.status}${s.settings.dry_run ? ', test mode' : ''}, ${s.settings.utm_campaign || 'no campaign'}`);
    }
    for (const s of seqs.filter((x) => x.settings.event?.mode === 'once' && x.status === 'active')) {
      const at = zonedToUtc(s.settings.event.at.slice(0, 10), s.settings.event.at.slice(11, 16), s.settings.timezone);
      at < new Date() ? warn('CRM', s.name, `one-off event ${s.settings.event.at} has passed; pause it or point it at the next session`) : pass('CRM', s.name, `one-off event ${s.settings.event.at}${s.settings.dry_run ? ', test mode' : ''}`);
    }
  });
  await guard('CRM', 'WhatsApp templates used by active sequences', () => {
    const t = crm('GET', '/api/automation/wa-templates').templates;
    const by = Object.fromEntries(t.map((x) => [x.sid, x]));
    const bad = [];
    let n = 0;
    for (const s of seqs.filter((x) => x.status === 'active')) for (const st of s.steps) for (const sid of [st.template?.sid, st.template?.image?.sid].filter(Boolean)) {
      n++; if (by[sid]?.status !== 'approved') bad.push(`${s.name}: ${by[sid]?.name || sid} is ${by[sid]?.status || 'unknown'}`);
    }
    bad.length ? fail('CRM', 'WhatsApp templates used by active sequences', bad.join('; ')) : pass('CRM', 'WhatsApp templates used by active sequences', `${n} template uses, all approved`);
  });
  await guard('CRM', 'Senders', () => {
    const s = crm('GET', '/api/automation/senders');
    const all = Object.values(s).filter(Array.isArray).flat();
    const issues = C.crm.senders.map((id) => [id, all.find((x) => x.id === id)]).filter(([, x]) => !x || x.status !== 'running').map(([id, x]) => `${id} ${x ? x.status : 'missing'}`);
    issues.length ? fail('CRM', 'Senders', issues.join('; ')) : pass('CRM', 'Senders', C.crm.senders.join(', ') + ' running');
  });
  await guard('CRM', 'AI calling', () => {
    const a = crm('GET', '/api/automation/ai-calls/status');
    a.enabled && a.providers?.vapi ? pass('CRM', 'AI calling', 'on, Vapi connected') : fail('CRM', 'AI calling', JSON.stringify(a));
  });
  await guard('Tracking', 'Tracking pipeline health', () => {
    const h = crm('GET', '/api/trk/health');
    const issues = [];
    if (!h.enabled) issues.push('tracking is off');
    if (h.oldest_pending_seconds > 900) issues.push(`events waiting ${Math.round(h.oldest_pending_seconds / 60)} min`);
    if (h.emit_failures_today) issues.push(`${h.emit_failures_today} emit failures today`);
    if (h.deals_unlinked) issues.push(`${h.deals_unlinked} deals without a contact`);
    issues.length ? warn('Tracking', 'Tracking pipeline health', issues.join('; ')) : pass('Tracking', 'Tracking pipeline health', `${h.budget?.events_today ?? 0} events today, nothing stuck`);
  });
  await guard('Tracking', 'Webinar funnel definition', () => {
    const f = crm('GET', '/api/trk/funnels').funnels.find((x) => x.id === C.crm.tracking_funnel_id);
    f && f.status === 'active' ? pass('Tracking', 'Webinar funnel definition', `${f.name} v${f.version}, ${f.entries} entries`) : fail('Tracking', 'Webinar funnel definition', 'missing or not active');
  });
}
async function checkDashboard() {
  await guard('Dashboard', 'dashboard.usetantra.com data', () => {
    const r = d1(C.cloudflare.dashboard_db, 'SELECT generated_at, status FROM snapshots WHERE funnel = ?', [C.dashboard_funnel])[0];
    if (!r) return fail('Dashboard', 'dashboard.usetantra.com data', 'no snapshot');
    const age = (Date.now() - Date.parse(r.generated_at)) / 36e5;
    r.status !== 'ok' ? fail('Dashboard', 'dashboard.usetantra.com data', `last build ${r.status}`) : age > 26 ? warn('Dashboard', 'dashboard.usetantra.com data', `last rebuilt ${age.toFixed(0)} hours ago`) : pass('Dashboard', 'dashboard.usetantra.com data', `rebuilt ${r.generated_at.slice(0, 16)} UTC`);
  });
  await guard('Funnel map', 'Funnel map is current', () => {
    const r = http('GET', C.funnel_map + 'data.js?cycle=' + Date.now(), { raw: true });
    const d = (r.text.match(/STATUS_DATE = '([^']+)'/) || [])[1];
    d ? pass('Funnel map', 'Funnel map is current', `status dated ${d}`) : warn('Funnel map', 'Funnel map is current', `could not read (${r.status})`);
  });
}

// ---------- roll ----------
async function roll() {
  const apply = flag('--apply');
  const want = campaignFor(S.next.date);
  const seqs = crm('GET', '/api/automation/sequences').sequences.filter((s) => s.pipeline_id === C.crm.pipeline_id);
  for (const [name, exp] of Object.entries(C.crm.sequences)) {
    if (!exp.campaign) continue;
    const s = seqs.find((x) => x.name === name);
    if (!s) { fail('Roll', name, 'sequence missing'); continue; }
    if (s.settings.utm_campaign === want) { pass('Roll', name, `already ${want}`); continue; }
    if (!apply) { add('Roll', name, 'info', `would set tracking campaign ${s.settings.utm_campaign} to ${want}`); continue; }
    await guard('Roll', name, () => { crm('PATCH', `/api/automation/sequences/${s.id}`, { settings: { utm_campaign: want } }); pass('Roll', name, `tracking campaign set to ${want}`); });
  }
  add('Roll', 'Pages', 'info', 'the pages pick the next session when built: the workflow runs Deploy funnel after each session');
}

// ---------- e2e: the fast test inside the CRM ----------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// Squeeze an offset in minutes: 3 days becomes 8 minutes, 1 day 4, 1 hour and less 1. Order is kept.
const squeeze = (min) => (min <= 0 ? 0 : Math.min(8, Math.max(1, Math.ceil(min / 360))));
const toMin = (w) => (w ? Number(w.amount || 0) * ({ minutes: 1, hours: 60, days: 1440, weeks: 10080 }[w.unit] || 1) : 0);
function fastStep(st, stageMap) {
  const x = JSON.parse(JSON.stringify(st));
  delete x.id;
  const sch = x.schedule || { type: 'after_previous' };
  x.wait = { amount: sch.type === 'after_previous' ? Math.min(1, toMin(x.wait)) : squeeze(toMin(x.wait)), unit: 'minutes' };
  x.schedule = { ...sch, time_of_day: null, any_time: true, max_late: 60 };
  if (sch.type === 'fixed') x.schedule = { type: 'after_previous', any_time: true, max_late: 60 };
  if (x.target_stage_id && stageMap[x.target_stage_id]) x.target_stage_id = stageMap[x.target_stage_id];
  if (x.redial) x.redial = { ...x.redial, enabled: false };
  return x;
}
async function e2e() {
  const live = flag('--live');
  const T = C.e2e;
  const email = live ? process.env.E2E_EMAIL : null, phone = live ? process.env.E2E_PHONE : null;
  if (live && !email) { fail('E2E', 'Live test contacts', 'set E2E_EMAIL (and E2E_PHONE for WhatsApp, SMS and AI calls)'); return; }
  const event = new Date(Date.now() + T.event_in_minutes * 60000);
  const eventLocal = new Intl.DateTimeFormat('sv-SE', { timeZone: W.timezone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(event).replace(' ', 'T');
  // 1. Test pipeline, same stage names as the real one.
  const prod = crm('GET', '/api/pipelines').pipelines.find((x) => x.id === C.crm.pipeline_id);
  let tp = crm('GET', '/api/pipelines').pipelines.find((x) => x.name === T.pipeline_name);
  if (!tp) { crm('POST', '/api/pipelines', { name: T.pipeline_name, type: 'deal', stages: prod.stages.map((s) => ({ name: s.name, color: s.color, probability: s.probability, kind: s.kind })) }); tp = crm('GET', '/api/pipelines').pipelines.find((x) => x.name === T.pipeline_name); pass('E2E', 'Test pipeline', `created ${tp.id}`); }
  else pass('E2E', 'Test pipeline', tp.id);
  const stageId = (name) => tp.stages.find((s) => s.name === name)?.id;
  const stageMap = Object.fromEntries(prod.stages.map((s) => [s.id, stageId(s.name)]));
  // 2. Copies of every live webinar sequence (and the reschedule ones), refreshed from the real ones on every run.
  const all = crm('GET', '/api/automation/sequences').sequences;
  const src = all.filter((s) => s.pipeline_id === C.crm.pipeline_id && (s.status === 'active' || T.include_drafts.includes(s.name)));
  const tests = [];
  for (const s of src) {
    const name = T.prefix + s.name;
    const settings = { ...s.settings, event: { name: s.settings.event?.name || 'Tantra live session', mode: 'once', at: eventLocal, duration_min: 10 }, dry_run: !live, utm_campaign: 'e2e-test', window: { start: '00:00', end: '23:59' }, days: [0, 1, 2, 3, 4, 5, 6] };
    const steps = s.steps.map((st) => fastStep(st, stageMap));
    const existing = all.find((x) => x.name === name && x.pipeline_id === tp.id);
    const target = stageMap[s.stage_id];
    let t;
    if (existing) { crm('PATCH', `/api/automation/sequences/${existing.id}`, { steps, settings, status: 'active' }); t = existing; }
    else { t = crm('POST', '/api/automation/sequences', { stage_id: target, name, steps, settings }).sequence; crm('PATCH', `/api/automation/sequences/${t.id}`, { status: 'active' }); }
    tests.push({ id: t.id, name: s.name, steps: steps.length, trigger: s.settings.trigger?.type || 'stage', stage: prod.stages.find((x) => x.id === s.stage_id)?.name });
  }
  pass('E2E', 'Test sequences', `${tests.length} copies, event at ${eventLocal} ${W.timezone}, ${live ? 'LIVE to the test contacts' : 'dry run (logs only)'}`);
  // 3. Three test deals, the way the webinar intake creates them.
  const stamp = Date.now().toString(36);
  const mk = (who, extra = {}) => crm('POST', '/api/deals', {
    pipeline_id: tp.id, stage_id: stageId('Registered'), title: `E2E ${who} ${stamp}`, contact_name: `E2E ${who}`,
    contact_email: email ? email.replace('@', `+e2e-${who}-${stamp}@`) : `e2e-${who}-${stamp}@example.com`, ...(phone ? { contact_phone: phone } : {}),
    tags: ['ew-registered', 'e2e-test'], custom: { ew_registered_at: new Date().toISOString(), ew_join_url: T.sample_join_url, ew_replay_url: T.sample_replay_url, ew_report_url: T.sample_report_url, ew_bonus_url: T.sample_bonus_url, timezone: W.timezone, ...extra },
  }).deal;
  const deals = { attended: mk('attended'), missed: mk('missed'), rescheduled: mk('rescheduled') };
  pass('E2E', 'Test deals', Object.entries(deals).map(([k, d]) => `${k} ${d.id}`).join(', '));
  const patch = (d, b) => crm('PATCH', `/api/deals/${d.id}`, b);
  await sleep(60000);
  patch(deals.attended, { tags: ['ew-registered', 'e2e-test', 'ew-survey-done'] });
  patch(deals.rescheduled, { stage_id: stageId('Webinar Reschedule'), tags: ['ew-registered', 'e2e-test', 'ew-rescheduled'] });
  // After the squeezed session: attended and missed, as the WebinarJam webhook would move them.
  await sleep(Math.max(0, event.getTime() + 60000 - Date.now()));
  patch(deals.attended, { stage_id: stageId('Attended'), tags: ['ew-registered', 'e2e-test', 'ew-survey-done', 'ew-attended'] });
  patch(deals.missed, { stage_id: stageId('Missed'), tags: ['ew-registered', 'e2e-test', 'ew-missed'] });
  // 4. Wait until every enrollment has finished, or the time is up.
  const ids = new Set(Object.values(deals).map((d) => d.id));
  const until = Date.now() + T.max_wait_minutes * 60000;
  let acts = [];
  while (Date.now() < until) {
    acts = tests.map((t) => ({ t, a: crm('GET', `/api/automation/sequences/${t.id}/enrollments`) }));
    const open = acts.flatMap(({ a }) => a.enrollments.filter((e) => ids.has(e.deal_id) && e.status === 'active'));
    if (!open.length) break;
    await sleep(30000);
  }
  // 5. Every step must have run (sent, or logged in a dry run); skips are fine only for the expected reasons.
  for (const { t, a } of acts) {
    const en = a.enrollments.filter((e) => ids.has(e.deal_id));
    const runs = a.runs.filter((r) => ids.has(r.deal_id));
    if (!en.length) { (t.trigger === 'stage' && t.stage === 'Registered' ? fail : warn)('E2E', t.name, 'no test deal entered it'); continue; }
    const bad = runs.filter((r) => r.status === 'failed' || (r.status === 'skipped' && !T.ok_skip.some((re) => new RegExp(re, 'i').test(r.detail))));
    const done = runs.filter((r) => ['sent', 'dry_run'].includes(r.status)).length;
    const stuck = en.filter((e) => e.status === 'active');
    if (bad.length) fail('E2E', t.name, bad.map((r) => `${r.channel} ${r.status}: ${r.detail.slice(0, 120)}`).join('; '));
    else if (stuck.length) warn('E2E', t.name, `${done} steps ran, still waiting on ${stuck.length} (step ${stuck[0].step_id})`);
    else pass('E2E', t.name, `${done} steps ran for ${en.length} test deal(s)`);
  }
  // 6. Tracking: the stage changes reached the event store.
  await guard('E2E', 'Tracking events for the test deals', () => {
    const got = Object.values(deals).map((d) => crm('GET', `/api/trk/events?deal_id=${d.id}&limit=50`).events || []);
    const n = got.flat().length;
    const stages = got.flat().filter((e) => e.event_name === 'stage_changed').length;
    stages ? pass('E2E', 'Tracking events for the test deals', `${n} events, ${stages} stage changes`) : warn('E2E', 'Tracking events for the test deals', `${n} events, no stage change yet (the tracker drains every minute)`);
  });
  if (!flag('--keep')) { for (const d of Object.values(deals)) crm('DELETE', `/api/deals/${d.id}`); pass('E2E', 'Clean up', 'test deals deleted (the test sequences stay for next time)'); }
}

// ---------- main ----------
const main = async () => {
  if (cmd === 'plan') {
    console.log(`cadence every ${S.every} days, ${W.start_time_local} ${W.timezone}`);
    console.log(`last session: ${S.last ? longDate(S.last.date) : 'none yet'}`);
    console.log(`next session: ${longDate(S.next.date)} (${S.next.start.toISOString()})`);
    console.log(`after that:   ${S.after.map((s) => s.date).join(', ')}`);
    console.log(`CRM tracking campaign for the next session: ${campaignFor(S.next.date)}`);
    return 0;
  }
  if (cmd === 'check') { await checkPages(); await checkWebinarJam(); await checkCrm(); await checkDashboard(); return report('Weekly check'); }
  if (cmd === 'roll') { await roll(); return report(flag('--apply') ? 'Roll to the next session' : 'Roll (preview)'); }
  if (cmd === 'e2e') { await guard('E2E', 'Fast end-to-end test', e2e); return report(flag('--live') ? 'Fast end-to-end test (live)' : 'Fast end-to-end test (dry run)'); }
  console.error('commands: plan | check | roll [--apply] | e2e [--live] [--keep]');
  return 2;
};
process.exitCode = await main();
