"""Anonymise extracted elements: _work/elements/<brand>/*.json -> _work/anon/<brand>/*.json + _work/anon/report.json.

Replaces ONLY identifiers: brand/product/people names (every brand's _subs.json plus GLOBAL below, applied to every
brand), links, emails, phones and @handles. Everything else stays verbatim. Then lists residual proper-noun candidates
(capitalised words not in the system dictionary) for a review pass.
usage: python3 anonymise.py
"""
import json, re, pathlib, collections

W = pathlib.Path(__file__).resolve().parent.parent / '_work'
SRC, OUT = W / 'elements', W / 'anon'
LABEL = {
    '{brand}': '[Company]', '{product}': '[Product]', '{programme}': '[Programme]', '{event_name}': '[Event Name]',
    '{host_name}': '[Host Name]', '{host_first_name}': '[Host First Name]', '{team_member}': '[Team Member]',
    '{guest_name}': '[Guest Speaker]', '{client_name}': '[Client Name]', '{client_company}': '[Client Company]',
    '{community_name}': '[Community]', '{newsletter_name}': '[Newsletter]', '{website}': '[Website]',
    '{address}': '[Address]', '{agency}': '[Agency]', '{organisation}': '[Organisation]', '{title}': '[Title]', '{product_feature}': '[Product Feature]',
}
# Client brand names live in _work/elements/_global_subs.json (private, git-ignored) with every brand's own _subs.json.
GLOBAL = []
EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
URL = re.compile(r'(?i)\b(?:https?://|www\.)[^\s<>()"\'\]]+|\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:com|ai|io|co\.uk|co|uk|org|net|live|tech|app|me|so|community|online|ly|dev|site|link|page|eu|us)\b(?:/[^\s<>()"\'\]]*)?')
FULLURL = re.compile(r'(?i)\b(?:https?://|www\.)[^\s<>()"\'\]]+')
PHONE = re.compile(r'(?<![\w$£€])\+?\d[\d ()-]{8,}\d(?![\w%])')
HANDLE = re.compile(r'(?<![\w.])@[A-Za-z][A-Za-z0-9_.]{2,}')
SKIP = set(json.loads((W / 'skip.json').read_text())) if (W / 'skip.json').exists() else set()   # e.g. speaker rosters with real bios (private list)
TEXT_KEYS = {'title', 'context', 'label', 'offset', 'subject', 'preheader', 'body', 'cta', 'heading', 'source'}

def link_label(u):
    l = u.lower()
    if re.search(r'calendly|cal\.com|book|consult|schedul|strategy|discovery|leadconnector', l): return '[Booking Link]'
    if re.search(r'replay|recording', l): return '[Replay Link]'
    if re.search(r'webinargeek|zoom\.|webinarjam|register|signup|sign-up|event|/live|watch|join', l): return '[Registration Link]'
    if re.search(r'linkedin\.com/in/', l): return '[LinkedIn Profile]'
    if re.search(r'linkedin\.com', l): return '[LinkedIn Link]'
    if re.search(r'chat\.whatsapp|wa\.me', l): return '[WhatsApp Link]'
    return '[Link]'

def compile_subs():
    pairs = list(GLOBAL)
    for f in [*SRC.glob('*/_subs.json'), *SRC.glob('_extra_subs.json'), *SRC.glob('_global_subs.json')]:
        for s in json.loads(f.read_text()):
            if s.get('find', '').strip() and len(s['find'].strip()) >= 3: pairs.append((s['find'].strip(), s['replace'].strip()))
    seen, out = set(), []
    for find, rep in sorted(pairs, key=lambda p: -len(p[0])):
        if find in seen: continue
        seen.add(find)
        word = find.replace(' ', '').replace('.', '').replace('-', '').replace("'", '').isalnum()
        is_name = rep in ('{host_name}', '{host_first_name}', '{team_member}', '{guest_name}', '{client_name}')
        pat = re.escape(find)
        if word: pat = r'(?<![A-Za-z0-9])' + pat + r'(?![A-Za-z0-9])'
        label = re.sub(r'\{([a-z_]+)\}', lambda m: LABEL.get(m.group(0), '[' + m.group(1).replace('_', ' ').title() + ']'), rep)
        out.append((re.compile(pat, 0 if is_name else re.I), label, find))
    return out

def scrub(s, subs, rep):
    if not isinstance(s, str) or not s: return s
    s = re.sub(r'(?m)^#{1,6} ', '', s.replace('\x0b', '\n'))   # heading marks were added by our own export, not the doc
    s = EMAIL.sub(lambda m: (rep.__setitem__('email', rep['email'] + 1), '[Email]')[1], s)
    link = lambda m: (rep.__setitem__('link', rep['link'] + 1), link_label(m.group(0)))[1]
    s = FULLURL.sub(link, s)                      # explicit links first, so a brand inside a URL can't leave a half link
    s = HANDLE.sub(lambda m: (rep.__setitem__('handle', rep['handle'] + 1), '[Handle]')[1], s)
    s = PHONE.sub(lambda m: (rep.__setitem__('phone', rep['phone'] + 1), '[Phone]')[1] if sum(c.isdigit() for c in m.group(0)) >= 9 else m.group(0), s)
    for rx, label, find in subs:                  # then names, so "Brand.ai" reads [Company], not [Link]
        s, n = rx.subn(label, s)
        if n: rep['sub:' + find] += n
    s = URL.sub(link, s)                          # then any bare domain left
    s = re.sub(r'\s*\(t\.[a-z0-9]+\)', '', s)  # Google Docs tab ids from our export
    return s

def walk(o, subs, rep, key=None):
    if isinstance(o, dict): return {k: walk(v, subs, rep, k) for k, v in o.items()}
    if isinstance(o, list): return [walk(x, subs, rep, key) for x in o]
    if isinstance(o, str) and (key in TEXT_KEYS or key is None or key == 'excluded_notes'): return scrub(o, subs, rep)
    return o

def main():
    subs = compile_subs()
    words = set(w.strip().lower() for w in open('/usr/share/dict/words'))
    report, cand = {}, collections.Counter()
    for d in sorted(p for p in SRC.iterdir() if p.is_dir()):
        (OUT / d.name).mkdir(parents=True, exist_ok=True)
        rep = collections.Counter(); n = 0
        for f in sorted(d.glob('*.json')):
            if f.name.startswith('_') or f.stem in SKIP: continue
            el = walk(json.loads(f.read_text()), subs, rep)
            el.pop('excluded_notes', None)
            (OUT / d.name / f.name).write_text(json.dumps(el, ensure_ascii=False, indent=1)); n += 1
            txt = json.dumps({k: v for k, v in el.items() if k not in ('source',)}, ensure_ascii=False)
            for m in re.finditer(r'(?<![.!?:"\n]\s)(?<!^)\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})?)\b', txt):
                w = m.group(1)
                if not all(x.lower() in words for x in w.split()): cand[w] += 1
        if (d / '_brand.json').exists(): (OUT / d.name / '_brand.json').write_text((d / '_brand.json').read_text())
        report[d.name] = {'elements': n, 'replacements': dict(rep.most_common())}
    (OUT / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (OUT / 'candidates.txt').write_text('\n'.join(f'{c}\t{w}' for w, c in cand.most_common()))
    print({b: r['elements'] for b, r in report.items()}, len(cand), 'residual candidates')

if __name__ == '__main__':
    main()
