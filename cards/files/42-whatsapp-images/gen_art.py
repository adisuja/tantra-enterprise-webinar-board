"""Kie.ai background art for the WhatsApp preview images (Adi 2026-11-09, budget $2 for all images).
Four wordless scenes, nano-banana-pro (18 credits each, about $0.09). The Tantra logo and all text are added in HTML, never by the model.
usage: python3 -I gen_art.py [name ...]  -> art/<name>.png
"""
import json, os, pathlib, ssl, sys, time, urllib.request, concurrent.futures as cf

HERE = pathlib.Path(__file__).parent
key = [l.split('=', 1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.config/tantra/keys/kie.env')) if l.startswith('KIE_API_KEY')][0]
CTX = ssl.create_default_context(cafile='/Users/adithyamurali/Library/Python/3.12/lib/python/site-packages/certifi/cacert.pem')
H = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

def post(url, body):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method='POST'), timeout=180, context=CTX))

def get(path):
    return json.load(urllib.request.urlopen(urllib.request.Request('https://api.kie.ai' + path, headers=H), timeout=120, context=CTX))

BASE = ("Absolutely no text, letters, numbers, logos or watermark anywhere. Premium 3D render, cinematic lighting, frosted glass and soft chrome, "
        "Apple keynote quality, ultra clean. Palette: near-black ink background (#0b0d12) fading to deep night violet (#1a1033), "
        "electric violet glow (#6d4aff), lavender highlights (#a78bfa), one small warm amber accent light (#fbbf24). "
        "Composition: the subject sits in the RIGHT 40 percent of a wide frame; the left 60 percent is calm, dark, almost empty space for a headline. ")
JOBS = {
    'time': BASE + "Subject: a floating frosted-glass calendar tile and a sleek glass clock ring orbiting it, thin glowing violet light trails circling like a countdown, tiny particles.",
    'live': BASE + "Subject: a floating glass presentation screen glowing violet from within, concentric broadcast signal rings radiating from it, a small amber recording light, soft volumetric haze.",
    'gift': BASE + "Subject: an open premium matte black box with violet edge lighting, glowing glass cards and a translucent glass key rising out of it, light spilling upward.",
    'chat': BASE + "Subject: three stacked frosted-glass chat bubbles floating at different depths, one glowing violet, linked by a thin light line to a small glass calendar tile with a glowing check.",
}

def run(name):
    t = post('https://api.kie.ai/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {'prompt': JOBS[name], 'aspect_ratio': '16:9', 'resolution': '1K', 'output_format': 'png'}})
    tid = t['data']['taskId']
    for _ in range(150):
        time.sleep(4)
        d = get(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
        if d.get('state') == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            (HERE / 'art' / f'{name}.png').write_bytes(urllib.request.urlopen(url, timeout=120, context=CTX).read())
            return name, 'ok'
        if d.get('state') == 'fail':
            return name, d.get('failMsg')
    return name, 'timeout'

if __name__ == '__main__':
    names = sys.argv[1:] or list(JOBS)
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(run, names): print(*r)
