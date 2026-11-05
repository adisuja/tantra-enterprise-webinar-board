#!/usr/bin/env python3
"""Item 12 cold calendar invites: one source for both variants.

python3 build.py [--date YYYY-MM-DD]
    writes invites.md, calendar-import.csv and calendar-series-example.ics for one session
    (default webinar.first_date). Known funnel-config values are filled; a value still FILL_ stays
    a visible merge field ({{webinar.title}}, {{domains.funnel_domain}}).
python3 build.py --tantra [--date YYYY-MM-DD]
    writes calendar-tantra.csv, the file to load, with line breaks as <br>.
    Refuses while any funnel-config value it needs is still FILL_.

Two kinds of field:
  [[token]]      filled here at build time from funnel-config.json and schedule.py
  {{firstName}}  Tantra merge tags, filled by Tantra per guest at send time
                 (https://usetantra.com/help/templates-and-ai/merge-tags-and-spintax).
No AI personalisation field anywhere (Adi 2026-11-05): merge tags only.
"""
import csv, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE.parent / "_shared" / "funnel-config.json"
sys.path.insert(0, str(HERE))
from schedule import session  # noqa: E402

TANTRA_TAGS = {"firstName", "company"}

TAIL = """If it's not relevant, just decline. No follow-up from me.

Get your join link here: [[registration_link]]

The session: [[webinar.title]]
Your host: [[brand.host_name]] ([[brand.host_full_name]]), [[brand.host_title]]. 250+ brands, 21+ countries, 10+ years.

Yes or Maybe keeps the time on your calendar. Your personal join link arrives when you register at the link above."""

VARIANTS = [
    {
        "id": "A", "name": "Meeting-style topic title, no merge fields", "utm": "cal_a", "personalized": "on",
        "title": "AI revenue generation teardown ([[webinar.duration_minutes]] min)",
        "description": """[[date_words]], [[range_words]]. [[webinar.duration_minutes]] minutes, live online.

For founders who want revenue that doesn't depend on referrals or on them selling every deal. You'll leave with the AI revenue system my team builds, stage by stage: who gets invited, who shows up, who books a sales call.

""" + TAIL,
    },
    {
        "id": "B", "name": "Problem title, first name and company merge fields", "utm": "cal_b", "personalized": "on",
        "title": "Founder Pipeline Teardown: Where AI Fits",
        "description": """Hi {{firstName}},

[[date_words]], [[range_words]]. [[webinar.duration_minutes]] minutes, live online.

If the pipeline at {{company}} still runs on referrals and your own calendar, this hour is for you. I'll take a founder's funnel apart stage by stage and show where AI takes over the repetitive work.

""" + TAIL,
    },
]

HEADER = ["variant", "campaign_name", "list_split", "event_title", "description", "date", "time", "end_time", "minutes",
          "timezone", "location", "utm_content", "use_personalized_template", "use_ai_personalization", "enable_utm_parameters", "merge_tags"]


def config_get(cfg, path):
    v = cfg
    for k in path.split("."):
        v = v[k]
    return v


def render(text, cfg, s, link):
    """Fill [[tokens]]. A FILL_ config value becomes a visible {{path}} merge field."""
    extra = {"date_words": s["date_words"], "range_words": s["range_words"], "registration_link": link}
    def sub(m):
        key = m.group(1)
        if key in extra:
            return extra[key]
        v = config_get(cfg, key)
        return "{{%s}}" % key if str(v).startswith("FILL_") else str(v)
    return re.sub(r"\[\[([a-z_.]+)\]\]", sub, text)


def reg_link(cfg, utm):
    domain = cfg["domains"]["funnel_domain"]
    host = "{{domains.funnel_domain}}" if domain.startswith("FILL_") else re.sub(r"^https?://", "", domain).rstrip("/")
    return (f"https://{host}{cfg['domains']['paths']['registration']}"
            f"?utm_source=calendar&utm_medium=invite&utm_campaign=enterprise-webinar&utm_content={utm}")


def rows(date_s):
    cfg = json.loads(CONFIG.read_text())
    s = session(date_s)
    out = []
    for i, v in enumerate(VARIANTS):
        link = reg_link(cfg, v["utm"])
        tags = sorted(set(re.findall(r"\{\{(\w+)\}\}", v["description"] + v["title"])) & TANTRA_TAGS)
        out.append({
            "variant": v["id"], "campaign_name": f"Enterprise webinar {s['date']}: calendar ({v['id']})",
            "list_split": f"half {i} of every sender's slice",
            "event_title": render(v["title"], cfg, s, link), "description": render(v["description"], cfg, s, link),
            "date": s["date"], "time": s["time"], "end_time": f"{s['end']:%H:%M}", "minutes": s["minutes"],
            "timezone": s["timezone"], "location": link, "utm_content": v["utm"],
            "use_personalized_template": v["personalized"], "use_ai_personalization": "off", "enable_utm_parameters": "off",
            "merge_tags": " ".join("{{%s}}" % t for t in tags) or "none",
        })
    return cfg, s, out


def unknown(r):
    """Config merge fields still unfilled (anything in {{ }} that is not a Tantra tag)."""
    found = re.findall(r"\{\{([\w.]+)\}\}", " ".join(str(x) for x in r.values()))
    return sorted({f for f in found if f not in TANTRA_TAGS})


def ics_text(s, r):
    def esc(t):
        return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    def fold(line):
        b, out = line.encode(), []
        while len(b) > 75:
            cut = 75 if not out else 74
            while (b[cut] & 0xC0) == 0x80:
                cut -= 1
            out.append(b[:cut].decode())
            b = b[cut:]
        out.append(b.decode())
        return "\r\n ".join(out)
    day = s["day"][:2].upper()
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Tantra//Enterprise webinar item 12//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "BEGIN:VTIMEZONE", "TZID:Europe/London",
        "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0000", "TZOFFSETTO:+0100", "TZNAME:BST", "DTSTART:19700329T010000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
        "BEGIN:STANDARD", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0000", "TZNAME:GMT", "DTSTART:19701025T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD", "END:VTIMEZONE",
        "BEGIN:VEVENT", "UID:enterprise-webinar-weekly@usetantra.com", "DTSTAMP:20261105T000000Z",
        f"DTSTART;TZID={s['timezone']}:{s['start']:%Y%m%dT%H%M%S}", f"DTEND;TZID={s['timezone']}:{s['end']:%Y%m%dT%H%M%S}",
        f"RRULE:FREQ=WEEKLY;BYDAY={day}",
        "SUMMARY:" + esc(r["event_title"]), "DESCRIPTION:" + esc(r["description"]), "LOCATION:" + esc(r["location"]),
        "STATUS:CONFIRMED", "TRANSP:OPAQUE", "END:VEVENT", "END:VCALENDAR",
    ]
    if s["timezone"] != "Europe/London":
        sys.exit("calendar-series-example.ics carries a Europe/London VTIMEZONE only; extend ics_text for " + s["timezone"])
    return "\r\n".join(fold(x) for x in lines) + "\r\n"


def write_source(date_s):
    cfg, s, out = rows(date_s)
    with open(HERE / "calendar-import.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(out)
    (HERE / "calendar-series-example.ics").write_text(ics_text(s, out[0]), newline="")
    md = ["# Cold Calendar Invites (generated by build.py: edit the copy there, then rerun)", "",
          f"Session: {s['when']}, {s['minutes']} minutes. Weekly, {s['weekly']}.", "",
          "`{{firstName}}` and `{{company}}` are Tantra merge tags, filled per guest at send. "
          "Any other `{{...}}` is a funnel-config value not set yet (`{{webinar.title}}`, `{{domains.funnel_domain}}`).", ""]
    for v, r in zip(VARIANTS, out):
        md += [f"## Variant {v['id']}: {v['name']}", "", "**Event title (as it shows in Google Calendar):**", "", "```text", r["event_title"], "```", "",
               f"{len(r['event_title'])} characters. Calendar grid preview (first 24): `{r['event_title'][:24]}`", "",
               f"**When:** {s['date_words']}, {s['range_words']}. Tantra fields: date {r['date']}, time {r['time']}, {r['minutes']} minutes, time zone {r['timezone']}", "",
               "**Event description:**", "", "```text", r["description"], "```", "",
               f"Merge tags: {r['merge_tags']}. Tantra step 4 switches: Use Personalized Template {r['use_personalized_template']}, Use AI personalization off, Enable UTM Parameters off (the link already carries `utm_content={v['utm']}`)", ""]
    (HERE / "invites.md").write_text("\n".join(md))
    print(f"wrote calendar-import.csv, calendar-series-example.ics and invites.md for {s['when']}")
    left = sorted({u for r in out for u in unknown(r)})
    if left:
        print("still unset in funnel-config.json (shown as merge fields): " + ", ".join(left))


def write_tantra(date_s):
    cfg, s, out = rows(date_s)
    missing = sorted({u for r in out for u in unknown(r)})
    if missing:
        sys.exit("not written, fill these in funnel-config.json first: " + ", ".join(missing))
    for r in out:
        r["description"] = r["description"].replace("\n", "<br>")
    with open(HERE / "calendar-tantra.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(out)
    print("wrote calendar-tantra.csv for " + s["when"])


if __name__ == "__main__":
    a = sys.argv
    date_s = None
    if "--date" in a:
        i = a.index("--date")
        if i + 1 >= len(a) or a[i + 1].startswith("--"):
            sys.exit("--date needs a value: --date YYYY-MM-DD")
        date_s = a[i + 1]
    try:
        (write_tantra if "--tantra" in a else write_source)(date_s)
    except ValueError as e:
        sys.exit(f"not written: {e}")
