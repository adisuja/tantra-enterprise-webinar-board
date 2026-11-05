#!/usr/bin/env python3
"""Item 11 cold email: one source for the copy.

python3 build.py [--date YYYY-MM-DD]
    writes cold-email-sequences.md and cold-email-import.csv for the session the thread points at
    (default webinar.first_date). Known funnel-config values are filled; a value still FILL_ stays a
    visible merge field ({{domains.funnel_domain}}).
python3 build.py --tantra [--date YYYY-MM-DD]
    writes cold-email-tantra.csv, the file to load. Refuses while any value it needs is FILL_.

Two kinds of field:
  [[token]]                  filled here at build time (funnel-config.json, ../12-calendar-invites/schedule.py)
  {{firstName}}, {{company}} Tantra merge tags, filled per contact at send
                             (https://usetantra.com/help/templates-and-ai/merge-tags-and-spintax)
No AI personalisation field (Adi 2026-11-05): merge tags only, every step a Predefined template.
"""
import csv, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE.parent / "_shared" / "funnel-config.json"
sys.path.insert(0, str(HERE.parent / "12-calendar-invites"))
from schedule import session  # noqa: E402

TANTRA_TAGS = {"firstName", "company"}
FOOTER = 'Not for you? Reply "no" and you won\'t hear from me again.'

SEQUENCES = [
    {
        "id": "A", "name": "Outcome-led", "utm": "ce_a",
        "subjects": ["AI for the revenue side", "where next month's deals come from", "a weekly session for founders"],
        "steps": [
            (0, """Hi {{firstName}},

A note for whoever owns next month's pipeline at {{company}}.

Most founders use AI for content and stop there. The revenue side (who you reach, who books a call) still runs by hand.

I take it apart live on [[date_short]] at [[time_words]], and every [[day]] after. My team has worked with 250+ brands.

Want a seat? [[registration_link]]

[[brand.host_name]]
[[brand.host_title]]"""),
            (3, """Hi {{firstName}},

One channel most founders skip: the calendar invite.

A UK coaching company my team worked with went from 30 registrations on its first webinar to 1,990 on its best. That week, 98,000 of the 99,859 people it reached got there by calendar invite.

In the session I show how that list was built and sent. [[registration_link]]

[[brand.host_name]]"""),
            (4, """Hi {{firstName}},

Last note from me. If a predictable pipeline isn't a priority this quarter, no problem.

If it is, the session runs live every [[day]] at [[time_words]]. Can't make the time? Register anyway and you'll get the recording. [[registration_link]]

[[brand.host_name]]"""),
        ],
    },
    {
        "id": "B", "name": "Problem-led", "utm": "ce_b",
        "subjects": ["if referrals slowed down next month", "who books your sales calls?", "the step where revenue leaks"],
        "steps": [
            (0, """Hi {{firstName}},

A note on how {{company}} fills its sales calendar.

Founder-led revenue usually rides on referrals and the founder selling. Good month, quiet month, and nobody knows which step broke.

The fix: measure every step and let AI run the repetitive work.

I show it live on [[date_short]], [[time_words]].

Save your seat: [[registration_link]]

[[brand.host_name]]
[[brand.host_title]]"""),
            (3, """Hi {{firstName}},

A London fintech network my team worked with sells a board-readiness programme. We ran its webinar on calendar invites, grew its outreach from 10,000 to 30,000 people across three sessions, and booked 17 sales calls along the way.

I'll walk through how it was set up, step by step. [[registration_link]]

[[brand.host_name]]"""),
            (4, """Hi {{firstName}},

I'll stop here. If revenue feels steady right now, that's a good sign.

If it ever stalls and you want to see exactly which step broke, the session runs every [[day]] at [[time_words]]: [[registration_link]]

[[brand.host_name]]"""),
        ],
    },
    {
        "id": "C", "name": "Built with you", "utm": "ce_c",
        "subjects": ["build it yourself, or with us", "your revenue system, built with you", "one hour, then decide"],
        "steps": [
            (0, """Hi {{firstName}},

This one is for whoever owns growth at {{company}}.

Most founders don't need another AI tool. They need the revenue system built with them and handed over working.

On [[date_short]] at [[time_words]] I show that build live, and how we'd do it with you.

Grab a seat: [[registration_link]]

[[brand.host_name]]
[[brand.host_title]]"""),
            (3, """Hi {{firstName}},

Who the session suits best: founders who want the system built with them and are ready to invest in growth this year.

If that's you, you'll see exactly what gets built, in what order, and what each step should produce. [[registration_link]]

[[brand.host_name]]"""),
            (4, """Hi {{firstName}},

Last one from me. Whether you build it yourself or with us, the session gives you the full map in [[webinar.duration_minutes]] minutes.

It runs every [[day]] at [[time_words]], and registrants get the recording. [[registration_link]]

[[brand.host_name]]"""),
        ],
    },
]

STEP_NAMES = {1: "Step 1 (day 0)", 2: "Follow-up 1 (3 days later, same thread)", 3: "Follow-up 2 (4 days later, same thread)"}
HEADER = ["sequence", "step", "delay_days", "subject", "body"]


def config_get(cfg, path):
    v = cfg
    for k in path.split("."):
        v = v[k]
    return v


def reg_link(cfg, utm):
    domain = cfg["domains"]["funnel_domain"]
    host = "{{domains.funnel_domain}}" if domain.startswith("FILL_") else re.sub(r"^https?://", "", domain).rstrip("/")
    return (f"https://{host}{cfg['domains']['paths']['registration']}"
            f"?utm_source=email&utm_medium=cold&utm_campaign=enterprise-webinar&utm_content={utm}")


def render(text, cfg, s, link):
    extra = {"date_short": s["date_short"], "time_words": s["time_words"], "day": s["day"], "registration_link": link}
    def sub(m):
        key = m.group(1)
        if key in extra:
            return extra[key]
        v = config_get(cfg, key)
        return "{{%s}}" % key if str(v).startswith("FILL_") else str(v)
    return re.sub(r"\[\[([a-z_.]+)\]\]", sub, text)


def rows(date_s):
    cfg = json.loads(CONFIG.read_text())
    s = session(date_s)
    out = []
    for q in SEQUENCES:
        link = reg_link(cfg, q["utm"])
        for i, (delay, body) in enumerate(q["steps"], 1):
            out.append((q, i, delay, q["subjects"][0] if i == 1 else "", render(body, cfg, s, link) + "\n\n" + FOOTER))
    return s, out


def unknown(text):
    return sorted({f for f in re.findall(r"\{\{([\w.]+)\}\}", text) if f not in TANTRA_TAGS})


def words(text, fallback=True):
    """Word count as the reader sees it, with the import fallbacks in place of the merge tags."""
    if fallback:
        text = text.replace("{{firstName}}", "there").replace("{{company}}", "your company")
    return len(re.sub(r"https?://\S+", "LINK", text).split())


def write_source(date_s):
    s, out = rows(date_s)
    with open(HERE / "cold-email-import.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for q, i, delay, subject, body in out:
            w.writerow([q["id"], i, delay, subject, body])
    md = ["# Cold Email Sequences (generated by build.py: edit the copy there, then rerun)", "",
          f"Sender: Adi. Plain text. Session these threads point at: {s['when']}, then weekly, {s['weekly']}.", "",
          "Every step: one link and the opt-out line, no postal address. Follow-ups go in the same thread (no subject). "
          "`{{firstName}}` and `{{company}}` are Tantra merge tags (import `there` and `your company` when unknown); "
          "`{{domains.funnel_domain}}` is the funnel domain, set at deploy.", ""]
    for q in SEQUENCES:
        md += [f"## Template {q['id']}: {q['name']}", "", "Subject lines (send the first; test the others as their own campaign):", ""]
        md += [f"{n}. {x}" for n, x in enumerate(q["subjects"], 1)] + [""]
        md += [f"Link tag: `utm_content={q['utm']}`", ""]
        for _, i, delay, subject, body in [r for r in out if r[0] is q]:
            md += [f"### {STEP_NAMES[i]} ({words(body)} words)", "", "```text", body, "```", ""]
    (HERE / "cold-email-sequences.md").write_text("\n".join(md))
    print(f"wrote cold-email-import.csv and cold-email-sequences.md for {s['when']}")
    counts = {f"{q['id']}{i}": words(b) for q, i, _, _, b in out}
    print("words (fallbacks in): " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    left = sorted({u for r in out for u in unknown(r[4])})
    if left:
        print("still unset in funnel-config.json (shown as merge fields): " + ", ".join(left))


def write_tantra(date_s):
    s, out = rows(date_s)
    missing = sorted({u for r in out for u in unknown(r[4])})
    if missing:
        sys.exit("not written, fill these in funnel-config.json first: " + ", ".join(missing))
    with open(HERE / "cold-email-tantra.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for q, i, delay, subject, body in out:
            w.writerow([q["id"], i, delay, subject, body])
    print("wrote cold-email-tantra.csv for " + s["when"])


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
