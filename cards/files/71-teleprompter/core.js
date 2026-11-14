// Tantra Teleprompter core. The same logic runs in two places:
//   server.js      Node on a Mac (Wi-Fi), or any server
//   worker/        a Cloudflare Worker with one Durable Object (teleprompter.usetantra.com)
//
// How it works: someone adds a script and taps Generate code. That makes a session: a code, a live
// state, and the scripts added under that code (they can add more and switch between them).
// Every phone that opens the same code joins the same session. A new code starts empty: nothing
// carries over between codes, and there are no accounts. A session nobody has opened for
// SESSION_TTL_DAYS is deleted.
'use strict';

const { parseImport } = require('./public/importers.js');

const SESSION_TTL_DAYS = 7;
const MAX_SCRIPT_CHARS = 500 * 1024;
const MAX_SCRIPTS = 50;
const CODE_LENGTH = 6;
const CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // no 0, O, 1, I, L

const DEFAULT_STATE = {
  scriptId: null,
  playing: false,
  speed: 5,            // 1 to 30
  dir: 1,              // 1 forward, -1 backward
  fontSize: 64,        // px on the prompter
  lineHeight: 1.35,
  margin: 6,           // percent padding on each side
  marker: 33,          // reading line, percent from top
  mirrorX: true,
  mirrorY: true,          // mirrored and flipped by default: that is how it reads off teleprompter glass
  align: 'left',
  anchor: { para: 0, frac: 0 }, // where the reading line is, device independent
  seq: 0,
};

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const num = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
const cleanCode = (c) => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);

function randomCode() {
  const bytes = new Uint8Array(CODE_LENGTH);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => CODE_ALPHABET[b % CODE_ALPHABET.length]).join('');
}

function randomId() {
  const abc = 'abcdefghijkmnpqrstuvwxyz23456789';
  const bytes = new Uint8Array(8);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => abc[b % abc.length]).join('');
}

function json(code, body) {
  return new Response(JSON.stringify(body), { status: code, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
}

// store: { sessions: { CODE: { state, scripts: { id: {id, title, text, updatedAt} }, created, lastActive } }, save(code) }
// opts:  { lan: () => [ip], port, setInterval, now }
function createCore(store, opts) {
  opts = opts || {};
  const now = opts.now || (() => Date.now());
  const encoder = new TextEncoder();
  const live = new Map(); // code -> Set of connected clients

  function prune() {
    const cutoff = now() - SESSION_TTL_DAYS * 86400000;
    for (const [code, s] of Object.entries(store.sessions)) {
      if ((s.lastActive || 0) < cutoff && !(live.get(code) || new Set()).size) { delete store.sessions[code]; store.save(code); }
    }
  }
  prune();
  (opts.setInterval || setInterval)(prune, 3600000);

  function touch(code) {
    const s = store.sessions[code];
    if (!s) return;
    if (now() - (s.lastActive || 0) > 60000) { s.lastActive = now(); store.save(code); }
  }

  function clients(code) {
    if (!live.has(code)) live.set(code, new Set());
    return live.get(code);
  }
  function write(set, client, text) {
    try { client.controller.enqueue(encoder.encode(text)); return true; }
    catch { set.delete(client); return false; }
  }
  function send(set, client, event, data) { return write(set, client, `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`); }
  function presence(code) {
    const p = { prompter: 0, remote: 0, other: 0 };
    for (const c of clients(code)) p[c.role in p ? c.role : 'other']++;
    return p;
  }
  function broadcast(code, event, data, except) {
    const set = clients(code);
    for (const c of [...set]) if (c !== except) send(set, c, event, data);
  }
  (opts.setInterval || setInterval)(() => {
    for (const set of live.values()) for (const c of [...set]) write(set, c, `event: ping\ndata: ${Date.now()}\n\n`);
  }, 10000);

  function cleanScript(b) {
    const text = String(b.text || '');
    if (!text.trim()) return { error: 'Add your script first.' };
    if (text.length > MAX_SCRIPT_CHARS) return { error: 'That script is too long (500 KB at most).' };
    return { title: String(b.title || '').trim().slice(0, 200) || 'Untitled script', text, updatedAt: now() };
  }
  const listScripts = (s) => Object.values(s.scripts)
    .map(({ id, title, updatedAt, text }) => ({ id, title, updatedAt, words: (text.match(/\S+/g) || []).length }))
    .sort((a, b) => b.updatedAt - a.updatedAt);

  function applyCommand(s, cmd) {
    const st = s.state;
    switch (cmd.type) {
      case 'play': st.playing = true; break;
      case 'pause': st.playing = false; break;
      case 'toggle': st.playing = !st.playing; break;
      case 'speed': st.speed = clamp(num(cmd.value, st.speed), 1, 30); break;
      case 'speedBy': st.speed = clamp(Math.round((st.speed + num(cmd.value, 0)) * 2) / 2, 1, 30); break;
      case 'dir': st.dir = cmd.value === -1 ? -1 : cmd.value === 1 ? 1 : -st.dir; break;
      case 'set': {
        const v = cmd.values || {};
        if ('fontSize' in v) st.fontSize = clamp(num(v.fontSize, st.fontSize), 20, 200);
        if ('lineHeight' in v) st.lineHeight = clamp(num(v.lineHeight, st.lineHeight), 1, 2.5);
        if ('margin' in v) st.margin = clamp(num(v.margin, st.margin), 0, 30);
        if ('marker' in v) st.marker = clamp(num(v.marker, st.marker), 5, 80);
        if ('mirrorX' in v) st.mirrorX = !!v.mirrorX;
        if ('mirrorY' in v) st.mirrorY = !!v.mirrorY;
        if ('align' in v) st.align = ['left', 'center'].includes(v.align) ? v.align : st.align;
        break;
      }
      case 'script':
        if (!s.scripts[cmd.id]) return { error: 'script not found' };
        st.scriptId = cmd.id; st.playing = false; st.anchor = { para: 0, frac: 0 };
        break;
      case 'jump':
        st.anchor = { para: Math.max(0, Math.floor(num(cmd.para, 0))), frac: 0 };
        return { relay: { type: 'jump', para: st.anchor.para } };
      case 'restart':
        st.playing = false; st.anchor = { para: 0, frac: 0 };
        return { state: true, relay: { type: 'jump', para: 0 } };
      case 'nudge':
        return { relay: { type: 'nudge', lines: clamp(num(cmd.lines, 0), -50, 50) } };
      default:
        return { error: 'unknown command' };
    }
    return { state: true };
  }

  async function body(request) {
    const raw = await request.text();
    if (raw.length > MAX_SCRIPT_CHARS + 10000) throw new Error('too large');
    try { return raw ? JSON.parse(raw) : {}; } catch { throw new Error('bad json'); }
  }

  function googleDocExport(u) {
    const m = u.match(/docs\.google\.com\/document\/d\/([a-zA-Z0-9_-]+)/);
    return m ? `https://docs.google.com/document/d/${m[1]}/export?format=txt` : null;
  }

  function openStream(request, code, role) {
    const set = clients(code);
    let client;
    const stream = new ReadableStream({
      start(controller) {
        client = { controller, role };
        set.add(client);
        write(set, client, 'retry: 1000\n\n');
        send(set, client, 'state', store.sessions[code].state);
        broadcast(code, 'presence', presence(code));
      },
      cancel() { drop(); },
    });
    function drop() {
      if (!client || !set.has(client)) return;
      set.delete(client);
      try { client.controller.close(); } catch {}
      broadcast(code, 'presence', presence(code));
    }
    if (request.signal) request.signal.addEventListener('abort', drop);
    return new Response(stream, {
      headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-store, no-transform', 'x-accel-buffering': 'no' },
    });
  }

  async function handleApi(request, url) {
    const parts = url.pathname.split('/').filter(Boolean);
    const method = request.method;

    if (parts[1] === 'info' && method === 'GET') {
      return json(200, { port: opts.port || null, lan: opts.lan ? opts.lan() : [], ttlDays: SESSION_TTL_DAYS });
    }

    // New session: the script comes first, then the code.
    if (parts[1] === 'sessions' && !parts[2] && method === 'POST') {
      const script = cleanScript(await body(request));
      if (script.error) return json(400, script);
      let code;
      do { code = randomCode(); } while (store.sessions[code]);
      const id = randomId();
      store.sessions[code] = { state: { ...DEFAULT_STATE, scriptId: id }, scripts: { [id]: { id, ...script } }, created: now(), lastActive: now() };
      store.save(code);
      return json(200, { code, scriptId: id, title: script.title });
    }

    if (parts[1] === 'import' && method === 'POST') {
      const b = await body(request);
      const target = String(b.url || '').trim();
      if (!/^https?:\/\//i.test(target)) return json(400, { error: 'Paste a full link that starts with https://' });
      if (/claude\.ai\/(code\/)?artifact/i.test(target)) {
        return json(400, { error: 'Claude Docs links are private, so they cannot be opened here. In the doc, use Export, Markdown, then upload the file.' });
      }
      const gdoc = googleDocExport(target);
      try {
        const r = await fetch(gdoc || target, { redirect: 'follow', headers: { 'user-agent': 'TantraTeleprompter/1.0' } });
        if (!r.ok) throw new Error(`the link answered ${r.status}`);
        const text = await r.text();
        if (gdoc && /<html/i.test(text.slice(0, 500))) {
          return json(400, { error: 'Google asked for a sign in. In the doc, click Share, set General access to "Anyone with the link", then try again.' });
        }
        return json(200, parseImport(text, { url: target, isGoogleDoc: !!gdoc }));
      } catch (e) {
        return json(400, { error: `Could not read that link: ${e.message}` });
      }
    }

    if (parts[1] === 'sessions' && parts[2]) {
      const code = cleanCode(parts[2]);
      const s = store.sessions[code];
      if (!s) return json(404, { error: 'No session with that code. Check the code, or add a script and generate a new one.' });
      touch(code);
      const action = parts[3];

      if (action === 'events' && method === 'GET') return openStream(request, code, url.searchParams.get('role') || 'other');
      if (!action && method === 'GET') return json(200, { code, state: s.state, presence: presence(code), scripts: listScripts(s) });

      if (action === 'scripts') {
        const id = parts[4];
        if (method === 'GET' && !id) return json(200, listScripts(s));
        if (method === 'GET' && id) return s.scripts[id] ? json(200, s.scripts[id]) : json(404, { error: 'not found' });
        if (method === 'POST' || method === 'PUT') {
          if (id && !s.scripts[id]) return json(404, { error: 'not found' });
          if (!id && Object.keys(s.scripts).length >= MAX_SCRIPTS) return json(400, { error: `This code already has ${MAX_SCRIPTS} scripts. Delete one first.` });
          const script = cleanScript(await body(request));
          if (script.error) return json(400, script);
          const sid = id || randomId();
          s.scripts[sid] = { id: sid, ...script };
          if (!s.state.scriptId || !s.scripts[s.state.scriptId]) s.state.scriptId = sid;
          store.save(code);
          broadcast(code, 'script', { id: sid, updatedAt: script.updatedAt });
          return json(200, s.scripts[sid]);
        }
        if (method === 'DELETE' && id) {
          if (!s.scripts[id]) return json(404, { error: 'not found' });
          if (Object.keys(s.scripts).length === 1) return json(400, { error: 'This is the only script in this code. Add another one before deleting it.' });
          delete s.scripts[id];
          if (s.state.scriptId === id) { s.state.scriptId = listScripts(s)[0].id; s.state.playing = false; s.state.anchor = { para: 0, frac: 0 }; broadcast(code, 'state', s.state); }
          store.save(code);
          broadcast(code, 'script', { id, deleted: true });
          return json(200, { ok: true });
        }
        return json(405, { error: 'method not allowed' });
      }

      if (action === 'cmd' && method === 'POST') {
        const out = applyCommand(s, await body(request));
        if (out.error) return json(400, out);
        s.state.seq++;
        if (out.state) broadcast(code, 'state', s.state);
        if (out.relay) broadcast(code, 'cmd', { ...out.relay, seq: s.state.seq, at: Date.now() });
        store.save(code);
        return json(200, { ok: true, seq: s.state.seq });
      }

      if (action === 'pos' && method === 'POST') {
        const b = await body(request);
        const para = Math.max(0, Math.floor(num(b.para, 0)));
        const frac = clamp(num(b.frac, 0), 0, 1);
        s.state.anchor = { para, frac };
        const msg = { para, frac, progress: clamp(num(b.progress, 0), 0, 1), atEnd: !!b.atEnd };
        const set = clients(code);
        for (const c of [...set]) if (c.role !== 'prompter') send(set, c, 'pos', msg);
        if (b.atEnd && s.state.playing && s.state.dir === 1) { s.state.playing = false; broadcast(code, 'state', s.state); }
        store.save(code);
        return json(200, { ok: true });
      }
    }
    return json(404, { error: 'not found' });
  }

  return {
    async fetch(request) {
      const url = new URL(request.url);
      try {
        return await handleApi(request, url);
      } catch (e) {
        return json(500, { error: e.message });
      }
    },
  };
}

module.exports = { createCore, DEFAULT_STATE, cleanCode, randomCode, SESSION_TTL_DAYS };
