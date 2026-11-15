"""Replace the CTA buttons with the booking link printed as text (the user: no buttons, show the links)."""
import os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = R + '/src'
BTN = re.compile(r'<a class="book" style="top:(\d+)px" href="\{\{BOOK\}\}" target="_blank" rel="noopener" data-a="pop" data-d="([\d.]+)">Book your call <svg class="ico" viewBox="0 0 24 24"><line x1="3" y1="12" x2="20" y2="12"/><polyline points="14,6 20,12 14,18"/></svg></a>')
n = 0
for f in ('b.html', 'e.html'):
    p = f'{S}/slides/{f}'; s = open(p).read()
    s, k = BTN.subn(lambda m: f'<a class="blink" style="top:{m.group(1)}px" href="{{{{BOOK}}}}" target="_blank" rel="noopener" data-a="rise" data-d="{m.group(2)}"><span class="vl s">Book your call at</span><span class="bl-url">{{{{BOOK_SHOW}}}}</span></a>', s)
    n += k; open(p, 'w').write(s)
print('buttons replaced:', n)
css = open(S + '/v3.css').read()
if '.blink' not in css:
    css += ('\n/* booking link shown as text, not a button */\n'
            '.blink { position: absolute; left: 140px; width: 1000px; display: flex; flex-direction: column; gap: 12px; text-decoration: none; }\n'
            '.blink .bl-url { font: 600 50px/1.25 var(--font); color: var(--iris); text-decoration: underline; text-decoration-thickness: 3px; text-underline-offset: 12px; text-decoration-color: rgba(167,139,250,.45); overflow-wrap: anywhere; }\n'
            '.blink:focus-visible { outline: 3px solid var(--iris); outline-offset: 8px; border-radius: 8px; }\n')
    open(S + '/v3.css', 'w').write(css)
b = open(R + '/tools/build.py').read()
if 'BOOK_SHOW' not in b:
    b = b.replace("BOOK = 'https://crm.usetantra.com/book/tantra/ai-revops-strategy-consultation?utm_source=webinar_deck'",
                  "BOOK = 'https://crm.usetantra.com/book/tantra/ai-revops-strategy-consultation?utm_source=webinar_deck'\n"
                  "# The link printed on the CTA slides. Swap in the short link once it exists, e.g. 'sellwithtantra.com/call'.\n"
                  "BOOK_SHOW = 'crm.usetantra.com/book/tantra/<wbr>ai-revops-strategy-consultation'")
    b = b.replace("slides = slides.replace('{{BOOK}}', BOOK).replace('{{QR}}', qr_block())",
                  "slides = slides.replace('{{BOOK_SHOW}}', BOOK_SHOW).replace('{{BOOK}}', BOOK).replace('{{QR}}', qr_block())")
    open(R + '/tools/build.py', 'w').write(b)
print('ok')
