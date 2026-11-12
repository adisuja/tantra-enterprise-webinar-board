"""Kie.ai artwork for the three Tantra plans on /tantra-plans/ (Adi 2026-11-12: premium generated image per option).
Reference: ref/tantra.png (the real Tantra mark) so the model draws the actual logo. No text in the art.
usage: python3 -I gen_plans_art.py [name ...]  -> art/<name>.png
"""
import base64, json, os, pathlib, ssl, sys, time, urllib.request, concurrent.futures as cf

HERE = pathlib.Path(__file__).parent
ART = HERE / 'art'
key = [l.split('=', 1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.config/tantra/keys/kie.env')) if l.startswith('KIE_API_KEY')][0]
CTX = ssl.create_default_context(cafile='/Users/adithyamurali/Library/Python/3.12/lib/python/site-packages/certifi/cacert.pem')
H = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

def post(url, body):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method='POST'), timeout=180, context=CTX))

def get(path):
    return json.load(urllib.request.urlopen(urllib.request.Request('https://api.kie.ai' + path, headers=H), timeout=120, context=CTX))

def upload():
    b64 = base64.b64encode((HERE / 'ref' / 'tantra.png').read_bytes()).decode()
    return post('https://kieai.redpandaai.co/api/file-base64-upload', {'base64Data': f'data:image/png;base64,{b64}', 'uploadPath': 'tantra-plans-ref', 'fileName': 'tantra.png'})['data']['downloadUrl']

BASE = ("The reference image is the Tantra logo (a circuit tree growing out of a glowing head): reproduce it faithfully where it appears, never invent a different logo. "
        "Absolutely no text, letters, words, numbers or watermark anywhere. Premium 3D product render, cinematic studio lighting, ultra clean, "
        "Apple keynote and luxury brand campaign quality, shallow depth of field, near-black ink background (#0b0d12), generous dark margins, subject centred. ")
JOBS = {
    'pro': BASE + ("Palette: deep violet (#6d4aff) and soft lilac (#a78bfa) light. Subject: a sleek precision outreach engine: a compact rounded slab of smoked glass and "
                   "brushed graphite, the Tantra logo glowing violet inside it. From it, thin glowing violet light paths fan out to four small floating frosted-glass "
                   "tiles, each holding one wordless icon: an envelope, a chat bubble, a professional network node icon, and a calendar page. Precise, efficient, modern."),
    'club': BASE + ("Palette: violet (#6d4aff) with warm champagne gold accents. Subject: an exclusive private members' club key: a heavy matte black metal membership card "
                    "with a bevelled champagne gold edge, the Tantra logo embossed in gold on it, resting at an angle on a dark polished stone plinth. Behind it, translucent "
                    "glass steps rise like a staircase, each step glowing slightly brighter, suggesting climbing revenue. Exclusive, aspirational, private."),
    'enterprise': BASE + ("Palette: rich gold (#f5c76b) and deep violet (#6d4aff) light, the most luxurious of the set. Subject: a monumental revenue engine as architecture: "
                          "a tall faceted tower of dark glass and polished gold, built from stacked layers that narrow upward like a funnel turned into a skyscraper, "
                          "warm gold light flowing up through its core, the Tantra logo glowing gold at its crown. Tiny frosted-glass panels orbit it, linked by gold light "
                          "lines. Dramatic low angle, volumetric light, reflective dark floor. Powerful, done-for-you, enterprise grade."),
}

def run(name, url):
    t = post('https://api.kie.ai/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {'prompt': JOBS[name.split('.')[0]], 'image_input': [url], 'aspect_ratio': '4:3', 'resolution': '2K', 'output_format': 'png'}})
    tid = t['data']['taskId']
    for _ in range(150):
        time.sleep(6)
        d = get(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
        if d['state'] == 'success':
            (ART / f'{name}.png').write_bytes(urllib.request.urlopen(json.loads(d['resultJson'])['resultUrls'][0], timeout=180, context=CTX).read())
            return f'{name} ok'
        if d['state'] == 'fail':
            return f'{name} fail {d.get("failMsg")}'
    return f'{name} timeout'

if __name__ == '__main__':
    ART.mkdir(exist_ok=True)
    url = upload()
    names = sys.argv[1:] or [f'{j}.{i}' for j in JOBS for i in (1, 2)]
    with cf.ThreadPoolExecutor(6) as ex:
        for r in ex.map(lambda n: run(n, url), names):
            print(r, flush=True)
