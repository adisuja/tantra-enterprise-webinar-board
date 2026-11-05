#!/usr/bin/env python3
"""Build the Tantra Enterprise CRM from one schema.

Writes:
  Tantra_Enterprise_CRM_template.xlsx          the sheet template (tabs, dropdowns, formatting, Summary formulas)
  apps-script/Code.gs                          the one file Adi pastes into Apps Script (src/*.gs + generated SCHEMA and SEQUENCES)
  ../18-19-booking/18-sequences-A-to-F.md      the review copy of every sequence, from ../18-19-booking/sequences.json

usage: python3 deliverables/23-crm/build.py
"""
import json
import pathlib
import re

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONFIG = json.loads((ROOT / "deliverables/_shared/funnel-config.json").read_text())
SEQ = json.loads((HERE.parent / "18-19-booking/sequences.json").read_text())

STAGES = ["1 New Lead", "2 Call Booked", "3 Confirmed", "4a Showed", "4b No-Show",
          "5 Proposal Sent", "6 Follow-Up", "7 Closed Won", "8 Closed Lost", "9 Nurture"]

# Tabs per CRM_CONTRACT.md. Column order matters only for the Summary formulas (letters below).
TABS = {
    "Contacts": ["email", "first_name", "last_name", "company", "phone", "whatsapp", "whatsapp_opt_in", "call_opt_in",
                 "newsletter_opt_in", "timezone", "lead_source", "utm_source", "utm_medium", "utm_campaign", "utm_content", "revenue_band", "invest_12m",
                 "main_channel", "bottleneck", "signoff", "hot_lead", "do_not_contact", "no_rebook", "last_reply_at",
                 "created_at", "updated_at"],
    "Webinar": ["key", "email", "webinar_date", "registered_at", "attended", "minutes_in_room", "joined_at", "left_at",
                "segment", "track", "join_url", "retarget_until", "cta_clicked", "cta_ids", "poll_1", "poll_2", "poll_3", "poll_4", "updated_at"],
    "Pipeline": ["deal_id", "email", "first_name", "company", "stage", "lead_source", "setter", "closer", "call_date",
                 "cal_uid", "show_status", "deal_value", "next_follow_up", "next_action", "revenue_band", "invest_12m",
                 "notes", "budget", "objections", "proposal_url", "proposal_sent_at", "lost_reason", "paid_at",
                 "join_link", "stage_changed_at", "created_at", "updated_at",
                 # Call 2 (Proposal Review), CRM_CONTRACT "Call 2": appended so every older column keeps its letter
                 "call2_date", "call2_status", "call2_cal_uid", "call2_join_link"],
    "Events": ["received_at", "kind", "event", "email", "source", "ts", "webinar_date", "data_json", "result"],
    "Sequences": ["id", "created_at", "email", "deal_id", "sequence", "step", "channel", "due_at", "status", "sent_at",
                  "outcome", "assignee", "subject", "text", "note"],
}

LISTS = {
    "stages": STAGES,
    "lead_source": ["Ad", "Organic", "Referral", "Old list", "Inbound DM", "Webinar"],
    "show_status": ["Showed", "No-Show", "Rescheduled"],
    "lost_reason": ["Price", "Timing", "Competitor", "Not a fit"],
    "seq_status": ["pending", "due", "sent", "done", "received", "skipped", "cancelled", "blocked", "failed"],
    "track": ["live", "replay"],
    "outcome": ["answered", "voicemail", "no_answer", "confirmed", "cant_attend"],
    "channel": ["whatsapp", "email", "task", "system"],
    "revenue_band": ["Under $10K a month", "$10K to $25K a month", "$25K to $100K a month",
                     "$100K to $500K a month", "Over $500K a month"],
    "invest_12m": ["yes", "no"],
    "main_channel": ["Referrals", "Outbound (cold email, LinkedIn)", "Paid ads", "Content and organic",
                     "Webinars or events", "Partnerships", "Other"],
    "signoff": ["Me", "Me and a partner or co-founder", "Someone else (I'll bring them)"],
    "segment": ["registered", "attended", "early_leaver", "stayed_to_offer", "no_show"],
    "yes_no": ["TRUE", "FALSE"],
    "call2_status": ["Booked", "Showed", "No-Show", "Rescheduled"],
}

closers = CONFIG["booking"]["closers"]
CALL2 = CONFIG["booking"]["call2"]
CLOSERS = [{"closer_name": c["name"], "closer_email": c["email"], "closer_whatsapp": c["whatsapp"],
            "closer_calcom": c["calcom_username"], "closer_call2_url": CALL2.get(c["name"].lower() + "_url", "")}
           for c in closers]

dom = CONFIG["domains"]
SETTINGS = [
    ("seq_c_rebook", "OFF", "ON runs the playbook's no-show rebook steps (C2 to C4). OFF matches the call description: a missed call is not rescheduled. Decision for Adi."),
    ("dispatch_mode", "queue", "queue: due messages wait in Sequences (status due) for the closer to send from Tantra. tantra: the script sends through the Tantra API (unverified, test first)."),
    ("setter_name", "", "Who confirms new bookings inside 5 minutes. Empty: the assigned closer does it."),
    ("setter_email", "", "Where setter tasks are emailed. Empty: the closer's email."),
    ("alert_emails", "ON", "ON emails the closer a lead brief on every booking and every reply."),
    ("calcom_event_slug", "enterprise-evaluation-call", "Call 1: the round-robin Evaluation Call. Bookings of any event type other than this and calcom_call2_slug are ignored."),
    ("calcom_call2_slug", CALL2["slug_per_closer"].split(" ")[0], "Call 2: the Proposal Review event type slug on each closer's own Cal.com profile. A booking of it sets call2_date and keeps the deal in 5 Proposal Sent."),
    ("default_timezone", CONFIG["webinar"]["timezone"] if not CONFIG["webinar"]["timezone"].startswith("FILL_") else "Europe/London",
     "Europe/London (webinar.timezone): used when Cal.com or the registration sends no timezone, for the closer's side of every alert, and as the sheet's timezone (Set up applies it)."),
    ("whatsapp_start_hour", "8", "WhatsApp sending window start, lead's local time."),
    ("whatsapp_end_hour", "20", "WhatsApp sending window end, lead's local time."),
    ("retarget_cutoff_minute", str(CONFIG["webinar"]["retarget_cutoff_minute"]), "Left before this minute: early_leaver. At or after: stayed_to_offer."),
    ("retarget_days", "42", "Early leavers and no-shows stay in retargeting this many days after the webinar."),
    ("booking_url", CONFIG["booking"]["round_robin_url"].split(" ")[0], "Cal.com round-robin link (item 19). Messages holding FILL_ never send."),
    ("due_diligence_url", (dom["funnel_domain"].split(" ")[0] + dom["paths"]["due_diligence"]), "Due diligence page (item 20)."),
    ("onboarding_link", "FILL_ONBOARDING_BOOKING_LINK", "Onboarding call booking link sent on Closed Won."),
    ("playbook_url", "", "Shared doc link to the speed-to-lead script and checklist, shown in closer alerts. Empty: the line is left out."),
    ("tantra_list_id", "", "dispatch_mode tantra only: an EMPTY Tantra contact list id (campaigns need one)."),
    ("tantra_whatsapp_account_id", "", "dispatch_mode tantra only: Tantra WhatsApp channel account id."),
    ("tantra_email_account_id", "", "dispatch_mode tantra only: Tantra mailbox account id."),
]

INK, PAPER, ACCENT = "0B0D12", "F7F8FB", "6D4AFF"


def col(tab, name):
    return get_column_letter(TABS[tab].index(name) + 1)


def build_xlsx(path):
    wb = Workbook()
    wb.remove(wb.active)
    head_font = Font(bold=True, color="FFFFFF", name="Inter")
    head_fill = PatternFill("solid", fgColor=INK)

    def header(ws, cols):
        ws.append(cols)
        for i, _ in enumerate(cols, 1):
            c = ws.cell(row=1, column=i)
            c.font, c.fill = head_font, head_fill
            ws.column_dimensions[get_column_letter(i)].width = 22 if i > 1 else 30
        ws.freeze_panes = "B2"

    # Summary first so it opens on top
    sm = wb.create_sheet("Summary")
    for name, cols in TABS.items():
        header(wb.create_sheet(name), cols)
    ls = wb.create_sheet("Lists")

    # Lists: one column per list, then closers, then settings
    list_keys = list(LISTS.keys())
    lists_header = list_keys + ["", "closer_name", "closer_email", "closer_whatsapp", "closer_calcom", "closer_call2_url", "",
                                "setting", "value", "setting_note"]
    header(ls, lists_header)
    depth = max(max(len(v) for v in LISTS.values()), len(SETTINGS))
    for r in range(depth):
        row = [LISTS[k][r] if r < len(LISTS[k]) else None for k in list_keys] + [None]
        cl = CLOSERS[r] if r < len(CLOSERS) else None
        row += [cl["closer_name"], cl["closer_email"], cl["closer_whatsapp"], cl["closer_calcom"], cl["closer_call2_url"]] if cl else [None] * 5
        row += [None]
        st = SETTINGS[r] if r < len(SETTINGS) else None
        row += list(st) if st else [None] * 3
        ls.append(row)
    ls.column_dimensions[get_column_letter(len(lists_header))].width = 90

    def lref(key):
        c = get_column_letter(list_keys.index(key) + 1)
        return f"Lists!${c}$2:${c}${len(LISTS[key]) + 1}"

    cn = get_column_letter(len(list_keys) + 2)  # closer_name column
    closer_ref = f"Lists!${cn}$2:${cn}$11"

    def dv(ws, tab, field, ref):
        v = DataValidation(type="list", formula1=ref, allow_blank=True, showErrorMessage=True)
        ws.add_data_validation(v)
        c = col(tab, field)
        v.add(f"{c}2:{c}5000")

    pl = wb["Pipeline"]
    dv(pl, "Pipeline", "stage", lref("stages"))
    dv(pl, "Pipeline", "lead_source", lref("lead_source"))
    dv(pl, "Pipeline", "closer", closer_ref)
    dv(pl, "Pipeline", "setter", closer_ref)
    dv(pl, "Pipeline", "show_status", lref("show_status"))
    dv(pl, "Pipeline", "call2_status", lref("call2_status"))
    dv(pl, "Pipeline", "lost_reason", lref("lost_reason"))
    dv(pl, "Pipeline", "revenue_band", lref("revenue_band"))
    dv(pl, "Pipeline", "invest_12m", lref("invest_12m"))
    ct = wb["Contacts"]
    dv(ct, "Contacts", "lead_source", lref("lead_source"))
    dv(ct, "Contacts", "revenue_band", lref("revenue_band"))
    dv(ct, "Contacts", "invest_12m", lref("invest_12m"))
    dv(ct, "Contacts", "main_channel", lref("main_channel"))
    dv(ct, "Contacts", "signoff", lref("signoff"))
    for f in ("whatsapp_opt_in", "call_opt_in", "newsletter_opt_in", "hot_lead", "do_not_contact", "no_rebook"):
        dv(ct, "Contacts", f, lref("yes_no"))
    sq = wb["Sequences"]
    dv(sq, "Sequences", "status", lref("seq_status"))
    dv(sq, "Sequences", "channel", lref("channel"))
    dv(sq, "Sequences", "outcome", lref("outcome"))
    wb_ = wb["Webinar"]
    dv(wb_, "Webinar", "segment", lref("segment"))
    dv(wb_, "Webinar", "track", lref("track"))

    # Phone numbers stay text, so +44... is never turned into a number
    for ws, tab, fields in ((ct, "Contacts", ("phone", "whatsapp")),):
        for f in fields:
            c = TABS[tab].index(f) + 1
            for r in range(2, 5001):
                ws.cell(row=r, column=c).number_format = "@"
    wcol = len(list_keys) + 4  # closer_whatsapp
    for r in range(2, 12):
        ls.cell(row=r, column=wcol).number_format = "@"

    # Conditional formatting
    st, nf = col("Pipeline", "stage"), col("Pipeline", "next_follow_up")
    fills = {"7 Closed Won": "C8F7D4", "8 Closed Lost": "F9D0D0", "4b No-Show": "FFE3B3", "9 Nurture": "E4E6EB",
             "3 Confirmed": "E2DBFF", "5 Proposal Sent": "D7ECFF"}
    for stage, color in fills.items():
        pl.conditional_formatting.add(f"A2:{get_column_letter(len(TABS['Pipeline']))}5000",
                                      FormulaRule(formula=[f'${st}2="{stage}"'], fill=PatternFill("solid", bgColor=color)))
    pl.conditional_formatting.add(f"{nf}2:{nf}5000", FormulaRule(
        formula=[f'AND(${nf}2<>"",${nf}2<TODAY(),${st}2<>"7 Closed Won",${st}2<>"8 Closed Lost")'],
        fill=PatternFill("solid", bgColor="FF8A8A"), font=Font(bold=True)))
    dn = col("Contacts", "do_not_contact")
    ct.conditional_formatting.add(f"A2:{get_column_letter(len(TABS['Contacts']))}5000", FormulaRule(
        formula=[f"${dn}2=TRUE"], fill=PatternFill("solid", bgColor="D9D9D9"), font=Font(color="808080")))
    ss_ = col("Sequences", "status")
    for val, color in (("due", "FFE3B3"), ("failed", "FF8A8A"), ("blocked", "FF8A8A"), ("sent", "C8F7D4")):
        sq.conditional_formatting.add(f"A2:{get_column_letter(len(TABS['Sequences']))}5000", FormulaRule(
            formula=[f'${ss_}2="{val}"'], fill=PatternFill("solid", bgColor=color)))
    seg = col("Webinar", "segment")
    for val, color in (("stayed_to_offer", "C8F7D4"), ("early_leaver", "FFE3B3"), ("no_show", "E4E6EB")):
        wb_.conditional_formatting.add(f"A2:{get_column_letter(len(TABS['Webinar']))}5000", FormulaRule(
            formula=[f'${seg}2="{val}"'], fill=PatternFill("solid", bgColor=color)))

    # Summary: formulas only
    P = lambda f: f"Pipeline!${col('Pipeline', f)}:${col('Pipeline', f)}"
    W = lambda f: f"Webinar!${col('Webinar', f)}:${col('Webinar', f)}"
    S = lambda f: f"Sequences!${col('Sequences', f)}:${col('Sequences', f)}"
    C = lambda f: f"Contacts!${col('Contacts', f)}:${col('Contacts', f)}"
    title = Font(bold=True, size=16, color=INK, name="Inter")
    h = Font(bold=True, color="FFFFFF", name="Inter")
    hf = PatternFill("solid", fgColor=ACCENT)
    sm["A1"] = "Tantra Enterprise CRM: Pipeline Summary"
    sm["A1"].font = title
    sm["A2"] = "Every number on this tab is a formula over the other tabs. Do not type here."

    def block(r, heads):
        for i, t in enumerate(heads):
            c = sm.cell(row=r, column=i + 1, value=t)
            c.font, c.fill = h, hf

    block(4, ["Stage", "Deals", "Deal value ($)"])
    for i, sname in enumerate(STAGES):
        r = 5 + i
        sm.cell(row=r, column=1, value=sname)
        sm.cell(row=r, column=2, value=f"=COUNTIF({P('stage')},A{r})")
        sm.cell(row=r, column=3, value=f"=SUMIF({P('stage')},A{r},{P('deal_value')})")
    tr = 5 + len(STAGES)
    sm.cell(row=tr, column=1, value="Total").font = Font(bold=True)
    sm.cell(row=tr, column=2, value=f"=SUM(B5:B{tr - 1})")
    sm.cell(row=tr, column=3, value=f"=SUM(C5:C{tr - 1})")

    r0 = tr + 2
    block(r0, ["Rate", "Value", "How it is worked out"])
    rates = [
        ("Calls booked", f'=COUNTIF({P("cal_uid")},"?*")', "Deals with a Cal.com booking"),
        ("Showed", f'=COUNTIF({P("show_status")},"Showed")', "Show status Showed"),
        ("No-Show", f'=COUNTIF({P("show_status")},"No-Show")', "Show status No-Show"),
        ("Show rate", f"=IFERROR(B{r0 + 2}/(B{r0 + 2}+B{r0 + 3}),\"\")", "Showed / (Showed + No-Show)"),
        ("Proposals sent", f"=COUNTA({P('proposal_sent_at')})-1", "Deals with a proposal date"),
        ("Proposal rate", f"=IFERROR(B{r0 + 5}/B{r0 + 2},\"\")", "Proposals / Showed"),
        ("Closed Won", f'=COUNTIF({P("stage")},"7 Closed Won")', "Stage 7"),
        ("Close rate (of shows)", f"=IFERROR(B{r0 + 7}/B{r0 + 2},\"\")", "Won / Showed"),
        ("Close rate (of proposals)", f"=IFERROR(B{r0 + 7}/B{r0 + 5},\"\")", "Won / Proposals"),
        ("Won value ($)", f'=SUMIF({P("stage")},"7 Closed Won",{P("deal_value")})', "Deal value of stage 7"),
        ("Overdue follow-ups", f'=COUNTIFS({P("next_follow_up")},"<"&TODAY(),{P("stage")},"<>7 Closed Won",{P("stage")},"<>8 Closed Lost")', "Next follow-up date in the past, deal open"),
        # Call 2 (Proposal Review)
        ("Call 2 booked", f'=COUNTIF({P("call2_status")},"?*")', "Deals with a Call 2 status (a cancelled Call 2 clears it)"),
        ("Call 2 showed", f'=COUNTIF({P("call2_status")},"Showed")', "call2_status Showed"),
        ("Call 2 no-show", f'=COUNTIF({P("call2_status")},"No-Show")', "call2_status No-Show"),
        ("Call 2 show rate", f"=IFERROR(B{r0 + 13}/(B{r0 + 13}+B{r0 + 14}),\"\")", "Call 2 Showed / (Showed + No-Show)"),
        ("Close rate (of Call 2 shows)", f'=IFERROR(COUNTIFS({P("stage")},"7 Closed Won",{P("call2_status")},"Showed")/B{r0 + 13},"")', "Won after a Call 2 / Call 2 Showed"),
    ]
    for i, (a, b, c) in enumerate(rates):
        sm.cell(row=r0 + 1 + i, column=1, value=a)
        sm.cell(row=r0 + 1 + i, column=2, value=b)
        sm.cell(row=r0 + 1 + i, column=3, value=c)
    for rr in (r0 + 4, r0 + 6, r0 + 8, r0 + 9, r0 + 15, r0 + 16):
        sm.cell(row=rr, column=2).number_format = "0.0%"

    r1 = r0 + len(rates) + 2
    block(r1, ["Closer", "Booked", "Showed", "Proposals", "Won", "Won value ($)"])
    for i in range(len(CLOSERS)):
        r = r1 + 1 + i
        sm.cell(row=r, column=1, value=f"=Lists!{cn}{2 + i}")
        sm.cell(row=r, column=2, value=f'=COUNTIFS({P("closer")},A{r},{P("cal_uid")},"?*")')
        sm.cell(row=r, column=3, value=f'=COUNTIFS({P("closer")},A{r},{P("show_status")},"Showed")')
        sm.cell(row=r, column=4, value=f'=COUNTIFS({P("closer")},A{r},{P("proposal_url")},"?*")')
        sm.cell(row=r, column=5, value=f'=COUNTIFS({P("closer")},A{r},{P("stage")},"7 Closed Won")')
        sm.cell(row=r, column=6, value=f'=SUMIFS({P("deal_value")},{P("closer")},A{r},{P("stage")},"7 Closed Won")')

    r2 = r1 + len(CLOSERS) + 2
    block(r2, ["Webinar segment", "People", "Note"])
    segs = [
        ("Webinar rows", f"=COUNTA({W('key')})-1", "One row per email per webinar date"),
        ("Attended", f"=COUNTIF({W('attended')},TRUE)", "minutes_in_room > 0"),
        ("Stayed to offer", f'=COUNTIF({W("segment")},"stayed_to_offer")', "In the room at minute 25 or later"),
        ("Early leaver", f'=COUNTIF({W("segment")},"early_leaver")', "Left before minute 25"),
        ("No-show", f'=COUNTIF({W("segment")},"no_show")', "Registered, never joined"),
        ("In retargeting today", f'=COUNTIF({W("retarget_until")},">="&TODAY())', "retarget_until on or after today"),
        ("Clicked the offer", f"=COUNTIF({W('cta_clicked')},TRUE)", "Hot leads"),
    ]
    for i, (a, b, c) in enumerate(segs):
        sm.cell(row=r2 + 1 + i, column=1, value=a)
        sm.cell(row=r2 + 1 + i, column=2, value=b)
        sm.cell(row=r2 + 1 + i, column=3, value=c)

    r3 = r2 + len(segs) + 2
    block(r3, ["Work queue", "Count", "Where"])
    work = [
        ("Rep tasks open", f'=COUNTIFS({S("channel")},"task",{S("status")},"due")', "Sequences: channel task, status due"),
        ("Messages waiting to send", f'=COUNTIFS({S("channel")},"<>task",{S("channel")},"<>system",{S("status")},"due")', "Sequences: status due (queue mode)"),
        ("Messages blocked", f'=COUNTIF({S("status")},"blocked")', "A FILL_ setting is missing: see the note column"),
        ("Do Not Contact", f"=COUNTIF({C('do_not_contact')},TRUE)", "Contacts tagged STOP"),
    ]
    for i, (a, b, c) in enumerate(work):
        sm.cell(row=r3 + 1 + i, column=1, value=a)
        sm.cell(row=r3 + 1 + i, column=2, value=b)
        sm.cell(row=r3 + 1 + i, column=3, value=c)
    sm.column_dimensions["A"].width = 30
    sm.column_dimensions["B"].width = 16
    sm.column_dimensions["C"].width = 48
    for c in "DEF":
        sm.column_dimensions[c].width = 16
    for row in sm.iter_rows():
        for c in row:
            if c.alignment is None or not c.alignment.wrap_text:
                c.alignment = Alignment(vertical="center")
    wb.save(path)


def build_gs():
    src = HERE / "apps-script/src"
    schema = {"tabs": TABS, "stages": STAGES, "lists": LISTS, "closers": CLOSERS,
              "settings": [{"setting": a, "value": b, "setting_note": c} for a, b, c in SETTINGS]}
    seqs = {s["id"]: {k: v for k, v in s.items()} for s in SEQ["sequences"]}
    parts = [
        "/* Tantra Enterprise CRM: web app (doPost), follow-up runner, WebinarJam import and sheet menu.\n"
        " * Generated by deliverables/23-crm/build.py from apps-script/src/*.gs, the CRM schema and\n"
        " * deliverables/18-19-booking/sequences.json. Paste this whole file into Extensions, Apps Script, Code.gs.\n"
        " * Edit the sources, not this file. */\n",
        "var SCHEMA = " + json.dumps(schema, indent=1) + ";\n",
        "var SEQUENCES = " + json.dumps(seqs, indent=1) + ";\n",
    ]
    for f in sorted(src.glob("*.gs")):
        parts.append(f"\n/* ===== {f.name} ===== */\n" + f.read_text())
    (HERE / "apps-script/Code.gs").write_text("\n".join(parts))


def human_offset(step):
    m = step["minutes"]
    if step["from"] == "call_start":
        if m < 0:
            m = -m
            return (f"{m // 1440} day before the call" if m % 1440 == 0 and m // 1440 == 1 else
                    f"{m // 60} hours before the call" if m % 60 == 0 else f"{m} minutes before the call")
        return f"{m} minutes after the call starts"
    if m == 0:
        return "Instant"
    if m % 1440 == 0:
        d = m // 1440
        return f"+{d} day" + ("s" if d > 1 else "")
    if m % 60 == 0:
        return f"+{m // 60} hour" + ("s" if m // 60 > 1 else "")
    if m > 1440:
        return f"+{m // 1440} days {m % 1440 // 60} hours"
    return f"+{m} minutes"


def build_md():
    out = ["# Sequences A to F, Nurture, Won and Rep Tasks",
           "",
           "Generated by `deliverables/23-crm/build.py` from [sequences.json](sequences.json). Edit the JSON, then run the build: the CRM runner sends exactly this text.",
           "",
           "Offer: Tantra Enterprise, $9,999. Call 1: 30-minute Enterprise Evaluation Call on Cal.com with Conor or Scott (round robin). Promise: a written proposal within one business day of the call, carrying the closer's Call 2 link. Call 2: 30-minute Proposal Review with the same closer, where the decision is made (Adi, 2026-11-05). WhatsApp replaces SMS everywhere.",
           "",
           "## Rules for Every Sequence",
           ""]
    for k, v in SEQ["rules"].items():
        out.append(f"- **{k.replace('_', ' ').capitalize()}:** {v}")
    out += ["", "## Merge Fields", "", "| Field | Filled from |", "| --- | --- |"]
    for k, v in SEQ["merge_fields"].items():
        out.append(f"| `{{{{{k}}}}}` | {v} |")
    for s in SEQ["sequences"]:
        out += ["", f"## {s['id']}: {s['name']}", "",
                f"- **Trigger:** `{s['trigger']}`",
                f"- **Runs while the deal is in:** {', '.join(s['valid_stages'])}",
                f"- **Stops on a reply:** {'yes' if s['stops_on_reply'] else 'no (booking logistics)'}"]
        if s.get("call") == 2:
            out.append("- **Call:** Call 2, the Proposal Review: \"before the call\" timings key off `call2_date`")
        if s.get("switch_note"):
            out.append(f"- **Switch:** {s['switch_note']}")
        out += ["", "| Step | When | Channel | Message |", "| --- | --- | --- | --- |"]
        for st in s["steps"]:
            flags = []
            if st.get("switch"):
                flags.append(f"only when `{st['switch']}` is ON")
            if st.get("expires_at_call"):
                flags.append("skipped if it would land after the call starts")
            if st.get("expires_minutes"):
                flags.append(f"skipped if more than {st['expires_minutes']} minutes late")
            if st.get("repeat_minutes"):
                flags.append(f"repeats every {st['repeat_minutes'] // 1440} days")
            if st.get("skip_if"):
                flags.append(f"skipped when the contact is flagged `{st['skip_if']}`")
            if st.get("lead_hours"):
                flags.append("waits for 08:00 to 20:00 lead time")
            if st.get("assignee"):
                flags.append(f"assigned to the {st['assignee']}")
            body = st["text"]
            if st.get("subject"):
                body = f"**Subject: {st['subject']}**\n\n{body}"
            if st.get("text_if_confirmed"):
                body += f"\n\n*If already confirmed:* {st['text_if_confirmed']}"
            cell = body.replace("|", "\\|").replace("\n", "<br>")
            when = human_offset(st) + (f" ({'; '.join(flags)})" if flags else "")
            out.append(f"| {st['id']} | {when} | {st['channel']} | {cell} |")
    (HERE.parent / "18-19-booking/18-sequences-A-to-F.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    build_xlsx(HERE / "Tantra_Enterprise_CRM_template.xlsx")
    build_gs()
    build_md()
    print("built: Tantra_Enterprise_CRM_template.xlsx, apps-script/Code.gs, ../18-19-booking/18-sequences-A-to-F.md")
