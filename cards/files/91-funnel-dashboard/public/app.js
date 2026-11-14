// Tantra Funnel Dashboard: the page. Pure display: every number comes from the model the
// Worker builds (/api/model). The formatter is the only gate between data and pixels and has
// no path that turns "unavailable" into 0 (dashboard kit, docs/05).
(function () {
  'use strict';

  // ---------------- tiny DOM helpers (text always through textContent) ----------------
  function el(tag, attrs) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k === 'style') n.setAttribute('style', v);
      else if (k.slice(0, 2) === 'on') n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : v);
    }
    for (var i = 2; i < arguments.length; i++) append(n, arguments[i]);
    return n;
  }
  function append(n, c) {
    if (c === null || c === undefined || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { append(n, x); }); return; }
    n.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
  }
  var SVGNS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs) {
    var n = document.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) if (attrs[k] !== null && attrs[k] !== undefined) {
      if (k === 'text') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    for (var i = 2; i < arguments.length; i++) if (arguments[i]) n.appendChild(arguments[i]);
    return n;
  }
  function icon(name) {
    var P = {
      overview: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z',
      acquisition: 'M12 2a10 10 0 100 20 10 10 0 000-20zm0 4l2.5 5.5L20 12l-5.5 2.5L12 20l-2.5-5.5L4 12l5.5-.5L12 6z',
      attendance: 'M12 12a4 4 0 100-8 4 4 0 000 8zm-7 9a7 7 0 0114 0H5z',
      nurture: 'M4 4h16v11H7l-3 3V4zm4 4v2h8V8H8z',
      commercial: 'M3 17l5-5 4 4 8-8v4h2V4h-8v2h4l-6 6-4-4-7 7 2 2z',
      sessions: 'M7 2v2H4v18h16V4h-3V2h-2v2H9V2H7zm-1 8h12v10H6V10z',
      health: 'M12 21l-8.5-8.2A5.2 5.2 0 0112 6.3a5.2 5.2 0 018.5 6.5L12 21zM7 11h3l1-2 2 4 1-2h3',
      settings: 'M19.4 13a7.6 7.6 0 000-2l2-1.6-2-3.4-2.4 1a7.4 7.4 0 00-1.7-1L15 3.5h-4l-.4 2.5a7.4 7.4 0 00-1.7 1l-2.4-1-2 3.4L6.6 11a7.6 7.6 0 000 2l-2 1.6 2 3.4 2.4-1c.5.4 1.1.7 1.7 1l.4 2.5h4l.4-2.5c.6-.3 1.2-.6 1.7-1l2.4 1 2-3.4-2-1.6zM12 15.5a3.5 3.5 0 110-7 3.5 3.5 0 010 7z',
      refresh: 'M17.7 6.3A8 8 0 104 12h2a6 6 0 1110.3 4.2L14 14v6h6l-2.2-2.2A8 8 0 0017.7 6.3z',
      palette: 'M12 3a9 9 0 000 18c1 0 1.5-.7 1.5-1.5 0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1 0-.8.7-1.5 1.5-1.5H16a5 5 0 005-5c0-4.1-4-7.8-9-7.8zM6.5 12a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm3-4a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm5 0a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm3 4a1.5 1.5 0 110-3 1.5 1.5 0 010 3z',
      chevron: 'M7 10l5 5 5-5H7z',
      close: 'M18.3 5.7L12 12l6.3 6.3-1.4 1.4L10.6 13.4 4.3 19.7 2.9 18.3 9.2 12 2.9 5.7 4.3 4.3l6.3 6.3 6.3-6.3 1.4 1.4z',
      sun: 'M12 7a5 5 0 100 10 5 5 0 000-10zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM1 11h3v2H1v-2zm19 0h3v2h-3v-2zM4.2 5.6l1.4-1.4 2.1 2.1-1.4 1.4-2.1-2.1zm12.1 12.1l1.4-1.4 2.1 2.1-1.4 1.4-2.1-2.1zM4.2 18.4l2.1-2.1 1.4 1.4-2.1 2.1-1.4-1.4zM16.3 6.3l2.1-2.1 1.4 1.4-2.1 2.1-1.4-1.4z',
      moon: 'M20 15.3A8.5 8.5 0 018.7 4 8.5 8.5 0 1020 15.3z',
      system: 'M3 4h18v12H3V4zm2 2v8h14V6H5zm3 12h8v2H8v-2z',
    };
    var s = svg('svg', { viewBox: '0 0 24 24', 'aria-hidden': 'true', fill: name === 'health' ? 'none' : 'currentColor' });
    var p = svg('path', { d: P[name] || '' });
    if (name === 'health') { p.setAttribute('stroke', 'currentColor'); p.setAttribute('stroke-width', '1.8'); p.setAttribute('stroke-linejoin', 'round'); }
    s.appendChild(p);
    return s;
  }

  // ---------------- formatting: null is never 0 ----------------
  var NA = 'n/a';
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function n0(v) { return isNum(v) ? Math.round(v).toLocaleString('en-US') : NA; }
  function pct(v, d) { if (!isNum(v)) return NA; var x = v * 100; return (Math.abs(x) >= 10 || d === 0 ? x.toFixed(d === undefined ? 1 : d) : x.toFixed(1)).replace(/\.0$/, '') + '%'; }
  function money(v) {
    if (!isNum(v)) return NA;
    var cur = (state.model && state.model.funnel.currency) || 'USD';
    var sym = cur === 'USD' ? '$' : cur === 'GBP' ? '£' : cur === 'EUR' ? '€' : cur === 'INR' ? '₹' : cur + ' ';
    if (Math.abs(v) >= 1e6) return sym + (v / 1e6).toFixed(2).replace(/\.?0+$/, '') + 'M';
    if (Math.abs(v) >= 1e4) return sym + Math.round(v / 1e3).toLocaleString('en-US') + 'K';
    if (Math.abs(v) >= 100 || Number.isInteger(v)) return sym + Math.round(v).toLocaleString('en-US');
    return sym + v.toFixed(2);
  }
  function ratioX(v) { return isNum(v) ? v.toFixed(v >= 10 ? 0 : 1) + 'x' : NA; }
  function fmtCell(c, kind) {
    var v = c ? c.v : null;
    if (kind === 'pct') return pct(v);
    if (kind === 'money') return money(v);
    if (kind === 'x') return ratioX(v);
    return n0(v);
  }
  function dayLabel(id, opts) { return new Date(id + 'T12:00:00Z').toLocaleDateString('en-GB', Object.assign({ day: 'numeric', month: 'short', timeZone: 'UTC' }, opts || {})); }
  function ago(iso) {
    var s = (Date.now() - Date.parse(iso)) / 1000;
    if (s < 60) return 'just now';
    if (s < 3600) return Math.round(s / 60) + ' min ago';
    if (s < 86400) return Math.round(s / 3600) + ' h ago';
    return Math.round(s / 86400) + ' days ago';
  }
  var CC = { '1': 'US and Canada', '7': 'Russia', '20': 'Egypt', '27': 'South Africa', '30': 'Greece', '31': 'Netherlands', '32': 'Belgium', '33': 'France', '34': 'Spain', '39': 'Italy', '41': 'Switzerland', '43': 'Austria', '44': 'United Kingdom', '45': 'Denmark', '46': 'Sweden', '47': 'Norway', '48': 'Poland', '49': 'Germany', '52': 'Mexico', '55': 'Brazil', '60': 'Malaysia', '61': 'Australia', '62': 'Indonesia', '63': 'Philippines', '64': 'New Zealand', '65': 'Singapore', '81': 'Japan', '82': 'South Korea', '86': 'China', '90': 'Turkey', '91': 'India', '92': 'Pakistan', '94': 'Sri Lanka', '212': 'Morocco', '233': 'Ghana', '234': 'Nigeria', '254': 'Kenya', '351': 'Portugal', '353': 'Ireland', '358': 'Finland', '852': 'Hong Kong', '880': 'Bangladesh', '966': 'Saudi Arabia', '971': 'UAE', '972': 'Israel', '974': 'Qatar' };
  var UTM = { calendar: 'Calendar invites', linkedin: 'LinkedIn', whatsapp: 'WhatsApp', email: 'Email', facebook: 'Facebook', '(no utm)': 'No tracking tag' };

  // ---------------- state ----------------
  var VIEWS = [
    { id: 'overview', label: 'Overview' },
    { id: 'acquisition', label: 'Acquisition' },
    { id: 'attendance', label: 'Attendance' },
    { id: 'nurture', label: 'Nurture' },
    { id: 'commercial', label: 'Commercial' },
    { id: 'sessions', label: 'Sessions' },
    { id: 'health', label: 'Data health', sep: true },
    { id: 'settings', label: 'Settings' },
  ];
  var state = { funnels: [], funnel: null, model: null, session: 'all', view: 'overview', busy: false, settings: null };

  function readHash() {
    var h = location.hash.replace(/^#\/?/, '');
    var parts = h.split('?');
    var q = new URLSearchParams(parts[1] || '');
    var v = parts[0] || 'overview';
    if (VIEWS.some(function (x) { return x.id === v; })) state.view = v;
    if (q.get('f')) state.funnel = q.get('f');
    if (q.get('s')) state.session = q.get('s');
  }
  function writeHash() {
    var h = '#/' + state.view + '?f=' + encodeURIComponent(state.funnel || '') + '&s=' + encodeURIComponent(state.session);
    if (location.hash !== h) history.replaceState(null, '', h);
  }

  async function api(path, opts) {
    var r = await fetch(path, Object.assign({ credentials: 'same-origin', headers: { 'content-type': 'application/json' } }, opts || {}));
    if (r.status === 401) { location.replace('/'); throw new Error('signed out'); }
    var d = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
    return d;
  }

  // ---------------- tooltip ----------------
  var tipEl = document.getElementById('tip');
  function showTip(evt, build) {
    tipEl.textContent = '';
    build(tipEl);
    tipEl.hidden = false;
    var x = evt.clientX, y = evt.clientY;
    if (evt.type === 'focus' || x === undefined) { var r = evt.target.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top; }
    var w = tipEl.offsetWidth, h = tipEl.offsetHeight;
    var left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 14));
    var top = y - h - 12 < 8 ? y + 16 : y - h - 12;
    tipEl.style.left = left + 'px';
    tipEl.style.top = top + 'px';
  }
  function hideTip() { tipEl.hidden = true; }
  function hover(node, build) {
    node.addEventListener('pointermove', function (e) { showTip(e, build); });
    node.addEventListener('pointerleave', hideTip);
    node.addEventListener('focus', function (e) { showTip(e, build); });
    node.addEventListener('blur', hideTip);
  }

  // ---------------- building blocks ----------------
  function dict(key) { return (state.model && state.model.dictionary[key]) || null; }
  var PROV = { LIVE: 'Live', DERIVED: 'Calculated', OPERATOR: 'Entered', MISSING: 'Unavailable' };

  function tile(key, cell, opts) {
    opts = opts || {};
    var d = dict(key);
    var label = opts.label || (d ? d.label : key);
    var val = fmtCell(cell, opts.kind);
    var na = !cell || cell.v === null;
    var foot = el('div', { class: 't-foot' },
      el('span', { class: 'prov ' + (cell ? cell.k : 'MISSING'), text: PROV[cell ? cell.k : 'MISSING'] }),
      cell && cell.conflict ? el('span', { class: 'flag conf', text: '⚠ Sources disagree' }) : null,
      cell && cell.immature ? el('span', { class: 'flag imm', text: '◷ So far' }) : null,
      cell && cell.floor && !na ? el('span', { class: 'flag floor', text: 'at least' }) : null,
      cell && cell.ceiling && !na ? el('span', { class: 'flag floor', text: 'at most' }) : null,
      opts.sub ? el('span', { text: opts.sub }) : null);
    var t = el('div', { class: 'tile', tabindex: '0', role: 'group', 'aria-label': label + ': ' + (na ? 'unavailable' : val) },
      el('div', { class: 't-label', text: label }),
      el('div', { class: 't-value' + (na ? ' na' : ''), text: val }),
      foot);
    hover(t, function (tp) {
      tp.appendChild(el('div', { class: 'tv', text: na ? 'Unavailable, not zero' : val }));
      if (d) tp.appendChild(el('div', { style: 'margin-top:4px', text: d.def }));
      if (cell && cell.s) tp.appendChild(el('div', { class: 'muted', style: 'margin-top:6px;font-size:12px', text: 'Source: ' + cell.s }));
      if (cell && cell.why) tp.appendChild(el('div', { style: 'margin-top:6px;font-size:12px', text: cell.why }));
      if (cell && cell.alts) cell.alts.forEach(function (a) { tp.appendChild(el('div', { class: 'tr' }, el('span', { text: a[0] }), el('b', { class: 'num', text: a[1] === null ? NA : fmtCell({ v: a[1] }, opts.kind) }))); });
      if (cell && cell.immature) tp.appendChild(el('div', { style: 'margin-top:6px;font-size:12px', text: 'Recorded so far. Sales from a session keep arriving for ' + state.model.funnel.maturity_days + ' days.' }));
    });
    return t;
  }

  function card(title, sub, body, extra) {
    return el('section', { class: 'card ' + ((extra && extra.cls) || '') },
      el('div', { class: 'ch' }, el('div', null, el('h2', { text: title }), sub ? el('div', { class: 'sub', text: sub }) : null), extra && extra.right ? extra.right : null),
      body);
  }
  function empty(title, body) { return el('div', { class: 'empty' }, el('b', { text: title }), el('span', { text: body })); }

  function funnelChart(stages) {
    var vals = stages.map(function (s) { return s.cell && isNum(s.cell.v) ? s.cell.v : null; });
    var max = Math.max.apply(null, vals.filter(isNum).concat([1]));
    var box = el('div', { class: 'funnel', role: 'list' });
    stages.forEach(function (s, i) {
      var v = vals[i];
      var w = v === null ? 0 : Math.max(0.8, Math.sqrt(v / max) * 100); // square-root scale keeps small late stages visible
      var known = v !== null;
      var fill = el('div', { class: 'fill' + (known ? '' : ' ghost'), style: 'width:' + w + '%' });
      var label = known ? n0(v) : 'Not connected';
      var inside = known && w > 22;
      var bar = el('div', { class: 'fbar' }, fill, el('div', { class: 'fv ' + (inside ? 'in' : 'out'), style: inside ? 'left:0' : 'left:' + (known ? w : 0) + '%', text: label }));
      var conv = isNum(s.conv) ? pct(s.conv) : NA;
      var from = s.from ? stages.find(function (x) { return x.key === s.from; }) : null;
      var row = el('div', { class: 'fstage', role: 'listitem', tabindex: '0' },
        el('div', { class: 'fl', text: s.label }, s.cell && s.cell.immature ? el('small', { text: 'so far' }) : null),
        bar,
        el('div', { class: 'fc' }, i === 0 ? el('span', { class: 'muted', text: 'start' }) : [el('b', { text: conv }), el('span', { text: from ? 'of ' + from.label.toLowerCase() : '' })]));
      hover(row, function (tp) {
        tp.appendChild(el('div', { class: 'tv', text: known ? n0(v) + ' ' + s.label.toLowerCase() : s.label + ': unavailable' }));
        if (isNum(s.conv) && from) tp.appendChild(el('div', { text: pct(s.conv) + ' of ' + n0(from.cell.v) + ' ' + from.label.toLowerCase() }));
        if (s.cell && s.cell.s) tp.appendChild(el('div', { class: 'muted', style: 'margin-top:4px;font-size:12px', text: s.cell.s }));
        if (s.cell && s.cell.why) tp.appendChild(el('div', { style: 'margin-top:4px;font-size:12px', text: s.cell.why }));
      });
      box.appendChild(row);
    });
    return box;
  }

  function hbars(rows, opts) {
    opts = opts || {};
    if (!rows.length) return empty(opts.emptyTitle || 'Nothing recorded yet', opts.emptyBody || '');
    var max = Math.max.apply(null, rows.map(function (r) { return r.n; }).concat([1]));
    return el('div', { class: 'hbars', role: 'list' }, rows.map(function (r) {
      var row = el('div', { class: 'hbar', role: 'listitem', tabindex: '0' },
        el('div', { class: 'hl', text: r.label, title: r.label }),
        el('div', { class: 'ht' }, el('div', { class: 'hf ' + (opts.series || ''), style: 'width:' + (r.n > 0 ? Math.max(1, (r.n / max) * 100) : 0) + '%' })),
        el('div', { class: 'hv', text: opts.fmt ? opts.fmt(r.n) : n0(r.n) }));
      hover(row, function (tp) {
        tp.appendChild(el('div', { class: 'tv', text: opts.fmt ? opts.fmt(r.n) : n0(r.n) }));
        tp.appendChild(el('div', { text: r.label }));
        if (opts.total) tp.appendChild(el('div', { class: 'muted', text: pct(r.n / opts.total) + ' of ' + n0(opts.total) }));
        if (r.extra) tp.appendChild(el('div', { class: 'muted', text: r.extra }));
      });
      return row;
    }));
  }

  // Column chart over days, single or two series, with a crosshair tooltip.
  function columns(points, series, opts) {
    opts = opts || {};
    var narrow = window.innerWidth < 700;
    var W = narrow ? 360 : (opts.half ? 480 : 760), H = narrow ? Math.round((opts.h || 220) * 0.8) : (opts.h || 220), L = 34, R = 8, T = 10, B = 26;
    var max = 1;
    points.forEach(function (p) { series.forEach(function (s) { if (isNum(p[s.key])) max = Math.max(max, p[s.key]); }); });
    var step = niceStep(max);
    var top = Math.ceil(max / step) * step;
    var iw = W - L - R, ih = H - T - B;
    var bw = iw / Math.max(points.length, 1);
    var barW = Math.min(24, Math.max(3, (bw - 4) / series.length - 2));
    var root = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': opts.label || 'chart' });
    for (var g = 0; g <= top; g += step) {
      var y = T + ih - (g / top) * ih;
      root.appendChild(svg('line', { x1: L, x2: W - R, y1: y, y2: y, stroke: g === 0 ? 'var(--axis)' : 'var(--grid)', 'stroke-width': 1 }));
      root.appendChild(svg('text', { x: L - 6, y: y + 3.5, 'text-anchor': 'end', text: g >= 1000 ? (g / 1000) + 'K' : g }));
    }
    var every = Math.ceil(points.length / (narrow ? 5 : 10));
    points.forEach(function (p, i) {
      var x0 = L + i * bw + (bw - (barW + 2) * series.length) / 2;
      series.forEach(function (s, j) {
        var v = p[s.key];
        if (!isNum(v) || v <= 0) return;
        var h = (v / top) * ih;
        var x = x0 + j * (barW + 2), y = T + ih - h;
        var r = Math.min(4, barW / 2, h);
        root.appendChild(svg('path', { d: 'M' + x + ',' + (T + ih) + 'V' + (y + r) + 'q0,-' + r + ' ' + r + ',-' + r + 'h' + (barW - 2 * r) + 'q' + r + ',0 ' + r + ',' + r + 'V' + (T + ih) + 'Z', fill: s.color }));
      });
      if (i % every === 0) root.appendChild(svg('text', { x: L + i * bw + bw / 2, y: H - 8, 'text-anchor': 'middle', text: opts.xfmt ? opts.xfmt(p) : dayLabel(p.day) }));
    });
    var cross = svg('rect', { x: 0, y: T, width: bw, height: ih, fill: 'var(--accent)', opacity: 0, rx: 4 });
    root.appendChild(cross);
    var hit = svg('rect', { x: L, y: T, width: iw, height: ih, fill: 'transparent', tabindex: '0' });
    root.appendChild(hit);
    var wrap = el('div', { class: 'chart' }, root);
    function at(e) {
      var rect = root.getBoundingClientRect();
      var x = ((e.clientX - rect.left) / rect.width) * W;
      var i = Math.max(0, Math.min(points.length - 1, Math.floor((x - L) / bw)));
      return i;
    }
    hit.addEventListener('pointermove', function (e) {
      var i = at(e), p = points[i];
      cross.setAttribute('x', L + i * bw); cross.setAttribute('opacity', 0.08);
      showTip(e, function (tp) {
        tp.appendChild(el('div', { style: 'font-weight:600;margin-bottom:2px', text: opts.xfull ? opts.xfull(p) : dayLabel(p.day, { weekday: 'short' }) }));
        series.forEach(function (s) { tp.appendChild(el('div', { class: 'tr' }, el('span', null, el('i', { class: 'key', style: 'background:' + s.color }), s.label), el('b', { class: 'num', text: isNum(p[s.key]) ? n0(p[s.key]) : NA }))); });
      });
    });
    hit.addEventListener('pointerleave', function () { cross.setAttribute('opacity', 0); hideTip(); });
    var out = el('div', null);
    if (series.length > 1) out.appendChild(el('div', { class: 'legend', style: 'margin-bottom:10px' }, series.map(function (s) { return el('span', null, el('i', { style: 'background:' + s.color }), s.label); })));
    out.appendChild(wrap);
    return out;
  }
  function niceStep(max) {
    var raw = max / 4, mag = Math.pow(10, Math.floor(Math.log10(raw || 1)));
    var n = raw / mag;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * mag;
  }
  function spark(points, key) {
    var W = 300, H = 64;
    var run = 0;
    var vals = points.map(function (p) { run += p[key] || 0; return run; }); // running total
    var max = Math.max.apply(null, vals.concat([1]));
    var s = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, preserveAspectRatio: 'none', class: 'spark', 'aria-hidden': 'true' });
    if (vals.length < 2) return s;
    var pts = vals.map(function (v, i) { return [(i / (vals.length - 1)) * W, H - 4 - (v / max) * (H - 10)]; });
    var d = 'M' + pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join('L');
    s.appendChild(svg('path', { d: d + 'L' + W + ',' + H + 'L0,' + H + 'Z', fill: 'var(--accent)', opacity: 0.1 }));
    s.appendChild(svg('path', { d: d, fill: 'none', stroke: 'var(--accent)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', 'vector-effect': 'non-scaling-stroke' }));
    var last = pts[pts.length - 1];
    s.appendChild(svg('circle', { cx: last[0], cy: last[1], r: 4, fill: 'var(--accent)', stroke: 'var(--surface)', 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke' }));
    return s;
  }
  // One whole split into parts (tall segmented bar): legend + direct labels where they fit.
  function segbar(parts) {
    var total = parts.reduce(function (a, p) { return a + (p.n || 0); }, 0);
    if (!total) return empty('Nothing recorded yet', '');
    var bar = el('div', { class: 'seg', role: 'img', 'aria-label': parts.map(function (p) { return p.label + ' ' + p.n; }).join(', ') });
    parts.forEach(function (p) {
      if (!p.n) return;
      var share = p.n / total;
      var b = el('div', { style: 'flex:' + p.n + ';background:' + p.color, tabindex: '0' }, share > 0.12 ? pct(share, 0) : '');
      hover(b, function (tp) { tp.appendChild(el('div', { class: 'tv', text: n0(p.n) })); tp.appendChild(el('div', { text: p.label + ' · ' + pct(share) })); });
      bar.appendChild(b);
    });
    return el('div', null, bar, el('div', { class: 'legend', style: 'margin-top:10px' }, parts.map(function (p) { return el('span', null, el('i', { style: 'background:' + p.color }), p.label + ' ' + n0(p.n)); })));
  }

  // ---------------- views ----------------
  function V() { return state.model.views[state.session] || state.model.views.all; }
  function sessLabel() {
    if (state.session === 'all') return 'all sessions';
    var s = state.model.sessions.find(function (x) { return x.id === state.session; });
    return s ? dayLabel(s.id, { weekday: 'long', year: 'numeric' }) + ' session' : state.session;
  }

  function header(title, sub, right) {
    return el('div', { class: 'head' }, el('div', null, el('h1', { text: title }), sub ? el('p', { text: sub }) : null), right || null);
  }

  function banners() {
    var m = state.model, out = [];
    if (m.degraded && m.degraded.length) out.push(el('div', { class: 'banner crit', role: 'status' }, el('b', { text: 'Partial refresh.' }), el('span', { text: ' ' + m.degraded.join(' and ') + ' did not answer on the last run' + (m.kept_from ? ', so figures from ' + ago(m.kept_from) + ' are still shown.' : '.') })));
    var v = V();
    if (state.session !== 'all') {
      var s = m.sessions.find(function (x) { return x.id === state.session; });
      if (s && s.status === 'upcoming') out.push(el('div', { class: 'banner info' }, el('b', { text: 'Upcoming session.' }), el('span', { text: ' Registrations are live; attendance and sales fill in after it airs.' })));
      else if (s && !s.mature) out.push(el('div', { class: 'banner warn' }, el('b', { text: 'Still maturing.' }), el('span', { text: ' This session aired ' + (s.age_days === 1 ? '1 day' : s.age_days + ' days') + ' ago. Sales are recorded so far and keep arriving for ' + m.funnel.maturity_days + ' days.' })));
    }
    if (v.confidence < 70) out.push(el('div', { class: 'banner warn' }, el('b', { text: 'Data confidence ' + v.confidence + '/100.' }), el('span', { text: ' Some figures here are unavailable or disagree between sources. Read them with care; Data health has the detail.' })));
    return out;
  }

  function viewOverview() {
    var v = V(), k = v.k, m = state.model;
    var trends = m.trends || [];
    var heroCell = k.registered;
    var hero = el('section', { class: 'hero' }, el('div', { class: 'hero-in' },
      el('div', null,
        el('div', { class: 'k-label' }, 'Registered', el('span', { class: 'prov ' + heroCell.k, text: PROV[heroCell.k] }), heroCell.conflict ? el('span', { class: 'flag conf', text: '⚠ Sources disagree' }) : null),
        el('div', { class: 'k-value num', text: n0(heroCell.v) }),
        el('div', { class: 'k-foot' }, el('b', { text: n0(k.self_registered.v) }), ' on our page · ', el('b', { text: n0(k.other_registered.v) }), ' through WebinarJam · ', sessLabel()),
        state.session === 'all' && trends.length > 1 ? [spark(trends, 'registered'), el('div', { class: 'muted', style: 'font-size:12px;margin-top:4px', text: 'Running total since ' + dayLabel(trends[0].day) })] : null),
      el('div', { class: 'tiles' },
        tile('attended', k.attended, { sub: isNum(k.attendance_rate.v) ? pct(k.attendance_rate.v) + ' show-up' : null }),
        tile('offer_clicks', k.offer_clicks),
        tile('calls_booked', k.calls_booked),
        tile('customers', k.customers),
        tile('revenue', k.revenue, { kind: 'money' }),
        tile('cost_per_registrant', k.cost_per_registrant, { kind: 'money' }))));

    var funnelCard = card('Funnel', 'People at each stage, ' + sessLabel() + '. Bars use a square-root scale so late stages stay visible; percentages are exact.', funnelChart(v.stages), { right: el('span', { class: 'chip', text: 'Confidence ' + v.confidence + '/100' }) });

    var ins = (m.insights || []).slice(0, 6);
    var insCard = card('What the numbers say', 'Computed from this funnel’s data. Each line names the figure it rests on.', ins.length ? el('div', { class: 'ins' }, ins.map(insightRow)) : empty('Nothing stands out yet', ''));

    var trendCard = card('Daily activity', 'Registrations and human offer clicks per day (' + (m.funnel.tz || 'UTC') + ').',
      trends.length ? columns(trends.slice(-45), [{ key: 'registered', label: 'Registrations', color: 'var(--s1)' }, { key: 'clicks', label: 'Offer clicks', color: 'var(--s2)' }], { label: 'Registrations and offer clicks per day' }) : empty('No daily data yet', ''));

    var comp = m.compare || [];
    var sessCard = card('Sessions', 'Registered and attended by session.', comp.length ? columns(comp.map(function (c) { return { day: c.id, registered: c.registered, attended: c.attended }; }), [{ key: 'registered', label: 'Registered', color: 'var(--s1)' }, { key: 'attended', label: 'Attended live', color: 'var(--s2)' }], { h: 200, half: true, xfmt: function (p) { return dayLabel(p.day); }, xfull: function (p) { return dayLabel(p.day, { weekday: 'long', year: 'numeric' }); }, label: 'Registered and attended by session' }) : empty('No sessions yet', ''));

    return [header(m.funnel.name, m.funnel.description), banners(), hero,
      el('div', { class: 'grid g-12', style: 'align-items:start' },
        el('div', { class: 'span-7 grid' }, funnelCard, trendCard),
        el('div', { class: 'span-5 grid' }, insCard, sessCard))];
  }
  function insightRow(i) {
    var mark = { good: '✓', warning: '!', critical: '×', info: 'i', setup: '+' }[i.level] || 'i';
    var word = { good: 'Good', warning: 'Watch', critical: 'Problem', info: 'Note', setup: 'Set up' }[i.level];
    return el('div', { class: 'insight ' + i.level }, el('div', { class: 'ic', 'aria-label': word, text: mark }),
      el('div', null, el('div', { class: 'it' }, el('span', { class: 'ia', text: word + ' · ' + i.area }), i.title), el('div', { class: 'ib', text: i.body })));
  }

  function viewAcquisition() {
    var v = V(), k = v.k, b = v.breakdown, m = state.model;
    var inviteTiles = el('div', { class: 'kv' }, tile('invited', k.invited), tile('rsvp_yes', k.rsvp_yes, { label: 'RSVP yes' }), tile('rsvp_maybe', k.rsvp_maybe, { label: 'RSVP maybe' }), tile('rsvp_no', k.rsvp_no, { label: 'RSVP no' }), tile('rsvp_waiting', k.rsvp_waiting, { label: 'No reply yet' }), tile('registration_efficiency', k.registration_efficiency, { kind: 'pct' }));
    var tantraSrc = m.sources.find(function (s) { return s.id === 'tantra'; });
    var invites = card('Calendar invites (Tantra app)', 'Invites sent and RSVPs from Tantra calendar campaigns tagged for this funnel.', el('div', null,
      tantraSrc && tantraSrc.status !== 'ok' ? el('div', { class: 'banner info', style: 'margin-bottom:14px' }, el('b', { text: tantraSrc.status === 'error' ? 'The Tantra app did not answer.' : 'Not connected yet.' }), el('span', { text: ' ' + (tantraSrc.status === 'error' ? tantraSrc.detail : 'Add a Tantra app API key under Settings to fill in invites and RSVPs. Open and click counts do not exist in the app, so they will never show here.') }), tantraSrc.status !== 'error' ? el('button', { class: 'btn', style: 'margin-left:auto', onclick: function () { go('settings'); }, text: 'Open Settings' }) : null) : null,
      inviteTiles));
    var regSplit = card('How people registered', 'Our page versus WebinarJam’s own form or hand entry.', segbar([{ label: 'Our page', n: k.self_registered.v || 0, color: 'var(--s1)' }, { label: 'WebinarJam directly', n: k.other_registered.v || 0, color: 'var(--s2)' }]));
    var utm = card('Registrants by source', 'Tracking tag on the registration (utm_source). Untagged links show as “No tracking tag”.', hbars(b.utm_source.map(function (r) { return { label: UTM[r.label] || r.label, n: r.n }; }), { total: k.registered.v }));
    var geo = card('Registrants by country', 'From the phone country code people gave WebinarJam.', hbars(b.country_code.map(function (r) { return { label: (CC[r.label] || '+' + r.label), n: r.n }; }), { total: k.registered.v, series: 's2', emptyBody: 'No phone numbers recorded.' }));
    var lead = card('When people registered', 'Days between registering and the session start.', hbars(b.lead_time, { total: k.registered.v, series: 's3' }));
    var con = m.content || {};
    var contentBody;
    if (con.status === 'ok') {
      var c = con.cells;
      contentBody = el('div', null,
        el('div', { class: 'kv' }, ['posts', 'impressions', 'reach', 'clicks', 'reactions', 'comments', 'shares', 'engagement_rate'].map(function (x) { return tile(x, c[x], { label: x.replace('_', ' ').replace(/^./, function (s) { return s.toUpperCase(); }), kind: x === 'engagement_rate' ? 'pct' : null }); })),
        con.linkedin ? el('div', { style: 'margin-top:14px' }, el('h3', { text: 'LinkedIn (engine batches)' }), el('div', { class: 'kv', style: 'margin-top:8px' }, ['posts', 'impressions', 'clicks', 'reactions', 'comments', 'shares'].map(function (x) { return tile(x, con.linkedin[x], { label: x.replace(/^./, function (s) { return s.toUpperCase(); }) }); }))) : null,
        el('p', { class: 'muted', style: 'font-size:12.5px;margin:12px 0 0', text: 'Content totals cover the whole funnel period, not one session. The engine has no webinar or UTM field yet, so posts are not tied to registrations.' }));
    } else {
      contentBody = empty(con.status === 'error' ? 'The content engine did not answer' : 'Content engine not connected', con.status === 'error' ? (con.error || '') : 'Add a workspace API token under Settings to show reach, clicks and engagement from organic posts.');
    }
    var content = card('Organic content (content engine)', 'Posts, reach and engagement that feed this funnel.', contentBody);
    return [header('Acquisition', 'How people reached the webinar, ' + sessLabel() + '.'), banners(), invites,
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, regSplit), el('div', { class: 'span-6' }, utm)),
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, geo), el('div', { class: 'span-6' }, lead)), content];
  }

  function viewAttendance() {
    var v = V(), k = v.k;
    var tiles = el('div', { class: 'tiles' }, tile('registered', k.registered), tile('attended', k.attended), tile('attendance_rate', k.attendance_rate, { kind: 'pct', sub: 'plan ' + pct(state.model.funnel.targets.attendance_rate, 0) }), tile('missed', k.missed), tile('left_early', k.left_early), tile('survey', k.survey), tile('replay', k.replay, { label: 'Watched replay' }));
    var split = card('What happened to registrants', 'Every registrant of aired sessions lands in one of these.', isNum(k.attended.v) ? segbar([
      { label: 'Stayed past the cutoff', n: k.stayed.v || 0, color: 'var(--s4)' },
      { label: 'Attended, left early', n: k.left_early.v || 0, color: 'var(--s2)' },
      { label: 'Missed', n: k.missed.v || 0, color: 'var(--s3)' },
    ]) : empty('No session has aired yet', 'Attendance fills in after the first session.'));
    var regions = card('Registrants by time zone region', 'From the browser time zone on our registration page.', hbars(V().breakdown.region, { total: k.self_registered.v, emptyBody: 'Only page sign-ups carry a time zone.' }));
    var fit = card('Fit tier from the survey', 'The tier the thank-you survey assigned.', hbars(V().breakdown.fit_tier, { total: k.survey.v, series: 's4', emptyBody: 'No surveys completed yet.' }));
    return [header('Attendance', 'Who showed up, ' + sessLabel() + '.'), banners(), tiles, split, el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, regions), el('div', { class: 'span-6' }, fit))];
  }

  function viewNurture() {
    var v = V(), k = v.k, b = v.breakdown;
    var wa = card('WhatsApp', 'Messages to registrants from the Tantra WhatsApp sender.', el('div', null,
      el('div', { class: 'kv' }, tile('wa_sent', k.wa_sent), tile('wa_delivery_rate', k.wa_delivery_rate, { kind: 'pct', sub: n0(k.wa_delivered.v) + ' delivered' }), tile('wa_read_rate', k.wa_read_rate, { kind: 'pct', sub: n0(k.wa_read.v) + ' read' }), tile('wa_failed', k.wa_failed, { label: 'Not delivered' }), tile('wa_replies', k.wa_replies, { label: 'Replies received' })),
      el('div', { style: 'margin-top:16px' }, segbar([{ label: 'Read', n: k.wa_read.v || 0, color: 'var(--s1)' }, { label: 'Delivered, not read', n: Math.max(0, (k.wa_delivered.v || 0) - (k.wa_read.v || 0)), color: 'var(--s2)' }, { label: 'Not delivered', n: k.wa_failed.v || 0, color: 'var(--s3)' }, { label: 'Sent, no status yet', n: Math.max(0, (k.wa_sent.v || 0) - (k.wa_delivered.v || 0) - (k.wa_failed.v || 0)), color: 'var(--s4)' }]))));
    var other = card('SMS, AI calls and opt-outs', null, el('div', { class: 'kv' }, tile('sms_sent', k.sms_sent, { label: 'SMS sent' }), tile('sms_delivered', k.sms_delivered, { label: 'SMS delivered' }), tile('sms_failed', k.sms_failed, { label: 'SMS not delivered' }), tile('ai_calls', k.ai_calls, { label: 'AI calls placed' }), tile('ai_answered', k.ai_answered, { label: 'AI calls answered' }), tile('optouts', k.optouts, { label: 'Opted out' })));
    var seq = card('Sequence enrolments', 'Registrants of these sessions enrolled in each CRM sequence.', hbars(b.sequences, { series: 's2' }));
    return [header('Nurture', 'Reminders and follow-up, ' + sessLabel() + '.'), banners(), wa, el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, other), el('div', { class: 'span-6' }, seq))];
  }

  function viewCommercial() {
    var v = V(), k = v.k, b = v.breakdown, m = state.model;
    var tiles = el('div', { class: 'tiles' }, tile('offer_clicks', k.offer_clicks), tile('calls_booked', k.calls_booked), tile('calls_showed', k.calls_showed), tile('open_deals', k.open_deals, { label: 'Open Enterprise deals' }), tile('pipeline_value', k.pipeline_value, { kind: 'money' }), tile('customers', k.customers));
    var buys = card('Purchases', 'Every offer this funnel sells.', el('div', { class: 'kv' }, tile('enterprise_customers', k.enterprise_customers, { sub: money(m.funnel.products.enterprise.price) }), tile('os_buyers', k.os_buyers, { sub: money(m.funnel.products.os.price) }), tile('pro_trials', k.pro_trials, { label: 'Tantra Pro trials' }), tile('pro_paid', k.pro_paid, { label: 'Tantra Pro paid' }), tile('cash_received', k.cash_received, { label: 'Dodo payments', kind: 'money' }), tile('revenue', k.revenue, { kind: 'money' })));
    var clicks = card('Offer clicks by link', 'Human clicks on go.usetantra.com links. Hover for all clicks including link previews.', hbars(b.placements.map(function (p) { return { label: p.placement.replace(/[_-]/g, ' '), n: p.human, extra: n0(p.all) + ' clicks including previews and bots' }; }).filter(function (r, i) { return r.n > 0 || i < 8; }), { emptyBody: 'No tracked link clicks in these sessions.' }));
    var bt = card('Bookings by page', 'Active bookings and cancellations. Test sources and internal addresses excluded.', b.booking_types.length ? el('div', { class: 'tbl-wrap' }, el('table', null, el('thead', null, el('tr', null, el('th', { text: 'Booking page' }), el('th', { class: 'n', text: 'Active' }), el('th', { class: 'n', text: 'Cancelled' }))), el('tbody', null, b.booking_types.map(function (t) { return el('tr', null, el('td', { text: t.label }), el('td', { class: 'n', text: n0(t.booked) }), el('td', { class: 'n', text: n0(t.cancelled) })); })))) : empty('No bookings yet', ''));
    var costs = card('Cost and return', k.total_cost.floor ? 'Only messaging spend is known, so every cost figure here is a floor (“at least”).' : 'Messaging spend plus costs entered in Settings.', el('div', { class: 'kv' }, tile('messaging_spend', k.messaging_spend, { label: 'Messaging spend', kind: 'money' }), tile('manual_costs', k.manual_costs, { label: 'Entered costs', kind: 'money' }), tile('total_cost', k.total_cost, { kind: 'money' }), tile('cost_per_registrant', k.cost_per_registrant, { kind: 'money' }), tile('cost_per_attendee', k.cost_per_attendee, { kind: 'money' }), tile('roas', k.roas, { kind: 'x' })));
    var parts = (b.revenue_parts || []).filter(function (p) { return p[1] > 0; });
    var rev = card('Revenue by offer', 'Recorded so far for sessions under ' + m.funnel.maturity_days + ' days old.', parts.length ? hbars(parts.map(function (p) { return { label: p[0], n: p[1] }; }), { fmt: money, series: 's4' }) : empty('No revenue recorded yet', 'Enterprise deals won, RevOps OS purchases and Dodo payments appear here as they land.'));
    return [header('Commercial', 'From offer to cash, ' + sessLabel() + '.'), banners(), tiles, buys,
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, clicks), el('div', { class: 'span-6' }, bt)),
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, costs), el('div', { class: 'span-6' }, rev))];
  }

  function viewSessions() {
    var m = state.model;
    var rows = m.compare.slice().reverse();
    var tbl = el('div', { class: 'tbl-wrap' }, el('table', null,
      el('thead', null, el('tr', null, ['Session', 'Status', 'Registered', 'Attended', 'Show-up', 'Offer clicks', 'Calls booked', 'Customers', 'Revenue', 'Cost', 'Score', 'Confidence'].map(function (h, i) { return el('th', { class: i > 1 ? 'n' : null, text: h }); }))),
      el('tbody', null, rows.map(function (r) {
        var sc = m.views[r.id].score;
        return el('tr', { style: 'cursor:pointer', tabindex: '0', onclick: function () { setSession(r.id); go('overview'); }, onkeydown: function (e) { if (e.key === 'Enter') { setSession(r.id); go('overview'); } } },
          el('td', { text: dayLabel(r.id, { weekday: 'short', year: 'numeric' }) }),
          el('td', null, el('span', { class: 'chip dot ' + r.status, text: r.status === 'aired' ? (r.mature ? 'Aired' : 'Aired · maturing') : r.status === 'live' ? 'Live now' : 'Upcoming' })),
          el('td', { class: 'n', text: n0(r.registered) }), el('td', { class: 'n', text: n0(r.attended) }), el('td', { class: 'n', text: pct(r.attendance_rate) }),
          el('td', { class: 'n', text: n0(r.clicks) }), el('td', { class: 'n', text: n0(r.booked) }), el('td', { class: 'n', text: n0(r.customers) }),
          el('td', { class: 'n', text: money(r.revenue) }), el('td', { class: 'n', text: money(r.cost) }),
          el('td', { class: 'n', title: sc && sc.why ? sc.why : null, text: sc && isNum(sc.v) ? sc.v + (sc.provisional ? '*' : '') : NA }),
          el('td', { class: 'n', text: r.confidence + '/100' }));
      }))));
    var notes = card('How scores work', null, el('p', { style: 'margin:0;color:var(--ink-2);font-size:14px', text: 'Each aired session is scored 0 to 100 against this funnel’s own other sessions, never an outside benchmark: registration 20%, attendance 20%, engagement 15%, outreach efficiency 10%, commercial conversion 20%, revenue 15%. A dimension with no data is left out and the weights are rebased; the score is then marked * (provisional). Commercial dimensions wait until a session is ' + m.funnel.maturity_days + ' days old. Scores start once two sessions have aired.' }));
    return [header('Sessions', 'Every session of this funnel side by side. Select a row to open it.'), card('All sessions', null, tbl, { cls: '' }), notes];
  }

  function viewHealth() {
    var m = state.model;
    var src = card('Sources', 'Each source is read on every refresh (every 15 minutes). A failed core source keeps the last good numbers on screen.', el('div', { class: 'tbl-wrap' }, el('table', null,
      el('thead', null, el('tr', null, el('th', { text: 'Source' }), el('th', { text: 'Status' }), el('th', { text: 'Detail' }), el('th', { class: 'n', text: 'Time' }))),
      el('tbody', null, m.sources.map(function (s) {
        var cls = s.status === 'ok' ? 'live' : s.status === 'not_connected' ? 'upcoming' : 'crit';
        var word = s.status === 'ok' ? 'Connected' : s.status === 'not_connected' ? 'Not connected' : 'Failed';
        return el('tr', null, el('td', { text: s.name }), el('td', null, el('span', { class: 'chip dot ' + cls, text: word })), el('td', { style: 'white-space:normal', text: s.detail || '' }), el('td', { class: 'n', text: s.ms + ' ms' }));
      })))));
    var v = V();
    var conf = card('Data confidence', 'Separate from performance: how complete and consistent the figures are.', el('div', null,
      el('div', { style: 'font-size:40px;font-weight:700', class: 'num', text: v.confidence + '/100' }),
      el('p', { class: 'muted', style: 'margin:6px 0 0;font-size:13.5px', text: '100 × (1 − unavailable ÷ expected) − 10 per conflict. Expected: registered, attended, invited, offer clicks, calls booked, revenue, cost.' }),
      v.conflicts.length ? el('p', { style: 'margin:10px 0 0', text: 'Disagreeing sources: ' + v.conflicts.join(', ') }) : el('p', { class: 'ok-msg', style: 'margin:10px 0 0', text: 'No source disagreements.' })));
    var notes = card('Notes from the last build', null, (m.notes || []).length ? el('ul', { style: 'margin:0;padding-left:18px;color:var(--ink-2);font-size:14px' }, m.notes.map(function (n) { return el('li', { text: n }); })) : empty('No notes', ''));
    var crmf = card('CRM funnel engine (cross-check)', 'The CRM’s own funnel definition counts entries since tracking was switched on, so it can trail the session counts.', m.crm_funnel && m.crm_funnel.length ? hbars(m.crm_funnel.map(function (s) { return { label: s.label, n: s.reached }; }), { series: 's2' }) : empty('No funnel definition found', ''));
    var defs = card('Definitions', 'What every figure means. The same text appears when you hover a figure.', el('dl', { class: 'def', style: 'margin:0' }, Object.keys(m.dictionary).map(function (key) { var d = m.dictionary[key]; return [el('dt', { text: d.label }), el('dd', { text: d.def })]; })));
    var runs = el('div', { id: 'runs' }, empty('Loading run log…', ''));
    api('/api/runs?funnel=' + encodeURIComponent(state.funnel)).then(function (d) {
      runs.textContent = '';
      runs.appendChild(el('div', { class: 'tbl-wrap' }, el('table', null, el('thead', null, el('tr', null, el('th', { text: 'Started' }), el('th', { text: 'Result' }), el('th', { class: 'n', text: 'Took' }))), el('tbody', null, d.runs.map(function (r) { return el('tr', null, el('td', { text: new Date(r.started_at).toLocaleString('en-GB') }), el('td', null, el('span', { class: 'chip dot ' + (r.status === 'ok' ? 'live' : r.status === 'failed' ? 'crit' : 'warn'), text: r.status })), el('td', { class: 'n', text: (r.ms / 1000).toFixed(1) + ' s' })); })))));
    }).catch(function () { runs.textContent = 'Run log unavailable.'; });
    return [header('Data health', 'Where every number comes from and how fresh it is.'), src,
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, conf), el('div', { class: 'span-6' }, card('Recent refreshes', null, runs))),
      el('div', { class: 'grid g-12' }, el('div', { class: 'span-6' }, notes), el('div', { class: 'span-6' }, crmf)), defs];
  }

  // ---------------- settings ----------------
  function viewSettings() {
    var wrap = el('div', { style: 'display:contents' });
    var body = el('div', { class: 'grid', style: 'gap:16px' }, empty('Loading settings…', ''));
    api('/api/settings?funnel=' + encodeURIComponent(state.funnel)).then(function (d) { state.settings = d; body.textContent = ''; settingsBody(body, d); }).catch(function (e) { body.textContent = ''; body.appendChild(empty('Could not load settings', e.message)); });
    append(wrap, [header('Settings', 'Connections and the facts only people know: costs, targets and which campaigns belong to this funnel. Nothing here holds personal data.'), body]);
    return [wrap];
  }
  function settingsBody(body, d) {
    var c = d.connections, inp = d.inputs || {}, def = d.defaults;
    function secretField(key, placeholder, hint) {
      var meta = c[key];
      var input = el('input', { class: 'input', type: 'password', autocomplete: 'off', placeholder: meta.set ? 'Saved (ends in ' + meta.last4 + '). Paste a new key to replace it.' : placeholder, 'data-key': key });
      return el('div', { class: 'field' }, el('label', { text: meta.label }), input, el('div', { class: 'hint', text: hint }));
    }
    function urlField(key, placeholder) {
      var meta = c[key];
      return el('div', { class: 'field' }, el('label', { text: meta.label }), el('input', { class: 'input', type: 'url', placeholder: placeholder, value: meta.value || '', 'data-key': key }));
    }
    var connMsg = el('span');
    function testBtn(src) {
      var out = el('span');
      var b = el('button', { class: 'btn', type: 'button', text: 'Test connection', onclick: async function () {
        b.disabled = true; out.className = 'muted'; out.textContent = 'Testing…';
        try { var r = await api('/api/settings/test?funnel=' + encodeURIComponent(state.funnel) + '&source=' + src, { method: 'POST', body: '{}' }); out.className = r.ok ? 'ok-msg' : 'err-msg'; out.textContent = r.message; }
        catch (e) { out.className = 'err-msg'; out.textContent = e.message; }
        b.disabled = false;
      } });
      return el('div', { class: 'row' }, b, out);
    }
    var conn = card('Connections', 'Keys are encrypted before they are stored and never shown again. Registrations, WebinarJam and the CRM are connected inside Cloudflare and need nothing here.', el('form', { class: 'form', onsubmit: async function (e) {
      e.preventDefault();
      var payload = {};
      this.querySelectorAll('[data-key]').forEach(function (i) { payload[i.getAttribute('data-key')] = i.value.trim(); });
      connMsg.className = 'muted'; connMsg.textContent = 'Saving…';
      try { await api('/api/settings/connections?funnel=' + encodeURIComponent(state.funnel), { method: 'POST', body: JSON.stringify(payload) }); connMsg.className = 'ok-msg'; connMsg.textContent = 'Saved. Refresh the data to pull from the new connection.'; this.querySelectorAll('input[type=password]').forEach(function (i) { i.value = ''; }); }
      catch (err) { connMsg.className = 'err-msg'; connMsg.textContent = err.message; }
    } },
      el('h3', { text: 'Tantra app (calendar campaigns)' }),
      secretField('tantra_api_key', 'tk_live_…', 'Create one in the Tantra app under API keys, signed in as the account that runs the webinar campaigns. It is used for read calls only.'),
      urlField('tantra_api_base', 'https://api.usetantra.com/api/v1'),
      testBtn('tantra'),
      el('h3', { style: 'margin-top:8px', text: 'Content engine' }),
      secretField('content_token', 'Workspace API token', 'content.usetantra.com: Settings, Workspace, API keys. Use the Account owner’s token so LinkedIn batch results are readable.'),
      urlField('content_base', 'https://content.usetantra.com/api'),
      testBtn('content'),
      el('div', { class: 'row' }, el('button', { class: 'btn primary', type: 'submit', text: 'Save connections' }), connMsg)));

    // facts form
    var costRows = el('div', { class: 'form', style: 'gap:8px' });
    var sessions = state.model.sessions;
    function costRow(cst) {
      cst = cst || { label: '', amount: '', session: 'all' };
      var sel = el('select', { class: 'input', 'data-f': 'session' }, el('option', { value: 'all', text: 'Whole funnel' }), sessions.map(function (s) { var o = el('option', { value: s.id, text: dayLabel(s.id, { weekday: 'short' }) }); if (s.id === cst.session) o.selected = true; return o; }));
      var row = el('div', { class: 'costrow' },
        el('input', { class: 'input', 'data-f': 'label', placeholder: 'What (e.g. WebinarJam plan, LinkedIn ads)', value: cst.label, 'aria-label': 'Cost label' }),
        el('input', { class: 'input', 'data-f': 'amount', type: 'number', min: '0', step: '0.01', placeholder: 'Amount USD', value: cst.amount, 'aria-label': 'Amount in USD' }),
        sel,
        el('button', { class: 'btn icon', type: 'button', 'aria-label': 'Remove cost', onclick: function () { row.remove(); } }, icon('close')));
      return row;
    }
    (inp.costs || []).forEach(function (x) { costRows.appendChild(costRow(x)); });
    if (!(inp.costs || []).length) costRows.appendChild(costRow());
    var t = Object.assign({}, def.targets, inp.targets || {});
    function pctIn(key, label) { return el('div', { class: 'field' }, el('label', { text: label }), el('input', { class: 'input', type: 'number', min: '0', max: '100', step: '0.5', 'data-t': key, value: Math.round(t[key] * 1000) / 10 })); }
    var tc = inp.tantra_campaigns && (inp.tantra_campaigns.tag || inp.tantra_campaigns.name_pattern) ? inp.tantra_campaigns : def.tantra_campaigns;
    var factsMsg = el('span');
    var facts = card('Funnel facts', 'Saved for this funnel only. Changes show on the next refresh.', el('form', { class: 'form', onsubmit: async function (e) {
      e.preventDefault();
      var f = this;
      var payload = {
        costs: Array.from(costRows.querySelectorAll('.costrow')).map(function (r) { return { label: r.querySelector('[data-f=label]').value, amount: r.querySelector('[data-f=amount]').value, session: r.querySelector('[data-f=session]').value }; }),
        targets: {},
        tantra_campaigns: { tag: f.querySelector('#tcTag').value, name_pattern: f.querySelector('#tcName').value },
        exclude_email_patterns: f.querySelector('#excl').value.split(/[\n,]/).map(function (s) { return s.trim(); }).filter(Boolean),
        content_batches: f.querySelector('#batches').value.split(/[\s,]+/).filter(Boolean),
        skip_dates: f.querySelector('#skip').value.split(/[\s,]+/).filter(Boolean),
        extra_dates: f.querySelector('#extra').value.split(/[\s,]+/).filter(Boolean),
        notes: (inp.notes || []),
      };
      f.querySelectorAll('[data-t]').forEach(function (i) { var x = parseFloat(i.value); if (isFinite(x)) payload.targets[i.getAttribute('data-t')] = x / 100; });
      factsMsg.className = 'muted'; factsMsg.textContent = 'Saving…';
      try { await api('/api/settings/inputs?funnel=' + encodeURIComponent(state.funnel), { method: 'POST', body: JSON.stringify(payload) }); factsMsg.className = 'ok-msg'; factsMsg.textContent = 'Saved. Refreshing…'; await refresh(true); factsMsg.textContent = 'Saved and refreshed.'; }
      catch (err) { factsMsg.className = 'err-msg'; factsMsg.textContent = err.message; }
    } },
      el('h3', { text: 'Costs' }), el('div', { class: 'hint muted', style: 'font-size:12.5px;margin-top:-6px', text: 'Ad spend, tool plans, production. Messaging spend comes from the CRM on its own.' }), costRows,
      el('div', null, el('button', { class: 'btn', type: 'button', text: 'Add a cost', onclick: function () { costRows.appendChild(costRow()); } })),
      el('h3', { style: 'margin-top:8px', text: 'Plan rates (%)' }),
      el('div', { class: 'grid', style: 'grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px' }, pctIn('attendance_rate', 'Show-up'), pctIn('booking_rate', 'Bookings per attendee'), pctIn('call_show_rate', 'Call show'), pctIn('close_rate', 'Close')),
      el('h3', { style: 'margin-top:8px', text: 'Which Tantra campaigns belong to this funnel' }),
      el('div', { class: 'grid', style: 'grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px' },
        el('div', { class: 'field' }, el('label', { for: 'tcTag', text: 'Campaign tag contains' }), el('input', { class: 'input', id: 'tcTag', value: tc.tag || '', placeholder: 'e.g. enterprise-webinar' })),
        el('div', { class: 'field' }, el('label', { for: 'tcName', text: 'or campaign name matches' }), el('input', { class: 'input', id: 'tcName', value: tc.name_pattern || '', placeholder: 'e.g. enterprise' }), el('div', { class: 'hint', text: 'A regular expression, not case sensitive. Use Test connection above to see which campaigns match.' }))),
      el('h3', { style: 'margin-top:8px', text: 'Content engine batches' }),
      el('div', { class: 'field' }, el('input', { class: 'input', id: 'batches', value: (inp.content_batches || []).join(', '), placeholder: 'Engine batch ids, comma separated' }), el('div', { class: 'hint', text: 'LinkedIn numbers are only readable per engine batch. List the batches that promote this webinar.' })),
      el('h3', { style: 'margin-top:8px', text: 'Schedule changes' }),
      el('div', { class: 'grid', style: 'grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px' },
        el('div', { class: 'field' }, el('label', { for: 'skip', text: 'Skipped dates' }), el('input', { class: 'input', id: 'skip', value: (inp.skip_dates || []).join(', '), placeholder: 'YYYY-MM-DD' })),
        el('div', { class: 'field' }, el('label', { for: 'extra', text: 'Extra dates' }), el('input', { class: 'input', id: 'extra', value: (inp.extra_dates || []).join(', '), placeholder: 'YYYY-MM-DD' }))),
      el('h3', { style: 'margin-top:8px', text: 'Extra addresses to exclude' }),
      el('div', { class: 'field' }, el('textarea', { class: 'input', id: 'excl', placeholder: 'One pattern per line, e.g. @agency.com', text: (inp.exclude_email_patterns || []).join('\n') }), el('div', { class: 'hint', text: 'Always excluded: ' + def.exclude_email_patterns.join(', ') })),
      el('div', { class: 'row' }, el('button', { class: 'btn primary', type: 'submit', text: 'Save facts' }), factsMsg)));
    append(body, [el('div', { class: 'grid g-12' }, el('div', { class: 'span-5' }, conn), el('div', { class: 'span-7' }, facts))]);
  }

  // ---------------- appearance drawer ----------------
  function openAppearance() {
    var T = window.TDTheme;
    var bg = el('div', { class: 'drawer-bg' });
    var dr = el('aside', { class: 'drawer', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Appearance' });
    function close() { bg.classList.remove('on'); dr.classList.remove('on'); setTimeout(function () { bg.remove(); dr.remove(); }, 260); document.removeEventListener('keydown', esc); themeBtn.focus(); }
    function esc(e) { if (e.key === 'Escape') close(); }
    bg.addEventListener('click', close);
    document.addEventListener('keydown', esc);
    function paint() {
      var cur = T.get();
      body.textContent = '';
      var modes = el('div', { class: 'seg-ctl', role: 'group', 'aria-label': 'Mode' }, [['light', 'Light', 'sun'], ['dark', 'Dark', 'moon'], ['system', 'System', 'system']].map(function (m) {
        return el('button', { type: 'button', 'aria-pressed': String(cur.mode === m[0]), onclick: function () { T.setMode(m[0]); paint(); } }, icon(m[2]), m[1]);
      }));
      var sw = el('div', { class: 'swatches' }, Object.keys(T.presets).map(function (key) {
        var p = T.presets[key];
        return el('button', { type: 'button', class: 'swatch', 'aria-pressed': String(cur.theme === key), onclick: function () { T.setTheme(key); paint(); } },
          el('div', { class: 'sg', style: 'background:linear-gradient(120deg,' + p.g.join(',') + ')' }), el('span', { text: p.name }));
      }));
      var a = el('input', { type: 'color', value: cur.accent, 'aria-label': 'Accent colour' });
      var g = el('input', { type: 'color', value: cur.grad, 'aria-label': 'Gradient end colour' });
      var warn = el('div', { class: 'muted', style: 'font-size:12.5px' });
      function applyCustom() {
        T.setCustom(a.value, g.value);
        var cl = T.contrast(a.value, '#ffffff'), cd = T.contrast(a.value, '#16171f');
        warn.textContent = (cl < 3 || cd < 3) ? 'This colour is hard to read in ' + (cl < 3 ? 'light' : 'dark') + ' mode, so a lighter or darker step of it is used there.' : 'Readable in both modes.';
        sw.querySelectorAll('.swatch').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        customBtn.setAttribute('aria-pressed', 'true');
      }
      a.addEventListener('input', applyCustom); g.addEventListener('input', applyCustom);
      var customBtn = el('button', { type: 'button', class: 'swatch', 'aria-pressed': String(cur.theme === 'custom'), onclick: applyCustom }, el('div', { class: 'sg', style: 'background:linear-gradient(120deg,' + cur.accent + ',' + cur.grad + ')' }), el('span', { text: 'Custom' }));
      sw.appendChild(customBtn);
      append(body, [
        el('div', null, el('h3', { style: 'margin-bottom:10px', text: 'Mode' }), modes),
        el('div', null, el('h3', { style: 'margin-bottom:10px', text: 'Theme' }), sw),
        el('div', null, el('h3', { style: 'margin-bottom:10px', text: 'Custom colours' }),
          el('div', { class: 'form', style: 'gap:10px' }, el('label', { class: 'color-in' }, a, 'Accent'), el('label', { class: 'color-in' }, g, 'Gradient end'), warn)),
        el('div', null, el('h3', { style: 'margin-bottom:10px', text: 'Preview' }), el('div', { class: 'preview' }, el('div', { class: 'pb' }), el('div', { class: 'row' }, el('button', { class: 'btn primary', type: 'button', text: 'Primary action' }), el('span', { class: 'prov LIVE', text: 'Live' }), el('span', { class: 'chip dot upcoming', text: 'Upcoming' })))),
        el('p', { class: 'muted', style: 'font-size:12.5px;margin:0', text: 'Saved on this device. Chart colours stay the same in every theme so a series always keeps its colour and stays readable for colour-blind viewers.' }),
      ]);
    }
    var body = el('div', { class: 'db' });
    append(dr, [el('div', { class: 'dh' }, el('h2', { text: 'Appearance' }), el('button', { class: 'btn icon ghost', type: 'button', 'aria-label': 'Close', onclick: close }, icon('close'))), body]);
    document.body.appendChild(bg); document.body.appendChild(dr);
    paint();
    requestAnimationFrame(function () { bg.classList.add('on'); dr.classList.add('on'); var f = dr.querySelector('button[aria-pressed="true"]'); if (f) f.focus(); });
  }

  // ---------------- chrome: nav, pickers, stamp ----------------
  var navEl = document.getElementById('nav');
  var contentEl = document.getElementById('content');
  var themeBtn = document.getElementById('themeBtn');
  var refreshBtn = document.getElementById('refreshBtn');
  themeBtn.appendChild(icon('palette'));
  refreshBtn.appendChild(icon('refresh'));
  themeBtn.addEventListener('click', openAppearance);
  refreshBtn.addEventListener('click', function () { refresh(true); });
  document.getElementById('signOut').addEventListener('click', async function () { await fetch('/api/logout', { method: 'POST' }); location.replace('/'); });

  function drawNav() {
    navEl.textContent = '';
    VIEWS.forEach(function (v) {
      if (v.sep) navEl.appendChild(el('div', { class: 'sep' }));
      navEl.appendChild(el('button', { type: 'button', 'aria-current': state.view === v.id ? 'page' : null, onclick: function () { go(v.id); } }, icon(v.id), el('span', { text: v.label })));
    });
  }

  function picker(host, label, current, options, onPick) {
    host.textContent = '';
    var menu = el('div', { class: 'menu', role: 'menu', hidden: true });
    var btn = el('button', { type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': 'false' }, el('span', { class: 'lbl', text: label }), el('span', { text: current }), icon('chevron'));
    btn.querySelector('svg').setAttribute('style', 'width:16px;height:16px;opacity:.6');
    function close() { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); document.removeEventListener('click', outside, true); }
    function outside(e) { if (!host.contains(e.target)) close(); }
    btn.addEventListener('click', function () {
      var open = menu.hidden;
      if (open) { menu.hidden = false; btn.setAttribute('aria-expanded', 'true'); document.addEventListener('click', outside, true); var f = menu.querySelector('.opt:not([disabled])'); if (f) f.focus(); } else close();
    });
    menu.addEventListener('keydown', function (e) {
      var opts = Array.from(menu.querySelectorAll('.opt:not([disabled])')), i = opts.indexOf(document.activeElement);
      if (e.key === 'Escape') { close(); btn.focus(); }
      if (e.key === 'ArrowDown') { e.preventDefault(); (opts[i + 1] || opts[0]).focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (opts[i - 1] || opts[opts.length - 1]).focus(); }
    });
    options.forEach(function (o) {
      if (o.header) { menu.appendChild(el('div', { class: 'hd', text: o.header })); return; }
      menu.appendChild(el('button', { type: 'button', class: 'opt', role: 'menuitemradio', 'aria-checked': String(!!o.selected), disabled: o.disabled, onclick: function () { close(); onPick(o.value); } },
        el('span', { class: 'check', text: o.selected ? '✓' : '' }), el('span', null, o.label, o.chip || null, o.hint ? el('small', { text: o.hint }) : null)));
    });
    host.appendChild(btn); host.appendChild(menu);
  }

  function drawPickers() {
    var f = state.funnels.find(function (x) { return x.id === state.funnel; });
    picker(document.getElementById('funnelPick'), 'Funnel', f ? f.short : 'Choose', [{ header: 'Funnels' }].concat(state.funnels.map(function (x) {
      return { value: x.id, label: x.name, selected: x.id === state.funnel, disabled: x.status !== 'live', hint: x.status === 'live' ? (x.generated ? 'Updated ' + ago(x.generated) : 'Live') : 'Coming soon: ' + x.description };
    })), function (id) { if (id !== state.funnel) { state.funnel = id; state.session = 'all'; load(); } });
    if (!state.model) { document.getElementById('sessionPick').textContent = ''; return; }
    var ss = state.model.sessions.slice().reverse();
    var cur = state.session === 'all' ? 'All sessions' : dayLabel(state.session, { weekday: 'short' });
    picker(document.getElementById('sessionPick'), 'Session', cur, [{ value: 'all', label: 'All sessions', selected: state.session === 'all', hint: ss.length + ' sessions so far' }, { header: 'Sessions' }].concat(ss.map(function (s) {
      return { value: s.id, label: dayLabel(s.id, { weekday: 'long', year: 'numeric' }), selected: state.session === s.id, hint: s.status === 'upcoming' ? 'Upcoming · registrations open' : s.status === 'live' ? 'Live now' : (s.mature ? 'Aired' : 'Aired ' + (s.age_days === 1 ? '1 day' : s.age_days + ' days') + ' ago · sales still maturing') };
    })), setSession);
  }
  function setSession(id) { state.session = id; render(); }

  function drawStamp() {
    var st = document.getElementById('stamp');
    if (!state.model) { st.textContent = ''; return; }
    var age = (Date.now() - Date.parse(state.model.generated)) / 60000;
    st.textContent = 'Data as of ' + ago(state.model.generated);
    st.title = new Date(state.model.generated).toLocaleString('en-GB');
    st.classList.toggle('stale', age > 60);
    document.getElementById('buildStamp').textContent = 'Build ' + (state.model.build || '').slice(0, 16);
  }

  function go(view) { state.view = view; render(); contentEl.focus({ preventScroll: true }); window.scrollTo({ top: 0 }); }

  function render() {
    writeHash();
    drawNav(); drawPickers(); drawStamp();
    contentEl.textContent = '';
    if (!state.model) { contentEl.appendChild(el('div', { class: 'loading', text: 'Loading the dashboard…' })); return; }
    var fn = { overview: viewOverview, acquisition: viewAcquisition, attendance: viewAttendance, nurture: viewNurture, commercial: viewCommercial, sessions: viewSessions, health: viewHealth, settings: viewSettings }[state.view] || viewOverview;
    try { append(contentEl, fn()); }
    catch (e) { console.error(e); contentEl.appendChild(empty('This view could not be drawn', e.message)); }
    document.title = (VIEWS.find(function (v) { return v.id === state.view; }) || {}).label + ' · ' + (state.model.funnel.short || 'Tantra Funnels');
  }

  async function refresh(force) {
    if (state.busy) return;
    state.busy = true;
    refreshBtn.classList.add('spin'); refreshBtn.disabled = true;
    contentEl.classList.add('skeleton');
    try {
      var d = force ? await api('/api/refresh?funnel=' + encodeURIComponent(state.funnel), { method: 'POST', body: '{}' }) : { model: await api('/api/model?funnel=' + encodeURIComponent(state.funnel)) };
      state.model = d.model;
      if (state.session !== 'all' && !state.model.views[state.session]) state.session = 'all';
      if (state.view !== 'settings' || !force) render(); else { drawStamp(); }
    } catch (e) {
      if (!state.model) { contentEl.textContent = ''; contentEl.appendChild(empty('Could not load the data', e.message)); }
    } finally {
      state.busy = false; refreshBtn.classList.remove('spin'); refreshBtn.disabled = false; contentEl.classList.remove('skeleton');
    }
  }

  async function load() {
    state.model = null;
    render();
    await refresh(false);
  }

  document.addEventListener('td-theme', function () { if (state.model && state.view !== 'settings') render(); });
  window.addEventListener('hashchange', function () { var f = state.funnel; readHash(); if (state.funnel !== f) load(); else render(); });
  setInterval(function () { if (!document.hidden && state.view !== 'settings') refresh(false); }, 5 * 60e3);
  setInterval(drawStamp, 60e3);
  var wasNarrow = window.innerWidth < 700;
  window.addEventListener('resize', function () { var n = window.innerWidth < 700; if (n !== wasNarrow && state.model && state.view !== 'settings') { wasNarrow = n; render(); } });

  (async function boot() {
    readHash();
    try {
      var d = await api('/api/funnels');
      state.funnels = d.funnels;
      if (!state.funnel || !d.funnels.some(function (f) { return f.id === state.funnel && f.status === 'live'; })) state.funnel = (d.funnels.find(function (f) { return f.status === 'live'; }) || d.funnels[0]).id;
      await load();
    } catch (e) {
      contentEl.textContent = '';
      contentEl.appendChild(empty('Could not reach the dashboard', e.message));
    }
  })();
})();
