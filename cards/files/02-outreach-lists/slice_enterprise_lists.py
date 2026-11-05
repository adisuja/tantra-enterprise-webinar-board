#!/usr/bin/env python3
"""Cut the EU and UK cold calendar slices for the weekly Enterprise webinar from the consolidated master CSV.

usage:
  python -I slice_enterprise_lists.py <master.csv> [--out ~/tantra-enterprise-lists] [--stats <dir in repo>]
         [--first-webinar 2026-11-12] [--week-size 100000] [--pools 4] [--max-weeks 40]
         [--caps 0,0,0,0,5040,10080,10080,8640,8640,10080,25200,37800,50400,75600] [--p0-caps 1750,1750,1750,1750]
         [--domain-week-cap 3] [--domain-total-cap 30] [--min-gap-days 60]

Adi 2026-11-05: "Let's focus on EU and UK, but ideally English-speaking contacts for the upcoming webinar."
What it does (rules in ICP_AND_SEGMENTS.md):
  1. Reads the master CSV in chunks (only the columns it needs).
  2. Drops junk and role mailboxes, every row with declined_series filled, and personal mailboxes (work addresses only).
  3. Excludes education, government and military domains (not Enterprise buyers).
  4. Keeps only EU and UK rows (plus Norway, Iceland, Switzerland, Liechtenstein), read from the domain ending:
     the master has no usable country column (location 3 rows, region "MIX", campaign_list empty).
     Language tier 1: UK, Ireland, Malta. Tier 2: Netherlands, Sweden, Denmark, Finland, Norway, Iceland.
     Tier 3: the rest of the EU, Switzerland, Liechtenstein and .eu.
  5. Ranks: past Yes/Maybe or registered no-show first (warm), then cold rows by weak fit last, language tier,
     Enterprise fit (A, B), name confidence and the oldest past invite, then a fixed hash.
  6. One slice per weekly webinar, S01 = the first webinar. Slice size = min(week-size, what the senders can send
     that week): --caps is the new 72-sender capacity per week before full warm-up (CAPACITY_PLAN.md), --p0-caps the
     older Tantra calendar senders that bridge the first weeks. From the week after --caps ends, week-size.
     So no contact is spent on a week whose senders cannot reach them. --caps flat cuts every slice at week-size.
  7. Every row goes into the earliest slice whose send window (the 7 days before the webinar) starts at least
     min-gap-days after its last_invited_date, at most domain-week-cap rows per recipient domain a week and
     domain-total-cap over the plan. Each recipient domain is tied to one sender pool (P1 to P4) by a fixed hash.
  8. Writes Tantra-ready CSVs outside the repo and count-only stats into the repo.

Output CSV header (context/from-workshop-project/02-lists/lists.md section 4, read by kits/tantra/leads.mjs):
  first_name,last_name,title,company,website,email,linkedin_url,country
first_name is never blank: rows with no known first name keep the master's "there" (leads.mjs drops a row
with a blank first name, and calendar invites carry no merge fields, so the value is never shown in an invite).
country is filled from the domain ending (United Kingdom, Ireland ...), "European Union" for .eu.
"""
import argparse, collections, hashlib, json, os, pathlib, re, subprocess, sys, time

import pandas as pd

SCHEMA = ["first_name", "last_name", "title", "company", "website", "email", "linkedin_url", "country"]
NEED = ["email", "first_name", "last_name", "name_confidence", "company", "domain", "email_type", "job_title",
        "location", "linkedin_url", "series_invited", "bucket", "accepted_yes_maybe_series", "declined_series",
        "registered_no_show_series", "last_invited_date"]

# Enterprise fit. A: segments that match the buyer. C: weak fit for a $10,000 done-with-you build. Else B.
TIER_A_BUCKET = re.compile(r"b2b|saas|software|fintech|banking|financ|wealth|venture|insurance|accounting|consult|"
                           r"management|strategy|staffing|executive search|crm|cyber|media|digital publishing")
TIER_C_BUCKET = re.compile(r"education|vocational|government|non-profit|advocacy|agriculture|field services|retail|"
                           r"hospitality|career coaching")
TIER_A_TLD = {"io", "ai", "co", "tech", "agency", "vc", "app", "studio", "dev", "software", "solutions", "consulting",
              "digital", "marketing", "media", "partners", "capital", "ventures", "cloud", "systems", "bank",
              "finance", "fund", "biz", "saas"}
TECH_SLD = re.compile(r"\.(?:io|ai|tech|agency|digital|studio)\.[a-z]{2}$")
ORG_LIKE = re.compile(r"(?:^|\.)(?:org|ngo)(?:\.[a-z]{2})?$")
NOT_ICP = re.compile(r"\.(?:edu|gov|mil|int)$|\.(?:edu|gov|mil|ac|k12|sch|nhs|police|gouv|govt|gob|go)\.[a-z]{2}$")

# Language tiers by country domain ending (ICP_AND_SEGMENTS.md explains each choice).
COUNTRY = {
    "uk": ("United Kingdom", 1), "london": ("United Kingdom", 1), "scot": ("United Kingdom", 1),
    "wales": ("United Kingdom", 1), "cymru": ("United Kingdom", 1), "ie": ("Ireland", 1), "mt": ("Malta", 1),
    "nl": ("Netherlands", 2), "se": ("Sweden", 2), "dk": ("Denmark", 2), "fi": ("Finland", 2),
    "no": ("Norway", 2), "is": ("Iceland", 2),
    "at": ("Austria", 3), "be": ("Belgium", 3), "bg": ("Bulgaria", 3), "hr": ("Croatia", 3), "cy": ("Cyprus", 3),
    "cz": ("Czechia", 3), "ee": ("Estonia", 3), "fr": ("France", 3), "de": ("Germany", 3), "gr": ("Greece", 3),
    "hu": ("Hungary", 3), "it": ("Italy", 3), "lv": ("Latvia", 3), "lt": ("Lithuania", 3), "lu": ("Luxembourg", 3),
    "pl": ("Poland", 3), "pt": ("Portugal", 3), "ro": ("Romania", 3), "sk": ("Slovakia", 3), "si": ("Slovenia", 3),
    "es": ("Spain", 3), "ch": ("Switzerland", 3), "li": ("Liechtenstein", 3), "eu": ("European Union", 3),
}
NAME_RANK = {"high": 0, "medium": 1, "none": 2}
FIT_RANK = {"A": 0, "B": 1, "C": 2}
DASHES = re.compile("[\u2013\u2014]")


def fit_of(bucket: str, tld: str, domain: str) -> str:
    parts = [p.strip().lower() for p in bucket.split(";") if p.strip()]
    if parts:
        if any(TIER_A_BUCKET.search(p) for p in parts):
            return "A"
        if all(TIER_C_BUCKET.search(p) for p in parts):
            return "C"
        return "B"
    if tld in TIER_A_TLD or TECH_SLD.search(domain):
        return "A"
    if ORG_LIKE.search(domain):
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
        funnel["dropped_junk"] += int((ch["email_type"] == "junk").sum())
        funnel["dropped_role"] += int((ch["email_type"] == "role").sum())
        ch = ch[~ch["email_type"].isin(["junk", "role"])]
        dec = ch["declined_series"] != ""
        funnel["dropped_declined"] += int(dec.sum()); ch = ch[~dec]
        dom = ch["domain"].where(ch["domain"] != "", ch["email"].str.split("@").str[1]).str.lower()
        ch = ch.assign(domain=dom, tld=dom.str.rsplit(".", n=1).str[-1])
        noticp = ch["domain"].str.contains(NOT_ICP)
        funnel["excluded_edu_gov_mil"] += int(noticp.sum()); ch = ch[~noticp]
        eu = ch["tld"].isin(COUNTRY)
        funnel["outside_eu_uk"] += int((~eu).sum()); ch = ch[eu]
        pers = ch["email_type"] == "personal"
        funnel["eu_uk_dropped_personal_mailbox"] += int(pers.sum()); ch = ch[~pers]
        keep.append(ch)
    df = pd.concat(keep, ignore_index=True)
    before = len(df)
    df = df.drop_duplicates("email")
    funnel["dropped_duplicate_email"] = before - len(df)
    return df, funnel


def to_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "first_name": df["first_name"].where(df["first_name"] != "", "there"),
        "last_name": df["last_name"],
        "title": df["job_title"],
        "company": df["company"],
        "website": df["domain"],
        "email": df["email"],
        "linkedin_url": df["linkedin_url"],
        "country": df["tld"].map(lambda t: COUNTRY[t][0]),
    })
    return out.apply(lambda c: c.str.replace(DASHES, "-", regex=True))


def write(df: pd.DataFrame, path: pathlib.Path, manifest: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    to_schema(df).to_csv(path, index=False, columns=SCHEMA)
    os.chmod(path, 0o600)
    manifest[str(path.relative_to(manifest["_root"]))] = {
        "rows": len(df), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def count(series) -> dict:
    return {str(k): int(v) for k, v in series.value_counts().sort_index().items()}


def describe(df: pd.DataFrame) -> dict:
    """Count-only profile of a set of rows: no email, name or recipient domain leaves this function."""
    vc = df["domain"].value_counts()
    return {
        "rows": int(len(df)),
        "warm": int(df["warm"].sum()),
        "language_tier": count(df["lang"]),
        "fit": count(df["fit"]),
        "name_confidence": {k: int(v) for k, v in df["name_confidence"].value_counts().items()},
        "distinct_recipient_domains": int(len(vc)),
        "max_rows_one_domain": int(vc.max()) if len(vc) else 0,
    }


def stats_md(s: dict) -> str:
    """SLICE_STATS.md from the stats dict: counts only."""
    f = s["funnel"]; n = lambda x: f"{x:,}"
    u = s["usable_by_language_tier"]
    L = ["# Slice Stats (count only, written by slice_enterprise_lists.py)", "",
         "No email, name or recipient domain appears here. The files themselves are in `~/tantra-enterprise-lists/`.", "",
         "## From Master to Usable EU and UK Work Addresses", "", "| Step | Rows |", "| --- | --- |",
         f"| Read from the master CSV | {n(f['read'])} |",
         f"| Dropped: junk mailbox | {n(f['dropped_junk'])} |",
         f"| Dropped: role mailbox (info@, sales@ ...) | {n(f['dropped_role'])} |",
         f"| Dropped: declined a past invite (any `declined_series`) | {n(f['dropped_declined'])} |",
         f"| Excluded: education, government or military domain | {n(f['excluded_edu_gov_mil'])} |",
         f"| Outside the EU and UK (or no country ending: .com, .io, .net ...) | {n(f['outside_eu_uk'])} |",
         f"| Dropped: personal mailbox on an EU or UK domain | {n(f['eu_uk_dropped_personal_mailbox'])} |",
         f"| **Usable EU and UK work addresses** | **{n(s['usable_total'])}** |", "",
         "## Usable by Language Tier", "",
         "| Tier | Countries | Usable | Warm | Weeks of 100,000 |", "| --- | --- | --- | --- | --- |"]
    names = {1: "UK, Ireland, Malta", 2: "Netherlands, Sweden, Denmark, Finland, Norway, Iceland",
             3: "Rest of the EU, Switzerland, Liechtenstein, .eu"}
    for t in ("1", "2", "3"):
        L.append(f"| {t} | {names[int(t)]} | {n(u[t]['rows'])} | {n(u[t]['warm'])} | {u[t]['rows'] / 100_000:.2f} |")
    L.append(f"| All | | {n(s['usable_total'])} | {n(sum(u[t]['warm'] for t in u))} | {s['usable_total'] / 100_000:.2f} |")
    L += ["", "Usable by country: " + ", ".join(f"{k} {n(v)}" for k, v in s["usable_by_country"].items()) + ".", "",
          "Enterprise fit of the usable rows: " + ", ".join(f"{k} {n(v)}" for k, v in s["usable_by_fit"].items())
          + " (C: education, non-profit, retail and similar; sliced last).", "",
          "## Weekly Slices (one per webinar)", "",
          "| Slice | Webinar | Send window | Capacity | Rows | Warm | Tier 1 | Tier 2 | Tier 3 | Fit C | Name none | Max rows one domain |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, v in s["slices"].items():
        t = v["language_tier"]
        L.append(f"| {k} | {v['webinar']} | {v['send_from']} to {v['send_to']} | {n(v['capacity'])} | {n(v['rows'])} | "
                 f"{n(v['warm'])} | {n(t.get('1', 0))} | {n(t.get('2', 0))} | {n(t.get('3', 0))} | {n(v['fit'].get('C', 0))} | "
                 f"{n(v['name_confidence'].get('none', 0))} | {v['max_rows_one_domain']} |")
    c = s["coverage"]
    L += ["", f"Scheduled: **{n(c['scheduled'])}** rows in {c['slices_with_rows']} slices, the last for the webinar of "
          f"{c['last_webinar']}. Full 100,000 slices: {c['full_slices']}. Before the first full slice: {n(c['before_first_full'])} rows.", "",
          f"Not scheduled (reserve): {n(s['reserve']['rows'])} rows, all over the {s['params']['domain_total_cap']}-per-domain "
          f"plan cap or the {s['params']['domain_week_cap']}-per-domain weekly cap in the last weeks.", "",
          "## Re-invite Gap", "",
          f"Every usable row was last invited by other senders between {s['reinvite_gap']['last_invited_date_min']} and "
          f"{s['reinvite_gap']['last_invited_date_max']} ({n(s['reinvite_gap']['last_invited_date_blank'])} rows have no date). "
          f"No row goes into a slice whose send window starts less than {s['params']['min_gap_days']} days after its last invite. "
          "Rows by month of last invite: " + ", ".join(f"{k} {n(v)}" for k, v in s["reinvite_gap"]["rows_by_last_invited_month"].items()) + ".", "",
          "Usable rows still too recent when each early send window opens: "
          + ", ".join(f"{k} {n(v)}" for k, v in s["reinvite_gap"]["too_recent_at_window"].items()) + ".", ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--out", default=str(pathlib.Path.home() / "tantra-enterprise-lists"))
    ap.add_argument("--stats", default=str(pathlib.Path(__file__).resolve().parent))
    ap.add_argument("--first-webinar", default="2026-11-12", help="Thursday of the first webinar (S01)")
    ap.add_argument("--week-size", type=int, default=100_000)
    ap.add_argument("--pools", type=int, default=4)
    ap.add_argument("--max-weeks", type=int, default=40)
    ap.add_argument("--caps", default="0,0,0,0,5040,10080,10080,8640,8640,10080,25200,37800,50400,75600",
                    help="new-sender capacity per week before full volume, or 'flat'")
    ap.add_argument("--p0-caps", default="1750,1750,1750,1750", help="older Tantra calendar senders, per week")
    ap.add_argument("--domain-week-cap", type=int, default=3)
    ap.add_argument("--domain-total-cap", type=int, default=30)
    ap.add_argument("--min-gap-days", type=int, default=60)
    a = ap.parse_args()

    out = pathlib.Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.chmod(out, 0o700)
    if inside_git_repo(out):
        sys.exit(f"refusing to write prospect data inside a git repo: {out}")
    t0 = time.time()
    df, funnel = load(a.master)

    df["warm"] = (df["accepted_yes_maybe_series"] != "") | (df["registered_no_show_series"] != "")
    df["lang"] = df["tld"].map(lambda t: COUNTRY[t][1])
    df["fit"] = [fit_of(b, t, d) for b, t, d in zip(df["bucket"], df["tld"], df["domain"])]
    df["pool"] = df["domain"].map(lambda d: stable_hash(d) % a.pools + 1)
    df["weak"] = (df["fit"] == "C").astype(int)
    df["wr"] = (~df["warm"]).astype(int)
    df["fr"] = df["fit"].map(FIT_RANK)
    df["nr"] = df["name_confidence"].map(NAME_RANK).fillna(2).astype(int)
    df["sr"] = df["series_invited"].map(series_rank)
    df["h"] = df["email"].map(stable_hash)
    df = df.sort_values(["wr", "weak", "lang", "fr", "nr", "sr", "h"], kind="mergesort").reset_index(drop=True)

    # Weekly capacity: slice k serves the webinar first_webinar + 7k; it is sent in the 7 days before.
    flat = a.caps.strip().lower() == "flat"
    ramp = [] if flat else [int(x) for x in a.caps.split(",") if x.strip()]
    p0 = [] if flat else [int(x) for x in a.p0_caps.split(",") if x.strip()]
    W = a.max_weeks
    webinar = [pd.Timestamp(a.first_webinar) + pd.Timedelta(weeks=k) for k in range(W)]
    window = [d - pd.Timedelta(days=7) for d in webinar]
    newcap = [ramp[k] if k < len(ramp) else a.week_size for k in range(W)]
    newcap = [min(c, a.week_size) for c in newcap]
    p0cap = [p0[k] if k < len(p0) else 0 for k in range(W)]
    pcap = [[0] + [c // a.pools] * a.pools for c in newcap]
    for k in range(W):
        pcap[k][0] = min(p0cap[k], a.week_size - (pcap[k][1] * a.pools))

    ok_from = pd.to_datetime(df["last_invited_date"].str[:10], errors="coerce") + pd.Timedelta(days=a.min_gap_days)
    minw = pd.Index(window).searchsorted(ok_from.fillna(pd.Timestamp("1900-01-01")).values)
    last = pd.to_datetime(df["last_invited_date"].str[:10], errors="coerce")

    fill = [[0] * (a.pools + 1) for _ in range(W)]
    dom_week = collections.Counter()
    dom_total = collections.Counter()
    slot_w = [-1] * len(df)
    slot_p = [-1] * len(df)
    for i, (d, p) in enumerate(zip(df["domain"].values, df["pool"].values)):
        if dom_total[d] >= a.domain_total_cap:
            continue
        for w in range(minw[i], W):
            if dom_week[(d, w)] >= a.domain_week_cap:
                continue
            q = 0 if fill[w][0] < pcap[w][0] else (p if fill[w][p] < pcap[w][p] else -1)
            if q < 0:
                continue
            fill[w][q] += 1; dom_week[(d, w)] += 1; dom_total[d] += 1
            slot_w[i] = w; slot_p[i] = q
            break
    df["w"] = slot_w
    df["p"] = slot_p

    manifest = {"_root": str(out)}
    sched = df[df["w"] >= 0]
    for (w, p, warm), g in sched.groupby(["w", "p", "warm"]):
        name = f"S{w + 1:02d}_{webinar[w].date()}_P{p}_{'warm' if warm else 'cold'}.csv"
        write(g, out / "slices" / name, manifest)
    reserve = df[df["w"] < 0]
    if len(reserve):
        write(reserve, out / "reserve" / "eu_uk_reserve.csv", manifest)
    manifest.pop("_root")
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    os.chmod(out / "MANIFEST.json", 0o600)

    slices = {}
    for w, g in sched.groupby("w"):
        slices[f"S{w + 1:02d}"] = {"webinar": str(webinar[w].date()), "send_from": str(window[w].date()),
                                   "send_to": str((webinar[w] - pd.Timedelta(days=1)).date()),
                                   "capacity": int(newcap[w] + p0cap[w]) if not flat else a.week_size,
                                   "capacity_new_senders": int(newcap[w]), "capacity_older_senders": int(p0cap[w]),
                                   **describe(g), "rows_by_pool": {f"P{k}": int(v) for k, v in g["p"].value_counts().sort_index().items()}}
    full = [k for k, v in slices.items() if v["rows"] >= a.week_size]
    first_full = int(full[0][1:]) - 1 if full else W
    usable_by_tier = {str(t): {"rows": int((df["lang"] == t).sum()), "warm": int(((df["lang"] == t) & df["warm"]).sum())}
                      for t in (1, 2, 3)}
    stats = {
        "_about": "Count-only stats from slice_enterprise_lists.py. No email, name or recipient domain.",
        "master_sha256_prefix": hashlib.sha256(open(a.master, "rb").read(1 << 20)).hexdigest()[:16] + " (first 1 MiB)",
        "params": {k: v for k, v in vars(a).items() if k not in ("master", "out", "stats")},
        "funnel": dict(funnel),
        "usable_total": int(len(df)),
        "usable_by_language_tier": usable_by_tier,
        "usable_by_country": {COUNTRY[t][0] if t not in ("london", "scot", "wales", "cymru") else f"United Kingdom (.{t})": int(v)
                              for t, v in df["tld"].value_counts().items()},
        "usable_by_fit": count(df["fit"]),
        "reinvite_gap": {
            "last_invited_date_min": str(last.min().date()), "last_invited_date_max": str(last.max().date()),
            "last_invited_date_blank": int(last.isna().sum()),
            "rows_by_last_invited_month": {str(k): int(v) for k, v in last.dt.to_period("M").value_counts().sort_index().items()},
            "too_recent_at_window": {f"S{k + 1:02d} ({window[k].date()})": int((minw > k).sum()) for k in range(6)},
        },
        "week_send_windows": {f"S{k + 1:02d}": str(window[k].date()) for k in range(W)},
        "slices": slices,
        "coverage": {"scheduled": int(len(sched)), "slices_with_rows": len(slices),
                     "last_webinar": slices[max(slices)]["webinar"] if slices else "",
                     "full_slices": len(full), "first_full_slice": full[0] if full else "",
                     "before_first_full": int((sched["w"] < first_full).sum())},
        "reserve": describe(reserve) if len(reserve) else {"rows": 0},
        "files_written": len(manifest),
        "seconds": round(time.time() - t0, 1),
    }
    stats_dir = pathlib.Path(a.stats)
    (stats_dir / "slice-stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    (stats_dir / "SLICE_STATS.md").write_text(stats_md(stats))
    print(json.dumps({k: stats[k] for k in ("funnel", "usable_total", "usable_by_language_tier", "coverage",
                                            "files_written", "seconds")}, indent=1))


if __name__ == "__main__":
    main()
