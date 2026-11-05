#!/usr/bin/env python3
"""Turn WebinarJam attendance exports into retargeting audiences (segments only).

This script never posts or writes CRM events: item 17's import_attendance is the only producer
of webinar.attended and webinar.no_show. It applies the same attendance rule so its segments
match the CRM Webinar tab.

usage:
  python3 retarget_segments.py --exports EXPORT.csv [EXPORT2.csv ...] --as-of 2026-11-20 \
      --out ~/tantra-private/27-retargeting [--exclude crm_exclusions.csv] \
      [--columns webinarjam_columns.json] [--webinar-date 2026-11-12]

Reads:
  * one or more WebinarJam exports (one session each, or many: each row carries its date);
    column names come from webinarjam_columns.json (an assumption until the first real export);
  * optional exclusions CSV from the CRM (columns: email, reason) holding everyone who booked,
    replied, opted out, re-registered, won or lost (booking.created, contact.replied,
    contact.opted_out, a later webinar.registered, deal.won, deal.lost); must have an email
    column and at least one row, or the script stops;
  * funnel-config.json for the minute cutoff (webinar.retarget_cutoff_minute).

Segments, per deliverables/_shared/CRM_CONTRACT.md:
  attended        WebinarJam marks the person as attended (if the export has no attended
                  column: time in the room or a join time). minutes_in_room is a whole number
                  floored at 1: a blank or 0 time becomes 1. Never null, never no_show.
  early_leaver    attended and minutes_in_room < cutoff (25)
  stayed_to_offer attended and minutes_in_room >= cutoff
  no_show         only registrants WebinarJam marks as not attended (minutes_in_room 0)
  retarget_until  webinar date + 42 days for early_leaver and no_show; day 42 is the drop day
Rows for the same email and date (rejoins) are merged first: attended if any row attended,
minutes summed.
A contact is in an audience on the --as-of date when its LATEST webinar is early_leaver or
no_show, as-of is on day 0 to 41 after it, and it is not excluded.
Phase: "replay" for days 0 to 13 after the webinar, "call" for days 14 to 41.

Writes into <out>/<as-of>/:
  meta_<segment>_<phase>.csv     Meta customer list, SHA-256 hashed: email, phone, fn, ln, country
  linkedin_<segment>_<phase>.csv LinkedIn contact list, SHA-256 hashed: email
  meta_exclude.csv, linkedin_exclude.csv   hashed exclusions (booked, replied, opted out)
  segments.csv                   plain per-contact result (personal data: never in the repo)
  summary.json                   counts only, no personal data
Refuses to write inside the git repo unless every email is on a reserved test domain.
"""
import argparse, csv, hashlib, json, os, re, string, sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CONFIG = os.path.join(REPO, "deliverables", "_shared", "funnel-config.json")
TEST_DOMAINS = ("example.com", "example.org", "example.net")
RETARGET_DAYS = 42
REPLAY_DAYS = 14
META_MIN, LINKEDIN_MIN = 100, 300  # smallest audience each platform will serve (check in the ad tools)

# Geo for a UK and EU audience: the language tiers of item 2 (02-outreach-lists/ICP_AND_SEGMENTS.md).
# ISO code: (English name, language tier, calling code). Ad locations in ads.csv come from here.
GEO_TIERS = {
    "gb": ("United Kingdom", 1, "44"), "ie": ("Ireland", 1, "353"), "mt": ("Malta", 1, "356"),
    "nl": ("Netherlands", 2, "31"), "se": ("Sweden", 2, "46"), "dk": ("Denmark", 2, "45"), "fi": ("Finland", 2, "358"),
    "no": ("Norway", 2, "47"), "is": ("Iceland", 2, "354"),
    "at": ("Austria", 3, "43"), "be": ("Belgium", 3, "32"), "bg": ("Bulgaria", 3, "359"), "hr": ("Croatia", 3, "385"),
    "cy": ("Cyprus", 3, "357"), "cz": ("Czechia", 3, "420"), "ee": ("Estonia", 3, "372"), "fr": ("France", 3, "33"),
    "de": ("Germany", 3, "49"), "gr": ("Greece", 3, "30"), "hu": ("Hungary", 3, "36"), "it": ("Italy", 3, "39"),
    "lv": ("Latvia", 3, "371"), "lt": ("Lithuania", 3, "370"), "lu": ("Luxembourg", 3, "352"), "pl": ("Poland", 3, "48"),
    "pt": ("Portugal", 3, "351"), "ro": ("Romania", 3, "40"), "sk": ("Slovakia", 3, "421"), "si": ("Slovenia", 3, "386"),
    "es": ("Spain", 3, "34"), "ch": ("Switzerland", 3, "41"), "li": ("Liechtenstein", 3, "423"),
}
CALLING = {k: v[2] for k, v in GEO_TIERS.items()}
CALLING.update({"us": "1", "ca": "1", "in": "91", "au": "61", "nz": "64", "sg": "65", "ae": "971", "za": "27"})
TRUNK_ZERO_KEPT = {"it"}  # Italian numbers keep their leading 0 after the country code

COUNTRY_NAMES = {v[0].lower(): k for k, v in GEO_TIERS.items()}
COUNTRY_NAMES.update({
    "uk": "gb", "u.k.": "gb", "great britain": "gb", "britain": "gb", "england": "gb", "scotland": "gb", "wales": "gb",
    "northern ireland": "gb", "republic of ireland": "ie", "the netherlands": "nl", "holland": "nl", "nederland": "nl",
    "sverige": "se", "danmark": "dk", "suomi": "fi", "norge": "no", "ísland": "is", "czech republic": "cz", "česko": "cz",
    "deutschland": "de", "österreich": "at", "belgië": "be", "belgique": "be", "españa": "es", "italia": "it",
    "polska": "pl", "schweiz": "ch", "suisse": "ch", "svizzera": "ch",
    "united states": "us", "usa": "us", "canada": "ca", "australia": "au", "india": "in", "singapore": "sg",
    "united arab emirates": "ae", "uae": "ae", "new zealand": "nz", "south africa": "za"})

def sha256(v):
    return hashlib.sha256(v.encode("utf-8")).hexdigest()

def norm_email(v):
    return (v or "").strip().lower()

def norm_name(v):
    v = (v or "").strip().lower()
    return "".join(ch for ch in v if ch not in string.punctuation and not ch.isspace())

def norm_country(v):
    v = (v or "").strip().lower()
    if re.fullmatch(r"[a-z]{2}", v):
        return v
    return COUNTRY_NAMES.get(v, "")

def norm_phone(v, cc="", country=""):
    """Digits with country code, no plus, no trunk zero (Meta spec). A national number such as
    07700 900123 takes its country code from the phone country code column, else from the
    Country column (UK and EU registrants often type it that way). Unknown country code: drop."""
    v = (v or "").strip()
    if not v:
        return ""
    digits = re.sub(r"\D", "", v)
    if v.startswith("+") or v.startswith("00"):
        return digits.lstrip("0")
    ccd = re.sub(r"\D", "", cc or "") or CALLING.get(country, "")
    if ccd:
        return ccd + (digits if country in TRUNK_ZERO_KEPT else digits.lstrip("0"))
    return ""

def parse_minutes(v, unit="minutes", colon_format="h:mm"):
    """Time in room. "1:05:30" is H:MM:SS. A two-part "1:05" is H:MM (65 minutes) unless
    webinarjam_columns.json sets "colon_format": "m:ss" (then 1 minute 5 seconds)."""
    v = (v or "").strip().lower()
    if not v:
        return None
    m = re.fullmatch(r"(\d+):(\d{1,2}):(\d{1,2})", v)
    if m:
        h, mi, s = map(int, m.groups())
        return h * 60 + mi + s / 60
    m = re.fullmatch(r"(\d+):(\d{1,2})", v)
    if m:
        a, b = map(int, m.groups())
        return a + b / 60 if colon_format == "m:ss" else a * 60 + b
    m = re.fullmatch(r"(?:(\d+)\s*h(?:ours?|rs?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?|s)?)?)?\s*(?:(\d+)\s*s(?:ec(?:onds?|s)?)?)?", v)
    if m and any(m.groups()):
        h, mi, s = (int(x) if x else 0 for x in m.groups())
        return h * 60 + mi + s / 60
    try:
        n = float(v)
    except ValueError:
        return None
    return n / 60 if unit == "seconds" else n

def parse_dt(v, formats):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        pass
    for f in formats:
        try:
            return datetime.strptime(v, f)
        except ValueError:
            continue
    return None

def yes(v):
    return (v or "").strip().lower() in ("yes", "y", "true", "1", "attended", "live")

def no(v):
    return (v or "").strip().lower() in ("no", "n", "false", "0", "did not attend", "absent")

def find_columns(header, cols):
    norm = {re.sub(r"\s+", " ", h.strip().lower()): h for h in header}
    found = {}
    for field, names in cols.items():
        if not isinstance(names, list) or field.startswith("_") or field == "date_formats":
            continue
        for n in names:
            key = re.sub(r"\s+", " ", n.strip().lower())
            if key in norm:
                found[field] = norm[key]
                break
    return found

def read_exports(paths, cols, fallback_date):
    rows, mapping_report = [], {}
    fmts = cols.get("date_formats", [])
    unit = cols.get("minutes_unit", "minutes")
    colon = cols.get("colon_format", "h:mm")
    for p in paths:
        with open(p, newline="", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            colmap = find_columns(r.fieldnames or [], cols)
            mapping_report[os.path.basename(p)] = colmap
            if "email" not in colmap:
                sys.exit("%s: no email column found. Edit webinarjam_columns.json (header is: %s)" % (p, r.fieldnames))
            for line in r:
                g = lambda k: line.get(colmap[k], "") if k in colmap else ""
                email = norm_email(g("email"))
                if not email or "@" not in email:
                    continue
                first, last = g("first_name").strip(), g("last_name").strip()
                if colmap.get("first_name", "").strip().lower() == "name" and not last and " " in first:
                    first, last = first.split(" ", 1)
                d = parse_dt(g("webinar_date"), fmts)
                wdate = d.date() if d else fallback_date
                if wdate is None:
                    sys.exit("%s: no webinar date for %s. Add a date column to the config or pass --webinar-date" % (p, "a row"))
                joined, left = parse_dt(g("joined_at"), fmts), parse_dt(g("left_at"), fmts)
                parsed = parse_minutes(g("minutes_in_room"), unit, colon)
                att_raw = g("attended")
                if yes(att_raw):
                    attended = True
                elif no(att_raw):
                    attended = False
                else:  # no attended column or a blank cell: time in the room or a join time means attended
                    attended = bool(parsed) or bool(joined)
                # CRM_CONTRACT attendance rule: whole minutes, floored at 1 for anyone attended
                minutes = max(1, int(parsed or 0)) if attended else 0
                rows.append(dict(email=email, first=first, last=last, phone=norm_phone(g("phone"), g("phone_country_code"), norm_country(g("country"))),
                                 country=norm_country(g("country")), webinar_date=wdate, minutes=minutes,
                                 attended=attended, joined=joined, left=left))
    return rows, mapping_report

def merge_rows(rows):
    """One row per email and webinar date. A person who drops out and rejoins shows up more than
    once in an export: sum the minutes, keep the earliest join and the latest leave."""
    merged = {}
    for r in rows:
        k = (r["email"], r["webinar_date"])
        m = merged.get(k)
        if m is None:
            merged[k] = dict(r)
            continue
        m["minutes"] = m["minutes"] + r["minutes"]
        m["attended"] = m["attended"] or r["attended"]
        m["joined"] = min([d for d in (m["joined"], r["joined"]) if d], default=None)
        m["left"] = max([d for d in (m["left"], r["left"]) if d], default=None)
        for f in ("first", "last", "phone", "country"):
            m[f] = m[f] or r[f]
    return list(merged.values())

def segment(r, cutoff):
    if not r["attended"]:
        return "no_show"
    return "early_leaver" if max(1, r["minutes"]) < cutoff else "stayed_to_offer"

def inside_repo(path):
    path = os.path.abspath(os.path.expanduser(path))
    return path == REPO or path.startswith(REPO + os.sep)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exports", nargs="+", required=True)
    ap.add_argument("--as-of", required=True, help="YYYY-MM-DD: the day the audiences are built for")
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude", help="CRM CSV with columns email, reason (booked, replied, opted_out)")
    ap.add_argument("--columns", default=os.path.join(HERE, "webinarjam_columns.json"))
    ap.add_argument("--webinar-date", help="YYYY-MM-DD for exports with no date column")
    a = ap.parse_args(argv)

    cfg = json.load(open(CONFIG))
    cutoff = int(cfg["webinar"]["retarget_cutoff_minute"])
    cols = json.load(open(a.columns))
    as_of = date.fromisoformat(a.as_of)
    fallback = date.fromisoformat(a.webinar_date) if a.webinar_date else None
    rows, mapping = read_exports(a.exports, cols, fallback)
    raw_rows = len(rows)
    rows = merge_rows(rows)

    excluded = {}
    if a.exclude:
        ex = csv.DictReader(open(a.exclude, newline="", encoding="utf-8-sig"))
        exmap = find_columns(ex.fieldnames or [], {"email": ["email", "Email", "E-mail"], "reason": ["reason", "Reason"]})
        if "email" not in exmap:
            sys.exit("REFUSED: exclusions file %s has no email column (header: %s). Without it, booked and "
                     "opted-out people would be retargeted." % (a.exclude, ex.fieldnames))
        for r in ex:
            e = norm_email(r.get(exmap["email"]))
            if e:
                excluded[e] = (r.get(exmap.get("reason", ""), "") or "excluded").strip()
        if not excluded:
            sys.exit("REFUSED: exclusions file %s has no rows. Export it again from the CRM: an empty list "
                     "would retarget everyone who booked, replied or opted out." % a.exclude)

    all_emails = {r["email"] for r in rows} | set(excluded)
    if inside_repo(a.out) and not all(e.split("@")[-1] in TEST_DOMAINS for e in all_emails):
        sys.exit("REFUSED: --out is inside the repo and the data holds real-looking emails. "
                 "Personal data stays outside the repo: use --out ~/tantra-private/27-retargeting")

    out = os.path.join(os.path.expanduser(a.out), as_of.isoformat())
    os.makedirs(out, exist_ok=True)

    # latest webinar per contact decides
    latest = {}
    for r in rows:
        cur = latest.get(r["email"])
        if cur is None or r["webinar_date"] > cur["webinar_date"]:
            latest[r["email"]] = r

    buckets, results = {}, []
    counts = {"rows": raw_rows, "merged_rows": len(rows), "contacts": len(latest), "stayed_to_offer": 0, "early_leaver": 0, "no_show": 0,
              "excluded": 0, "dropped_after_6_weeks": 0, "not_started": 0}
    for e, r in sorted(latest.items()):
        seg = segment(r, cutoff)
        counts[seg] += 1
        until = r["webinar_date"] + timedelta(days=RETARGET_DAYS)
        status, phase = "", ""
        if seg not in ("early_leaver", "no_show"):
            status = "not_retargeted"
        elif e in excluded:
            status = "excluded:" + excluded[e]; counts["excluded"] += 1
        elif as_of >= until:  # day 42 is the drop day
            status = "dropped_after_6_weeks"; counts["dropped_after_6_weeks"] += 1
        elif as_of < r["webinar_date"]:
            status = "not_started"; counts["not_started"] += 1
        else:
            phase = "replay" if (as_of - r["webinar_date"]).days < REPLAY_DAYS else "call"
            status = "active"
            buckets.setdefault((seg, phase), []).append(r)
        results.append({"email": e, "webinar_date": r["webinar_date"].isoformat(), "segment": seg,
                        "minutes_in_room": r["minutes"],
                        "retarget_until": until.isoformat() if seg in ("early_leaver", "no_show") else "",
                        "phase": phase, "status": status})

    def meta_row(r):
        return {"email": sha256(r["email"]),
                "phone": sha256(r["phone"]) if r["phone"] else "",
                "fn": sha256(norm_name(r["first"])) if norm_name(r["first"]) else "",
                "ln": sha256(norm_name(r["last"])) if norm_name(r["last"]) else "",
                "country": sha256(r["country"]) if r["country"] else ""}

    def write(name, header, items):
        with open(os.path.join(out, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(items)

    audiences = {}
    for seg in ("early_leaver", "no_show"):
        for phase in ("replay", "call"):
            items = buckets.get((seg, phase), [])
            write("meta_%s_%s.csv" % (seg, phase), ["email", "phone", "fn", "ln", "country"], [meta_row(r) for r in items])
            write("linkedin_%s_%s.csv" % (seg, phase), ["email"], [{"email": sha256(r["email"])} for r in items])
            audiences["%s_%s" % (seg, phase)] = len(items)
    write("meta_exclude.csv", ["email", "phone", "fn", "ln", "country"], [{"email": sha256(e), "phone": "", "fn": "", "ln": "", "country": ""} for e in sorted(excluded)])
    write("linkedin_exclude.csv", ["email"], [{"email": sha256(e)} for e in sorted(excluded)])
    write("segments.csv", ["email", "webinar_date", "segment", "minutes_in_room", "retarget_until", "phase", "status"], results)

    warnings = []
    for k, n in audiences.items():
        if 0 < n < META_MIN:
            warnings.append("%s: %d contacts, under Meta's %d minimum; combine phases or wait a week" % (k, n, META_MIN))
        if 0 < n < LINKEDIN_MIN:
            warnings.append("%s: %d contacts, under LinkedIn's %d matched-member minimum" % (k, n, LINKEDIN_MIN))
    summary = {"as_of": as_of.isoformat(), "cutoff_minute": cutoff, "counts": counts, "audiences": audiences,
               "excluded_list": len(excluded), "columns_matched": mapping, "warnings": warnings}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=2)
    print(json.dumps({"out": out, "counts": counts, "audiences": audiences, "warnings": len(warnings)}, indent=2))
    return out

if __name__ == "__main__":
    main()
