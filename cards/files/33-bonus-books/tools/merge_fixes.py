"""Fold the final anonymity check (_work/media/fixes_*.json) back into the review files, then re-run apply_media.py."""
import json, pathlib
W = pathlib.Path(__file__).resolve().parent.parent / '_work' / 'media'
outmap = json.loads((W / 'out_map.json').read_text())
reviews = {f.name: json.loads(f.read_text()) for f in W.glob('review_*.json')}
n = d = 0
for ff in W.glob('fixes_*.json'):
    for fx in json.loads(ff.read_text()):
        src = outmap.get(fx['name'])
        if not src: print('unknown', fx['name']); continue
        items = reviews[src['review']]
        it = next((i for i in items if i['file'] == src['file']), None)
        if it is None: it = {'file': src['file'], 'keep': True, 'blur': []}; items.append(it)
        if fx.get('drop'): it['keep'] = False; d += 1
        else: it['blur'] = (it.get('blur') or []) + fx.get('blur', []); n += 1
for name, items in reviews.items(): (W / name).write_text(json.dumps(items, indent=1))
print(f'{n} images got extra blur, {d} dropped')
