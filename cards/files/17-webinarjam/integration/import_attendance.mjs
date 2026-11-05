// WebinarJam registrants export (CSV) -> CRM webinar.attended / webinar.no_show events (CRM_CONTRACT.md).
//
//   node import_attendance.mjs --csv export.csv --date 2026-11-12 [--start 10:00] [--tz Europe/London]
//                              [--columns columns.json] [--out events.json] [--live]
//
// Dry run unless --live: prints a summary and writes the events to --out (default: stdout).
// --live POSTs each event to integrations.crm_webhook_url?k=$CRM_SHARED_SECRET.
// --start and --tz default to webinar.start_time_local and webinar.timezone in funnel-config.json;
// they are only needed when the entry column is an offset from the start.
// Use the export with EVERY registrant (Registrants, Export, "Export all registrants"): rows that did not
// attend become webinar.no_show. The "attendees only" export has no no-shows.

import config from '../../_shared/funnel-config.json' with { type: 'json' };
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { isFill, isEmail, isoZ, norm, parseCsv, parseMinutes, parseSeconds, parseClock, zonedToUtc, truthy, findColumn, sleep } from './lib.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));

// rows: array of arrays with a header row. opts: { date, start, tz, columns, nowMs }
export function toEvents(rows, opts) {
  const { date, start, tz, columns } = opts;
  const head = rows[0] || [];
  const col = {};
  for (const k of ['email', 'attended', 'minutes', 'entered', 'left', 'live_date']) col[k] = findColumn(head, columns[k] || []);
  if (col.email < 0) throw new Error(`No email column. Headers: ${head.join(', ')}`);
  const startMs = start && tz ? zonedToUtc(`${date} ${start}`, tz) : null;
  const mode = columns.entered_is || 'auto';
  const ts = isoZ(opts.nowMs ?? Date.now());
  const cutoff = Number(config.webinar.retarget_cutoff_minute) || 25;
  const out = { events: [], attended: 0, stayed: 0, early: 0, no_show: 0, skipped: 0, notes: [], columns: {} };
  for (const [k, i] of Object.entries(col)) out.columns[k] = i >= 0 ? head[i] : '(none)';

  const seen = new Set();
  for (const r of rows.slice(1)) {
    const email = norm(r[col.email]).replace(/ /g, '');
    if (!isEmail(email) || seen.has(email)) { out.skipped++; continue; }
    seen.add(email);
    let mins = col.minutes >= 0 ? parseMinutes(r[col.minutes], columns.minutes_is) : 0;
    const flag = col.attended >= 0 ? truthy(r[col.attended]) : mins > 0;
    if (!flag) {
      out.events.push({ event: 'webinar.no_show', email, ts, source: 'webinarjam_export', webinar_date: date, data: {} });
      out.no_show++;
      continue;
    }
    if (mins === 0) mins = 1; // marked attended with no time: count as present, as the CRM importer does
    let joined = null;
    const raw = col.entered >= 0 ? String(r[col.entered] || '').trim() : '';
    const day = col.live_date >= 0 && /^\d{4}-\d{2}-\d{2}/.test(String(r[col.live_date])) ? String(r[col.live_date]).slice(0, 10) : date;
    if (raw) {
      const looksClock = /\d{4}-\d{2}-\d{2}|[ap]\.?m\.?$/i.test(raw);
      if (mode === 'clock' || (mode === 'auto' && looksClock)) joined = tz ? parseClock(raw, day, tz) : null;
      else { const sec = parseSeconds(raw, columns.minutes_is); if (sec !== null && startMs !== null) joined = startMs + sec * 1000; }
    }
    let left = null;
    if (col.left >= 0 && String(r[col.left] || '').trim() && tz) left = parseClock(r[col.left], day, tz);
    if (left === null && joined !== null) left = joined + mins * 60000;
    out.events.push({ event: 'webinar.attended', email, ts, source: 'webinarjam_export', webinar_date: date,
      data: { minutes_in_room: mins, joined_at: joined === null ? '' : isoZ(joined), left_at: left === null ? '' : isoZ(left) } });
    out.attended++;
    if (mins >= cutoff) out.stayed++; else out.early++;
  }
  if (out.attended && out.events.every((e) => e.event !== 'webinar.attended' || !e.data.joined_at)) out.notes.push('joined_at is blank: pass --start and --tz, or set entered_is in columns.json');
  return out;
}

async function cli(argv) {
  const arg = (k) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : undefined; };
  const csv = arg('--csv'), date = arg('--date');
  if (!csv || !/^\d{4}-\d{2}-\d{2}$/.test(date || '')) { console.log('usage: node import_attendance.mjs --csv export.csv --date YYYY-MM-DD [--start HH:MM] [--tz Area/City] [--columns file] [--out file] [--live]'); process.exit(2); }
  const w = config.webinar;
  const start = arg('--start') || (/^\d{1,2}:\d{2}$/.test(w.start_time_local) ? w.start_time_local : undefined);
  const tz = arg('--tz') || (isFill(w.timezone) ? undefined : w.timezone);
  const columns = JSON.parse(readFileSync(arg('--columns') || path.join(here, 'columns.json'), 'utf8'));
  const res = toEvents(parseCsv(readFileSync(csv, 'utf8')), { date, start, tz, columns });

  console.error(`columns used: ${JSON.stringify(res.columns)}`);
  console.error(`${date}: ${res.attended} attended (${res.stayed} stayed to minute ${w.retarget_cutoff_minute}, ${res.early} left earlier), ${res.no_show} no-shows, ${res.skipped} rows skipped`);
  res.notes.forEach((n) => console.error(`note: ${n}`));

  if (!argv.includes('--live')) {
    const json = JSON.stringify(res.events, null, 2);
    if (arg('--out')) { writeFileSync(arg('--out'), json); console.error(`[dry-run] ${res.events.length} events written to ${arg('--out')}; nothing sent. Add --live to post them.`); }
    else console.log(json);
    return;
  }
  const url = config.integrations.crm_webhook_url, secret = process.env.CRM_SHARED_SECRET;
  if (isFill(url) || !secret) throw new Error('crm_webhook_url (funnel-config) or CRM_SHARED_SECRET (env) is missing');
  let sent = 0, failed = 0;
  for (const ev of res.events) {
    const r = await fetch(`${url}?k=${encodeURIComponent(secret)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ev), redirect: 'follow' });
    const j = await r.json().catch(() => ({}));
    if (j.ok) sent++; else { failed++; console.error(`failed (${r.status}): ${j.error || 'no ok'}`); }
    await sleep(200);
  }
  console.error(`[live] ${sent} sent, ${failed} failed. Re-running updates the same Webinar tab rows (the Events log gets a second copy).`);
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  cli(process.argv.slice(2)).catch((e) => { console.error(e.message); process.exit(1); });
}
