"""Round 7: proof wall on slide 9, a case card on every case study slide, and the layout faults from the full QA pass.
Data: cases.json and testimonials.json from the enterprise webinar workspace (read only). Testimonials are copied verbatim."""
import json, os, re
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = ROOT + '/src'
WS = '/home/user/tantra-enterprise-webinar-workspace/deliverables/13-15a-26-20-pages/src/data'
TESTI = json.load(open(WS + '/testimonials.json'))
TESTI = TESTI if isinstance(TESTI, list) else TESTI.get('testimonials', TESTI.get('items', TESTI))
if isinstance(TESTI, dict): TESTI = list(TESTI.values())


def read(p): return open(f'{S}/{p}').read()
def write(p, s): open(f'{S}/{p}', 'w').write(s)


def section(path, sid, new):
    s = read(path)
    m = re.search(r'<section class="slide" id="%s".*?</section>\n?' % re.escape(sid), s, re.S)
    if not m: raise SystemExit(f'section {sid} not found in {path}')
    write(path, s[:m.start()] + new.strip() + '\n' + s[m.end():])


def sub(path, pairs):
    s = read(path)
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:120]}')
        s = s.replace(a, b)
    write(path, s)


# ---------- case card (left column of a case study slide) ----------
CARD = {
    'growth-idea': dict(ph='shweta', name='Shweta', role='Founder &amp; CEO, Growth Idea',
                        what='UK business-coaching group for owner-led SMBs',
                        facts=[('Based in', 'London, UK'), ('Founded', '2008'), ('Team', '15+ coaches and staff'), ('Revenue', '$1.5MN to $1.9MN a year')]),
    'appster': dict(ph='tom-alfoldi', name='Tom Alfoldi', role='Founder &amp; CEO, Growth Factors by Appster',
                    what='Melbourne app development company',
                    facts=[('Based in', 'Melbourne, Australia'), ('Founded', '2011'), ('Team', '400 at peak'), ('Revenue', '$8MN to $25MN a year')]),
    'fintechcircle': dict(ph='susanne', name='Susanne', role='Founder &amp; Chair, FintechCircle',
                          what='London fintech network selling a board-readiness programme',
                          facts=[('Based in', 'London, UK'), ('Founded', '2014'), ('Team', '8 people'), ('Revenue', 'Under $25K a month at the start')]),
    'rhenus': dict(ph='jacek-dudkiewicz', name='Jacek Dudkiewicz', role='ex-Managing Director, Rhenus Automation',
                   what='Intelligent automation unit of the Rhenus Group: RPA, AI and process mining',
                   facts=[('Based in', 'Nadarzyn, Poland'), ('Founded', '2017'), ('Team', '200+ in the unit'), ('Revenue', '$100K to $500K a month at the start')]),
}


def ccard(cid, extra=''):
    c = CARD[cid]
    facts = ''.join(f'<dt>{k}</dt><dd{" class=\"rev\"" if k == "Revenue" else ""}>{v}</dd>' for k, v in c['facts'])
    return (f'<div class="ccard card"{extra}><div class="cx-top"><img class="cx-ph" src="assets/p/{c["ph"]}.webp" alt="{c["name"]}">'
            f'<div class="cx-id"><img class="cx-lg" src="assets/l/{cid}.webp" alt="{cid}"><span class="cx-nm">{c["name"]}</span>'
            f'<span class="cx-ti">{c["role"]}</span></div></div><p class="cx-what">{c["what"]}</p><dl class="cx-facts">{facts}</dl></div>')


# ---------- proof cards (3 x 2 grids) ----------
def pcard(lg, ph, name, role, what, n, lbl):
    return (f'<div class="pcard card"><div class="pc-top"><img class="pc-ph" src="assets/p/{ph}.webp" alt="{name}"><div class="pc-id">'
            f'<img class="pc-lg" src="assets/l/{lg}.webp" alt="{lg}"><span class="pc-nm">{name}</span><span class="pc-ro">{role}</span></div></div>'
            f'<span class="pc-what">{what}</span><div class="pc-m"><span class="n">{n}</span><span class="vl">{lbl}</span></div></div>')


REV = [
    ('cavli', 'ajit-thomas', 'Ajit Thomas', 'Co-founder &amp; CMO', 'Cellular IoT modules, San Jose', '$15MN', 'ARR, from $1.5MN'),
    ('appster', 'tom-alfoldi', 'Tom Alfoldi', 'CEO, Growth Factors by Appster', 'App development, Melbourne', '$25MN', 'ARR in 2 years, from $8MN'),
    ('quantum-scaling', 'alexander-gesell', 'Alexander Gesell', 'Founder &amp; Lead Coach', 'Webinar coaching, Tallinn', '$6MN', 'ARR in 3 years, from zero'),
    ('kadima', 'alan-stein', 'Alan Stein', 'Founder &amp; CEO', 'Career coaching, New York', '$1.8MN', 'ARR, from under $0.5MN'),
    ('wxrks', 'gabriel-fairman', 'Gabriel Fairman', 'Founder &amp; CEO', 'AI translation, California', '$5MN', 'ARR, from $2.5MN'),
    ('bamf', 'houston-golden', 'Houston Golden', 'Founder &amp; CEO', 'LinkedIn agency, Los Angeles', '$1MN+', 'ARR from one launch'),
]
PIPE = [
    ('rhenus', 'jacek-dudkiewicz', 'Jacek Dudkiewicz', 'ex-Managing Director', 'Enterprise automation, Poland', '50+', 'MQLs in 4 months'),
    ('fintechcircle', 'susanne', 'Susanne', 'Founder &amp; Chair', 'Fintech network, London', '17', 'sales calls in 3 episodes'),
    ('coinfirm', 'sachin-dutta', 'Sachin Dutta', 'ex-CMO, Coinfirm', 'Blockchain AML, London', '4 to 14', 'sales meetings a month'),
    ('salestherapy', 'vivek-vanwari', 'Vivek Vanwari', 'Founder', 'Sales mentoring, Chicago', '6', 'sales calls from webinar 1'),
    ('omniance', 'marc-eichner', 'Marc Eichner', 'Co-founder &amp; CEO', 'AI consulting, Germany', '1 to 8', 'inbound conversations a month'),
    ('ecommerce-platforms', 'catalin-zorzini', 'Catalin Zorzini', 'Founder', 'Software reviews, London', '7MN+', 'visits a year, 3.5x the goal'),
]
INDUSTRY = [
    ('cavli', 'ajit-thomas', 'Ajit Thomas', 'Co-founder &amp; CMO', 'Software and tech: IoT modules', '$15MN', 'ARR, from $1.5MN'),
    ('appster', 'tom-alfoldi', 'Tom Alfoldi', 'CEO, Growth Factors by Appster', 'Agencies: app development', '$25MN', 'ARR in 2 years'),
    ('growth-idea', 'shweta', 'Shweta', 'Founder &amp; CEO', 'Coaching and training', '80', 'sales calls from webinars'),
    ('neural-it', 'sailesh-paul', 'Sailesh Paul', 'Founder, President &amp; CEO', 'Consulting: legal services', '7x', 'more people live'),
    ('ecommerce-platforms', 'catalin-zorzini', 'Catalin Zorzini', 'Founder', 'Media and publishing', '7MN+', 'visits a year'),
    ('ikrshna', 'anand-kadakol', 'Anand Kadakol', 'Author', 'Authors: a book launch', '#1', 'on the Kindle Store in 3 weeks'),
]


def fcard(lg, ph, name, role, what, chips, rev, mets):
    ch = f'<span class="fc-facts">{" · ".join(chips)}</span><span class="fc-rev">{rev}</span>'
    ms = ''.join(f'<div><span class="n{" a-s" if i == 0 else ""}">{n}</span><span class="vl">{l}</span></div>' for i, (n, l) in enumerate(mets))
    return (f'<div class="fcard card"><div class="fc-top"><img class="fc-ph" src="assets/p/{ph}.webp" alt="{name}"><div class="fc-id">'
            f'<img class="fc-lg" src="assets/l/{lg}.webp" alt="{lg}"><span class="fc-nm">{name}, <span>{role}</span></span><span class="fc-what">{what}</span></div></div>'
            f'<div class="fc-lines">{ch}</div><div class="fc-m">{ms}</div></div>')


FEAT = [
    fcard('growth-idea', 'shweta', 'Shweta', 'Founder &amp; CEO', 'UK business-coaching group for owner-led SMBs',
          ['London, UK', 'since 2008', '15+ coaches and staff'], 'Revenue $1.5MN to $1.9MN a year',
          [('80', 'sales calls, 11 webinars'), ('765,105', 'people reached'), ('7 to 321', 'came live per webinar'), ('4', 'clients won')]),
    fcard('neural-it', 'sailesh-paul', 'Sailesh Paul', 'Founder, President &amp; CEO', 'Medical-record review and demand letters for US injury law firms',
          ['Hicksville, New York', 'since 2004', '220+ people'], 'Revenue $25K to $100K a month at the start',
          [('17 to 127', 'came live per webinar'), ('141,734', 'reached at law firms'), ('6', 'sales calls booked'), ('50,560', 'invites per webinar')]),
]

# ---------- testimonial wall (verbatim) ----------
def tw(t):
    lg = t['logo']
    lgt = '<span class="tw-lgt">Netwrk.ai</span>' if lg == 'netwrk' else ''
    q = (t.get('quote') or t.get('text')).strip()
    return (f'<div class="tw card"><div class="tw-top"><img class="tw-ph" src="assets/p/{t["photo"]}.webp" alt="{escape(t["name"])}"><div class="tw-id">'
            f'<span class="tw-nm">{escape(t["name"])}</span><span class="tw-ti">{escape(t["title"])}</span>'
            f'<span class="tw-lgr"><img class="tw-lg" src="assets/l/{lg}.webp" alt="{lg}">{lgt}</span></div></div><p class="tw-q">{escape(q)}</p></div>')


WALL = [t for t in TESTI if t['name'] != 'Tom Alfoldi']
assert len(WALL) == 8, len(WALL)
TW = ''.join(tw(t) for t in WALL)

LOGOS = ['growth-idea', 'fintechcircle', 'neural-it', 'cavli', 'appster', 'coinfirm', 'rhenus', 'kadima', 'wxrks', 'bamf', 'dataguard', 'omniance',
         'upgrad', 'licious', 'leapwork', 'merkle-science', 'salestherapy', 'quantum-scaling', '91springboard', 'springup', 'salesup', 'wowmakers',
         'iboson', 'imaginegrowth', 'ingwe', 'tripsalam', 'esya', 'ikrshna', 'myfels', 'hair-loss-revolution', 'ytc', 'unblock', 'ecomm-design',
         'matcha-tea', 'ecommerce-platforms', 'flabba']
for l in LOGOS: assert os.path.exists(f'{ROOT}/deck/assets/l/{l}.webp'), l
for t in WALL: assert os.path.exists(f'{ROOT}/deck/assets/p/{t["photo"]}.webp'), t['photo']

S9 = f'''
<section class="slide" id="s-working" data-title="The proof: 400+ brands" data-bg="dim" data-steps="4" data-reel="11">
  <h2 class="t" data-only="0" data-a="words">Don't take <span class="a">my word for it.</span></h2>
  <div class="fgrid" data-only="0" data-a="stagger" data-d=".4" data-st=".2">{''.join(FEAT)}</div>
  <h2 class="t" data-only="1" data-a="words">The <span class="a-s">revenue</span> it added.</h2>
  <div class="pgrid" data-only="1" data-a="stagger" data-d=".3" data-st=".08">{''.join(pcard(*r) for r in REV)}</div>
  <h2 class="t" data-only="2" data-a="words">The <span class="a">pipeline</span> it built.</h2>
  <div class="pgrid" data-only="2" data-a="stagger" data-d=".3" data-st=".08">{''.join(pcard(*r) for r in PIPE)}</div>
  <h2 class="t" data-only="3" data-a="words">In their <span class="a">own words.</span></h2>
  <div class="twall" data-only="3" data-a="fade" data-d=".3"><div class="mq-row tw-row"><div class="mq-track tw-track">{TW}{TW}</div></div></div>
  <h2 class="t" data-only="4" data-a="words"><span class="a">400+ brands.</span> 21+ countries.<br>47+ industries.</h2>
  <div class="lwall" data-only="4" data-a="stagger" data-d=".3" data-st=".02">{''.join(f'<div class="lw"><img src="assets/l/{l}.webp" alt="{l}"></div>' for l in LOGOS)}</div>
  <aside class="notes"><p><b>Minute 5. The proof, five clicks.</b> 1: Growth Idea and Neural IT. 2: the revenue it added. 3: the pipeline it built. 4: their words (the wall scrolls; read one). 5: the logos. Testimonials are verbatim; never trim or reword them.</p></aside>
</section>
'''
section('slides/a.html', 's-working', S9)

# ---------- slide 34: Tom ----------
TOMQ = next(t for t in TESTI if t['name'] == 'Tom Alfoldi')['quote'].strip().strip('“”"')
S34 = f'''
<section class="slide" id="s-voice" data-title="This is what having a system looks like" data-bg="dim" data-reel="11">
  {ccard('appster', ' data-a="rise" data-d=".2"')}
  <h2 class="t rt" style="font-size:80px" data-a="words" data-d=".3">This is what having <span class="a">a system</span> looks like.</h2>
  <div class="tq2 card" data-a="rise" data-d=".7"><p class="tq2-q">"{escape(TOMQ).replace("&#x27;Wow, I wouldn&#x27;t have written them myself.&#x27;", "<span class=\"a\">'Wow, I wouldn't have written them myself.'</span>").replace('&#x27;', "'")}"</p></div>
  <div class="rmets" data-a="stagger" data-d="1.2"><div><span class="n a-s">$25MN</span><span class="vl s">ARR in 2 years</span></div><div><span class="n">21%</span><span class="vl s">of revenue from a new consulting line</span></div><div><span class="n">10 to 60</span><span class="vl s">sales calls a month</span></div></div>
  <aside class="notes"><p><b>Minute 19.</b> Read the quote word for word. Then the numbers: Appster reached $25MN in ARR in two years, 21% of it from a new LinkedIn consulting line, and sales calls went from 10 to 60 a month.</p></aside>
</section>
'''
section('slides/b.html', 's-voice', S34)

# ---------- slide 47: Growth Idea, best webinar ----------
S47 = f'''
<section class="slide" id="s-proof2" data-title="Proof: a room full of buyers" data-bg="dim" data-reel="10">
  {ccard('growth-idea', ' data-a="rise" data-d=".2"')}
  <h2 class="t rt" style="font-size:80px" data-a="words" data-d=".4">99,859 invited. <span class="a-s">A room full of buyers.</span></h2>
  <div class="chain2" data-a="stagger" data-d=".9" data-st=".15">
    <div><span class="n">99,859</span><span class="vl s">reached</span></div>
    <div><span class="n">1,990</span><span class="vl s">registered</span></div>
    <div><span class="n">321</span><span class="vl s">came live</span></div>
    <div><span class="n a-s">25</span><span class="vl s">sales calls</span></div>
    <div><span class="n a-s">2</span><span class="vl s">clients</span></div>
  </div>
  <div class="mcmp rt2 card" data-a="rise" data-d="1.6">
    <div class="mc-r"><span class="vl s">First webinar</span><div class="cmp-bar"><i style="width:11.5%;background:var(--ember)"></i></div><span class="n a-e">0.23%</span></div>
    <div class="mc-r"><span class="vl s">Best webinar</span><div class="cmp-bar"><i style="width:100%;background:var(--signal)"></i></div><span class="n a-s">2.0%</span></div>
    <div class="mc-x"><span class="n a-s">8.6x</span><span class="vl s">the registration rate</span></div>
  </div>
  <span class="cap m" style="left:780px" data-a="fade" data-d="2">Measured · Growth Idea, best webinar, 28 Aug 2025</span>
  <aside class="notes"><p><b>Minute 27.</b> Shweta runs Growth Idea, a UK coaching group for owner-led businesses. First webinar: 12,898 reached, 30 registered, 7 live. Best: 99,859 reached, 1,990 registered, 321 live, 25 sales calls, 2 clients. 8.6 times the registration rate.</p></aside>
</section>
'''
section('slides/c.html', 's-proof2', S47)

# ---------- slide 61: FintechCircle ----------
S61 = f'''
<section class="slide" id="s-proof3" data-title="Proof: invites that kept growing" data-bg="dim" data-reel="10">
  {ccard('fintechcircle', ' data-a="rise" data-d=".2"')}
  <h2 class="t rt" style="font-size:80px" data-a="words" data-d=".4">From 1 call an episode <span class="a-s">to 9.</span></h2>
  <div class="fc-bars2 rt2" data-a="stagger" data-d=".9" data-st=".12">
    <div class="fcb"><span class="vl s">10,000</span><i style="height:26%"></i><span class="vl s">Ep 1</span></div>
    <div class="fcb"><span class="vl s">20,046</span><i style="height:52.6%"></i><span class="vl s">Ep 2</span></div>
    <div class="fcb"><span class="vl s">30,000</span><i style="height:78.7%"></i><span class="vl s">Ep 3</span></div>
    <div class="fcb"><span class="vl s">38,138</span><i style="height:100%"></i><span class="vl s">Ep 4</span></div>
  </div>
  <div class="fc-row rt2" data-a="stagger" data-d="1.5"><div><span class="n a-s">17</span><span class="vl s">sales calls in 3 episodes</span></div><div><span class="n">1 to 9</span><span class="vl s">calls per episode</span></div><div><span class="n">117</span><span class="vl s">came live, up from 59</span></div><div><span class="n">175</span><span class="vl s">programme applications</span></div></div>
  <span class="cap m" style="left:780px" data-a="fade" data-d="2">Measured · FintechCircle · bars: invites per episode</span>
  <aside class="notes"><p><b>Minute 33.</b> Susanne runs FintechCircle, a London fintech network. Episode one: 10,000 invites, 59 live, one call. Invites grew every episode to 38,138; calls went from 1 to 9 an episode, 17 across three episodes; 175 applied to the programme. No pipeline figure for this client.</p></aside>
</section>
'''
section('slides/d.html', 's-proof3', S61)

# ---------- slide 65: Rhenus, then industries ----------
S65 = f'''
<section class="slide" id="s-ceiling" data-title="Same machine. Bigger deals." data-bg="burst 520 640" data-steps="1" data-reel="9">
  <div class="hero dimmed" data-only="0" data-a="fade"><img src="img/ceiling.webp" alt="" class="kb"><div class="shade f"></div></div>
  {ccard('rhenus', ' data-only="0" data-a="rise" data-d=".2"')}
  <h2 class="t rt" data-only="0" data-a="words" data-d=".4">Same machine. <span class="a">Bigger deals.</span></h2>
  <div class="ceil4" data-only="0" data-a="stagger" data-d="1">
    <div class="card"><span class="n a-s">50+</span><span class="vl s">marketing-qualified leads in 4 months</span></div>
    <div class="card"><span class="n">3 to 15</span><span class="vl s">sales calls a month</span></div>
    <div class="card"><span class="n">60</span><span class="vl s">enterprise registrants per webinar</span></div>
    <div class="card"><span class="n">4x</span><span class="vl s">Jacek's LinkedIn following, to 6,000</span></div>
  </div>
  <span class="cap d" style="left:780px" data-only="0" data-a="fade" data-d="1.8">Rhenus Automation case study, as published on our pages</span>
  <h2 class="t" data-only="1" data-a="words">And it works <span class="a">across industries.</span></h2>
  <div class="pgrid" data-only="1" data-a="stagger" data-d=".3" data-st=".08">{''.join(pcard(*r) for r in INDUSTRY)}</div>
  <aside class="notes"><p><b>Minute 36.</b> Jacek ran the enterprise automation unit of the Rhenus Group. Deals came from the network and trade fairs. Same machine, outreach and webinars for enterprise buyers: 50+ MQLs in 4 months, sales calls from 3 to 15 a month, 60 enterprise registrants per webinar. Click: one client per industry.</p></aside>
</section>
'''
section('slides/e.html', 's-ceiling', S65)

# ---------- slide 63: who the numbers belong to ----------
sub('slides/e.html', [
    ('<div class="vis stages" style="top:360px">',
     '<div class="cstrip" data-a="fade" data-d=".5"><img src="assets/l/growth-idea.webp" alt="Growth Idea"><span>Shweta\'s UK coaching group, London</span><span class="dot"></span><span class="a-s">Revenue $1.5MN to $1.9MN a year</span></div>\n  <div class="vis stages" style="top:440px">'),
    ("That's all three steps.", "That's all three phases."),
])

# ---------- slide 18: the nine mechanisms fit the slide ----------
sub('slides/a.html', [
    ('<span class="vl s">One live session that teaches, then makes one offer</span>', '<span class="vl s">One live session, then one offer</span>'),
    ('<span class="vl s">A few live sessions where they build with you</span>', '<span class="vl s">A few live sessions, built with you</span>'),
    ('<span class="vl s">Daily tasks for a few days, the offer on the last</span>', '<span class="vl s">Daily tasks, then the offer</span>'),
    ('<span class="vk">Courses and launches</span><span class="vl s">Value videos, then a cart that opens and closes</span>', '<span class="vk">Course launches</span><span class="vl s">Free videos, then a cart that closes</span>'),
    ('<span class="vl s">Qualifying questions, then a consultative call</span>', '<span class="vl s">Qualifying questions, then a call</span>'),
    ('<span class="vl s">A free resource that earns the email</span>', '<span class="vl s">A free guide that earns the email</span>'),
    ('<span class="vl s">A free group that teaches; the keenest step up</span>', '<span class="vl s">A free group; the keenest step up</span>'),
    ('<span class="vl s">Value posts build trust; warm DMs book calls</span>', '<span class="vl s">Value posts, then warm DMs</span>'),
    # slide 19: title and body no longer collide
    ('<h2 class="t" style="top:240px;width:960px" data-only="0" data-a="words">End-to-end AI orchestration <span class="a-e">and growth.</span></h2>',
     '<h2 class="t" style="top:190px;width:960px" data-only="0" data-a="words">End-to-end AI orchestration <span class="a-e">and growth.</span></h2>'),
    ('<p class="b" style="top:520px;width:800px" data-only="0" data-a="rise" data-d=".6">Tools that don\'t talk.',
     '<p class="b" style="top:580px;width:800px" data-only="0" data-a="rise" data-d=".6">Tools that don\'t talk.'),
])

# ---------- slide 23: the grid for the stages, then the OS under all six ----------
s = read('slides/a.html')
m = re.search(r'<div class="stages6" data-a="stagger" data-d=".6" data-st=".1">(.*?)</div></div>\n', s, re.S)
cells = re.findall(r'<div class="stg6 card"><span class="n s6-n">(\d+)</span><span class="vk">([^<]+)</span><span class="vl s">([^<]+)</span><span class="s6-k">([^<]+)</span></div>', s)
assert len(cells) == 6, cells
grid = ''.join(f'<div class="stg6 card"><div class="s6-h"><span class="n s6-n">{n}</span><span class="vk">{nm}</span></div><span class="vl s">{el}</span><span class="s6-k">{k}</span></div>' for n, nm, el, k in cells)
chips = ''.join(f'<div class="s6c card"><span class="n s6-n">{n}</span><span class="s6c-nm">{nm}</span><span class="s6-k">{k}</span></div>' for n, nm, el, k in cells)
s = s.replace(m.group(0), f'<div class="stages6 g32" data-only="0" data-a="stagger" data-d=".6" data-st=".1">{grid}</div>\n'
                          f'  <div class="st6row" data-only="1" data-a="stagger" data-d=".1" data-st=".06">{chips}</div>\n')
s = s.replace('<div class="osband card" data-step="1" data-a="rise">', '<div class="osband card" data-only="1" data-a="rise" data-d=".5">')
write('slides/a.html', s)

# ---------- wording: phases, not steps ----------
sub('slides/b.html', [
    ('data-title="Step 1: Access your market"', 'data-title="Phase 1: Access your market"'),
    ('data-title="Step 1: three ingredients"', 'data-title="Phase 1: three ingredients"'),
    ('data-title="1 of 3 steps in"', 'data-title="1 of 3 phases in"'),
    ('1 of 3 steps in. <span class="a">The best part is still ahead.</span>', '1 of 3 phases in. <span class="a">The best part is still ahead.</span>'),
])
sub('slides/c.html', [
    ('data-title="Step 2: Capture attention"', 'data-title="Phase 2: Capture attention"'),
    ('Start with the clean, verified list from step 1.', 'Start with the clean, verified list from phase 1.'),
    ('fed by the step 1 research', 'fed by the phase 1 research'),
])
sub('slides/d.html', [('data-title="Step 3: Build trust at scale"', 'data-title="Phase 3: Build trust at scale"')])

# ---------- dividers: the phase line sits under the title ----------
for f in ['slides/b.html', 'slides/c.html', 'slides/d.html']:
    s = read(f)
    s = s.replace('<h2 class="t" style="top:auto;bottom:250px;width:1200px" data-a="words" data-d=".5">',
                  '<h2 class="t" style="top:auto;bottom:240px;width:1200px" data-a="words" data-d=".5">')
    s = re.sub(r'<p class="b" style="top:auto;bottom:150px;width:1[35]00px" data-a="rise" data-d="1">',
               '<p class="b dsub" style="top:auto;bottom:150px" data-a="rise" data-d="1">', s)
    write(f, s)

css = read('v3.css')
css += '''
/* ---------- round 7 ---------- */
/* case card: who, what, facts and revenue, on every case study slide */
.ccard { position: absolute; left: 140px; top: 110px; width: 560px; padding: 32px 34px 36px; display: flex; flex-direction: column; gap: 24px; background: rgba(14,15,24,.95); border-color: var(--line-2); box-shadow: 0 30px 80px rgba(0,0,0,.45); z-index: 3; }
.cx-top { display: flex; gap: 24px; align-items: flex-start; }
.cx-ph { width: 168px; height: 210px; object-fit: cover; object-position: 50% 22%; border-radius: 20px; flex: none; }
.cx-id { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.cx-lg { height: 48px; width: auto; max-width: 290px; object-fit: contain; object-position: left center; align-self: flex-start; margin: 4px 0 10px; }
.cx-nm { font: 600 40px/1.15 var(--font); color: var(--text); }
.cx-ti { font: 400 32px/1.25 var(--font); color: var(--mute); }
.cx-what { margin: 0; font: 400 36px/1.3 var(--font); color: var(--text); }
.cx-facts { margin: 0; padding-top: 22px; border-top: 1px solid var(--line-2); display: grid; grid-template-columns: max-content 1fr; gap: 12px 22px; }
.cx-facts dt { font: 400 32px/1.3 var(--font); color: var(--dim); }
.cx-facts dd { margin: 0; font: 600 32px/1.3 var(--font); color: var(--text); }
.cx-facts dd.rev { color: var(--signal); }
.t.rt { left: 780px; width: 1000px; }
.rt2 { left: 780px !important; right: 140px !important; }
.tq2 { position: absolute; left: 780px; right: 140px; top: 340px; padding: 36px 42px; }
.tq2-q { margin: 0; font: 400 38px/1.45 var(--font); color: var(--text); }
.rmets { position: absolute; left: 780px; right: 140px; top: 770px; display: grid; grid-template-columns: 1fr 1.3fr 1fr; gap: 30px; }
.rmets > div, .chain2 > div { display: flex; flex-direction: column; gap: 8px; }
.rmets .n { font-size: 64px; }
.chain2 { position: absolute; left: 780px; right: 140px; top: 360px; display: grid; grid-template-columns: 1.3fr 1fr 1fr 1fr .7fr; gap: 36px; }
.chain2 > div { position: relative; }
.chain2 > div:not(:last-child)::after { content: ""; position: absolute; right: -27px; top: 20px; width: 18px; height: 18px; border-top: 4px solid var(--iris); border-right: 4px solid var(--iris); transform: rotate(45deg); }
.chain2 .n { font-size: 58px; }
.chain2 .vl { font-size: 34px; }
#s-proof2 .mcmp { top: 560px; }
#s-proof3 .fc-bars2 { top: 330px; height: 330px; }
#s-proof3 .fc-row { top: 710px; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 24px; }
#s-proof3 .fc-row .n { font-size: 60px; }
.ceil4 { position: absolute; left: 780px; right: 140px; top: 370px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.ceil4 .card { padding: 30px 34px; display: flex; flex-direction: column; gap: 10px; background: rgba(18,20,29,.92); }
.ceil4 .n { font-size: 68px; }
.cstrip { position: absolute; left: 140px; top: 340px; display: flex; align-items: center; gap: 20px; font: 400 36px/1.2 var(--font); color: var(--mute); }
.cstrip img { height: 46px; width: auto; margin-right: 8px; }
.cstrip .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dim); }
.cstrip span { white-space: nowrap; }
.cap.low { bottom: 52px; }
/* proof wall, slide 9 */
.fgrid { position: absolute; left: 140px; right: 140px; top: 240px; bottom: 116px; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
.fcard { padding: 28px 30px; display: flex; flex-direction: column; gap: 18px; background: rgba(14,15,24,.95); border-color: var(--line-2); min-height: 0; }
.fc-top { display: flex; gap: 24px; align-items: flex-start; }
.fc-ph { width: 150px; height: 188px; object-fit: cover; object-position: 50% 22%; border-radius: 18px; flex: none; }
.fc-id { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.fc-lg { height: 52px; width: auto; max-width: 280px; object-fit: contain; object-position: left center; align-self: flex-start; margin-bottom: 6px; }
.fc-nm { font: 600 34px/1.2 var(--font); color: var(--text); }
.fc-nm span { font-weight: 400; color: var(--mute); }
.fc-what { font: 400 32px/1.28 var(--font); color: var(--mute); }
.fc-lines { display: flex; flex-direction: column; gap: 6px; padding-top: 16px; border-top: 1px solid var(--line-2); }
.fc-facts { font: 400 30px/1.3 var(--font); color: var(--text); }
.fc-rev { font: 600 32px/1.3 var(--font); color: var(--signal); }
.fc-m { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 26px; margin-top: auto; }
.fc-m > div { display: flex; flex-direction: column; gap: 4px; }
.fc-m .n { font-size: 58px; }
.fc-m .vl { font-size: 32px; line-height: 1.2; }
.pgrid { position: absolute; left: 140px; right: 140px; top: 240px; bottom: 108px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: 1fr 1fr; gap: 22px; }
.pcard { display: flex; flex-direction: column; gap: 10px; padding: 20px 26px; background: rgba(14,15,24,.95); border-color: var(--line-2); min-height: 0; overflow: hidden; }
.pc-top { display: flex; gap: 20px; align-items: center; }
.pc-ph { width: 90px; height: 112px; object-fit: cover; object-position: 50% 22%; border-radius: 16px; flex: none; }
.pc-id { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.pc-lg { height: 32px; width: auto; max-width: 230px; object-fit: contain; object-position: left center; align-self: flex-start; margin-bottom: 6px; }
.pc-nm { font: 600 31px/1.12 var(--font); color: var(--text); }
.pc-ro { font: 400 30px/1.2 var(--font); color: var(--mute); }
.pc-what { font: 400 30px/1.25 var(--font); color: var(--dim); }
.pc-m { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 16px; margin-top: auto; }
.pc-m .n { font-size: 60px; color: var(--signal); }
.pc-m .vl { font-size: 32px; line-height: 1.2; color: var(--text); }
.twall { position: absolute; left: 0; right: 0; top: 240px; -webkit-mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent); mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent); }
.tw-row { overflow: hidden; padding: 6px 0; }
.tw-track { display: flex; gap: 28px; align-items: flex-start; width: max-content; animation: mq 170s linear infinite; }
.tw { width: 700px; flex: none; padding: 30px 34px; display: flex; flex-direction: column; gap: 22px; background: rgba(14,15,24,.95); border-color: var(--line-2); }
.tw-top { display: flex; gap: 20px; align-items: center; }
.tw-ph { width: 92px; height: 115px; object-fit: cover; object-position: 50% 22%; border-radius: 16px; flex: none; }
.tw-id { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.tw-nm { font: 600 32px/1.15 var(--font); color: var(--text); }
.tw-ti { font: 400 26px/1.25 var(--font); color: var(--mute); }
.tw-lgr { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.tw-lg { height: 34px; width: auto; max-width: 220px; object-fit: contain; object-position: left center; opacity: .9; }
.tw-lgt { font: 600 26px/1 var(--font); color: var(--text); }
.tw-q { margin: 0; font: 400 29px/1.45 var(--font); color: var(--text); }
.mq-track.tw-track img.tw-ph { width: 92px; height: 115px; max-width: none; opacity: 1; }
.mq-track.tw-track img.tw-lg { height: 34px; width: auto; max-width: 220px; opacity: .9; }
.lwall { position: absolute; left: 140px; right: 140px; top: 350px; display: flex; flex-wrap: wrap; justify-content: center; gap: 18px; }
.lwall .lw { width: 186px; height: 100px; display: grid; place-items: center; border-radius: 18px; background: rgba(255,255,255,.035); border: 1px solid var(--line); }
.lwall .lw img { max-width: 150px; max-height: 50px; width: auto; height: auto; object-fit: contain; opacity: .92; }
/* slide 18: nine mechanisms inside the frame */
.mechs { top: 350px; gap: 18px; }
.mech { grid-template-columns: 56px 1fr; column-gap: 18px; padding: 20px 26px; }
.mech .mi { width: 56px; height: 56px; }
.mech .vk { font-size: 40px; }
.mech .vl { font-size: 36px; line-height: 1.2; }
/* slide 23: six stages in two rows, then the OS under all six */
.stages6.g32 { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; top: 350px; }
.stages6.g32 .stg6 { min-height: 0; padding: 24px 28px; gap: 12px; }
.s6-h { display: flex; align-items: baseline; gap: 16px; }
.stages6.g32 .vk { font-size: 40px; }
.stages6.g32 .s6-k { align-self: flex-start; margin-top: 4px; }
.st6row { position: absolute; left: 140px; right: 140px; top: 350px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.s6c { padding: 22px 22px 24px; display: flex; flex-direction: column; gap: 10px; }
.s6c-nm { font: 600 34px/1.18 var(--font); color: var(--text); }
.s6c .s6-k { align-self: flex-start; margin-top: auto; }
.osband { top: 650px; height: 220px; }
/* slide 28: the sample site fits its panel */
.mpanel { top: 300px; height: 650px; }
.mp-site { top: 170px; }
/* slide 38: sender name and subline stacked */
.gm-from > div { display: flex; flex-direction: column; gap: 6px; line-height: 1.2; }
/* slide 66: chips stay inside the card */
.bt { top: 300px; height: 640px; padding: 48px 56px; gap: 22px; }
.bt .lrow { max-width: 1320px; }
/* dividers: one line under the title */
.b.dsub { width: 1640px; font-size: 44px; line-height: 1.3; }
/* slide 8: logo clear of the photo, GrowthClub mark readable */
.host-cut { left: 150px; }
.jc-lg > img[alt="GrowthClub"] { filter: brightness(2.2) contrast(1.1); max-height: 60px; }
/* slide 28: the sample site sits below the count; its paragraph steps aside for the verdict */
.mpanel { top: 330px; height: 630px; }
.mp-site { top: 190px; }
.mp-site.cut-state .ms-p { visibility: hidden; }
/* round 7b: photo clear of the footer logo; slide 23 cards inside the frame */
.host-cut { left: 120px; bottom: 96px; height: 930px; }
.host-stats2 { grid-template-columns: 1.25fr 1fr 1fr 1fr; }
.stages6.g32 { top: 330px; gap: 18px; }
.s6-h { flex-direction: column; align-items: flex-start; gap: 2px; }
.stages6.g32 .s6-n { font-size: 44px; }
.stages6.g32 .vk { font-size: 34px; }
.stages6.g32 .vl { font-size: 30px; line-height: 1.24; }
.stages6.g32 .s6-k { font-size: 30px; padding: 8px 14px; }
.st6row { top: 330px; }
.s6c { padding: 20px 18px 22px; gap: 8px; }
.s6c .s6-n { font-size: 40px; }
.s6c-nm { font-size: 30px; line-height: 1.18; }
.s6c .s6-k { font-size: 28px; padding: 6px 12px; }
.osband { top: 640px; }
'''
write('v3.css', css)
print('round 7 applied')
