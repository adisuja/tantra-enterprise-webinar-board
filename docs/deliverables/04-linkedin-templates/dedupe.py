#!/usr/bin/env python3
"""Give every prospect exactly one sender (owner_profile), keyed on LinkedIn URL, so no prospect hears from two profiles.

usage:
  python3 deliverables/04-linkedin-templates/dedupe.py OUT.csv IN.csv [IN.csv ...] [--suppress FILE.csv ...]

IN files (kept OUTSIDE the repo) need a `linkedin_url` column. Optional columns, used when present:
  title             job title, for the title rule
  connected_to      profile keys already connected to this person, separated by ; (for example "adi;bhaskar")
  last_messaged_by  the profile key that messaged them most recently
  engaged_profile   the profile key whose post they liked or commented on
  engaged_at        date of that engagement, YYYY-MM-DD (earliest wins)
--suppress files: anyone whose linkedin_url appears there (registrants, repliers, do-not-contact, people in an
active campaign) is dropped.

Rules (OVERVIEW.md, Audience Splits), first that applies wins:
  1. Already connected to a sender: messenger, owned by the sender who messaged them last; otherwise the
     title-rule sender if connected; otherwise the first connected sender in title-rule order.
  2. Engaged with a sender's post: content_engagement, owned by the sender of the earliest engagement.
  3. Everyone else: connector (or InMail, picked by hand), owned by the title rule.
OUT gets every input column plus owner_profile, campaign and rule. Prints counts only, never names or URLs.
"""
import csv, re, sys, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
ORDER = ["bharath", "bhaskar", "aquila", "nelbin", "ben", "adi"]
TITLE_RULES = [
    ("bharath", r"\bcto\b|chief technology|engineering|technical co-?founder"),
    ("bhaskar", r"\bcmo\b|chief marketing|marketing|growth|demand gen"),
    ("aquila", r"revops|revenue operations|marketing ops|sales ops|automation"),
    ("nelbin", r"\bcoo\b|chief operating|operations|chief of staff|general manager"),
    ("ben", r"digital|\bweb\b|product|agency"),
]

def norm_url(u):
    u = (u or "").strip().lower()
    m = re.search(r"linkedin\.com/(in|pub)/([^/?#\s]+)", u)
    return f"linkedin.com/in/{m.group(2)}" if m else ""

def by_title(title):
    t = (title or "").lower()
    for key, pat in TITLE_RULES:
        if re.search(pat, t):
            return key
    return "adi"

def keys(v):
    return [k for k in (x.strip().lower() for x in (v or "").split(";")) if k in ORDER]

def main(argv):
    if len(argv) < 2 or argv[0].startswith("-"):
        sys.exit(__doc__)
    out = pathlib.Path(argv[0]).resolve()
    if REPO in out.parents:
        sys.exit("Refusing to write prospect data inside the repo. Write OUT outside it (AGENT_RULES rule 5).")
    ins, sup, mode = [], [], None
    for a in argv[1:]:
        if a == "--suppress":
            mode = "sup"; continue
        (sup if mode == "sup" else ins).append(a)

    suppressed = set()
    for f in sup:
        with open(f, newline="", encoding="utf-8-sig") as fh:
            suppressed |= {norm_url(r.get("linkedin_url")) for r in csv.DictReader(fh)}

    people, cols, stats = {}, [], {"rows": 0, "no_url": 0, "duplicates_merged": 0, "suppressed": 0}
    for f in ins:
        with open(f, newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            cols += [c for c in rd.fieldnames if c not in cols]
            for r in rd:
                stats["rows"] += 1
                u = norm_url(r.get("linkedin_url"))
                if not u:
                    stats["no_url"] += 1; continue
                if u in suppressed:
                    stats["suppressed"] += 1; continue
                if u not in people:
                    people[u] = dict(r, _conn=set(keys(r.get("connected_to"))), _eng=[])
                else:
                    stats["duplicates_merged"] += 1
                    p = people[u]
                    p["_conn"] |= set(keys(r.get("connected_to")))
                    for c, v in r.items():
                        if v and not p.get(c):
                            p[c] = v
                ep = keys(r.get("engaged_profile"))
                if ep:
                    people[u]["_eng"].append(((r.get("engaged_at") or "9999-99-99").strip(), ep[0]))

    owners = {k: 0 for k in ORDER}
    for u, p in people.items():
        title_owner = by_title(p.get("title"))
        last = keys(p.get("last_messaged_by"))
        if p["_conn"]:
            if last and last[0] in p["_conn"]:
                owner, rule = last[0], "1 connected, last messaged"
            elif title_owner in p["_conn"]:
                owner, rule = title_owner, "1 connected, title"
            else:
                owner, rule = next(k for k in ORDER if k in p["_conn"]), "1 connected, order"
            campaign = "messenger"
        elif p["_eng"]:
            owner, rule, campaign = sorted(p["_eng"])[0][1], "2 earliest engagement", "content_engagement"
        else:
            owner, rule, campaign = title_owner, "3 title", "connector"
        p.update(owner_profile=owner, campaign=campaign, rule=rule)
        owners[owner] += 1

    out_cols = cols + [c for c in ("owner_profile", "campaign", "rule") if c not in cols]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(people.values())
    print(f"rows read {stats['rows']}, unique prospects {len(people)}, duplicates merged {stats['duplicates_merged']}, "
          f"no LinkedIn URL {stats['no_url']}, suppressed {stats['suppressed']}")
    print("owners: " + ", ".join(f"{k} {v}" for k, v in owners.items()))

if __name__ == "__main__":
    main(sys.argv[1:])
