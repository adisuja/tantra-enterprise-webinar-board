// Shared helpers for register.mjs and import_attendance.mjs. No dependencies, Node 18+ or a Cloudflare Worker.

export const isFill = (v) => v === undefined || v === null || v === '' || (typeof v === 'string' && /^(FILL_|STUB)/.test(v));
export const isEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(s || ''));
export const norm = (s) => String(s ?? '').trim().toLowerCase().replace(/[_\s]+/g, ' ');
export const isoZ = (ms) => new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z');

// Wall-clock parts of an instant in an IANA zone.
function partsIn(ms, tz) {
  const f = new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const p = Object.fromEntries(f.formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return { y: +p.year, mo: +p.month, d: +p.day, h: +p.hour % 24, mi: +p.minute, s: +p.second };
}

// "2026-11-12 11:00[:ss]" read as wall time in tz, returned as epoch ms (UTC).
export function zonedToUtc(local, tz) {
  const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?/.exec(String(local).trim());
  if (!m) throw new Error(`not a local date-time: ${local}`);
  const want = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0));
  let guess = want;
  for (let i = 0; i < 2; i++) {
    const p = partsIn(guess, tz);
    const seen = Date.UTC(p.y, p.mo - 1, p.d, p.h, p.mi, p.s);
    guess += want - seen;
  }
  return guess;
}

export const localDate = (ms, tz) => { const p = partsIn(ms, tz); return `${p.y}-${String(p.mo).padStart(2, '0')}-${String(p.d).padStart(2, '0')}`; };

// RFC 4180 CSV: quoted fields, doubled quotes, commas and newlines inside quotes, optional BOM.
export function parseCsv(text) {
  const rows = []; let row = []; let f = ''; let q = false;
  const s = String(text).replace(/^\uFEFF/, '');
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"' && s[i + 1] === '"') { f += '"'; i++; }
      else if (c === '"') q = false;
      else f += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && s[i + 1] === '\n') i++;
      row.push(f); f = ''; if (row.some((x) => x !== '')) rows.push(row); row = [];
    } else f += c;
  }
  row.push(f); if (row.some((x) => x !== '')) rows.push(row);
  return rows;
}

// Time in room to whole minutes. Three parts "01:05:30" are always hours:minutes:seconds. A two-part value
// like "05:30" is either hours:minutes or minutes:seconds, so it is refused until minutes_is says which
// (columns.json: "hms" = hours:minutes, "ms" = minutes:seconds, "minutes" = plain numbers only).
// Seconds of 30 or more round up, as in the CRM's own importer. Also "65", "1h 5m" or a number.
export function parseMinutes(v, mode) {
  if (v === null || v === undefined || v === '') return 0;
  if (typeof v === 'number') return Math.round(v);
  const s = String(v).trim().toLowerCase();
  const three = /^(\d+):(\d{1,2}):(\d{1,2})$/.exec(s);
  if (three) return +three[1] * 60 + +three[2] + (+three[3] >= 30 ? 1 : 0);
  const two = /^(\d+):(\d{1,2})$/.exec(s);
  if (two) {
    if (mode === 'hms') return +two[1] * 60 + +two[2];
    if (mode === 'ms') return +two[1] + (+two[2] >= 30 ? 1 : 0);
    throw new Error(`"${s}" has two parts and could be hours:minutes or minutes:seconds. Set "minutes_is" in columns.json to "hms" or "ms".`);
  }
  const h = /(\d+)\s*h/.exec(s), m = /(\d+)\s*m/.exec(s);
  if (h || m) return (h ? +h[1] * 60 : 0) + (m ? +m[1] : 0);
  const n = Number(s);
  return Number.isNaN(n) ? 0 : Math.round(n);
}

// Offset from the start to seconds: "00:03:20", "3m 20s", "200" (seconds), and two-part values by the same
// minutes_is rule ("hms": hours:minutes, "ms": minutes:seconds; refused while unset).
export function parseSeconds(v, mode) {
  const s = String(v ?? '').trim().toLowerCase();
  if (!s) return null;
  const hms = /^(\d+):(\d{1,2}):(\d{1,2})$/.exec(s);
  if (hms) return +hms[1] * 3600 + +hms[2] * 60 + +hms[3];
  const two = /^(\d+):(\d{1,2})$/.exec(s);
  if (two) {
    if (mode === 'hms') return +two[1] * 3600 + +two[2] * 60;
    if (mode === 'ms') return +two[1] * 60 + +two[2];
    throw new Error(`"${s}" has two parts and could be hours:minutes or minutes:seconds. Set "minutes_is" in columns.json to "hms" or "ms".`);
  }
  const h = /(\d+)\s*h/.exec(s), m = /(\d+)\s*m(?!s)/.exec(s), sec = /(\d+)\s*s/.exec(s);
  if (h || m || sec) return (h ? +h[1] * 3600 : 0) + (m ? +m[1] * 60 : 0) + (sec ? +sec[1] : 0);
  return /^\d+$/.test(s) ? +s : null;
}

// A clock value, with or without a date, to epoch ms in tz. date fills in when the value has none.
export function parseClock(v, date, tz) {
  const s = String(v ?? '').trim();
  if (!s) return null;
  const full = /^(\d{4}-\d{2}-\d{2})[ T](\d{1,2}:\d{2}(?::\d{2})?)/.exec(s);
  if (full) return zonedToUtc(`${full[1]} ${full[2]}`, tz);
  const ampm = /^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([ap])\.?m\.?$/i.exec(s);
  if (ampm) {
    let h = +ampm[1] % 12; if (ampm[4].toLowerCase() === 'p') h += 12;
    return zonedToUtc(`${date} ${h}:${ampm[2]}:${ampm[3] || '00'}`, tz);
  }
  const c = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(s);
  if (c) return zonedToUtc(`${date} ${c[1]}:${c[2]}:${c[3] || '00'}`, tz);
  return null;
}

export const truthy = (v) => ['yes', 'y', 'true', '1', 'attended', 'x'].includes(norm(v));

// First column whose header equals an alias, else the first that contains one. -1 if none.
export function findColumn(headers, aliases) {
  const names = headers.map(norm);
  for (const a of aliases) { const i = names.indexOf(norm(a)); if (i >= 0) return i; }
  for (const a of aliases) { const i = names.findIndex((n) => n.includes(norm(a))); if (i >= 0) return i; }
  return -1;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
