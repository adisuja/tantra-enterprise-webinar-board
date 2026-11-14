// Appearance: light/dark mode plus colour themes. Runs in <head> before first paint.
// Saved per viewer in localStorage (a convenience, so every read and write is guarded).
// Chart series colours never change with the theme: they were validated for colour-blind
// separation in both modes (dataviz validator), and a series keeps its colour everywhere.
// The theme changes the accent (buttons, focus, single-series charts, the hero) and the gradient.
(function () {
  var PRESETS = {
    volt:     { name: 'Tantra Volt', light: '#6d4aff', dark: '#8f7bff', g: ['#6d4aff', '#22d3ee'] },
    ocean:    { name: 'Ocean',       light: '#0a6fd1', dark: '#4a9bf0', g: ['#0a6fd1', '#14b8a6'] },
    emerald:  { name: 'Emerald',     light: '#0b875b', dark: '#2fb37f', g: ['#059669', '#84cc16'] },
    sunset:   { name: 'Sunset',      light: '#c9461a', dark: '#f07a45', g: ['#f97316', '#e11d48'] },
    orchid:   { name: 'Orchid',      light: '#c42a6a', dark: '#ec5f97', g: ['#db2777', '#8b5cf6'] },
    graphite: { name: 'Graphite',    light: '#4a5263', dark: '#a3acbd', g: ['#1e293b', '#64748b'] },
    aurora:   { name: 'Aurora',      light: '#5b4ae0', dark: '#8b8bff', g: ['#4f46e5', '#06b6d4', '#10b981'] },
  };
  function read(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
  function write(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function hexToRgb(h) { h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join(''); var n = parseInt(h, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function lum(h) { var c = hexToRgb(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; }
  function contrast(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  // Move a colour toward white (amt > 0) or black (amt < 0).
  function shade(h, amt) { var c = hexToRgb(h); return '#' + c.map(function (v) { var t = amt > 0 ? 255 : 0; return Math.round(v + (t - v) * Math.abs(amt)).toString(16).padStart(2, '0'); }).join(''); }
  var SURF = { light: '#ffffff', dark: '#16171f' };
  // A custom accent is nudged until it clears 3:1 against the surface, so it stays legible.
  function legible(hex, mode) {
    var c = hex, i = 0;
    while (contrast(c, SURF[mode]) < 3 && i < 12) { c = shade(c, mode === 'dark' ? 0.12 : -0.12); i++; }
    return c;
  }

  function resolveMode(pref) {
    if (pref === 'light' || pref === 'dark') return pref;
    try { return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; } catch (e) { return 'light'; }
  }

  function apply() {
    var root = document.documentElement;
    var pref = read('td-mode', 'system');
    var mode = resolveMode(pref);
    var key = read('td-theme', 'volt');
    var p = PRESETS[key];
    var accent, grad;
    if (key === 'custom') {
      var a = read('td-custom-accent', '#6d4aff');
      var g2 = read('td-custom-grad', '#22d3ee');
      accent = legible(a, mode);
      grad = [a, g2];
    } else {
      if (!p) { p = PRESETS.volt; key = 'volt'; }
      accent = p[mode];
      grad = p.g;
    }
    root.setAttribute('data-theme', mode);
    root.setAttribute('data-palette', key);
    root.style.setProperty('--accent', accent);
    root.style.setProperty('--accent-soft', 'color-mix(in srgb, ' + accent + ' 14%, transparent)');
    root.style.setProperty('--accent-line', 'color-mix(in srgb, ' + accent + ' 40%, transparent)');
    root.style.setProperty('--on-accent', contrast(accent, '#ffffff') >= 4.5 ? '#ffffff' : '#0b0d12');
    root.style.setProperty('--grad', 'linear-gradient(120deg, ' + grad.join(', ') + ')');
    root.style.setProperty('--grad-a', grad[0]);
    root.style.setProperty('--grad-b', grad[grad.length - 1]);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', mode === 'dark' ? '#0e0f15' : '#f6f7fb');
  }

  window.TDTheme = {
    presets: PRESETS,
    get: function () { return { mode: read('td-mode', 'system'), theme: read('td-theme', 'volt'), accent: read('td-custom-accent', '#6d4aff'), grad: read('td-custom-grad', '#22d3ee') }; },
    setMode: function (m) { write('td-mode', m); apply(); document.dispatchEvent(new CustomEvent('td-theme')); },
    setTheme: function (t) { write('td-theme', t); apply(); document.dispatchEvent(new CustomEvent('td-theme')); },
    setCustom: function (a, g) { write('td-custom-accent', a); write('td-custom-grad', g); write('td-theme', 'custom'); apply(); document.dispatchEvent(new CustomEvent('td-theme')); },
    contrast: contrast,
    apply: apply,
  };
  apply();
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      if (read('td-mode', 'system') === 'system') { apply(); document.dispatchEvent(new CustomEvent('td-theme')); }
    });
  } catch (e) {}
})();
