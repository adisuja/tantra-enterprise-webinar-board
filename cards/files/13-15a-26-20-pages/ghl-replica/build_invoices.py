#!/usr/bin/env python3
"""GoHighLevel Invoices replica for the registration page (Adi, 2026-11-07): the second case-study screenshot.

Same method as build.py: a read-only capture of the Payments > Invoices page (never committed, pass it with --source),
every data field replaced with the illustrative data below, identifiers of the source account removed, CSS pruned,
then one clean HTML file and one image.

Adi's spec: period January 1 to July 31; 1 invoice in draft, 2 in due, 34 received, 3 overdue; received at least $300k;
every invoice name, number, customer, issue date, amount and status randomised (Paid and Overdue rows).

usage: python3 build_invoices.py --source /tmp/ghl/inv-orig.html
outputs: invoices.html, invoices-data.json, ../src/assets/img/ghl-invoices.webp
"""
import argparse, base64, io, json, pathlib, random, re
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from PIL import Image
import build as base

HERE = pathlib.Path(__file__).parent
W, H = 1440, 900
random.seed(202611071)

CUSTOMERS = ['Rohan Mehta', 'Simon Archer', 'Grant Holloway', 'Jonas Albrecht', 'Patrick Doyle', 'Henry Lancaster', 'Caleb Morrison',
             'Yuki Tanaka', 'Anika Bose', 'Hannah Kowalski', 'Priya Natarajan', 'Daniel Whitford', 'Sofia Marchetti', 'Ethan Brooks']
ITEMS = ['Enterprise Funnel Build', 'AI RevOps Retainer', 'Webinar Funnel Setup', 'VSL Funnel Build', 'Outbound Infrastructure Setup',
         'Growth Retainer', 'Pipeline Automation Build', 'Paid Ads Funnel Launch', 'AI Calling Setup', 'CRM Migration and Automation']
AVATAR_BG = ['rgb(153, 189, 117)', 'rgb(184, 112, 89)', 'rgb(176, 104, 184)', 'rgb(110, 138, 199)', 'rgb(199, 140, 84)', 'rgb(94, 165, 160)']
START, END = date(2026, 1, 1), date(2026, 7, 31)
COUNTS = {'draft': 1, 'due': 2, 'received': 34, 'overdue': 3}


def r100(lo, hi):
    return int(-(-random.uniform(lo, hi) // 100) * 100)


def full(v):
    return f'${v:,.2f}'


def card(v):
    # GHL's summary cards: full amount under $100k, thousands with two decimals above.
    return full(v) if v < 100000 else f'${v / 1000:.2f}k'


def day(d):
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def build_data():
    received = [r100(5000, 16000) for _ in range(COUNTS['received'])]
    while sum(received) < 300000:  # Adi: received revenue at least $300k
        received = [v + 500 for v in received]
    overdue = [r100(4000, 14000) for _ in range(COUNTS['overdue'])]
    draft = [r100(6000, 15000)]
    due = [r100(4000, 15000) for _ in range(COUNTS['due'])]
    span = (END - START).days
    # Ten table rows inside the period: three overdue invoices and seven of the paid ones, newest first.
    rows = [{'status': 'Overdue', 'amount': v} for v in overdue] + [{'status': 'Paid', 'amount': v} for v in random.sample(received, 7)]
    random.shuffle(rows)
    dates = sorted((START + timedelta(days=random.randint(0, span)) for _ in rows), reverse=True)
    nums = sorted(random.sample(range(1180, 1260), len(rows)), reverse=True)
    custs = random.sample(CUSTOMERS, len(rows))
    for i, row in enumerate(rows):
        c = custs[i]
        row.update({
            'name': random.choice([f'{random.choice(ITEMS)}', f'{c.split()[0]} {random.choice(ITEMS)}', f'{random.choice(ITEMS)} {random.choice(["Q1", "Q2", "Month 2", "Month 3", "Phase 1", "Phase 2"])}']),
            'number': f'INV-00{nums[i]:04d}', 'customer': c, 'initials': ''.join(w[0] for w in c.split()[:2]),
            'avatar': random.choice(AVATAR_BG), 'date': day(dates[i]), 'amount': full(row['amount']),
        })
    return {
        'location_name': 'Tantra Enterprise', 'location_city': 'Bengaluru, Karnataka', 'user_initials': 'AM',
        'range': [f"{START.strftime('%B')} {START.day}, {START.year}", f"{END.strftime('%B')} {END.day}, {END.year}"],
        'cards': [
            [f"{COUNTS['draft']} Invoice(s) in Draft", card(sum(draft))],
            [f"{COUNTS['due']} Invoice(s) in Due", card(sum(due))],
            [f"{COUNTS['received']} Invoice(s) received", card(sum(received))],
            [f"{COUNTS['overdue']} Invoice(s) Overdue", card(sum(overdue))],
        ],
        'rows': rows,
    }


SPECIFIC = r"""
  $$('.hl_switcher-loc-name').forEach(e => e.textContent = D.location_name);
  $$('.hl_switcher-loc-city').forEach(e => e.textContent = D.location_city);
  $$('.avatar_img').forEach(e => e.textContent = D.user_initials);
  $$('img.agency-logo').forEach(e => { e.src = D.logo; e.removeAttribute('srcset'); });
  // Summary cards, in page order.
  const titles = $$('.ui-statistic-header p.title'), values = $$('p.ui-display-sm-semibold').filter(e => !e.closest('table'));
  D.cards.forEach(([t, v], i) => { if (titles[i]) titles[i].textContent = t; if (values[i]) values[i].textContent = v; });
  // Period: January 1 to July 31, shown the way GHL shows a chosen range.
  $$('.hr-date-picker--range input').forEach((e, i) => { e.setAttribute('value', D.range[i]); e.setAttribute('data-keep', ''); });
  $$('.hr-date-picker--range .hr-input__placeholder').forEach(e => e.remove());
  // Rows: status pills cloned from GHL's own Paid and Overdue pills.
  const rows = $$('tbody tr');
  const pill = {};
  rows.forEach(r => { const td = $('[data-col-key=status]', r); const t = td && td.innerText.trim(); if (t && !pill[t]) pill[t] = td.innerHTML; });
  rows.forEach((r, i) => {
    const d = D.rows[i];
    if (!d) { r.remove(); return; }
    const set = (sel, t) => { const e = $(sel, r); if (!e) throw new Error('row ' + i + ' missing ' + sel); e.textContent = t; };
    set('[data-col-key=name] p span, [data-col-key=name] p', d.name);
    set('[data-col-key=invoiceNumber] p', d.number);
    set('[data-col-key="contactDetails.name"] p span, [data-col-key="contactDetails.name"] p', d.customer);
    const av = $('.hr-avatar', r); av.style.backgroundColor = d.avatar; set('.hr-avatar__text', d.initials);
    set('[data-col-key=issueDate] p', d.date);
    set('[data-col-key=amount] p', d.amount);
    if (pill[d.status]) $('[data-col-key=status]', r).innerHTML = pill[d.status];
  });
"""


def transform_js():
    t = base.TRANSFORM
    head = t[:t.index('  // 1. Account identity')]
    tail = t[t.index('  // 3. Anything not rendered'):]
    return head + SPECIFIC + tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, help='static capture of the GHL Invoices page (never committed)')
    ap.add_argument('--scale', type=float, default=2)
    ap.add_argument('--no-prune', action='store_true')
    ap.add_argument('--no-sweep', action='store_true')
    a = ap.parse_args()
    d = build_data()
    (HERE / 'invoices-data.json').write_text(json.dumps(d, indent=1, ensure_ascii=False))
    m = re.search(r'/location/([A-Za-z0-9]{16,})/', pathlib.Path(a.source).read_text(errors='ignore'))
    d.update(loc=m.group(1) if m else None, prune=not a.no_prune, sweep=not a.no_sweep,
             logo='data:image/png;base64,' + base64.b64encode((base.IMG / 'tantra-mark-white.png').read_bytes()).decode())
    with sync_playwright() as p:
        b = p.chromium.launch(ignore_default_args=['--hide-scrollbars'])
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto(pathlib.Path(a.source).resolve().as_uri(), wait_until='networkidle', timeout=120000)
        pg.wait_for_timeout(800)
        r = pg.evaluate(transform_js(), d)
        out = HERE / 'invoices.html'
        out.write_text(base.page_html(r, 0))
        shot = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=a.scale)
        shot.goto(out.resolve().as_uri(), wait_until='networkidle', timeout=120000)
        shot.wait_for_timeout(1200)
        (HERE / 'invoices-text-audit.json').write_text(json.dumps(shot.evaluate(base.TEXT_AUDIT), indent=1, ensure_ascii=False))
        im = Image.open(io.BytesIO(shot.screenshot())).convert('RGB')
        im.save(base.IMG / 'ghl-invoices.webp', 'WEBP', quality=88, method=6)
        im.save('/tmp/ghl/invoices-preview.png')
        b.close()
    print('wrote invoices.html and ghl-invoices.webp', im.size, d['cards'])


if __name__ == '__main__':
    main()
