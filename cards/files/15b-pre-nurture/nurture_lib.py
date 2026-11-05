#!/usr/bin/env python3
"""Shared builder for the 15b, 22 and 27 message sets.

One source per item (its build.py holds the copy). This module:
  * resolves [[config tokens]] from deliverables/_shared/funnel-config.json at build time
    (a FILL_ value is never printed: the token becomes a {{merge_field}} instead);
  * converts named WhatsApp variables to WhatsApp Business positional variables {{1}}, {{2}};
  * validates WhatsApp bodies against template rules and email steps against copy rules;
  * writes one CSV per channel, standalone HTML emails, a gallery and COPY.md.
Pattern taken from context/from-workshop-project/15b-pre-nurture/webinar-reminder-emails/build.py.
"""
import csv, html, json, os, re, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG = json.load(open(os.path.join(ROOT, "deliverables", "_shared", "funnel-config.json")))
sys.path.insert(0, os.path.join(ROOT, "deliverables", "12-calendar-invites"))
from schedule import session  # noqa: E402  (one source for the schedule in words)


def schedule_line():
    """The decided schedule, printed at the top of COPY.md and the email gallery."""
    try:
        s = session()
    except ValueError as e:
        return "Schedule: not set (%s)." % e
    return ("Schedule: first session %s, %d minutes; then %s. Each registrant sees the time in their own "
            "timezone through {{webinar_date_local}}, {{webinar_time_local}} and {{webinar_when_local}}." % (s["when"], s["minutes"], s["weekly"]))


CSV_COLUMNS = ["step_id", "trigger", "offset_minutes", "channel", "template_name",
               "subject", "body", "variables"]

# ---- brand tokens (context/from-workshop-project/brand/tokens.json) ----
INK, PAPER, VOLT, SLATE, LINE, WHITE, LILAC = ("#0b0d12", "#f7f8fb", "#6d4aff", "#5b6472",
                                                "#e2e8f0", "#ffffff", "#f1efff")
HEAD = "'Clash Display', 'Satoshi', 'Helvetica Neue', Arial, sans-serif"
BODY = "'Inter', 'Satoshi', -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# ---- every per-person or not-yet-known value, with where it comes from ----
VARIABLES = {
    "first_name": "Contact first name (webinar.registered data.first_name). Fallback: there",
    "webinar_title": "funnel-config webinar.title",
    "webinar_date_local": "Next webinar date in the registrant's timezone (data.timezone, fallback webinar.timezone; from webinar.day_of_week, first_date, weekly)",
    "webinar_time_local": "webinar.start_time_local converted to the registrant's timezone (webinar.registered data.timezone, IANA; fallback webinar.timezone), with the zone, for example 10:00 GMT (London) or 11:00 CET (Berlin) for the 12 November session",
    "webinar_when_local": "Date and time in one value, in the registrant's timezone, for example Thu 12 Nov, 10:00 GMT (London) or Thu 12 Nov, 11:00 CET (Berlin) (keeps WhatsApp templates light on variables)",
    "join_url": "Personal WebinarJam join link, merged from the contact: the register Worker (item 17) adds join_url to webinar.registered and the CRM stores it. funnel-config webinar.join_url (the generic room link) is only a fallback for a contact with no personal link",
    "calendar_url": "Add-to-calendar link for this registrant (WebinarJam calendar link or item 23 .ics)",
    "watch_url": "domains.funnel_domain + domains.paths.indoctrination",
    "video_funnels_url": "domains.funnel_domain + /watch/#funnels (media.indoctrination_videos.funnels plays there)",
    "video_revops_os_url": "domains.funnel_domain + /watch/#revops-os",
    "video_traffic_channels_url": "domains.funnel_domain + /watch/#traffic-channels",
    "video_bonuses_url": "domains.funnel_domain + /watch/#bonuses",
    "booking_url": "booking.round_robin_url (Cal.com team event, Conor and Scott)",
    "recording_url": "domains.funnel_domain + domains.paths.recording",
    "recording_offer_url": "recording page link that starts the video at the minute the offer begins (recording_url + #t=<seconds>)",
    "unsubscribe_url": "Sending tool unsubscribe link (Tantra footer)",
    "company_address": "brand.legal_footer_address",
    "linkedin_first_name": "First name as shown on LinkedIn (Tantra LinkedIn campaign field)",
}

def cfg(path):
    cur = CONFIG
    for k in path.split("."):
        cur = cur[k]
    return cur

def _money(n):
    return "${:,}".format(n)

TOKENS = {
    "host": lambda: cfg("brand.host_name"),
    "host_title": lambda: cfg("brand.host_title"),
    "company": lambda: cfg("brand.company"),
    "offer": lambda: cfg("offer.name"),
    "price": lambda: _money(cfg("offer.price_usd")),
    "call_title": lambda: cfg("booking.event_title"),
    "call_minutes": lambda: str(cfg("booking.duration_minutes")),
    "duration": lambda: str(cfg("webinar.duration_minutes")),
    "teach_minutes": lambda: str(cfg("webinar.presentation_minutes")),
    "qa_minutes": lambda: str(cfg("webinar.qa_minutes")),
    "cutoff": lambda: str(cfg("webinar.retarget_cutoff_minute")),
    "platform": lambda: cfg("webinar.platform"),
    "include1": lambda: cfg("offer.includes")[0],
    "include2": lambda: cfg("offer.includes")[1],
    "include3": lambda: cfg("offer.includes")[2],
    "include4": lambda: cfg("offer.includes")[3],
    "inc1": lambda: _lc(cfg("offer.includes")[0]),
    "inc2": lambda: _lc(cfg("offer.includes")[1]),
    "inc3": lambda: _lc(cfg("offer.includes")[2]),
    "inc4": lambda: _lc(cfg("offer.includes")[3]),
    "proposal": lambda: _lc(cfg("offer.proposal_sla")).replace("written", "a written", 1),
    "fit_budget": lambda: re.search(r"\$[\d,]+ or more", cfg("offer.fit")).group(0),
}

def _lc(s):
    return s[0].lower() + s[1:] if s and not s[:2].isdigit() and not s[0].isdigit() else s

def resolve(text):
    def sub(m):
        key = m.group(1)
        if key not in TOKENS:
            raise KeyError("unknown token [[%s]]" % key)
        val = TOKENS[key]()
        if str(val).startswith("FILL_"):
            return "{{%s}}" % key
        return str(val)
    return re.sub(r"\[\[([a-z0-9_]+)\]\]", sub, text)

VAR_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")

def named_vars(text):
    seen = []
    for v in VAR_RE.findall(text):
        if v not in seen:
            seen.append(v)
    return seen

def to_positional(text):
    names = named_vars(text)
    out = text
    for i, n in enumerate(names, 1):
        out = out.replace("{{%s}}" % n, "{{%d}}" % i)
    return out, names

def var_column(names, positional):
    if positional:
        return "; ".join("{{%d}}=%s" % (i, n) for i, n in enumerate(names, 1))
    return "; ".join(names)

# ---- validators ----
def check_whatsapp(step_id, name, body):
    p = []
    if not re.fullmatch(r"[a-z0-9_]{1,512}", name):
        p.append("template name must be lowercase letters, digits, underscores")
    if len(body) > 1024:
        p.append("body over 1,024 characters (%d)" % len(body))
    s = body.strip()
    if re.match(r"\{\{\d+\}\}", s) or re.search(r"\{\{\d+\}\}[.!]?$", s):
        p.append("body starts or ends on a variable")
    if re.search(r"\}\}\s*\{\{", body):
        p.append("two variables side by side")
    if "\t" in body or "    " in body:
        p.append("tab or 4+ spaces")
    if "STOP" not in body:
        p.append("no STOP line")
    if re.search(r"\[\[|\]\]|\[[A-Z ]+\]", body):
        p.append("unresolved bracket")
    return ["%s whatsapp: %s" % (step_id, x) for x in p]

BANNED = ["leverage", "unlock", "seamless", "game-changer", "game changer", "supercharge",
          "fast-paced world", "end to end", "engineered system", "delve", "robust", "elevate",
          "nothing to" + " buy", "no" + " pitch", "100%" + " free"]

def check_text(step_id, text):
    p = []
    low = text.lower()
    for w in BANNED:
        if w in low:
            p.append("banned phrase '%s'" % w)
    if re.search("[\u2013\u2014]", text):
        p.append("en or em dash")
    if re.search(r"\[\[|\]\]", text):
        p.append("unresolved config token")
    for v in VAR_RE.findall(text):
        if v not in VARIABLES and v not in TOKENS:
            p.append("unknown merge field {{%s}}" % v)
    return ["%s: %s" % (step_id, x) for x in p]

# ---- HTML email ----
def _p(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r'<strong style="font-weight:600;color:%s;">\1</strong>' % INK, t)
    return t.replace("\n", "<br>")

def _button(label, url):
    return f"""
<tr><td align="center" style="padding:10px 0 6px;">
  <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="{url}" style="height:52px;v-text-anchor:middle;width:360px;" arcsize="18%" stroke="f" fillcolor="{VOLT}"><center style="color:#ffffff;font-family:Arial,sans-serif;font-size:15px;font-weight:bold;">{html.escape(label)}</center></v:roundrect><![endif]-->
  <!--[if !mso]><!-- -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:360px;margin:0 auto;"><tr>
    <td align="center" bgcolor="{VOLT}" style="border-radius:10px;">
      <a href="{url}" style="display:block;padding:16px 24px;font-family:{BODY};font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:10px;">{html.escape(label)}</a>
    </td></tr></table>
  <!--<![endif]-->
</td></tr>"""

def render_email(step, footer_reason, logo="img/tantra-mark-ink.png"):
    e = step["email"]
    rows = []
    if e.get("eyebrow"):
        rows.append(f'<tr><td style="padding:0 0 14px;font-family:{BODY};font-size:12px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:{VOLT};">{html.escape(e["eyebrow"])}</td></tr>')
    rows.append(f'<tr><td style="padding:0 0 18px;"><h1 style="margin:0;font-family:{HEAD};font-weight:600;font-size:28px;line-height:1.2;color:{INK};">{_p(e["headline"])}</h1></td></tr>')
    for para in e["paras"]:
        if para.startswith("CTA"):
            continue
        rows.append(f'<tr><td style="padding:0 0 16px;font-family:{BODY};font-size:16px;line-height:1.6;color:{INK};">{_p(para)}</td></tr>')
    label, var = e["cta"]
    rows.append(_button(label, "{{%s}}" % var))
    if e.get("cta2"):
        l2, v2 = e["cta2"]
        rows.append(f'<tr><td align="center" style="padding:10px 0 4px;font-family:{BODY};font-size:14px;color:{SLATE};">{html.escape(e.get("cta2_lead", "Or"))} <a href="{{{{{v2}}}}}" style="color:{VOLT};font-weight:600;">{html.escape(l2)}</a></td></tr>')
    if e.get("ps"):
        rows.append(f'<tr><td style="padding:18px 0 0;font-family:{BODY};font-size:15px;line-height:1.6;color:{SLATE};">{_p(e["ps"])}</td></tr>')
    rows.append(f'<tr><td style="padding:24px 0 0;font-family:{BODY};font-size:16px;line-height:1.5;color:{INK};">{html.escape(resolve("[[host]]"))}<br><span style="font-size:13px;color:{SLATE};">{html.escape(resolve("[[host_title]]"))}</span></td></tr>')
    body = "".join(rows)
    return f"""<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>{html.escape(e["subject"])}</title>
<style>
  body{{margin:0;padding:0;background:{PAPER};-webkit-text-size-adjust:100%;}}
  table{{border-collapse:collapse;}}
  img{{border:0;display:block;}}
  @media only screen and (max-width:620px){{ .card{{width:100%!important;}} .pad{{padding-left:22px!important;padding-right:22px!important;}} h1{{font-size:24px!important;}} }}
</style>
</head>
<body style="margin:0;background:{PAPER};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAPER};">{html.escape(e["preheader"])}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{PAPER};">
<tr><td align="center" style="padding:28px 12px;">
  <table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:{WHITE};border:1px solid {LINE};border-radius:14px;">
    <tr><td class="pad" style="padding:30px 40px 0;">
      <img src="{logo}" width="40" height="40" alt="{html.escape(resolve('[[company]]'))}" style="width:40px;height:40px;">
    </td></tr>
    <tr><td class="pad" style="padding:26px 40px 34px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{body}</table>
    </td></tr>
    <tr><td class="pad" style="padding:20px 40px 28px;border-top:1px solid {LINE};font-family:{BODY};font-size:12px;line-height:1.7;color:{SLATE};">
      {html.escape(footer_reason)}<br>
      {{{{company_address}}}}<br>
      <a href="{{{{unsubscribe_url}}}}" style="color:{SLATE};">Unsubscribe</a>
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""

def email_plain(step):
    e = step["email"]
    parts = [p for p in e["paras"]]
    label, var = e["cta"]
    parts.append("%s: {{%s}}" % (label, var))
    if e.get("cta2"):
        l2, v2 = e["cta2"]
        parts.append("%s %s: {{%s}}" % (e.get("cta2_lead", "Or"), l2[0].lower() + l2[1:], v2))
    if e.get("ps"):
        parts.append(e["ps"])
    parts.append(resolve("[[host]]"))
    return "\n\n".join(parts).replace("**", "")

def resolve_step(step):
    s = json.loads(json.dumps(step))
    if "email" in s:
        e = s["email"]
        for k in ("subject", "preheader", "headline", "eyebrow", "ps", "cta2_lead"):
            if e.get(k):
                e[k] = resolve(e[k])
        e["paras"] = [resolve(p) for p in e["paras"]]
        e["cta"] = [resolve(e["cta"][0]), e["cta"][1]]
        if e.get("cta2"):
            e["cta2"] = [resolve(e["cta2"][0]), e["cta2"][1]]
    for k in ("whatsapp", "linkedin", "trigger"):
        if s.get(k):
            s[k] = resolve(s[k])
    return s

WA_WINDOW = ("WhatsApp only 08:00 to 20:00 in the registrant's timezone (data.timezone, fallback webinar.timezone); "
             "outside it the email goes and the WhatsApp is skipped")

def build(steps, out_dir, prefix, footer_reason, gallery_title, extra_checks=None, call_rows=None,
          wa_category="Utility"):
    """steps: list of dicts with step_id, trigger, offset, anchor, template, email{...}, whatsapp."""
    problems = []
    steps = [resolve_step(s) for s in steps]
    email_rows, wa_rows = [], []
    emails_dir = os.path.join(out_dir, "emails")
    os.makedirs(emails_dir, exist_ok=True)
    gallery = []
    for s in steps:
        trig = "%s | %s" % (s["anchor"], s["trigger"])
        if "email" in s:
            plain = email_plain(s)
            problems += check_text(s["step_id"] + " email", plain + s["email"]["subject"] + s["email"]["headline"])
            email_rows.append({"step_id": s["step_id"], "trigger": trig, "offset_minutes": s["offset"],
                               "channel": "email", "template_name": "%s_email" % s["template"],
                               "subject": s["email"]["subject"], "body": plain,
                               "variables": var_column(named_vars(s["email"]["subject"] + plain), False)})
            fname = "%s.html" % s["step_id"]
            with open(os.path.join(emails_dir, fname), "w") as f:
                f.write(render_email(s, footer_reason))
            gallery.append((fname, s["step_id"], s["email"]["subject"]))
        if s.get("whatsapp"):
            body, names = to_positional(s["whatsapp"])
            name = "%s_wa" % s["template"]
            problems += check_text(s["step_id"] + " whatsapp", s["whatsapp"])
            problems += check_whatsapp(s["step_id"], name, body)
            cat = s.get("wa_category", wa_category)
            wa_trig = "%s; %s; template category %s" % (trig, WA_WINDOW, cat)
            wa_rows.append({"step_id": s["step_id"], "trigger": wa_trig, "offset_minutes": s["offset"],
                            "channel": "whatsapp", "template_name": name, "subject": "",
                            "body": body, "variables": var_column(names, True)})
        if extra_checks:
            problems += extra_checks(s)
    def write(name, rows):
        if not rows:
            return
        with open(os.path.join(out_dir, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            w.writeheader()
            w.writerows(rows)
    write("email.csv", email_rows)
    write("whatsapp.csv", wa_rows)
    if call_rows:
        write("vodex.csv", call_rows)
    # gallery
    tiles = "".join(f'<a class="t" href="{fn}" target="pv"><b>{html.escape(sid)}</b><span>{html.escape(subj)}</span></a>' for fn, sid, subj in gallery)
    with open(os.path.join(emails_dir, "index.html"), "w") as f:
        f.write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(gallery_title)}</title>
<style>body{{margin:0;font-family:{BODY};color:{INK};background:{PAPER};}}header{{padding:20px 24px;border-bottom:1px solid {LINE};background:#fff;}}h1{{font-family:{HEAD};font-size:20px;margin:0;}}
.w{{display:flex;min-height:calc(100vh - 64px);}}nav{{width:320px;overflow:auto;padding:12px;border-right:1px solid {LINE};background:#fff;}}
.t{{display:block;padding:10px 12px;margin-bottom:8px;border:1px solid {LINE};border-radius:8px;color:{INK};text-decoration:none;}}.t:hover{{border-color:{VOLT};}}
.t b{{display:block;font-size:11px;letter-spacing:.08em;color:{VOLT};}}.t span{{font-size:14px;}}iframe{{flex:1;border:0;min-height:calc(100vh - 64px);}}
@media(max-width:760px){{.w{{flex-direction:column;}}nav{{width:auto;}}}}</style></head>
<body><header><h1>{html.escape(gallery_title)}</h1><p style="margin:6px 0 0;font-size:13px;color:{SLATE};">{html.escape(schedule_line())}</p></header><div class="w"><nav>{tiles}</nav><iframe name="pv" src="{gallery[0][0] if gallery else ''}"></iframe></div></body></html>""")
    # COPY.md for reading
    lines = ["# %s: Full Copy" % gallery_title, "",
             "Generated by build.py from the same source as the CSVs and HTML. Edit build.py, then rerun it.", "",
             schedule_line(), ""]
    for s in steps:
        lines += ["## %s: %s" % (s["step_id"], s["title"]), "",
                  "- When: %s, offset %s minutes" % (s["anchor"], s["offset"]),
                  "- Who: %s" % s["trigger"], ""]
        if "email" in s:
            lines += ["**Email subject:** %s  " % s["email"]["subject"],
                      "**Preheader:** %s  " % s["email"]["preheader"],
                      "**Headline:** %s" % s["email"]["headline"], "", "```", email_plain(s), "```", ""]
        if s.get("whatsapp"):
            lines += ["**WhatsApp** (`%s_wa`, %s template, sent only 08:00 to 20:00 local):" % (s["template"], s.get("wa_category", wa_category)), "", "```", s["whatsapp"], "```", ""]
        if s.get("linkedin"):
            lines += ["**LinkedIn:**", "", "```", s["linkedin"], "```", ""]
    with open(os.path.join(out_dir, "COPY.md"), "w") as f:
        f.write("\n".join(lines))
    return problems, steps
