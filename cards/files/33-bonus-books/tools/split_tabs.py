"""Split fetched docs into one file per tab: _work/tabs/<brand>/<NN>-<slug>.txt and an index tsv."""
import json, re, sys, pathlib
W = pathlib.Path(sys.argv[1]); out = W / 'tabs'; out.mkdir(exist_ok=True)
BR = json.loads((W / 'brands.json').read_text())   # doc id prefix -> folder name (private)
rows = []
for f in sorted((W / 'docs').glob('*.txt')):
    b = BR[f.name[:5]]; d = out / b; d.mkdir(exist_ok=True)
    parts = re.split(r'\n@@TAB (.*)\n', f.read_text())
    for i in range(1, len(parts), 2):
        title = parts[i].strip(); body = parts[i + 1]
        n = (i + 1) // 2; slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
        p = d / f'{n:02d}-{slug}.txt'; p.write_text(f'TAB: {title}\n\n{body}')
        rows.append(f'{b}\t{p.name}\t{len(body)}\t{title}')
(W / 'tabs_index.tsv').write_text('\n'.join(rows) + '\n')
print(len(rows), 'tabs')
