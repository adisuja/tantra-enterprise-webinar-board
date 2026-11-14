#!/usr/bin/env python3
"""Make the plans pages show what Dodo really charges (card 72, Adi 2026-11-14).

Dodo converts USD prices with its own daily rates and adds local tax (GST, VAT) on top at checkout. This asks Dodo's
checkout preview, per currency, for each live club product, and writes the pre-tax amounts into
deliverables/_shared/funnel-config.json > tantra_plans (club_100k.monthly, enterprise.renewal, club_10m.renewal), plus
tantra_plans.dodo_snapshot with the date, the rates and the tax rates Dodo applied. One-time prices that have no Dodo
product yet (blocked by the cart limit) are converted with the same rates and marked as estimates.

Run before a deploy when prices or rates matter: DODO_PAYMENTS_API_KEY=... python3 tools/dodo_price_snapshot.py
The key never goes in the repo (Mac: ~/.config/tantra/keys/dodo.env).
"""
import datetime, json, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CFG = ROOT / 'deliverables' / '_shared' / 'funnel-config.json'
KEY = os.environ['DODO_PAYMENTS_API_KEY']
COUNTRY = {'INR': 'IN', 'GBP': 'GB', 'EUR': 'DE'}
SYM = {'USD': '$', 'INR': '₹', 'GBP': '£', 'EUR': '€'}


def preview(pid, country):
    body = json.dumps({'product_cart': [{'product_id': pid, 'quantity': 1}], 'billing_address': {'country': country}}).encode()
    req = urllib.request.Request('https://live.dodopayments.com/checkouts/preview', data=body, method='POST',
                                 headers={'Authorization': f'Bearer {KEY}', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fmt(cur, minor):
    n = round(minor / 100)
    if cur == 'INR':  # Indian grouping: 1,92,194
        s = str(n)
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        return SYM[cur] + ','.join(parts + [tail]) if parts else SYM[cur] + tail
    return f'{SYM[cur]}{n:,}'


def main():
    d = json.loads(CFG.read_text())
    T = d['tantra_plans']
    monthly = 'pdt_0Nrt7GB0Fbq27xz21GlYk'
    renew = {'enterprise': 'pdt_0Nrt7GXlUDLfsEH3pYK3a', 'club_10m': 'pdt_0Nrt7GlYeMa6DDNiOsg6D'}
    snap = {'date': datetime.date.today().isoformat(), 'rates': {}, 'tax_rate_pct': {}, 'note': 'Pre-tax amounts from Dodo checkout preview; local tax is added at checkout.'}
    first, then = {'USD': '$1,999'}, {'USD': '$999'}
    for cur, cc in COUNTRY.items():
        p = preview(monthly, cc)
        first[cur] = fmt(cur, p['current_breakup']['subtotal'])
        then[cur] = fmt(cur, p['recurring_breakup']['subtotal'])
        snap['rates'][cur] = round(p['recurring_breakup']['subtotal'] / 99900, 5)
        snap['tax_rate_pct'][cur] = (p['product_cart'][0].get('tax_rate') or 0) / 100
    T['club_100k']['monthly'] = {'first': first, 'then': then}
    for key, pid in renew.items():
        m = {'USD': T[key]['renewal']['USD']}
        for cur, cc in COUNTRY.items():
            m[cur] = fmt(cur, preview(pid, cc)['recurring_breakup']['subtotal'])
        T[key]['renewal'] = m
    # One-time prices without a Dodo product yet: the same rates, marked as estimates.
    for key, usd in (('club_100k', 599900), ('enterprise', 1799900), ('club_10m', 2499700)):
        T[key]['prices'] = {'USD': fmt('USD', usd), **{cur: fmt(cur, usd * r) for cur, r in snap['rates'].items()}}
    snap['estimated'] = ['club_100k.prices', 'enterprise.prices', 'club_10m.prices']
    T['dodo_snapshot'] = snap
    CFG.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'first': first, 'then': then, 'rates': snap['rates'], 'tax': snap['tax_rate_pct']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
