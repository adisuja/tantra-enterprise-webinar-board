"""Writes v2/branding_seed.json: card 29's eight people and the Tantra page as Tantra Branding projects
(POST /api/branding/import in tantra-crm, docs/crm/branding/PRD_BRANDING.md). Same source as PROFILE_SPEC.md:
it imports gen_spec.py (which rewrites PROFILE_SPEC.md as a side effect, unchanged).
Each element gets `reference` (the approved spec) and, where it is known, `current` (live on LinkedIn): Adi's profile
and the Tantra page were edited live on 13 and 14 Nov, so they match the spec; the others carry the 13 Nov audit
headline. Images point at the team pack and are marked as checked by hand on card 29. No consent is recorded here:
each person confirms their AI avatar consent in the Brand tab intake.
Run: python3 deliverables/29-linkedin-profile-branding/v2/branding_seed.py"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import gen_spec as g  # noqa: E402

PACK = 'https://adisuja.github.io/tantra-enterprise-webinar-pages/linkedin-profiles/v2/assets/'
CAMPAIGN, CHANNEL = 'cmp_f427ef8e47514047be1d', 'chn_c1118abc4dc74c06a10b'
DEST = {'workshop': g.ORG, 'consultation': g.BOOK}
CHECKED = 'card 29, checked by eye in the desktop and phone mock (13 to 14 Nov): no label text, logos inside chips, caption fits'


def captions():
    out = {}
    for k, c in g.v2['captions'].items():
        out[k] = ' '.join(c['lines'] + c['em']) if 'lines' in c else f"{c['line1']} {c['line2']}"
    return out


CAPS = captions()


def caption(k):
    chosen = CAPS[g.v2['caption_by_asset'][k]]
    return {'options': [chosen] + [c for c in CAPS.values() if c != chosen], 'chosen': chosen}


def image(name, w, h):
    return {'image': PACK + name, 'meta': {'checked': CHECKED, 'width': w, 'height': h}}


def audit_headlines():
    """The 'Now' headline per person from AUDIT.md (13 Nov, before the edits)."""
    text = (HERE / 'AUDIT.md').read_text()
    names = {'Adithya Murali': 'adi', 'Bharath Krishna Pai': 'bharath', 'Bhaskar Dev': 'bhaskar', 'Nelbin Joseph': 'nelbin', 'Aquila Eldho': 'aquila', 'Ben Basil Tomy': 'ben'}
    out = {}
    for sec in re.split(r'\n## ', text):
        head = sec.split('\n', 1)[0]
        key = next((v for n, v in names.items() if head.startswith(n)), None)
        m = re.search(r'^\| Headline \| (.+?) \| ', sec, re.M)
        if key and m:
            out[key] = m.group(1).replace('\\|', '|').strip()
    return out


NOW = audit_headlines()


def links(k, short=True):
    f = g.L if short else g.LONG
    return {'featured_workshop': f(k, 'featured'), 'featured_consultation': f(k, 'featured', 'consultation'),
            'website_workshop': f(k, 'website'), 'website_consultation': f(k, 'website', 'consultation'),
            'about_workshop': f(k, 'about'), 'about_consultation': f(k, 'about', 'consultation'),
            'role_workshop': f(k, 'role'), 'role_consultation': f(k, 'role', 'consultation')}


def profile(k, name, url, title, headline, about, desc, skills, lk, has_photo, answers, live):
    ref = {
        'cover': image(f'{k}-cover-1584x396.png', 1584, 396),
        'caption': caption(k),
        'headline': headline, 'about': about, 'role_title': title, 'role_description': desc, 'skills': skills,
        'featured_1': {'title': g.v2['workshop']['featured_title'], 'description': g.v2['workshop']['featured_description'], 'url': lk['featured_workshop'], 'image': PACK + 'featured-workshop-1200x627.png'},
        'featured_2': {'title': g.v2['consult']['featured_title'], 'description': g.v2['consult']['featured_description'], 'url': lk['featured_consultation'], 'image': PACK + 'featured-consultation-1200x627.png'},
        'website_1': {'url': lk['website_workshop'], 'type': 'Company'},
        'website_2': {'url': lk['website_consultation'], 'type': 'Other'},
    }
    if has_photo:
        ref['photo'] = image(f'{k}-photo-1200.png', 1200, 1200)
    els = {key: {'reference': v} for key, v in ref.items()}
    if live:
        for key in els:
            els[key]['current'] = ref[key]
    elif k in NOW:
        els['headline']['current'] = NOW[k]
    return {'person_key': k, 'name': name, 'kind': 'profile', 'profile_url': url, 'title': title,
            'campaign_id': CAMPAIGN, 'channel_id': CHANNEL,
            'context': {'answers': answers, 'sources': {a: 'seed' for a in answers}, 'destinations': DEST, 'links': lk, 'utm_campaign': 'enterprise-webinar', 'seed': 'card 29 PROFILE_SPEC.md and AUDIT.md, 15 Nov 2026'},
            'elements': els}


def answers_for(k, title, role):
    return {'company': 'Tantra', 'title': title, 'offer': 'Join the live AI RevOps workshop, or book an AI revenue strategy consultation',
            'audience': 'B2B founders and revenue leaders', 'pain': 'Leads go cold between the first click and the first call',
            'proof': '400+ brands, 47+ industries, 21+ countries. Client logos approved 7 Nov: Google, Amazon, Techstars, upGrad and the "Brands We\'ve Helped Grow" set',
            'role': role, 'links': f"{g.ORG} and {g.BOOK}", 'voice': '"I" and "you", open on a specific pain, plain words, one focal action, no AI filler'}


projects = []
for p in g.v1['people']:
    k = p['key']
    ab = g.about(p)
    role = g.fixroles(p['experience']['role_line']).replace('live webinar', 'live AI RevOps workshop')
    desc = (role + "\n\nTantra builds AI revenue systems with B2B teams: traffic, capture, nurture, the live session and the pipeline, "
            "wired into one CRM with one weekly number for every stage. The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries."
            f"\n\nSee it live: {g.L(k, 'role')}")
    projects.append(profile(k, p['name'], p['url'], g.TITLES[k], g.HEADLINES[k], ab, desc, g.SKILLS[k], links(k), True,
                            answers_for(k, g.TITLES[k], role), live=(k == 'adi')))

# Scott and Conor: their 16 short links exist since 15 Nov (open item 7).
SHORT_EVANGELISTS = True
for ev in g.EVANGELISTS:
    k = ev['key']
    lk = links(k, short=SHORT_EVANGELISTS)
    ab = ev['about'] + ("\n\nTwo ways in:\n→ Join the live AI RevOps workshop: " + lk['about_workshop'] + "\n→ Book an AI revenue strategy consultation: " + lk['about_consultation'])
    desc = (ev['role'] + "\n\nTantra builds AI revenue systems with B2B teams: traffic, capture, nurture, the live session and the pipeline, "
            "wired into one CRM with one weekly number for every stage. The team behind it has built funnels and outreach for 400+ brands in 47+ industries across 21+ countries."
            f"\n\nSee it live: {lk['role_workshop']}")
    projects.append(profile(k, ev['name'], None, 'Evangelist', ev['headline'], ab, desc, ev['skills'], lk, False, answers_for(k, 'Evangelist', ev['role']), live=False))

co = g.co
page_ref = {
    'logo': {'image': 'https://adisuja.github.io/tantra-enterprise-webinar-pages/company-page/assets/tantra-logo-400-light.png', 'meta': {'checked': CHECKED}},
    'cover': image('tantra-company-cover-strips-violet-4200x700.png', 4200, 700),
    'caption': caption('company'),
    'tagline': co['tagline'], 'overview': g.cab, 'specialties': co['specialties'], 'founded': '2018',
    'button': {'label': 'Register', 'url': g.SHORT + 'tantra-btn'},
}
projects.append({'person_key': 'tantra', 'name': co['name'], 'kind': 'page', 'profile_url': 'https://www.linkedin.com/company/13588687/',
                 'campaign_id': CAMPAIGN, 'channel_id': CHANNEL,
                 'context': {'answers': {'company': 'Tantra', 'offer': 'Register for the live AI RevOps workshop', 'audience': 'B2B founders and revenue leaders',
                                         'pain': 'Leads go cold between the first click and the first call', 'proof': '400+ brands, 47+ industries, 21+ countries',
                                         'links': f"{g.ORG} and {g.BOOK}"},
                             'destinations': DEST, 'links': {'about_workshop': g.SHORT + 'tantra-aw', 'about_consultation': g.SHORT + 'tantra-ac', 'button_workshop': g.SHORT + 'tantra-btn'},
                             'utm_campaign': 'enterprise-webinar', 'seed': 'card 29 and card 06, 15 Nov 2026'},
                 'elements': {key: {'reference': v, 'current': v} for key, v in page_ref.items()}})

bad = [(p['person_key'], key) for p in projects for key, e in p['elements'].items() if re.search('[–—]', json.dumps(e['reference'], ensure_ascii=False))]
(HERE / 'branding_seed.json').write_text(json.dumps({'projects': projects}, ensure_ascii=False, indent=1) + '\n')
print(f'branding_seed.json written: {len(projects)} projects; dash problems: {bad or "none"}')
