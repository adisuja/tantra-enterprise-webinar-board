#!/usr/bin/env python3
"""Independent check of the files slice_enterprise_lists.py wrote. Prints counts only, then PASS or FAIL.

usage: python -I verify_slices.py <master.csv> [--out ~/tantra-enterprise-lists]

Checks: exact header; email and first_name never blank; no email in two files; no em or en dash in any cell;
main slices hold up to 100,000 rows a week and 25,000 a pool; no cold file holds a declined, junk, role, warm,
personal, education/government or EU/UK-held row; warm files hold only past Yes/Maybe or registered no-shows;
at most 3 rows per recipient domain per week and 30 over the plan; at least 60 days since each row's last invite; MANIFEST row counts and hashes match.
"""
import argparse, collections, hashlib, json, pathlib, re, sys

import pandas as pd

SCHEMA = ["first_name", "last_name", "title", "company", "website", "email", "linkedin_url", "country"]
HOLD = {"at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr", "de", "gr", "hu", "ie", "it", "lv", "lt",
        "lu", "mt", "nl", "pl", "pt", "ro", "sk", "si", "es", "se", "is", "li", "no", "uk", "ch", "eu"}
NOT_ICP = re.compile(r"\.(?:edu|gov|mil|int)$|\.(?:edu|gov|mil|ac|k12|sch|nhs|police|gouv|govt|gob|go)\.[a-z]{2}$")

ap = argparse.ArgumentParser()
ap.add_argument("master")
ap.add_argument("--out", default=str(pathlib.Path.home() / "tantra-enterprise-lists"))
a = ap.parse_args()
out = pathlib.Path(a.out).expanduser()
fails = []

m = pd.read_csv(a.master, dtype=str, keep_default_na=False, encoding="utf-8-sig",
                usecols=["email", "domain", "email_type", "declined_series", "accepted_yes_maybe_series",
                         "registered_no_show_series", "last_invited_date"]).set_index("email")
starts = {k: pd.Timestamp(v) for k, v in json.loads((pathlib.Path(__file__).resolve().parent / "slice-stats.json")
                                                   .read_text())["reinvite_gap"]["week_starts"].items()}
GAP = pd.Timedelta(days=60)
manifest = json.loads((out / "MANIFEST.json").read_text())
seen = {}
rows_by_kind = collections.Counter()
dom_week = collections.Counter()
dom_total = collections.Counter()
for f in sorted(out.rglob("*.csv")):
    rel = str(f.relative_to(out))
    raw = f.read_bytes()
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
        fails.append(f"{rel}: email not in master")
    kind = f.parent.name
    if kind in ("ramp", "warm") and (rel.endswith("_warm.csv") or kind == "warm"):
        kind = "warm"
    rows_by_kind[kind] += len(df)
    warm_flag = (src["accepted_yes_maybe_series"] != "") | (src["registered_no_show_series"] != "")
    if (src["declined_series"] != "").any() or src["email_type"].isin(["junk", "role"]).any():
        fails.append(f"{rel}: holds a declined, junk or role row")
    if src["domain"].str.contains(NOT_ICP).any():
        fails.append(f"{rel}: holds an education, government or military domain")
    tld = src["domain"].str.rsplit(".", n=1).str[-1]
    if kind in ("main", "ramp", "warm") and rel.split("/")[-1][:3] in starts:
        last = pd.to_datetime(src["last_invited_date"].str[:10], errors="coerce")
        if (last + GAP > starts[rel.split("/")[-1][:3]]).any():
            fails.append(f"{rel}: a row last invited less than 60 days before its week starts")
    if kind == "hold":
        if not tld.isin(HOLD).all():
            fails.append(f"{rel}: hold file has a non-held domain")
        continue
    if tld.isin(HOLD).any():
        fails.append(f"{rel}: holds an EU, EEA, UK or Swiss domain")
    if kind == "warm":
        if not warm_flag.all():
            fails.append(f"{rel}: warm file has a row with no past Yes/Maybe or no-show")
        continue
    if warm_flag.any() or (src["email_type"] == "personal").any():
        fails.append(f"{rel}: cold file has a warm or personal row")
    if kind in ("main", "ramp"):
        week = rel.split("/")[1][:3]
        if kind == "main" and len(df) > 25_000:
            fails.append(f"{rel}: more than 25,000 rows in one pool")
        for d, n in src["domain"].value_counts().items():
            dom_week[(d, week)] += n; dom_total[d] += n

main_weeks = collections.Counter(r.split("/")[1][:3] for r in manifest if r.startswith("main/"))
main_rows = collections.Counter()
for r, v in manifest.items():
    if r.startswith("main/"):
        main_rows[r.split("/")[1][:3]] += v["rows"]
if any(n > 100_000 for n in main_rows.values()):
    fails.append("a main week holds more than 100,000 rows")
if dom_week and max(dom_week.values()) > 3:
    fails.append(f"a recipient domain has {max(dom_week.values())} rows in one week")
if dom_total and max(dom_total.values()) > 30:
    fails.append(f"a recipient domain has {max(dom_total.values())} rows over the plan")

print(json.dumps({"files": len(manifest), "unique_emails": len(seen), "rows_by_kind": dict(rows_by_kind),
                  "main_rows_by_week": dict(sorted(main_rows.items())),
                  "max_rows_one_domain_one_week": max(dom_week.values()) if dom_week else 0,
                  "max_rows_one_domain_plan": max(dom_total.values()) if dom_total else 0}, indent=1))
for x in fails[:20]:
    print("FAIL", x)
print("PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
