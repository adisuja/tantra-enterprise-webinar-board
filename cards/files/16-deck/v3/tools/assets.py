"""Copy and optimise the repo imagery the V3 deck uses, and build the platform logo sprite.
Sources: tantra-enterprise-webinar-workspace @ 679637c (pages, bonus art, WhatsApp cards, funnel covers, library),
tantra-content (Adi photos), simple-icons (platform marks)."""
import json, os, glob
from PIL import Image, ImageOps

V3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = V3 + '/deck/assets'
WS = '/home/user/tantra-enterprise-webinar-workspace/deliverables'
PG = WS + '/13-15a-26-20-pages/src/assets/img'
ADI = '/home/user/tantra-content/content/brand/people/adi'
SI = V3 + '/vendor/si/package'
SI10 = V3 + '/vendor/si10/package'

def save(im, path, q=82, maxw=None, maxh=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if maxw and im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    if maxh and im.height > maxh: im = im.resize((round(im.width * maxh / im.height), maxh), Image.LANCZOS)
    im.save(path, 'WEBP', quality=q, method=6)
    return im.size

# people: approved published photos (Motoz founder excluded: PROOF_PACK 3 bans Motoz)
for f in glob.glob(PG + '/people/*.jpg'):
    n = os.path.basename(f)[:-4]
    if n == 'patrick-lundbom': continue
    save(Image.open(f).convert('RGB'), f'{A}/p/{n}.webp', 84)

# client logos as white silhouettes for dark slides (never Google, Amazon, Techstars or Motoz: PROOF_PACK 1 and 3)
BAN = {'google', 'amazon', 'techstars', 'motoz'}
for f in glob.glob(PG + '/logos/*.png'):
    n = os.path.basename(f)[:-4]
    if n in BAN: continue
    im = Image.open(f).convert('RGBA')
    bbox = im.getchannel('A').getbbox()
    if bbox: im = im.crop(bbox)
    a = im.getchannel('A')
    # logos drawn on an opaque light box (aykido): key out the light background
    if a.getextrema()[0] > 200:
        g = ImageOps.grayscale(im)
        a = ImageOps.invert(g).point(lambda v: 255 if v > 60 else 0)
    w = Image.new('RGBA', im.size, (255, 255, 255, 0)); w.putalpha(a)
    save(w, f'{A}/l/{n}.webp', 90, maxh=160)
    save(im, f'{A}/lc/{n}.webp', 90, maxh=160)

# bonus covers, OS art, books
for n in ('playbook-a', 'prompts-a', 'calculator-a', 'playbook-b', 'prompts-b', 'calculator-b'):
    save(Image.open(f'{PG}/bonus/full/{n}.webp').convert('RGB'), f'{A}/b/{n}.webp', 84, maxh=900)
for n in ('os-box', 'os-core'):
    save(Image.open(f'{PG}/os/{n}.webp').convert('RGB'), f'{A}/{n}.webp', 84, maxw=1600)

# our own funnel: WhatsApp cards and page covers (our pages, not client pages)
for f in glob.glob(WS + '/42-whatsapp-images/out/*.jpg'):
    save(Image.open(f).convert('RGB'), f'{A}/wa/{os.path.basename(f)[:-4]}.webp', 82, maxw=1200)
for f in glob.glob(WS + '/39-funnel-map/src/covers/*.jpg'):
    save(Image.open(f).convert('RGB'), f'{A}/pg/{os.path.basename(f)[:-4]}.webp', 82, maxw=900)

# library examples (already published, faces and names blurred in the bonus library) for the training-data mosaic
LIB = WS + '/33-bonus-books/site/library/media'
PICK = ['f6dddbc2c44d04ca', '7e3175de54481425', '81082dbc6035d304', 'c0e4727a6e8bd776', 'cc38d362a5846cc8', 'b4750f8464341426',
        '6bc7ea71f4975aab', 'ba43dd652bf95cf0', '4daec57fa8fd52fe', 'd16b50c47e8c18c5', '5014679a721f94f0', '214630d388de64e5',
        '414c654a071f2123', '914c59623df8f4ff', '154b7a0992058018', '4351182568597dd3', '5cb2311d07554c91', '716cae49cd184da3',
        '6a05ed092c1847a1', '312cc2b8796f240a', '3a152b0b32ecb652', 'cd4bf4bc38f7476e']
for h in PICK:
    im = Image.open(f'{LIB}/{h}.webp').convert('RGB')
    save(ImageOps.fit(im, (480, 300), Image.LANCZOS, centering=(.5, .3)), f'{A}/lib/{h}.webp', 76)

# Adi: real photo for the host slide, identity-locked avatars elsewhere
save(ImageOps.fit(Image.open(ADI + '/photos/blazer-rail.jpg').convert('RGB'), (800, 1000), Image.LANCZOS, centering=(.5, .3)), f'{A}/adi-blazer.webp', 84)
save(ImageOps.fit(Image.open(ADI + '/photos/studio-white-shirt.jpg').convert('RGB'), (800, 1000), Image.LANCZOS, centering=(.5, .3)), f'{A}/adi-studio.webp', 84)
save(ImageOps.fit(Image.open(ADI + '/avatars/floor-overwhelmed.jpg').convert('RGB'), (900, 1125), Image.LANCZOS, centering=(.5, .5)), f'{A}/adi-floor.webp', 82)
save(ImageOps.fit(Image.open(ADI + '/avatars/speaking.jpg').convert('RGB'), (900, 1125), Image.LANCZOS, centering=(.5, .35)), f'{A}/adi-speaking.webp', 82)
save(ImageOps.fit(Image.open(ADI + '/avatars/headshot.jpg').convert('RGB'), (600, 600), Image.LANCZOS), f'{A}/adi-head.webp', 84)
for n in ('tantra-mark-white.png', 'tantra-word-white.png'):
    im = Image.open(f'{PG}/{n}').convert('RGBA'); bb = im.getchannel('A').getbbox(); im = im.crop(bb) if bb else im
    save(im, f'{A}/{n[:-4]}.webp', 90, maxw=900)

# platform logo sprite: simple-icons paths (LinkedIn and Outlook from the v10 set, removed later upstream)
data = {i['slug'] if 'slug' in i else i['title'].lower().replace(' ', '').replace('.', 'dot'): i for i in json.load(open(SI + '/data/simple-icons.json'))} if os.path.exists(SI + '/data/simple-icons.json') else {}
LOGOS = {  # slug: (display name, colour on dark; None = brand hex)
    'whatsapp': ('WhatsApp', None), 'googlecalendar': ('Google Calendar', None), 'gmail': ('Gmail', None), 'linkedin': ('LinkedIn', '#0A66C2'),
    'cloudflare': ('Cloudflare', None), 'zoom': ('Zoom', None), 'wistia': ('Wistia', None), 'caldotcom': ('Cal.com', '#ffffff'),
    'stripe': ('Stripe', None), 'twilio': ('Twilio', None), 'elevenlabs': ('ElevenLabs', '#ffffff'), 'hubspot': ('HubSpot', None),
    'googleanalytics': ('Google Analytics', None), 'meta': ('Meta', None), 'claude': ('Claude', None), 'anthropic': ('Anthropic', '#ffffff'),
    'openai': ('OpenAI', '#ffffff'), 'googlegemini': ('Gemini', None), 'resend': ('Resend', '#ffffff'), 'microsoftoutlook': ('Outlook', '#0078D4'),
    'googlesheets': ('Google Sheets', None), 'youtube': ('YouTube', None), 'googlemeet': ('Google Meet', None), 'google': ('Google', '#ffffff'),
}
def icon(slug):
    for root in (SI, SI10):
        p = f'{root}/icons/{slug}.svg'
        if os.path.exists(p): return open(p).read(), root
    return None, None
def hexof(slug, root):
    for f in (root + '/_data/simple-icons.json', root + '/data/simple-icons.json'):
        if os.path.exists(f):
            j = json.load(open(f)); j = j['icons'] if isinstance(j, dict) else j
            for i in j:
                s = i.get('slug') or i['title'].lower().replace(' ', '').replace('.', 'dot').replace('+', 'plus')
                if s == slug: return '#' + i['hex']
    return '#ffffff'
syms, meta = [], {}
for slug, (name, col) in LOGOS.items():
    svg, root = icon(slug)
    if not svg: print('missing', slug); continue
    import re
    path = re.search(r'<path d="([^"]+)"', svg).group(1)
    c = col or hexof(slug, root)
    if c.lower() in ('#000000', '#191919', '#292929', '#111111', '#0b0d12', '#181717'): c = '#ffffff'
    syms.append(f'<symbol id="lg-{slug}" viewBox="0 0 24 24"><path fill="{c}" d="{path}"/></symbol>')
    meta[slug] = {'name': name, 'color': c}
open(V3 + '/src/logos.svg', 'w').write('<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">' + ''.join(syms) + '</svg>')
json.dump(meta, open(V3 + '/src/logos.json', 'w'), indent=1)
print('logos', len(syms), {k: v['color'] for k, v in meta.items()})
tot = sum(os.path.getsize(f) for f in glob.glob(A + '/**/*.*', recursive=True))
print('assets', len(glob.glob(A + '/**/*.*', recursive=True)), 'files', round(tot / 1024), 'KB')
