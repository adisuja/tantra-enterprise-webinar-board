// Tantra WhatsApp scheduler (board card 36). Posts the webinar reminders into the Tantra Community on WhatsApp:
// the Announcements group (only admins post, every member sees it) and THE COMMUNITY (the discussion group).
//
// Free and self-built: Baileys (MIT, github.com/WhiskeySockets/Baileys) speaks the WhatsApp Web protocol as a linked
// device of an admin number, like WhatsApp Web in a browser. This is NOT the official WhatsApp Business Platform
// (the official Groups API needs an Official Business Account, caps groups at 8 people and has no Communities), so
// WhatsApp's terms do not cover it: link a spare admin number, never a personal one, and keep volume low.
//
// Commands
//   node wa.mjs link [--phone 447700900000]  Link the admin number (QR in the terminal and at STATE/qr.png, or an
//                                             8-character pairing code with --phone). Once only.
//   node wa.mjs groups                        Find the Tantra Community, its Announcements group and THE COMMUNITY;
//                                             save their ids and invite links to STATE/targets.json.
//   node wa.mjs plan [--weeks 4]              Build schedule.json for the next webinars from funnel-config.json and
//                                             the approved 15b WhatsApp copy (deliverables/15b-pre-nurture/whatsapp.csv).
//   node wa.mjs send-due [--dry-run]          Send every post whose time has come (launchd runs this every minute).
//                                             Connects only when something is due; never sends a post twice; skips
//                                             posts more than 20 minutes late.
//   node wa.mjs post <announcements|community> "text"   Send one message now.
//
// State (session keys, targets, sent log) lives outside the repo in ~/.config/tantra/whatsapp and is never committed.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import makeWASocket, { useMultiFileAuthState, DisconnectReason, Browsers, fetchLatestBaileysVersion } from 'baileys';
import QRCode from 'qrcode';
import pino from 'pino';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const STATE = process.env.TANTRA_WA_STATE || path.join(os.homedir(), '.config', 'tantra', 'whatsapp');
const AUTH = path.join(STATE, 'auth');
const TARGETS = path.join(STATE, 'targets.json');
const SENT = path.join(STATE, 'sent.json');
const SCHEDULE = path.join(HERE, 'schedule.json');
const COMMUNITY_NAME = process.env.TANTRA_WA_COMMUNITY || 'Tantra Community';
const DISCUSSION_NAME = process.env.TANTRA_WA_DISCUSSION || 'THE COMMUNITY';
const LATE_LIMIT_MIN = 20;

const args = process.argv.slice(2);
const cmd = args[0];
const flag = (n) => { const i = args.indexOf(`--${n}`); return i >= 0 ? (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true) : null; };
const readJson = (p, d) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return d; } };
const writeJson = (p, v) => { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, JSON.stringify(v, null, 1) + '\n', { mode: 0o600 }); };
const log = (...a) => console.log(new Date().toISOString(), ...a);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- Connection: resolves with an open socket; handles the restart WhatsApp asks for right after linking ----------
async function connect({ linking = false, phone = null } = {}) {
  fs.mkdirSync(AUTH, { recursive: true, mode: 0o700 });
  const { state, saveCreds } = await useMultiFileAuthState(AUTH);
  if (!linking && !state.creds.me) throw new Error(`Not linked yet. Run: node wa.mjs link`);
  const { version } = await fetchLatestBaileysVersion();
  return new Promise((resolve, reject) => {
    let pairingAsked = false;
    const open = () => {
      const sock = makeWASocket({ version, auth: state, browser: Browsers.macOS('Chrome'), logger: pino({ level: 'silent' }), markOnlineOnConnect: false, syncFullHistory: false });
      sock.ev.on('creds.update', saveCreds);
      sock.ev.on('connection.update', async (u) => {
        if (u.qr && linking && !phone) {
          await QRCode.toFile(path.join(STATE, 'qr.png'), u.qr, { width: 420 });
          // A page that reloads itself, so the QR on screen is always the current one (they rotate every ~20 s).
          fs.writeFileSync(path.join(STATE, 'qr.html'), `<!doctype html><meta http-equiv="refresh" content="3"><title>Link the Tantra scheduler</title><body style="font:16px system-ui;text-align:center;padding:40px"><p>On the scheduler phone: WhatsApp, Settings, Linked devices, Link a device, then scan.</p><img src="qr.png?${Date.now()}" width="420" height="420" alt="WhatsApp link QR code">`);
          console.log(await QRCode.toString(u.qr, { type: 'terminal', small: true }));
          log(`Scan with the admin phone: WhatsApp, Settings, Linked devices, Link a device. Also saved: ${path.join(STATE, 'qr.png')}`);
        }
        if (u.qr && linking && phone && !pairingAsked) {
          pairingAsked = true;
          const code = await sock.requestPairingCode(String(phone).replace(/\D/g, ''));
          log(`Pairing code: ${code}. On the admin phone: WhatsApp, Settings, Linked devices, Link a device, Link with phone number instead.`);
        }
        if (u.connection === 'open') resolve(sock);
        if (u.connection === 'close') {
          const code = u.lastDisconnect?.error?.output?.statusCode;
          if (code === DisconnectReason.restartRequired) return open(); // normal once, right after linking
          if (code === DisconnectReason.loggedOut) return reject(new Error('Logged out: the device was unlinked on the phone. Run: node wa.mjs link'));
          if (linking && code === DisconnectReason.timedOut) return reject(new Error('QR expired. Run link again.'));
          reject(new Error(`Connection closed (${code ?? 'unknown'})`));
        }
      });
    };
    open();
  });
}
const done = async (sock) => { await sleep(4000); try { sock.end(undefined); } catch {} };

// ---------- groups: find the community, its Announcements group and the discussion group ----------
async function groups() {
  const sock = await connect();
  const all = Object.values(await sock.groupFetchAllParticipating());
  const community = all.find((g) => g.isCommunity && g.subject === COMMUNITY_NAME);
  if (!community) { await done(sock); throw new Error(`No community called "${COMMUNITY_NAME}" on this number. Is it an admin?`); }
  const linked = all.filter((g) => g.linkedParent === community.id);
  const announce = linked.find((g) => g.isCommunityAnnounce) || all.find((g) => g.isCommunityAnnounce && g.linkedParent === community.id);
  const discussion = linked.find((g) => !g.isCommunityAnnounce && g.subject === DISCUSSION_NAME);
  const invite = async (jid) => { try { return `https://chat.whatsapp.com/${await sock.groupInviteCode(jid)}`; } catch { return null; } };
  const t = {
    community: { id: community.id, name: community.subject, invite: await invite(community.id) },
    announcements: announce ? { id: announce.id, name: announce.subject } : null,
    community_chat: discussion ? { id: discussion.id, name: discussion.subject, invite: await invite(discussion.id) } : null,
    found_at: new Date().toISOString(),
  };
  writeJson(TARGETS, t);
  console.log(JSON.stringify(t, null, 1));
  if (!t.announcements) log('Warning: no Announcements group found under the community.');
  await done(sock);
}

// ---------- plan: the next webinars' posts, from funnel-config and the approved 15b copy ----------
function zonedToUtc(dateStr, timeStr, tz) {
  // The UTC instant of a wall-clock time in a time zone (no library): guess, then correct by the zone's offset.
  const [y, m, d] = dateStr.split('-').map(Number); const [hh, mm] = timeStr.split(':').map(Number);
  let t = Date.UTC(y, m - 1, d, hh, mm);
  for (let i = 0; i < 2; i++) {
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).formatToParts(new Date(t)).map((x) => [x.type, x.value]));
    const shown = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute);
    t += Date.UTC(y, m - 1, d, hh, mm) - shown;
  }
  return new Date(t);
}
function csv(text) {
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { f += '"'; i++; } else if (c === '"') q = false; else f += c; }
    else if (c === '"') q = true; else if (c === ',') { row.push(f); f = ''; } else if (c === '\n') { row.push(f); rows.push(row); row = []; f = ''; } else if (c !== '\r') f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const [h, ...rest] = rows; return rest.filter((r) => r.length > 1).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i] ?? ''])));
}
// The 15b 1-to-1 copy becomes a group post: no first name, no reply keywords, nothing else changed.
// Room links are personal (one WebinarJam link per seat), so a group post never carries one: the link line becomes a
// pointer to the person's own link, sent to them 1-to-1 (Adi 2026-11-08).
const POINTER = 'Your personal join link is in your WebinarJam email and in my WhatsApp message to you.';
function groupCopy(body) {
  let s = body.replace(/^Hi \{\{1\}\}, it's Adi\.\s*/, '').replace(/^Hi \{\{1\}\},\s*/, '');
  s = s.replace(/^(Your join link|Join here|Join now): \{\{\d\}\}$/m, POINTER);
  s = s.split('\n').filter((l) => !/^Reply\b|Reply STOP|Already in\? Ignore this/.test(l.trim())).join('\n').replace(/\n{3,}/g, '\n\n').trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}
function plan() {
  const cfg = readJson(path.join(ROOT, 'deliverables', '_shared', 'funnel-config.json'), null);
  if (!cfg) throw new Error('funnel-config.json not found');
  const w = cfg.webinar; const weeks = Number(flag('weeks') || 4);
  const known = (v) => typeof v === 'string' && v && !v.startsWith('FILL_');
  const join = known(w.join_url) ? w.join_url : null;
  const approved = !!flag('approved'); // Adi's ok of the group wording (card 36)
  const rows = csv(fs.readFileSync(path.join(ROOT, 'deliverables', '15b-pre-nurture', 'whatsapp.csv'), 'utf8'));
  const STEPS = ['15B-D1', '15B-H1', '15B-M15', '15B-L0']; // tomorrow, 1 hour, 15 minutes, live now
  const posts = [];
  const first = new Date(`${w.first_date}T00:00:00Z`);
  const today = new Date(); today.setUTCHours(0, 0, 0, 0);
  for (let k = 0, n = 0; n < weeks && k < 60; k++) {
    const d = new Date(first.getTime() + k * 7 * 864e5);
    if (w.cadence !== 'weekly' && k > 0) break;
    if (d < today) continue;
    n++;
    const date = d.toISOString().slice(0, 10);
    const start = zonedToUtc(date, w.start_time_local, w.timezone);
    const dateLocal = new Intl.DateTimeFormat('en-GB', { timeZone: w.timezone, weekday: 'long', day: 'numeric', month: 'long' }).format(start);
    const timeLocal = `${w.start_time_local} UK time`;
    for (const id of STEPS) {
      const r = rows.find((x) => x.step_id === id); if (!r) continue;
      // Variables by name, from the csv's own "{{n}}=name" list.
      const vars = Object.fromEntries(r.variables.split(';').map((p) => p.trim().split('=')).filter((p) => p.length === 2));
      const val = { webinar_date_local: dateLocal, webinar_time_local: timeLocal, join_url: join };
      let text = groupCopy(r.body); let missing = [];
      text = text.replace(/\{\{(\d)\}\}/g, (m, i) => { const name = vars[`{{${i}}}`]; const v = val[name]; if (!v) missing.push(name); return v || `[${name}]`; });
      posts.push({ id: `${date}:${id}`, at: new Date(start.getTime() + Number(r.offset_minutes) * 60000).toISOString(), target: 'announcements', text, ...(missing.length ? { hold: `waiting on ${missing.join(', ')}` } : approved ? {} : { hold: 'waiting on Adi\'s ok of the wording' }) });
    }
  }
  writeJson(SCHEDULE, { built_at: new Date().toISOString(), source: 'funnel-config.json + 15b-pre-nurture/whatsapp.csv', posts });
  for (const p of posts) log(p.id, p.at, p.target, p.hold ? `HOLD (${p.hold})` : 'ready');
  log(`${posts.length} posts written to ${SCHEDULE}`);
}

// ---------- send-due: launchd calls this every minute ----------
async function sendDue() {
  const dry = !!flag('dry-run');
  const { posts = [] } = readJson(SCHEDULE, {});
  const sent = readJson(SENT, {});
  const now = Date.now();
  const due = posts.filter((p) => !sent[p.id] && !p.hold && new Date(p.at).getTime() <= now);
  const late = due.filter((p) => now - new Date(p.at).getTime() > LATE_LIMIT_MIN * 60000);
  for (const p of late) { sent[p.id] = { skipped: 'too late', at: new Date().toISOString() }; log('skip (late)', p.id); }
  const go = due.filter((p) => !late.includes(p));
  if (!go.length) { if (late.length) writeJson(SENT, sent); return; }
  if (dry) { for (const p of go) log('DRY', p.id, p.target, JSON.stringify(p.text)); return; }
  const t = readJson(TARGETS, null); if (!t) throw new Error('No targets yet. Run: node wa.mjs groups');
  const sock = await connect();
  for (const p of go) {
    const jid = p.target === 'community' ? t.community_chat?.id : t.announcements?.id;
    if (!jid) { log('no target for', p.id, p.target); continue; }
    await sock.sendMessage(jid, { text: p.text });
    sent[p.id] = { sent: new Date().toISOString(), jid };
    writeJson(SENT, sent);
    log('sent', p.id, p.target);
    await sleep(3000 + Math.random() * 4000); // never back to back
  }
  await done(sock);
}

async function postNow() {
  const target = args[1]; const text = args.slice(2).join(' ');
  if (!['announcements', 'community'].includes(target) || !text) throw new Error('Usage: node wa.mjs post <announcements|community> "text"');
  const t = readJson(TARGETS, null); if (!t) throw new Error('No targets yet. Run: node wa.mjs groups');
  const jid = target === 'community' ? t.community_chat?.id : t.announcements?.id;
  const sock = await connect();
  await sock.sendMessage(jid, { text });
  log('sent to', target);
  await done(sock);
}

// Pairing codes and QR codes expire after about 2 minutes; keep issuing fresh ones for up to 10 minutes.
async function link() {
  const until = Date.now() + 10 * 60000;
  for (;;) {
    try { const s = await connect({ linking: true, phone: flag('phone') }); log('Linked.'); await done(s); return; }
    catch (e) { if (!/expired/i.test(e.message) || Date.now() > until) throw e; log('Code expired, issuing a new one.'); }
  }
}
// join: the linked number joins the community (and so its Announcements group) through the public invite link.
async function join() {
  const cfg = readJson(path.join(ROOT, 'deliverables', '_shared', 'funnel-config.json'), {});
  const code = (cfg.community?.whatsapp_announcement_url || '').split('/').pop();
  if (!code || code.startsWith('FILL')) throw new Error('No community invite link in funnel-config (community.whatsapp_announcement_url)');
  const sock = await connect();
  const info = await sock.communityGetInviteInfo(code).catch(() => null);
  log('Invite is for:', info?.subject || '(unknown)');
  const res = await sock.communityAcceptInvite(code);
  log('Joined:', res || 'ok');
  await done(sock);
}
const run = { link, join, groups, plan: async () => plan(), 'send-due': sendDue, post: postNow }[cmd];
if (!run) { console.log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').filter((l) => l.startsWith('//')).slice(0, 22).map((l) => l.slice(3)).join('\n')); process.exit(cmd ? 1 : 0); }
run().then(() => process.exit(0)).catch((e) => { log('ERROR', e.message); process.exit(1); });
