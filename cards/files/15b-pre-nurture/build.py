#!/usr/bin/env python3
"""15b pre-webinar nurture: the one source of copy and timing.

Run:  python3 deliverables/15b-pre-nurture/build.py
Writes email.csv, whatsapp.csv, vodex.csv, emails/*.html, emails/index.html and COPY.md.
[[token]] = a fact read from funnel-config.json at build time. {{field}} = a merge field the
sending tool fills per registrant (see VARIABLES in nurture_lib.py and README.md).
Offsets are minutes from the anchor: webinar_start (negative = before) or registration.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nurture_lib as L

ALL = "every registrant (email); whatsapp_opt_in = true (WhatsApp)"
LIVE = ALL + "; skipped if tagged cant_make_it"
STOP = "Reply STOP to opt out."

STEPS = [
dict(step_id="15B-R0", title="Registration confirmation", anchor="registration", offset=0,
     template="tew_confirm",
     trigger="whatsapp_opt_in = true; sent within 1 minute of webinar.registered. No 15b email: WebinarJam already sends the confirmation email with the personal join link (item 17), so nobody gets two",
     whatsapp="Hi {{first_name}}, it's [[host]] from [[company]]. Your seat for my live session is saved for {{webinar_when_local}}.\n\nYour personal join link: {{join_url}}\n\nReply CAL and I'll send a link to add it to your calendar. " + STOP),

dict(step_id="15B-R1", title="Catch-up: the four videos (late registrants only)", anchor="registration", offset=60,
     template="tew_catchup_videos",
     trigger=ALL + "; only if registered after webinar_start minus 10080 min (missed 15B-W1) and this send lands at least 26 hours before the start",
     email=dict(
        subject="Start here: 4 short videos before {{webinar_date_local}}",
        preheader="You missed my first emails. Here's the short version.",
        eyebrow="Before we go live",
        headline="Four Short Videos to Watch Before We Go Live",
        paras=[
          "Hi {{first_name}},",
          "You registered close to the date, so you missed my first emails. Here's the short version.",
          "Before {{webinar_date_local}}, watch the four videos on this page:",
          "1. **Funnels.** How the funnel you just came through is built.\n2. **RevOps OS.** What runs after someone says yes.\n3. **Traffic Channels.** Where the right people come from, and how [[company]] runs the outreach.\n4. **Bonuses.** What I'll cover at the end of the session.",
          "Start with number one today.",
        ],
        cta=("Watch the Four Videos", "watch_url"),
     ),
     whatsapp="Hi {{first_name}}, it's [[host]]. Before {{webinar_date_local}}, watch the four short videos on this page: funnels, the RevOps OS, traffic channels and the bonuses.\n\n{{watch_url}}\n\nStart with number one today. " + STOP),

dict(step_id="15B-W1", title="One week out + video 1 (Funnels)", anchor="webinar_start", offset=-10080,
     template="tew_week_video1", trigger=ALL,
     email=dict(
        subject="One week out: you're inside the funnel I'll teach",
        preheader="Video 1 takes it apart, step by step.",
        eyebrow="One week to go",
        headline="You're Already Inside the Funnel I'll Teach",
        paras=[
          "Hi {{first_name}},",
          "Quick question. How did you end up registered for this session?",
          "Something reached you. A page made you a promise. A form took your details. And now this email lands exactly one week before we go live.",
          "That's a funnel. You're standing inside it.",
          "Video 1 takes it apart, step by step: what reached you, what the page had to say, and what happens next. Watch it before {{webinar_date_local}} and you'll see every piece I build on in the live session.",
        ],
        cta=("Watch Video 1: Funnels", "video_funnels_url"),
        ps="We go live {{webinar_date_local}} at {{webinar_time_local}}. Your join link stays the same.",
     ),
     whatsapp="Hi {{first_name}}, it's [[host]]. We go live in one week, on {{webinar_date_local}}.\n\nBefore then, watch video 1. It takes apart the funnel you just came through, step by step: {{video_funnels_url}}\n\n" + STOP),

dict(step_id="15B-V2", title="Video 2 (RevOps OS)", anchor="webinar_start", offset=-7200,
     template="tew_video2", trigger=ALL,
     email=dict(
        subject="Video 2: where pipelines go quiet",
        preheader="Most revenue leaks after the yes, not before it.",
        eyebrow="Video 2 of 4",
        headline="Most Revenue Leaks After the Yes",
        paras=[
          "Hi {{first_name}},",
          "Here's where most teams lose money. Not at the top, where everybody is looking. After the yes.",
          "A lead registers and nobody reminds them. A call gets booked and nobody confirms it. A proposal goes out and nobody follows up.",
          "Each gap looks small. Together, they're where your pipeline goes quiet.",
          "Video 2 shows the RevOps OS: the CRM stages, the follow-ups and the triggers that close those gaps without someone chasing every lead by hand.",
        ],
        cta=("Watch Video 2: RevOps OS", "video_revops_os_url"),
     ),
     whatsapp="Hi {{first_name}}, video 2 is up. It covers what happens after someone says yes: the reminders, follow-ups and CRM steps where most pipelines leak.\n\n{{video_revops_os_url}}\n\n" + STOP),

dict(step_id="15B-D3", title="Three days out + video 3 (Traffic Channels)", anchor="webinar_start", offset=-4320,
     template="tew_3days_video3", trigger=ALL, wa_category="Marketing",
     email=dict(
        subject="3 days out: where 1,990 registrations came from",
        preheader="Most webinars don't have a content problem. They have a reach problem.",
        eyebrow="Three days to go",
        headline="Where 1,990 Registrations Came From",
        paras=[
          "Hi {{first_name}},",
          "We go live in three days, on {{webinar_date_local}} at {{webinar_time_local}}.",
          "Most founders I talk to think their webinar has a content problem. Usually it has a reach problem. Too few of the right people ever hear about it.",
          "Here's one example from our work with Growth Idea, a UK business-coaching group. Their best webinar reached 99,859 people, and 98,000 of them came from calendar invites. That one session got 1,990 registrations, 321 people live and 25 sales calls.",
          "Video 3 shows the traffic channels behind numbers like that, and how [[company]] runs the outreach for each one.",
        ],
        cta=("Watch Video 3: Traffic Channels", "video_traffic_channels_url"),
     ),
     whatsapp="Hi {{first_name}}, three days to go: {{webinar_date_local}} at {{webinar_time_local}}.\n\nVideo 3 is up. It shows the traffic channels behind one client webinar that reached 99,859 people and got 1,990 registrations: {{video_traffic_channels_url}}\n\n" + STOP),

dict(step_id="15B-V4", title="Video 4 (Bonuses)", anchor="webinar_start", offset=-2880,
     template="tew_video4", trigger=ALL,
     email=dict(
        subject="Video 4 of 4, then we go live",
        preheader="The last video before the session.",
        eyebrow="Video 4 of 4",
        headline="The Last Video Before We Go Live",
        paras=[
          "Hi {{first_name}},",
          "Two days to go.",
          "You've seen how the funnel works, what runs after the yes, and where the traffic comes from. Video 4 is the last one. It covers the bonuses, so nothing at the end of the session comes as a surprise.",
          "Skipped one of the first three? All four are on the same page.",
        ],
        cta=("Watch Video 4: Bonuses", "video_bonuses_url"),
     ),
     whatsapp="Hi {{first_name}}, two days to go. Video 4 of 4 is up and covers the bonuses. All four videos are on the same page: {{video_bonuses_url}}\n\n" + STOP),

dict(step_id="15B-D1", title="One day out", anchor="webinar_start", offset=-1440,
     template="tew_1day", trigger=LIVE,
     email=dict(
        subject="Tomorrow at {{webinar_time_local}}: bring two things",
        preheader="Your rough lead numbers and one question.",
        eyebrow="Live tomorrow",
        headline="We're Live Tomorrow. Bring Two Things",
        paras=[
          "Hi {{first_name}},",
          "Tomorrow, {{webinar_date_local}} at {{webinar_time_local}}, we go live.",
          "Two things make the hour worth it:",
          "1. **Your numbers.** Roughly how many leads you get a month, and how many turn into calls. Rough is fine.\n2. **One question.** The last [[qa_minutes]] minutes are open Q&A. Bring the question you'd ask if you had me for five minutes.",
          "Here's how the hour runs. [[teach_minutes]] minutes on the system: funnels, the RevOps OS and traffic. In that time I also show how we build it with companies that want it done with them. Then your questions.",
        ],
        cta=("Open My Join Link", "join_url"),
        ps="Can't make it after all? Reply to this email and I'll send you the recording.",
     ),
     whatsapp="Hi {{first_name}}, it's [[host]]. We go live tomorrow, {{webinar_date_local}} at {{webinar_time_local}}.\n\nBring your rough lead numbers and one question for the Q&A.\n\nYour join link: {{join_url}}\n\nReply CANT if you can't make it. " + STOP),

dict(step_id="15B-H3", title="Three hours before", anchor="webinar_start", offset=-180,
     template="tew_3hours", trigger=LIVE,
     email=dict(
        subject="Today at {{webinar_time_local}}: your join link",
        preheader="Block the full [[duration]] minutes if you can.",
        eyebrow="Today",
        headline="We Go Live in Three Hours",
        paras=[
          "Hi {{first_name}},",
          "Three hours from now, at {{webinar_time_local}}, we go live.",
          "Block the full [[duration]] minutes if you can. The system comes first, then how we build it with your team, then Q&A. Leave early and you miss the part that answers \"so how do I actually do this?\"",
        ],
        cta=("Open My Join Link", "join_url"),
     ),
     whatsapp="Hi {{first_name}}, we go live today at {{webinar_time_local}}, three hours from now. Block the full [[duration]] minutes if you can.\n\nYour join link: {{join_url}}\n\n" + STOP),

dict(step_id="15B-H1", title="One hour before", anchor="webinar_start", offset=-60,
     template="tew_1hour", trigger=LIVE,
     email=dict(
        subject="One hour to go",
        preheader="A laptop works best: I share my screen.",
        eyebrow="One hour",
        headline="One Hour to Go",
        paras=[
          "Hi {{first_name}},",
          "We start in one hour, at {{webinar_time_local}}.",
          "Join from a laptop if you can. I share my screen the whole time, and the details are easier to see on a bigger screen.",
        ],
        cta=("Open My Join Link", "join_url"),
     ),
     whatsapp="Hi {{first_name}}, we start in one hour, at {{webinar_time_local}}. A laptop works best because I share my screen.\n\nYour join link: {{join_url}}\n\n" + STOP),

dict(step_id="15B-M15", title="Fifteen minutes before", anchor="webinar_start", offset=-15,
     template="tew_15min", trigger=LIVE,
     email=dict(
        subject="Starting in 15 minutes",
        preheader="The room is open.",
        eyebrow="15 minutes",
        headline="The Room Is Open",
        paras=["Hi {{first_name}},", "The room is open. We start in 15 minutes."],
        cta=("Join Now", "join_url"),
     ),
     whatsapp="Hi {{first_name}}, the room is open and we start in 15 minutes.\n\nJoin here: {{join_url}}\n\n" + STOP),

dict(step_id="15B-L0", title="Live now", anchor="webinar_start", offset=0,
     template="tew_live", trigger=LIVE + "; not yet in the room (WebinarJam live attendance) if that signal is available",
     email=dict(
        subject="We're live",
        preheader="Come in now and you'll catch the start.",
        eyebrow="Live now",
        headline="We're Live Now",
        paras=["Hi {{first_name}},", "We just went live. Come in now and you'll catch the start."],
        cta=("Join the Session", "join_url"),
     ),
     whatsapp="Hi {{first_name}}, we're live now. Come in and you'll catch the start.\n\nJoin here: {{join_url}}\n\n" + STOP),

dict(step_id="15B-L10", title="You're late, join now (+10 minutes)", anchor="webinar_start", offset=10,
     template="tew_late", trigger=LIVE + "; only registrants not in the room at +10 min (WebinarJam live attendance); without that signal, every registrant, and the copy covers people already in",
     email=dict(
        subject="We started 10 minutes ago. There's still time",
        preheader="You've missed the warm-up, not the system.",
        eyebrow="Started 10 minutes ago",
        headline="You're Late, but Not Too Late",
        paras=[
          "Hi {{first_name}},",
          "We started 10 minutes ago and I haven't seen you in the room yet.",
          "You've missed the warm-up, not the system. The funnel breakdown and the build come next, and the Q&A is at the end.",
        ],
        cta=("Join Now", "join_url"),
        ps="Already in the room? Ignore this one.",
     ),
     whatsapp="Hi {{first_name}}, we started 10 minutes ago. You haven't missed the main part yet.\n\nJoin now: {{join_url}}\n\nAlready in? Ignore this. " + STOP),

dict(step_id="15B-X1", title="Can't make it (reply or call outcome)", anchor="event:quick_reply_cant_or_call_cant_attend", offset=0,
     template="tew_cant_make_it", wa_category="Marketing",
     trigger="contact.quick_reply keyword CANT, an email reply to 15B-D1 saying they can't come, or a Vodex call with outcome cant_attend; sets track to replay (CRM_CONTRACT), which stops 15B-D1 to 15B-L10 and both calls",
     email=dict(
        subject="No problem. Here's what happens next",
        preheader="I'll send you the recording after the session.",
        eyebrow="Thanks for telling me",
        headline="Can't Make It Live? Here's the Plan",
        paras=[
          "Hi {{first_name}},",
          "Thanks for letting me know. I'll send you the recording after the session, so keep an eye on your inbox.",
          "If you'd rather skip ahead, book a [[call_minutes]]-minute [[call_title]] with my team. We look at your funnel with you, and if it's a fit you get a written proposal within one business day.",
        ],
        cta=("Book an Evaluation Call", "booking_url"),
     ),
     whatsapp="Thanks for letting me know, {{first_name}}. I'll send you the recording after the session.\n\nIf you'd rather talk now, book a [[call_minutes]]-minute evaluation call with my team: {{booking_url}}\n\n" + STOP),

dict(step_id="15B-X2", title="Calendar link resend (reply or call outcome)", anchor="event:reply_cal_or_call_add_to_calendar", offset=0,
     template="tew_calendar_link",
     trigger="contact.quick_reply keyword CAL, or a Vodex call where the person asked for the calendar link",
     email=dict(
        subject="Your calendar link for {{webinar_date_local}}",
        preheader="One click adds the session.",
        eyebrow="Calendar",
        headline="Add the Session to Your Calendar",
        paras=["Hi {{first_name}},", "Here's your calendar link. One click adds {{webinar_title}} on {{webinar_date_local}} at {{webinar_time_local}}."],
        cta=("Add It to My Calendar", "calendar_url"),
     ),
     whatsapp="Here's your calendar link, {{first_name}}. One tap adds the live session to your calendar: {{calendar_url}}\n\n" + STOP),
]

CALLS = [
 {"step_id": "15B-C1", "trigger": "webinar_start | call_opt_in = true, valid phone, track still pre (no CANT), has opened none of the 15b emails and not replied on WhatsApp; inside 08:00 to 20:00 in the registrant's timezone, else the latest in-window time before webinar_start minus 180; max 1 attempt",
  "offset_minutes": -1320, "channel": "vodex_call", "template_name": "tew_call_day_before",
  "subject": "", "variables": "first_name; webinar_title; webinar_time_local"},
 {"step_id": "15B-C2", "trigger": "webinar_start | call_opt_in = true, valid phone, invest_12m is $10,000 or more (registration answer), track still pre (no CANT, no cant_attend outcome), not opted out; only inside 08:00 to 20:00 local, else skipped; max 1 attempt",
  "offset_minutes": -15, "channel": "vodex_call", "template_name": "tew_call_high_intent",
  "subject": "", "variables": "first_name; webinar_time_local"},
]
CALL_BODIES = {
 "15B-C1": "Script A (vodex/VODEX_CALL_SCRIPT.md). Greeting: Hi, is this {{first_name}}? This is [[company]]'s automated assistant, calling for [[host]] about the live session you registered for. It starts tomorrow at {{webinar_time_local}}. You can say stop at any time. Can you still make it? Voicemail: Hi {{first_name}}, this is [[company]]'s automated assistant calling for [[host]]. Just a reminder that {{webinar_title}} starts tomorrow at {{webinar_time_local}}. Your join link is in your email and on WhatsApp. To stop these calls, reply STOP to any of [[host]]'s emails or WhatsApp messages. Thanks.",
 "15B-C2": "Script B (vodex/VODEX_CALL_SCRIPT.md). Greeting: Hi {{first_name}}, this is [[company]]'s automated assistant calling for [[host]]. The live session starts in 15 minutes and the room is already open. You can say stop at any time. Can you make it? Voicemail: Hi {{first_name}}, this is [[company]]'s automated assistant calling for [[host]]. The live session starts in 15 minutes and the room is open. Your join link is in your email and on WhatsApp. To stop these calls, reply STOP to any of [[host]]'s emails or WhatsApp messages.",
}

def main():
    calls = []
    for c in CALLS:
        row = dict(c)
        row["body"] = L.resolve(CALL_BODIES[c["step_id"]])
        calls.append(row)
    problems, _ = L.build(STEPS, HERE, "15B", footer_reason="You're getting this because you registered for {{webinar_title}}.",
                          gallery_title="15b Pre-Webinar Emails", call_rows=calls)
    for c in calls:
        problems += L.check_text(c["step_id"], c["body"])
    for p in problems:
        print("PROBLEM", p)
    print("15b build: %d steps, %d problems" % (len(STEPS), len(problems)))
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
