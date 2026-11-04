#!/usr/bin/env python3
"""Plan the 15b sends for one registrant. This is the rule book in code; the sending side
(Tantra campaigns fed by item 23's runner) must give the same answer.

usage:
  python3 scheduler.py --selftest
  python3 scheduler.py --registered 2026-11-10T09:00:00Z --start 2026-11-12T16:00:00Z [--tz Asia/Kolkata]

The registrant's timezone is webinar.registered data.timezone (IANA, from the browser). When it
is missing, the webinar timezone from funnel-config.json is used (UTC while that is unfilled).

Rules (SEQUENCE_MAP.md explains them in words):
 1. Registered after the start: only 15B-L0 (we're live) at once, and only while the session is
    still running (registered < start + webinar.duration_minutes). After that, nothing: the
    item 22 no-show track or the next date applies.
 2. 15B-R0 at registration: WhatsApp only. WebinarJam sends the confirmation email with the
    personal join link (item 17), so 15b sends no confirmation email.
 3. 15B-R1 (catch-up videos) at registration + 60 min, only if the registrant missed 15B-W1
    and the send lands at least 26 hours before the start.
 4. A start-anchored step whose time has passed at registration is skipped.
 5. A start-anchored step due less than 30 minutes after an earlier planned message is skipped,
    except 15B-M15, 15B-L0 and 15B-L10 (they carry the link at the moment it matters).
 6. Day-level steps (W1, V2, D3, V4, D1) move into 08:00 to 20:00 in the registrant's timezone:
    before 08:00 moves to 08:00, at or after 20:00 moves to 19:00, same local date.
 7. WhatsApp window (CRM_CONTRACT): every WhatsApp step, live-day reminders included, goes only
    between 08:00 and 20:00 in the registrant's timezone. Outside it the email still goes and
    the WhatsApp is skipped. Waiving this for live-day steps is Adi's decision.
 8. Calls keep to 08:00 to 20:00 local, always. 15B-C1 outside the window moves to 19:30 local
    on the same day (or the day before if it fell before 08:00) and is skipped if that is past
    or later than start minus 180 min. 15B-C2 outside the window is skipped.
"""
import argparse, csv, json, os, sys
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "..", "_shared", "funnel-config.json")))
DURATION = timedelta(minutes=int(CONFIG["webinar"]["duration_minutes"]))
DAY_LEVEL = {"15B-W1", "15B-V2", "15B-D3", "15B-V4", "15B-D1"}
EXEMPT_GAP = {"15B-M15", "15B-L0", "15B-L10"}
GAP = timedelta(minutes=30)

def webinar_tz():
    tz = str(CONFIG["webinar"].get("timezone", ""))
    return "UTC" if not tz or tz.startswith("FILL_") else tz

def load_steps():
    by_id = {}
    for name in ("email.csv", "whatsapp.csv", "vodex.csv"):
        for r in csv.DictReader(open(os.path.join(HERE, name))):
            by_id.setdefault(r["step_id"], {"row": r, "channels": set()})["channels"].add(r["channel"])
    return by_id

def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def in_window(dt, tz):
    return 8 <= dt.astimezone(tz).hour < 20

def shift_day_level(dt, tz):
    loc = dt.astimezone(tz)
    if loc.hour < 8:
        return datetime.combine(loc.date(), dtime(8, 0), tz)
    if loc.hour >= 20:
        return datetime.combine(loc.date(), dtime(19, 0), tz)
    return dt

def plan(registered, start, tz_name=None):
    """Returns [(step_id, send_time, channels)] sorted by time. channels: tuple of email, whatsapp, call."""
    tz = ZoneInfo(tz_name or webinar_tz())
    steps = load_steps()
    def msg(sid, t):
        ch = []
        if "email" in steps[sid]["channels"]:
            ch.append("email")
        if "whatsapp" in steps[sid]["channels"] and in_window(t, tz):
            ch.append("whatsapp")
        return (sid, t, tuple(ch))
    if registered >= start:
        return [msg("15B-L0", registered)] if registered < start + DURATION else []
    out = [msg("15B-R0", registered)]
    starts = sorted(((sid, int(s["row"]["offset_minutes"])) for sid, s in steps.items()
                     if s["row"]["trigger"].startswith("webinar_start") and s["row"]["channel"] != "vodex_call"),
                    key=lambda x: x[1])
    w1_time = start + timedelta(minutes=-10080)
    r1 = registered + timedelta(minutes=60)
    if registered > w1_time and r1 <= start - timedelta(hours=26):
        out.append(msg("15B-R1", r1))
    for sid, off in starts:
        t = start + timedelta(minutes=off)
        if sid in DAY_LEVEL:
            t = shift_day_level(t, tz)
        if t <= registered:
            continue
        if sid not in EXEMPT_GAP and any(timedelta(0) <= t - prev < GAP for _, prev, _ in out):
            continue
        out.append(msg(sid, t))
    c1 = start + timedelta(minutes=-1320)
    if not in_window(c1, tz):
        loc = c1.astimezone(tz)
        d = loc.date() if loc.hour >= 20 else loc.date() - timedelta(days=1)
        c1 = datetime.combine(d, dtime(19, 30), tz)
    if registered < c1 <= start - timedelta(minutes=180):
        out.append(("15B-C1", c1, ("call",)))
    c2 = start + timedelta(minutes=-15)
    if c2 > registered and in_window(c2, tz):
        out.append(("15B-C2", c2, ("call",)))
    return sorted(out, key=lambda x: x[1])

def ids(p):
    return [s for s, _, _ in p]

def selftest():
    S = parse("2026-11-12T16:00:00Z")  # a Thursday, 16:00 UTC
    def at(**kw):
        return S - timedelta(**kw)
    ALL = ["15B-R0", "15B-W1", "15B-V2", "15B-D3", "15B-V4", "15B-D1", "15B-C1", "15B-H3", "15B-H1", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]
    cases = [
        ("10 days early", at(days=10), "UTC", ALL),
        ("4 days early: catch-up, no W1 or V2", at(days=4), "UTC",
         ["15B-R0", "15B-R1", "15B-D3", "15B-V4", "15B-D1", "15B-C1", "15B-H3", "15B-H1", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]),
        ("25 hours early: no catch-up (under 26h)", at(hours=25), "UTC",
         ["15B-R0", "15B-D1", "15B-C1", "15B-H3", "15B-H1", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]),
        ("24h10m early: D1 within 30 min of R0 is skipped", at(hours=24, minutes=10), "UTC",
         ["15B-R0", "15B-C1", "15B-H3", "15B-H1", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]),
        ("3h10m early: H3 skipped, C1 past", at(hours=3, minutes=10), "UTC",
         ["15B-R0", "15B-H1", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]),
        ("20 min early: M15 kept although 5 min after R0", at(minutes=20), "UTC",
         ["15B-R0", "15B-M15", "15B-C2", "15B-L0", "15B-L10"]),
        ("during the live session: we're live only", S + timedelta(minutes=5), "UTC", ["15B-L0"]),
        ("after the session ended: nothing (fix 1)", S + DURATION + timedelta(minutes=1), "UTC", []),
        ("India registrant, 21:30 IST start: C2 skipped (outside 08 to 20)", at(days=10), "Asia/Kolkata",
         ["15B-R0", "15B-W1", "15B-V2", "15B-D3", "15B-V4", "15B-D1", "15B-C1", "15B-H3", "15B-H1", "15B-M15", "15B-L0", "15B-L10"]),
        ("no timezone: falls back to the webinar timezone", at(days=10), None,
         ids(plan(at(days=10), S, webinar_tz()))),
    ]
    fails = 0
    for name, reg, tz, want in cases:
        got = ids(plan(reg, S, tz))
        ok = got == want
        fails += not ok
        print("%s %s" % ("PASS" if ok else "FAIL", name))
        if not ok:
            print("   want", want, "\n   got ", got)
    # fix 2: WhatsApp window applies to live-day steps too. India: H3 at 18:30 IST keeps WhatsApp,
    # H1 20:30, M15 21:15, L0 21:30, L10 21:40 IST lose WhatsApp but keep email.
    p = {sid: ch for sid, _, ch in plan(at(days=10), S, "Asia/Kolkata")}
    checks = [("H3 18:30 IST keeps WhatsApp", p["15B-H3"] == ("email", "whatsapp"))]
    for sid in ("15B-H1", "15B-M15", "15B-L0", "15B-L10"):
        checks.append(("%s after 20:00 IST: email only, WhatsApp skipped" % sid, p[sid] == ("email",)))
    late = {sid: ch for sid, _, ch in plan(parse("2026-11-10T08:00:00Z"), S, "America/Los_Angeles")}
    checks.append(("R0 at 00:00 PST: WhatsApp skipped and no 15b email (WebinarJam sends the confirmation)", late["15B-R0"] == ()))
    p10 = {sid: ch for sid, _, ch in plan(at(days=10), S, "UTC")}
    checks.append(("R0 in window: WhatsApp only, never a second confirmation email", p10["15B-R0"] == ("whatsapp",)))
    for sid, t, ch in plan(at(days=10), S, "Asia/Kolkata"):
        if "whatsapp" in ch or ch == ("call",):
            checks.append(("%s inside 08:00 to 20:00 IST" % sid, 8 <= t.astimezone(ZoneInfo("Asia/Kolkata")).hour < 20))
    for name, ok in checks:
        fails += not ok
        print("%s %s" % ("PASS" if ok else "FAIL", name))
    print("selftest: %d failures" % fails)
    return fails

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--registered")
    ap.add_argument("--start")
    ap.add_argument("--tz", help="registrant IANA timezone (data.timezone); default: webinar timezone")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    tz = a.tz or webinar_tz()
    for sid, t, ch in plan(parse(a.registered), parse(a.start), tz):
        print(sid, t.astimezone(ZoneInfo(tz)).isoformat(), "+".join(ch))
