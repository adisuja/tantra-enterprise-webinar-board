"""Round 12 (Adi, 19 Nov 2026): slide 9, the six conversion mechanisms, each as a Tantra landing page on an iPhone in
Safari (iOS 26, floating address bar). The page scrolls by itself; a click moves to the next funnel (src/js/flow.js).
Proof on the pages is limited to what the deck already states ($5MN for our own brands); no deadlines or scarcity."""
from ios import phone, ic, av, E

LOGO = 'assets/logo/tantra-mark.webp'
HEAD = f'<div class="fp-top"><img src="{LOGO}" alt=""><b>Tantra</b><span class="fp-menu"><i></i><i></i></span></div>'

def safari(domain, page, pid):
    bar = (f'<div class="sf-bar"><span class="gl r">{ic("back")}</span><span class="gl pill sf-url"><small>AA</small>'
           f'<b>{E(domain)}</b><svg viewBox="0 0 24 24" class="i"><path d="M19 12a7 7 0 1 1-2.1-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
           f'<path d="M19 4v4h-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
           f'<span class="gl r">{ic("dots")}</span></div>')
    return phone(f'<div class="fp-view"><div class="fp">{HEAD}{page}<div class="fp-foot"><img src="{LOGO}" alt=""><span>© 2026 Tantra · usetantra.com</span></div></div></div>{bar}', 'sf', pid)

def cta(t, sub=None):
    s = f'<small>{E(sub)}</small>' if sub else ''
    return f'<a class="fp-cta">{E(t)}</a>{s}'

def items(rows, kind='num'):
    out = ''
    for i, (a, b) in enumerate(rows):
        mark = f'<span>{i + 1:02d}</span>' if kind == 'num' else '<span class="ck"><svg viewBox="0 0 24 24"><path d="m6 12.5 4 4 8-9" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
        out += f'<li>{mark}<div><b>{E(a)}</b><p>{E(b)}</p></div></li>'
    return f'<ul class="fp-list">{out}</ul>'

def host():
    return (f'<div class="fp-host">{av("Adithya Murali", "av-adi.webp", 52)}<div><b>Adi Murali</b><span>Founder and CEO, Tantra</span></div></div>')

STAT = '<div class="fp-stat"><b>$5MN</b><span>in revenue generated for our own brands with this engine</span></div>'

PAGES = [
    ('Webinar funnels', 'webinar.sellwithtantra.com', f'''
<span class="fp-eye">Free live training</span>
<h3>Build an AI RevOps engine that books sales calls for you</h3>
<p class="fp-sub">A live 60-minute session for founders and revenue leaders.</p>
{host()}
<div class="fp-when"><div><small>Day</small><b>Thursday</b></div><div><small>Time</small><b>4 PM IST</b></div><div><small>Length</small><b>60 min</b></div></div>
{cta('Save my free seat', 'Free · Live on Zoom')}
<h5>What you'll learn</h5>
{items([('Where AI finds buyers who are ready now', 'The five buying signals and how to read them.'), ('One post, five touches', 'How a comment becomes a DM, an email and a booked call.'), ('The engine, end to end', 'Traffic, leads and deals, with an AI workflow behind each.')])}
{STAT}
{cta('Save my free seat')}'''),
    ('Video sales letters', 'usetantra.com/watch', f'''
<span class="fp-eye">Watch the 9-minute breakdown</span>
<h3>How AI turns one post into booked sales calls</h3>
<div class="fp-vid"><img src="img/inflection.webp" alt=""><span class="fp-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span><div class="fp-prog"><i></i></div><small>2:14 / 9:06</small></div>
{cta('Book a 15-minute call', 'Pick a time that suits you')}
<h5>Inside the video</h5>
{items([('The content engine', 'Posts that make buyers raise their hand.'), ('The outreach engine', 'LinkedIn, email and WhatsApp, answered by an AI SDR.'), ('The conversion engine', 'Pages and calls that turn attention into revenue.')], 'check')}
{host()}
{cta('Book a 15-minute call')}'''),
    ('Community funnels', 'usetantra.com/community', f'''
<span class="fp-eye">The Tantra community</span>
<h3>Build your AI revenue engine with founders doing the same</h3>
<div class="fp-faces">{av('Adithya Murali', 'av-adi.webp', 40)}{av('Nelbin Joseph', 'av-nelbin.webp', 40)}{av('Bharath Krishna Pai', 'av-bharath.webp', 40)}{av('Bhaskar Dev', 'av-bhaskar.webp', 40)}<span>Founders and revenue leaders, building every week</span></div>
{cta('Join the community')}
<div class="fp-cards"><div><b>Weekly build sessions</b><p>Build one piece of your engine live, with the team.</p></div><div><b>The prompt library</b><p>250+ real funnel elements, ready to rebuild for your brand.</p></div><div><b>Funnel teardowns</b><p>What works, slide by slide and email by email.</p></div></div>
<h5>Common questions</h5>
<div class="fp-faq"><div>Who is it for? <span>+</span></div><div>How much time does it take? <span>+</span></div><div>Do I need to code? <span>+</span></div></div>
{cta('Join the community')}'''),
    ('Product launch funnels', 'usetantra.com/sdr', f'''
<span class="fp-eye">New</span>
<h3>Meet the Tantra AI SDR</h3>
<p class="fp-sub">It replies to every lead on LinkedIn, WhatsApp and email, in your voice.</p>
<div class="fp-chat"><p class="in">Does it work for a team of 12?</p><p class="out">Yes, it's built for teams your size. Want a seat, or 15 minutes with Adi?</p><p class="in">15 minutes, Thursday?</p><p class="out">Done. The invite is in your inbox.</p></div>
{cta('Get early access')}
<h5>Every channel, one inbox</h5>
<div class="fp-ch"><div><svg class="lgi"><use href="#lg-linkedin"/></svg>LinkedIn</div><div><svg class="lgi"><use href="#lg-whatsapp"/></svg>WhatsApp</div><div><svg class="lgi"><use href="#lg-gmail"/></svg>Email</div></div>
{items([('Connect your channels', 'LinkedIn, WhatsApp and your mailbox.'), ('Teach it your offer', 'Your pages, your calls, your answers.'), ('It books the calls', 'Straight into your calendar and CRM.')])}
{cta('Get early access')}'''),
    ('Book funnels', 'usetantra.com/playbook', f'''
<div class="fp-book"><div class="cover"><img src="{LOGO}" alt=""><b>The AI RevOps Playbook</b><span>Adithya Murali</span></div></div>
<h3>Get the AI RevOps Playbook, free</h3>
<p class="fp-sub">The exact engine behind $5MN in revenue for our own brands, chapter by chapter.</p>
{cta('Send me the book', 'Digital copy, straight to your inbox')}
<h5>Inside the book</h5>
{items([('Content that sells', 'The 10 formats with numbers behind them.'), ('Outreach on every channel', 'Signals, sequences and the AI SDR.'), ('Pages that convert', 'Webinars, VSLs and launches.'), ('The sales call', 'From booked call to closed deal.')])}
{host()}
{cta('Send me the book')}'''),
    ('Workshop funnels', 'usetantra.com/workshop', f'''
<span class="fp-eye">Two-day live workshop</span>
<h3>Build your AI RevOps engine in two days</h3>
<p class="fp-sub">Bring your offer. Leave with the engine running.</p>
<div class="fp-days"><div><small>Day 1</small><b>Traffic and leads</b><p>The content engine, lead magnets and the LinkedIn DM flow.</p></div><div><small>Day 2</small><b>Leads into deals</b><p>Outreach, the AI SDR, your pages and the sales call.</p></div></div>
{cta('Reserve my seat', 'Live on Zoom, with Q&A after each block')}
<h5>You leave with</h5>
{items([('Your content engine', 'Set up and posting.'), ('Your outreach sequences', 'Live on LinkedIn and email.'), ('Your conversion page', 'Built and published.')], 'check')}
{host()}
{cta('Reserve my seat')}'''),
]

def slide9():
    phones = ''.join(safari(d, p, f'fn{i}') for i, (_, d, p) in enumerate(PAGES))
    lis = ''.join(f'<li><span>0{i + 1}</span>{E(n)}</li>' for i, (n, _, _) in enumerate(PAGES))
    return phones, lis

# ---- round 12b (Adi, 19 Nov): the real pages, captured at iPhone size (393 pt wide, 2x) on 19 Nov 2026 by
# /tmp/qs/fn/shoot3.js from the live sites (the playbook from deliverables/33-bonus-books/site, which is password-gated live)
REAL = [('Webinar funnels', 'event.webinarjam.com', 'wj'),
        ('Video sales letters', 'webinar.sellwithtantra.com', 'vsl'),
        ('Community funnels', 'webinar.sellwithtantra.com', 'community'),
        ('Product launch funnels', 'usetantra.com', 'launch'),
        ('Book funnels', 'bonuses.sellwithtantra.com', 'book'),
        ('Workshop funnels', 'webinar.sellwithtantra.com', 'webinar')]

def real_phone(domain, key, pid):
    from PIL import Image
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    im = Image.open(f'{root}/deck/assets/r12/fn-{key}.webp').convert('RGB')
    r, g, b = im.getpixel((6, 4))
    dark = (r * 299 + g * 587 + b * 114) / 1000 < 140
    bar = (f'<div class="sf-bar"><span class="gl r">{ic("back")}</span><span class="gl pill sf-url"><small>AA</small>'
           f'<b>{E(domain)}</b><svg viewBox="0 0 24 24" class="i"><path d="M19 12a7 7 0 1 1-2.1-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
           f'<path d="M19 4v4h-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>'
           f'<span class="gl r">{ic("dots")}</span></div>')
    html = phone(f'<div class="fp-view"><img class="fp fp-shot" src="assets/r12/fn-{key}.webp" alt=""></div>{bar}', 'sf real' + (' dk' if dark else ''), pid)
    return html.replace('<div class="ip-scr">', f'<div class="ip-scr" style="--sb:rgb({r},{g},{b})">', 1)

def slide9():
    phones = ''.join(real_phone(d, k, f'fn{i}') for i, (_, d, k) in enumerate(REAL))
    lis = ''.join(f'<li><span>0{i + 1}</span>{E(n)}</li>' for i, (n, _, _) in enumerate(REAL))
    return phones, lis
