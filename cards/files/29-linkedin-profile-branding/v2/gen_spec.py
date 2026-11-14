"""Writes v2/PROFILE_SPEC.md: every LinkedIn field for the six profiles and the Tantra company page, from
v1 copy.json (approved Abouts), v2 copy.json (images and Featured), card 06 copy.json and funnel-config.json.
Run: python3 deliverables/29-linkedin-profile-branding/v2/gen_spec.py"""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[2]
v1 = json.loads((HERE.parent / 'copy.json').read_text())
v2 = json.loads((HERE / 'copy.json').read_text())
co = json.loads((ROOT / 'deliverables/06-company-page/copy.json').read_text())
cfg = json.loads((ROOT / 'deliverables/_shared/funnel-config.json').read_text())
W = cfg['webinar']
WHEN = f"every {W['day_of_week']} at {W['start_time_local']} UK time"
REG = cfg['domains']['funnel_domain'] + '/'
# Organic traffic (LinkedIn profiles, content) goes to jointantra.com: same site as REG, same Worker, no redirect (Adi 2026-11-14).
ORG = 'https://jointantra.com/'
BOOK = cfg['booking']['round_robin_url']
utm = lambda base, medium, content: f"{base}?utm_source=linkedin&utm_medium={medium}&utm_campaign=enterprise-webinar&utm_content={content}"

# Titles: Adi 2026-11-13, word for word. Experience title = TITLES[k], company = the Tantra page.
TITLES = {
    'adi': 'Leading the team', 'bhaskar': 'Leading marketing & product', 'nelbin': 'Leading marketing ops',
    'aquila': 'Leading automations', 'bharath': 'Leading development', 'ben': 'Leading development',
}
HEADLINES = {
    'adi': 'Leading the team @ Tantra | AI RevOps that turns cold traffic into booked calls and closed revenue | 400+ brands, 21+ countries | Join my live AI RevOps workshop: link below 👇',
    'bhaskar': 'Leading marketing & product @ Tantra | Marketing that books sales calls, not vanity leads | AI RevOps for B2B teams | Join our live AI RevOps workshop: link below 👇',
    'nelbin': 'Leading marketing ops @ Tantra | An owner, a checklist and a weekly number for every funnel stage | AI RevOps for B2B teams | Live workshop: link below 👇',
    'aquila': 'Leading automations @ Tantra | I automate the reminders, follow ups and handoffs B2B teams still do by hand | AI RevOps | Live workshop: link below 👇',
    'bharath': 'Leading development @ Tantra | The CRM, integrations and AI agents behind every Tantra funnel | AI RevOps for B2B teams | Live workshop: link below 👇',
    'ben': 'Leading development @ Tantra | Pages, forms and tracking that turn clicks into booked calls | AI RevOps for B2B teams | Live workshop: link below 👇',
}
# First person role lines in the v1 Abouts and role lines that named the old titles.
ROLE_FIX = {
    "I'm the CMO at Tantra.": "I lead marketing and product at Tantra.",
    "I'm the CTO at Tantra.": "I lead development at Tantra.",
    "I run operations at Tantra.": "I run marketing operations at Tantra.",
    "I lead technology: the stack,": "I lead development: the stack,",
    "I run operations: an owner,": "I run marketing operations: an owner,",
    "I lead marketing: the content,": "I lead marketing and product: the content,",
}
SKILLS = {
    'adi': ['AI RevOps', 'Webinar Marketing', 'Sales Funnel Strategy', 'RevOps', 'Lead Generation'],
    'bhaskar': ['Marketing Strategy', 'Webinar Marketing', 'Lead Generation', 'Content Marketing', 'Marketing Analytics'],
    'nelbin': ['Operations Management', 'RevOps', 'Process Improvement', 'Project Management', 'Marketing Operations'],
    'aquila': ['Marketing Automation', 'Workflow Automation', 'CRM', 'AI Agents', 'Email Marketing'],
    'bharath': ['Software Architecture', 'CRM Integration', 'AI Agents', 'API Development', 'Cloud Infrastructure'],
    'ben': ['Web Development', 'Landing Page Optimization', 'Conversion Rate Optimization', 'A/B Testing', 'Web Analytics'],
}


def fill(s):
    s = s.replace('{{when_cap}}', WHEN[0].upper() + WHEN[1:]).replace('{{when}}', WHEN).replace('{{minutes}}', str(W['duration_minutes'])).replace('{{day}}', W['day_of_week'])
    return s


def capline(k):
    c = v2['captions'][v2['caption_by_asset'][k]]
    head = ' '.join(c['lines'] + c['em']) if 'lines' in c else f"{c['line1']} {c['line2']}"
    return (head + (f" / {c['bar']}" if c.get('bar') else ' (one size, no bar)') + ' (caption test, Adi 2026-11-13)')


def fixroles(t):
    for a, b in ROLE_FIX.items():
        t = t.replace(a, b)
    return t


# Tracked short links in the Tantra CRM (campaign "LinkedIn organic: team profiles", cmp_f427ef8e47514047be1d), Adi 2026-11-14.
# go.usetantra.com/l/<key>-<spot>: f featured, w website, a about, r role; w workshop (jointantra.com), c consultation.
# Each redirects to the destination with utm_source=linkedin, utm_medium=profile, utm_campaign=enterprise-webinar,
# utm_content=<key>-<where>-<kind>, plus the CRM click id, so clicks and leads report per person and per spot.
SHORT = 'https://go.usetantra.com/l/'


def L(k, where, kind='workshop', medium='profile'):
    return SHORT + f"{k}-{where[0]}{kind[0]}"


def LONG(k, where, kind='workshop', medium='profile'):
    return utm(ORG if kind == 'workshop' else BOOK, medium, f"{k}-{where}-{kind}")


def about(p):
    k = p['key']
    a = fixroles(fill(p['about']))
    a = a.replace('runs a live', 'runs a live').replace('live webinar', 'live AI RevOps workshop')
    a = re.sub(r'\n\nSave your seat: \S+$', '', a)
    return a + ("\n\nTwo ways in:\n→ Join the live AI RevOps workshop: " + L(k, 'about') +
                "\n→ Book an AI revenue strategy consultation: " + L(k, 'about', 'consultation'))


def check(name, text, limit):
    bad = [c for c in text if c in (chr(0x2013), chr(0x2014))]
    return f"{len(text)} / {limit} characters" + (' OVER LIMIT' if len(text) > limit else '') + (' HAS A DASH' if bad else '')


out = ["# LinkedIn Profile and Company Page Spec (v2, 13 November 2026)", "",
       "Generated by `gen_spec.py`. Every field, in LinkedIn's order, for the six profiles and the Tantra company page. "
       "Images are in `assets/`; how they are built is in `README.md`. No em or en dashes anywhere.", "",
       "## What Changed From v1 (Corrections)", "",
       "| Field | v1 said | v2 says, and why |", "| --- | --- | --- |",
       "| Cover | Text only, no people | The person twice (AI avatar portrait left, AI side profile at the right edge), one shared caption and two rows of client logos (Google, Amazon, Techstars, upGrad and more) |",
       "| Featured | One item: \"Live Webinar: From Cold List to Booked Sales Calls\" | Two items: the live AI RevOps workshop (with bonus previews) and the strategy consultation |",
       "| Booking link | Cal.com (PROOF_PACK section 6 still says a 30-minute call on Cal.com) | " + BOOK + " (45 minutes, Tantra CRM group calendar, funnel-config 2026-11-11). PROOF_PACK section 6 is out of date |",
       "| Company cover size | 1128 x 191 in some notes | 4200 x 700 (6:1), the size card 06 verified in LinkedIn Help; a 1200 x 200 copy is included |",
       "| Adi's website links | growthclub.org and an old booking link (read 2026-11-05) | Workshop registration and the consultation booking link (below) |",
       "| About endings | One link to the webinar | Two links: workshop and consultation |",
       "| Headlines | Webinar framing | AI RevOps framing, still pointing to Featured |",
       "| Titles | CTO, CMO, Head of Operations, Automation Lead, Development Lead | Adi 2026-11-13: Leading the team (Adi), Leading marketing & product (Bhaskar), Leading automations (Aquila), Leading development (Bharath, Ben), Leading marketing ops (Nelbin) |", "",
       "## Shared by All Six Profiles", "",
       f"- **Cover**: `assets/<key>-cover-1584x396.png` (LinkedIn recommends 1584 x 396, max 8 MB). Upload the `@2x` file if LinkedIn accepts it; it is sharper on retina screens.",
       f"- **Featured 1** (Add a link): URL = the \"Lands on\" link of Featured 1 in your Links table (LinkedIn cannot preview go.usetantra.com short links yet, so Featured uses the full UTM link), image `assets/featured-workshop-1200x627.png`, title \"{v2['workshop']['featured_title']}\", description \"{v2['workshop']['featured_description']}\" ({check('', v2['workshop']['featured_description'], 200)})",
       f"- **Featured 2** (Add a link): URL = the \"Lands on\" link of Featured 2 in your Links table, image `assets/featured-consultation-1200x627.png`, title \"{v2['consult']['featured_title']}\", description \"{v2['consult']['featured_description']}\" ({check('', v2['consult']['featured_description'], 200)})",
       "- Remove every older Featured item that points to GrowthClub or a past event.",
       f"- **Contact info, Website**: add the workshop link (type: Company) and the consultation link (type: Other) from your Links table; LinkedIn no longer allows custom labels. Remove growthclub.org links and any old Cal.com link.",
       "- **Custom button** (only shows with Premium or Creator tools): \"Visit my website\", the workshop link with `utm_content=<key>-button`.",
       "- **Experience, current role**: Company = the Tantra page (https://www.linkedin.com/company/13588687/, pick it from the dropdown so the logo shows, never free text), Employment type Full time, Location Kochi, Kerala, India unless the person says otherwise, Location type as true for them, \"Ends current position as\" off. Add the two Featured images as Media on the role.",
       "- **Profile language**: English. **Open to**: leave as each person has it.", ""]

for p in v1['people']:
    k = p['key']
    h = HEADLINES[k]
    ab = about(p)
    exp = p['experience']
    desc = (fixroles(exp['role_line']).replace('live webinar', 'live AI RevOps workshop') + "\n\nTantra builds AI revenue systems with B2B teams: traffic, capture, nurture, the live session and the pipeline, "
            "wired into one CRM with one weekly number for every stage. The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries."
            f"\n\nSee it live: {L(k, 'role')}")
    out += [f"## {p['name']} ({p['url']})", "",
            "| Field | Value | Check |", "| --- | --- | --- |",
            f"| Profile photo | Keep the current photo if it is a clear, front facing headshot; otherwise use the Drive folder photo the cover uses (`src/cutouts/{k}.png` source) | |",
            f"| Cover | `assets/{k}-cover-1584x396.png`, caption: {capline(k)} | Verified in desktop and phone mock (`shots/mock-{k}.png`) |",
            f"| Headline | {h.replace('|', '\\|')} | {check('', h, 220)} |",
            f"| Experience title | {TITLES[k]} | Adi 2026-11-13; company field = the Tantra page |",
            f"| Top skills (5) | {', '.join(SKILLS[k])} | Add the same five to the Tantra role's skills |", "",
            f"**Links for {p['name'].split()[0]}** (organic traffic goes to jointantra.com; every link carries its own utm_content):", "",
            "Use the short link everywhere except Featured: LinkedIn cannot build a preview from go.usetantra.com yet, so the two Featured items use their \"Lands on\" link.", "",
            "| Where | Short link (use this) | Lands on (UTMs added by the CRM) |", "| --- | --- | --- |",
            *[f"| {lab} | {L(k, w, kd)} | {LONG(k, w, kd)} |" for lab, w, kd in [
                ('Featured 1, workshop', 'featured', 'workshop'), ('Featured 2, consultation', 'featured', 'consultation'),
                ('Contact info website (Company)', 'website', 'workshop'), ('Contact info website (Other)', 'website', 'consultation'),
                ('About, workshop line', 'about', 'workshop'), ('About, consultation line', 'about', 'consultation'),
                ('Role description and role media, workshop', 'role', 'workshop'), ('Role media, consultation', 'role', 'consultation')]], "",
            "**About** (" + check('', ab, 2600) + "):", "", "```text", ab, "```", "",
            "**Experience description** (" + check('', desc, 2000) + "):", "", "```text", desc, "```", ""]

# Evangelists (Adi 2026-11-14): Scott and Conor, title "Evangelist" at the Tantra page. No AI avatar or photo yet, so
# their covers use the team face strips (build.mjs evangelistCover). Their links are the full jointantra.com UTM
# links (LONG); CRM short links can be added later. Never mention how they are paid.
EVANGELIST_SYSTEM = ("→ Traffic: calendar invites, cold email and LinkedIn, sent from your own accounts\n"
                     "→ Capture: registration and booking pages that feed one CRM\n"
                     "→ Nurture: email and WhatsApp reminders and follow ups that run on their own\n"
                     "→ Conversion: a weekly live session that ends in booked sales calls\n"
                     "→ Pipeline: every booking, call and proposal tracked to the deal")
EVANGELISTS = [
    {'key': 'scott', 'name': 'Scott McArthur',
     'headline': 'Evangelist @ Tantra | I help B2B founders turn cold traffic into booked sales calls with AI RevOps | 400+ brands, 21+ countries | Join our live AI RevOps workshop: link below 👇',
     'skills': ['B2B Sales', 'Sales Strategy', 'RevOps', 'Lead Generation', 'Consultative Selling'],
     'about': ("Most founders I speak with don't have a lead problem. They have a follow up problem.\n\n"
               "The traffic is there. People visit, download, register, even reply once. Then nobody gets back to them at the right moment, and the pipeline quietly goes cold.\n\n"
               "I'm an Evangelist at Tantra. I spend my days with B2B founders and revenue leaders, looking at how their pipeline actually runs, stage by stage, and showing them where AI can take over the repetitive work.\n\n"
               "Tantra builds AI revenue systems with B2B teams:\n" + EVANGELIST_SYSTEM + "\n\n"
               "The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries.\n\n"
               "If you want to see the whole system working before you talk to anyone, join our live AI RevOps workshop. If you'd rather talk it through for your own business, book a strategy consultation and we'll map where your pipeline leaks."),
     'role': "I work with B2B founders and revenue leaders to map how their pipeline runs today, and which parts AI should run for them."},
    {'key': 'conor', 'name': 'Conor Norton',
     'headline': 'Evangelist @ Tantra | AI RevOps for B2B teams: more booked calls from the traffic you already have | 400+ brands, 21+ countries | Join our live AI RevOps workshop: link below 👇',
     'skills': ['Business Development', 'B2B Sales', 'Sales Funnel Strategy', 'CRM', 'Lead Generation'],
     'about': ("Every week I talk to B2B teams who are doing everything right on paper. The posts go out, the ads run, the inbox fills up. And the number that matters, booked calls with the right people, barely moves.\n\n"
               "Almost every time, the gap sits between the first click and the first conversation. Reminders that never went out. Follow ups that depend on someone remembering. Leads that went cold in a spreadsheet.\n\n"
               "I'm an Evangelist at Tantra. My job is to understand how your revenue engine works today and show you, plainly, which parts AI can run for you and which still need your team.\n\n"
               "What Tantra builds with you:\n" + EVANGELIST_SYSTEM + "\n\n"
               "The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries.\n\n"
               "The easiest way to see it is our live AI RevOps workshop: we take the whole funnel apart on screen. Or book a strategy consultation and we'll look at your numbers together."),
     'role': "I help B2B teams see where their pipeline leaks between the first click and the first call, and what AI can run for them."},
]
for ev in EVANGELISTS:
    k = ev['key']
    ab = ev['about'] + ("\n\nTwo ways in:\n→ Join the live AI RevOps workshop: " + LONG(k, 'about') +
                        "\n→ Book an AI revenue strategy consultation: " + LONG(k, 'about', 'consultation'))
    desc = (ev['role'] + "\n\nTantra builds AI revenue systems with B2B teams: traffic, capture, nurture, the live session and the pipeline, "
            "wired into one CRM with one weekly number for every stage. The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries."
            f"\n\nSee it live: {LONG(k, 'role')}")
    h = ev['headline']
    out += [f"## {ev['name']} (Evangelist, your own LinkedIn profile)", "",
            "| Field | Value | Check |", "| --- | --- | --- |",
            "| Profile photo | Keep your current photo if it is a clear, front facing headshot (a branded one can be made from a photo you share) | |",
            f"| Cover | `assets/{k}-cover-1584x396.png` (the team, the caption and client logos), caption: {capline(k)} | Verified in desktop and phone mock (`shots/mock-{k}.png`) |",
            f"| Headline | {h.replace('|', '\\|')} | {check('', h, 220)} |",
            "| Experience title | Evangelist | Adi 2026-11-14; company field = the Tantra page |",
            "| Location | Keep your own | |",
            f"| Top skills (5) | {', '.join(ev['skills'])} | Add the same five to the Tantra role's skills |", "",
            f"**Links for {ev['name'].split()[0]}** (organic traffic goes to jointantra.com; every link carries its own utm_content):", "",
            "Use these links as they are, in every place listed. Never shorten them or drop the utm parameters.", "",
            "| Where | Short link (use this) | Lands on (UTMs added by the CRM) |", "| --- | --- | --- |",
            *[f"| {lab} | {LONG(k, w, kd)} | {LONG(k, w, kd)} |" for lab, w, kd in [
                ('Featured 1, workshop', 'featured', 'workshop'), ('Featured 2, consultation', 'featured', 'consultation'),
                ('Contact info website (Company)', 'website', 'workshop'), ('Contact info website (Other)', 'website', 'consultation'),
                ('About, workshop line', 'about', 'workshop'), ('About, consultation line', 'about', 'consultation'),
                ('Role description and role media, workshop', 'role', 'workshop'), ('Role media, consultation', 'role', 'consultation')]], "",
            "**About** (" + check('', ab, 2600) + "):", "", "```text", ab, "```", "",
            "**Experience description** (" + check('', desc, 2000) + "):", "", "```text", desc, "```", ""]

cab = fill(co['about']).replace("Our team has built", "Our team has built").replace('Start with the webinar: ' + 'https://webinar.sellwithtantra.com', f"Start with the live workshop: {SHORT}tantra-aw\nOr book an AI revenue strategy consultation: {SHORT}tantra-ac")
out += ["## Tantra Company Page (https://www.linkedin.com/company/13588687/)", "",
        "Card 06 (`deliverables/06-company-page/ADMIN_STEPS.md`) has the click path and LinkedIn's rename rules. v2 changes only the cover, the button and the About ending.", "",
        "| Field | Value | Check |", "| --- | --- | --- |",
        f"| Name | {co['name']} | Rename rules in card 06 step 2 |",
        f"| Tagline | {co['tagline']} | {check('', co['tagline'], 120)} |",
        "| Logo | `deliverables/06-company-page/assets/tantra-logo-400-light.png` (400 x 400) | |",
        "| Cover | `assets/tantra-company-cover-strips-violet-4200x700.png` (A2, face strips graded violet; Adi 2026-11-13). Caption: " + capline('company') + ". Alternates A1 `strips`, B1 `panels`, B2 `glow`, B3 `tiles`; 1200 x 200 fallbacks beside them | Verified in mock (`shots/mock-company.png`), under 3 MB |",
        f"| Website | {co['website']} | |",
        f"| Industry | {co['industry']} | Replaces Marketing Services |",
        f"| Company size | {co['company_size']} | |",
        "| Company type, Year founded | Privately held, 2018 (page shows 2024 today; Adi 2026-11-13: change to 2018) | |",
        "| Headquarters address | FILL: funnel-config `brand.legal_footer_address` is still empty. Adi supplies the registered address; until then keep the existing location | Blocked on Adi |",
        f"| Specialties | {', '.join(co['specialties'])} | {len(co['specialties'])} of 20 |",
        f"| Custom button | Register, {SHORT}tantra-btn | Tracked short link to jointantra.com, Adi 2026-11-14 |",
        f"| Featured / pinned post | Card 06 pinned post, with `assets/featured-workshop-1200x627.png` as its image | |", "",
        "**About** (" + check('', cab, 2000) + "):", "", "```text", cab, "```", ""]
(HERE / 'PROFILE_SPEC.md').write_text('\n'.join(out) + '\n')
print('PROFILE_SPEC.md written;', sum('OVER LIMIT' in l or 'HAS A DASH' in l for l in out), 'limit or dash problems')
