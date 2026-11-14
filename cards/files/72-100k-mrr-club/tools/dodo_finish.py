#!/usr/bin/env python3
"""Finish the Dodo one-time checkouts for the three clubs (card 72). Safe to run any number of times.

  python3 deliverables/72-100k-mrr-club/tools/dodo_finish.py status   # read only: key works, products, tax per country
  python3 deliverables/72-100k-mrr-club/tools/dodo_finish.py finish   # create what is missing and wire the links in

What `finish` does, for each one-time product ($5,999, $17,999, $24,997):
  - finds it by name in Dodo, or creates it (USD, tax-exclusive). Dodo refuses the CREATE itself while the business's
    cart value limit is too low (422 CART_AMOUNT_EXCEEDS_LIMIT), so creating it is also the test of the limit: no
    throwaway product is needed. A refused product is reported as BLOCKED and nothing else changes for it.
  - writes its checkout link into deliverables/_shared/funnel-config.json, in the field the pages read:
      club_100k.checkout.pay_in_full, enterprise.checkout.pay, club_10m.checkout.pay
Then it reruns tools/dodo_price_snapshot.py so the INR, GBP and EUR amounts come from Dodo's checkout preview.

Exit code 0: all three wired. 2: at least one still blocked by the cart limit. 1: any other error.
The key is read from DODO_PAYMENTS_API_KEY or ~/.config/tantra/keys/dodo.env and is never printed.
"""
import json, os, subprocess, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / 'deliverables' / '_shared' / 'funnel-config.json'
API = 'https://live.dodopayments.com'
BUSINESS = 'bus_WjIz7R0JDBfhmc430JrKY'
RETURN = 'https://webinar.sellwithtantra.com/tantra-plans/'  # both domains serve these pages; existing links use this host

# config key, checkout field the pages read, product name, cents, return path, description
ONE_TIME = [
    ('club_100k', 'pay_in_full', 'Tantra 100K MRR Club: 6 months, paid in full', 599900, '100k-mrr-club/join/',
     'Six months in the Tantra 100K MRR Club: the Tantra Academy course, the Funnel OS, the Content OS and Tantra Pro, the weekly group coaching call and a weekly coaching hour with our expert team, and the members group. One payment.'),
    ('enterprise', 'pay', 'Tantra $5M ARR Club: 6 months', 1799900, 'enterprise/',
     'Six months in the Tantra $5M ARR Club: our world-class team builds your revenue engine with you, makes it live and coaches you one to one for 2 hours every week, backed by the Tantra 10X ROI Guarantee over 18 months. One payment.'),
    ('club_10m', 'pay', 'Tantra $10M ARR Club: 6 months', 2499700, '10m-arr-club/',
     'Six months in the Tantra $10M ARR Club: our world-class team builds and runs the revenue engine for a company on the way to $10M a year, with 2 hours of one to one coaching every week, backed by the Tantra 10X ROI Guarantee over 18 months. One payment.'),
]
MONTHLY = 'pdt_0Nrt7GB0Fbq27xz21GlYk'


def key():
    k = os.environ.get('DODO_PAYMENTS_API_KEY')
    f = Path.home() / '.config' / 'tantra' / 'keys' / 'dodo.env'
    if not k and f.exists():
        for line in f.read_text().splitlines():
            if line.strip().startswith('DODO_PAYMENTS_API_KEY='):
                k = line.split('=', 1)[1].strip().strip('"\'')
    if not k:
        sys.exit(f'No Dodo key: set DODO_PAYMENTS_API_KEY or put it in {f}')
    os.environ['DODO_PAYMENTS_API_KEY'] = k  # for dodo_price_snapshot.py
    return k


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f'Bearer {key()}', 'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {'message': raw[:300]}


def products():
    out, page = {}, 0
    while True:
        st, r = call('GET', f'/products?page_size=100&page_number={page}')
        if st != 200:
            sys.exit(f'GET /products failed ({st}): {r}. Is the key right and not rotated away?')
        items = r.get('items', [])
        for p in items:
            out[p['name']] = p
        if len(items) < 100:
            return out
        page += 1


def link(pid, ret):
    return f'https://checkout.dodopayments.com/buy/{pid}?quantity=1&redirect_url=' + urllib.parse.quote(RETURN + ret + '?paid=1', safe='')


def tax_preview():
    rows = {}
    for cc in ('IN', 'GB', 'DE', 'US'):
        st, r = call('POST', '/checkouts/preview', {'product_cart': [{'product_id': MONTHLY, 'quantity': 1}], 'billing_address': {'country': cc}})
        if st != 200:
            rows[cc] = f'preview failed ({st})'
            continue
        b = r.get('current_breakup', {})
        rows[cc] = f"{r.get('currency', '?')} subtotal {b.get('subtotal')} tax {b.get('tax')} rate {(r['product_cart'][0].get('tax_rate') or 0) / 100}%"
    return rows


def status():
    have = products()
    print(f'Key works: {len(have)} products in Dodo.')
    for _, _, name, cents, _, _ in ONE_TIME:
        p = have.get(name)
        print(f"  {'FOUND  ' if p else 'MISSING'} {name} (${cents // 100:,})" + (f" {p['product_id']}" if p else ''))
    print('Tax at checkout for the 100K monthly product (amounts in minor units, so 151312 GBP = £1,513.12):')
    for cc, row in tax_preview().items():
        print(f'  {cc}: {row}')


def finish():
    have = products()
    d = json.loads(CFG.read_text())
    T = d['tantra_plans']
    blocked = []
    for cfg_key, field, name, cents, ret, desc in ONE_TIME:
        p = have.get(name)
        if not p:
            st, r = call('POST', '/products', {'name': name, 'description': desc, 'tax_category': 'edtech', 'brand_id': BUSINESS,
                                              'metadata': {'tantra_offer': cfg_key + '_full'},
                                              'price': {'type': 'one_time_price', 'price': cents, 'currency': 'USD', 'discount': 0,
                                                        'purchasing_power_parity': False, 'tax_inclusive': False}})
            if st == 422 and r.get('code') == 'CART_AMOUNT_EXCEEDS_LIMIT':
                print(f'BLOCKED {name}: Dodo still refuses ${cents // 100:,} (cart value limit). Nothing changed for it.')
                blocked.append(name)
                continue
            if st not in (200, 201):
                sys.exit(f'Creating {name} failed ({st}): {r}')
            p = r
            print(f"CREATED {name}: {p['product_id']}")
        else:
            print(f"FOUND   {name}: {p['product_id']}")
        co = T[cfg_key].setdefault('checkout', {})
        co[field] = link(p['product_id'], ret)
        co.setdefault('_products', {})[field] = f"{p['product_id']} (${cents // 100:,} one time, 6 months)"
        co['_note'] = f'One time product live in Dodo ({p["product_id"]}), wired by tools/dodo_finish.py.'
        T[cfg_key].setdefault('dodo_full_product', p['product_id'])
    CFG.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print('Updating the local currency prices from Dodo...')
    subprocess.run([sys.executable, str(Path(__file__).with_name('dodo_price_snapshot.py'))], check=True)
    print('Tax at checkout for the 100K monthly product (amounts in minor units, so 151312 GBP = £1,513.12):')
    for cc, row in tax_preview().items():
        print(f'  {cc}: {row}')
    if blocked:
        print(f'{len(blocked)} still blocked. Send or chase the email in DODO_SUPPORT_HANDOFF.md, then run this again.')
        sys.exit(2)
    print('All three one-time checkouts are wired. Build, scan, commit and deploy next.')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    key()
    {'status': status, 'finish': finish}.get(cmd, lambda: sys.exit('usage: dodo_finish.py status|finish'))()
