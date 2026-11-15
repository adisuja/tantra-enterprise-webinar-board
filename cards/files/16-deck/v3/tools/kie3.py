"""V3 deck art on Kie.ai (nano-banana-pro, 2K, 16:9), in Tantra's house style (dark violet glass renders).
usage: python3 kie3.py credit | python3 kie3.py run name [name ...] | python3 kie3.py run all
Budget guard: stops submitting when the balance would fall below FLOOR. The key is injected by the proxy."""
import json, os, sys, time, urllib.request, io
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, RAW, LOG = ROOT + '/deck/img', ROOT + '/kie-raw', ROOT + '/kie-log.json'
API, MODEL = 'https://api.kie.ai', 'nano-banana-pro'
START, CAP = 4695.49, 1000.0          # balance when V3 began; $5 = 1,000 credits
FLOOR = START - CAP
STYLE = (' Style: premium 3D render matching a dark luxury tech brand. Deep ink-black background (#0b0d12) fading into dark violet; '
         'objects made of translucent smoked glass and frosted crystal with iridescent violet (#6d4aff) and soft lavender (#a78bfa) '
         'edge light, gentle volumetric glow, a few floating light particles, studio lighting, ultra clean, high detail, calm and '
         'minimal. Keep the left third of the frame mostly empty dark space. No text, no letters, no numbers, no logos, '
         'no watermarks, no people unless described.')
P = {
 'cover': 'A colossal translucent glass funnel built from stacked floating rings, set in the right two thirds of the frame. Thousands of tiny glowing particles pour in at the wide top and leave the narrow bottom as a handful of bright violet orbs. Thin orbit rings of light circle the funnel.',
 'inflection': 'A single ribbon of glowing violet glass runs flat across a dark reflective floor, then bends sharply upward into a steep rising curve on the right, with a bright light trail along the bend.',
 'bottleneck': 'A tall elegant glass hourglass. The upper bulb is packed with thousands of glowing violet particles that are all jammed at the very narrow neck; only a thin trickle reaches the nearly empty lower bulb.',
 'noise': 'A small calm glowing glass cube at the centre right, surrounded by a chaotic storm of hundreds of floating glass notification bubbles, chat bubbles and pop-up cards with motion blur.',
 'volume': 'A large elegant glass funnel standing in darkness, almost completely empty: only three tiny glowing drops fall through it.',
 'feast': 'A glass rollercoaster track floating in dark space with extreme high peaks and deep plunging valleys; light glows on the peaks, the valleys fall into darkness.',
 'zombie': 'An old-fashioned desk telephone made of dark smoked glass on a dusty surface, thin cobwebs on the receiver, one dim flicker of violet light inside it, abandoned mood.',
 'darts': 'A dark glass dartboard on a dark wall, with dozens of glowing glass darts stuck all over the wall around it and almost none on the board.',
 'nodial': 'A sleek dark control panel with an empty round socket where a dial should be; several glowing cables hang loose and disconnected below it.',
 'market': 'Aerial view of a vast dark ocean whose surface is made of tens of thousands of tiny glowing violet points of light, stretching to the horizon in gentle waves.',
 'teacup': 'A delicate translucent glass teacup resting on a black rock at the edge of a vast dark ocean at night. The ocean surface is scattered with countless tiny violet lights all the way to the horizon; the teacup holds only a few.',
 'junk': 'A messy heap of shredded paper strips and crumpled sheets, dull grey and lifeless, lit by cold light, a few faint violet sparks inside.',
 'smalllist': 'A tiny open notebook with only three short lines of light, alone in the middle of a vast dark glass table.',
 'byhand': 'A small desk with a single lamp, buried under towering stacks of paper files that rise into the darkness, warm lamp light against cold violet shadows. No person.',
 'overnight': 'A glowing glass server core at night: rows of hair-thin light filaments process thousands of tiny glass cards in parallel, calm and precise.',
 'drown': 'One glowing violet glass envelope floating just above an endless sea of identical grey paper envelopes that stretches into darkness.',
 'spam': 'A cracked dark glass inbox tray overflowing, hundreds of identical grey envelopes spilling out onto the floor.',
 'calendar': 'A floating translucent glass calendar grid tile; a glowing violet event card slides neatly into one open slot.',
 'blueocean': 'Split horizon: on the right a calm luminous ocean of soft blue and violet light with a single glass calendar tile floating on the surface; far in the background on the left a stormy grey sea of paper envelopes.',
 'engine': 'A precise glass machine with many parallel glowing rails; thousands of tiny glowing cards glide along the rails and drop into rows of calendar-like slots.',
 'stage': 'An empty dark auditorium seen from the stage: rows of seats rise into darkness, each seat faintly glowing violet, a single soft spotlight on the stage floor.',
 'pillar': 'A thin glass pillar with a visible crack glowing hot violet, supporting a precarious stack of five heavy translucent glass blocks.',
 'firstdate': 'A candlelit restaurant table for two at night, an open ring box with a sparkling diamond ring placed in front of an empty chair across the table, moody violet ambient light, shallow depth of field, photographic.',
 'onetomany': 'One bright violet orb on the left sends thin beams of light that fan out to hundreds of small glowing glass seats arranged in curved rows on the right.',
 'blueprint': 'A glowing technical blueprint of a stage and a sequence of five connected rooms drawn in thin violet light lines on a dark glass plane, precise and engineered.',
 'brain': 'A luminous glass brain made of thousands of tiny floating translucent cards and slides, joined by fine violet neural light threads.',
 'taste': 'A human hand holding a fine brush adds the final stroke of light to an almost finished glass sculpture. Only the hand and wrist are visible.',
 'tuning': 'Close-up of a sleek dark mixing console: one glowing violet fader is being raised among many unlit faders, shallow depth of field.',
 'evergreen': 'A small glowing violet sapling grows out of a round glass recording light, with fine roots of light spreading below it.',
 'machine': 'A long horizontal glass machine with five chambers; a wide stream of particles enters the first chamber, narrows at each chamber, and leaves the last one as four bright violet orbs.',
 'ceiling': 'A glass ceiling shattering upward as a beam of violet light breaks through it, shards suspended in the air.',
 'core': 'A central translucent glass cube glowing violet, with dozens of small blank glass tiles orbiting it on rings of light, each tile joined to the cube by a thin light thread.',
 'journey': 'A winding path of glowing glass tiles climbs a dark mountain in three switchbacks toward a bright summit.',
 'diy': 'A cluttered workbench under a single lamp with a half built glass machine, tangled glowing wires, scattered tools and six unfinished modules.',
 'team': 'Six empty office chairs around a dark glass conference table, a small glowing light in front of each chair, empty and quiet.',
 'guess': 'A large glowing question mark made of frosted glass, with blurry fragments of generic floating text cards drifting around it.',
 'flag': 'Seen from a dark empty shore at dusk: a distant island where a glowing violet flag has already been planted.',
 'surprise': 'A sealed translucent glass gift box tied with a ribbon of light, soft violet light leaking from its seams, a few sparks floating above it, centred in the right half of the frame.',
 'booked': 'A glass desk calendar on a dark desk with one glowing violet booked slot, warm hopeful dawn light from the right.',
}

def req(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method='POST' if body is not None else 'GET',
                               headers={'Authorization': 'Bearer proxy-injected', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read() or b'{}')

def credit():
    return float(req('/api/v1/chat/credit').get('data'))

def log(row):
    rows = json.load(open(LOG)) if os.path.exists(LOG) else []
    rows.append(row); json.dump(rows, open(LOG, 'w'), indent=1)

def save(name, url):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'deck-builder'}), timeout=180).read()
    open(f'{RAW}/{name}.png', 'wb').write(raw)
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    if im.width > 1920: im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
    im.save(f'{OUT}/{name}.webp', 'WEBP', quality=82, method=6)
    return os.path.getsize(f'{OUT}/{name}.webp')

def run(names, per_image=None):
    os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
    bal = credit(); print('balance', bal, 'floor', FLOOR, flush=True)
    tasks = {}
    for n in names:
        if os.path.exists(f'{OUT}/{n}.webp'): print('skip (exists)', n); continue
        est = per_image or 24
        if bal - est * (len(tasks) + 1) < FLOOR: print('STOP: budget floor reached before', n); break
        res = req('/api/v1/jobs/createTask', {'model': MODEL, 'input': {'prompt': (P[n] + STYLE)[:5000], 'aspect_ratio': '16:9',
                                                                       'resolution': '2K', 'output_format': 'png'}})
        tid = (res.get('data') or {}).get('taskId')
        print(n, '->', tid or res, flush=True)
        if tid: tasks[n] = tid
        time.sleep(0.9)
    t0 = time.time()
    while tasks and time.time() - t0 < 1500:
        time.sleep(10)
        for n, tid in list(tasks.items()):
            try:
                d = (req(f'/api/v1/jobs/recordInfo?taskId={tid}').get('data') or {})
            except Exception as e:
                print('poll error', n, e, flush=True); continue
            st = (d.get('state') or '').lower()
            if st == 'success':
                rj = d.get('resultJson'); rj = json.loads(rj) if isinstance(rj, str) else (rj or {})
                url = (rj.get('resultUrls') or [None])[0]
                try:
                    size = save(n, url); print('OK', n, size, flush=True); log({'name': n, 'task': tid, 'ok': True, 'bytes': size})
                except Exception as e:
                    print('DOWNLOAD FAIL', n, url, e, flush=True); log({'name': n, 'task': tid, 'ok': False, 'url': url, 'err': str(e)})
                tasks.pop(n)
            elif st in ('fail', 'failed', 'error'):
                print('FAIL', n, d.get('failMsg') or d, flush=True); log({'name': n, 'task': tid, 'ok': False, 'err': d.get('failMsg')}); tasks.pop(n)
    for n in tasks: print('TIMEOUT', n, flush=True)
    b2 = credit(); print('balance after', b2, 'spent this run', round(bal - b2, 2), 'spent total', round(START - b2, 2), flush=True)

if __name__ == '__main__':
    if sys.argv[1] == 'credit': print(credit())
    else:
        names = list(P) if sys.argv[2:] == ['all'] else sys.argv[2:]
        run(names, float(os.environ['PER']) if os.environ.get('PER') else None)
