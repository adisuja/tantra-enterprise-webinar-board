"""Kie.ai artwork for the bonus covers (no text). usage: python3 -I gen_art.py [playbook-a prompts-a ...]; then convert art/*.png to webp."""
import json, os, pathlib, ssl, time, urllib.request, sys, concurrent.futures as cf
ART = pathlib.Path(__file__).parent / 'art'
key = [l.split('=',1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.config/tantra/keys/kie.env')) if l.startswith('KIE_API_KEY')][0]
CTX = ssl.create_default_context(cafile='/Users/adithyamurali/Library/Python/3.12/lib/python/site-packages/certifi/cacert.pem')
H = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
def req(path, body=None):
    r = urllib.request.Request('https://api.kie.ai' + path, data=json.dumps(body).encode() if body else None, headers=H, method='POST' if body else 'GET')
    return json.load(urllib.request.urlopen(r, timeout=120, context=CTX))
BASE = ("Premium book cover background artwork, abstract 3D render, cinematic studio lighting, ultra clean, high detail, "
        "lots of calm empty dark space in the top half for a title, the subject sits in the lower half. "
        "One seamless smooth gradient background with no horizon line, no seams and no hard edges. Absolutely no text, no letters, no numbers, no logos, no watermark.")
JOBS = {
 'playbook-a': "Subject: an elegant floating isometric blueprint of a revenue funnel: stacked translucent glass layers connected by thin glowing lines and nodes, like an architectural plan of a sales system. Palette: near-black ink background (#0b0d12), deep violet and electric purple light (#6d4aff, #a78bfa), soft lilac highlights.",
 'prompts-a': "Subject: a glowing AI core made of a faceted glass crystal, surrounded by floating translucent glass cards orbiting it, fine light trails between them, sense of intelligence and automation. Palette: rich electric violet background (#4b2fd6 to #6d4aff), lilac and white highlights, a touch of deep indigo.",
 'playbook-b': "Subject: an elegant floating isometric blueprint of a revenue funnel: stacked translucent glass layers connected by thin glowing lines and nodes, like an architectural plan of a sales system. Palette: midnight black-blue background (#02070a), electric blue light (#0297de, #33ade8), cool cyan highlights.",
 'calculator-a': "Subject: a sleek floating glass revenue dashboard: translucent frosted glass slabs with rising bar chart columns and a glowing circular dial gauge, small glass number keys, crisp reflections. Palette: a LIGHT airy background, soft pale lilac to white (#f3f0ff to #ffffff), objects in frosted glass with electric violet (#6d4aff) and lilac (#a78bfa) light inside them, soft violet shadows.",
 'calculator-b': "Subject: a sleek floating glass revenue dashboard: translucent frosted glass slabs with rising bar chart columns and a glowing circular dial gauge, small glass number keys, crisp reflections. Palette: a LIGHT airy background, soft pale ice blue to white (#eaf0f3 to #ffffff), objects in frosted glass lit with electric blue (#0297de) and a warm coral orange (#fc734d) accent, soft blue shadows.",
 'prompts-b': "Subject: a glowing AI core made of a faceted glass crystal, surrounded by floating translucent glass cards orbiting it, fine light trails between them, sense of intelligence and automation. Palette: deep midnight background (#03111a) with warm coral-orange light (#fc734d) as the key light and electric blue (#0297de) rim light.",
}
def run(name):
    t = req('/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {'prompt': BASE + ' ' + JOBS[name], 'aspect_ratio': '2:3', 'resolution': '2K', 'output_format': 'png'}})
    tid = t['data']['taskId']
    for _ in range(120):
        time.sleep(6)
        d = req(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
        if d['state'] == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            open(ART / f'{name}.png', 'wb').write(urllib.request.urlopen(url, timeout=180, context=CTX).read())
            return f'{name} ok {d.get("creditsConsumed")}'
        if d['state'] == 'fail': return f'{name} fail {d.get("failMsg")}'
    return f'{name} timeout'
names = sys.argv[1:] or list(JOBS)
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(run, names): print(r, flush=True)
