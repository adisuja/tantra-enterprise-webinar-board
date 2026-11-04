#!/usr/bin/env python3
"""Item 11 cold email: one source for the copy.

python3 build.py            writes cold-email-sequences.md and cold-email-import.csv (merge fields kept)
python3 build.py --tantra   writes cold-email-tantra.csv: funnel-config values filled, Tantra tags swapped in.
                            Refuses while any FILL_ value it needs is still unset.
"""
import csv, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE.parent / "_shared" / "funnel-config.json"

FOOTER = 'Not for you? Reply "no" and you won\'t hear from me again.'

SEQUENCES = [
    {
        "id": "A", "name": "Outcome-led", "utm": "ce_a",
        "subjects": ["AI for the revenue side", "where next month's deals come from", "a weekly session for founders"],
        "steps": [
            (0, """Hi {{first_name}},

{{ai_first_line}}

Most founders use AI for content and stop there. The revenue side (who you reach, who books a call) still runs by hand.

Every {{webinar.day_of_week}} at {{webinar.start_time_local}} I take it apart live. My team has worked with 250+ brands.

Want a seat? {{registration_link}}

{{brand.host_name}}
{{brand.host_title}}"""),
            (3, """Hi {{first_name}},

One channel most founders skip: the calendar invite.

A UK coaching company my team worked with went from 30 registrations on its first webinar to 1,990 on its best. That week, 98,000 of the 99,859 people it reached got there by calendar invite.

In the session I show how that list was built and sent. {{registration_link}}

{{brand.host_name}}"""),
            (4, """Hi {{first_name}},

Last note from me. If a predictable pipeline isn't a priority this quarter, no problem.

If it is, the session runs live every {{webinar.day_of_week}}. Can't make the time? Register anyway and you'll get the recording. {{registration_link}}

{{brand.host_name}}"""),
        ],
    },
    {
        "id": "B", "name": "Problem-led", "utm": "ce_b",
        "subjects": ["if referrals slowed down next month", "who books your sales calls?", "the step where revenue leaks"],
        "steps": [
            (0, """Hi {{first_name}},

{{ai_first_line}}

Founder-led revenue usually rides on referrals and the founder selling. Good month, quiet month, and nobody knows which step broke.

The fix: measure every step and let AI run the repetitive work.

I show it live every {{webinar.day_of_week}}, {{webinar.start_time_local}}.

Save your seat: {{registration_link}}

{{brand.host_name}}
{{brand.host_title}}"""),
            (3, """Hi {{first_name}},

A London fintech network my team worked with sells a board-readiness programme. We ran its webinar on calendar invites, grew its outreach from 10,000 to 30,000 people across three sessions, and booked 17 sales calls along the way.

I'll walk through how it was set up, step by step. {{registration_link}}

{{brand.host_name}}"""),
            (4, """Hi {{first_name}},

I'll stop here. If revenue feels steady right now, that's a good sign.

If it ever stalls and you want to see exactly which step broke, the session runs every {{webinar.day_of_week}}: {{registration_link}}

{{brand.host_name}}"""),
        ],
    },
    {
        "id": "C", "name": "Built with you", "utm": "ce_c",
        "subjects": ["build it yourself, or with us", "your revenue system, built with you", "one hour, then decide"],
        "steps": [
            (0, """Hi {{first_name}},

{{ai_first_line}}

Most founders don't need another AI tool. They need the revenue system built with them and handed over working.

Every {{webinar.day_of_week}} at {{webinar.start_time_local}} I show that build live, and how we'd do it with you.

Grab a seat: {{registration_link}}

{{brand.host_name}}
{{brand.host_title}}"""),
            (3, """Hi {{first_name}},

Who the session suits best: founders who want the system built with them and are ready to invest in growth this year.

If that's you, you'll see exactly what gets built, in what order, and what each step should produce. {{registration_link}}

{{brand.host_name}}"""),
            (4, """Hi {{first_name}},

Last one from me. Whether you build it yourself or with us, the session gives you the full map in {{webinar.duration_minutes}} minutes.

It runs every {{webinar.day_of_week}}, and registrants get the recording. {{registration_link}}

{{brand.host_name}}"""),
        ],
    },
]

STEP_NAMES = {1: "Step 1 (day 0)", 2: "Follow-up 1 (3 days later, same thread)", 3: "Follow-up 2 (4 days later, same thread)"}


def rows():
    for s in SEQUENCES:
        for i, (delay, body) in enumerate(s["steps"], 1):
            yield s, i, delay, (s["subjects"][0] if i == 1 else ""), body + "\n\n" + FOOTER


def write_source():
    with open(HERE / "cold-email-import.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sequence", "step", "delay_days", "subject", "body"])
        for s, i, delay, subject, body in rows():
            w.writerow([s["id"], i, delay, subject, body])
    md = ["# Cold Email Sequences (generated by build.py: edit the copy there, then rerun)", "",
          "Sender: Adi. Plain text. Every step: one link, the opt-out line, the postal footer. Follow-ups go in the same thread (no subject).", ""]
    for s in SEQUENCES:
        md += [f"## Template {s['id']}: {s['name']}", "", "Subject lines (send the first; test the others as their own campaign):", ""]
        md += [f"{n}. {x}" for n, x in enumerate(s["subjects"], 1)] + [""]
        md += [f"Link tag: `utm_content={s['utm']}`", ""]
        for i, (delay, body) in enumerate(s["steps"], 1):
            md += [f"### {STEP_NAMES[i]}", "", "```text", body, "", FOOTER, "```", ""]
    (HERE / "cold-email-sequences.md").write_text("\n".join(md))
    print("wrote cold-email-import.csv and cold-email-sequences.md")


def write_tantra():
    cfg = json.loads(CONFIG.read_text())
    def get(path):
        v = cfg
        for k in path.split("."):
            v = v[k]
        return v
    domain = get("domains.funnel_domain")
    base = domain if domain.startswith("http") else "https://" + domain
    out = []
    for s, i, delay, subject, body in rows():
        link = f"{base.rstrip('/')}{get('domains.paths.registration')}?utm_source=email&utm_medium=cold&utm_campaign=enterprise-webinar&utm_content={s['utm']}"
        text = body.replace("{{registration_link}}", link)
        text = text.replace("{{first_name}}", "{{firstName}}").replace("{{ai_first_line}}", "{{custom.ai_first_line}}")
        text = re.sub(r"\{\{((?:webinar|brand)\.[a-z_]+)\}\}", lambda m: str(get(m.group(1))), text)
        out.append([s["id"], i, delay, subject, text])
    missing = sorted({m for r in out for m in re.findall(r"FILL_[A-Z_]+", r[4])})
    if missing:
        sys.exit("not written, fill these in funnel-config.json first: " + ", ".join(missing))
    with open(HERE / "cold-email-tantra.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sequence", "step", "delay_days", "subject", "body"])
        w.writerows(out)
    print("wrote cold-email-tantra.csv")


if __name__ == "__main__":
    write_tantra() if "--tantra" in sys.argv else write_source()
