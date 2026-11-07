#!/usr/bin/env python3
"""GoHighLevel Opportunities replica for the registration page (Adi, 2026-11-07).

Design source: a static capture of the Opportunities board (DOM plus stylesheets), taken read-only
from the GHL tab through the OpenCLI browser bridge. The capture holds real contact data, so it is
never committed; pass its path with --source. This script swaps every data field for the illustrative
data in data.py, removes every identifier of the source account, drops every off-screen card, prunes
the CSS to the rules in use, and writes one clean HTML file per view, then renders each to an image.

usage: python3 build.py --source /tmp/ghl/orig.html
outputs: pipeline-a.html, pipeline-b.html (replicas), ../src/assets/img/ghl-pipeline-{a,b}.webp
"""
import argparse, json, pathlib, re, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image
import data

HERE = pathlib.Path(__file__).parent
IMG = HERE.parent / 'src' / 'assets' / 'img'
W, H = 1440, 900
# First visible stage per view at a 1440 laptop width: A starts at Upcoming 1st Call Booked, B at Warm List (Deal Won filled in).
VIEWS = {'a': 630, 'b': 1575}

TRANSFORM = r"""
(D) => {
  const PRUNE = D.prune;
  const $ =(s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const leaf = (re) => $$('body *').filter(e => e.childElementCount === 0 && re.test(e.textContent.trim()));
  // 1. Account identity: location switcher, agency logo, user avatar, saved views.
  $$('.hl_switcher-loc-name').forEach(e => e.textContent = D.location_name);
  $$('.hl_switcher-loc-city').forEach(e => e.textContent = D.location_city);
  $$('.avatar_img').forEach(e => e.textContent = D.user_initials);
  $$('img.agency-logo').forEach(e => { e.src = D.logo; e.removeAttribute('srcset'); });
  $$('.view-label').forEach((e, i) => { if (D.views[i]) e.textContent = D.views[i]; });
  leaf(/^\d+ opportunities$/).filter(e => e.classList.contains('count')).forEach(e => e.textContent = D.total);
  // 2. Stages: loading skeletons out, the empty Deal Won column gets a card list, then every card is rewritten.
  $$('.crm-opportunities-card-skeleton').forEach(e => e.remove());
  const stages = $$('.crm-opportunities-stage');
  const byName = Object.fromEntries(stages.map(s => [$('.crm-opportunities-stage-name', s).textContent.trim(), s]));
  const donor = $('.crm-opportunities-stage-cards', byName['Hot List (Verbal Commit)']);
  for (const st of D.stages) {
    const s = byName[st.stage]; if (!s) continue;
    $('.crm-opportunities-stage-count', s).textContent = st.count;
    $('.crm-opportunities-stage-value', s).textContent = st.total;
    let list = $('.crm-opportunities-stage-cards', s);
    if (st.cards.length && !$('.crm-opportunities-card-wrapper', list)) { const c = donor.cloneNode(true); list.replaceWith(c); list = c; }
    const wrappers = $$('.crm-opportunities-card-wrapper', list);
    wrappers.forEach((w, i) => {
      const c = st.cards[i];
      if (!c) { w.remove(); return; }
      $('.crm-opportunities-card-name a', w).textContent = c.name;
      const cell = (id) => $$(`tr#${id} td`, w).filter(td => td.textContent.trim());
      const set = (td, t) => { const sp = $('span span', td) || $('span', td); sp.textContent = t; };
      const [bl, bv] = cell('companyName'); set(bv, c.business);
      const [sl, sv] = cell('source'); set(sl, 'Funnel: '); set(sv, c.funnel);
      const [vl, vv] = cell('monetaryValue'); set(vl, 'Deal Value: '); set(vv, c.value);
      const chip = $$('span.block.min-w-0.truncate', w).find(e => /\d(st|nd|rd|th),/.test(e.textContent)); if (chip) chip.textContent = c.when;
      // Assigned user: a photo becomes an initials avatar in GHL's own default style.
      const img = $('.crm-opportunities-card-assignee .hr-avatar img', w);
      if (img) img.outerHTML = `<span class="hr-avatar__text" style="transform: translateX(-50%) translateY(-50%) scale(1);"><div data-v-6aa814c5="" class="text-xs text-gray-600">${c.assignee}</div></span>`;
      else $$('.crm-opportunities-card-assignee .text-xs.text-gray-600', w).forEach(e => e.textContent = c.assignee);
    });
  }
  // 3. Anything not rendered goes (menus, popovers, hidden templates): no stray data rides along.
  if (D.sweep) $$('body *').forEach(e => { if (e.isConnected && !e.closest('table') && getComputedStyle(e).display === 'none') e.remove(); });
  // 4. Attributes that point at the source account or a person.
  const kill = new RegExp([D.loc, 'msgsndr-private', 'customers/detail', 'companyPhotos'].filter(Boolean).join('|'));
  $$('body, body *').forEach(e => [...e.attributes].forEach(a => {
    // The account id also rides along as a class token: drop the token, keep the classes the CSS needs.
    if (a.name === 'class') { if (kill.test(a.value)) e.setAttribute('class', a.value.split(/\s+/).filter(t => !kill.test(t)).join(' ')); return; }
    if (/^on/.test(a.name) || ['href', 'data-contact-id', 'data-pipeline-stage-id', 'data-image-src', 'srcset'].includes(a.name) || kill.test(a.value)) e.removeAttribute(a.name);
  }));
  $$('[id]').forEach(e => { if (/^[A-Za-z0-9]{20}$/.test(e.id)) e.removeAttribute('id'); });
  $$('img:not([src])').forEach(e => e.remove());
  $$('input:not([data-keep])').forEach(e => e.removeAttribute('value')); $$('[data-keep]').forEach(e => e.removeAttribute('data-keep'));
  // 5. CSS: keep only rules that match something, plus fonts, keyframes and variables.
  const used = (sel) => sel.split(',').some(p => {
    // Strip pseudo-classes, but not the escaped colons inside Tailwind class names (xl\:w-36).
    const s = p.replace(/(?<!\\)::?[a-zA-Z-]+(\([^)]*\))?/g, '').trim() || '*';
    try { return !!document.querySelector(s); } catch { return true; }
  });
  const keep = (rules) => [...rules].map(r => {
    if (r instanceof CSSStyleRule) return (!PRUNE || used(r.selectorText)) ? r.cssText : '';
    if (r instanceof CSSMediaRule || r instanceof CSSSupportsRule || (window.CSSLayerBlockRule && r instanceof CSSLayerBlockRule)) {
      const inner = keep(r.cssRules); return inner ? r.cssText.slice(0, r.cssText.indexOf('{') + 1) + inner + '}' : '';
    }
    return r.cssText;
  }).filter(Boolean).join('\n');
  const css = [], links = [];
  for (const sh of document.styleSheets) { try { css.push(keep(sh.cssRules)); } catch { if (sh.href) links.push(sh.href); } }
  $$('style, link[rel=stylesheet]').forEach(e => e.remove());
  return { css: css.join('\n'), links, body: document.body.outerHTML,
    html: [...document.documentElement.attributes].filter(a => a.name !== 'class').map(a => `${a.name}="${a.value}"`).join(' ') };
}
"""

TEXT_AUDIT = r"""() => [...new Set([...document.querySelectorAll('body *')].filter(e => e.childElementCount === 0).map(e => e.textContent.trim()).filter(Boolean))]"""


def page_html(r, scroll):
    links = ''.join(f'<link rel="stylesheet" href="{h}">' for h in r['links'])
    # The board's horizontal scroll position is the only script: it picks which stages are in view.
    js = f"<script>addEventListener('load',()=>{{document.querySelector('.crm-opportunities-kanban').scrollLeft={scroll}}})</script>" if scroll else ''
    return (f'<!doctype html>\n<html {r["html"]}>\n<head>\n<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">\n'
            f'<title>Opportunities</title>\n{links}\n<style>\n{r["css"]}\n</style>\n</head>\n{r["body"]}\n{js}\n</html>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='static capture of the GHL Opportunities page (never committed)')
    ap.add_argument('--scale', type=float, default=2)
    ap.add_argument('--no-prune', action='store_true')
    ap.add_argument('--no-sweep', action='store_true')
    a = ap.parse_args()
    d = data.build()
    # The source account's location id is read from the capture, never stored here.
    m = re.search(r'/location/([A-Za-z0-9]{16,})/', pathlib.Path(a.source).read_text(errors='ignore'))
    d['loc'] = m.group(1) if m else None
    (HERE / 'data.json').write_text(json.dumps({k: v for k, v in d.items() if k != 'loc'}, indent=1, ensure_ascii=False))
    d['logo'] = 'data:image/png;base64,' + base64.b64encode((IMG / 'tantra-mark-white.png').read_bytes()).decode()
    with sync_playwright() as p:
        # Real scrollbars, as on a Mac browser screenshot (headless hides them by default).
        b = p.chromium.launch(ignore_default_args=['--hide-scrollbars'])
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto(pathlib.Path(a.source).resolve().as_uri(), wait_until='networkidle', timeout=120000)
        pg.wait_for_timeout(800)
        r = pg.evaluate(TRANSFORM, {**d, 'prune': not a.no_prune, 'sweep': not a.no_sweep})
        for key, scroll in VIEWS.items():
            out = HERE / f'pipeline-{key}.html'
            out.write_text(page_html(r, scroll))
            shot = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=a.scale)
            shot.goto(out.resolve().as_uri(), wait_until='networkidle', timeout=120000)
            shot.wait_for_timeout(1200)
            png = shot.screenshot()
            if key == 'a':
                (HERE / 'text-audit.json').write_text(json.dumps(shot.evaluate(TEXT_AUDIT), indent=1, ensure_ascii=False))
            shot.close()
            im = Image.open(io.BytesIO(png)).convert('RGB')
            im.save(IMG / f'ghl-pipeline-{key}.webp', 'WEBP', quality=88, method=6)
            print('wrote', out.name, f'ghl-pipeline-{key}.webp', im.size, f'{out.stat().st_size // 1024} KB html')
        b.close()


if __name__ == '__main__':
    main()
