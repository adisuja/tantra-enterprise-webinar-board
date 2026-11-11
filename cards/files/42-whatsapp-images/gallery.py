"""Gallery of every WhatsApp preview image (card 42), published with the funnel map at /wa-images/.
Writes ../39-funnel-map/src/wa-images/index.html from images.json. Run: python3 gallery.py, then bash ../39-funnel-map/publish.sh."""
import html, json, pathlib
HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / '39-funnel-map/src/wa-images'
BASE = 'https://crm-api.usetantra.com/media/wa/'
ims = json.load(open(HERE / 'images.json'))['images']
VIA = {
    'webinar': 'Tantra CRM, WhatsApp Business API +1 445 622 7661 (Twilio)',
    'sales': "Tantra CRM, Adi's WhatsApp account (Unipile)",
}
def row(i):
    t = i['template']
    how = (f'Template image version <code>{t}_img</code>: waiting for Meta (submitted 9 Nov). The text version <code>{t}</code> sends until it is approved.'
           if t else 'Attached to the free-text message, with the text as its caption.')
    if i['group'] == 'sales':
        how = 'Attached to the message, with the text as its caption. If WhatsApp refuses the image, the text still goes out.'
    label = (i.get('big') or f"{i['count']} {i['unit']}").replace('[', '').replace(']', '')
    return (f'<figure><a href="{BASE}{i["key"]}.jpg?v=1" target="_blank" rel="noopener"><img src="{BASE}{i["key"]}.jpg?v=1" alt="{html.escape(label)}" loading="lazy"></a>'
            f'<figcaption><b>{html.escape(i["msg"])}</b> · {html.escape(label)}<br><span>{VIA[i["group"]]}</span><br><span>{how}</span></figcaption></figure>')
groups = [('Webinar funnel (Business API)', [i for i in ims if i['group'] == 'webinar']), ('Sales pipeline (WhatsApp account)', [i for i in ims if i['group'] == 'sales'])]
body = ''.join(f'<h2>{g}</h2><div class="grid">{"".join(row(i) for i in L)}</div>' for g, L in groups)
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>WhatsApp preview images | Tantra</title><style>
body{{margin:0;font:15px/1.5 Inter,system-ui,sans-serif;color:#0b0d12;background:#f7f8fb}}main{{max-width:1180px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-size:28px;letter-spacing:-.03em;margin:0 0 6px}}h2{{font-size:18px;margin:32px 0 12px}}p.lead{{color:#5b6472;margin:0 0 8px;max-width:70ch}}a{{color:#4b2fd6}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}figure{{margin:0;background:#fff;border:1px solid #e6e8ef;border-radius:14px;overflow:hidden}}
figure img{{display:block;width:100%;aspect-ratio:1.91/1;object-fit:cover}}figcaption{{padding:10px 12px 12px;font-size:13px}}figcaption span{{color:#5b6472}}code{{font-size:12px;background:#f3f0ff;padding:1px 4px;border-radius:4px}}
</style></head><body><main><p><a href="../">Back to the funnel map</a></p><h1>WhatsApp preview images</h1>
<p class="lead">Every image that goes out with a WhatsApp message, and how it is sent. Pick or change them in the CRM: Automation, open the sequence, click the WhatsApp step, Preview image.</p>
{body}</main></body></html>'''
OUT.mkdir(parents=True, exist_ok=True)
for bad in ('—', '–'):
    assert bad not in page, 'dash in gallery'
(OUT / 'index.html').write_text(page)
print('wrote', OUT / 'index.html')
