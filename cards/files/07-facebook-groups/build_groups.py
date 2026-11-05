#!/usr/bin/env python3
"""Builds GROUPS.md and groups.csv for item 7 from groups-data.json (read from each group's About page through
Agent Reach / OpenCLI in Adi's own Chrome, 2026-11-05) and the judgements in classify.py.
Personal (non-business) groups are never written here: they live in private/ only."""
import csv, json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from classify import C, PERM, OFFTOPIC, PENDING_NOTE
D = {g["slug"]: g for g in json.loads((HERE / "groups-data.json").read_text())}
ORDER = ["Own communities", "Startups and founders (Europe and UK)", "Outreach software and lead generation",
         "LinkedIn sales and marketing", "B2B growth and GTM", "Growth hacking and marketing", "SaaS founders and marketing",
         "Coaching and consulting", "Agencies and service businesses", "AI automation and agencies", "Sales and high-ticket closing",
         "Webinars and funnels", "Software deals and tools", "Startups and founders (global)", "Startups and founders (US and other regions)"]
def n(x): return f"{x:,}" if isinstance(x, int) else "?"
def act(g): return "; ".join(x for x in (g.get("posts_today"), g.get("posts_month")) if x) or "not shown"
rows = []
for slug, (cat, pri, perm, about, aud, topics, idea) in C.items():
    g = D[slug]
    rows.append(dict(category=cat, priority=pri, name=g["name"], url=g["url"], members=g.get("members"), privacy=g.get("privacy"),
                     visibility=g.get("visible"), member_location=aud, group_location=g.get("location") or "not set",
                     facebook_tags=", ".join(g.get("tags") or []) or "none set", topics=topics, about=about, activity=act(g),
                     new_members_week=g.get("new_members_week", ""), created=g.get("created", ""), last_visit=g.get("meta", ""),
                     can_post=PERM[perm], rules=" | ".join(g.get("rules") or []) or "no written rules", idea=idea))
rows.sort(key=lambda r: (ORDER.index(r["category"]), r["priority"], -(r["members"] or 0)))
pa = {p: sum(r["priority"] == p for r in rows) for p in "ABC"}
L = ["# Facebook Groups: Every Group, Categorised, With a Post Idea Each", "",
     f"Read on 2026-11-05 from Adi's own Facebook (Groups you've joined, then each group's About page), through the Agent Reach OpenCLI route in his signed-in Chrome, read only. Adi is in 113 groups and has 4 join requests pending. {len(rows)} are business groups that fit this webinar; the other {len(OFFTOPIC)} business groups are listed at the end as off-topic; personal groups (housing, household help, gaming, fitness and similar) are counted only and kept off this public board.", "",
     "**How to read it.** Priority A: post first (fit, size and activity). B: post in week 2 or 3. C: low reach (quiet or tiny group) or a weak fit. \"Can we post ourselves\" comes from each group's own written rules. Most groups ban promotion and links, so the idea there is a teaching post with no link: readers who want more open Adi's profile, which the profile branding (card 29) points at the registration page.", "",
     "**Member location.** Facebook shows where a group is based (the location the admins set) but never where its members are; the member location column is that setting plus what the group's name, description and rules say.", "",
     f"**Ideas only (Adi 2026-11-05).** Each row carries one pitched idea for Adi to approve. The posts themselves are written later in the content studio project. Priority A: {pa['A']} groups, B: {pa['B']}, C: {pa['C']}.", ""]
for cat in ORDER:
    rs = [r for r in rows if r["category"] == cat]
    if not rs: continue
    L += [f"## {cat} ({len(rs)})", ""]
    for r in rs:
        L += [f"### {r['priority']} · [{r['name']}]({r['url']})", "",
              f"- **About:** {r['about']}",
              f"- **Members:** {n(r['members'])} · {r['privacy']} group, {r['visibility'].lower()} in search · created {r['created'] or 'unknown'}",
              f"- **Where the members are:** {r['member_location']}" + (f" (group location setting: {r['group_location']})" if r['group_location'] != 'not set' and r['group_location'].split(',')[0] not in r['member_location'] else ""),
              f"- **Facebook tags:** {r['facebook_tags']} · **Topics:** {r['topics']}",
              f"- **Activity:** {r['activity']}; {r['new_members_week'] or 'new members not shown'}",
              f"- **Can we post ourselves?** {r['can_post']}",
              f"- **Rules (the admins' own words, shortened):** {r['rules'][:600]}",
              f"- **Pitched idea:** {r['idea']}", ""]
L += ["## Pending Join Requests (4)", "", PENDING_NOTE, "",
      f"## Business Groups That Don't Fit This Webinar ({len(OFFTOPIC)})", "",
      "| Group | Members | Why not |", "| --- | --- | --- |"]
for slug, why in OFFTOPIC.items():
    g = D[slug]; L.append(f"| [{g['name']}]({g['url']}) | {n(g.get('members'))} | {why} |")
L += ["", "## Personal Groups", "", "Adi's personal groups (Bangalore housing and household help, gaming, fitness, diet, a residential community and similar) are not business channels for this webinar. They are counted here and listed by name only in the private repo folder, never on this public board.", ""]
(HERE / "GROUPS.md").write_text("\n".join(L) + "\n")
with open(HERE / "groups.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
tr = ["group_name","group_url","priority","can_post","posted_date","post_url","comments","registrations","notes"]
with open(HERE / "group-tracker.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(tr)
    for r in rows:
        if not r["idea"].startswith(("Skip", "Not eligible")): w.writerow([r["name"], r["url"], r["priority"], r["can_post"], "", "", "", "", ""])
print(f"{len(rows)} business groups (A {pa['A']}, B {pa['B']}, C {pa['C']}), {len(OFFTOPIC)} off-topic")
