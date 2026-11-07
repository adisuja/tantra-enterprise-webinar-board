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
    ('foundation', 'Foundations', 'The documents every funnel element is written from.'),
    ('traffic', 'Stage 1: Traffic', 'Outreach, event pages and ads that bring cold buyers to your page.'),
    ('landing', 'Stage 2: Landing and Sign-Up', 'The pages that turn a click into a registrant.'),
    ('nurture', 'Stage 3: Reminders and Nurture', 'What gets a registrant to show up.'),
    ('conversion', 'Stage 4: Conversion Mechanism', 'The session, script and live engagement that make the offer.'),
    ('sales', 'Stage 5: Follow-Up and Close', 'Everything after the session: attendees, no-shows, replays and sales calls.'),
    ('content', 'Stage 6: Content and 52-Week Growth', 'Posts and newsletters that keep the list warm all year.'),
]
TYPES = {  # id: (category, name, description)
    'company_overview': ('foundation', 'Company Overview', 'What the company does, for whom and why it is different, as briefed to the team.'),
    'icp': ('foundation', 'Ideal Customer Profile', 'The accounts and people the funnel is built to reach.'),
    'buyer_persona': ('foundation', 'Buyer Persona', 'The person the copy speaks to: goals, pains, objections and triggers.'),
    'targeting_criteria': ('foundation', 'Targeting and Prospecting Criteria', 'The list filters: titles, industries, sizes and regions.'),
    'job_titles': ('foundation', 'Job Title Lists', 'Exact titles used as list filters.'),
    'positioning': ('foundation', 'Positioning Document', 'How the offer is framed against the alternatives.'),
    'tone_of_voice': ('foundation', 'Tone of Voice', 'How the brand sounds, and how it never sounds.'),
    'brand_voice_prompt': ('foundation', 'Brand Voice Prompt', 'A prompt that teaches an AI assistant the brand voice.'),
    'profile_branding': ('foundation', 'LinkedIn Profile Branding', 'Headline, about section and banner copy for the people who send outreach.'),
    'offer_doc': ('foundation', 'Offer Document', 'The offer, its components and its price.'),
    'title_bank': ('foundation', 'Event Title Bank', 'Tested titles for the session or event.'),
    'cold_email_sequence': ('traffic', 'Cold Email Sequences', 'Multi-step cold email threads that invite named buyers.'),
    'cold_calendar_invite': ('traffic', 'Cold Calendar Invites', 'Invite titles and descriptions that land in a prospect calendar.'),
    'linkedin_outreach_sequence': ('traffic', 'LinkedIn Outreach Sequences', 'Connection notes and the messages that follow acceptance.'),
    'linkedin_event_page': ('traffic', 'LinkedIn Event Pages', 'The event title and description on LinkedIn.'),
    'webinar_platform_event_page': ('traffic', 'Webinar Platform Event Pages', 'The registration page copy on the webinar platform.'),
    'event_banner_copy': ('traffic', 'Event Banner Copy', 'The words on event and profile banners.'),
    'ad_copy': ('traffic', 'Ad Copy', 'Paid ad headlines, primary text and calls to action.'),
    'ad_plan': ('traffic', 'Ad Plans', 'Campaign structure, audiences and budgets.'),
    'lead_gen_form': ('traffic', 'Lead Gen Forms', 'In-platform lead forms for paid social.'),
    'giveaway_asset': ('traffic', 'Giveaway Assets', 'Free resources offered to earn the registration.'),
    'event_outreach_sequence': ('traffic', 'Event Outreach Sequences', 'Outreach around an in-person or third-party event.'),
    'landing_page_long': ('landing', 'Landing Pages (Long Form)', 'Full registration pages, section by section.'),
    'landing_page_short': ('landing', 'Landing Pages (Short Form)', 'Short registration pages for warm traffic.'),
    'registration_page': ('landing', 'Registration Pages', 'Platform registration page copy.'),
    'reverse_squeeze_page': ('landing', 'Reverse Squeeze Page Scripts', 'Video-first page scripts that teach before they ask.'),
    'website_page': ('landing', 'Website Pages', 'Supporting website copy.'),
    'case_study': ('landing', 'Case Studies', 'Client stories used on pages, in emails and in the session.'),
    'testimonials': ('landing', 'Testimonials', 'Client words used as proof.'),
    'confirmation_email': ('nurture', 'Confirmation Emails', 'The message that lands the moment someone registers.'),
    'reminder_email_sequence': ('nurture', 'Reminder Email Sequences', 'Timed reminders before the session.'),
    'reminder_whatsapp': ('nurture', 'WhatsApp Reminders', 'Short reminder messages on WhatsApp.'),
    'promo_email_sequence': ('nurture', 'Promotional Email Sequences', 'Emails that promote the event to an existing list.'),
    'webinar_outline': ('conversion', 'Session Outlines', 'The structure of the live session, section by section.'),
    'webinar_script': ('conversion', 'Session Scripts', 'Word-for-word talk tracks for the session.'),
    'deck_outline': ('conversion', 'Deck Outlines', 'Slide-by-slide deck plans.'),
    'bonus_slide': ('conversion', 'Bonus Slides', 'The slide that stacks the bonuses on the offer.'),
    'start_end_slide': ('conversion', 'Start and End Slides', 'Holding slides before and after the session.'),
    'chat_prompts': ('conversion', 'Chat Prompts', 'Questions posted in chat to keep the room engaged.'),
    'polls': ('conversion', 'Live Polls', 'Polls that segment the room and surface buyers.'),
    'live_dms': ('conversion', 'Live Direct Messages', 'One-to-one messages sent during the session.'),
    'seeded_qa': ('conversion', 'Seeded Q&A', 'Questions the team asks openly to start the Q&A.'),
    'attendee_followup': ('sales', 'Attendee Follow-Ups', 'What attendees receive after the session.'),
    'noshow_followup': ('sales', 'No-Show Follow-Ups', 'What registrants who missed it receive.'),
    'replay_email': ('sales', 'Replay Emails', 'Emails that deliver the recording.'),
    'remarketing_email': ('sales', 'Remarketing Emails', 'Emails that bring past contacts back.'),
    'whatsapp_followup': ('sales', 'WhatsApp Follow-Ups', 'Post-session follow-ups on WhatsApp.'),
    'sales_call_reminders': ('sales', 'Sales Call Reminders', 'Reminders before a booked sales call.'),
    'sales_call_followups': ('sales', 'Sales Call Follow-Ups', 'Follow-ups after a sales call.'),
    'poll_reengagement': ('sales', 'Poll Re-Engagement', 'Messages to people based on their poll answers.'),
    'cohort_email': ('sales', 'Cohort Emails', 'Emails that sell into a cohort or programme.'),
    'rejection_downsell': ('sales', 'Downsell Emails', 'A lighter offer for people who declined.'),
    'linkedin_post': ('content', 'LinkedIn Posts', 'Posts from founder and team profiles.'),
    'newsletter': ('content', 'Newsletters', 'Weekly or monthly newsletters to the list.'),
    'blog_article': ('content', 'Blog Articles', 'Long-form articles.'),
    'content_prompt': ('content', 'Content Prompts', 'Prompts used to produce content at scale.'),
    'content_calendar': ('content', 'Content Calendars', 'Planned posting schedules.'),
}
DASH_FIX = [(re.compile(r'(?<=\d)\s?[–—]\s?(?=\d)'), ' to '), (re.compile(r'\s+[–—]\s+'), ', '), (re.compile('[–—]'), ', ')]

def undash(o):
    if isinstance(o, dict): return {k: undash(v) for k, v in o.items()}
    if isinstance(o, list): return [undash(x) for x in o]
    if isinstance(o, str):
        for rx, rep in DASH_FIX: o = rx.sub(rep, o)
        return o
    return o

def offer_group(t):
    t = t.lower()
    if 'software' in t: return 'Software + Service' if any(w in t for w in ('service', 'implementation', 'pilot', 'done')) else 'Software'
    if any(w in t for w in ('training', 'programme', 'program', 'course', 'certification')): return 'Training Programme'
    if 'consult' in t or 'coaching' in t: return 'Consulting'
    return 'Done-for-You Service'

def library_data():
    if not ANON.exists():
        return json.loads(DATA_SNAPSHOT.read_text())
    brands, elements = {}, []
    for d in sorted(p for p in ANON.iterdir() if p.is_dir()):
        b = json.loads((d / '_brand.json').read_text()) if (d / '_brand.json').exists() else {}
        code = 'b' + str(len(brands) + 1)
        brands[code] = {k: b.get(k, '') for k in ('label', 'industry', 'niche', 'offer', 'offer_type', 'audience', 'geography', 'funnels_used', 'conversion_mechanism')}
        brands[code]['offer_type'] = offer_group(b.get('offer_type', ''))
        for f in sorted(d.glob('*.json')):
            if f.name.startswith('_'): continue
            el = json.loads(f.read_text())
            if el.get('type') not in TYPES: continue
            keep = {k: el[k] for k in ('title', 'type', 'funnel', 'context', 'variants', 'sections') if el.get(k)}
            keep['id'] = f'{code}-{len(elements) + 1}'; keep['brand'] = code
            if not re.sub(r'\[[^\]]*\]|[^A-Za-z]', '', keep.get('title', '')):   # title was only a placeholder after anonymising
                keep['title'] = TYPES[el['type']][1].rstrip('s') + (': ' + keep['title'] if keep.get('title') else '')
            keep['category'] = TYPES[el['type']][0]
            elements.append(undash(keep))
    order = {t: i for i, t in enumerate(TYPES)}
    elements.sort(key=lambda e: (order[e['type']], e['brand']))
    industries = sorted({b['industry'] for b in brands.values() if b.get('industry')})
    offers = sorted({b['offer_type'] for b in brands.values() if b.get('offer_type')})
    cats = [{'id': c, 'name': n, 'desc': d, 'types': [{'id': t, 'name': v[1], 'desc': v[2]} for t, v in TYPES.items() if v[0] == c]} for c, n, d in CATEGORIES]
    data = {'brands': undash(brands), 'elements': elements, 'categories': cats, 'industries': industries, 'offers': offers, 'funnelNames': {**FN, 'reverse-squeeze': 'Reverse Squeeze Page', 'book-a-call': 'Book a Call', 'product-launch': 'Product Launch'}}
    DATA_SNAPSHOT.parent.mkdir(exist_ok=True)
    DATA_SNAPSHOT.write_text(json.dumps(data, ensure_ascii=False))
    return data

def load_prompts():
    """content/prompts/setup.md is the setup prompt; content/prompts/types.md holds '## <type_id> | <name>' sections."""
    setup = (CONTENT / 'prompts' / 'setup.md').read_text().strip() if (CONTENT / 'prompts' / 'setup.md').exists() else ''
    types = {}
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

def hub():
    body = f'''<main id="main" class="hub"><div class="hub__in">
  <p class="hub__k">Your webinar bonuses</p>
  <h1>Build any B2B funnel, then let AI write every piece of it.</h1>
  <p class="hub__lead">Two of the three bonuses from the webinar are here. Start with the playbook: it walks you through every task, in order, for the funnel you choose. Use the library and its prompts whenever a task asks you to write an element.</p>
  <div class="hub__books">
    <a class="book" href="/playbook/"><img src="/assets/img/playbook-a.webp?v={V}" alt="Cover: The $1MN+ B2B RevOps Playbook" width="800" height="1200"><div><p class="book__n">Bonus 01</p><h2>The $1MN+ B2B RevOps Playbook</h2><p>Every task to plan, build, launch and run one of eight funnel types, step by step, with the prompt for each build.</p><span class="btn btn--primary">Open the playbook</span></div></a>
    <a class="book" href="/library/"><img src="/assets/img/prompts-a.webp?v={V}" alt="Cover: The $1MN+ AI Funnel Prompt Library" width="800" height="1200"><div><p class="book__n">Bonus 02</p><h2>The $1MN+ AI Funnel Prompt Library</h2><p>Real funnel elements from B2B brands, sorted by stage, industry and offer, each with a prompt that rebuilds it for your brand in any AI assistant.</p><span class="btn btn--primary">Open the library</span></div></a>
  </div>
  <p class="hub__foot">Bookmark this page. Your access stays on this device for six months. <a href="/__logout">Sign out</a></p>
</div></main>'''
    return page('Your Webinar Bonuses', 'hub', body, css=['hub.css'])

def library_page(data):
    body = '''<main id="main" class="lib">
  <div class="lib__hero"><div><h1>The <em>$1MN+</em> AI Funnel Prompt Library</h1><p>Real funnel elements we wrote for B2B brands, with every brand name removed. Pick an industry or offer, open an element type on the left, read the real examples, then copy the AI prompt that rebuilds it for your brand.</p></div><div class="lib__stats"></div></div>
  <ol class="steps3"><li><b>Set up once.</b> Paste the <a href="/prompts/#setup">setup prompt</a> into a new project in ChatGPT, Claude, Gemini, Grok or any assistant, and fill in your Funnel Brief.</li><li><b>Pick an element.</b> Choose the element type on the left, then open an example that fits your industry and offer.</li><li><b>Copy the AI prompt.</b> Press <b>Copy AI prompt with this example</b>, fill every [FILL: ...] and paste it into the same project.</li></ol>
  <div class="filters"></div>
  <div class="lib__grid">
    <aside class="rail"><button class="btn rail__toggle" aria-expanded="false"><span>Element types</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg></button><div class="rail__body"><input class="search" type="search" placeholder="Search every element" aria-label="Search every element"><nav aria-label="Element types"></nav></div></aside>
    <section class="list" aria-live="polite"><div id="list"></div></section>
  </div>
</main>'''
    return page('The $1MN+ AI Funnel Prompt Library', 'library', body, css=['library.css'], js=['library.js'])

def prompts_page(prompts, data):
    present = {e['type'] for e in data['elements']}
    tools = [('ChatGPT', 'Projects: New project, paste the setup prompt into the project instructions, upload your Funnel Brief as a file.'),
             ('Claude', 'Projects: Create project, paste the setup prompt into project instructions, add your Funnel Brief to project knowledge.'),
             ('Gemini', 'Gems: New Gem, paste the setup prompt as the instructions, add your Funnel Brief as a knowledge file.'),
             ('Grok', 'Projects (or a new chat with the setup prompt as the first message), then attach your Funnel Brief.'),
             ('Codex, Claude Code or Cursor', 'Make a folder, save the setup prompt as AGENTS.md (Codex, Cursor) or CLAUDE.md (Claude Code), and save your Funnel Brief as funnel-brief.md next to it.'),
             ('Any other assistant', 'Paste the setup prompt and your filled Funnel Brief as the first message of a new chat, and keep using that chat.')]
    tl = ''.join(f'<li><b>{esc(a)}</b>{esc(b)}</li>' for a, b in tools)
    by_cat = []
    for c in data['categories']:
        items = ''.join(f'<details><summary>{esc(t["name"])}<span>{f'<a href="/library/#t={t["id"]}">See examples</a>' if t["id"] in present else 'No library examples yet'}</span></summary><div>{prompt_box(t["name"] + " prompt", prompts["types"][t["id"]]["prompt"].replace("{{EXAMPLE}}", "REFERENCE EXAMPLE:" + chr(10) + chr(34) * 3 + chr(10) + "[FILL: paste one example from the library, or use Copy AI prompt with this example in the library]" + chr(10) + chr(34) * 3))}</div></details>' for t in c['types'] if t['id'] in prompts['types'])
        if items: by_cat.append(f'<h3 class="pp__cat">{esc(c["name"])}</h3><div class="plist">{items}</div>')
    body = f'''<main id="main" class="pp">
  <h1>The AI prompts</h1>
  <p class="lead">One setup prompt turns your AI assistant into a funnel copywriter that knows your brand. Then one prompt per funnel element rebuilds any example in the library for your offer, your buyer and your links.</p>
  <h2 id="setup">Step 1: The setup prompt</h2>
  <p>Run this once per brand. It holds your Funnel Brief and the rules every element follows, so each element prompt after it stays short.</p>
  {prompt_box('Setup prompt', prompts['setup'])}
  <h2 id="where">Step 2: Where to paste it</h2>
  <ul class="tools">{tl}</ul>
  <h2 id="elements">Step 3: One prompt per element</h2>
  <p>Fill every <span class="fill" style="color:#92400e;background:#fef3c7">[FILL: ...]</span>. In the <a href="/library/">library</a>, <b>Copy AI prompt with this example</b> on any example gives you the same prompt with that example already pasted in.</p>
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
