/* Hub pages: Funnels (every funnel of a brand) and Integrations (every provider, per brand).
   Same dock, tokens and type as the kit dashboard. Data from /api/*. Text always escaped. */
"use strict";
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const q = encodeURIComponent;
const P = new URLSearchParams(location.search);
const PAGE = document.body.dataset.page;
const nn = x => x != null && !Number.isNaN(x);
const f0 = x => nn(x) ? Math.round(x).toLocaleString('en-US') : '\u2014';
const pc = (x, d = 1) => nn(x) ? x.toFixed(d) + '%' : '\u2014';
let H = { brands: [], providers: [], categories: {}, brand: null, conns: [], funnels: [] };

async function api(path, opts = {}) {
  const r = await fetch(path, { credentials: 'same-origin', headers: { 'content-type': 'application/json' }, ...opts, body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (r.status === 401) { location.href = '/'; throw new Error('signed out'); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || ('Request failed (' + r.status + ')'));
  return d;
}

/* ---------- theme (same storage keys as the dashboard) ---------- */
const tdGet = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } };
const tdSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
function applyTheme() {
  const m = tdGet('td-mode', tdGet('wi-theme', 'system'));
  const dark = m === 'dark' || (m === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
  const de = document.documentElement; de.dataset.theme = dark ? 'dark' : 'light';
  de.dataset.palette = tdGet('td-palette', (H.brand && H.brand.config && H.brand.config.palette) || 'classic'); de.dataset.gradient = tdGet('td-grad', 'on');
}

/* ---------- icons and dock ---------- */
const I = {
  funnels: '<path d="M4 5h16l-6 7v6l-4 2v-8z"/>', integrations: '<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="18" r="2.4"/><path d="M8.4 6h7.2M6 8.4v7.2M18 8.4v7.2M8.4 18h7.2"/>',
  theme: '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>', out: '<path d="M14 4h5v16h-5"/><path d="M10 8l-4 4 4 4"/><path d="M6 12h10"/>',
  brand: '<path d="M4 20V8l8-4 8 4v12"/><path d="M9 20v-6h6v6"/>' };
const ico = k => `<svg viewBox="0 0 24 24" aria-hidden="true">${I[k] || ''}</svg>`;
const initials = s => String(s || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('');
function dock() {
  const b = H.brand || {};
  const it = (href, k, l, sub, on) => `<a class="dk${on ? ' on' : ''}" href="${href}" ${on ? 'aria-current="page"' : ''}>${ico(k)}<span class="tag">${l}</span><span class="tg"><b>${l}</b><small>${sub}</small></span></a>`;
  $('#dock').innerHTML = `<div class="brand"><button class="td-sw" id="tdSw" aria-haspopup="menu"><span class="td-mark">${esc(initials(b.name))}</span><span class="bw"><b>${esc(b.name || 'Brands')}</b><small>${H.funnels.length} funnel${H.funnels.length === 1 ? '' : 's'}</small></span><span class="chev">▾</span></button></div>
   <div class="grp">This brand</div>
   ${it('/funnels?b=' + q(b.id || ''), 'funnels', 'Funnels', 'Every funnel and how it is doing', PAGE === 'funnels')}
   ${it('/integrations?b=' + q(b.id || ''), 'integrations', 'Integrations', `${H.conns.length} connected`, PAGE === 'integrations')}
   <div class="gap"></div>
   <button class="dk aux" id="brandBtn">${ico('brand')}<span class="tag">Brand settings</span><span class="tg"><b>Brand settings</b><small>Name, theme, exclusions</small></span></button>
   <button class="dk aux" id="modeBtn">${ico('theme')}<span class="tag">Light / dark</span><span class="tg"><b>Light / dark</b></span></button>
   <button class="dk aux" id="outBtn">${ico('out')}<span class="tag">Sign out</span><span class="tg"><b>Sign out</b></span></button>`;
}
function topStrip() { if ($('#tdTop')) return; const st = document.querySelector('.stage'); const d = document.createElement('div'); d.id = 'tdTop'; d.className = 'td-top';
  d.innerHTML = `<button class="td-sw" id="tdSwM" aria-haspopup="menu" aria-label="Switch brand"><span class="td-mark">${esc(initials(H.brand && H.brand.name))}</span><span class="bw"><b>${esc(H.brand ? H.brand.name : 'Brands')}</b><small>${H.funnels.length} funnel${H.funnels.length === 1 ? '' : 's'}</small></span><span class="chev">▾</span></button><button class="td-ic" id="modeBtnM" aria-label="Light or dark">${ico('theme')}</button>`;
  st.insertBefore(d, st.firstChild); }
function bar(title) {
  $('#bar').innerHTML = `<div class="crumb"><b>${esc(H.brand ? H.brand.name : 'Tantra')}</b><span>${esc(title)}</span></div>`;
}
function menu(anchor) {
  let m = $('#tdMenu'); if (!m) { m = document.createElement('div'); m.id = 'tdMenu'; m.className = 'td-menu'; document.body.appendChild(m); }
  if (m.classList.contains('on')) { m.classList.remove('on'); return; }
  m.innerHTML = H.brands.map(b => `<a href="/${PAGE}?b=${q(b.id)}" class="${H.brand && b.id === H.brand.id ? 'on' : ''}"><span class="td-mark" style="width:24px;height:24px;font-size:11px">${esc(initials(b.name))}</span><span><span>${esc(b.name)}</span><small>${b.funnels} funnel${b.funnels === 1 ? '' : 's'} · ${b.connections} integration${b.connections === 1 ? '' : 's'}</small></span></a>`).join('') +
    `<div class="sep"></div><button class="it" data-newbrand="1"><span><span>Add a brand</span><small>Its own funnels and integrations</small></span></button>`;
  const r = anchor.getBoundingClientRect(); m.style.left = Math.max(8, Math.min(r.left, innerWidth - 300)) + 'px'; m.style.top = (innerWidth <= 760 ? 70 : r.bottom + 6) + 'px'; m.classList.add('on');
}

/* ---------- drawer (kit markup) ---------- */
function openDrawer(html) { const d = $('#drawer'); d.innerHTML = `<button class="x" data-close="1" aria-label="Close">✕</button>${html}`; d.classList.add('on'); $('#scrim').classList.add('on'); d.scrollTop = 0; const f = d.querySelector('input,select,button:not(.x)'); (f || d.querySelector('.x')).focus(); }
function closeDrawer() { $('#drawer').classList.remove('on'); $('#scrim').classList.remove('on'); }
const field = (f, val, opt) => `<label class="hf"><span>${esc(f.label)}${f.optional ? ' <i>optional</i>' : ''}</span>
  <input class="hi" ${opt ? 'data-opt' : 'data-cred'}="${esc(f.key)}" type="${f.secret ? 'password' : 'text'}" autocomplete="off" placeholder="${esc(f.placeholder || '')}" value="${f.secret ? '' : esc(val || '')}">${f.help ? `<small>${esc(f.help)}</small>` : ''}</label>`;
const toast = (msg, bad) => { let t = $('#toast'); if (!t) { t = document.createElement('div'); t.id = 'toast'; document.body.appendChild(t); } t.className = 'toast on' + (bad ? ' bad' : ''); t.textContent = msg; clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 4200); };

/* ---------- motion (content kit timeline, live) ---------- */
function animate(root) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  root.querySelectorAll('[data-n]').forEach(el => { const to = +el.dataset.n; if (!nn(to)) return; const t0 = performance.now(), dur = 900; const fmt = el.dataset.fmt === 'pct' ? (v => v.toFixed(1) + '%') : el.dataset.fmt === 'money' ? (v => el.dataset.cur + Math.round(v).toLocaleString('en-US')) : (v => Math.round(v).toLocaleString('en-US'));
    const st = t => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(to * e); if (k < 1) requestAnimationFrame(st); }; requestAnimationFrame(st); });
}

/* ================= FUNNELS ================= */
const TPL = {
  webinar: { l: 'Webinar', d: 'Live sessions on a schedule: invited, registered, attended, booked, bought.', unit: ['webinar', 'webinars', 'W'] },
  workshop: { l: 'Workshop or challenge', d: 'A multi-day live event run in cohorts.', unit: ['cohort', 'cohorts', 'C'] },
  call: { l: 'Booked call', d: 'Outreach straight to a sales call, measured in weekly cohorts.', unit: ['week', 'weeks', 'Wk'] },
  lead_magnet: { l: 'Lead magnet', d: 'Content or a download that turns into leads, then calls and sales, in weekly cohorts.', unit: ['week', 'weeks', 'Wk'] },
  launch: { l: 'Product launch', d: 'One launch window with its waitlist, cart open and sales.', unit: ['launch', 'launches', 'L'] },
};
function spark(vals) { const v = vals.filter(nn); if (v.length < 2) return ''; const max = Math.max(...v, 1), W = 160, Hh = 40; const pts = vals.map((x, i) => [i / (vals.length - 1) * W, Hh - 4 - (nn(x) ? x : 0) / max * (Hh - 8)]);
  const d = 'M' + pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L');
  return `<svg class="hs" viewBox="0 0 ${W} ${Hh}" preserveAspectRatio="none" aria-hidden="true"><path d="${d}L${W},${Hh}L0,${Hh}Z" fill="var(--ocean-soft)"/><path d="${d}" fill="none" stroke="var(--ocean)" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>`; }
async function pageFunnels() {
  bar('Funnels');
  const b = H.brand;
  if (!b) { $('#canvas').innerHTML = `<div class="rise"><h1 class="h2">Add your first brand</h1><p class="sub" style="margin-top:10px">A brand holds its own funnels and its own integrations.</p><button class="hb primary" data-newbrand="1" style="margin-top:20px">Add a brand</button></div>`; return; }
  const list = H.funnels;
  const cards = list.map((f, i) => { const s = f.summary || {};
    return `<a class="fx rise" style="--d:${i}" href="/f/${q(f.id)}">
      <div class="fx-h"><span class="pill">${esc((TPL[f.template] || {}).l || f.template)}</span>${f.status !== 'live' ? `<span class="pill prov">${esc(f.status)}</span>` : ''}<span class="sp"></span><span class="fx-age">${s.generated ? 'Updated ' + esc(ago(s.generated)) : 'Building…'}</span></div>
      <h2 class="h3 fx-n">${esc(f.name)}</h2>
      <div class="fx-k">
        <div><b class="num" data-n="${nn(s.registrations) ? s.registrations : ''}">${f0(s.registrations)}</b><span>${esc(s.reg_label || 'Registered')}</span></div>
        <div><b class="num" data-n="${nn(s.attend_pct) ? s.attend_pct : ''}" data-fmt="pct">${pc(s.attend_pct)}</b><span>${esc(s.att_label || 'Attendance rate')}</span></div>
        <div><b class="num" data-n="${nn(s.customers) ? s.customers : ''}">${f0(s.customers)}</b><span>Customers</span></div>
        <div><b class="num td-gt" data-n="${nn(s.revenue) ? s.revenue : ''}" data-fmt="money" data-cur="${esc(s.currency_symbol || '$')}">${nn(s.revenue) ? esc(s.currency_symbol || '$') + f0(s.revenue) : '\u2014'}</b><span>Revenue</span></div>
      </div>
      <div class="fx-f">${spark(s.spark || [])}<span class="fx-meta">${nn(s.events) ? f0(s.events) + ' ' + esc(s.events === 1 ? (s.unit_singular || 'event') : (s.unit_plural || 'events')) : ''}${nn(s.confidence) ? ' · data confidence ' + f0(s.confidence) + '/100' : ''}</span><span class="go">→</span></div></a>`; }).join('');
  const missing = H.missing || [];
  $('#canvas').innerHTML = `<section class="rise"><span class="lbl">${esc(b.name)}</span><h1 class="hero-t">Funnels</h1>
      <p class="sub" style="margin-top:10px">Every funnel this brand runs, each with the full dashboard behind it. Numbers refresh hourly from the connected tools.</p>
      <div class="hrow"><button class="hb primary" data-newfunnel="1">Add a funnel</button><a class="hb" href="/integrations?b=${q(b.id)}">Integrations · ${H.conns.length} connected</a></div></section>
    ${missing.length ? `<div class="td-setup rise" style="--d:1"><div class="sub"><b>Connect ${missing.length === 1 ? 'one more source' : missing.length + ' more sources'}</b> to fill every section of these dashboards.</div><div class="roles">${missing.map(m => `<a class="td-cn" href="/integrations?b=${q(b.id)}&cat=${q(m.category)}">${esc(m.label)}</a>`).join('')}</div></div>` : ''}
    <div class="fxg sec">${cards || `<div class="hempty rise"><img src="/img/empty-funnels.jpg" alt="" width="360"><h2 class="h2">No funnels yet</h2><p class="sub">Pick a template, give it a name, and the dashboard builds itself from the tools you connect.</p><button class="hb primary" data-newfunnel="1">Add a funnel</button></div>`}</div>`;
  animate($('#canvas'));
  if (P.get('new') === '1') funnelDrawer();
}
const ago = iso => { const s = (Date.now() - Date.parse(iso)) / 1000; return s < 90 ? 'just now' : s < 3600 ? Math.round(s / 60) + ' min ago' : s < 86400 ? Math.round(s / 3600) + ' h ago' : Math.round(s / 86400) + ' days ago'; };
function funnelDrawer(f) {
  f = f || { template: 'webinar', config: {} }; const c = f.config || {}, s = c.schedule || {};
  openDrawer(`<span class="lbl">${f.id ? 'Edit funnel' : 'New funnel'}</span><h2 style="font-size:clamp(28px,4vw,40px);letter-spacing:-.03em;margin-bottom:16px">${f.id ? esc(f.name) : 'Add a funnel'}</h2>
    <form id="ff" class="hform">
      <label class="hf"><span>Name</span><input class="hi" name="name" required value="${esc(f.name || '')}" placeholder="Enterprise webinar"></label>
      <div class="hf"><span>Template</span><div class="tplg">${Object.entries(TPL).map(([k, t]) => `<label class="tpl"><input type="radio" name="template" value="${k}" ${f.template === k ? 'checked' : ''}><b>${t.l}</b><small>${t.d}</small></label>`).join('')}</div></div>
      <fieldset class="hset"><legend>Schedule (webinar and workshop templates)</legend>
        <div class="h2c"><label class="hf"><span>First date</span><input class="hi" name="first" type="date" value="${esc(s.first || '')}"></label><label class="hf"><span>Start time</span><input class="hi" name="time" type="time" value="${esc(s.time || '11:00')}"></label></div>
        <div class="h2c"><label class="hf"><span>Time zone</span><input class="hi" name="tz" value="${esc(s.tz || 'Europe/London')}"></label><label class="hf"><span>Repeats every (days)</span><input class="hi" name="every" type="number" min="0" value="${esc(s.every_days ?? 7)}"></label></div>
      </fieldset>
      <fieldset class="hset"><legend>Money and market</legend>
        <div class="h2c"><label class="hf"><span>Currency</span><select class="hi" name="currency">${['USD', 'GBP', 'EUR', 'INR', 'AUD', 'CAD', 'AED', 'SGD'].map(x => `<option ${(c.currency || 'USD') === x ? 'selected' : ''}>${x}</option>`).join('')}</select></label><label class="hf"><span>Home market (country)</span><input class="hi" name="home" value="${esc(c.home_market || 'United States')}"></label></div>
        <div class="h2c"><label class="hf"><span>Smallest real sale</span><input class="hi" name="minsale" type="number" min="0" value="${esc(c.min_real_payment ?? 50)}"><small>Payments below this are tests or deposits.</small></label><label class="hf"><span>Sales maturity (days)</span><input class="hi" name="maturity" type="number" min="1" value="${esc(c.maturity_days ?? 21)}"><small>How long sales keep arriving after an event.</small></label></div>
      </fieldset>
      <fieldset class="hset"><legend>What belongs to this funnel</legend>
        <label class="hf"><span>Campaigns whose name or tag contains</span><input class="hi" name="match" value="${esc(c.campaign_match || '')}" placeholder="enterprise"><small>Used for outreach and email campaigns from every connected tool. Empty means all.</small></label>
        <label class="hf"><span>Link campaigns (prefixes)</span><input class="hi" name="links" value="${esc((c.link_campaigns || []).join(', '))}" placeholder="webinar_, tantra_pro"></label>
        <label class="hf"><span>Booking pages or event types (names contain)</span><input class="hi" name="bookings" value="${esc((c.booking_match || []).join(', '))}" placeholder="strategy call"></label>
      </fieldset>
      <div class="hrow"><button class="hb primary" type="submit">${f.id ? 'Save' : 'Create funnel'}</button>${f.id ? `<button class="hb danger" type="button" data-delfunnel="${esc(f.id)}">Delete funnel</button>` : ''}</div>
    </form>`);
  $('#ff').addEventListener('submit', async e => { e.preventDefault(); const F = new FormData(e.target); const t = F.get('template');
    const cfg = { ...c, currency: F.get('currency'), home_market: F.get('home'), min_real_payment: +F.get('minsale') || 0, maturity_days: +F.get('maturity') || 21,
      campaign_match: F.get('match') || '', link_campaigns: String(F.get('links') || '').split(',').map(x => x.trim()).filter(Boolean), booking_match: String(F.get('bookings') || '').split(',').map(x => x.trim()).filter(Boolean),
      schedule: { first: F.get('first') || null, time: F.get('time') || '11:00', tz: F.get('tz') || 'UTC', every_days: +F.get('every') || 0, duration_min: s.duration_min || 60 },
      unit: { singular: TPL[t].unit[0], plural: TPL[t].unit[1], prefix: TPL[t].unit[2] } };
    try { const r = await api('/api/funnels', { method: 'POST', body: { id: f.id, brand_id: H.brand.id, name: F.get('name'), template: t, config: cfg } }); toast('Saved. Building the dashboard…'); location.href = '/f/' + q(r.id); } catch (err) { toast(err.message, true); } });
}

/* ================= INTEGRATIONS ================= */
async function pageIntegrations() {
  bar('Integrations');
  if (!H.brand) { $('#canvas').innerHTML = '<p class="sub">Add a brand first.</p>'; return; }
  const cat = P.get('cat') || 'all';
  const byP = {}; H.conns.forEach(c => { (byP[c.provider] = byP[c.provider] || []).push(c); });
  const cats = Object.entries(H.categories).filter(([k]) => H.providers.some(p => p.category === k));
  const tile = (p, i) => { const cs = byP[p.id] || []; const c = cs[0];
    const st = !c ? '' : c.status === 'active' ? (c.last_ok_at ? 'ok' : 'wait') : c.status === 'auth_error' ? 'bad' : c.status === 'rate_limited' ? 'wait' : 'bad';
    const word = !c ? 'Not connected' : st === 'ok' ? 'Connected' : st === 'wait' ? (c.status === 'rate_limited' ? 'Slowed by provider' : 'First refresh pending') : c.status === 'auth_error' ? 'Key refused' : 'Last refresh failed';
    return `<button class="it rise${c ? ' has' : ''}" style="--d:${Math.min(i, 12)}" data-prov="${esc(p.id)}"><span class="it-m" style="--c:${esc(p.color || '#64748b')}">${esc(initials(p.name))}</span><span class="it-b"><b>${esc(p.name)}</b><small>${esc(H.categories[p.category] || p.category)}</small></span>
      <span class="it-s ${st}">${word}${c && c.last_ok_at ? `<small>${esc(ago(c.last_ok_at))}${nn(c.rows_last) ? ' · ' + f0(c.rows_last) + (c.rows_last === 1 ? ' row' : ' rows') : ''}</small>` : ''}</span></button>`; };
  const GROUP = { outreach: ['tantra', 'cold_email', 'linkedin'] };
  const shown = H.providers.filter(p => cat === 'all' || p.category === cat || (GROUP[cat] || []).includes(p.category)).sort((a, b) => (byP[b.id] ? 1 : 0) - (byP[a.id] ? 1 : 0) || a.name.localeCompare(b.name));
  const reqHour = H.conns.reduce((s, c) => s + (c.requests_last || 0), 0);
  $('#canvas').innerHTML = `<img class="ih-art rise" src="/img/integrations.jpg" alt="" aria-hidden="true"><section class="rise"><span class="lbl">${esc(H.brand.name)}</span><h1 class="hero-t">Integrations</h1>
     <p class="sub" style="margin-top:10px">Connect the tools this brand uses across its revenue workflow. Keys are encrypted and never shown again. Each source refreshes once an hour, spread across the hour and kept inside its provider's rate limits.</p>
     <div class="ikp"><div><b class="num" data-n="${H.conns.length}">${H.conns.length}</b><span>connected</span></div><div><b class="num" data-n="${H.providers.length}">${H.providers.length}</b><span>available</span></div><div><b class="num" data-n="${reqHour}">${f0(reqHour)}</b><span>calls in the last refresh</span></div></div></section>
   <div class="chips sec" role="tablist"><button class="chp${cat === 'all' ? ' on' : ''}" data-cat="all">All</button>${cats.map(([k, l]) => `<button class="chp${cat === k || (cat === 'outreach' && ['tantra','cold_email','linkedin'].includes(k)) ? ' on' : ''}" data-cat="${esc(k)}">${esc(l)}</button>`).join('')}</div>
   <div class="itg">${shown.map(tile).join('')}</div>`;
  animate($('#canvas'));
  const want = P.get('provider'); if (want) provDrawer(want);
}
async function provDrawer(id) {
  const p = H.providers.find(x => x.id === id); if (!p) return;
  const c = H.conns.find(x => x.provider === id);
  let ds = [];
  if (c) { try { ds = (await api('/api/connections/' + q(c.id))).datasets || []; } catch (e) {} }
  const lim = p.limits || {};
  openDrawer(`<span class="lbl">${esc(H.categories[p.category] || p.category)}</span><h2 style="font-size:clamp(28px,4vw,40px);letter-spacing:-.03em">${esc(p.name)}</h2>
    <p class="sub" style="margin-top:8px">Gives this brand: ${esc((p.provides || []).map(x => DSL[x] || x).join(', ') || 'data pushed from your own systems')}.${p.docs ? ` <a class="link" href="${esc(p.docs)}" target="_blank" rel="noopener">API docs</a>` : ''}</p>
    ${c ? `<div class="ledger" style="margin-top:16px">${[['Status', c.status === 'active' ? (c.last_ok_at ? 'Connected' : 'Waiting for the first refresh') : (c.last_error || c.status)], ['Last good refresh', c.last_ok_at ? ago(c.last_ok_at) : 'not yet'], ['Next refresh', c.next_due_at ? new Date(c.next_due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'soon'], ['Calls used last time', f0(c.requests_last)], ...ds.map(d => [DSL[d.dataset] || d.dataset, f0(d.rows) + (d.rows === 1 ? ' row' : ' rows')])].map(([a, b]) => `<div class="li"><span>${esc(a)}</span><span class="num">${esc(b)}</span></div>`).join('')}</div>` : ''}
    <form id="pf" class="hform" style="margin-top:18px">
      ${p.push ? `<p class="sub">This source receives data instead of fetching it. After saving, send rows in the normalized format to the address shown here.</p>${c && c.ingest_url ? `<label class="hf"><span>Ingest address</span><input class="hi" readonly value="${esc(c.ingest_url)}"></label>` : ''}` : ''}
      ${(p.auth.fields || []).map(f => field(f, c && !f.secret ? (c.public || {})[f.key] : '', false)).join('')}
      ${c && c.has_creds && (p.auth.fields || []).some(f => f.secret) ? `<p class="sub" style="font-size:13px">A key is saved (ending ${esc(c.last4 || '****')}). Leave key fields empty to keep it.</p>` : ''}
      ${(p.options || []).length ? `<fieldset class="hset"><legend>Options</legend>${p.options.map(o => field(o, c ? (c.options || {})[o.key] : '', true)).join('')}</fieldset>` : ''}
      <p class="sub" style="font-size:13px">Refreshes every ${f0(Math.max(lim.refresh_minutes || 60, 30))} minutes, at most ${f0(lim.max_requests || 30)} calls each time${lim.notes ? '. ' + esc(lim.notes) : '.'}</p>
      <div class="hrow"><button class="hb primary" type="submit">${c ? 'Save' : 'Connect'}</button>${c ? `<button class="hb" type="button" data-test="${esc(c.id)}">Test</button><button class="hb" type="button" data-sync="${esc(c.id)}">Refresh now</button><button class="hb danger" type="button" data-disc="${esc(c.id)}">Disconnect</button>` : ''}</div>
      <div id="pmsg" class="sub" style="margin-top:10px" role="status"></div>
    </form>`);
  $('#pf').addEventListener('submit', async e => { e.preventDefault(); const creds = {}, options = {};
    $$('#pf [data-cred]').forEach(i => { if (i.value.trim()) creds[i.dataset.cred] = i.value.trim(); }); $$('#pf [data-opt]').forEach(i => { options[i.dataset.opt] = i.value.trim(); });
    $('#pmsg').textContent = 'Saving and testing…';
    try { const r = await api('/api/connections', { method: 'POST', body: { id: c && c.id, brand_id: H.brand.id, provider: p.id, creds, options } });
      $('#pmsg').innerHTML = r.test && r.test.ok ? `<b style="color:var(--good)">Connected.</b> ${esc(r.test.detail || '')} The first refresh starts now.` : `<b style="color:var(--bad)">Saved, but the test failed:</b> ${esc(r.test ? r.test.detail : 'no answer')}`;
      await load(); pageIntegrations(); } catch (err) { $('#pmsg').innerHTML = `<b style="color:var(--bad)">${esc(err.message)}</b>`; } });
}
const DSL = { campaigns: 'campaign results', touches: 'people contacted', events: 'events', registrations: 'registrations', attendance: 'attendance', questions: 'questions', bookings: 'booked calls', deals: 'deals', payments: 'payments', contacts: 'audience details', messages: 'messages and calls', ad_daily: 'ad spend and clicks', content_daily: 'content reach', link_clicks: 'link clicks', web_daily: 'website visits', surveys: 'surveys' };

/* ---------- brand settings ---------- */
function brandDrawer(b) {
  b = b || { config: {} }; const c = b.config || {};
  openDrawer(`<span class="lbl">${b.id ? 'Brand settings' : 'New brand'}</span><h2 style="font-size:clamp(28px,4vw,40px);letter-spacing:-.03em;margin-bottom:16px">${b.id ? esc(b.name) : 'Add a brand'}</h2>
    <form id="bf" class="hform">
      <label class="hf"><span>Name</span><input class="hi" name="name" required value="${esc(b.name || '')}"></label>
      <label class="hf"><span>Default theme</span><select class="hi" name="palette">${['classic', 'volt', 'aurora', 'emerald', 'sunset', 'orchid', 'graphite'].map(x => `<option value="${x}" ${(c.palette || 'classic') === x ? 'selected' : ''}>${x[0].toUpperCase() + x.slice(1)}</option>`).join('')}</select><small>Viewers can still choose their own under Appearance.</small></label>
      <label class="hf"><span>Never count these addresses (one per line)</span><textarea class="hi" name="excl" rows="4" placeholder="@yourcompany.com">${esc((c.exclude_patterns || []).join('\n'))}</textarea><small>Team and test sign-ups. Matching people are dropped before any number is counted.</small></label>
      <div class="hrow"><button class="hb primary" type="submit">${b.id ? 'Save' : 'Create brand'}</button></div>
    </form>`);
  $('#bf').addEventListener('submit', async e => { e.preventDefault(); const F = new FormData(e.target);
    try { const r = await api('/api/brands', { method: 'POST', body: { id: b.id, name: F.get('name'), config: { ...c, palette: F.get('palette'), exclude_patterns: String(F.get('excl') || '').split('\n').map(x => x.trim()).filter(Boolean) } } });
      location.href = '/funnels?b=' + q(r.id); } catch (err) { toast(err.message, true); } });
}

/* ================= SETUP (a funnel with no events yet) ================= */
async function pageSetup() {
  const fid = decodeURIComponent(document.body.dataset.funnel || ''); const f = H.funnels.find(x => x.id === fid) || {};
  bar(f.name || 'Funnel');
  $('#canvas').innerHTML = `<section class="rise"><span class="lbl">${esc(H.brand ? H.brand.name : '')}</span><h1 class="hero-t">${esc(f.name || 'This funnel')}</h1>
    <p class="sub" style="margin-top:12px">The dashboard appears as soon as there is a first ${esc((f.config && f.config.unit && f.config.unit.singular) || 'event')} with data. ${f.template === 'webinar' || f.template === 'workshop' || f.template === 'launch' ? 'Set the schedule, or connect the webinar platform so its sessions are read directly.' : 'Connect the tools that record leads, calls and payments.'}</p>
    <div class="hrow"><button class="hb primary" id="editF">Edit schedule and settings</button><a class="hb" href="/integrations?b=${q(H.brand.id)}">Integrations</a><button class="hb" id="rebuildF">Check again</button></div></section>
    ${(H.missing || []).length ? `<div class="td-setup rise" style="--d:1"><div class="sub"><b>Still to connect</b></div><div class="roles">${H.missing.map(m => `<a class="td-cn" href="/integrations?b=${q(H.brand.id)}&cat=${q(m.category)}">${esc(m.label)}</a>`).join('')}</div></div>` : ''}
    <div class="hempty" style="border:0"><img src="/img/empty-funnels.jpg" alt="" width="360"></div>`;
  $('#editF').onclick = () => funnelDrawer(f);
  $('#rebuildF').onclick = async () => { await api('/api/funnels/' + q(fid) + '/rebuild', { method: 'POST' }); location.reload(); };
}

/* ---------- events and boot ---------- */
document.addEventListener('click', async e => { const t = e.target, c = s => t.closest(s); let x;
  if (c('[data-close]') || t.id === 'scrim') { closeDrawer(); return; }
  if (c('#tdSw,#tdSwM')) { e.stopPropagation(); menu(c('#tdSw,#tdSwM')); return; }
  const m = $('#tdMenu'); if (m && m.classList.contains('on') && !c('#tdMenu')) m.classList.remove('on');
  if (c('[data-newbrand]')) { if (m) m.classList.remove('on'); brandDrawer(); return; }
  if (c('#brandBtn')) { brandDrawer(H.brand); return; }
  if (c('#modeBtn,#modeBtnM')) { tdSet('td-mode', document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); applyTheme(); return; }
  if (c('#outBtn')) { await fetch('/api/logout', { method: 'POST' }); location.href = '/'; return; }
  if (c('[data-newfunnel]')) { funnelDrawer(); return; }
  if ((x = c('[data-cat]'))) { const u = new URL(location); u.searchParams.set('cat', x.dataset.cat); history.replaceState(null, '', u); P.set('cat', x.dataset.cat); pageIntegrations(); return; }
  if ((x = c('[data-prov]'))) { provDrawer(x.dataset.prov); return; }
  if ((x = c('[data-test]'))) { $('#pmsg').textContent = 'Testing…'; try { const r = await api('/api/connections/' + q(x.dataset.test) + '/test', { method: 'POST' }); $('#pmsg').innerHTML = r.ok ? `<b style="color:var(--good)">Works.</b> ${esc(r.detail || '')}` : `<b style="color:var(--bad)">Failed:</b> ${esc(r.detail || '')}`; } catch (err) { $('#pmsg').textContent = err.message; } return; }
  if ((x = c('[data-sync]'))) { $('#pmsg').textContent = 'Refreshing…'; try { const r = await api('/api/connections/' + q(x.dataset.sync) + '/sync', { method: 'POST' }); $('#pmsg').innerHTML = r.ok ? `<b style="color:var(--good)">Refreshed.</b> ${f0(r.rows)} rows, ${f0(r.requests)} calls.` : `<b style="color:var(--bad)">${esc(r.error || 'Refresh failed')}</b>`; await load(); } catch (err) { $('#pmsg').textContent = err.message; } return; }
  if ((x = c('[data-disc]'))) { if (!confirm('Disconnect this source? Its stored data is removed from the dashboard.')) return; await api('/api/connections/' + q(x.dataset.disc), { method: 'DELETE' }); closeDrawer(); await load(); pageIntegrations(); return; }
  if ((x = c('[data-delfunnel]'))) { if (!confirm('Delete this funnel and its dashboard? The integrations stay.')) return; await api('/api/funnels/' + q(x.dataset.delfunnel), { method: 'DELETE' }); location.href = '/funnels?b=' + q(H.brand.id); return; }
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeDrawer(); const m = $('#tdMenu'); if (m) m.classList.remove('on'); } });
async function load() {
  const d = await api('/api/hub?b=' + q(P.get('b') || document.body.dataset.brand || ''));
  H = { ...H, ...d };
  applyTheme(); dock(); topStrip();
}
(async () => {
  applyTheme();
  try { await load(); } catch (e) { $('#canvas').innerHTML = `<p class="sub">${esc(e.message)}</p>`; return; }
  if (P.get('newbrand') === '1') brandDrawer();
  if (PAGE === 'funnels') await pageFunnels(); else if (PAGE === 'setup') await pageSetup(); else await pageIntegrations();
})();
