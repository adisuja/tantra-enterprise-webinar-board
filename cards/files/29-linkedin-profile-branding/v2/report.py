"""Builds the card 29 v2 team report (one HTML page plus every image) into a folder for static hosting.
Run: python3 deliverables/29-linkedin-profile-branding/v2/report.py <out_dir>
Published at https://adisuja.github.io/tantra-enterprise-webinar-pages/linkedin-profiles/v2/"""
import html, json, pathlib, re, shutil, sys, datetime
import markdown

HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path(sys.argv[1])
copy = json.loads((HERE / 'copy.json').read_text())
V = datetime.datetime.now().strftime('%Y%m%d%H%M')
md = lambda t: markdown.markdown(t, extensions=['tables', 'fenced_code'])
e = html.escape

if OUT.exists():
    shutil.rmtree(OUT)
for d in ('assets', 'shots'):
    shutil.copytree(HERE / d, OUT / d, ignore=shutil.ignore_patterns('*-guides*'))
for f in ('PROFILE_SPEC.md', 'TEAM_GUIDE.md', 'li-upload.sh'):
    shutil.copy(HERE / f, OUT / f)

spec = (HERE / 'PROFILE_SPEC.md').read_text()
parts = re.split(r'^## ', spec, flags=re.M)
sec = {p.split('\n', 1)[0]: p.split('\n', 1)[1] for p in parts[1:]}
find = lambda name: next(v for k, v in sec.items() if k.startswith(name))

PEOPLE = [('adi', 'Adithya Murali', 'Leading the team'), ('bhaskar', 'Bhaskar', 'Leading marketing & product'),
          ('aquila', 'Aquila Eldho', 'Leading automations'), ('bharath', 'Bharath', 'Leading development'),
          ('ben', 'Ben Basil Tomy', 'Leading development'), ('nelbin', 'Nelbin', 'Leading marketing ops'),
          ('scott', 'Scott McArthur', 'Evangelist'), ('conor', 'Conor Norton', 'Evangelist')]
NOPHOTO = {'scott', 'conor'}  # no photo yet: their cover only (the team strips stand in for them)
COVERS = [('strips-violet', 'A2: face strips, violet grade', True), ('strips', 'A1: face strips, natural colour', False),
          ('panels', 'B1: side profiles on violet panels', False), ('glow', 'B2: side profiles on the dark background', False), ('tiles', 'B3: side profiles on stacked bright tiles (earlier, does not blend)', False)]


def img(p, alt=''):
    return f'<a href="{p}?v={V}" target="_blank"><img src="{p}?v={V}" alt="{e(alt)}" loading="lazy"></a>'


def dl(*files):
    return '<p class="dl">' + ' &#183; '.join(f'<a href="{f}?v={V}" download>{e(label)}</a>' for f, label in files) + '</p>'


people = ''
for k, name, title in PEOPLE:
    body = find(name.split()[0])
    people += f'''<section id="{k}"><h3>{e(name)}: {e(title)} @ Tantra</h3>
<div class="pc">{'' if k in NOPHOTO else img(f'assets/{k}-photo-1200.png', name + ' photo')}<div>{img(f'assets/{k}-cover-1584x396.png', name + ' cover')}</div></div>
{dl(*[x for x in ((f'assets/{k}-cover-1584x396@2x.png', 'Cover, upload this (3168 x 792)'), None if k in NOPHOTO else (f'assets/{k}-photo-1200.png', 'Profile photo 1200 x 1200'), (f'shots/mock-{k}.png', 'How the cover looks on LinkedIn')) if x])}
<details><summary>{e(name)}'s fields: headline, About, experience, skills</summary>{md(body)}</details></section>'''

covers = ''.join(f'''<div class="opt{' pick' if pick else ''}"><h4>{e(label)}{' (chosen)' if pick else ''}</h4>{img(f'assets/tantra-company-cover-{v}-1200x200.png', label)}
{dl((f'assets/tantra-company-cover-{v}-4200x700.png', 'Upload size 4200 x 700'), (f'assets/tantra-company-cover-{v}-1200x200.png', '1200 x 200'), (f'assets/tantra-collage-{v}-1330x700.png', 'Collage alone'))}</div>''' for v, label, pick in COVERS)

WHO = {'adi': 'Adi', 'nelbin': 'Nelbin', 'bhaskar': 'Bhaskar', 'bharath': 'Bharath', 'aquila': 'Aquila', 'ben': 'Ben', 'scott': 'Scott', 'conor': 'Conor', 'company': 'Tantra company page'}
test = ''.join(f"<tr><td>{e(' '.join(c['lines'] + c['em']) if 'lines' in c else c['line1'] + ' ' + c['line2'])}</td><td>{e(c.get('bar') or 'none, one size')}</td><td>{', '.join(WHO[a] for a, kk in copy['caption_by_asset'].items() if kk == key)}</td></tr>" for key, c in copy['captions'].items())
caps = ''.join(f'''<div class="opt"><h4>Round 1, option {i + 1}: {e(o['line1'])} {e(o['line2'])} / {e(o['bar'])}</h4>{img(f'shots/captions/round1/caption-{i + 1}-adi.png')}</div>''' for i, o in enumerate(copy['caption_round1']))
cur = copy['cover']

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tantra LinkedIn rebrand v2: team pack</title>
<style>
body{{font-family:Inter,system-ui,-apple-system,sans-serif;background:#0b0c12;color:#e8e9f0;margin:0;line-height:1.55}}
main{{max-width:1180px;margin:0 auto;padding:28px 20px 80px}}a{{color:#b9a8ff}}h1{{font-size:30px;margin:0 0 6px}}
h2{{font-size:22px;margin:52px 0 12px;padding-top:12px;border-top:1px solid #23253a}}h3{{font-size:18px;margin:34px 0 8px}}h4{{font-size:15px;margin:18px 0 6px;color:#cfd2e3}}
img{{display:block;width:100%;height:auto;border-radius:6px;margin:6px 0}}.dl{{font-size:14px;margin:4px 0 0}}
.opt.pick{{outline:2px solid #8b6cff;outline-offset:8px;border-radius:6px}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0}}td,th{{border:1px solid #2a2c42;padding:7px 9px;text-align:left;vertical-align:top}}
pre{{white-space:pre-wrap;background:#14151f;padding:12px;border-radius:6px;font-size:13.5px}}code{{font-size:13px}}
details{{margin:10px 0;background:#11121b;border:1px solid #23253a;border-radius:8px;padding:8px 14px}}summary{{cursor:pointer;font-weight:600}}
nav a{{margin-right:14px;font-size:14px}}.pc{{display:grid;grid-template-columns:150px 1fr;gap:16px;align-items:center}}.pc>a img{{border-radius:50%}}.logos3{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}@media(max-width:700px){{.two{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Tantra LinkedIn rebrand v2: team pack</h1>
<p>Updated {datetime.datetime.now().strftime('%d %b %Y, %H:%M')}. Everything for the six profiles and the Tantra page: images, every field, and every version we made.</p>
<nav><a href="#guide">Team guide and prompt</a><a href="#status">Live status</a><a href="#decisions">Decisions</a><a href="#profiles">Profiles</a><a href="#featured">Featured</a><a href="#company">Company page</a><a href="#captions">Captions</a><a href="#audit">Audit</a><a href="#how">How to apply</a></nav>

<h2 id="guide">Team guide and the Claude Code prompt</h2>
<p>Raw files for Claude: <a href="TEAM_GUIDE.md">TEAM_GUIDE.md</a> &#183; <a href="PROFILE_SPEC.md">PROFILE_SPEC.md</a> &#183; <a href="li-upload.sh">li-upload.sh</a></p>
<details open><summary>Step by step, the prompt, and the known blockers</summary>{md((HERE / 'TEAM_GUIDE.md').read_text().split('\n', 2)[2])}</details>

<h2 id="status">Live status after the edits</h2>
{md((HERE / 'AUDIT.md').read_text().split('## After the Edits', 1)[1].split('\n', 1)[1])}

<h2 id="decisions">Decisions (Adi, 13 Nov 2026)</h2>
<table><tr><th>What</th><th>Decision</th></tr>
<tr><td>Profile covers and Featured images</td><td>Approved</td></tr>
<tr><td>Company page cover</td><td>A2, face strips graded violet</td></tr>
<tr><td>Captions</td><td>Four captions tested at once, one per asset group (see Captions)</td></tr>
<tr><td>Titles</td><td>{'<br>'.join(f'{e(n)}: {e(t)} @ Tantra' for _, n, t in PEOPLE)}</td></tr>
<tr><td>Tantra page founded</td><td>2018</td></tr>
<tr><td>Organic traffic domain</td><td>jointantra.com (same site as webinar.sellwithtantra.com, one deploy updates both; bonuses also on bonuses.jointantra.com). Every LinkedIn link has its own utm_content: see each person's Links table</td></tr>
<tr><td>Image text</td><td>Headline, bar and logos only. No labels</td></tr></table>

<h2 id="profiles">Profiles: your cover and your fields</h2>
<p>Find your name. Upload the cover, then copy each field from your section. Shared steps for everyone are in "How to apply".</p>
{people}

<h2 id="featured">Featured images (same for all six)</h2>
<div class="two"><div>{img('assets/featured-workshop-1200x627.png')}{dl(('assets/featured-workshop-1200x627@2x.png', 'Workshop, 2400 x 1254'), ('assets/featured-workshop-1200x627.png', '1200 x 627'))}</div>
<div>{img('assets/featured-consultation-1200x627.png')}{dl(('assets/featured-consultation-1200x627@2x.png', 'Consultation, 2400 x 1254'), ('assets/featured-consultation-1200x627.png', '1200 x 627'))}</div></div>
{md(find('Shared by All Six'))}

<h2 id="company">Tantra company page</h2>
<h4>Page logo: D is live (from the newest mark, usetantra.com tantra-mark-hub.webp). E, F and the first round A, B, C are alternates</h4><div class="logos3">{''.join(f"<div><h4>Logo {v.upper()}{' (live)' if v == 'd' else ''}</h4>{img(f'assets/tantra-logo-{v}-1200.png')}{dl((f'assets/tantra-logo-{v}-1200.png', '1200 x 1200'))}</div>" for v in 'defabc')}</div>
<h4>Logos and photos at feed size</h4>{img('shots/logo-and-photos-preview.png')}
{covers}
<h4>On LinkedIn</h4>{img('shots/mock-company.png')}
<details><summary>Every page field: tagline, About, specialties, button</summary>{md(find('Tantra Company Page'))}</details>

<h2 id="captions">Caption options</h2>
<p>Four captions run at the same time, so each one gets real profile traffic. Every profile's Featured links carry its own <code>utm_content</code>, so registrations trace back to the caption.</p>
<table><tr><th>Headline</th><th>Bar</th><th>On</th></tr>{test}</table>
<details><summary>Round 1 options (not used)</summary>{caps}</details>

<h2 id="audit">Audit: where each profile stands today</h2>
<details open><summary>Read 13 Nov 2026</summary>{md((HERE / 'AUDIT.md').read_text().split('\n', 2)[2])}</details>

<h2 id="how">How to apply</h2>
<details><summary>Runbook (Adi's profile and the page are edited by Claude; the other five apply their own)</summary>{md((HERE / 'RUNBOOK.md').read_text().split('\n', 2)[2])}</details>
<details><summary>What changed from v1</summary>{md(find('What Changed'))}</details>
<p>Version 1 (5 Nov): <a href="../">linkedin-profiles</a></p>
</main></body></html>'''
(OUT / 'index.html').write_text(page)
bad = [c for c in page if c in (chr(0x2013), chr(0x2014))]
print(f'report written to {OUT}; dashes: {len(bad)}; version {V}')
