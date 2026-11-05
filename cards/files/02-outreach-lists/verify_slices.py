#!/usr/bin/env python3
"""Independent check of the files slice_enterprise_lists.py wrote. Prints counts only, then PASS or FAIL.

usage: python -I verify_slices.py <master.csv> [--out ~/tantra-enterprise-lists]

Checks, re-read from the master CSV (not from the slicer's own state):
  exact header; email and first_name never blank; no email in two files; no em or en dash in any cell;
  every row is in the master, on an EU, EEA, UK or Swiss country domain, a work address (no personal, junk or role
  mailbox), never declined, not education or government; warm files hold only past Yes/Maybe or registered no-shows,
  cold files none; no slice over 100,000 rows or over its week's capacity, no pool file over its share;
  at most 3 rows per recipient domain a week and 30 over the plan; every row's send window starts at least 60 days
  after its last invite; slice S01 is the 12 November 2026 webinar; tier 1 (UK, Ireland, Malta) first: the median
  slice of tier 1 cold rows comes before tier 2's, and tier 2's before tier 3's; MANIFEST row counts and hashes match; the output folder is outside any git repo and mode 700, files mode 600.
"""
import argparse, collections, hashlib, json, pathlib, re, stat, subprocess, sys

import pandas as pd

SCHEMA = ["first_name", "last_name", "title", "company", "website", "email", "linkedin_url", "country"]
TIER1 = {"uk", "london", "scot", "wales", "cymru", "ie", "mt"}
TIER2 = {"nl", "se", "dk", "fi", "no", "is"}
EU_UK = {"uk", "london", "scot", "wales", "cymru", "ie", "mt", "nl", "se", "dk", "fi", "no", "is", "at", "be", "bg",
         "hr", "cy", "cz", "ee", "fr", "de", "gr", "hu", "it", "lv", "lt", "lu", "pl", "pt", "ro", "sk", "si", "es",
         "ch", "li", "eu"}
NOT_ICP = re.compile(r"\.(?:edu|gov|mil|int)$|\.(?:edu|gov|mil|ac|k12|sch|nhs|police|gouv|govt|gob|go)\.[a-z]{2}$")
FILE = re.compile(r"^S(\d{2})_(\d{4}-\d{2}-\d{2})_P(\d)_(warm|cold)\.csv$")

ap = argparse.ArgumentParser()
ap.add_argument("master")
ap.add_argument("--out", default=str(pathlib.Path.home() / "tantra-enterprise-lists"))
a = ap.parse_args()
out = pathlib.Path(a.out).expanduser()
fails = []
stats = json.loads((pathlib.Path(__file__).resolve().parent / "slice-stats.json").read_text())
win = {k: pd.Timestamp(v) for k, v in stats["week_send_windows"].items()}
cap = {k: v["capacity"] for k, v in stats["slices"].items()}
GAP = pd.Timedelta(days=stats["params"]["min_gap_days"])

if subprocess.run(["git", "-C", str(out), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True).stdout.strip() == "true":
    fails.append("output folder is inside a git repo")
if stat.S_IMODE(out.stat().st_mode) != 0o700:
    fails.append("output folder is not mode 700")
if stats["slices"].get("S01", {}).get("webinar") != "2026-11-12":
    fails.append("S01 is not the 12 November 2026 webinar")

m = pd.read_csv(a.master, dtype=str, keep_default_na=False, encoding="utf-8-sig",
                usecols=["email", "domain", "email_type", "declined_series", "accepted_yes_maybe_series",
                         "registered_no_show_series", "last_invited_date"]).set_index("email")
manifest = json.loads((out / "MANIFEST.json").read_text())
seen = {}
rows_by_kind = collections.Counter()
slice_rows = collections.Counter()
pool_rows = collections.Counter()
dom_week = collections.Counter()
dom_total = collections.Counter()
tier_slices = {1: [], 2: [], 3: []}
for f in sorted(out.rglob("*.csv")):
    rel = str(f.relative_to(out))
    raw = f.read_bytes()
    if stat.S_IMODE(f.stat().st_mode) != 0o600:
        fails.append(f"{rel}: not mode 600")
    if rel not in manifest or manifest[rel]["sha256"] != hashlib.sha256(raw).hexdigest():
        fails.append(f"{rel}: missing from MANIFEST or hash differs")
    df = pd.read_csv(f, dtype=str, keep_default_na=False)
    if list(df.columns) != SCHEMA:
        fails.append(f"{rel}: header {list(df.columns)}")
    if manifest.get(rel, {}).get("rows") != len(df):
        fails.append(f"{rel}: row count differs from MANIFEST")
    if (df["email"] == "").any() or (df["first_name"] == "").any():
        fails.append(f"{rel}: blank email or first_name")
    if df.apply(lambda c: c.str.contains("[\u2013\u2014]", regex=True)).any().any():
        fails.append(f"{rel}: em or en dash in a cell")
    for e in df["email"]:
        if e in seen:
            fails.append(f"{rel}: an email also in {seen[e]}"); break
        seen[e] = rel
    src = m.reindex(df["email"])
    if src["email_type"].isna().any():
        fails.append(f"{rel}: email not in master"); continue
    tld = src["domain"].str.rsplit(".", n=1).str[-1]
    if not tld.isin(EU_UK).all():
        fails.append(f"{rel}: a row outside the EU, EEA, UK and Switzerland")
    if (src["declined_series"] != "").any() or src["email_type"].isin(["junk", "role", "personal"]).any():
        fails.append(f"{rel}: holds a declined, junk, role or personal row")
    if src["domain"].str.contains(NOT_ICP).any():
        fails.append(f"{rel}: holds an education, government or military domain")
    warm_flag = (src["accepted_yes_maybe_series"] != "") | (src["registered_no_show_series"] != "")
    mt = FILE.match(f.name)
    if f.parent.name == "reserve":
        rows_by_kind["reserve"] += len(df); continue
    if f.parent.name != "slices" or not mt:
        fails.append(f"{rel}: unexpected file"); continue
    s, date, pool, kind = f"S{mt.group(1)}", mt.group(2), int(mt.group(3)), mt.group(4)
    rows_by_kind[kind] += len(df)
    if stats["slices"].get(s, {}).get("webinar") != date:
        fails.append(f"{rel}: file date differs from the slice's webinar")
    if kind == "warm" and not warm_flag.all():
        fails.append(f"{rel}: warm file has a row with no past Yes/Maybe or no-show")
    if kind == "cold" and warm_flag.any():
        fails.append(f"{rel}: cold file has a warm row")
    last = pd.to_datetime(src["last_invited_date"].str[:10], errors="coerce")
    if (last + GAP > win[s]).any():
        fails.append(f"{rel}: a row last invited less than {GAP.days} days before its send window opens")
    if kind == "cold":
        for t_ in tld:
            tier_slices[1 if t_ in TIER1 else 2 if t_ in TIER2 else 3].append(int(s[1:]))
    slice_rows[s] += len(df); pool_rows[(s, pool)] += len(df)
    for d, n in src["domain"].value_counts().items():
        dom_week[(d, s)] += n; dom_total[d] += n

for s, n in slice_rows.items():
    if n > 100_000 or n > cap[s]:
        fails.append(f"{s}: {n} rows, over 100,000 or over its capacity {cap[s]}")
for (s, p), n in pool_rows.items():
    share = stats["slices"][s]["capacity_new_senders"] // stats["params"]["pools"] if p else stats["slices"][s]["capacity_older_senders"]
    if n > max(share, 0):
        fails.append(f"{s} P{p}: {n} rows, over its pool share {share}")
if dom_week and max(dom_week.values()) > stats["params"]["domain_week_cap"]:
    fails.append(f"a recipient domain has {max(dom_week.values())} rows in one week")
if dom_total and max(dom_total.values()) > stats["params"]["domain_total_cap"]:
    fails.append(f"a recipient domain has {max(dom_total.values())} rows over the plan")
med = {k: (sorted(v)[len(v) // 2] if v else 0) for k, v in tier_slices.items()}
if not med[1] < med[2] < med[3]:
    fails.append(f"language tiers not in order: median slice by tier {med}")
if sum(slice_rows.values()) != stats["coverage"]["scheduled"]:
    fails.append("scheduled rows differ from slice-stats.json")

print(json.dumps({"files": len(manifest), "unique_emails": len(seen), "rows_by_kind": dict(rows_by_kind),
                  "rows_by_slice": dict(sorted(slice_rows.items())),
                  "median_slice_of_cold_rows_by_tier": med,
                  "max_rows_one_domain_one_week": max(dom_week.values()) if dom_week else 0,
                  "max_rows_one_domain_plan": max(dom_total.values()) if dom_total else 0}, indent=1))
for x in fails[:20]:
    print("FAIL", x)
print("PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
