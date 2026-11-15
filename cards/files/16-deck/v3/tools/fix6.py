"""Round 6: user requests (host, proof, bonuses, agenda, problems, Funnel OS, logo on every slide)."""
import os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = R + '/src'

def section(path, num, new):
    p = f'{S}/slides/{path}'; s = open(p).read()
    m = re.search(r'<!-- %d [^\n]*-->\n.*?(?=\n<!-- \d+ |\Z)' % num, s, flags=re.S)
    if not m: raise SystemExit(f'section {num} not found in {path}')
    s = s[:m.start()] + new.strip('\n') + s[m.end():]
    open(p, 'w').write(s)

def sub(path, pairs):
    p = f'{S}/{path}'; s = open(p).read()
    for a, b in pairs:
        if a not in s: raise SystemExit(f'NOT FOUND in {path}: {a[:110]}')
        s = s.replace(a, b)
    open(p, 'w').write(s)

TL = '<span class="tlock"><img src="assets/tantra-mark-white.webp" alt=""><img src="assets/tantra-word.webp" alt="Tantra"></span>'

section('a.html', 8, f'''<!-- 8 HOST (QS 8) -->
<section class="slide" id="s-host" data-title="I'm Adi, founder of Tantra" data-bg="dim" data-reel="9">
  <div class="host-glow" data-a="fade" data-d=".1"></div>
  <img class="host-cut" src="assets/adi-cutout.webp" alt="Adi, founder of Tantra" data-a="fade" data-d=".15">
  <h2 class="t" style="left:820px;top:120px;width:960px" data-a="words" data-d=".4">I'm Adi. <span class="a">Founder of Tantra.</span></h2>
  <div class="journey3" data-a="stagger" data-d=".9" data-st=".16">
    <div class="jc"><div class="jc-lg"><img src="assets/l/growthclub.webp" alt="GrowthClub"></div><span class="vl s">Founder</span></div>
    <div class="jc"><div class="jc-lg"><img src="assets/l/quantum-scaling.webp" alt="Quantum Scaling"></div><span class="vl s">Co-founder: zero to $6MN ARR in 3 years</span></div>
    <div class="jc on"><div class="jc-lg">{TL}</div><span class="vl s">Founder: 400+ brands</span></div>
  </div>
  <div class="host-stats2" data-a="stagger" data-d="1.5">
    <div><span class="n">400+</span><span class="vl s">brands</span></div>
    <div><span class="n">10+</span><span class="vl s">years</span></div>
    <div><span class="n">21+</span><span class="vl s">countries</span></div>
    <div><span class="n">47+</span><span class="vl s">industries</span></div>
  </div>
  <aside class="notes"><p><b>Minute 4. QS slide 8.</b> "Why listen to me? I'm Adi, a serial founder in AI and RevOps. I started GrowthClub. I co-founded Quantum Scaling and grew it from zero to $6MN in ARR in three years, on content and webinars. Then I founded Tantra. Over ten years: 400+ brands, 21+ countries, 47+ industries." Never say $50M.</p></aside>
</section>''')

LOGOS = ['growth-idea', 'fintechcircle', 'neural-it', 'cavli', 'appster', 'coinfirm', 'rhenus', 'kadima', 'wxrks', 'bamf', 'dataguard', 'omniance', 'upgrad', 'licious', 'leapwork',
         'merkle-science', 'salestherapy', 'quantum-scaling', '91springboard', 'springup', 'salesup', 'wowmakers', 'iboson', 'imaginegrowth', 'ingwe', 'tripsalam', 'esya', 'ikrshna',
         'myfels', 'hair-loss-revolution', 'ytc', 'unblock', 'ecomm-design', 'matcha-tea', 'ecommerce-platforms', 'flabba', 'netwrk']
def row(ids):
    imgs = ''.join(f'<img src="assets/l/{i}.webp" alt="{i}">' for i in ids)
    return f'<div class="mq-row"><div class="mq-track">{imgs}{imgs}</div></div>'
half = (len(LOGOS) + 1) // 2

section('a.html', 9, f'''<!-- 9 ALREADY WORKING (QS 9) -->
<section class="slide" id="s-working" data-title="400+ brands run this today" data-bg="dim" data-reel="11">
  <h2 class="t" data-a="words"><span class="a">400+ brands</span> run this today.</h2>
  <div class="case2" data-a="stagger" data-d=".5" data-st=".2">
    <div class="cc">
      <img class="cc-ph" src="assets/p/shweta.webp" alt="Shweta">
      <div class="cc-b">
        <div class="cc-top"><img class="cc-lg" src="assets/l/growth-idea.webp" alt="Growth Idea"><span class="vl s">Shweta, Founder &amp; CEO</span></div>
        <div class="cc-m">
          <div><span class="n a-s">80</span><span class="vl s">sales calls from 11 webinars</span></div>
          <div><span class="n">8.6x</span><span class="vl s">registration rate, first to best</span></div>
          <div><span class="n">321</span><span class="vl s">came live to one webinar</span></div>
          <div><span class="n">765,105</span><span class="vl s">people reached</span></div>
        </div>
      </div>
    </div>
    <div class="cc">
      <img class="cc-ph" src="assets/p/sailesh-paul.webp" alt="Sailesh Paul">
      <div class="cc-b">
        <div class="cc-top"><img class="cc-lg" src="assets/l/neural-it.webp" alt="Neural IT"><span class="vl s">Sailesh, Founder &amp; CEO</span></div>
        <div class="cc-m">
          <div><span class="n a-s">7x</span><span class="vl s">more people live: 17 to 127</span></div>
          <div><span class="n">141,734</span><span class="vl s">attorneys and staff reached</span></div>
          <div><span class="n">6</span><span class="vl s">sales calls with law firms</span></div>
          <div><span class="n">50,560</span><span class="vl s">invites a webinar, from 10,000</span></div>
        </div>
      </div>
    </div>
  </div>
  <div class="marquee" data-a="fade" data-d="1.3">{row(LOGOS[:half])}{row(LOGOS[half:])}</div>
  <span class="cap m" data-a="fade" data-d="1.6">Client trackers · Growth Idea May 2025 to Feb 2026 · Neural IT Jan to Apr 2026</span>
  <aside class="notes"><p><b>Minute 5. QS slide 9.</b> "Don't take my word for it. Shweta's team at Growth Idea, a UK coaching group: 80 sales calls from 11 webinars, 765,105 people reached, and 8.6 times the registration rate from their first webinar to their best. Sailesh at Neural IT sells to personal-injury law firms: 141,734 attorneys and staff reached, seven times more people live, 17 to 127, and 6 sales calls with law firms." The logos are clients on our case-study and registration pages (no Google, Amazon or Techstars).</p></aside>
</section>''')

section('a.html', 11, '''<!-- 11 BONUSES (QS 11) -->
<section class="slide" id="s-gifts" data-title="Your bonuses" data-bg="dim" data-reel="10">
  <h2 class="t" data-a="words">Your bonuses, <span class="a">on us.</span></h2>
  <p class="b" style="top:250px;width:1640px" data-a="rise" data-d=".6">All of it arrives on WhatsApp and email. Your Revenue Calculator may already be there.</p>
  <div class="gifts" data-a="stagger" data-d=".8" data-st=".12">
    <div class="gift"><div class="g-img"><img src="assets/b/playbook-a.webp" alt=""></div><span class="vk">The $1MN+ B2B RevOps Playbook</span></div>
    <div class="gift"><div class="g-img"><img src="assets/b/prompts-a.webp" alt=""></div><span class="vk">The $1MN+ AI Funnel Prompt Library</span></div>
    <div class="gift"><div class="g-img"><img src="assets/b/calculator-a.webp" alt=""></div><span class="vk">Your AI RevOps Revenue Calculator</span></div>
    <div class="gift"><div class="g-img wide"><img src="img/surprise.webp" alt="" style="object-position:72% 50%"></div><span class="vk">A surprise bonus</span></div>
  </div>
  <aside class="notes"><p><b>Minute 5. QS slide 11.</b> "Here's what you get from today, sent to your WhatsApp and email: the $1MN+ B2B RevOps Playbook, the $1MN+ AI Funnel Prompt Library, your AI RevOps Revenue Calculator, which some of you already have, and a surprise bonus I'll show you at the end." No dollar values on the bonuses.</p></aside>
</section>''')

section('a.html', 12, '''<!-- 12 THE PLAN (QS 12) -->
<section class="slide" id="s-plan" data-title="Here's the plan" data-bg="dim" data-reel="8">
  <h2 class="t" data-a="words">Here's the <span class="a">plan.</span></h2>
  <div class="vis agenda" style="top:380px" data-a="stagger" data-d=".6" data-st=".14">
    <div class="ag"><span class="n ag-m">10 min</span><i class="ag-dot"></i><span class="vk">What's holding back your revenue growth?</span></div>
    <div class="ag"><span class="n ag-m">30 min</span><i class="ag-dot"></i><span class="vk">The three phases of the AI RevOps engine</span></div>
    <div class="ag"><span class="n ag-m">45 min</span><i class="ag-dot"></i><span class="vk a">Live Q&amp;A: I answer all your questions live</span></div>
  </div>
  <aside class="notes"><p><b>Minute 6. QS slide 12.</b> "First ten minutes: what's holding back your revenue growth. Then thirty minutes on the three phases of the AI RevOps engine. Then 45 minutes of live Q&amp;A, where I answer all your questions live."</p></aside>
</section>''')

section('a.html', 15, '''<!-- 15 THREE THINGS AT ONCE (QS 15) -->
<section class="slide" id="s-camps" data-title="Three things leaders fight at once" data-bg="dim" data-reel="9">
  <h2 class="t" data-a="words">Most leaders fight <span class="a-e">three things at once.</span></h2>
  <div class="camps" data-a="stagger" data-d=".6" data-st=".14">
    <div class="camp"><div class="c-img"><img src="img/volume.webp" alt=""></div><span class="n c-n a-e">01</span><span class="vk">Lead volume and quality</span></div>
    <div class="camp"><div class="c-img"><img src="img/machine.webp" alt="" style="object-position:58% 50%"></div><span class="n c-n a-e">02</span><span class="vk">Conversion mechanisms</span></div>
    <div class="camp"><div class="c-img"><img src="img/core.webp" alt=""></div><span class="n c-n a-e">03</span><span class="vk">End-to-end AI orchestration and growth</span></div>
  </div>
  <aside class="notes"><p><b>Minute 7. QS slide 15.</b> "Camp one: lead volume and quality. Not enough of the right buyers, and the ones who book aren't ready. Camp two: conversion mechanisms. Nothing warms buyers up before you ask for the call. Camp three: orchestration. No one system builds, runs and improves the funnel, so nothing compounds. Type 1, 2 or 3 in the chat."</p></aside>
</section>''')

section('a.html', 16, '''<!-- 16 PROBLEM 1 (QS 16) -->
<section class="slide" id="s-volume" data-title="Problem 1: Lead volume and quality" data-bg="dim" data-reel="7">
  <div class="hero" data-gl="img/volume.webp"><img src="img/volume.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t" style="top:300px;width:900px" data-a="words">Lead volume <span class="a-e">and quality.</span></h2>
  <p class="b" style="top:540px;width:800px" data-a="rise" data-d=".6">Not enough qualified buyers, and the ones who book <span class="a-e">aren't ready.</span></p>
  <aside class="notes"><p><b>Minute 8. QS slides 16 and 18.</b> "Camp one. It isn't consistent, and when you do get calls, they say 'I never filled that in' or 'pitch me'. Zombie calls."</p></aside>
</section>''')

section('a.html', 17, '''<!-- 17 FEAST OR FAMINE (QS 17) -->
<section class="slide" id="s-feast" data-title="Feast or famine" data-bg="dim" data-reel="8">
  <div class="hero shift"><img src="img/feast.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t w4" data-a="words">And the result is <span class="a-e">feast or famine.</span></h2>
  <ul class="dash-list" style="top:360px" data-a="stagger" data-d=".7" data-st=".12">
    <li>Referrals</li><li>Inconsistent outreach</li><li>Content that doesn't convert</li><li>Agencies that overpromised</li><li class="a-e">Zombie calls that go nowhere</li>
  </ul>
  <aside class="notes"><p><b>Minute 8. QS slide 17.</b> "Some months you're on top of the world. Then months of nothing, and you're wondering how you'll make payroll. Who here can relate?" Tell your own version only if it's true for you.</p></aside>
</section>''')

ICON = {
 'webinar': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M10 8l4 2-4 2z"/><line x1="8" y1="20" x2="16" y2="20"/>',
 'workshop': '<circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/><path d="M2 20c0-3.5 2.7-6 6-6s6 2.5 6 6M10 20c0-3.5 2.7-6 6-6s6 2.5 6 6"/>',
 'challenge': '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
 'vsl': '<rect x="2" y="5" width="15" height="14" rx="2"/><path d="M17 10l5-3v10l-5-3"/>',
 'guide': '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/><line x1="9" y1="13" x2="17" y2="13"/><line x1="9" y1="17" x2="15" y2="17"/>',
 'launch': '<path d="M12 2c3 2 5 6 5 10l-2 5H9l-2-5c0-4 2-8 5-10z"/><circle cx="12" cy="10" r="2"/><path d="M9 17l-2 4M15 17l2 4"/>',
 'call': '<path d="M5 3h4l2 5-3 2a12 12 0 0 0 6 6l2-3 5 2v4a2 2 0 0 1-2 2A18 18 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
 'community': '<circle cx="12" cy="7" r="3"/><circle cx="5" cy="11" r="2.4"/><circle cx="19" cy="11" r="2.4"/><path d="M6 21c0-3.3 2.7-6 6-6s6 2.7 6 6M1 19c0-2.2 1.6-4 4-4M23 19c0-2.2-1.6-4-4-4"/>',
 'social': '<path d="M4 4h16v12H8l-4 4z"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="12" x2="13" y2="12"/>',
}
MECH = [('webinar', 'Webinars', 'One live session that teaches, then makes one offer'),
        ('workshop', 'Workshops', 'A few live sessions where they build with you'),
        ('challenge', 'Challenges', 'Daily tasks for a few days, the offer on the last'),
        ('vsl', 'Video sales letters', 'The page gives before it asks'),
        ('guide', 'PDF guides', 'A free resource that earns the email'),
        ('launch', 'Courses and launches', 'Value videos, then a cart that opens and closes'),
        ('call', 'Book-a-call pages', 'Qualifying questions, then a consultative call'),
        ('community', 'Communities', 'A free group that teaches; the keenest step up'),
        ('social', 'Social following', 'Value posts build trust; warm DMs book calls')]
cards = ''.join(f'<div class="mech card"><svg class="mi" viewBox="0 0 24 24">{ICON[k]}</svg><span class="vk">{n}</span><span class="vl s">{d}</span></div>' for k, n, d in MECH)

section('a.html', 18, f'''<!-- 18 PROBLEM 2: CONVERSION MECHANISMS (replaces QS 18) -->
<section class="slide" id="s-quality" data-title="Problem 2: Conversion mechanisms" data-bg="dim" data-steps="1" data-reel="8">
  <div class="hero" data-only="0" data-a="fade"><img src="img/zombie.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t" style="top:300px;width:900px" data-only="0" data-a="words">Conversion <span class="a-e">mechanisms.</span></h2>
  <p class="b" style="top:540px;width:820px" data-only="0" data-a="rise" data-d=".6">Most send cold buyers straight to "book a call". <span class="a-e">Nothing warms them up first.</span></p>
  <h2 class="t" data-only="1" data-a="words">Pick the mechanism <span class="a">that fits your buyer.</span></h2>
  <div class="mechs" data-only="1" data-a="stagger" data-d=".3" data-st=".06">{cards}</div>
  <aside class="notes"><p><b>Minute 9. Problem 2.</b> "Camp two: the conversion mechanism. Most people push cold buyers straight to a call, and the call has to do everything." Click: "There are many ways to warm a buyer up before the ask: webinars, workshops, challenges, video sales letters, PDF guides, courses and launches, book-a-call pages, communities, a social following. Each fits a different buyer." From the Playbook's eight funnels.</p></aside>
</section>''')

section('a.html', 19, '''<!-- 19 PROBLEM 3: ORCHESTRATION (replaces QS 19) -->
<section class="slide" id="s-trial" data-title="Problem 3: End-to-end AI orchestration" data-bg="dim" data-steps="1" data-reel="8">
  <div class="hero shift" data-only="0" data-a="fade"><img src="img/nodial.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <div class="hero dimmed" data-only="1" data-a="fade"><img src="assets/os-core.webp" alt="" class="kb"><div class="shade f"></div><div class="shade l2"></div></div>
  <h2 class="t" style="top:240px;width:960px" data-only="0" data-a="words">End-to-end AI orchestration <span class="a-e">and growth.</span></h2>
  <p class="b" style="top:520px;width:800px" data-only="0" data-a="rise" data-d=".6">Tools that don't talk. Nobody running the funnel day to day. <span class="a-e">Nothing tested.</span></p>
  <h2 class="t" style="width:1100px" data-only="1" data-a="words">You need one agentic system <span class="a">that does all three.</span></h2>
  <div class="orch" data-only="1" data-a="stagger" data-d=".4" data-st=".14">
    <div class="card"><span class="n o-n2">Build</span><span class="vl s">every element of every stage of the funnel</span></div>
    <div class="card"><span class="n o-n2">Run</span><span class="vl s">the daily and weekly operations</span></div>
    <div class="card"><span class="n o-n2 a-s">Test</span><span class="vl s">every element, to lift the number at each stage</span></div>
  </div>
  <aside class="notes"><p><b>Minute 9. Problem 3.</b> "Camp three: orchestration. The tools don't talk to each other, nobody runs the funnel day to day, and nothing gets tested, so nothing improves." Click: "What you need is one agentic system that builds every element of the funnel, runs the daily and weekly operations, and tests every element to lift the number at each stage."</p></aside>
</section>''')

section('a.html', 20, '''<!-- 20 NOTHING CONNECTS (QS 20) -->
<section class="slide" id="s-nodial" data-title="Nothing connects, nothing compounds" data-bg="dim" data-reel="8">
  <div class="hero shift"><img src="img/darts.webp" alt="" class="kb"><div class="shade l2"></div></div>
  <h2 class="t w4" data-a="words">Nothing connects. <span class="a-e">Nothing compounds.</span></h2>
  <ul class="dash-list" style="top:380px" data-a="stagger" data-d=".7" data-st=".12">
    <li>Making it up as you go</li><li>Chasing new trends and growth hacks</li><li>Doing everything by hand</li><li class="a-e">No dial you can turn up on demand</li>
  </ul>
  <aside class="notes"><p><b>Minute 10. QS slide 20.</b> "You hope it works, because there's no dial you can turn up when you need more calls. Every new tactic starts you back at zero."</p></aside>
</section>''')

STAGES = [('01', 'Traffic engine', 'Cold email, calendar invites, LinkedIn, ads', 'Visit rate'),
          ('02', 'Landing and registration', 'Landing page, form, thank-you page', 'Sign-up rate'),
          ('03', 'Multi-channel nurture', 'Confirmation, email, WhatsApp and SMS reminders', 'Show-up rate'),
          ('04', 'Conversion mechanism', 'Webinar, workshop, VSL, call, challenge, launch', 'Booking rate'),
          ('05', 'Revenue engine', 'Pipeline, booking page, proposal, checkout', 'Close rate'),
          ('06', 'Long-term nurture', 'Newsletter, WhatsApp, re-engagement', 'Rebooking rate')]
st = ''.join(f'<div class="stg6 card"><span class="n s6-n">{a}</span><span class="vk">{b}</span><span class="vl s">{c}</span><span class="s6-k">{d}</span></div>' for a, b, c, d in STAGES)

section('a.html', 23, f'''<!-- 23 THE COMPLETE SYSTEM: THE FUNNEL OS (QS 23) -->
<section class="slide" id="s-system" data-title="The complete system: the Funnel OS" data-bg="dim" data-steps="1" data-reel="9">
  <h2 class="t" data-a="words">The complete system: <span class="a">the Funnel OS.</span></h2>
  <div class="stages6" data-a="stagger" data-d=".6" data-st=".1">{st}</div>
  <div class="osband card" data-step="1" data-a="rise">
    {TL}
    <div class="os-what"><span class="vk">One OS builds, runs and tests all six stages</span><span class="vl s">Knowledge, data, prompts, templates, automations, benchmarks and revenue equations</span></div>
    <div class="os-ai"><svg class="lgi"><use href="#lg-claude"/></svg><svg class="lgi"><use href="#lg-openai"/></svg><svg class="lgi"><use href="#lg-googlegemini"/></svg></div>
  </div>
  <aside class="notes"><p><b>Minute 11. QS slide 23.</b> "So what's the system? Every funnel has the same six stages: the traffic engine, landing and registration, nurture, the conversion mechanism, the revenue engine, and long-term nurture. Each has its own elements and its own number: visit rate, sign-up rate, show-up rate, booking rate, close rate, rebooking rate." Click: "The Funnel OS is one operating system that builds every element of every stage, runs it, and tests it: the knowledge, data, prompts, templates, automations, benchmarks and revenue equations my team builds funnels with. It runs in Claude, ChatGPT or Gemini. Today I'll walk you through it in three phases." Poll 2 runs here.</p></aside>
</section>''')

# phase lines on the three dividers
sub('slides/b.html', [('<h2 class="t" style="top:auto;bottom:210px;width:1200px" data-a="words" data-d=".5">Access your <span class="a">market.</span></h2>',
    '<h2 class="t" style="top:auto;bottom:250px;width:1200px" data-a="words" data-d=".5">Access your <span class="a">market.</span></h2>\n  <p class="b" style="top:auto;bottom:150px;width:1300px" data-a="rise" data-d="1">Phase 1 · Funnel OS stage 1: the traffic engine</p>')])
sub('slides/c.html', [('<h2 class="t" style="top:auto;bottom:210px;width:1200px" data-a="words" data-d=".5">Capture <span class="a">attention.</span></h2>',
    '<h2 class="t" style="top:auto;bottom:250px;width:1200px" data-a="words" data-d=".5">Capture <span class="a">attention.</span></h2>\n  <p class="b" style="top:auto;bottom:150px;width:1300px" data-a="rise" data-d="1">Phase 2 · stages 1 and 2: invites and registration</p>')])
sub('slides/d.html', [('<h2 class="t" style="top:auto;bottom:210px;width:1200px" data-a="words" data-d=".5">Build trust <span class="a">at scale.</span></h2>',
    '<h2 class="t" style="top:auto;bottom:250px;width:1200px" data-a="words" data-d=".5">Build trust <span class="a">at scale.</span></h2>\n  <p class="b" style="top:auto;bottom:150px;width:1500px" data-a="rise" data-d="1">Phase 3 · stages 3 to 6: nurture, the session, the sale, the follow-up</p>')])

# proof boosts: 34 Appster numbers, 47 two clients, 61 came live, 65 Rhenus numbers plus a case wall
sub('slides/b.html', [('<div class="tq-who"><span class="vk">Tom Alfoldi</span><span class="vl s">Founder &amp; CEO, Growth Factors by Appster</span><img src="assets/l/appster.webp" alt="Appster"></div>',
    '<div class="tq-who"><span class="vk">Tom Alfoldi</span><span class="vl s">Founder &amp; CEO, Growth Factors by Appster</span><img src="assets/l/appster.webp" alt="Appster"></div>\n      <div class="tq-m"><div><span class="n a-s">$25MN</span><span class="vl s">ARR in 2 years</span></div><div><span class="n">21%</span><span class="vl s">from the new consulting line</span></div><div><span class="n">10 to 60</span><span class="vl s">sales calls a month</span></div></div>')])
sub('slides/c.html', [('    <div><span class="n a-s">25</span><span class="vl s">sales calls</span></div>\n  </div>',
    '    <div><span class="n a-s">25</span><span class="vl s">sales calls</span></div><i class="arr"></i>\n    <div><span class="n a-s">2</span><span class="vl s">clients</span></div>\n  </div>')])
sub('slides/d.html', [('<div class="fc-row" data-a="stagger" data-d="1.5"><div><span class="n a-s">17</span><span class="vl s">sales calls in 3 episodes</span></div><div><span class="n">1 to 9</span><span class="vl s">calls per episode</span></div><div><span class="n">175</span><span class="vl s">programme applications</span></div></div>',
    '<div class="fc-row" data-a="stagger" data-d="1.5"><div><span class="n a-s">17</span><span class="vl s">sales calls in 3 episodes</span></div><div><span class="n">1 to 9</span><span class="vl s">calls per episode</span></div><div><span class="n">59 to 117</span><span class="vl s">came live per episode</span></div><div><span class="n">175</span><span class="vl s">programme applications</span></div></div>')])

WALL = [('ajit-thomas', 'cavli', '$15MN', 'ARR, from $1.5MN'), ('tom-alfoldi', 'appster', '$25MN', 'ARR in 2 years'), ('alexander-gesell', 'quantum-scaling', '$6MN', 'ARR in 3 years, from zero'),
        ('alan-stein', 'kadima', '$1.8MN', 'ARR, from under $0.5MN'), ('sachin-dutta', 'coinfirm', 'Acquired', 'by Lukka in 2024'), ('gabriel-fairman', 'wxrks', '2x', 'content reach in 2 months'),
        ('houston-golden', 'bamf', '$1MN+', 'ARR from one launch'), ('catalin-zorzini', 'ecommerce-platforms', '7MN+', 'visits a year'), ('shweta', 'growth-idea', '80', 'sales calls from webinars'),
        ('susanne', 'fintechcircle', '175', 'programme applications'), ('sailesh-paul', 'neural-it', '7x', 'more people live'), ('vivek-vanwari', 'salestherapy', '6', 'sales calls on webinar 1')]
wall = ''.join(f'<div class="wt card"><img class="wt-ph" src="assets/p/{p}.webp" alt=""><div class="wt-b"><img class="wt-lg" src="assets/l/{l}.webp" alt="{l}"><span class="n wt-n">{n}</span><span class="vl s">{t}</span></div></div>' for p, l, n, t in WALL)
p = f'{S}/slides/e.html'; s = open(p).read()
a = '<section class="slide" id="s-ceiling" data-title="Same machine. Bigger deals." data-bg="burst 520 640" data-reel="9">'
assert a in s
s = s.replace(a, '<section class="slide" id="s-ceiling" data-title="Same machine. Bigger deals." data-bg="burst 520 640" data-steps="1" data-reel="9">')
blk = re.search(r'(<section class="slide" id="s-ceiling".*?)(\n  <aside class="notes">)', s, flags=re.S)
body = blk.group(1)
body2 = body.replace('<div class="hero dimmed">', '<div class="hero dimmed" data-only="0" data-a="fade">')
body2 = body2.replace('<div class="pf-photo" data-a="fade" data-d=".2">', '<div class="pf-photo" data-only="0" data-a="fade" data-d=".2">')
body2 = body2.replace('<h2 class="t" style="left:700px;width:1080px" data-a="words" data-d=".4">Same machine.', '<h2 class="t" style="left:700px;width:1080px" data-only="0" data-a="words" data-d=".4">Same machine.')
body2 = body2.replace('<p class="b" style="left:700px;top:330px;width:1080px" data-a="rise" data-d=".9">', '<p class="b" style="left:700px;top:330px;width:1080px" data-only="0" data-a="rise" data-d=".9">')
body2 = body2.replace('<div class="ceil3" data-a="stagger" data-d="1.2">', '<div class="ceil3 c4" data-only="0" data-a="stagger" data-d="1.2">')
body2 = body2.replace('<div class="card"><span class="n">From zero</span><span class="vl s">a standing start on LinkedIn</span></div>',
                      '<div class="card"><span class="n">3 to 15</span><span class="vl s">sales calls a month</span></div>\n    <div class="card"><span class="n">60</span><span class="vl s">enterprise registrants per webinar</span></div>')
body2 = body2.replace('<span class="cap d" style="left:700px" data-a="fade" data-d="1.8">', '<span class="cap d" style="left:700px" data-only="0" data-a="fade" data-d="1.8">')
body2 += f'\n  <h2 class="t" data-only="1" data-a="words">And it works <span class="a">across industries.</span></h2>\n  <div class="wall" data-only="1" data-a="stagger" data-d=".3" data-st=".05">{wall}</div>\n  <span class="cap d" data-only="1" data-a="fade" data-d="1">From our case studies page</span>'
s = s[:blk.start(1)] + body2 + s[blk.end(1):]
s = s.replace('Source: the Rhenus case study on our pages (cases.json, Adi, 8 November 2026).</p></aside>', 'Click for the wall: twelve clients across software, agencies, coaching, legal and media, all from our case studies page.</p></aside>')
open(p, 'w').write(s)

# slide 73: the bonuses line
sub('slides/e.html', [('<div class="gift-mini" style="top:870px" data-a="stagger" data-d="1.4"><img src="assets/b/playbook-a.webp" alt=""><img src="assets/b/prompts-a.webp" alt=""><span class="vl s">Everyone who stayed gets the Playbook, the Prompt Library and the replay.</span></div>',
    '<div class="gift-mini" style="top:870px" data-a="stagger" data-d="1.4"><img src="assets/b/playbook-a.webp" alt=""><img src="assets/b/prompts-a.webp" alt=""><img src="assets/b/calculator-a.webp" alt=""><span class="vl s">Your bonuses arrive on WhatsApp and email, with a surprise.</span></div>')])

# the Tantra logo on every slide (mark plus wordmark)
b = open(R + '/tools/build.py').read()
b = b.replace('<div id="hud" aria-hidden="true"><img class="word" src="assets/tantra-word.webp" alt=""><span class="count">1</span></div>',
              '<div id="hud" aria-hidden="true"><span class="hudlogo"><img class="mk" src="assets/tantra-mark-white.webp" alt=""><img class="wd" src="assets/tantra-word.webp" alt=""></span><span class="count">1</span></div>')
open(R + '/tools/build.py', 'w').write(b)

css = '''
/* round 6 */
#hud .hudlogo { position: absolute; left: 140px; bottom: 34px; display: flex; align-items: center; gap: 14px; opacity: .92; }
#hud .hudlogo .mk { height: 50px; width: auto; }
#hud .hudlogo .wd { height: 26px; width: auto; }
#stage.is-light #hud .hudlogo img { filter: invert(1) brightness(.3); }
.tlock { display: inline-flex; align-items: center; gap: 12px; }
.tlock img:first-child { height: 58px; width: auto; }
.tlock img:last-child { height: 32px; width: auto; }
.host-glow { position: absolute; left: -140px; top: 60px; width: 1000px; height: 1000px; background: radial-gradient(closest-side, rgba(109,74,255,.42), rgba(109,74,255,0)); }
.host-cut { position: absolute; left: 70px; bottom: 0; height: 1040px; width: auto; filter: drop-shadow(0 30px 60px rgba(0,0,0,.6)); }
.journey3 { position: absolute; left: 820px; right: 140px; top: 380px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.jc { display: flex; flex-direction: column; gap: 18px; padding: 30px 28px; border-radius: 26px; background: rgba(18,20,29,.92); border: 1px solid var(--line-2); }
.jc.on { border-color: rgba(167,139,250,.7); box-shadow: 0 0 50px rgba(109,74,255,.3); }
.jc-lg { height: 64px; display: flex; align-items: center; }
.jc-lg > img { max-height: 54px; max-width: 100%; width: auto; object-fit: contain; }
.jc .vl { color: var(--text); }
.host-stats2 { position: absolute; left: 820px; right: 140px; top: 760px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.host-stats2 > div { display: flex; flex-direction: column; gap: 6px; }
.host-stats2 .n { font-size: 96px; }
.case2 { position: absolute; left: 140px; right: 140px; top: 270px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.cc { display: flex; gap: 28px; padding: 24px; border-radius: 30px; background: rgba(18,20,29,.94); border: 1px solid var(--line-2); }
.cc-ph { width: 230px; height: 300px; object-fit: cover; border-radius: 22px; flex: none; }
.cc-b { flex: 1; display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.cc-top { display: flex; flex-direction: column; gap: 8px; }
.cc-lg { height: 46px; width: auto; max-width: 260px; object-fit: contain; object-position: left center; }
.cc-m { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 22px; }
.cc-m > div { display: flex; flex-direction: column; gap: 4px; }
.cc-m .n { font-size: 52px; }
.cc-m .vl { line-height: 1.15; }
.marquee { position: absolute; left: 0; right: 0; top: 700px; display: flex; flex-direction: column; gap: 26px; -webkit-mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent); mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent); }
.mq-row { overflow: hidden; }
.mq-track { display: flex; gap: 70px; align-items: center; width: max-content; animation: mq 70s linear infinite; }
.mq-row:nth-child(2) .mq-track { animation-direction: reverse; animation-duration: 80s; }
.mq-track img { height: 58px; width: auto; max-width: 230px; object-fit: contain; opacity: .8; }
@keyframes mq { from { transform: translateX(0) } to { transform: translateX(-50%) } }
@media (prefers-reduced-motion: reduce) { .mq-track { animation: none; } }
.gifts { top: 400px; }
.g-img { height: 400px; }
.mechs { position: absolute; left: 140px; right: 140px; top: 330px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.mech { display: grid; grid-template-columns: 64px 1fr; grid-template-rows: auto auto; column-gap: 22px; row-gap: 6px; padding: 26px 30px; align-items: center; }
.mech .mi { grid-row: 1 / span 2; width: 64px; height: 64px; fill: none; stroke: var(--iris); stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; align-self: start; }
.mech .vl { line-height: 1.2; }
.orch { position: absolute; left: 140px; right: 140px; top: 470px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; }
.orch .card { padding: 40px 40px 46px; display: flex; flex-direction: column; gap: 14px; background: rgba(18,20,29,.9); min-height: 300px; }
.o-n2 { font-size: 96px; color: var(--iris); }
.stages6 { position: absolute; left: 140px; right: 140px; top: 330px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.stg6 { display: flex; flex-direction: column; gap: 14px; padding: 28px 24px; min-height: 420px; position: relative; }
.stg6 .vk { line-height: 1.12; }
.stg6 .vl { line-height: 1.22; }
.s6-n { font-size: 52px; color: var(--iris); }
.s6-k { margin-top: auto; align-self: flex-start; padding: 10px 16px; border-radius: 12px; background: rgba(52,211,153,.14); color: var(--signal); font: 600 36px/1.1 var(--font); }
.osband { position: absolute; left: 140px; right: 140px; top: 790px; height: 170px; padding: 24px 36px; display: flex; align-items: center; gap: 36px; border-color: rgba(167,139,250,.6); background: linear-gradient(100deg, rgba(109,74,255,.35), rgba(18,20,29,.94) 60%); }
.osband .os-what { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.osband .os-ai { display: flex; gap: 20px; }
.osband .os-ai .lgi { width: 56px; height: 56px; }
.tq-m { display: flex; gap: 46px; margin-top: 4px; }
.tq-m > div { display: flex; flex-direction: column; gap: 4px; }
.tq-m .n { font-size: 52px; }
.chain .n { font-size: 70px; }
.fc-row { grid-template-columns: repeat(4, 1fr); gap: 22px; }
.fc-row .n { font-size: 64px; }
.ceil3.c4 { grid-template-columns: repeat(2, 1fr); top: 440px; }
.ceil3.c4 .card { padding: 26px 30px; }
.wall { position: absolute; left: 140px; right: 140px; top: 290px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
.wt { display: flex; gap: 18px; padding: 18px; align-items: center; }
.wt-ph { width: 110px; height: 138px; object-fit: cover; border-radius: 16px; flex: none; }
.wt-b { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.wt-lg { height: 34px; width: auto; max-width: 180px; object-fit: contain; object-position: left center; opacity: .85; margin-bottom: 4px; }
.wt-n { font-size: 52px; color: var(--signal); }
.wt .vl { line-height: 1.15; }
.gift-mini img { height: 118px; }
'''
open(f'{S}/v3.css', 'a').write(css)
print('round 6 applied')
