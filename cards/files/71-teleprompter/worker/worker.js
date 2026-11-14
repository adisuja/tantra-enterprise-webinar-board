// Cloudflare Worker for teleprompter.usetantra.com.
// Static files from ../public are bundled into the script (assets.generated.js). Everything under /api goes to one Durable Object,
// which runs the same core as the Mac server and keeps scripts and rooms in its storage.
import { DurableObject } from 'cloudflare:workers';
import { createCore } from '../core.js';
import files from './assets.generated.js';

const MIME = {
  html: 'text/html; charset=utf-8', js: 'text/javascript; charset=utf-8', css: 'text/css; charset=utf-8',
  png: 'image/png', woff2: 'font/woff2', webmanifest: 'application/manifest+json', svg: 'image/svg+xml',
};
const decoded = {};
function bytes(p, entry) {
  if (typeof entry === 'string') return entry;
  if (!decoded[p]) decoded[p] = Uint8Array.from(atob(entry.b64), (c) => c.charCodeAt(0));
  return decoded[p];
}
const PRETTY = { '/': '/index.html', '/prompter': '/prompter.html', '/remote': '/remote.html', '/scripts': '/scripts.html' };

function serveFile(url) {
  const p = PRETTY[url.pathname] || url.pathname;
  const entry = files[p];
  if (entry === undefined) return new Response('Not found', { status: 404 });
  const ext = p.split('.').pop();
  const cache = ext === 'woff2' || ext === 'png' ? 'public, max-age=86400' : 'no-cache';
  return new Response(bytes(p, entry), { headers: { 'content-type': MIME[ext] || 'text/plain', 'cache-control': cache } });
}

export class Hub extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.ready = ctx.blockConcurrencyWhile(async () => {
      const st = ctx.storage;
      // One key per session. Data from earlier designs (script library, rooms, seeds) is cleared once.
      if ((await st.get('schema')) !== 3) { await st.deleteAll(); await st.put('schema', 3); }
      const sessions = {};
      for (const [k, v] of await st.list({ prefix: 'session:' })) sessions[k.slice(8)] = v;
      const dirty = new Set();
      let timer = null;
      const flush = async () => {
        timer = null;
        const puts = {}; const dels = [];
        for (const code of dirty) { if (store.sessions[code]) puts['session:' + code] = store.sessions[code]; else dels.push('session:' + code); }
        dirty.clear();
        const keys = Object.keys(puts);
        for (let i = 0; i < keys.length; i += 100) await st.put(Object.fromEntries(keys.slice(i, i + 100).map((k) => [k, puts[k]])));
        if (dels.length) await st.delete(dels);
      };
      const store = {
        sessions,
        save(code) { dirty.add(code); if (!timer) timer = setTimeout(flush, 300); },
      };
      this.core = createCore(store, {});
    });
  }
  async fetch(request) {
    await this.ready;
    return this.core.fetch(request);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      const hub = env.HUB.get(env.HUB.idFromName('hub'));
      return hub.fetch(request);
    }
    return serveFile(url);
  },
};
