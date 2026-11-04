#!/usr/bin/env python3
"""Cut the Enterprise cold calendar lists from the consolidated Added to Calendar CSV.

usage:
  python -I slice_enterprise_lists.py <master.csv> [--out ~/tantra-enterprise-lists] [--stats <dir in repo>]
         [--weeks 10] [--week-size 100000] [--pools 4] [--domain-week-cap 3] [--domain-total-cap 30]
         [--ramp 22000,22000,22000,17600,17600,22000,55000,55000,55000,55000] [--ramp-start-week 4]
         [--day0 2026-11-09] [--min-gap-days 60]

What it does (rules in ICP_AND_SEGMENTS.md):
  1. Reads the master CSV in chunks (only the columns it needs).
  2. Drops junk and role mailboxes, and every row with declined_series filled.
  3. Excludes education, government and military domains (not Enterprise buyers).
  4. Holds rows on EU, EEA, UK and Swiss country domains in a review file until the outreach rules are checked.
  5. Moves past Yes/Maybe responders and registered no-shows to the warm list (they know this kind of webinar).
  6. Drops personal mailboxes from the cold list (kept on the warm list).
  7. Ranks the cold rows: tier A, B, C, then name confidence, then the oldest past invite first.
     Every row was invited by other senders between 2026-07-22 and 2026-10-19, so no row goes into a week that
     starts less than min-gap-days after its last_invited_date (week dates from --day0 and --ramp-start-week).
  8. Fills 10 main weeks (S01 to S10) of up to week-size rows, split into sender pools by recipient domain,
     at most domain-week-cap rows per recipient domain a week and domain-total-cap over the whole plan.
  9. Fills the ramp weeks (R01 to R10, the warm-up weeks before full volume): warm list first, then the next
     ranked cold rows. Whatever is left is the reserve for after S10.
 10. Writes Tantra-ready CSVs outside the repo and count-only stats into the repo.

Output CSV header (context/from-workshop-project/02-lists/lists.md section 4, read by kits/tantra/leads.mjs):
  first_name,last_name,title,company,website,email,linkedin_url,country
first_name is never blank: rows with no known first name keep the master's "there" (leads.mjs drops a row
with a blank first name, and calendar invites carry no merge fields, so the value is never shown in an invite).
"""
import argparse, collections, hashlib, json, os, pathlib, re, subprocess, sys, time

import pandas as pd

SCHEMA = ["first_name", "last_name", "title", "company", "website", "email", "linkedin_url", "country"]
NEED = ["email", "first_name", "last_name", "name_confidence", "company", "domain", "email_type", "job_title",
        "location", "linkedin_url", "series_invited", "bucket", "accepted_yes_maybe_series", "declined_series",
        "registered_no_show_series", "last_invited_date"]

# Tier A: segments that match the Enterprise buyer (B2B software, financial services, consulting, staffing,
# agencies). Tier C: weak fit for a $10,000 done-with-you build. Everything else (General, unknown) is tier B.
TIER_A_BUCKET = re.compile(r"b2b|saas|software|fintech|banking|financ|wealth|venture|insurance|accounting|consult|"
                           r"management|strategy|staffing|executive search|crm|cyber|media|digital publishing")
TIER_C_BUCKET = re.compile(r"education|vocational|government|non-profit|advocacy|agriculture|field services|retail|"
                           r"hospitality|career coaching")
TIER_A_TLD = {"io", "ai", "co", "tech", "agency", "vc", "app", "studio", "dev", "software", "solutions", "consulting",
              "digital", "marketing", "media", "partners", "capital", "ventures", "cloud", "systems", "bank",
              "finance", "fund", "biz", "saas"}
NOT_ICP = re.compile(r"\.(?:edu|gov|mil|int)$|\.(?:edu|gov|mil|ac|k12|sch|nhs|police|gouv|govt|gob|go)\.[a-z]{2}$")
GDPR_HOLD = {"at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr", "de", "gr", "hu", "ie", "it", "lv", "lt",
             "lu", "mt", "nl", "pl", "pt", "ro", "sk", "si", "es", "se", "is", "li", "no", "uk", "ch", "eu"}
NAME_RANK = {"high": 0, "medium": 1, "none": 2}
DASHES = re.compile("[\u2013\u2014]")


def tier_of(bucket: str, tld: str) -> str:
    parts = [p.strip().lower() for p in bucket.split(";") if p.strip()]
    if parts:
        if any(TIER_A_BUCKET.search(p) for p in parts):
            return "A"
        if all(TIER_C_BUCKET.search(p) for p in parts):
            return "C"
        return "B"
    if tld in TIER_A_TLD:
        return "A"
    if tld == "org":
        return "C"
    return "B"


def series_rank(s: str) -> int:
    m = re.search(r"E(\d+)", s or "")
    return int(m.group(1)) - 149 if m else 0  # never invited first, then E150 (oldest) to E162 (newest)


def stable_hash(s: str) -> int:
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:8], "big")


def inside_git_repo(path: pathlib.Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        return r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def load(master: str):
    funnel = collections.Counter()
    keep = []
    for ch in pd.read_csv(master, usecols=NEED, dtype=str, keep_default_na=False, chunksize=250_000,
                          encoding="utf-8-sig"):
        funnel["read"] += len(ch)
        ch["email"] = ch["email"].str.strip().str.lower()
        ok = ch["email"].str.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")
        funnel["dropped_invalid_email"] += int((~ok).sum()); ch = ch[ok]
        jr = ch["email_type"].isin(["junk", "role"])
        funnel["dropped_junk"] += int((ch["email_type"] == "junk").sum())
        funnel["dropped_role"] += int((ch["email_type"] == "role").sum()); ch = ch[~jr]
        dec = ch["declined_series"] != ""
        funnel["dropped_declined"] += int(dec.sum()); ch = ch[~dec]
        dom = ch["domain"].where(ch["domain"] != "", ch["email"].str.split("@").str[1]).str.lower()
        ch = ch.assign(domain=dom, tld=dom.str.rsplit(".", n=1).str[-1])
        noticp = ch["domain"].str.contains(NOT_ICP)
        funnel["excluded_edu_gov_mil"] += int(noticp.sum()); ch = ch[~noticp]
        ch = ch.assign(warm=(ch["accepted_yes_maybe_series"] != "") | (ch["registered_no_show_series"] != ""),
                       hold=ch["tld"].isin(GDPR_HOLD))
        keep.append(ch)
    df = pd.concat(keep, ignore_index=True)
    before = len(df)
    df = df.drop_duplicates("email")
    funnel["dropped_duplicate_email"] = before - len(df)
    return df, funnel


def to_schema(df: pd.DataFrame) -> pd.DataFrame:
    personal = df["email_type"] == "personal"
    out = pd.DataFrame({
        "first_name": df["first_name"].where(df["first_name"] != "", "there"),
        "last_name": df["last_name"],
        "title": df["job_title"],
        "company": df["company"],
        "website": df["domain"].where(~personal, ""),
        "email": df["email"],
        "linkedin_url": df["linkedin_url"],
        "country": df["location"],
    })
    return out.apply(lambda c: c.str.replace(DASHES, "-", regex=True))


def write(df: pd.DataFrame, path: pathlib.Path, manifest: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    to_schema(df).to_csv(path, index=False, columns=SCHEMA)
    os.chmod(path, 0o600)
    manifest[str(path.relative_to(manifest["_root"]))] = {
        "rows": len(df), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def describe(df: pd.DataFrame) -> dict:
    """Count-only profile of a set of rows: no email, name or recipient domain leaves this function."""
    vc = df["domain"].value_counts()
    return {
        "rows": int(len(df)),
        "tier": {k: int(v) for k, v in df["tier"].value_counts().sort_index().items()} if "tier" in df else {},
        "name_confidence": {k: int(v) for k, v in df["name_confidence"].value_counts().items()},
        "email_type": {k: int(v) for k, v in df["email_type"].value_counts().items()},
        "has_segment_bucket": int((df["bucket"] != "").sum()),
        "distinct_recipient_domains": int(len(vc)),
        "max_rows_one_domain": int(vc.max()) if len(vc) else 0,
        "last_invited_series": {("never" if k == "" else k): int(v)
                                for k, v in df["series_invited"].value_counts().sort_index().items()},
    }


def stats_md(s: dict) -> str:
    """SLICE_STATS.md from the stats dict: counts only."""
    f = s["funnel"]; n = lambda x: f"{x:,}"
    L = ["# Slice stats (count only, written by slice_enterprise_lists.py)", "",
         "No email, name or recipient domain appears here. The files themselves are in `~/tantra-enterprise-lists/`.", "",
         "## From master to usable", "", "| Step | Rows |", "| --- | --- |",
         f"| Read from the master CSV | {n(f['read'])} |",
         f"| Dropped: junk mailbox | {n(f['dropped_junk'])} |",
         f"| Dropped: role mailbox (info@, sales@ ...) | {n(f['dropped_role'])} |",
         f"| Dropped: declined a past invite (any `declined_series`) | {n(f['dropped_declined'])} |",
         f"| Excluded: education, government or military domain | {n(f['excluded_edu_gov_mil'])} |",
         f"| Warm (past Yes/Maybe or registered no-show, never declined) | {n(f['warm_total'])} |",
         f"| of which held for the EU/UK review | {n(f['warm_held_gdpr_review'])} |",
         f"| of which on the warm list | {n(f['warm_list'])} |",
         f"| Cold held for the EU/UK review (country domains) | {n(f['cold_held_gdpr_review'])} |",
         f"| Cold dropped: personal mailbox | {n(f['cold_personal_mailbox_dropped'])} |",
         f"| **Cold usable** | **{n(f['cold_usable'])}** |", "",
         "Cold usable by tier: " + ", ".join(f"{k} {n(v)}" for k, v in s["cold_usable_by_tier"].items()) + ".", "",
         f"Main list: **{n(s['main_total'])}** rows in 10 weekly slices. Gap to 1,000,000: **{n(s['gap_to_main_target'])}**.", "",
         "## Main slices (S01 to S10, 25,000 rows per sender pool)", "",
         "| Slice | Starts | Rows | Tier A | Tier B | Tier C | Name high | Name medium | Name none | Has segment | Recipient domains | Max rows one domain |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, v in s["main_slices"].items():
        t, c = v["tier"], v["name_confidence"]
        L.append(f"| {k} | {s['reinvite_gap']['week_starts'][k]} | {n(v['rows'])} | {n(t.get('A', 0))} | {n(t.get('B', 0))} | {n(t.get('C', 0))} | "
                 f"{n(c.get('high', 0))} | {n(c.get('medium', 0))} | {n(c.get('none', 0))} | "
                 f"{n(v['has_segment_bucket'])} | {n(v['distinct_recipient_domains'])} | {v['max_rows_one_domain']} |")
    g = s["reinvite_gap"]
    L += ["", f"## Ramp weeks (R01 to R{len(s['ramp_week_totals']):02d}, before full volume)", "",
          "| Week | Starts | Warm rows | Cold rows | Total |", "| --- | --- | --- | --- | --- |"]
    for w, tot in s["ramp_week_totals"].items():
        wr = sum(v for k, v in s["ramp_warm"].items() if k.startswith(w))
        L.append(f"| {w} | {g['week_starts'][w]} | {n(wr)} | {n(tot - wr)} | {n(tot)} |")
    L += ["", "## Re-invite gap", "",
          f"Every row was last invited by other senders between {g['last_invited_date_min']} and "
          f"{g['last_invited_date_max']} ({n(g['last_invited_date_blank'])} rows have no date). No row goes into a week "
          f"that starts less than {s['params']['min_gap_days']} days after its last invite. Rows by month of last invite: "
          + ", ".join(f"{k} {n(v)}" for k, v in g["rows_by_last_invited_month"].items()) + ".", "",
          "Cold usable rows still too recent at the start of each week: "
          + ", ".join(f"{k} {n(v)}" for k, v in g["cold_rows_too_recent_for_week"].items()) + "."]
    wl, rs, h = s["warm_list"], s["reserve_after_S10"], s["hold_gdpr_review"]
    L += ["", "## Warm list", "",
          f"{n(wl['rows'])} rows: {n(wl['registered_no_show'])} registered and did not attend, "
          f"{n(wl['yes_maybe_only'])} answered Yes or Maybe only. Personal mailboxes kept: "
          f"{n(wl['email_type'].get('personal', 0))}. Unscheduled after the ramp: {n(wl['unscheduled'])}.", "",
          "## Held for the EU, EEA, UK and Swiss review", "",
          f"{n(h['cold'])} cold and {n(h['warm'])} warm rows on country domains. By country domain: "
          + ", ".join(f".{k} {n(v)}" for k, v in h["by_country_domain"].items()) + ".", "",
          "## Reserve for after S10", "",
          f"{n(rs['rows'])} cold rows not yet scheduled; {n(rs['usable_within_domain_total_cap'])} of them fit "
          "inside the 30-per-domain cap. Tiers: " + ", ".join(f"{k} {n(v)}" for k, v in rs["tier"].items())
          + ". Name confidence: " + ", ".join(f"{k} {n(v)}" for k, v in rs["name_confidence"].items()) + ".", ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--out", default=str(pathlib.Path.home() / "tantra-enterprise-lists"))
    ap.add_argument("--stats", default=str(pathlib.Path(__file__).resolve().parent))
    ap.add_argument("--weeks", type=int, default=10)
    ap.add_argument("--week-size", type=int, default=100_000)
    ap.add_argument("--pools", type=int, default=4)
    ap.add_argument("--domain-week-cap", type=int, default=3)
    ap.add_argument("--domain-total-cap", type=int, default=30)
    ap.add_argument("--ramp", default="22000,22000,22000,17600,17600,22000,55000,55000,55000,55000")
    ap.add_argument("--ramp-start-week", type=int, default=4, help="plan week (1 = the week of day 0) of R01")
    ap.add_argument("--day0", default="2026-11-09", help="Monday the Workspaces are paid; week dates follow")
    ap.add_argument("--min-gap-days", type=int, default=60)
    a = ap.parse_args()

    out = pathlib.Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if inside_git_repo(out):
        sys.exit(f"refusing to write prospect data inside a git repo: {out}")
    t0 = time.time()
    df, funnel = load(a.master)

    df["pool"] = df["domain"].map(lambda d: stable_hash(d) % a.pools + 1)
    df["tier"] = [tier_of(b, t) for b, t in zip(df["bucket"], df["tld"])]

    warm_all = df[df["warm"]]
    cold_all = df[~df["warm"]]
    hold_warm = warm_all[warm_all["hold"]]
    warm = warm_all[~warm_all["hold"]]
    hold_cold = cold_all[cold_all["hold"]]
    cold = cold_all[~cold_all["hold"]]
    personal_cold = int((cold["email_type"] == "personal").sum())
    cold = cold[cold["email_type"] != "personal"].copy()
    funnel.update({"warm_total": len(warm_all), "warm_held_gdpr_review": len(hold_warm), "warm_list": len(warm),
                   "cold_held_gdpr_review": len(hold_cold), "cold_personal_mailbox_dropped": personal_cold,
                   "cold_usable": len(cold)})

    cold["nr"] = cold["name_confidence"].map(NAME_RANK).fillna(2).astype(int)
    cold["sr"] = cold["series_invited"].map(series_rank)
    cold["h"] = cold["email"].map(stable_hash)
    cold = cold.sort_values(["tier", "nr", "sr", "h"], kind="mergesort").reset_index(drop=True)

    # Week start dates and, per row, the first ramp and main week it may go into (re-invite gap).
    ramp = [int(x) for x in a.ramp.split(",") if x.strip()]
    day0 = pd.Timestamp(a.day0)
    ramp_starts = [day0 + pd.Timedelta(weeks=a.ramp_start_week - 1 + k) for k in range(len(ramp))]
    main_starts = [day0 + pd.Timedelta(weeks=a.ramp_start_week - 1 + len(ramp) + k) for k in range(a.weeks)]

    def first_week(frame, starts):
        ok_from = pd.to_datetime(frame["last_invited_date"].str[:10], errors="coerce") + pd.Timedelta(days=a.min_gap_days)
        idx = pd.Series(pd.Index(starts).searchsorted(ok_from.fillna(pd.Timestamp("1900-01-01")).values), index=frame.index)
        return idx.values

    minm = first_week(cold, main_starts)
    minr = first_week(cold, ramp_starts)
    minr_warm = first_week(warm, ramp_starts)
    last = pd.to_datetime(pd.concat([cold, warm])["last_invited_date"].str[:10], errors="coerce")
    gap_stats = {
        "last_invited_date_min": str(last.min().date()), "last_invited_date_max": str(last.max().date()),
        "last_invited_date_blank": int(last.isna().sum()),
        "rows_by_last_invited_month": {str(k): int(v) for k, v in last.dt.to_period("M").value_counts().sort_index().items()},
        "week_starts": {**{f"R{k + 1:02d}": str(d.date()) for k, d in enumerate(ramp_starts)},
                        **{f"S{k + 1:02d}": str(d.date()) for k, d in enumerate(main_starts)}},
        "cold_rows_too_recent_for_week": {**{f"R{k + 1:02d}": int((minr > k).sum()) for k in range(len(ramp))},
                                          "S01": int((minm > 0).sum())},
    }

    # Main weeks: greedy fill in rank order, per pool, with per-domain caps.
    cap = a.week_size // a.pools
    fill = [[0] * (a.pools + 1) for _ in range(a.weeks)]
    first_open = [0] * (a.pools + 1)
    dom_week = collections.Counter()
    dom_total = collections.Counter()
    slot = [""] * len(cold)
    pools_done = 0
    for i, (d, p) in enumerate(zip(cold["domain"].values, cold["pool"].values)):
        if first_open[p] >= a.weeks or dom_total[d] >= a.domain_total_cap:
            continue
        w = max(first_open[p], minm[i])
        while w < a.weeks and (fill[w][p] >= cap or dom_week[(d, w)] >= a.domain_week_cap):
            w += 1
        if w == a.weeks:
            continue
        slot[i] = f"S{w + 1:02d}_P{p}"
        fill[w][p] += 1; dom_week[(d, w)] += 1; dom_total[d] += 1
        while first_open[p] < a.weeks and fill[first_open[p]][p] >= cap:
            first_open[p] += 1
            if first_open[p] == a.weeks:
                pools_done += 1
        if pools_done == a.pools:
            break
    cold["slot"] = slot

    # Ramp weeks: warm list first, then the next ranked cold rows, within each pool's share of the week.
    rcap = [[r // a.pools] * (a.pools + 1) for r in ramp]
    warm = warm.copy()
    warm["slot"] = ""
    wslot = warm["slot"].values.copy()
    for i, p in enumerate(warm["pool"].values):
        for w in range(minr_warm[i], len(ramp)):
            if rcap[w][p] > 0:
                rcap[w][p] -= 1; wslot[i] = f"R{w + 1:02d}_P{p}"; break
    warm["slot"] = wslot
    rdw = collections.Counter()
    left = sum(rcap[w][q] for w in range(len(ramp)) for q in range(1, a.pools + 1))
    cslot = cold["slot"].values.copy()
    for i, (d, p) in enumerate(zip(cold["domain"].values, cold["pool"].values)):
        if left == 0:
            break
        if cslot[i] or dom_total[d] >= a.domain_total_cap:
            continue
        for w in range(minr[i], len(ramp)):
            if rcap[w][p] > 0 and rdw[(d, w)] < a.domain_week_cap:
                rcap[w][p] -= 1; rdw[(d, w)] += 1; dom_total[d] += 1; left -= 1
                cslot[i] = f"R{w + 1:02d}_P{p}"; break
    cold["slot"] = cslot

    manifest = {"_root": str(out)}
    for s, g in cold[cold["slot"].str.startswith("S")].groupby("slot"):
        write(g, out / "main" / f"{s}.csv", manifest)
    for s, g in cold[cold["slot"].str.startswith("R")].groupby("slot"):
        write(g, out / "ramp" / f"{s}_cold.csv", manifest)
    for s, g in warm[warm["slot"] != ""].groupby("slot"):
        write(g, out / "ramp" / f"{s}_warm.csv", manifest)
    leftover_warm = warm[warm["slot"] == ""]
    if len(leftover_warm):
        write(leftover_warm, out / "warm" / "warm_unscheduled.csv", manifest)
    write(hold_cold, out / "hold" / "gdpr_review_cold.csv", manifest)
    write(hold_warm, out / "hold" / "gdpr_review_warm.csv", manifest)
    reserve = cold[cold["slot"] == ""]
    write(reserve, out / "reserve" / "cold_reserve_after_S10.csv", manifest)
    manifest.pop("_root")
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    os.chmod(out / "MANIFEST.json", 0o600)

    main_rows = cold[cold["slot"].str.startswith("S")]
    stats = {
        "_about": "Count-only stats from slice_enterprise_lists.py. No email, name or recipient domain.",
        "master_sha256_prefix": hashlib.sha256(open(a.master, "rb").read(1 << 20)).hexdigest()[:16] + " (first 1 MiB)",
        "params": {k: v for k, v in vars(a).items() if k not in ("master", "out", "stats")},
        "funnel": dict(funnel),
        "reinvite_gap": gap_stats,
        "cold_usable_by_tier": {k: int(v) for k, v in cold["tier"].value_counts().sort_index().items()},
        "main_total": int(len(main_rows)),
        "gap_to_main_target": int(max(0, a.weeks * a.week_size - len(main_rows))),
        "main_slices": {s: describe(g) for s, g in main_rows.assign(week=main_rows["slot"].str[:3]).groupby("week")},
        "main_slice_pool_rows": {s: int(len(g)) for s, g in main_rows.groupby("slot")},
        "ramp_cold": {s: int(len(g)) for s, g in cold[cold["slot"].str.startswith("R")].groupby("slot")},
        "ramp_warm": {s: int(len(g)) for s, g in warm[warm["slot"] != ""].groupby("slot")},
        "ramp_week_totals": {f"R{w + 1:02d}": int((cold["slot"].str.startswith(f"R{w + 1:02d}")).sum()
                                                  + (warm["slot"].str.startswith(f"R{w + 1:02d}")).sum())
                             for w in range(len(ramp))},
        "warm_list": describe(warm) | {
            "registered_no_show": int((warm["registered_no_show_series"] != "").sum()),
            "yes_maybe_only": int(((warm["registered_no_show_series"] == "")).sum()),
            "unscheduled": int(len(leftover_warm))},
        "hold_gdpr_review": {"cold": int(len(hold_cold)), "warm": int(len(hold_warm)),
                             "by_country_domain": {k: int(v) for k, v in
                                                   pd.concat([hold_cold, hold_warm])["tld"].value_counts().items()}},
        "reserve_after_S10": describe(reserve) | {"usable_within_domain_total_cap": int(sum(
            min(n, max(0, a.domain_total_cap - dom_total[d])) for d, n in reserve["domain"].value_counts().items()))},
        "files_written": len(manifest),
        "seconds": round(time.time() - t0, 1),
    }
    stats_dir = pathlib.Path(a.stats)
    (stats_dir / "slice-stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    (stats_dir / "SLICE_STATS.md").write_text(stats_md(stats))
    print(json.dumps({k: stats[k] for k in ("funnel", "cold_usable_by_tier", "main_total", "gap_to_main_target",
                                            "ramp_week_totals", "files_written", "seconds")}, indent=1))


if __name__ == "__main__":
    main()
