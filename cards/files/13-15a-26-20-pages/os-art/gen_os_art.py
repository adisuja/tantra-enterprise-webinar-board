"""Kie.ai product artwork for the Tantra RevOps OS on /funnelos/ (Adi 2026-11-09).

The real logos go in as reference images (ref/*.png: the Tantra mark from the site, Claude, Gemini, ChatGPT and Grok from
iconify's official-logo sets), so the model draws the actual marks instead of inventing them. No text in the art.
usage: python3 -I gen_os_art.py [name ...]   -> art/<name>.png ; then python3 -I build.py
"""
import base64, json, os, pathlib, ssl, sys, time, urllib.request, concurrent.futures as cf

HERE = pathlib.Path(__file__).parent
ART = HERE / 'art'
key = [l.split('=', 1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.config/tantra/keys/kie.env')) if l.startswith('KIE_API_KEY')][0]
CTX = ssl.create_default_context(cafile='/Users/adithyamurali/Library/Python/3.12/lib/python/site-packages/certifi/cacert.pem')
H = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}


def post(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method='POST')
    return json.load(urllib.request.urlopen(r, timeout=180, context=CTX))


def get(path):
    r = urllib.request.Request('https://api.kie.ai' + path, headers=H)
    return json.load(urllib.request.urlopen(r, timeout=120, context=CTX))


def upload(name):
    b64 = base64.b64encode((HERE / 'ref' / f'{name}.png').read_bytes()).decode()
    d = post('https://kieai.redpandaai.co/api/file-base64-upload',
             {'base64Data': f'data:image/png;base64,{b64}', 'uploadPath': 'tantra-os-ref', 'fileName': f'{name}.png'})
    return d['data']['downloadUrl']


REFS = ['tantra', 'claude', 'gemini', 'chatgpt', 'grok']
BASE = ("Use the five reference images as the exact logos: image 1 is the Tantra logo (a circuit tree growing out of a glowing head), "
        "image 2 the Claude logo (coral orange starburst), image 3 the Gemini logo (four-point gradient sparkle), image 4 the ChatGPT logo "
        "(black hexagonal knot, render it in white), image 5 the Grok logo (circle cut by a diagonal slash, render it in white). Reproduce each mark faithfully, "
        "never invent or distort a logo. Absolutely no text, no letters, no words, no numbers, no watermark anywhere. "
        "Premium 3D product render, cinematic studio lighting, ultra clean, crisp glass and brushed aluminium materials, shallow depth of field, "
        "Apple keynote quality. Palette: near-black ink background (#0b0d12) with a deep violet glow (#6d4aff, #a78bfa) behind the subject, soft lilac rim light. ")
JOBS = {
    'os-core': BASE + (
        "Subject: an operating system shown as a physical premium software bundle: a thick, rounded, translucent glass slab standing at a slight angle "
        "in the centre, the Tantra logo glowing inside it like a core. Around it, small floating frosted-glass cards orbit in an arc, each a tiny wordless "
        "wireframe of a funnel element (a landing page, an email, a calendar, a chat bubble, a pipeline bar chart, a video player), linked to the core by thin "
        "glowing violet light lines. In front, on a dark reflective floor, four rounded glass app tiles sit in a row like plugged-in modules, each showing one "
        "AI assistant logo: Claude, Gemini, ChatGPT, Grok, with light flowing from each tile into the core. Wide composition, subject centred, generous dark margins."),
    'os-box': BASE + (
        "Subject: a luxurious software product box, like a boxed operating system edition: a matte black box with violet edge lighting, standing three-quarter "
        "view, the Tantra logo embossed and glowing on its front face. The lid is lifted and hovering above, and from the open box rise translucent glass layers "
        "of a revenue funnel (stacked glass panels showing wordless wireframes of pages, emails, calendars and charts) connected by glowing light lines. Around "
        "the box, four small glowing glass orbs float, each holding one AI assistant logo: Claude, Gemini, ChatGPT, Grok, with thin light lines linking them to the box. "
        "Wide composition, subject centred, generous dark margins."),
}


def run(name, urls):
    t = post('https://api.kie.ai/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {
        'prompt': JOBS[name.split('.')[0]], 'image_input': urls, 'aspect_ratio': '16:9', 'resolution': '2K', 'output_format': 'png'}})
    tid = t['data']['taskId']
    for _ in range(150):
        time.sleep(6)
        d = get(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
        if d['state'] == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            (ART / f'{name}.png').write_bytes(urllib.request.urlopen(url, timeout=180, context=CTX).read())
            return f'{name} ok'
        if d['state'] == 'fail':
            return f'{name} fail {d.get("failMsg")}'
    return f'{name} timeout'


if __name__ == '__main__':
    ART.mkdir(exist_ok=True)
    urls = [upload(r) for r in REFS]
    names = sys.argv[1:] or [f'{j}.{i}' for j in JOBS for i in (1, 2)]
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(lambda n: run(n, urls), names):
            print(r, flush=True)
