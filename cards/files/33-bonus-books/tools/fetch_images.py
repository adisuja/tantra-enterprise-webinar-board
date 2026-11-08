"""Download every image embedded in the client docs, mapped to its tab. PRIVATE output: _work/media/raw/<brand>/.
usage: python3 tools/fetch_images.py   (uses the local Google token, like fetch_docs.py)"""
import json, pathlib, re, ssl, urllib.request, certifi, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch_docs import token, CTX
W = pathlib.Path(__file__).resolve().parent.parent / '_work'
BR = json.loads((W / 'brands.json').read_text())
IDS = [l.split()[0] for l in (W / 'doc_ids.txt').read_text().split('\n') if l.strip()]
at = token(); manifest = []
def walk_tabs(tabs):
    for t in tabs:
        yield t
        yield from walk_tabs(t.get('childTabs', []))
def find_ids(content):
    for el in content:
        for e in el.get('paragraph', {}).get('elements', []):
            if 'inlineObjectElement' in e: yield e['inlineObjectElement']['inlineObjectId']
        for oid in el.get('paragraph', {}).get('positionedObjectIds', []): yield oid
        for row in el.get('table', {}).get('tableRows', []):
            for cell in row['tableCells']: yield from find_ids(cell['content'])
for did in IDS:
    brand = BR[did[:5]]; out = W / 'media' / 'raw' / brand; out.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(f'https://docs.googleapis.com/v1/documents/{did}?includeTabsContent=true', headers={'Authorization': 'Bearer ' + at})
    d = json.load(urllib.request.urlopen(req, context=CTX))
    for tab in walk_tabs(d.get('tabs', [])):
        dt = tab.get('documentTab', {}); title = tab['tabProperties'].get('title', '')
        objs = {**dt.get('inlineObjects', {}), **dt.get('positionedObjects', {})}
        for i, oid in enumerate(dict.fromkeys(find_ids(dt.get('body', {}).get('content', [])))):
            o = objs.get(oid, {}); prop = o.get('inlineObjectProperties', o.get('positionedObjectProperties', {}))
            emb = prop.get('embeddedObject', {}); uri = emb.get('imageProperties', {}).get('contentUri')
            if not uri: continue
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]
            f = out / f'{slug}-{i + 1:02d}.png'
            try:
                data = urllib.request.urlopen(urllib.request.Request(uri, headers={'Authorization': 'Bearer ' + at}), context=CTX).read()
                f.write_bytes(data)
                manifest.append({'brand': brand, 'tab': title, 'file': str(f.relative_to(W)), 'bytes': len(data), 'desc': emb.get('description', '') or emb.get('title', '')})
            except Exception as e:
                print('fail', brand, title, e)
(W / 'media' / 'manifest.json').write_text(json.dumps(manifest, indent=1))
from collections import Counter
print(len(manifest), 'images', Counter(m['brand'] for m in manifest))
