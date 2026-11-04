#!/usr/bin/env python3
"""WebinarJam chat log (and Cal.com bookings) to CRM_CONTRACT events: webinar.poll_answered and webinar.cta_clicked.

WebinarJam keeps poll results per session only and cannot report offer clicks per person (item 17,
EVENT_CONFIG.md). So per-person answers come from the chat: every poll is mirrored by "type A to D in the
chat", and the main call to action by "type BOOKED". Offer clicks come from the booking itself: each offer
cue links to the Cal.com round robin with utm_content=<cta_id>, and Cal.com bookings carry it.
Attendance (webinar.attended, webinar.no_show) is NOT done here: item 17's integration/import_attendance.mjs owns it.

usage:
  python3 -I map_engagement.py --chat CHAT.csv --date 2026-11-12 --start 11:00 --tz America/New_York \
      [--registrants REGISTRANTS.csv] [--bookings BOOKINGS.csv] [--out DIR] [--send]

  --chat         the session's chat log export (WebinarJam: the session's Log, chat download)
  --registrants  the registrants export of the same session; used only to find the email when a chat line has a
                 name and no email (a name must match exactly one registrant, otherwise the line is skipped)
  --bookings     a Cal.com bookings export (or the CRM's booking rows) with email and utm_content
  --start/--tz   session start, used when chat times are clock times; offsets like 00:12:30 need neither
  --out          folder for events.jsonl, summary.json and unmatched.csv (default: print the summary only)
  --send         POST every event to integrations.crm_webhook_url?k=<secret>. Without it, nothing leaves the machine.
                 The secret is read from $CRM_SHARED_SECRET or ~/.config/tantra/keys/crm-shared-secret, never printed.

Column names live in columns.json (aliases, matched case-insensitively). They are assumptions until the first
real export: put the real headers first in each list. Timing (poll windows, offer cues) comes from engagement.json,
which export_from_deck.mjs writes from the deck spec.
"""
import argparse, csv, json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CONFIG = os.path.join(REPO, "deliverables", "_shared", "funnel-config.json")
TEST_DOMAINS = ("example.com", "example.org", "example.net")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [], []
    return [h.strip() for h in rows[0]], rows[1:]


def find_col(head, aliases):
    low = [h.lower().strip() for h in head]
    for a in aliases:
        if a.lower() in low:
            return low.index(a.lower())
    for a in aliases:
        for i, h in enumerate(low):
            if a.lower() in h:
                return i
    return -1


def norm_email(v):
    return (v or "").strip().lower()


def norm_name(v):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (v or "").lower())).strip()


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def zoned(date, hhmm, tz):
    from zoneinfo import ZoneInfo
    return datetime.strptime(f"{date} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(tz))


CLOCK_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p",
                 "%I:%M:%S %p", "%I:%M %p", "%H:%M:%S", "%Y-%m-%dT%H:%M:%S"]


def minute_of(value, date, start, tz, mode, duration=60):
    """Minutes after the session start for one chat time. mode: offset, clock or auto.
    In auto mode a three-part time (HH:MM:SS) is an offset unless --start is known and it lands past the end of the
    session (webinar.duration_minutes): then it is a clock time, for example 11:04:40 for an 11:00 start."""
    v = (value or "").strip()
    if not v:
        return None
    is_clock = mode == "clock" or (mode == "auto" and (re.search(r"[ap]\.?m", v, re.I) or re.match(r"\d{4}-\d\d-\d\d|\d+/\d+/\d+", v)))
    if not is_clock:
        parts = v.split(":")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            h, m, s = map(int, parts)
            offset = h * 60 + m + s / 60
            if mode == "offset" or start is None or h * 60 + m <= duration:
                return offset
            is_clock = True
        elif mode == "offset":
            raise ValueError(f"cannot read offset time {v!r}")
    if start is None:
        raise ValueError("chat times are clock times: pass --start and --tz")
    for fmt in CLOCK_FORMATS:
        try:
            t = datetime.strptime(v, fmt)
        except ValueError:
            continue
        if t.year == 1900:
            t = t.replace(year=start.year, month=start.month, day=start.day)
        t = t.replace(tzinfo=start.tzinfo)
        return (t - start).total_seconds() / 60
    raise ValueError(f"unknown time format {v!r}")


def key(v):
    """Lower case, letters and digits only: 'Follow-up', 'follow up' and 'FOLLOW UP!' are the same answer."""
    return re.sub(r"[^a-z0-9]", "", (v or "").lower())


def poll_answer(message, poll):
    """One poll answer, or None. Accepts a letter ('b', 'B)', 'option B'), a letter followed by a separator and text
    ('D - follow-up', 'b. show up'), a letter followed by the option's own text ('D follow up'), or the option text
    alone ('follow up'). A letter followed by unrelated words ('a great session') is not an answer."""
    m = (message or "").strip()
    by_letter = {o["letter"]: o for o in poll["options"]}
    hit = re.fullmatch(r"\W*(?:option\s+)?([A-Za-z])\W*", m, re.I)
    if hit and hit.group(1).upper() in by_letter:
        return by_letter[hit.group(1).upper()]
    hit = re.fullmatch(r"\W*(?:option\s+)?([A-Za-z])\s*[\)\.:\-]+\s*(.+)", m, re.I)
    if hit and hit.group(1).upper() in by_letter:
        return by_letter[hit.group(1).upper()]
    hit = re.fullmatch(r"\W*(?:option\s+)?([A-Za-z])\s+(.+)", m, re.I)
    if hit and hit.group(1).upper() in by_letter and key(hit.group(2)) == key(by_letter[hit.group(1).upper()]["text"]):
        return by_letter[hit.group(1).upper()]
    for o in poll["options"]:
        if key(m) and key(m) == key(o["text"]):
            return o
    return None


def is_booked(message, word):
    """The whole message is the keyword ('BOOKED', 'booked!', 'Booked!!'), nothing else: 'not booked yet' is not a click."""
    return re.fullmatch(r"\W*" + re.escape(word) + r"\W*", message or "", re.I) is not None


def build(args, eng, cols, cfg):
    date = args.date
    start = zoned(date, args.start, args.tz) if args.start and args.tz else None
    now = datetime.now(timezone.utc)
    events, unmatched = [], []
    stats = {"chat_lines": 0, "poll_answers": 0, "cta_from_chat": 0, "cta_from_bookings": 0, "skipped_no_identity": 0, "skipped_time": 0}

    # name to email, from the registrants export (only unique names)
    by_name = {}
    if args.registrants:
        head, rows = read_csv(args.registrants)
        ce, cf, cl, cn = (find_col(head, cols["registrants"][k]) for k in ("email", "first_name", "last_name", "name"))
        if ce < 0:
            raise SystemExit(f"registrants: no email column in {head}")
        for r in rows:
            e = norm_email(r[ce])
            if not EMAIL_RE.match(e):
                continue
            full = norm_name(r[cn]) if cn >= 0 else norm_name(" ".join(x for x in [r[cf] if cf >= 0 else "", r[cl] if cl >= 0 else ""]))
            if full:
                by_name.setdefault(full, set()).add(e)

    polls = sorted(eng["polls"], key=lambda p: p["opens_at_minute"])
    ctas = sorted(eng["ctas"], key=lambda c: c["show_at_minute"])
    answers, clicks, chat_clickers = {}, {}, set()

    if args.chat:
        head, rows = read_csv(args.chat)
        c = cols["chat"]
        ce, cn, cm, ct = (find_col(head, c[k]) for k in ("email", "name", "message", "time"))
        if cm < 0 or ct < 0:
            raise SystemExit(f"chat: need a message and a time column, got {head}")
        presenters = {norm_name(x) for x in c.get("ignore_names", [])}
        for r in rows:
            stats["chat_lines"] += 1
            name = r[cn] if cn >= 0 else ""
            if norm_name(name) in presenters:
                continue
            email = norm_email(r[ce]) if ce >= 0 else ""
            if not EMAIL_RE.match(email):
                hits = by_name.get(norm_name(name), set())
                email = next(iter(hits)) if len(hits) == 1 else ""
            msg = r[cm]
            try:
                minute = minute_of(r[ct], date, start, args.tz, c.get("time_is", "auto"), int(cfg["webinar"]["duration_minutes"]))
            except ValueError:
                stats["skipped_time"] += 1
                continue
            if minute is None:
                stats["skipped_time"] += 1
                continue
            # a poll answer: inside a poll's window, a valid letter or option
            for p in polls:
                if p["opens_at_minute"] <= minute <= p["opens_at_minute"] + p["window_minutes"]:
                    o = poll_answer(msg, p)
                    if o:
                        if not email:
                            stats["skipped_no_identity"] += 1
                            unmatched.append({"name": name, "kind": f"poll_{p['poll_id']}", "minute": round(minute, 1)})
                        else:
                            answers[(email, p["poll_id"])] = (minute, o)  # the last answer in the window wins
            # BOOKED after an offer cue is live: a click on the cue showing at that minute
            if is_booked(msg, eng.get("booked_keyword", "BOOKED")):
                live = [x for x in ctas if x["show_at_minute"] <= minute]
                if live:
                    if not email:
                        stats["skipped_no_identity"] += 1
                        unmatched.append({"name": name, "kind": "booked", "minute": round(minute, 1)})
                    else:
                        clicks.setdefault((email, live[-1]["cta_id"]), ("webinarjam_chat", start + timedelta(minutes=minute) if start else now))
                        chat_clickers.add(email)  # counted once per person, however often they type it

    if args.bookings:
        head, rows = read_csv(args.bookings)
        b = cols["bookings"]
        ce, cu, cc = (find_col(head, b[k]) for k in ("email", "utm_content", "created"))
        if ce < 0 or cu < 0:
            raise SystemExit(f"bookings: need email and utm_content columns, got {head}")
        known = {x["cta_id"] for x in ctas}
        for r in rows:
            email, cid = norm_email(r[ce]), (r[cu] or "").strip()
            if EMAIL_RE.match(email) and cid in known:
                when = now
                if cc >= 0 and r[cc].strip():
                    try:
                        when = datetime.fromisoformat(r[cc].strip().replace("Z", "+00:00"))
                    except ValueError:
                        pass
                clicks[(email, cid)] = ("calcom_booking", when)  # a booking is the strongest evidence of the click
                stats["cta_from_bookings"] += 1

    for (email, pid), (minute, o) in sorted(answers.items()):
        t = start + timedelta(minutes=minute) if start else now
        events.append({"event": "webinar.poll_answered", "email": email, "ts": iso(t), "source": "webinarjam_chat",
                       "webinar_date": date, "data": {"poll_id": pid, "answer": f"{o['letter']}: {o['text']}"}})
    stats["poll_answers"] = len(answers)
    for (email, cid), (source, t) in sorted(clicks.items()):
        events.append({"event": "webinar.cta_clicked", "email": email, "ts": iso(t), "source": source,
                       "webinar_date": date, "data": {"cta_id": cid}})
    stats["events"] = len(events)
    stats["cta_clicked"] = len(clicks)
    stats["cta_from_chat"] = len(chat_clickers)
    return events, unmatched, stats


def secret():
    s = os.environ.get("CRM_SHARED_SECRET")
    p = os.path.expanduser("~/.config/tantra/keys/crm-shared-secret")
    if not s and os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            s = f.read().strip()
    return s


def send(events, cfg):
    url = cfg["integrations"]["crm_webhook_url"]
    if not url.startswith("https://"):
        raise SystemExit("integrations.crm_webhook_url is not filled in funnel-config.json; nothing sent")
    k = secret()
    if not k:
        raise SystemExit("no CRM secret in $CRM_SHARED_SECRET or ~/.config/tantra/keys/crm-shared-secret; nothing sent")
    ok = bad = 0
    for ev in events:
        req = urllib.request.Request(f"{url}?k={k}", data=json.dumps(ev).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read().decode() or "{}")
            ok += 1 if body.get("ok") else 0
            bad += 0 if body.get("ok") else 1
        except Exception as e:  # report the event type only, never the person
            bad += 1
            print(f"send failed for one {ev['event']}: {type(e).__name__}", file=sys.stderr)
    print(f"sent: {ok} ok, {bad} failed")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--chat"); ap.add_argument("--registrants"); ap.add_argument("--bookings")
    ap.add_argument("--date", required=True); ap.add_argument("--start"); ap.add_argument("--tz")
    ap.add_argument("--engagement", default=os.path.join(HERE, "engagement.json"))
    ap.add_argument("--columns", default=os.path.join(HERE, "columns.json"))
    ap.add_argument("--out"); ap.add_argument("--send", action="store_true")
    args = ap.parse_args(argv)
    if not (args.chat or args.bookings):
        ap.error("give --chat, --bookings or both")
    cfg = load_json(CONFIG)
    events, unmatched, stats = build(args, load_json(args.engagement), load_json(args.columns), cfg)
    if args.out:
        out = os.path.abspath(os.path.expanduser(args.out))
        inside = out == REPO or out.startswith(REPO + os.sep)
        if inside and any(not e["email"].endswith(TEST_DOMAINS) for e in events):
            raise SystemExit("refusing to write real people's data inside the repo; use a folder like ~/tantra-private/21-engagement")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "events.jsonl"), "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        with open(os.path.join(out, "unmatched.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["name", "kind", "minute"]); w.writeheader(); w.writerows(unmatched)
        with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=1)
    print(json.dumps(stats))
    if args.send:
        send(events, cfg)
    return events, unmatched, stats


if __name__ == "__main__":
    main()
