#!/usr/bin/env python3
"""The webinar schedule in words, read from funnel-config.json. One source for items 11, 12 and 15b.

python3 schedule.py [YYYY-MM-DD]   prints the strings for that session (default webinar.first_date)

The audience is UK and EU, so every time shows UK time first and the Central European equivalent
(CET in winter, CEST in summer, computed per date, never hardcoded).
"""
import datetime, json, pathlib, sys
from zoneinfo import ZoneInfo

CONFIG = pathlib.Path(__file__).resolve().parent.parent / "_shared" / "funnel-config.json"
EU = ZoneInfo("Europe/Paris")


def cfg():
    return json.loads(CONFIG.read_text())["webinar"]


def is_fill(v):
    return str(v).startswith("FILL_")


def zone_words(tz_name, dt):
    return "UK time" if tz_name == "Europe/London" else dt.tzname()


def session(date_s=None):
    """Every schedule string for one session. Raises ValueError while the schedule is unset."""
    w = cfg()
    for k in ("start_time_local", "timezone", "first_date", "day_of_week"):
        if is_fill(w[k]):
            raise ValueError(f"webinar.{k} is still FILL_ in funnel-config.json")
    d = datetime.date.fromisoformat(date_s or w["first_date"])
    if d.strftime("%A") != w["day_of_week"]:
        raise ValueError(f"{d} is a {d.strftime('%A')}, the webinar runs on {w['day_of_week']}")
    tz = ZoneInfo(w["timezone"])
    h, m = map(int, w["start_time_local"].split(":"))
    start = datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
    end = start + datetime.timedelta(minutes=int(w["duration_minutes"]))
    s_eu, e_eu = start.astimezone(EU), end.astimezone(EU)
    zone = zone_words(w["timezone"], start)
    eu = s_eu.tzname()
    date_words = f"{d.strftime('%A')} {d.day} {d.strftime('%B')} {d.year}"
    return {
        "date": d.isoformat(),
        "date_words": date_words,
        "date_short": f"{d.strftime('%A')} {d.day} {d.strftime('%B')}",
        "day": w["day_of_week"],
        "start": start, "end": end,
        "time": f"{start:%H:%M}",
        "time_eu": f"{s_eu:%H:%M}",
        "time_words": f"{start:%H:%M} {zone} ({s_eu:%H:%M} {eu})",
        "range_words": f"{start:%H:%M} to {end:%H:%M} {zone} ({s_eu:%H:%M} to {e_eu:%H:%M} {eu})",
        "when": f"{date_words}, {start:%H:%M} {zone} ({s_eu:%H:%M} {eu})",
        "weekly": f"every {w['day_of_week']} at {start:%H:%M} {zone} ({s_eu:%H:%M} {eu})",
        "minutes": int(w["duration_minutes"]),
        "timezone": w["timezone"],
    }


if __name__ == "__main__":
    s = session(sys.argv[1] if len(sys.argv) > 1 else None)
    for k, v in s.items():
        print(f"{k}: {v}")
