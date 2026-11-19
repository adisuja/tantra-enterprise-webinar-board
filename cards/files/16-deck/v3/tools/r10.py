"""Round 10 (Adi, 19 Nov 2026): the new opening, QS slides 1 to 8 rebuilt from Adi's notes in Tab 40.
Writes src/slides/a0.html (12 slides). The LinkedIn posts and comments are real (src/r10-posts.json, read from the
public posts on 19 Nov 2026); no disclaimer lines on slides (Adi, 19 Nov).
usage: python3 tools/r10.py   (build.py runs it first)"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ios, funnels

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = json.load(open(ROOT + '/src/r10-posts.json'))
E = html.escape

AUTH = {  # who wrote it, their photo (initials if none), the keyword commenters typed, the resource they asked for
    'nelbin':  ('Nelbin Joseph', 'av-nelbin.webp', 'free access', 'the AI LinkedIn sales team setup'),
    'ipsita':  ('Ipsita Dhar', None, 'Meet', 'the Meeting Factory playbook'),
    'bharath': ('Bharath Krishna Pai', 'av-bharath.webp', 'Try it', 'the Claude prospecting system'),
    'adi':     ('Adithya Murali', 'av-adi.webp', 'PROMPTS', 'the AI Funnel Prompt Starter Pack'),
    'bhaskar': ('Bhaskar Dev', 'av-bhaskar.webp', 'webinar funnel', 'the webinar funnel maths sheet'),
}
ADI_BODY = ("I finally pulled 250+ real funnel elements into one prompt library.\n\nAnd I'm giving you the 7 prompts I'd start "
            "with, free ↓\n\nIt's for founders who are tired of opening a blank chat and hoping.\n\nIt obviously can't replace "
            "what you know about your own buyer.\n\nBut it does stop AI from guessing. Every prompt points at a real example and "
            "rebuilds it for your brand.")

def initials(n):
    return ''.join(w[0] for w in n.split()[:2]).upper()

def avatar(name, img, cls='av'):
    if img:
        return f'<img class="{cls}" src="assets/r10/{img}" alt="">'
    return f'<span class="{cls} ini">{E(initials(name))}</span>'

def clean(t):
    t = t.replace('—', ',').replace('–', ' to ')
    return re.sub(r'\s+', ' ', t).strip()

def body_of(k):
    b = ADI_BODY if k == 'adi' else POSTS[k].get('body', '')
    b = b.replace('—', ',').replace('–', ' to ')
    # break the one-paragraph public text into readable lines at sentence ends and arrows
    if '\n' not in b:
        b = re.sub(r'(?<=[.!?↓\U0001F92F]) (?=[A-Z→])', '\n', b)
        b = b.replace(' → ', '\n→ ')
    return b

def post_card(k, n_lines=4, n_comments=2, cls='pc'):
    """A LinkedIn post drawn as one clean, readable card: author, the opening lines, counts, two real comments."""
    name, img, kw, res = AUTH[k]
    p = POSTS[k]
    lines = [l for l in body_of(k).split('\n') if l.strip()][:n_lines]
    cc = p.get('comments_count') or len(p['comments'])
    if cc == '?':
        cc = len(p['comments'])
    seen, coms = set(), []
    for c in p['comments']:
        if c['name'] in seen or c['name'].startswith(name.split()[0]) or len(coms) >= n_comments:
            continue
        seen.add(c['name'])
        t = clean(c['text'])
        if len(t) > 70:
            t = t[:67].rsplit(' ', 1)[0] + '...'
        coms.append(f'<div class="pc-c"><b>{E(clean(c["name"]).split(",")[0])}</b><span>{E(t)}</span></div>')
    return (f'<div class="{cls} card"><div class="pc-a">{avatar(name, img)}<div><b>{E(name)}</b><span>LinkedIn · Nov 2026</span></div>'
            f'<svg class="lgi"><use href="#lg-linkedin"/></svg></div>'
            f'<div class="pc-b">{"".join(f"<p>{E(l)}</p>" for l in lines)}</div>'
            f'<div class="pc-n">{E(str(cc))} comments</div>{"".join(coms)}</div>')

CAP = '<p class="cap10" data-a="fade" data-d=".05">AI + automations can now do insane stuff.</p>'
LOGO = 'assets/logo/tantra-mark.webp'

def steps(items, d=.9):
    return ('<ol class="st10" data-a="stagger" data-d="%s" data-st=".15">' % d
            + ''.join(f'<li><span>{i + 1}</span>{t}</li>' for i, t in enumerate(items)) + '</ol>')

def slides():
    S = []
    S.append(f'''<!-- 1 GOING LIVE (QS 1), round 11 -->
<section class="slide" id="s-live" data-title="Going live now" data-bg="dim" data-reel="9">
  <div class="live11" data-a="rise" data-d=".2"><img src="{LOGO}" alt="Tantra"><h1 class="t"><i class="dot"></i>Going live now</h1></div>
  <aside class="notes"><p><b>Minute 0. QS slide 1.</b> "We're live, folks." Ask where people are joining from; say you're in Bangalore. Ask what they sell and who they sell to. Phones, Outlook and WhatsApp away.</p></aside>
</section>''')
    S.append('''<!-- 2 ENGAGE IN THE CHAT (QS 2), round 11 -->
<section class="slide" id="s-chat" data-title="Engage in the chat" data-bg="dim" data-reel="7">
  <h2 class="t" data-a="words">Engage in the chat. <span class="a">We'll have a live Q&amp;A at the end.</span></h2>
  <div class="q11 card" data-a="rise" data-d=".7"><p>What would you like to learn about AI revenue generation and sales, for this to be the most valuable workshop you've been on?</p></div>
  <aside class="notes"><p><b>Minute 1. QS slide 2.</b> Founders, executives, sales and RevOps leaders: pop thoughts and questions in the chat so the session can be personalised. Q&amp;A at the end.</p></aside>
</section>''')
    S.append('''<!-- 3 CHANGED FOREVER (QS 3), round 11 -->
<section class="slide" id="s-inflect" data-title="Revenue generation has changed forever" data-bg="dim" data-reel="8">
  <div class="hero" data-gl="img/inflection.webp"><img src="img/inflection.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t w4" data-a="words">Revenue generation and sales online have <span class="a">changed forever.</span></h2>
  <p class="b w4" style="top:520px" data-a="rise" data-d=".8">What took months, CRM integrations and tens of thousands of dollars now runs in days, with AI.</p>
  <aside class="notes"><p><b>Minute 2. QS slide 3.</b> When the OpenAI API landed, revenue generation changed for good. Two paths: keep doing it the old way, by hand and with more hires, or build it the way AI-enabled teams do, in a tenth of the time.</p></aside>
</section>''')
    S.append('''<!-- 4 THE QUESTION (QS 4), round 11 -->
<section class="slide" id="s-question" data-title="Employing AI to generate revenue, step by step" data-bg="dim" data-reel="7">
  <div class="hero" data-gl="img/bottleneck.webp"><img src="img/bottleneck.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t w4" style="top:300px" data-a="words">How do you employ AI to generate revenue, <span class="a">step by step?</span></h2>
  <aside class="notes"><p><b>Minute 2. QS slide 4.</b> "I'll show you how to build, deploy and run an end-to-end AI RevOps engine. You pour context in; the system builds and runs; you optimise." We built it for ourselves first.</p></aside>
</section>''')
    # ---- round 12: slides 5 to 7 as real iPhone screens, joined by connector lines (tools/ios.py, src/js/flow.js)
    def cm(k, names, trim=150):
        out = []
        for n in names:
            c = next(c for c in POSTS[k]['comments'] if c['name'] == n)
            t = clean(re.sub(r'\s*—\s*', ', ', c['text']))
            if len(t) > trim:
                t = t[:trim].rsplit(' ', 1)[0] + '... more'
            out.append((clean(n).split('{')[0].strip(), t, c['age']))
        return out
    def lines(k, n):
        return [l for l in body_of(k).split('\n') if l.strip()][:n]
    R12 = json.load(open(ROOT + '/src/r12-posts.json'))  # real posts and comments, read 19 Nov 2026 (tools: /tmp/qs/li)
    AK = 'assets/r12/c-anthony-kennedy.webp'
    p1 = ios.li_real(R12['n680'], ['Anthony Kennedy', 'Ashwin Sewgobind', 'Lucas Beill'], hl='Anthony Kennedy', lines=3, img_h=150, pid='c-p1')
    p2 = ios.li_dm('Anthony Kennedy', AK, [('day', 'Yesterday'),
        ('Nelbin Joseph', 'av-nelbin.webp', '4:12 PM', "Anthony, thanks for the comment! Here's the free AI marketing team: 48 skills, agents, guides and templates for Claude.", ('Claude marketing pack: 48 skills, agents and templates', '7-page PDF · tinyurl.com'), True)], pid='c-p2')
    p3 = ios.mail('Nelbin Joseph', 'Anthony Kennedy', '9:02 AM', 'Your free AI marketing team for Claude',
        ['Hi Anthony,', 'You commented MARKETING on my post yesterday, so here is the full pack again in one place: 48 skills, agents, guides and templates, plus 300+ prompts.',
         'Start with the 8 Planning & Research skills. They build your strategy before Claude writes a word.',
         'Want a 15-minute walkthrough for your team? Pick any time on my calendar.', 'Nelbin'], pid='c-p3')
    p3 = p3.replace('<h4 class="ml-sub">', '<h4 class="ml-sub hl">')
    def ph(x, n, label, html_):
        return f'<div class="ph12" style="left:{x}px"><p><span>{n}</span>{label}</p>{html_}</div>'
    S.append(f"""<!-- 5a CONTENT (QS 5), round 12 -->
<section class="slide" id="s-content" data-title="AI can now do insane stuff: content" data-bg="dim" data-reel="10">
  {CAP}
  <h2 class="t h11" data-a="words" data-d=".2">Content that makes buyers <span class="a">raise their hand.</span></h2>
  <svg class="flow11" data-a="draw" data-d="1.9" data-st=".55" data-dur="1"><path id="f5a" data-from="#c-p1" data-to="#c-p2" data-side="r-l"/><path id="f5b" data-from="#c-p2" data-to="#c-p3" data-side="r-l"/><path id="f5c" data-from="#c-p3" data-to="#c-crm" data-side="r-l"/></svg>
  <div data-a="stagger" data-d=".6" data-st=".25">
    {ph(60, 1, 'They comment the keyword', p1)}{ph(593, 2, 'AI sends it by LinkedIn DM', p2)}{ph(1126, 3, 'A follow-up email, next day', p3)}
    <div class="crm12" id="c-crm" style="left:1644px;top:560px"><div class="crm-h"><img src="{LOGO}" alt="">Tantra CRM</div><small>New deal</small><div class="crm-p"><img src="{AK}" alt=""><b>Anthony Kennedy</b></div><span class="crm-r">Chief Marketing Officer</span>
      <dl><dt>Source</dt><dd>LinkedIn post</dd><dt>Keyword</dt><dd>MARKETING</dd><dt>Stage</dt><dd>Lead</dd><dt>Next</dt><dd>Sales call</dd></dl></div>
  </div>
  <aside class="notes"><p><b>Minute 3. QS slide 5.</b> 50 content formats; 10 have numbers proving pipeline growth. The resource giveaway: walk the line left to right. A real comment on Nelbin's post, the resource by LinkedIn DM, the follow-up email the next day, then the deal opens in the CRM for sales.</p></aside>
</section>""")
    feeds = [('n845', ['James Yeo', 'Scott Lovingood', 'Scott Sutton']), ('b224', ['Goran Granić', 'Jules Johnson', 'Ricardo Pereira']),
             ('i449', ['Elena Poughia', 'Tanay Saxena', 'Amber Cheema'])]
    ph6 = ''
    for i, (k, who) in enumerate(feeds):
        h = ios.li_real(R12[k], who, lines=2, img_h=0, pid=f's6-{i}')
        ph6 += f'<div class="ph12" style="left:{235 + i * 517}px;top:390px">{h}</div>'
    S.append(f"""<!-- 5b EVERY PROFILE (QS 5), round 12 -->
<section class="slide" id="s-stream" data-title="AI can now do insane stuff: content at scale" data-bg="dim" data-reel="10">
  {CAP}
  <div class="kpi12" id="s6-k" data-a="stagger" data-d=".3"><div><b>0.5MN+</b><span>impressions a month</span></div><div><b>$100K</b><span>in pipeline value every month</span></div></div>
  <svg class="flow11" data-a="draw" data-d="1.6" data-st=".2" data-dur="1.1"><path data-from="#s6-0" data-to="#s6-k" data-side="t-b"/><path data-from="#s6-1" data-to="#s6-k" data-side="t-b"/><path data-from="#s6-2" data-to="#s6-k" data-side="t-b"/></svg>
  <div data-a="stagger" data-d=".7" data-st=".15">{ph6}</div>
  <aside class="notes"><p><b>Minute 4. QS slide 5.</b> Same play across every team profile, every week: Nelbin, Ipsita, Bharath, Bhaskar and me. Every comment gets the resource by DM and email and lands in the CRM. Together: 0.5MN+ impressions a month and $100K in pipeline value every month.</p></aside>
</section>""")
    o1 = ios.li_dm('Rahul Mehta', None, [('day', 'Today'),
        ('Adithya Murali', 'av-adi.webp', '9:14 AM', "Saw your post on longer sales cycles, Rahul. We're running a live hour on exactly that this Thursday. Worth a seat?", None, False),
        ('Rahul Mehta', None, '11:02 AM', 'Does it work for a team of 12?', None, False),
        ('Adithya Murali', 'av-adi.webp', '11:02 AM', "Yes, it's built for teams your size. Want a seat, or 15 minutes with me?", None, True)], pid='o-p1')
    o2 = ios.wa('Meera Iyer', [('day', 'Today'),
        ('out', "Hi Meera, your seat for Thursday is saved. Here's the join link for 4 PM: webinar.sellwithtantra.com/join", '9:30 AM', False),
        ('in', 'Can my co-founder join too?', '10:12 AM', False),
        ('out', "Of course. I've sent her a seat by email as well. See you both on Thursday.", '10:12 AM', True)], pid='o-p2')
    o3 = ios.mail('Adi Murali', 'Daniel Brooks', '2:41 PM', 'Re: A quick idea for your team',
        ['Hi Daniel,', 'Good question. Yes, the same setup runs for a three-person team and a forty-person one.',
         'Two times for a 15-minute walkthrough: Tuesday 11 AM or Wednesday 3 PM. Which suits you?', 'Adi'],
        ('On Mon, Daniel Brooks wrote:', 'Interesting. What would this look like for a smaller team like ours?'), pid='o-p3')
    o3 = o3.replace('<div class="ml-body">', '<div class="ml-body hl">', 1)
    ph7 = ''.join(f'<div class="ph12" style="left:{235 + i * 517}px;top:400px">{h}</div>' for i, h in enumerate((o1, o2, o3)))
    S.append(f"""<!-- 5c OUTREACH (QS 5), round 12 -->
<section class="slide" id="s-outreach" data-title="AI can now do insane stuff: outreach" data-bg="dim" data-reel="10">
  {CAP}
  <h2 class="t h11" data-a="words" data-d=".2">Outreach on every channel, <span class="a">answered by AI.</span></h2>
  <div class="node12" id="o-node" data-a="rise" data-d=".6"><img src="{LOGO}" alt=""><b>Tantra AI SDR replies on every channel</b></div>
  <svg class="flow11" data-a="draw" data-d="1.5" data-st=".15" data-dur="1"><path data-from="#o-node" data-to="#o-p1" data-side="b-t"/><path data-from="#o-node" data-to="#o-p2" data-side="b-t"/><path data-from="#o-node" data-to="#o-p3" data-side="b-t"/></svg>
  <div data-a="stagger" data-d=".9" data-st=".15">{ph7}</div>
  <aside class="notes"><p><b>Minute 4. QS slide 5.</b> Multi-channel outreach: LinkedIn (great for B2B), WhatsApp and email. The marked message on each phone is the AI SDR's reply: it answers every response, on every platform.</p></aside>
</section>""")
    S.append(f"""<!-- 5d CONVERSION ENGINES (QS 5), round 12 -->
<section class="slide" id="s-convert" data-title="AI can now do insane stuff: conversion engines" data-bg="dim" data-reel="10">
  {CAP}
  <h2 class="t h11" data-a="words" data-d=".2">Conversion engines that <span class="a">turn attention into calls.</span></h2>
  <figure class="cv12" data-a="rise" data-d=".6"><div class="shot11"><img src="assets/r10/lp-tantra-ent-webinar.webp" alt="The Tantra Enterprise webinar page"></div><figcaption><b>The conversion mechanism that brought you here.</b></figcaption></figure>
  <aside class="notes"><p><b>Minute 5. QS slide 5.</b> This webinar is a conversion engine: the page that brought you here. AI builds these end to end.</p></aside>
</section>""")
    fphones, flis = funnels.slide9()
    S.append(f"""<!-- 5e CONVERSION MECHANISMS (QS 5), round 12: click to move to the next funnel -->
<section class="slide" id="s-mech" data-title="Conversion mechanisms" data-bg="dim" data-reel="9" data-steps="5">
  {CAP}
  <h2 class="t h11 fn-t" data-a="words" data-d=".2">Conversion mechanisms turn cold traffic into <span class="a">revenue in the bank.</span></h2>
  <ol class="fn-list" data-a="stagger" data-d=".6" data-st=".06">{flis}</ol>
  <p class="fn-path" data-a="rise" data-d="1.2">Know you <span>→</span> like you <span>→</span> trust you <span>→</span> <b>book a sales call.</b></p>
  <div class="fn-view" data-a="rise" data-d=".5"><div class="fn-track">{fphones}</div></div>
  <aside class="notes"><p><b>Minute 5. QS slide 5.</b> Each page scrolls by itself; click to move to the next funnel: webinar, VSL, community, product launch, book, workshop. Each one walks your buyer from knowing you to liking you to trusting you, until they book a call. AI can now build every one of them, end to end.</p></aside>
</section>""")
    S.append('''<!-- 6 THE GAP (QS 6), round 11 -->
<section class="slide" id="s-gap" data-title="Most founders don't have the infrastructure" data-bg="dim" data-reel="7">
  <div class="hero" data-gl="img/noise.webp"><img src="img/noise.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t w4" data-a="words">Most founders don't have the infrastructure, or the know-how, <span class="a">to put these to work.</span></h2>
  <p class="b w4" style="top:640px" data-a="rise" data-d="1">A new tool every week. The pipeline stays the same.</p>
  <aside class="notes"><p><b>Minute 6. QS slide 6.</b> You could build this yourself with enough time, but the noise of new tools and paths means we never build what moves the pipeline.</p></aside>
</section>''')
    S.append(f'''<!-- 7 WHAT I'LL SHOW YOU (QS 7), round 11 -->
<section class="slide" id="s-not" data-title="A system, end to end" data-bg="dim" data-reel="8">
  <h2 class="t" data-a="words">Today I'll show you a system that runs it <span class="a">end to end.</span></h2>
  {steps(['Generate traffic', 'Turn that traffic into leads', 'Turn those leads into deals'], .7).replace('st10', 'st10 big')}
  <p class="b" style="top:820px" data-a="rise" data-d="1.6">One process, with an AI workflow behind every step.</p>
  <aside class="notes"><p><b>Minute 6. QS slide 7.</b> Not traffic tips, not how CRMs work, not vibe coding in Claude Code. If that's what you came for, no hard feelings. An end-to-end AI RevOps engine. "Type 1 in the chat if you want it."</p></aside>
</section>''')
    S.append('''<!-- 8 HOST (QS 8), round 11 -->
<section class="slide" id="s-host" data-title="I'm Adi, founder and CEO of Tantra" data-bg="dim" data-reel="9">
  <div class="host10-img" data-a="fade" data-d=".2"><img src="assets/r10/adi-host.webp" alt="Adi, founder and CEO of Tantra"></div>
  <h2 class="t host10-t" data-a="words" data-d=".3">I'm Adi, <span class="a">founder and CEO of Tantra.</span></h2>
  <div class="host11-stat" data-a="rise" data-d="1"><b>$5MN</b><span>in revenue generated for our own brands</span></div>
  <p class="b host11-pass" data-a="rise" data-d="1.5">My passion is where AI meets RevOps.</p>
  <aside class="notes"><p><b>Minute 7. QS slide 8.</b> Why listen to me: founder and CEO of Tantra, $5MN in revenue generated for our own brands, and the passion: where AI meets RevOps.</p></aside>
</section>''')
    return '\n\n'.join(S) + '\n\n'

if __name__ == '__main__':
    open(ROOT + '/src/slides/a0.html', 'w').write(slides())
    print('a0.html: 12 opening slides (round 12)')
