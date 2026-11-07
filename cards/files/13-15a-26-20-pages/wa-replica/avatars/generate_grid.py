import json, os, ssl, time, urllib.request
key = [l.split('=',1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.config/tantra/keys/kie.env')) if l.startswith('KIE_API_KEY')][0]
CTX = ssl.create_default_context(cafile='/Users/adithyamurali/Library/Python/3.12/lib/python/site-packages/certifi/cacert.pem')
H = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
def req(path, body=None):
    r = urllib.request.Request('https://api.kie.ai' + path, data=json.dumps(body).encode() if body else None, headers=H, method='POST' if body else 'GET')
    return json.load(urllib.request.urlopen(r, timeout=120, context=CTX))
prompt = ("A 3 by 4 grid of twelve separate square smartphone profile pictures of twelve different fictional adults, "
 "each like a casual WhatsApp profile photo: selfies, holiday snaps, office headshots, outdoor portraits, varied lighting. "
 "Mix of ages 28 to 55, men and women, South Asian, Black, White, East Asian, Latino and Middle Eastern founders. "
 "Each face centred and filling most of its square, natural candid phone camera look, realistic skin, no filters. "
 "Thin pure black gutters between squares. No text, no logos, no watermarks.")
t = req('/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {'prompt': prompt, 'aspect_ratio': '3:4', 'resolution': '2K', 'output_format': 'png'}})
tid = t['data']['taskId']; print('task', tid, flush=True)
for _ in range(80):
    time.sleep(6)
    d = req(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
    if d['state'] == 'success':
        url = json.loads(d['resultJson'])['resultUrls'][0]
        open('/tmp/wa/gen/grid.png', 'wb').write(urllib.request.urlopen(url, timeout=120, context=CTX).read()); print('ok', d.get('creditsConsumed')); break
    if d['state'] == 'fail': print('fail', d.get('failMsg')); break
