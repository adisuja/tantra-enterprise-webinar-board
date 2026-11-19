"""Round 12 (Adi, 19 Nov 2026): iPhone screens for the opening slides 5 to 7, drawn the way the apps look on iOS today
(iOS 26 status bar and Dynamic Island; LinkedIn post page with comments, LinkedIn messaging, Apple Mail message view with
the floating Liquid Glass toolbar, WhatsApp chat with its floating chat bar). Every screen is 393 x 852 points, drawn at
1 pt = 1 px so the connector lines (src/js/flow.js) can read element positions directly. Styles: src/ios.css."""
import html, re

E = html.escape

def ic(name):
    """Inline outline icons in the style of the iOS apps (SF Symbols and LinkedIn's own set)."""
    P = {
        'back': '<path d="M15 4 7 12l8 8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
        'dots': '<circle cx="5" cy="12" r="1.9"/><circle cx="12" cy="12" r="1.9"/><circle cx="19" cy="12" r="1.9"/>',
        'like': '<path d="M7 10v10H4V10h3Zm2 10V10l4-7c1.3 0 2.2 1 2 2.3L14.5 9H19a2 2 0 0 1 2 2.3l-1.2 6.8A2.3 2.3 0 0 1 17.5 20H9Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>',
        'comment': '<path d="M4 5h16v11H9l-5 4V5Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>',
        'repost': '<path d="M7 7h11l-3-3M17 17H6l3 3M18 7v5M6 17v-5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
        'send': '<path d="M21 3 3 10.5l7 2.5 2.5 7L21 3Zm-11 10 5-5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>',
        'video': '<path d="M3 7h12v10H3zM15 10.5 21 7v10l-6-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
        'phone': '<path d="M6.6 3.5 9.4 7 7.8 9.4a12 12 0 0 0 6.8 6.8l2.4-1.6 3.5 2.8-1.7 3.1C11 20.5 3.5 13 3.5 5.2l3.1-1.7Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
        'plus': '<path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
        'camera': '<path d="M4 8h3.5L9 6h6l1.5 2H20v11H4V8Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="13.3" r="3.4" fill="none" stroke="currentColor" stroke-width="1.8"/>',
        'mic': '<rect x="9" y="3" width="6" height="11" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
        'trash': '<path d="M4 6.5h16M9.5 6.5V4h5v2.5M6.5 6.5l1 13.5h9l1-13.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>',
        'folder': '<path d="M3 6h6l2 2h10v11H3V6Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
        'reply': '<path d="M10 6 4 12l6 6M4 12h10a6 6 0 0 1 6 6" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
        'compose': '<path d="M4 20h4L19 9l-4-4L4 16v4ZM13 7l4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
        'up': '<path d="m6 15 6-6 6 6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
        'down': '<path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
        'globe': '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 12h17M12 3.5c3 3.4 3 13.6 0 17M12 3.5c-3 3.4-3 13.6 0 17" fill="none" stroke="currentColor" stroke-width="1.5"/>',
        'image': '<rect x="4" y="5" width="16" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="9" cy="10" r="1.6"/><path d="m5 18 5-5 3 3 2-2 4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
        'doc': '<path d="M6 3h8l4 4v14H6V3Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 3v4h4M9 12h6M9 16h6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
        'ticks': '<path d="m2 12.5 4 4 8-9M10 16.5l1 1 8-9" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
        'sticker': '<path d="M12 3.5a8.5 8.5 0 1 0 8.5 8.5V9.5L14.5 3.5H12Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    }[name]
    fill = ' fill="currentColor"' if name in ('dots', 'image') else ''
    return f'<svg class="i i-{name}" viewBox="0 0 24 24"{fill}>{P}</svg>'

STATUS = ('<div class="ip-st"><b>9:41</b><span class="ip-isl"></span><span class="ip-sys">'
          '<svg viewBox="0 0 19 12"><rect x="0" y="8" width="3.2" height="4" rx=".8"/><rect x="5" y="5.5" width="3.2" height="6.5" rx=".8"/>'
          '<rect x="10" y="3" width="3.2" height="9" rx=".8"/><rect x="15" y="0" width="3.2" height="12" rx=".8"/></svg>'
          '<svg viewBox="0 0 17 12"><path d="M8.5 2.3c2.5 0 4.8 1 6.5 2.6l1.2-1.3A11 11 0 0 0 8.5.5 11 11 0 0 0 .8 3.6L2 4.9a9.2 9.2 0 0 1 6.5-2.6Zm0 3.6c1.5 0 2.9.6 4 1.6l1.2-1.3a7.5 7.5 0 0 0-10.4 0l1.2 1.3c1.1-1 2.5-1.6 4-1.6Zm0 3.6c.6 0 1.1.2 1.5.6L8.5 11.7 7 10.1c.4-.4.9-.6 1.5-.6Z"/></svg>'
          '<span class="ip-bat"><i></i></span></span></div>')

def phone(screen, cls='', pid=''):
    idattr = f' id="{pid}"' if pid else ''
    return f'<div class="ip {cls}"{idattr}><div class="ip-scr">{STATUS}{screen}</div></div>'

def av(name, img=None, size=40, cls=''):
    if img:
        src = img if img.startswith('assets/') else f'assets/r10/{img}'
        return f'<img class="ip-av {cls}" style="width:{size}px;height:{size}px" src="{src}" alt="">'
    ini = ''.join(w[0] for w in name.split()[:2]).upper()
    return f'<span class="ip-av ini {cls}" style="width:{size}px;height:{size}px;font-size:{round(size * .38)}px">{E(ini)}</span>'

# ---------------------------------------------------------------- LinkedIn: a post, opened, with its comments
def li_post(author, img, lines, reactions, comments_n, comments, hl=None, cls='', age='2w'):
    """comments: list of (name, text, age). hl: index of the comment to mark as the one the flow starts from."""
    body = ''.join(f'<p>{E(l)}</p>' for l in lines)
    cs = ''
    for i, (n, t, age) in enumerate(comments):
        mark = ' hl' if i == hl else ''
        cs += (f'<div class="li-cm{mark}">{av(n, None, 32)}<div class="li-cb"><div class="li-cn"><b>{E(n)}</b><span>{E(age)}</span>{ic("dots")}</div>'
               f'<p>{E(t)}</p><div class="li-cl">Like <i>|</i> Reply</div></div></div>')
    return phone(f'''<div class="li-nav">{ic('back')}<span class="li-srch">Search</span>{ic('dots')}</div>
<div class="li-post"><div class="li-au">{av(author, img, 48)}<div><b>{E(author)} <span>• 1st</span></b><small>{E(age)} • {ic('globe')}</small></div></div>
<div class="li-tx">{body}<p class="li-more">...more</p></div>
<div class="li-rx"><span class="li-em"><i class="e1">👍</i><i class="e2">👏</i><i class="e3">❤️</i></span>{E(reactions)}<span class="li-rc">{E(comments_n)} comments</span></div>
<div class="li-act"><span>{ic('like')}Like</span><span>{ic('comment')}Comment</span><span>{ic('repost')}Repost</span><span>{ic('send')}Send</span></div></div>
<div class="li-sort">Most relevant <svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.4"/></svg></div>
<div class="li-cms">{cs}</div>''', 'li ' + cls)

# ---------------------------------------------------------------- LinkedIn messaging thread
def li_dm(peer, peer_img, items, cls='', pid=''):
    """items: ('day', label) | (name, img, time, text, attach or None, hl bool)."""
    out = ''
    for it in items:
        if it[0] == 'day':
            out += f'<div class="ld-day"><span>{E(it[1])}</span></div>'
            continue
        n, img, tm, text, att, hl = it
        a = ''
        if att:
            a = f'<div class="ld-att">{ic("doc")}<div><b>{E(att[0])}</b><span>{E(att[1])}</span></div></div>'
        out += (f'<div class="ld-m{" hl" if hl else ""}">{av(n, img, 40)}<div><div class="ld-h"><b>{E(n)}</b><span>• {E(tm)}</span></div>'
                f'<p>{E(text)}</p>{a}</div></div>')
    return phone(f'''<div class="ld-nav">{ic('back')}{av(peer, peer_img, 32)}<div class="ld-who"><b>{E(peer)}</b><span>Active now</span></div>{ic('video')}{ic('dots')}</div>
<div class="ld-body">{out}</div>
<div class="ld-bar"><div class="ld-in">Write a message...</div><div class="ld-tools">{ic('image')}{ic('plus')}<b>GIF</b><span class="ld-send">Send</span></div></div>''', 'ld ' + cls, pid)

# ---------------------------------------------------------------- Apple Mail, one message open (iOS 26)
def mail(sender, to, when, subject, paras, quote=None, cls='', pid=''):
    body = ''.join(f'<p>{E(p)}</p>' for p in paras)
    q = f'<div class="ml-q"><small>{E(quote[0])}</small><p>{E(quote[1])}</p></div>' if quote else ''
    return phone(f'''<div class="ml-nav"><span class="gl r">{ic('back')}</span><span class="gl pill">{ic('up')}{ic('down')}</span></div>
<div class="ml-hd">{av(sender, None, 42, 'ml-av')}<div class="ml-from"><b>{E(sender)}</b><span>To: {E(to)} <i>›</i></span></div><time>{E(when)}</time></div>
<h4 class="ml-sub">{E(subject)}</h4>
<div class="ml-body">{body}{q}</div>
<div class="ml-bar"><span class="gl r">{ic('trash')}</span><span class="gl pill wide">{ic('folder')}{ic('reply')}</span><span class="gl r">{ic('compose')}</span></div>''', 'ml ' + cls, pid)

# ---------------------------------------------------------------- WhatsApp chat (iOS, Liquid Glass chat bar)
def wa(peer, items, cls='', pid=''):
    """items: ('day', label) | ('out'|'in', text, time, hl bool)."""
    out = ''
    for it in items:
        if it[0] == 'day':
            out += f'<div class="wa-day"><span>{E(it[1])}</span></div>'
            continue
        d, text, tm, hl = it
        tick = ic('ticks') if d == 'out' else ''
        out += f'<div class="wa-m {d}{" hl" if hl else ""}"><p>{E(text)}<span class="wa-t">{E(tm)}{tick}</span></p></div>'
    return phone(f'''<div class="wa-nav"><span class="gl r">{ic('back')}</span>{av(peer, None, 36)}<div class="wa-who"><b>{E(peer)}</b><span>online</span></div><span class="gl pill">{ic('video')}{ic('phone')}</span></div>
<div class="wa-body">{out}</div>
<div class="wa-bar"><span class="gl r">{ic('plus')}</span><div class="wa-in">{ic('sticker')}</div><span class="gl r">{ic('camera')}</span><span class="gl r">{ic('mic')}</span></div>''', 'wa ' + cls, pid)

# ---------------------------------------------------------------- LinkedIn post, from real data (round 12b)
RX = ('<span class="li-em"><i class="e1"><svg viewBox="0 0 16 16"><path fill="#fff" d="M5 7v6H3V7h2Zm1 6V7l2.5-4.2c.8 0 1.3.6 1.2 1.4L9.3 6.5H12a1.2 1.2 0 0 1 1.2 1.4l-.7 4A1.4 1.4 0 0 1 11 13H6Z"/></svg></i>'
      '<i class="e2"><svg viewBox="0 0 16 16"><path fill="#fff" d="M8 2.5 9.2 6l3.6.2-2.8 2.3.9 3.5L8 10.1 5.1 12l.9-3.5-2.8-2.3L6.8 6 8 2.5Z"/></svg></i>'
      '<i class="e3"><svg viewBox="0 0 16 16"><path fill="#fff" d="M8 13.2 3.3 8.6a2.8 2.8 0 0 1 4-4L8 5.3l.7-.7a2.8 2.8 0 0 1 4 4L8 13.2Z"/></svg></i></span>')

def comment(c, hl=False, author=None):
    deg = f' <span>• {E(c["deg"])}</span>' if c.get('deg') else ''
    head = f'<small>{E(c["head"])}</small>' if c.get('head') else ''
    rep = ''
    if c.get('reply') and author:
        nm = c['name']
        first = c['reply'].split('\n')[0].strip()
        body = E(first)
        if first.startswith(nm):
            body = f'<b class="mn">{E(nm)}</b>{E(first[len(nm):])}'
        link = re.search(r'https?://\S+', c['reply'])
        tail = f'<br>Here you go: <a>{E(link.group(0))}</a>' if link and link.group(0) not in first else ''
        rep = (f'<div class="li-rp">{av(author["author"], author["avatar"], 32)}<div class="li-cb"><div class="li-cn"><b>{E(author["author"])}</b><em>Author</em><span>{E(c["age"])}</span>{ic("dots")}</div>'
               f'<small>{E(author["head"])}</small><p>{body}{tail}</p><div class="li-cl">Like <i>|</i> Reply</div></div></div>')
    return (f'<div class="li-cm{" hl" if hl else ""}">{av(c["name"], c.get("avatar"), 40)}<div class="li-cb"><div class="li-cn"><b>{E(c["name"])}</b>{deg}<span>{E(c["age"])}</span>{ic("dots")}</div>'
            f'{head}<p>{E(c["text"])}</p><div class="li-cl">Like <i>|</i> Reply</div></div></div>{rep}')

def li_real(d, picks, hl=None, lines=3, img_h=190, cls='', pid='', views=None):
    """d: one post from src/r12-posts.json. picks: comment names to show, in order. hl: name to mark."""
    src = d['body'].replace('\u2014', ',').replace('\u2013', ',')
    body = [l for l in re.split(r'\n+', src) if l.strip()]
    if len(body) < 2:
        body = re.split(r'(?<=[.!?]) (?=[A-Z(])', src)
    tx = ''.join(f'<p>{E(l)}</p>' for l in body[:lines])
    cs, used = '', set()
    for n in picks:
        c = next((c for c in d['list'] if c['name'] == n and id(c) not in used), None)
        if not c: continue
        used.add(id(c)); cs += comment(c, n == hl, d)
    img = f'<div class="li-img" style="height:{img_h}px"><img src="{d["image"]}" alt=""></div>' if d.get('image') and img_h else ''
    rp = f' • {d["reposts"]} reposts' if d.get('reposts') else ''
    vw = (f'<div class="li-vw"><svg viewBox="0 0 16 16"><path d="M2 13h12M4 11V7M8 11V3M12 11V8" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>'
          f'<b>{E(views)}</b> impressions<span>View analytics</span></div>') if views else ''
    nav = f'<div class="li-nav">{ic("back")}<span class="li-srch">Search</span>{ic("dots")}</div>'
    au = (f'<div class="li-post"><div class="li-au">{av(d["author"], d["avatar"], 48)}<div><b>{E(d["author"])} <span>• 1st</span></b>'
          f'<small class="li-hd">{E(d["head"])}</small><small>{E(d["age"])} • {ic("globe")}</small></div></div>'
          f'<div class="li-tx">{tx}<p class="li-more">...more</p></div></div>{img}')
    soc = (f'<div class="li-post"><div class="li-rx">{RX}{d["reactions"]:,}<span class="li-rc">{d["comments"]:,} comments{rp}</span></div>{vw}'
           f'<div class="li-act"><span>{ic("like")}Like</span><span>{ic("comment")}Comment</span><span>{ic("repost")}Repost</span><span>{ic("send")}Send</span></div></div>')
    sort = '<div class="li-sort">Most relevant <svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.4"/></svg></div>'
    return phone(nav + au + soc + sort + f'<div class="li-cms">{cs}</div>', 'li ' + cls, pid)
