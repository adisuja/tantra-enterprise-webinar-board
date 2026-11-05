#!/usr/bin/env python3
"""Builds item 4 from one source: 6 profile markdowns, the Tantra CSVs, note-check.md and the limits block in OVERVIEW.md.

usage: python3 deliverables/04-linkedin-templates/build.py

Adi's decisions of 2026-11-05:
  * Content engagement is the ONLY personalised type: each sender has their own copy, tied to their own posts.
  * InMail, connector and messenger use ONE shared template each, identical for all six senders.
    Only the sender slots differ: [me] (sender's first name), [hosts] ("I host" for Adi, "Adi, our founder, hosts"
    for the others) and the utm_content in [link].
  * Limits per plan (free now, Sales Navigator soon) live in profiles.json.

Copy slots, filled here:
  [first] -> {{firstName}}   [co] -> {{company}}   [topic] -> {{custom.post_topic}}   (Tantra fills these at send time)
  [host] [brand] [min] [qa]  -> brand.host_name, brand.company, webinar.duration_minutes, webinar.qa_minutes
  [when] -> "every Thursday at 10:00 UK time (11:00 in Central Europe)", from webinar.day_of_week, start_time_local, timezone
  [link] -> domains.funnel_domain + domains.paths.registration + UTMs (a {{token}} until funnel_domain is filled)
Merge fields only, no AI personalisation. Exit 1 on any failed check.
"""
import csv, json, re, sys, pathlib, datetime
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONFIG = json.loads((ROOT / "deliverables/_shared/funnel-config.json").read_text())
PJ = json.loads((HERE / "profiles.json").read_text())
PROFILES, PLANS, CEIL, DAYS = PJ["profiles"], PJ["plans"], PJ["tantra_ceilings"], PJ["sending_days_per_week"]

TYPES = ["content_engagement", "inmail", "connector", "messenger"]
SHARED_TYPES = ["inmail", "connector", "messenger"]
UTM_MEDIUM = {"content_engagement": "engagement", "inmail": "inmail", "connector": "connector", "messenger": "messenger"}
TANTRA_ACTIONS = {"visit_profile", "connection_request", "send_message"}   # CHANNEL_ACTIONS.linkedin in Tantra's source
WORST = {"{{firstName}}": 15, "{{company}}": 35, "{{custom.post_topic}}": 40}
BANNED = ["leverage", "unlock", "seamless", "game-changer", "game changer", "supercharge", "fast-paced",
          "end to end", "end-to-end", "engineered system", "delve", "robust", "elevate", "no " + "pitch",
          "nothing to " + "buy", "100% " + "free", "400+ founders", "$100k to $300k", "guarantee",
          "hope all is", "hope things are", "thought of you", "you'd get a lot", "{{custom.company}}"]

V, C, M, I = "visit_profile", "connection_request", "send_message", "inmail"

def step(action, delay, message="", subject="", track=None, when=""):
    return {"action": action, "delay": delay, "message": message.strip(), "subject": subject, "track": track, "when": when}

# =============================================================================================
# SHARED TEMPLATES: one per type, identical for all six senders. Delays are days after the previous step.
# Connection notes go out only on Sales Navigator; free accounts send the request without a note,
# so the first message after acceptance must stand on its own.
# =============================================================================================
SHARED = {
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], could you predict next quarter's booked sales calls at [co] from the numbers you have today? That's the problem I work on. Glad to connect."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Thanks for connecting, [first].

One pattern I see in almost every founder-led company: the problem isn't traffic. It's that nobody can see where a prospect drops out between first touch and a booked call.

Fix that view and the next hire, channel or budget decision gets obvious.

How does [co] track it today?"""),
  step(M, 3, message="""
[first], this is what we take apart live, [when].

[hosts] the session: [min] minutes on the funnel, the RevOps system behind it, the AI that does the busywork and the channels that fill it.

Bring your numbers. You'll leave knowing which stage to fix first.

Save your seat: [link]"""),
  step(M, 4, message="""
This isn't theory, [first].

For Growth Idea, a UK business-coaching group, one webinar reached 99,859 people. 1,990 registered, 321 came live and 25 booked sales calls.

Their first webinar got 30 registrations. Every stage was measured, so every week got better.

The session shows the build: [link]"""),
  step(M, 6, message="""
Last note from me, [first].

If a predictable pipeline is on this year's list for [co], the session runs [when]: [link]

If not, no hard feelings. Good luck with the quarter."""),
 ],
 "messenger": [
  step(M, 0, message="""
[first], quick question: how much of [co]'s pipeline last quarter came from referrals nobody could have planned for?

For most founders I speak with, it's most of it.

[hosts] a live session [when] on building the other kind: a funnel, a RevOps system and AI on the busywork, measured stage by stage. It draws on 10+ years of work with 400+ brands.

[min] minutes. Want a seat? [link]"""),
  step(M, 4, message="""
[first], one number from the session: a UK coaching group went from 30 registrations on their first webinar to 1,990 on their best.

Same team. The difference was measuring every stage and fixing the weakest one each week.

Seat's here if useful: [link]"""),
  step(M, 5, message="""
Last nudge, [first]. It runs every week, so any Thursday works: [link]

And if a quick chat about [co] would help more than a session, just reply here."""),
 ],
 "inmail": [
  step(I, 0, track="inmail", subject="[first], a question about pipeline at [co]", message="""
Hi [first],

Quick question: could you predict next quarter's booked sales calls at [co] today?

Most founders I speak with can't. Leads come from referrals, a good month on ads, a lucky post. Nothing they can measure and repeat.

[hosts] a live session [when] on building the other kind of pipeline: the funnel, the RevOps system behind it and the AI that runs the busywork. It draws on 10+ years of work with 400+ brands.

[min] minutes, including [qa] minutes of Q&A. Save your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="5 days after the InMail, non-repliers only", message="Hi [first], I sent you an InMail last week about building a pipeline you can measure. Connecting either way, as our work overlaps."),
  step(M, 1, track="followup", when="1 day after they accept", message="""
Thanks for connecting, [first]. Here's the session link I mentioned: [link]

It runs [when], so pick whichever week suits you."""),
 ],
}

# =============================================================================================
# CONTENT ENGAGEMENT: personalised per sender, in their own voice, tied to their own post ([topic]).
# Track "2nd/3rd" connects first (no note on a free account), track "1st" messages straight away.
# =============================================================================================
def ce(note, accept, proof, first, nudge):
    return [
        step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
        step(C, 0, track="2nd/3rd", message=note),
        step(M, 1, track="2nd/3rd", when="1 day after they accept", message=accept),
        step(M, 4, track="2nd/3rd", message=proof),
        step(M, 0, track="1st", message=first),
        step(M, 4, track="1st", message=nudge),
    ]

CE = {}
CE["adi"] = ce(
 "Hi [first], you engaged with my post on [topic]. I go much deeper on it in a live session I host every Thursday. Glad to connect.",
 """
Thanks for connecting, [first].

My post on [topic] was one slice. Live, I walk through the whole revenue engine behind it: the funnel, the RevOps system that runs it and the AI that does the busywork.

I run it [when], [min] minutes. Your seat: [link]""",
 """
[first], one example I break down in the session.

For FintechCircle, a London fintech network, outreach grew from 10,000 to 20,046 to 30,000 calendar invites across three episodes. Those three episodes booked 17 sales calls.

I show how it was built, stage by stage: [link]""",
 """
Hi [first], thanks for engaging with my post on [topic].

I unpack the full system behind it live [when]: funnel, RevOps, AI and the channels that feed it. [min] minutes.

Want a seat? [link]""",
 "[first], quick follow-up. If [topic] is on your plate this quarter, Thursday's session shows the full build behind it: [link]")

CE["bharath"] = ce(
 "[first], saw you on my post about [topic]. The stack behind it gets a full walkthrough in a live session every Thursday. Happy to connect.",
 """
Good to be connected, [first].

The post on [topic] showed one piece of the stack. The session shows how it all connects: funnel, CRM, outreach and AI agents, with every stage measured.

[host], our founder, hosts it [when], and the stack I build is part of what he shows. Your seat: [link]""",
 """
[first], a number for scale: across 11 webinars for a UK coaching group, outreach reached 765,105 people and 80 sales calls were booked.

The wiring behind that is in the session: [link]""",
 """
[first], saw you on my post about [topic].

If you want the full stack behind it, [host], our founder, walks through it live [when]: [link]""",
 "[first], if you'd rather see the wiring behind [topic] than read about it, Thursday's session is the place: [link]")

CE["bhaskar"] = ce(
 "Thanks for weighing in on my [topic] post, [first]. Turning content into pipeline gets a full session every Thursday. Would be glad to connect.",
 """
Appreciate the connect, [first].

That post on [topic] was one piece of the system. The session shows the whole path from content to booked call, with a number on every stage.

[host], our founder, hosts it [when]. Your seat: [link]""",
 """
[first], a single episode for a London fintech network went out as 38,138 calendar invites and drew 187 Yes and 221 Maybe RSVPs.

The setup behind it is in the session: [link]""",
 """
Thanks for weighing in on my [topic] post, [first].

[host], our founder, runs a live session [when] on the full path from content to booked call: [link]""",
 "One more thought, [first]: if [topic] matters to your pipeline this quarter, Thursday's session ties it to booked calls. [link]")

CE["nelbin"] = ce(
 "Hi [first], good to see you on my post about [topic]. The process behind it is covered step by step in a session every Thursday. Glad to connect.",
 """
Glad we're connected, [first].

My post on [topic] covered one step. The session covers the whole process: who owns each stage, what gets measured weekly and what the AI handles.

[host], our founder, hosts it [when]. Your seat: [link]""",
 """
[first], a process example from the session.

In one logged experiment for a UK coaching group, a 100,000-invite calendar push aimed for 250 attendees and got 441. Logging it is what made it repeatable.

The full checklist is here: [link]""",
 """
[first], good to see you on my [topic] post.

[host], our founder, runs a live session [when] on building revenue as a repeatable process: [link]""",
 "[first], following up once. Thursday's session turns [topic] into a weekly checklist you can run: [link]")

CE["aquila"] = ce(
 "[first], noticed you on my post about [topic]. The automations behind it are shown live every Thursday. Let's connect.",
 """
Thanks for accepting, [first].

That post on [topic] was a single automation. The session shows the whole chain: invites, reminders, follow-ups and handoffs that run without someone remembering.

[host], our founder, hosts it [when]. Your seat: [link]""",
 """
[first], here's what that looks like at scale: for a UK coaching group we built calendar-invite outreach at 12,000 to 120,000 invites per webinar, plus the reminders and follow-up around it.

The session shows the flow: [link]""",
 """
Hi [first], noticed you on my post about [topic].

[host], our founder, runs a live session [when] on the revenue engine, including the automations I build: [link]""",
 "[first], a last pointer: Thursday's session shows which parts of [topic] to automate first. [link]")

CE["ben"] = ce(
 "Hi [first], appreciate you engaging with my [topic] post. The build behind it is shown in a live session every Thursday. Glad to connect.",
 """
Nice to connect, [first].

My [topic] post was one part of the build. The session covers the rest: pages, forms, tracking and the tests that decide what stays.

[host], our founder, hosts it [when]. Your seat: [link]""",
 """
[first], one test from the session: a long landing page was expected to bring 70 registrations and brought 96.

We only knew because both pages were tracked. The setup is here: [link]""",
 """
[first], appreciate you engaging with my post on [topic].

[host], our founder, runs a live session [when] on the full revenue engine, including the build side I work on: [link]""",
 "[first], last one from me: Thursday's session shows how to test [topic] with real numbers. [link]")

# =============================================================================================
# Config helpers and rendering
# =============================================================================================
def get(path):
    cur = CONFIG
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def is_fill(v):
    return isinstance(v, str) and v.startswith("FILL_")

unresolved, fails = set(), []
names = {p["key"]: p for p in PROFILES}

def when_text():
    day, t, tz, first = get("webinar.day_of_week"), get("webinar.start_time_local"), get("webinar.timezone"), get("webinar.first_date")
    if any(v is None or is_fill(v) for v in (day, t, tz, first)):
        unresolved.add("webinar schedule")
        return "{{webinar.when}}"
    start = datetime.datetime.fromisoformat(f"{first}T{t}").replace(tzinfo=ZoneInfo(tz))
    cet = start.astimezone(ZoneInfo("Europe/Paris")).strftime("%H:%M")
    label = "UK time" if tz == "Europe/London" else tz
    return f"every {day} at {t} {label} ({cet} in Central Europe)"

WHEN = when_text()

def reg_url(profile, ctype):
    dom = get("domains.funnel_domain")
    path = get("domains.paths.registration") or "/"
    q = f"?utm_source=linkedin&utm_medium={UTM_MEDIUM[ctype]}&utm_campaign=enterprise-webinar&utm_content={profile}"
    if is_fill(dom) or not dom:
        unresolved.add("domains.funnel_domain")
        return "{{domains.funnel_domain}}" + path + q
    dom = re.sub(r"^https?://", "", dom).rstrip("/")
    return f"https://{dom}{path}{q}"

def hosts(profile):
    host = get("brand.host_name")
    return "I host" if names[profile]["name"] == host else f"{host}, our founder, hosts"

SLOTS = {"[first]": "{{firstName}}", "[co]": "{{company}}", "[topic]": "{{custom.post_topic}}",
         "[host]": "brand.host_name", "[brand]": "brand.company", "[min]": "webinar.duration_minutes", "[qa]": "webinar.qa_minutes"}

def render(text, profile, ctype):
    text = (text.replace("[link]", reg_url(profile, ctype)).replace("[me]", names[profile]["name"])
                .replace("[hosts]", hosts(profile)).replace("[when]", WHEN))
    for slot, val in SLOTS.items():
        if val.startswith("{{"):
            text = text.replace(slot, val)
        elif slot in text:
            v = get(val)
            if v is None or is_fill(v):
                unresolved.add(val)
                v = "{{" + val + "}}"
            text = text.replace(slot, str(v))
    left = re.findall(r"\[[a-z]+\]", text)
    if left:
        fails.append(f"{profile} {ctype}: unknown slot {left}")
    return text

def worst_len(text):
    for tag, n in WORST.items():
        text = text.replace(tag, "X" * n)
    return len(text)

def sender_neutral(text, profile, ctype):
    """Rendered text with this sender's own slots put back, for the shared-template identity check."""
    t = text.replace(reg_url(profile, ctype), "<LINK>").replace(hosts(profile), "<HOSTS>")
    return re.sub(rf"\b{re.escape(names[profile]['name'])}\b", "<ME>", t)

def norm(text, profile):
    t = text
    for ct in TYPES:
        t = t.replace(reg_url(profile, ct), "<LINK>")
    return re.sub(r"\s+", " ", t.replace(names[profile]["name"], "<ME>")).strip().lower()

def copy_for(k, ctype):
    return CE[k] if ctype == "content_engagement" else SHARED[ctype]

# =============================================================================================
# Build rows and run the copy checks
# =============================================================================================
GROUPS = {"content_engagement": [], "connector": [], "messenger": [], "inmail_step1": [], "inmail_followup": []}
RENDERED = {}           # (profile, ctype) -> list of rendered steps
notes, seen_full, seen_open = [], {}, {}
shared_forms = {t: {} for t in SHARED_TYPES}

assert set(names) == set(CE), f"profiles and content engagement copy differ: {set(names) ^ set(CE)}"
for p in PROFILES:
    k = p["key"]
    for ctype in TYPES:
        counters, out = {}, []
        for s in copy_for(k, ctype):
            if ctype == "inmail":
                ct = "inmail_step1" if s["action"] == I else "inmail_followup"
            elif ctype == "content_engagement":
                ct = "content_engagement_1st" if s["track"] == "1st" else "content_engagement"
            else:
                ct = ctype
            counters[ct] = counters.get(ct, 0) + 1
            msg, subj = render(s["message"], k, ctype), render(s["subject"], k, ctype)
            n = worst_len(msg)
            r = dict(s, r_message=msg, r_subject=subj, n=n, no=counters[ct], ct=ct)
            out.append(r)
            if s["action"] == C:
                notes.append((p["name"], ct, counters[ct], n, ctype in SHARED_TYPES))
                if n >= 300:
                    fails.append(f"{k} {ct} step {counters[ct]}: connection note {n} chars (limit is under 300)")
            if s["action"] == I and (not subj or worst_len(subj) > 200 or n > 1900):
                fails.append(f"{k} {ct}: InMail needs a subject and must fit LinkedIn's limits (subject 200, body 1,900)")
            if s["action"] == M and n > 1000:
                fails.append(f"{k} {ct} step {counters[ct]}: message {n} chars, keep messages short")
            low = (msg + " " + subj).lower()
            fails += [f"{k} {ct} step {counters[ct]}: banned phrase '{b}'" for b in BANNED if b in low]
            if re.search("[\\u2013\\u2014]", msg + subj):
                fails.append(f"{k} {ct} step {counters[ct]}: dash")
            if ctype in SHARED_TYPES:
                key = (ct, counters[ct])
                shared_forms[ctype].setdefault(key, set()).add(sender_neutral(subj + "\n" + msg, k, ctype))
            elif msg:
                full = norm(msg, k)
                for kk, store in ((full, seen_full), (full[:60], seen_open)):
                    other = store.setdefault(kk, k)
                    if other != k:
                        what = "message" if store is seen_full else "opening (first 60 characters)"
                        fails.append(f"{k} {ct} step {counters[ct]}: same content engagement {what} as {other}; each sender needs their own")
            if s["action"] == C:
                rule = "Sales Navigator only: on a free account send the request without a note"
            elif s["action"] == I:
                rule = "Sales Navigator only: off on free accounts"
            elif ctype == "inmail":
                rule = "Sales Navigator only (follows the InMail)"
            else:
                rule = "free and Sales Navigator"
            row = {"profile": k, "campaign_type": ct, "step": counters[ct], "delay_days": s["delay"], "action": s["action"],
                   "subject": subj, "message": msg, "char_count": n if msg else 0, "plan_rule": rule}
            GROUPS["content_engagement" if ct.startswith("content_engagement") else ct].append(row)
        RENDERED[(k, ctype)] = out
        if not any(reg_url(k, ctype) in s["r_message"] for s in out):
            fails.append(f"{k} {ctype}: no registration link")

# Shared templates: after putting the sender slots back, all six senders must read exactly the same.
shared_steps = 0
for ctype, steps in shared_forms.items():
    for (ct, no), forms in steps.items():
        shared_steps += 1
        if len(forms) != 1:
            fails.append(f"{ctype} {ct} step {no}: shared template differs between senders ({len(forms)} versions)")
# Content engagement must stay personal: no sender may reuse another's wording.
ce_msgs = sum(1 for k in names for s in CE[k] if s["message"])

for g, rows in GROUPS.items():
    if g != "inmail_step1":
        bad = [r for r in rows if r["action"] not in TANTRA_ACTIONS]
        if bad:
            fails.append(f"{g}.csv: actions Tantra rejects: {sorted({r['action'] for r in bad})}")

# =============================================================================================
# LIMITS: per LinkedIn account, Monday to Friday. Tantra caps per account, so the account limits are the sums.
# =============================================================================================
def limits(plan):
    d = PLANS[plan]
    cr_day = d["connector_requests"] + d["content_engagement_requests"]
    cr_week_raw = cr_day * DAYS
    cr_week = min(cr_week_raw, CEIL["connection_requests_week"])
    ce_req_week = d["content_engagement_requests"] * DAYS
    msg_day = d["messenger_messages"] + d["content_engagement_messages"] + d["connector_requests"]
    return {
        "connector_day": d["connector_requests"], "connector_week": d["connector_requests"] * DAYS,
        "connector_week_eff": cr_week - ce_req_week,
        "messenger_day": d["messenger_messages"], "messenger_week": d["messenger_messages"] * DAYS,
        "ce_req_day": d["content_engagement_requests"], "ce_req_week": ce_req_week,
        "ce_msg_day": d["content_engagement_messages"], "ce_msg_week": d["content_engagement_messages"] * DAYS,
        "inmail_day": d["inmail"], "inmail_week": d["inmail"] * DAYS,
        "cr_day": cr_day, "cr_week_raw": cr_week_raw, "cr_week": cr_week,
        "msg_day": msg_day, "msg_week": msg_day * DAYS,
        "visits_day": cr_day + d["inmail"], "visits_week": (cr_day + d["inmail"]) * DAYS,
    }

L = {plan: limits(plan) for plan in PLANS}
for plan, x in L.items():
    if x["cr_day"] > CEIL["connection_requests_day"] or x["msg_day"] > CEIL["messages_day"] or x["msg_week"] > CEIL["messages_week"] \
       or x["visits_day"] > CEIL["profile_visits_day"] or x["visits_week"] > CEIL["profile_visits_week"]:
        fails.append(f"{plan}: an account limit is above Tantra's ceiling")
for key in ("connector_requests", "messenger_messages", "content_engagement_requests", "content_engagement_messages"):
    if PLANS["sales_navigator"][key] != 2 * PLANS["free"][key]:
        fails.append(f"sales_navigator {key} is not 2x free (Adi 2026-11-05)")
if PLANS["free"]["inmail"] != 0:
    fails.append("free plan must have no InMail (Adi 2026-11-05)")

def warm(n, f):
    return max(1, int(n * f + 0.5))

def limits_md():
    f, s = L["free"], L["sales_navigator"]
    six = 6
    out = [
     "Per LinkedIn account. Weekly = daily x " + f"{DAYS} sending days (Monday to Friday). Tantra caps per account, not per campaign, so the account limits below are the sums of the campaign numbers. Tantra's ceilings, which can be lowered but never raised: {CEIL['connection_requests_day']} requests a day and {CEIL['connection_requests_week']} a week, {CEIL['messages_day']} messages a day and {CEIL['messages_week']} a week, {CEIL['profile_visits_day']} visits a day and {CEIL['profile_visits_week']} a week.", "",
     "### Per Campaign Type, One Account", "",
     "| Campaign | Free, a day | Free, a week | Sales Navigator, a day | Sales Navigator, a week |", "|---|---|---|---|---|",
     f"| Connector (connection requests) | {f['connector_day']} | {f['connector_day']} x {DAYS} = {f['connector_week']} | {s['connector_day']} | {s['connector_day']} x {DAYS} = {s['connector_week']}, capped to {s['connector_week_eff']} (see below) |",
     f"| Messenger (messages) | {f['messenger_day']} | {f['messenger_day']} x {DAYS} = {f['messenger_week']} | {s['messenger_day']} | {s['messenger_day']} x {DAYS} = {s['messenger_week']} |",
     f"| InMail | none | none | {s['inmail_day']} (our recommendation) | {s['inmail_day']} x {DAYS} = {s['inmail_week']} |",
     f"| Content engagement, connection requests | {f['ce_req_day']} | {f['ce_req_day']} x {DAYS} = {f['ce_req_week']} | {s['ce_req_day']} | {s['ce_req_day']} x {DAYS} = {s['ce_req_week']} |",
     f"| Content engagement, messages | {f['ce_msg_day']} | {f['ce_msg_day']} x {DAYS} = {f['ce_msg_week']} | {s['ce_msg_day']} | {s['ce_msg_day']} x {DAYS} = {s['ce_msg_week']} |", "",
     "### Account Limits To Set In Tantra (Recommended Caps)", "",
     "| Account limit | Free, a day | Free, a week | Sales Navigator, a day | Sales Navigator, a week |", "|---|---|---|---|---|",
     f"| Connection requests (connector + content engagement) | {f['connector_day']} + {f['ce_req_day']} = {f['cr_day']} | {f['cr_day']} x {DAYS} = {f['cr_week']} | {s['connector_day']} + {s['ce_req_day']} = {s['cr_day']} | {s['cr_day']} x {DAYS} = {s['cr_week_raw']}, capped to **{s['cr_week']}** |",
     f"| Messages (messenger + content engagement + connector follow-ups) | {f['messenger_day']} + {f['ce_msg_day']} + {f['connector_day']} = {f['msg_day']} | {f['msg_day']} x {DAYS} = {f['msg_week']} | {s['messenger_day']} + {s['ce_msg_day']} + {s['connector_day']} = {s['msg_day']} | {s['msg_day']} x {DAYS} = {s['msg_week']} |",
     f"| Profile visits (one per request, one per InMail) | {f['visits_day']} | {f['visits_week']} | {s['visits_day']} | {s['visits_week']} |",
     f"| InMail | 0 | 0 | {s['inmail_day']} | {s['inmail_week']} |", "",
     "### All Six Accounts, A Week", "",
     "| Total | Free | Sales Navigator |", "|---|---|---|",
     f"| Connection requests | {f['cr_week']} x {six} = {f['cr_week'] * six} (connector {f['connector_week'] * six}, content engagement {f['ce_req_week'] * six}) | {s['cr_week']} x {six} = {s['cr_week'] * six:,} (connector {s['connector_week_eff'] * six}, content engagement {s['ce_req_week'] * six}) |",
     f"| Messenger messages | {f['messenger_week']} x {six} = {f['messenger_week'] * six} | {s['messenger_week']} x {six} = {s['messenger_week'] * six:,} |",
     f"| Content engagement messages | {f['ce_msg_week']} x {six} = {f['ce_msg_week'] * six} | {s['ce_msg_week']} x {six} = {s['ce_msg_week'] * six} |",
     f"| All messages, at most | {f['msg_week']} x {six} = {f['msg_week'] * six:,} | {s['msg_week']} x {six} = {s['msg_week'] * six:,} |",
     f"| InMail | 0 | {s['inmail_week']} x {six} = {s['inmail_week'] * six} |", "",
     "Notes on the math:", "",
     f"- **Sales Navigator hits Tantra's weekly ceiling.** 2x gives {s['cr_day']} requests a day, {s['cr_week_raw']} a week, but Tantra stops every account at {CEIL['connection_requests_week']} a week. Content engagement keeps its {s['ce_req_week']}, so connector gets {CEIL['connection_requests_week']} minus {s['ce_req_week']} = {s['connector_week_eff']} a week (about {round(s['connector_week_eff'] / DAYS)} a day). {s['cr_day']} a day is also above Tantra's 20 to 30 guidance for Sales Navigator, so step up to it over two weeks (below).",
     f"- **Free matches Tantra's free guidance:** {f['cr_day']} requests a day (guidance 15 to 20, without a note) and {f['cr_week']} a week (guidance up to 100).",
     f"- **Connector follow-ups** are the messages to people who accepted. They are budgeted at one a day per request sent ({f['connector_day']} free, {s['connector_day']} Sales Navigator). If more queue up, Tantra moves them to the next day.",
     f"- **Messenger** sends 3 messages per person, so {f['messenger_day']} messages a day is about {round(f['messenger_day'] / 3)} new people a day in steady state ({round(s['messenger_day'] / 3)} on Sales Navigator).",
     f"- **InMail ({s['inmail_day']} a day) is our recommendation.** {PLANS['sales_navigator']['_inmail']}",
     "- **Connection notes.** Free accounts get about 3 personalised notes a month, so every request from a free account goes without a note. Notes switch on with Sales Navigator.", "",
     "### Warm-Up", "",
     "Free accounts (all six today). Step up only after a clean week: no LinkedIn warning or restriction, and the acceptance rate not falling. On any warning, drop back one week. Withdraw requests still pending after 3 weeks.", "",
     "| Week | Connector | Messenger | Content engagement (requests + messages) | Account: requests a day, messages a day |", "|---|---|---|---|---|",
    ]
    fr = PLANS["free"]
    for w, fac in ((1, 0.5), (2, 0.75), (3, 1.0)):
        cn, me, cr, cm = (warm(fr["connector_requests"], fac), warm(fr["messenger_messages"], fac),
                          warm(fr["content_engagement_requests"], fac), warm(fr["content_engagement_messages"], fac))
        lab = f"{w}" if w < 3 else "3 onwards"
        out.append(f"| {lab} | {cn} | {me} | {cr} + {cm} | {cn + cr}, {me + cm + cn} |")
    sn = PLANS["sales_navigator"]
    mid = {k2: int(fr[k2] * 1.5 + 0.5) for k2 in ("connector_requests", "messenger_messages", "content_engagement_requests", "content_engagement_messages")}
    out += ["",
     f"After the Sales Navigator upgrade, do not jump to 2x: run 1.5x for one clean week (connector {mid['connector_requests']}, messenger {mid['messenger_messages']}, content engagement {mid['content_engagement_requests']} + {mid['content_engagement_messages']}, InMail 5), then the full Sales Navigator numbers (connector {sn['connector_requests']}, messenger {sn['messenger_messages']}, content engagement {sn['content_engagement_requests']} + {sn['content_engagement_messages']}, InMail {sn['inmail']})."]
    return "\n".join(out)

LIMITS_MD = limits_md()

# =============================================================================================
# Write CSVs, note-check.md, OVERVIEW limits block, profile markdowns
# =============================================================================================
cols = ["profile", "campaign_type", "step", "delay_days", "action", "subject", "message", "char_count", "plan_rule"]
(HERE / "csv").mkdir(exist_ok=True)
for old in ("inmail.csv", "inmail_manual_step1.csv"):
    if (HERE / "csv" / old).exists():
        (HERE / "csv" / old).unlink()
for g, rows in GROUPS.items():
    with open(HERE / "csv" / f"{g}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

# One row per note: shared notes are counted once per sender (they render the same length for everyone).
lines = ["# Connection Note Check", "",
         "Generated by build.py. Each note is counted with merge fields at worst-case length "
         f"(firstName {WORST['{{firstName}}']}, company {WORST['{{company}}']}, custom.post_topic {WORST['{{custom.post_topic}}']} characters). "
         "LinkedIn's limit is 300. Notes go out on Sales Navigator only: a free account gets about 3 personalised notes a month (200 characters each), so free accounts send every request without a note.", "",
         "| Profile | Campaign | Step | Template | Worst-case chars | Under 300 | Under 200 |", "|---|---|---|---|---|---|---|"]
for name, ct, no, n, shared in notes:
    lines.append(f"| {name} | {ct} | {no} | {'shared' if shared else 'personal'} | {n} | {'yes' if n < 300 else 'NO'} | {'yes' if n <= 200 else 'no'} |")
lines += ["", f"Result: {sum(1 for x in notes if x[3] < 300)} of {len(notes)} notes under 300 characters; {sum(1 for x in notes if x[3] <= 200)} under 200."]
(HERE / "note-check.md").write_text("\n".join(lines) + "\n")

ov = HERE / "OVERVIEW.md"
if ov.exists():
    text = ov.read_text()
    a, b = "<!-- limits:start (generated by build.py) -->", "<!-- limits:end -->"
    if a in text and b in text:
        text = text.split(a)[0] + a + "\n" + LIMITS_MD + "\n" + b + text.split(b, 1)[1]
        ov.write_text(text)
    else:
        fails.append("OVERVIEW.md has no limits markers")

TITLES = {"content_engagement": "Content Engagement (Personal: Likers and Commenters of My Posts)",
          "inmail": "InMail (Shared Template, Sales Navigator Only)",
          "connector": "Connector (Shared Template)",
          "messenger": "Messenger (Shared Template, 1st-Degree Connections)"}
WHO = {
 "content_engagement": "People who liked or commented on one of this sender's own posts. One campaign per post, started within 24 hours of the post. Split the engager export by degree: 2nd and 3rd degree run the connect track, 1st degree the message track.",
 "inmail": "Prospects in this sender's audience who are not connected and are worth an InMail: Open Profiles first (no credit used), then the best fits on credits. Off until this account is on Sales Navigator. If Tantra shows no InMail step, step 1 is sent by hand in Sales Navigator and, 5 days later, **only the people who did not reply** are imported into the follow-up campaign.",
 "connector": "Cold prospects in this sender's audience (2nd and 3rd degree). Only people who accept get the messages.",
 "messenger": "This sender's own 1st-degree connections who match the audience and are owned by no other sender.",
}
FIELDS = {
 "content_engagement": "`{{firstName}}` and `{{custom.post_topic}}` (a 2 to 6 word phrase for the post, the same value on every row of that post's export). If the test message shows `{{custom.post_topic}}` blank, type the phrase into the step text instead: each post has its own campaign.",
 "inmail": "`{{firstName}}` and `{{company}}`. If step 1 goes out by hand in Sales Navigator, type the first name and company in place of the tags. The sign-off is the sender's name.",
 "connector": "`{{firstName}}` and `{{company}}`.",
 "messenger": "`{{firstName}}` and `{{company}}`.",
}
ACTION_LABEL = {V: "Visit profile", C: "Connection request with note", M: "Message", I: "InMail"}
TRACK = {"1st": "1st degree", "2nd/3rd": "2nd/3rd degree", "followup": "Follow-up", "inmail": "InMail"}
link_note = ("`{{domains.funnel_domain}}` is still FILL_ in funnel-config.json: **do not load these steps into Tantra until it is filled and build.py has run again**, "
             "because Tantra renders an unknown tag as blank text.") if "domains.funnel_domain" in unresolved else "Built from funnel-config.json."

def plan_limit(ctype):
    f, s = L["free"], L["sales_navigator"]
    return {
     "content_engagement": f"Free: {f['ce_req_day']} connection requests and {f['ce_msg_day']} messages a day ({f['ce_req_week']} and {f['ce_msg_week']} a week), requests without a note. Sales Navigator: {s['ce_req_day']} and {s['ce_msg_day']} a day ({s['ce_req_week']} and {s['ce_msg_week']} a week), with the note.",
     "inmail": f"Free: none. Sales Navigator: {s['inmail_day']} a day, {s['inmail_week']} a week (our recommendation; about 2 a day on credits, the rest Open Profiles). The follow-up requests count toward the connection request limit.",
     "connector": f"Free: {f['connector_day']} connection requests a day, {f['connector_week']} a week, without a note. Sales Navigator: {s['connector_day']} a day, with the note; {s['connector_week_eff']} a week under Tantra's {CEIL['connection_requests_week']} a week ceiling.",
     "messenger": f"Free: {f['messenger_day']} messages a day, {f['messenger_week']} a week. Sales Navigator: {s['messenger_day']} a day, {s['messenger_week']} a week.",
    }[ctype]

for p in PROFILES:
    k = p["key"]
    f, s = L["free"], L["sales_navigator"]
    out = [f"# {p['name']}: LinkedIn Outreach Templates", "",
           f"Role: **{p['role']}**. Content engagement voice: {p['voice']}", "",
           "| Field | Value |", "|---|---|",
           f"| LinkedIn URL | {p['linkedin_url']} |",
           f"| Title on LinkedIn | {p['title']} |",
           f"| LinkedIn plan | {p['linkedin_plan']} now; {p['plan_next']} |",
           f"| Audience (only this sender contacts them) | {p['audience']} |",
           f"| UTM code | `utm_content={k}` on every link |", "",
           "Content engagement is written for this sender alone. InMail, connector and messenger are the shared templates, word for word the same for all six senders; only the sender's name and the link's UTM differ.", "",
           "## Account Limits For This Sender", "",
           "Set on the account in Tantra (Tantra caps per account, not per campaign). Full math and warm-up: [OVERVIEW.md](../OVERVIEW.md).", "",
           "| Account limit | Free, a day | Free, a week | Sales Navigator, a day | Sales Navigator, a week |", "|---|---|---|---|---|",
           f"| Connection requests | {f['cr_day']} | {f['cr_week']} | {s['cr_day']} | {s['cr_week']} |",
           f"| Messages | {f['msg_day']} | {f['msg_week']} | {s['msg_day']} | {s['msg_week']} |",
           f"| Profile visits | {f['visits_day']} | {f['visits_week']} | {s['visits_day']} | {s['visits_week']} |",
           f"| InMail | 0 | 0 | {s['inmail_day']} | {s['inmail_week']} |", ""]
    for i, ctype in enumerate(TYPES, 1):
        steps = RENDERED[(k, ctype)]
        out += [f"## Set {i}: {TITLES[ctype]}", "",
                f"**Who:** {WHO[ctype]}", "",
                f"**Personalisation fields:** {FIELDS[ctype]}", "",
                f"**Registration link (the exact text in the copy):** `{reg_url(k, ctype)}`. {link_note}", "",
                f"**Limits:** {plan_limit(ctype)}", "",
                "**Stop rules:** a reply, a registration from any source (CRM `webinar.registered`) or a do-not-contact request removes the person from every LinkedIn campaign the same day.", "",
                "| Track | Step | Wait (days after previous step) | Action | Chars (worst case) |", "|---|---|---|---|---|"]
        for r in steps:
            track = TRACK.get(r["track"], "main")
            when = f" ({r['when']})" if r["when"] else ""
            label = ACTION_LABEL[r["action"]] + (" (no note on free)" if r["action"] == C else "")
            out.append(f"| {track} | {r['no']} | {r['delay']}{when} | {label} | {r['n'] if r['r_message'] else 'n/a'} |")
        out.append("")
        for r in steps:
            if r["action"] == V:
                continue
            prefix = TRACK.get(r["track"], "")
            out += [f"### {prefix + ', ' if prefix else ''}Step {r['no']}: {ACTION_LABEL[r['action']]}", ""]
            if r["action"] == C:
                out += ["Sales Navigator only. On a free account, leave the note empty.", ""]
            if r["r_subject"]:
                out += [f"Subject: `{r['r_subject']}`", ""]
            out += ["```text", r["r_message"], "```", ""]
    (HERE / "profiles").mkdir(exist_ok=True)
    (HERE / "profiles" / f"{k}.md").write_text("\n".join(out))

print(f"sets: {len(PROFILES) * len(TYPES)} ({len(PROFILES)} senders x {len(TYPES)} types)")
print(f"shared templates: {shared_steps} steps across {', '.join(SHARED_TYPES)}, identical for all {len(PROFILES)} senders")
print(f"content engagement: {ce_msgs} personal messages, {len(seen_full)} distinct, {len(seen_open)} distinct openings")
print(f"connection notes: {len(notes)}, longest worst case {max(x[3] for x in notes)} chars, {sum(1 for x in notes if x[3] <= 200)} under 200")
print("csv rows: " + ", ".join(f"{g} {len(r)}" for g, r in GROUPS.items()))
for plan, x in L.items():
    print(f"{plan}: per account {x['cr_day']} requests/day ({x['cr_week']}/week), {x['msg_day']} messages/day ({x['msg_week']}/week), "
          f"{x['inmail_day']} InMail/day; six accounts {x['cr_week'] * 6:,} requests/week, {x['inmail_week'] * 6} InMail/week")
if unresolved:
    print("NOT READY to import: still FILL_ in funnel-config.json: " + ", ".join(sorted(unresolved)))
for fl in fails:
    print("FAIL " + fl)
if fails:
    sys.exit(1)
print("checks: 0 failures")
