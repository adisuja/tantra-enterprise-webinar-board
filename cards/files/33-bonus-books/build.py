#!/usr/bin/env python3
"""Builds the bonus site (served by worker/, behind the TANTRA password) into site/.

  /             hub: the two books
  /playbook/    The $1MN+ B2B RevOps Playbook (content/playbook/*.md)
  /library/     The $1MN+ AI Funnel Prompt Library: templates (from _work/anon, the anonymised elements) + data.json
  /prompts/     setup prompt and every element prompt (content/prompts/*.md)

Content syntax (content/playbook/*.md): front matter (id, nav, part), markdown, plus
  @@task <num> | <title> | <time> | <tool>   ...   @@end      a task card (reference task-card anatomy)
  @@funnel <id>[,<id>]   ...   @@end                           shown only for those funnel types (switcher at top)
  @@examples <type>[,<type>]                                   links into the library for those element types
  ```prompt <title>   ...   ```                                a copyable prompt box ([FILL: ...] highlighted)
usage: python3 build.py            (writes site/; does not deploy; see publish.sh)
"""
import html, json, pathlib, re, time, shutil
import markdown

HERE = pathlib.Path(__file__).parent
SITE, SRC, CONTENT = HERE / 'site', HERE / 'src', HERE / 'content'
ANON = HERE / '_work' / 'anon'
DATA_SNAPSHOT = HERE / 'private' / 'library.json'   # committed, anonymised; used when _work/ is absent
V = str(int(time.time()))
FUNNELS = [
    ('webinar', 'Webinar'), ('workshop', 'Workshop'), ('rsp', 'Reverse Squeeze Page'), ('call', 'Book a Call'),
    ('challenge', 'Challenge'), ('community', 'Community'), ('social', 'Social Following'), ('launch', 'Product Launch'),
]
FN = dict(FUNNELS)
DASH = re.compile('[–—]')

def md(text):
    return markdown.markdown(text, extensions=['tables', 'sane_lists', 'attr_list'])

def esc(s):
    return html.escape(str(s), quote=True)

def prompt_box(title, body):
    b = re.sub(r'(\[FILL:[^\]]*\])', r'<span class="fill">\1</span>', esc(body.strip('\n')))
    return (f'<div class="prompt"><div class="prompt__head"><span class="prompt__label">{esc(title or "Prompt")}</span>'
            f'<button class="btn btn--sm" data-copy-pre>Copy prompt</button></div><pre>{b}</pre></div>')

# ---------------------------------------------------------------- playbook

def parse_front(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    meta = dict(l.split(':', 1) for l in m.group(1).splitlines()) if m else {}
    return {k.strip(): v.strip() for k, v in meta.items()}, text[m.end():] if m else text

def render_blocks(lines, ctx):
    """Render a list of lines with @@ blocks and ```prompt fences into HTML."""
    out, buf, i = [], [], 0
    def flush():
        if buf:
            out.append(md('\n'.join(buf))); buf.clear()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```prompt'):
            flush(); title = ln[len('```prompt'):].strip(); j = i + 1
            while not lines[j].startswith('```'): j += 1
            out.append(prompt_box(title, '\n'.join(lines[i + 1:j]))); i = j + 1; continue
        if ln.startswith('@@examples'):
            flush(); spec, _, label = ln.split(None, 1)[1].partition('|')
            types = [t.strip() for t in spec.split(',') if t.strip() in ctx['present']]
            if not types: i += 1; continue
            links = ''.join(f'<a class="exlink" href="../library/#t={t}">{esc(ctx["types"].get(t, t.replace("_", " ").title()))}</a>' for t in types)
            out.append(f'<p class="exrow"><span>{esc(label.strip() or "Real examples in the library:")}</span>{links}</p>'); i += 1; continue
        if ln.startswith('@@task') or ln.startswith('@@funnel'):
            flush(); depth, j = 1, i + 1
            while depth:
                if lines[j].startswith('@@task') or lines[j].startswith('@@funnel'): depth += 1
                elif lines[j].strip() == '@@end': depth -= 1
                j += 1
            inner = render_blocks(lines[i + 1:j - 1], ctx)
            if ln.startswith('@@funnel'):
                ids = [x.strip() for x in ln.split(None, 1)[1].split(',')]
                tag = ' · '.join(FN[x] for x in ids)
                out.append(f'<div class="fv" data-funnels="{" ".join(ids)}"><p class="fv__tag">For the {esc(tag)} funnel</p>{inner}</div>')
            else:
                num, title, t, tool = [x.strip() for x in (ln[len('@@task'):].split('|') + ['', '', ''])[:4]]
                tid = f'task-{ctx["ch"]}-' + num.replace('.', '-')
                ctx['tasks'].append((num, title, tid))
                meta = ''.join(f'<span><i>{k}</i>{esc(v)}</span>' for k, v in (('Time', t), ('Tool', tool)) if v)
                out.append(f'<article class="tk" id="{tid}"><header class="tk__h"><p class="tk__n">Task {esc(num)}</p><h3>{esc(title)}</h3>'
                           f'<div class="tk__meta">{meta}</div></header><div class="tk__b">{inner}</div></article>')
            i = j; continue
        buf.append(ln); i += 1
    flush()
    return '\n'.join(out)

def build_playbook(types, present):
    chapters = []
    for f in sorted((CONTENT / 'playbook').glob('*.md')):
        meta, body = parse_front(f.read_text())
        ctx = {'types': types, 'tasks': [], 'ch': meta.get('id', f.stem), 'present': present}
        h = render_blocks(body.split('\n'), ctx)
        chapters.append({**meta, 'html': h, 'tasks': ctx['tasks']})
    nav, parts, last = [], [], None
    for c in chapters:
        if c.get('part') != last:
            nav.append(f'<p class="toc__part">{esc(c.get("part", ""))}</p>'); last = c.get('part')
        tasks = ''.join(f'<li><a href="#{tid}"><b>{esc(n)}</b> {esc(t)}</a></li>' for n, t, tid in c['tasks'])
        sub = (f'<button class="toc__more" aria-expanded="false">+ {len(c["tasks"])} tasks</button><ol class="toc__tasks">{tasks}</ol>') if c['tasks'] else ''
        nav.append(f'<div class="toc__ch"><a href="#{c["id"]}" data-ch="{c["id"]}">{esc(c["nav"])}</a>{sub}</div>')
        fl = f' data-funnels="{esc(c["funnels"])}"' if c.get('funnels') else ''
        parts.append(f'<section class="ch" id="{c["id"]}"{fl}>{c["html"]}</section>')
    switch = ''.join(f'<button class="fsw__b" data-f="{k}" aria-pressed="false">{esc(n)}</button>' for k, n in FUNNELS)
    n_tasks = sum(len(c['tasks']) for c in chapters)
    body = f'''<div class="pb">
  <aside class="toc" aria-label="Playbook contents"><button class="btn toc__toggle" aria-expanded="false">Contents</button><nav class="toc__body"><p class="toc__h">Playbook</p>{''.join(nav)}</nav></aside>
  <main id="main" class="pb__main">
    <div class="fsw" role="group" aria-label="Your funnel"><span class="fsw__l">Your funnel</span><div class="fsw__opts">{switch}</div></div>
    {''.join(parts)}
  </main>
</div>'''
    return page('The $1MN+ B2B RevOps Playbook', 'playbook', body, css=['playbook.css'], js=['playbook.js'], extra=f' data-tasks="{n_tasks}"'), n_tasks

# ---------------------------------------------------------------- library

CATEGORIES = [
    ('foundation', 'Foundations'), ('traffic', 'Stage 1: Traffic Generation Engine'), ('landing', 'Stage 2: Landing and Registration'),
    ('nurture', 'Stage 3: Multi-Channel Nurture'), ('conversion', 'Stage 4: Conversion Mechanism'),
    ('sales', 'Stage 5: Revenue Engine'), ('growth', 'Stage 6: Long-Term Nurture Engine'),
]
# id: (category, name, description, playbook anchor, task number, task title, funnel to open the playbook on)
TYPES = {
    'brand_offer': ('foundation', 'Company, Offer and Brand Voice', 'The company overview, the offer, the positioning and the brand voice every other element is written from, as one document per brand.', 'task-decisions-1-02', '1.02', 'Name your method, set your voice and list your proof', ''),
    'icp': ('foundation', 'Ideal Customer Profile and Targeting', 'Who the funnel is for: the accounts, the buyer persona, and the exact list filters and job titles.', 'task-decisions-1-04', '1.04', 'Define the buyer persona from real customers', ''),
    'event_titles': ('foundation', 'Event Titles', 'Tested titles for the session, workshop or video.', 'task-decisions-1-07', '1.07', 'Set the date and write the event line', ''),
    'cold_email': ('traffic', 'Cold Email Sequences', 'Multi-step cold email threads that invite named buyers.', 'task-traffic-2-01', '2.01', 'Write the cold email thread', ''),
    'calendar_invite': ('traffic', 'Cold Calendar Invites', 'Invite titles and descriptions that land in a prospect calendar.', 'task-traffic-2-02', '2.02', 'Write the cold calendar invite', ''),
    'linkedin_outreach': ('traffic', 'LinkedIn Outreach Sequences', 'Connection notes and the messages that follow acceptance.', 'task-traffic-2-03', '2.03', 'Write the LinkedIn outreach sequence', ''),
    'linkedin_profile': ('traffic', 'LinkedIn Profile Branding', 'Headlines, about sections and banner copy for the people who send outreach.', 'task-traffic-2-04', '2.04', 'Brand the sender profiles', ''),
    'event_page': ('traffic', 'Event Pages', 'The event listing on LinkedIn and on the webinar platform.', 'task-traffic-2-05', '2.05', 'Publish the event pages', ''),
    'ads': ('traffic', 'Ads and Ad Plans', 'Paid ad copy and the campaign plan behind it.', 'task-traffic-2-06', '2.06', 'Write and launch two ads', ''),
    'social_posts': ('traffic', 'LinkedIn Posts', 'Posts that teach, build trust and promote the event.', 'task-traffic-2-07', '2.07', 'Set up your content engine', ''),
    'lead_magnet': ('traffic', 'Lead Magnets and Giveaways', 'Free resources that earn a registration, a follow or an email.', 'task-conversion-social-5-03', '5.03', 'Offer one free resource that collects the email', 'social'),
    'landing_page': ('landing', 'Landing Pages', 'Long-form landing pages and their parts: registration pages, a thank-you page and a lead gen form.', 'task-landing-3-01', '3.01', 'Build the landing page in nine blocks', ''),
    'proof': ('landing', 'Testimonials and Case Studies', 'Client proof used on pages, in emails and in the session.', 'task-landing-3-01', '3.01', 'Build the landing page in nine blocks', ''),
    'confirmation': ('nurture', 'Confirmation Messages', 'The message that lands the moment someone signs up.', 'task-nurture-4-01', '4.01', 'Write the confirmation message', ''),
    'reminders': ('nurture', 'Reminders and Promotion', 'Email and WhatsApp reminders that get registrants to show up, and promotion emails to your own list.', 'task-nurture-4-02', '4.02', 'Write the reminder sequence', ''),
    'session': ('conversion', 'Session Outlines and Scripts', 'The structure and talk track of the live session.', 'task-conversion-webinar-5-01', '5.01', 'Write the session story', 'webinar'),
    'deck': ('conversion', 'Deck Outlines', 'Slide-by-slide decks, bonus slides and holding slides.', 'task-conversion-webinar-5-02', '5.02', 'Build the deck', 'webinar'),
    'live_engagement': ('conversion', 'Live Engagement: Polls, Chat, DMs and Q&A', 'Everything that keeps the room talking and surfaces buyers during the session.', 'task-conversion-webinar-5-03', '5.03', 'Write the run of show, polls, chat prompts and DMs', 'webinar'),
    'vsl': ('conversion', 'Video Sales Letter Scripts', 'Video-first scripts for a reverse squeeze page: teach first, then ask.', 'task-conversion-rsp-5-01', '5.01', 'Write the video sales letter script', 'rsp'),
    'event_followup': ('sales', 'Attendee and No-Show Follow-Ups', 'What attendees, no-shows and replay viewers receive after the session.', 'task-close-6-01', '6.01', 'Follow up attendees and no-shows', ''),
    'call_followup': ('sales', 'Sales Call Reminders and Follow-Ups', 'The messages around a booked sales call.', 'task-close-6-03', '6.03', 'Put a clock on every pipeline stage', ''),
    'offer_emails': ('sales', 'Offer, Cohort and Downsell Emails', 'Emails that sell the offer, a cohort seat or a lighter version.', 'task-conversion-launch-5-03', '5.03', 'Open the cart and close it on time', 'launch'),
    'newsletter': ('growth', 'Newsletters', 'The weekly letter that keeps every non-buyer warm for a year.', 'task-growth-7-01', '7.01', 'Write the welcome series that teaches your method', ''),
    'reengagement': ('growth', 'Re-Engagement and Remarketing', 'Emails that bring back past registrants, old leads and lost deals.', 'task-growth-7-03', '7.03', 'Reactivate the old list', ''),
}
DASH_FIX = [(re.compile(r'(?<=\d)\s?[–—]\s?(?=\d)'), ' to '), (re.compile(r'\s+[–—]\s+'), ', '), (re.compile('[–—]'), ', ')]
CLEAN = HERE / '_work' / 'clean'

def undash(o):
    if isinstance(o, dict): return {k: undash(v) for k, v in o.items()}
    if isinstance(o, list): return [undash(x) for x in o]
    if isinstance(o, str):
        for rx, rep in DASH_FIX: o = rx.sub(rep, o)
        return re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t]+\n', '\n', o)).strip() if '\n' in o else o.strip()
    return o

def offer_group(t):
    t = t.lower()
    if 'software' in t: return 'Software + Service' if any(w in t for w in ('service', 'implementation', 'pilot', 'done')) else 'Software'
    if any(w in t for w in ('training', 'programme', 'program', 'course', 'certification')): return 'Training Programme'
    if 'consult' in t or 'coaching' in t: return 'Consulting'
    return 'Done-for-You Service'

# One document per brand for these types (Adi, 2026-11-08): ICP, persona, targeting and job titles are one thing;
# company overview, offer, positioning and brand voice are one thing.
SINGLE = {
    'icp': ('Ideal Customer Profile and Targeting', ['Ideal customer profile', 'Buyer persona', 'Targeting criteria', 'Job titles']),
    'brand_offer': ('Company, Offer and Brand Voice', ['Company overview', 'Offer', 'Positioning', 'Brand voice']),
}

def merge_single(elements, brands):
    out, groups = [], {}
    for e in elements:
        if e['type'] in SINGLE: groups.setdefault((e['type'], e['brand']), []).append(e)
        else: out.append(e)
    for (t, b), els in groups.items():
        name, order = SINGLE[t]
        els.sort(key=lambda e: order.index(e['subtype']) if e['subtype'] in order else 9)
        parts, seen = [], set()
        for e in els:
            for v in e['versions'][:1]:
                for p in v['parts']:
                    lab = e['subtype'] + (': ' + p['label'] if p.get('label') and p['label'].lower() != e['subtype'].lower() else '')
                    if lab.lower() in seen: lab = f"{lab} ({e['title']})"
                    seen.add(lab.lower())
                    if any(p['body'].strip() == q['body'].strip() for q in parts): continue
                    parts.append({**p, 'label': lab})
        niche = brands[b].get('niche') or brands[b].get('label', '')
        sl = list(dict.fromkeys(e['subtype'] for e in els if e['subtype']))
        subs = ', '.join(sl)
        said = (', '.join(sl[:-1]) + ' and ' + sl[-1]) if len(sl) > 1 else (sl[0] if sl else name)
        art = 'an' if niche[:1].lower() in 'aeiou' else 'a'
        media = [m for e in els for m in e.get('media', [])]
        out.append({**({'media': media} if media else {}), 'id': els[0]['id'], 'brand': b, 'type': t, 'subtype': subs, 'title': f'{name}: {niche}'[:90],
                    'context': f'One document holding the {said.lower()} for {art} {niche} brand.', 'funnel': 'any', 'versions': [{'label': '', 'parts': parts}]})
    return out

MEDIA_MAP = HERE / '_work' / 'media' / 'media_map.json'

def library_data():
    mm = json.loads(MEDIA_MAP.read_text()) if MEDIA_MAP.exists() else {'attach': {}, 'elements': [], 'pages': []}
    if not CLEAN.exists():
        return json.loads(DATA_SNAPSHOT.read_text())
    brands, elements, codes = {}, [], {}
    for d in sorted(p for p in CLEAN.iterdir() if p.is_dir()):
        src = ANON / d.name / '_brand.json'
        b = json.loads(src.read_text()) if src.exists() else {}
        code = 'b' + str(len(brands) + 1)
        label = b.get('label', '')
        brands[code] = {'label': label, 'industry': b.get('industry', ''), 'niche': label.split(' · ', 1)[-1] if ' · ' in label else b.get('niche', ''),
                        'offer_type': offer_group(b.get('offer_type', '')), 'audience': b.get('audience', '')}
        for f in sorted(d.glob('*.json')):
            if f.name.startswith('_'): continue
            el = json.loads(f.read_text())
            if el.get('type') not in TYPES or not el.get('versions'): continue
            versions = [{'label': v.get('label', ''), 'parts': [{k: (re.sub(r'(^|:\s*)Section:\s*', r'\1', p[k]) if k == 'label' else p[k]) for k in ('label', 'subject', 'preheader', 'body', 'cta') if p.get(k)} for p in v.get('parts', []) if p.get('body')]} for v in el['versions']]
            versions = [v for v in versions if v['parts']]
            media = mm['attach'].get(f'{d.name}/{f.name}', [])
            if not versions and not media: continue
            keep = {'id': f'{code}-{len(elements) + 1}', 'brand': code, 'type': el['type'], 'subtype': el.get('subtype', ''), 'title': el.get('title', ''),
                    'context': el.get('context', ''), 'funnel': el.get('funnel', ''), 'versions': versions}
            if media: keep['media'] = media
            elements.append(undash(keep))
        codes[d.name] = code
    for g in mm['elements'] + mm['pages']:   # media-only elements and live page captures
        if g.get('type') not in TYPES or g.get('brand') not in codes: continue
        e = {'id': f"{codes[g['brand']]}-{len(elements) + 1}", 'brand': codes[g['brand']], 'type': g['type'], 'subtype': g.get('subtype', ''),
             'title': g.get('title', ''), 'context': g.get('context', ''), 'funnel': 'any', 'versions': []}
        if g.get('media'): e['media'] = g['media']
        if g.get('page'): e['page'] = g['page']
        elements.append(undash(e))
    elements = merge_single(elements, brands)
    order = {t: i for i, t in enumerate(TYPES)}
    elements.sort(key=lambda e: (order[e['type']], 0 if e.get('page') else 1, e['subtype'], e['brand']))
    industries = sorted({b['industry'] for b in brands.values() if b.get('industry')})
    offers = sorted({b['offer_type'] for b in brands.values() if b.get('offer_type')})
    present = {e['type'] for e in elements}
    cats = [{'id': c, 'name': n, 'types': [{'id': t, 'name': v[1], 'desc': v[2], 'task': v[3], 'taskNum': v[4], 'taskTitle': v[5], 'funnel': v[6], 'funnelName': FN.get(v[6], '')} for t, v in TYPES.items() if v[0] == c and t in present]} for c, n in CATEGORIES]
    data = {'brands': undash(brands), 'elements': elements, 'categories': [c for c in cats if c['types']], 'industries': industries, 'offers': offers}
    DATA_SNAPSHOT.parent.mkdir(exist_ok=True)
    DATA_SNAPSHOT.write_text(json.dumps(data, ensure_ascii=False))
    return data

def load_prompts():
    """content/prompts/setup.md is the setup prompt; content/prompts/types.md holds '## <type_id> | <name>' sections."""
    setup = (CONTENT / 'prompts' / 'setup.md').read_text().strip() if (CONTENT / 'prompts' / 'setup.md').exists() else ''
    types = {}
    for f in sorted((CONTENT / 'prompts' / 'types').glob('*.md')):   # one file per element type: first line '# <name>'
        head, _, body = f.read_text().partition('\n')
        types[f.stem] = {'name': head.lstrip('# ').strip(), 'prompt': body.strip()}
    if types: return {'setup': setup, 'types': types}
    p = CONTENT / 'prompts' / 'types.md'
    if p.exists():
        for blk in re.split(r'^## ', p.read_text(), flags=re.M)[1:]:
            head, _, body = blk.partition('\n')
            tid, _, name = head.partition('|')
            types[tid.strip()] = {'name': name.strip() or TYPES.get(tid.strip(), ('', tid))[1], 'prompt': body.strip()}
    return {'setup': setup, 'types': types}

# ---------------------------------------------------------------- shell

NAV = [('/', 'hub', 'Bonuses'), ('/playbook/', 'playbook', 'Playbook'), ('/library/', 'library', 'Template Library'), ('/prompts/', 'prompts', 'AI Prompts')]

def page(title, key, body, css=(), js=(), extra=''):
    nav = ''.join(f'<a href="{h}"{" aria-current=page" if k == key else ""}>{esc(n)}</a>' for h, k, n in NAV)
    name = {'hub': 'Your Webinar Bonuses', 'playbook': 'The B2B RevOps Playbook', 'library': 'The AI Funnel Prompt Library', 'prompts': 'The AI Funnel Prompt Library'}[key]
    links = ''.join(f'<link rel="stylesheet" href="/assets/{c}?v={V}">' for c in ('base.css', *css))
    scripts = ''.join(f'<script src="/assets/{j}?v={V}" defer></script>' for j in ('common.js', *js))
    out = f'''<!doctype html>
<html lang="en" data-v="{V}"{extra}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{esc(title)} · Tantra</title><link rel="icon" href="/assets/img/tantra-favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
{links}{scripts}</head>
<body class="is-{key}"><a class="skip" href="#main">Skip to content</a>
<header class="bar"><div class="bar__in"><a class="brand" href="/"><img class="m" src="/assets/img/tantra-mark-ink.png" alt="" width="45" height="30"><img class="w" src="/assets/img/tantra-word-ink.png" alt="Tantra" height="13"><span class="brand__sep"></span><span class="brand__name">{esc(name)}</span></a><nav class="bar__nav" aria-label="Bonuses">{nav}</nav></div><div class="progress"></div></header>
{body}
<div class="toast" role="status" aria-live="polite"></div>
</body></html>'''
    if DASH.search(out):
        raise SystemExit(f'em or en dash found in {key}: ' + out[max(0, DASH.search(out).start() - 80):DASH.search(out).start() + 20])
    return out

# Bonus 04 (Adi 2026-11-12, round 2): the 72-hour Tantra engine offer, built as a product showcase. A live countdown to the
# second; the channels with their real logos (iconify "logos" set, CC0, and vscode-icons for Outlook, in src/brands/);
# the webinar follow-up flow (the CRM's own webinar sequences); a custom sequence; a full cold calendar invite; and the
# three Tantra plans. Deadline, code and prices come from the funnel config so the hub and /tantra-plans/ always agree.
# After the deadline the block stays; only the Pro discount (price, 25% tag, code, countdown) goes (?state=expired shows that state).
TP = json.loads((HERE.parent / '_shared' / 'funnel-config.json').read_text())['tantra_plans']
BRANDS = {p.stem: 'data:image/svg+xml;base64,' + __import__('base64').b64encode(p.read_bytes()).decode() for p in (SRC / 'brands').glob('*.svg')}

def brand(name, alt, size=22):
    return f'<img class="bl" src="{BRANDS[name]}" alt="{esc(alt)}" width="{size}" height="{size}">'

def engine_offer():
    pro, club = TP['pro'], TP['club_100k']
    site = 'https://webinar.sellwithtantra.com' + TP['path']
    utm = '?utm_source=bonus-hub&utm_medium=bonus04&utm_campaign=tantra-plans'
    channels = [
        ('google-gmail', 'Gmail', 'Unlimited mailboxes, warmed up'),
        ('outlook', 'Outlook', 'Email from your Microsoft inbox'),
        ('google-calendar', 'Google Calendar', 'Cold invites that land on the calendar'),
        ('microsoft-icon', 'Microsoft 365', 'Invites on Outlook calendars too'),
        ('linkedin-icon', 'LinkedIn', 'Connection requests and messages'),
        ('whatsapp-icon', 'WhatsApp', 'Personal messages and reminders'),
    ]
    ch = ''.join(f'<li>{brand(i, n, 28)}<b>{n}</b><span>{d}</span></li>' for i, n, d in channels)
    # The webinar sequences are the ones live in the Tantra CRM for this webinar (registered, survey done, attended, missed).
    flow = [
        ('Registers', 'The moment they sign up', [('google-gmail', 'Confirmation email'), ('whatsapp-icon', 'WhatsApp with their join link'), ('google-calendar', 'Calendar hold')], 'v'),
        ('Before the session', 'Day before, hour before, going live', [('google-gmail', 'Reminder emails'), ('whatsapp-icon', 'WhatsApp reminders'), (None, 'SMS at go time')], 'v'),
        ('Attended', 'Stayed for the offer', [('google-gmail', 'Bonuses delivered'), ('whatsapp-icon', 'Book-a-call nudge')], 'g'),
        ('Missed it', 'No-show or left early', [('google-gmail', 'Replay link'), ('whatsapp-icon', 'Replay reminder'), (None, 'SMS before the replay closes')], 'r'),
    ]
    def step(lg, t):
        icon = brand(lg, '', 16) if lg else '<span class="sms">SMS</span>'
        return f'<li>{icon}<span>{t}</span></li>'
    fl = ''.join(f'<li class="wf__n wf__n--{tone}"><p class="wf__k">{k}</p><p class="wf__t">{t}</p><ul>{"".join(step(a, b) for a, b in steps)}</ul></li>' for k, t, steps, tone in flow)
    seq = [
        ('Day 0', 'google-calendar', 'Cold calendar invite', 'Lands on their calendar for Thursday 11:00', ''),
        ('Day 0', 'google-gmail', 'Email: the why behind the invite', 'Sent from a warmed-up mailbox', ''),
        ('Day 1', 'linkedin-icon', 'LinkedIn connection request', 'With a short personal note', 'If not accepted the invite'),
        ('Day 2', 'whatsapp-icon', 'WhatsApp message', 'One line and the join link', 'If no reply'),
        ('Day 3', 'google-gmail', 'Email: last call', 'Then the sequence stops', 'If still no reply'),
    ]
    sq = ''.join(f'<li><span class="sq__d">{d}</span>{brand(lg, "", 20)}<div><b>{t}</b><small>{s}</small></div>{f"<em>{c}</em>" if c else ""}</li>' for d, lg, t, s, c in seq)
    plans = f'''<div class="pls">
      <a class="pl pl--ent" href="{site}enterprise/{utm}"><span class="pl__k">Done for you</span><b>Tantra Enterprise</b><span class="pl__p">Built, live and bringing in revenue</span><span class="pl__c">Join the $5M ARR Club</span></a>
      <a class="pl pl--club" href="{site}100k-mrr-club/{utm}"><span class="pl__k">Build it with us</span><b>The 100K MRR Club</b><span class="pl__p">{esc(club['prices']['USD'])} {esc(club['per'])}</span><span class="pl__c">Apply for access</span></a>
      <a class="pl pl--pro" href="{site}pro/{utm}"><span class="pl__k">Run it yourself</span><b>Tantra Pro</b><span class="pl__p"><span data-deal><s>${pro['list_usd']}</s> ${pro['price_usd']} a month</span><span data-after>${pro['list_usd']} a month</span></span><span class="pl__c">Start {pro['trial_days']} days free</span></a>
    </div>'''
    return f'''<section class="eng" id="engine" data-deadline="{TP['deadline_utc']}" aria-labelledby="eng-h">
    <div class="eng__top">
      <p class="eng__badge">Bonus 04 · Webinar attendees only</p>
      <div class="cd" data-deal aria-live="off"><p class="cd__l">This offer ends in</p><div class="cd__row"><span><b data-cd="d">03</b><i>days</i></span><span><b data-cd="h">00</b><i>hours</i></span><span><b data-cd="m">00</b><i>min</i></span><span><b data-cd="s">00</b><i>sec</i></span></div><p class="cd__w">{esc(TP['deadline_label'])}</p></div>
    </div>
    <div class="eng__hero">
      <div>
        <h2 id="eng-h">The engine that filled this webinar is yours. <span>Free for {pro['trial_days']} days.</span></h2>
        <p class="eng__lead">Email, LinkedIn, WhatsApp and cold calendar invites, run from one place, with every registrant followed up on autopilot. <span data-deal>Start before the timer hits zero and you pay <b>${pro['price_usd']} a month instead of ${pro['list_usd']}</b>, 25% off.</span><span data-after>Start free today, then <b>${pro['list_usd']} a month</b>. Cancel any time.</span></p>
        <div class="eng__cta"><a class="btn btn--primary btn--lg" href="{site}{utm}">See the Tantra plans</a><a class="eng__alt" href="{site}pro/{utm}">Start my {pro['trial_days']}-day free trial</a></div>
      </div>
      <div class="price"><p class="price__k"><span data-deal>Tantra Pro, webinar price</span><span data-after>Tantra Pro</span></p><p class="price__n"><s data-deal>${pro['list_usd']}</s><b data-deal>${pro['price_usd']}</b><b data-after>${pro['list_usd']}</b><small>/month</small></p><p class="price__off"><span data-deal>25% off · </span>{pro['trial_days']} days free · cancel any time</p>{f'<p class="price__code" data-deal>Code <code>{esc(TP["coupon_code"])}</code></p>' if TP.get('coupon_code') else ''}</div>
    </div>

    <div class="blk"><p class="blk__k">01 · Omnichannel outreach</p><h3>Every channel your buyers live in, from one engine</h3>
      <ul class="chs">{ch}</ul></div>

    <div class="blk"><p class="blk__k">02 · Webinar integration</p><h3>Every registrant gets the right follow-up, on the right channel, by itself</h3>
      <p class="blk__p">The same sequences run this webinar: Tantra reads who registered, who showed up and who missed it, and sends each person the message that fits.</p>
      <ol class="wf">{fl}</ol></div>

    <div class="blk blk--split"><div><p class="blk__k">03 · Custom sequences</p><h3>Design your own follow-up, step by step</h3>
      <p class="blk__p">Mix calendar invites, email, LinkedIn and WhatsApp in one sequence. Set the delay for each step and the condition that moves people on, and Tantra stops the moment someone replies or accepts.</p></div>
      <div class="sq"><div class="sq__bar"><span>Sequence</span><b>Webinar invite: VP Sales, UK</b><i>Active</i></div><ol>{sq}</ol></div></div>

    <div class="blk blk--cal"><div class="cal__copy"><p class="blk__k blk__k--gold">04 · The only app in the world that does this</p><h3>Cold calendar invites that land on the calendar, not in the inbox</h3>
      <ul class="cal__pts"><li><b>Seen where the day is planned.</b> The invite sits on their Google or Outlook calendar with your time already blocked.</li><li><b>Every answer tracked.</b> Yes, Maybe and No come back into Tantra as replies you can act on.</li><li><b>Follow-up that fits the answer.</b> A Yes gets reminders, a Maybe gets a nudge, a No stops the sequence.</li></ul></div>
      <div class="gev" aria-label="A cold calendar invite as it appears in Google Calendar">
        <div class="gev__top">{brand('google-calendar', 'Google Calendar', 20)}<span>Google Calendar</span><i>Invitation</i></div>
        <div class="gev__body">
          <p class="gev__t"><span class="gev__sw"></span>How 400+ Brands Use AI Funnels to Generate $100K to $300K Monthly</p>
          <p class="gev__when">Thursday, 19 November · 11:00 to 12:00<br><small>United Kingdom time · does not repeat</small></p>
          <a class="gev__join" tabindex="-1">{brand('google-meet', 'Google Meet', 18)}Join with Google Meet</a>
          <ul class="gev__rows">
            <li><span class="gev__i">⏰</span>Reminders: 1 day before, 30 minutes before</li>
            <li><span class="gev__i">✉</span>Organiser: Adi, Tantra</li>
            <li><span class="gev__i">≡</span>A 60-minute live build of the AI webinar funnel: traffic, registration, nurture, the live session and the follow-up that books calls.</li>
          </ul>
          <div class="gev__guests"><p>3 guests <small>1 yes, 2 awaiting</small></p><ul><li><span class="av">A</span>Adi <small>Organiser</small></li><li><span class="av av--2">Y</span>You <small>Awaiting</small></li><li><span class="av av--3">T</span>Your team <small>Awaiting</small></li></ul></div>
          <div class="gev__rsvp"><span>Going?</span><b>Yes</b><i>No</i><i>Maybe</i></div>
        </div>
      </div></div>

    <div class="blk blk--plans"><p class="blk__k">Choose how you want it built</p><h3>Three Tantra plans<span data-deal>, at webinar prices until the timer ends</span></h3>{plans}</div>
  </section>
  <script>
  (function(){{var s=document.getElementById('engine'),end=Date.parse(s.dataset.deadline),q=function(k){{return s.querySelector('[data-cd='+k+']');}},p=function(n){{return (n<10?'0':'')+n;}};
  function t(){{var ms=end-Date.now();if(/[?&]state=expired/.test(location.search))ms=-1;if(ms<=0){{s.classList.add('is-over');return;}}
  q('d').textContent=p(Math.floor(ms/864e5));q('h').textContent=p(Math.floor(ms/36e5)%24);q('m').textContent=p(Math.floor(ms/6e4)%60);q('s').textContent=p(Math.floor(ms/1e3)%60);}}
  t();setInterval(t,1000);}})();
  </script>'''

def hub():
    body = f'''<main id="main" class="hub"><div class="hub__in">
  <p class="hub__k">Your webinar bonuses</p>
  <h1>Build any B2B funnel, then let AI write every piece of it.</h1>
  <p class="hub__lead">All three bonuses from the webinar are here. Start with the playbook: it walks you through every task, in order, for the funnel you choose. Use the library and its prompts whenever a task asks you to write an element.</p>
  <div class="hub__books">
    <a class="book" href="/playbook/"><img src="/assets/img/playbook-a.webp?v={V}" alt="Cover: The $1MN+ B2B RevOps Playbook" width="800" height="1200"><div><p class="book__n">Bonus 01</p><h2>The $1MN+ B2B RevOps Playbook</h2><p>Every task to plan, build, launch and run one of eight funnel types, step by step, with the prompt for each build.</p><span class="btn btn--primary">Open the playbook</span></div></a>
    <a class="book" href="/library/"><img src="/assets/img/prompts-a.webp?v={V}" alt="Cover: The $1MN+ AI Funnel Prompt Library" width="800" height="1200"><div><p class="book__n">Bonus 02</p><h2>The $1MN+ AI Funnel Prompt Library</h2><p>Real funnel elements from B2B brands, sorted by stage, industry and offer, each with a prompt that rebuilds it for your brand in any AI assistant.</p><span class="btn btn--primary">Open the library</span></div></a>
    <a class="book" id="calc" href="https://webinar.sellwithtantra.com/calculator/"><img src="/assets/img/calculator-a.jpg?v={V}" alt="Cover: AI RevOps Revenue Calculator" width="800" height="1200"><div><p class="book__n">Bonus 03</p><h2>Your AI RevOps Revenue Calculator</h2><p>The traffic, the KPI at every stage and the revenue your funnel needs, built from your own survey answers.</p><span class="btn btn--primary">Open my calculator</span></div></a>
  </div>
  {engine_offer()}
  <script>
  // Bonus 03 is personal: the bonus link carries the person's calculator answers after #p=, kept on this device for later visits.
  (function(){{var m=location.hash.match(/[#&]p=([^&]+)/),k='tb_calc_p',p=null;
  try{{if(m){{p=m[1];localStorage.setItem(k,p);history.replaceState(null,'',location.pathname);}}else p=localStorage.getItem(k);}}catch(e){{}}
  if(p)document.getElementById('calc').href='https://webinar.sellwithtantra.com/calculator/#p='+p;}})();
  </script>
  <p class="hub__foot">Bookmark this page. Your access stays on this device for six months. <a href="/__logout">Sign out</a></p>
</div></main>'''
    return page('Your Webinar Bonuses', 'hub', body, css=['hub.css'])

def library_page(data):
    n_el, n_ty = len(data['elements']), sum(len(c['types']) for c in data['categories'])
    body = f'''<main id="main" class="lib">
  <div class="lib__top"><div><h1>The $1MN+ AI Funnel Prompt Library</h1><p>{n_el} real funnel elements from {len(data['brands'])} B2B funnels, in {n_ty} types that follow the playbook. Read an example, then copy its prompt: your AI assistant rebuilds it for your brand.</p></div><a class="btn" href="/prompts/#setup">Start with the setup prompt</a></div>
  <div class="bar2"><div class="seg seg--i" role="group" aria-label="Industry"></div><select class="sel sel--o" aria-label="Offer type"></select><input class="search" type="search" placeholder="Search every element" aria-label="Search every element"></div>
  <div class="panes">
    <aside class="rail" aria-label="Element types"><nav></nav></aside>
    <section class="col" aria-label="Examples"><select class="sel picker" aria-label="Element type"></select><div class="list" aria-live="polite"></div></section>
    <section class="pv" aria-label="Preview" aria-live="polite"></section>
  </div>
</main>'''
    return page('The $1MN+ AI Funnel Prompt Library', 'library', body, css=['library.css'], js=['library.js'])

def prompts_page(prompts, data):
    present = {e['type'] for e in data['elements']}
    tools = [('ChatGPT', 'Projects: New project, paste the setup prompt into the project instructions, upload your Funnel Brief as a file.'),
             ('Claude', 'Projects: Create project, paste the setup prompt into the project instructions, add your Funnel Brief to the project knowledge.'),
             ('Gemini', 'Gems: New Gem, paste the setup prompt as the instructions, add your Funnel Brief as a knowledge file.'),
             ('Grok', 'Projects, or a new chat with the setup prompt as the first message, then attach your Funnel Brief.'),
             ('Codex, Claude Code or Cursor', 'Make a folder, save the setup prompt as AGENTS.md (Codex, Cursor) or CLAUDE.md (Claude Code), and save your Funnel Brief as funnel-brief.md next to it.'),
             ('Any other assistant', 'Paste the setup prompt and your filled Funnel Brief as the first message of a new chat, and keep using that chat.')]
    tl = ''.join(f'<li><b>{esc(a)}</b>{esc(b)}</li>' for a, b in tools)
    ex = '"""\n[FILL: paste one example from the library here, or press Prompt on an example in the library to get this filled in]\n"""'
    by_cat = []
    for c in data['categories']:
        rows = []
        for t in c['types']:
            if t['id'] not in prompts['types']: continue
            body = prompts['types'][t['id']]['prompt'].replace('{{EXAMPLE}}', ex)
            link = f'<a href="/library/#t={t["id"]}">See examples</a>' if t['id'] in present else ''
            rows.append(f'<div class="prow"><div class="prow__h"><b>{esc(t["name"])}</b>{link}<button class="btn btn--sm btn--primary" data-copy-raw>Copy prompt</button></div><details><summary>Read the prompt</summary>{prompt_box(t["name"] + " prompt", body)}</details></div>')
        if rows: by_cat.append(f'<h3 class="pp__cat">{esc(c["name"])}</h3><div class="plist">{"".join(rows)}</div>')
    body = f'''<main id="main" class="pp">
  <h1>The AI prompts</h1>
  <p class="lead">One setup prompt turns your AI assistant into a funnel copywriter that knows your business. Then one prompt per funnel element writes it for your offer, your buyer and your links, following a proven template.</p>
  <h2 id="setup">Step 1: The setup prompt</h2>
  <p>Run it once per funnel, with your Funnel Brief filled in. Every element prompt after it relies on it.</p>
  {prompt_box('Setup prompt', prompts['setup'])}
  <h2 id="where">Step 2: Where to paste it</h2>
  <ul class="tools">{tl}</ul>
  <h2 id="elements">Step 3: One prompt per element</h2>
  <p>Each prompt holds the element's full template. Fill every <span class="fill" style="color:#92400e;background:#fef3c7">[FILL: ...]</span>. In the <a href="/library/">library</a>, the Prompt button on any example gives you the same prompt with that example already inside.</p>
  {''.join(by_cat)}
</main>'''
    return page('The AI prompts', 'prompts', body, css=['library.css'])

def main():
    for d in ('playbook', 'library', 'prompts'): (SITE / d).mkdir(parents=True, exist_ok=True)
    for f in SRC.glob('*.*'): shutil.copy(f, SITE / 'assets' / f.name)
    data = library_data()
    data['prompts'] = load_prompts()
    types = {t: v[1] for t, v in TYPES.items()}
    pb, n_tasks = build_playbook(types, {e['type'] for e in data['elements']})
    (SITE / 'playbook' / 'index.html').write_text(pb)
    (SITE / 'index.html').write_text(hub())
    (SITE / 'library' / 'index.html').write_text(library_page(data))
    (SITE / 'library' / 'data.json').write_text(json.dumps(data, ensure_ascii=False))
    (SITE / 'prompts' / 'index.html').write_text(prompts_page(data['prompts'], data))
    (SITE / '404.html').write_text(page('Not found', 'hub', '<main id="main" class="hub"><div class="hub__in"><h1>That page does not exist.</h1><p><a href="/">Back to your bonuses</a></p></div></main>', css=['hub.css']))
    bad = [k for k, v in data['prompts']['types'].items() if DASH.search(v['prompt'])] + (['setup'] if DASH.search(data['prompts']['setup']) else [])
    if bad: raise SystemExit('dash in prompts: ' + ', '.join(bad))
    print(f'built v{V}: {len(data["elements"])} elements, {len(data["brands"])} brands, {n_tasks} playbook tasks, {len(data["prompts"]["types"])} element prompts')

if __name__ == '__main__':
    main()
