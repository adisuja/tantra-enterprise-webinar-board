// Shared helpers: API calls, session codes, a live connection that heals itself, keep awake, QR codes.
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);

  async function api(path, opts) {
    opts = opts || {};
    const r = await fetch(path, {
      method: opts.method || (opts.body ? 'POST' : 'GET'),
      headers: { 'content-type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      cache: 'no-store',
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) { const e = new Error(data.error || `Request failed (${r.status})`); e.status = r.status; throw e; }
    return data;
  }

  // A session code links devices. It comes from ?code= in the link; each phone also remembers its last code.
  const cleanCode = (c) => String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
  function rememberCode(c) { try { localStorage.setItem('tp_code', c); } catch {} }
  function lastCode() { try { return cleanCode(localStorage.getItem('tp_code')); } catch { return ''; } }
  function codeFromUrl() {
    const c = cleanCode(qs.get('code'));
    if (c) rememberCode(c);
    return c;
  }
  // Prompter, remote and scripts pages need a code: without one, go to the home page.
  function requireCode() {
    const c = codeFromUrl() || lastCode();
    if (!c) { location.replace('/'); throw new Error('no session code'); }
    return c;
  }
  const sessionPath = (code, rest) => `/api/sessions/${encodeURIComponent(code)}${rest || ''}`;
  // A wrong or expired code goes back to the home page with a note.
  function ensureSession(code) {
    return api(sessionPath(code)).catch((e) => { if (e.status === 404) location.replace('/?missing=' + encodeURIComponent(code)); throw e; });
  }
  const scriptsPath = (code, id) => sessionPath(code, '/scripts' + (id ? '/' + encodeURIComponent(id) : ''));

  // Live connection to a session over Server-Sent Events.
  // Reconnects on errors, on silence (no ping for 25 s), and when the phone wakes up.
  function connect(room, role, handlers) {
    let es = null, lastMsg = 0, closed = false, retryTimer = null;
    const setStatus = handlers.status || function () {};
    function open() {
      clearTimeout(retryTimer);
      if (es) es.close();
      const url = sessionPath(room, `/events?role=${role}&t=${Date.now()}`);
      es = new EventSource(url);
      setStatus('connecting');
      es.onopen = () => { lastMsg = Date.now(); setStatus('online'); };
      es.onerror = () => {
        setStatus('offline');
        if (es.readyState === 2) { retryTimer = setTimeout(open, 1000); }
      };
      for (const ev of ['state', 'cmd', 'pos', 'presence', 'script', 'ping']) {
        es.addEventListener(ev, (e) => {
          lastMsg = Date.now();
          setStatus('online');
          if (ev === 'ping') return;
          let data; try { data = JSON.parse(e.data); } catch { return; }
          if (handlers[ev]) handlers[ev](data);
        });
      }
    }
    open();
    setInterval(() => { if (!closed && Date.now() - lastMsg > 25000) open(); }, 5000);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && (!es || es.readyState !== 1 || Date.now() - lastMsg > 12000)) open();
    });
    window.addEventListener('online', open);
    window.addEventListener('pageshow', (e) => { if (e.persisted) open(); });
    return { reopen: open, close() { closed = true; if (es) es.close(); } };
  }

  // Send a command; returns round trip time in ms.
  async function command(room, cmd) {
    const t0 = performance.now();
    await api(sessionPath(room, '/cmd'), { body: cmd });
    return Math.round(performance.now() - t0);
  }

  // Keep the screen on: Wake Lock where the page is secure, a silent looping video otherwise.
  function keepAwake() {
    let lock = null, video = null;
    async function on() {
      if ('wakeLock' in navigator && window.isSecureContext) {
        try { lock = await navigator.wakeLock.request('screen'); lock.addEventListener('release', () => { lock = null; }); return 'wakelock'; } catch {}
      }
      if (!video) {
        video = document.createElement('video');
        video.setAttribute('playsinline', ''); video.setAttribute('muted', ''); video.muted = true; video.loop = true;
        video.setAttribute('title', 'keep awake');
        video.style.cssText = 'position:fixed;width:1px;height:1px;opacity:0.01;left:0;bottom:0;pointer-events:none';
        const webm = document.createElement('source'); webm.src = window.KEEPAWAKE_WEBM; webm.type = 'video/webm';
        const mp4 = document.createElement('source'); mp4.src = window.KEEPAWAKE_MP4; mp4.type = 'video/mp4';
        video.append(webm, mp4);
        document.body.appendChild(video);
      }
      try { await video.play(); return 'video'; } catch { return 'none'; }
    }
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && (lock === null)) on(); });
    return { on };
  }

  function qrSvg(text, px) {
    if (typeof qrcode !== 'function') return '';
    const q = qrcode(0, 'M'); q.addData(text); q.make();
    const n = q.getModuleCount(), s = px / (n + 8);
    let d = '';
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${(c + 4) * s},${(r + 4) * s}h${s}v${s}h-${s}z`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${px} ${px}" width="${px}" height="${px}" role="img" aria-label="QR code"><rect width="100%" height="100%" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
  }

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  window.TP = { api, ensureSession, connect, command, keepAwake, codeFromUrl, requireCode, rememberCode, lastCode, cleanCode, sessionPath, scriptsPath, qrSvg, esc, qs };
})();
