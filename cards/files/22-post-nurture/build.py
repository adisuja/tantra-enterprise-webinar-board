#!/usr/bin/env python3
"""22 post-webinar nurture: the one source of copy and timing for the three 14-day tracks.

Run:  python3 deliverables/22-post-nurture/build.py
Writes email.csv, whatsapp.csv, emails/*.html, emails/index.html and COPY.md.
Uses the 15b builder (deliverables/15b-pre-nurture/nurture_lib.py). Offsets are minutes from
webinar start (Thursday 10:00 UK). Day-level steps land on weekdays only, at 10:00 UK; days 7 and
14 are the next Thursdays, so they go at 14:00 UK, after that day's live session. Every message carries {{booking_url}} and the recording page.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "15b-pre-nurture"))
import nurture_lib as L

STOP = "Reply STOP to opt out."
EXIT = "; stops on booking.created, contact.replied, contact.opted_out, deal.won or deal.lost"
SEG = {
    "A": "segment stayed_to_offer (attended, minutes_in_room >= [[cutoff]])",
    "B": "segment early_leaver (attended, minutes_in_room under [[cutoff]])",
    "C": "segment no_show (registered, minutes_in_room = 0)",
}
def trig(t):
    return SEG[t] + "; email to all in segment, WhatsApp to whatsapp_opt_in" + EXIT

BOOK = ("Book My Evaluation Call", "booking_url")
REC = ("Watch the Recording", "recording_url")

# ---- shared blocks (used by more than one track, each track gets its own opening) ----
CALL_STEPS = [
    "1. **When you book,** you answer a few short questions, so the call starts on your numbers, not on small talk.",
    "2. **On the call** we go through your funnel, your numbers and what you want from the next 12 months. Then we tell you straight whether [[offer]] fits.",
    "3. **After the call,** if it fits, you get [[proposal]]. If it doesn't, we say so.",
]
CALL_RULE = "One rule: a missed call isn't rescheduled. So pick a time you'll actually keep."
OFFER_LIST = "It's [[inc1]], [[inc2]], [[inc3]], and [[inc4]], for [[price]]."
FIT = [
    "[[offer]] fits if both of these are true:",
    "1. You want the system built with you, not just explained to you.\n2. You have [[fit_budget]] to invest in the next 12 months.",
    "It doesn't fit if you'd rather build it all yourself, or if that budget isn't there yet. Both are fine. Keep the recording and use it.",
    "If it does fit, the call is [[call_minutes]] minutes, and you get [[proposal]] if we both want to go ahead.",
]
FINTECH = [
    "The first episode of a webinar series is the hardest. Small list, no data, no idea what works.",
    "FintechCircle, a London fintech network, started at 10,000 people reached and 1 call booked. By the third episode, outreach had grown to 30,000 calendar invites, and the first three episodes booked 17 calls between them.",
    "Nothing magic happened between episode one and episode three. The system did the work: more reach every time, the same follow-up every time, and the numbers in one place so each episode improved on the last.",
]
GROWTH_COMPOUND = [
    "Growth Idea's first webinar with us, in May 2025, got 30 registrations and 7 people live.",
    "Their best one, in August 2025, got 1,990 registrations, 321 people live and 25 sales calls.",
    "Same company. What changed was the engine around the webinar: calendar-invite outreach at scale, two landing pages tested against each other, reminders, follow-up, and a weekly analytics sheet that told us what to fix next.",
]
GROWTH_BEST = [
    "Here's what the full system looked like for one client. Growth Idea is a UK business-coaching group. Their best webinar with us reached 99,859 people, 98,000 of them through calendar invites.",
    "That one session got 1,990 registrations, 321 people live and 25 sales calls.",
    "That's what the second half of my session was about. Not one tactic, but the engine that turns reach into calls, week after week.",
]

STEPS = [
# ================= Track A: stayed to the offer =================
dict(step_id="22A-0", title="Stayed: recording + book the call", anchor="webinar_start", offset=120, template="pw_a0", trigger=trig("A") + "; sent when attendance arrives (from T+120 min)",
 email=dict(subject="Thanks for staying to the end, {{first_name}}", preheader="The recording, and the one next step.", eyebrow="Thank you",
   headline="Thanks for Staying to the End",
   paras=["Hi {{first_name}},",
     "Thanks for staying for the whole session. You saw the part most webinars skip: how the system actually gets built with your team.",
     "If you want it built with you, the next step is a [[call_minutes]]-minute [[call_title]] with my team. We look at your funnel, your numbers and your goals. If it's a fit, you get [[proposal]].",
     "Book it while the session is still fresh in your head."],
   cta=BOOK, cta2=("rewatch the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, it's [[host]]. Thanks for staying to the end today.\n\nBook your [[call_minutes]]-minute evaluation call here: {{booking_url}}\n\nThe recording, if you want any part again: {{recording_url}}\n\n" + STOP),

dict(step_id="22A-1", title="Stayed: teach, find the leak closest to the money", anchor="webinar_start", offset=1440, template="pw_a1", trigger=trig("A") + "; teaching email, no booking link (they already sat through the offer); no WhatsApp",
 email=dict(subject="Start with the leak closest to the money", preheader="One exercise from yesterday's session.", eyebrow="Day 1",
   headline="Start With the Leak Closest to the Money",
   paras=["Hi {{first_name}},",
     "Yesterday you saw the whole system. That's a lot to take in, so here's the one exercise I'd do first.",
     "Write your funnel down as five steps: **reach, registration, show-up, call, sale.** Next to each, write the number from last month. Rough is fine.",
     "Now start from the end and work backwards. The first step where the number drops hard is your leak. Fix that one before you touch anything above it, because a leak near the money costs more than a leak near the top.",
     "If you want to see how I map it, it's in the first half of the recording."],
   cta=("Rewatch the Funnel Section", "recording_url")),
),

dict(step_id="22A-2", title="Stayed: FintechCircle proof", anchor="webinar_start", offset=5760, template="pw_a2", trigger=trig("A") + "; email only (Track A WhatsApp goes on days 0, 5, 7 and 14)",
 email=dict(subject="From 10,000 people reached to 30,000 invites", preheader="What kept improving from episode one to three.", eyebrow="How it compounds",
   headline="What Happened When FintechCircle Kept Going",
   paras=["Hi {{first_name}},"] + FINTECH + ["That's what we build with you. Book a call and we'll show you what it looks like for your funnel."],
   cta=BOOK, cta2=("rewatch the session", "recording_url"), cta2_lead="Or")),

dict(step_id="22A-3", title="Stayed: what happens on the call", anchor="webinar_start", offset=7200, template="pw_a3", trigger=trig("A"),
 email=dict(subject="What happens on the evaluation call", preheader="Before, during and after. No surprises.", eyebrow="The call",
   headline="What Happens on the [[call_minutes]]-Minute Call",
   paras=["Hi {{first_name}},", "Some people don't book because they don't know what they're walking into. Fair enough. Here's exactly what happens."] + CALL_STEPS + [CALL_RULE],
   cta=BOOK, cta2=("rewatch the session first", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, here's what happens on the evaluation call: [[call_minutes]] minutes on your funnel and numbers, a straight answer on fit, and [[proposal]] if it fits.\n\nBook here: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="22A-4", title="Stayed: teach, if you build it yourself, build it in this order", anchor="webinar_start", offset=8640, template="pw_a4", trigger=trig("A") + "; teaching email, no booking link (they already sat through the offer); no WhatsApp",
 email=dict(subject="If you build it yourself, build it in this order", preheader="Four pieces, one at a time.", eyebrow="Day 6",
   headline="If You Build It Yourself, Build It in This Order",
   paras=["Hi {{first_name}},",
     "Plenty of teams build this themselves. The ones who stall usually start everything at once. Here's the order I'd follow.",
     "1. **The numbers sheet.** One weekly row: reach, registrations, live, calls. You can't fix what you don't see.\n2. **The reminder ladder.** Timed from the start of the session, not from registration, with WhatsApp for anyone who opted in.\n3. **The follow-up tracks.** Stayed, left early and never showed each get their own messages.\n4. **More reach.** Only now. More people into a leaky funnel just makes a bigger leak.",
     "Finish one before you start the next. Each piece is in the recording if you want to see it built."],
   cta=("Rewatch the Build", "recording_url")),
),

dict(step_id="22A-5", title="Stayed: Growth Idea, 30 to 1,990", anchor="webinar_start", offset=10320, template="pw_a5", trigger=trig("A"),
 email=dict(subject="30 registrations to 1,990", preheader="Same company, different engine.", eyebrow="One week on",
   headline="From 30 Registrations to 1,990",
   paras=["Hi {{first_name}},"] + GROWTH_COMPOUND + ["If your first webinars look like their first one, that's normal. The question is whether you have the system to get from one to the other.", "Book a call and we'll show you where that gap is in your funnel."],
   cta=BOOK, cta2=("rewatch the session", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, one more client example. Growth Idea's first webinar with us got 30 registrations. Their best got 1,990, with 321 live and 25 sales calls.\n\nFind your gap on a call: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="22A-6", title="Stayed: teach, the weekly 20-minute review", anchor="webinar_start", offset=15840, template="pw_a6", trigger=trig("A") + "; teaching email, no booking link (they already sat through the offer); no WhatsApp",
 email=dict(subject="The 20-minute review I'd run every week", preheader="Three numbers, one change.", eyebrow="Day 11",
   headline="The 20-Minute Review I'd Run Every Week",
   paras=["Hi {{first_name}},",
     "Most funnels don't break in one go. They drift. A reminder stops sending, a page gets slower, a follow-up goes out a day late, and nobody notices for a month.",
     "So block 20 minutes a week, same day, same time:",
     "1. **Look at three numbers:** registration to live, live to calls, calls to sales.\n2. **Find the one that moved the wrong way** since last week.\n3. **Change one thing** to fix it, and write down what you changed.",
     "That's it. One change a week adds up faster than a big rebuild twice a year. I walk through how I read these numbers in the recording."],
   cta=("Rewatch the Numbers Section", "recording_url")),
),

dict(step_id="22A-7", title="Stayed: last note about the call", anchor="webinar_start", offset=20400, template="pw_a7", trigger=trig("A") + "; last step, then the newsletter (newsletter_opt_in only)",
 email=dict(subject="My last note about the call", preheader="The link, one more time.", eyebrow="Last note",
   headline="My Last Note About the Call",
   paras=["Hi {{first_name}},",
     "This is the last email I'll send you about the evaluation call.",
     "If the timing isn't right, no problem. If you ticked the newsletter box, you'll keep getting one breakdown of the system a week, and nothing else from me about this.",
     "If the timing is right, here's the link one last time."],
   cta=BOOK, cta2=("the recording stays here", "recording_url"), cta2_lead="And"),
 whatsapp="Hi {{first_name}}, last message from me about the evaluation call.\n\nIf the timing's right: {{booking_url}}\nThe recording stays here: {{recording_url}}\n\nThanks for coming to the session. " + STOP),

# ================= Track B: early leavers =================
dict(step_id="22B-0", title="Early leaver: the part you missed (replay first)", anchor="webinar_start", offset=120, template="pw_b0", trigger=trig("B") + "; sent when attendance arrives (from T+120 min)",
 email=dict(subject="You left before the part that matters most", preheader="The recording picks up where you dropped off.", eyebrow="Thanks for coming",
   headline="You Left Before the Part That Matters Most",
   paras=["Hi {{first_name}},",
     "Thanks for coming today. You had to drop off early, which happens. But the part you missed is the one that answers \"so how do I build this?\"",
     "The recording is up. Jump to where you left and watch from there."],
   cta=REC, cta2=("if you already know you want it built with you, book an evaluation call", "booking_url"), cta2_lead="Or,"),
 whatsapp="Hi {{first_name}}, it's [[host]]. Thanks for coming today. You left before the part that shows how to build it.\n\nThe recording: {{recording_url}}\n\nWant it built with you? Book a call: {{booking_url}}\n\n" + STOP),

dict(step_id="22B-1", title="Early leaver: what came after you left", anchor="webinar_start", offset=1440, template="pw_b1", trigger=trig("B"),
 email=dict(subject="What you missed after you left", preheader="The short version, in three points.", eyebrow="The short version",
   headline="Here's What Came After You Left",
   paras=["Hi {{first_name}},", "In case you don't get to the recording, here's the short version of what came after you left.",
     "1. **The system.** Funnels, the RevOps OS and the traffic channels, built to run every week, not once.\n2. **How we build it with you: [[offer]].** " + OFFER_LIST + "\n3. **Who it's for.** Teams that want it built with them and have [[fit_budget]] to invest in the next 12 months.",
     "The next step is a [[call_minutes]]-minute evaluation call. If it fits, you get [[proposal]]."],
   cta=BOOK, cta2=("watch that part of the recording", "recording_offer_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, what came after you left: the system, how we build it with your team ([[offer]], [[price]]) and who it's for.\n\nWatch that part: {{recording_offer_url}}\nOr book a call: {{booking_url}}\n\n" + STOP),

dict(step_id="22B-2", title="Early leaver: Growth Idea best webinar", anchor="webinar_start", offset=5760, template="pw_b2", trigger=trig("B"),
 email=dict(subject="One webinar: 1,990 registrations, 25 sales calls", preheader="What the full system looked like for one client.", eyebrow="Client example",
   headline="What the Full System Looked Like for One Client",
   paras=["Hi {{first_name}},"] + GROWTH_BEST + ["The recording walks through it from the point you left."],
   cta=REC, cta2=("skip ahead and book an evaluation call", "booking_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, one client's best webinar with us: 99,859 people reached, 1,990 registrations, 321 live, 25 sales calls. The second half of the session shows the engine behind it.\n\nRecording: {{recording_url}}\nBook a call: {{booking_url}}\n\n" + STOP),

dict(step_id="22B-3", title="Early leaver: what happens on the call", anchor="webinar_start", offset=7200, template="pw_b3", trigger=trig("B"),
 email=dict(subject="What happens on the evaluation call", preheader="Before, during and after.", eyebrow="The call",
   headline="What Happens on the [[call_minutes]]-Minute Call",
   paras=["Hi {{first_name}},", "You left the session before I explained the call, so here it is."] + CALL_STEPS + [CALL_RULE],
   cta=BOOK, cta2=("watch the full session first", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, you left before I explained the evaluation call: [[call_minutes]] minutes on your funnel and numbers, a straight answer on fit, and [[proposal]] if it fits.\n\nBook: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="22B-4", title="Early leaver: FintechCircle proof", anchor="webinar_start", offset=10320, template="pw_b4", trigger=trig("B"),
 email=dict(subject="From 10,000 people reached to 30,000 invites", preheader="What kept improving from episode one to three.", eyebrow="One week on",
   headline="What Happened When FintechCircle Kept Going",
   paras=["Hi {{first_name}},"] + FINTECH + ["That's the engine the second half of the session covers. Book a call to see it for your funnel."],
   cta=BOOK, cta2=("watch the second half of the recording", "recording_offer_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, FintechCircle's webinar series grew from 10,000 people reached to 30,000 calendar invites by episode three, with 17 calls booked across the first three.\n\nBook: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="22B-5", title="Early leaver: who it fits", anchor="webinar_start", offset=15840, template="pw_b5", trigger=trig("B"),
 email=dict(subject="Is this a fit? A straight answer", preheader="Who it's for, and who it isn't.", eyebrow="Fit",
   headline="Who This Is For, and Who It Isn't",
   paras=["Hi {{first_name}},", "You left the session early, so you may not know whether any of this is for you. Here's the straight version."] + FIT,
   cta=BOOK, cta2=("keep the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, a straight answer on fit. [[offer]] is for teams that want it built with them and have [[fit_budget]] to invest in the next 12 months.\n\nIf that's you: {{booking_url}}\nIf not, keep the recording: {{recording_url}}\n\n" + STOP),

dict(step_id="22B-6", title="Early leaver: two weeks on", anchor="webinar_start", offset=20400, template="pw_b6", trigger=trig("B") + "; then item 27 weeks 3 to 6",
 email=dict(subject="Two weeks on: what's changed?", preheader="One honest question.", eyebrow="Two weeks on",
   headline="Two Weeks On, What's Changed in Your Pipeline?",
   paras=["Hi {{first_name}},", "Two weeks ago you joined my session. One honest question: what has changed in your pipeline since?",
     "If the answer is \"nothing yet,\" you're not behind. You're normal. Knowing the system and having it run every week are two different things.",
     "Closing that gap is what the evaluation call is for."],
   cta=BOOK, cta2=("finish the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, two weeks since the session. What's changed in your pipeline? If the answer is nothing yet, that's the gap we close with you.\n\nBook: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

# ================= Track C: no-shows (replay first) =================
dict(step_id="22C-0", title="No-show: the recording is up", anchor="webinar_start", offset=180, template="pw_c0", trigger=trig("C") + "; sent when attendance arrives, no later than T+180 min (fallback: everyone not marked attended)",
 email=dict(subject="Missed it? The recording is up", preheader="The full session, ready when you are.", eyebrow="Recording",
   headline="You Missed It Live. Here's the Recording",
   paras=["Hi {{first_name}},", "We missed you today. No problem: the full recording is up.",
     "It covers the funnel, the RevOps OS, the traffic channels, how we build it with your team, and the Q&A."],
   cta=REC, cta2=("skip ahead and book an evaluation call", "booking_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, it's [[host]]. We missed you today. The full recording is up: {{recording_url}}\n\nWant to skip ahead? Book an evaluation call: {{booking_url}}\n\n" + STOP),

dict(step_id="22C-1", title="No-show: watch it with one question", anchor="webinar_start", offset=1440, template="pw_c1", trigger=trig("C"),
 email=dict(subject="Watch it with one question in mind", preheader="Where do your leads go quiet?", eyebrow="Before you press play",
   headline="Watch the Recording With One Question in Mind",
   paras=["Hi {{first_name}},", "Recordings are easy to skip. So here's a way to make it worth the time.",
     "Before you press play, write down one thing: **the step in your funnel where leads go quiet.** Maybe they register and don't show. Maybe they book and don't buy. Maybe nobody follows up.",
     "Then watch with that step in mind. You'll know within the first half whether the system fixes it."],
   cta=REC, cta2=("talk it through with us on an evaluation call", "booking_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, before you watch the recording, write down the one step where your leads go quiet. Then watch with that in mind.\n\nRecording: {{recording_url}}\nOr talk it through: {{booking_url}}\n\n" + STOP),

dict(step_id="22C-2", title="No-show: Growth Idea best webinar", anchor="webinar_start", offset=5760, template="pw_c2", trigger=trig("C"),
 email=dict(subject="One webinar: 1,990 registrations, 25 sales calls", preheader="What the full system looked like for one client.", eyebrow="Client example",
   headline="What the Full System Looked Like for One Client",
   paras=["Hi {{first_name}},"] + GROWTH_BEST[:2] + ["That's what the session covers. Not one tactic, but the engine that turns reach into calls, week after week.", "It's all in the recording."],
   cta=REC, cta2=("skip ahead and book an evaluation call", "booking_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, one client's best webinar with us: 99,859 people reached, 1,990 registrations, 321 live, 25 sales calls. The recording shows the engine behind it.\n\nRecording: {{recording_url}}\nBook a call: {{booking_url}}\n\n" + STOP),

dict(step_id="22C-3", title="No-show: how we build it with you", anchor="webinar_start", offset=7200, template="pw_c3", trigger=trig("C"),
 email=dict(subject="How we build it with you", preheader="What's included, what it costs, who it's for.", eyebrow="The offer",
   headline="How We Build the System With Your Team",
   paras=["Hi {{first_name}},", "You missed the live session, so you also missed the part where I explain how we work with companies directly. Here it is in three lines.",
     "1. **What it is: [[offer]].** " + OFFER_LIST + "\n2. **Who it's for.** Teams that want it built with them and have [[fit_budget]] to invest in the next 12 months.\n3. **How it starts.** A [[call_minutes]]-minute evaluation call. If it fits, you get [[proposal]].",
     CALL_RULE],
   cta=BOOK, cta2=("watch that part of the recording", "recording_offer_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, the part of the session you missed: how we build the system with your team. [[offer]], [[price]], for teams with [[fit_budget]] to invest this year.\n\nBook a call: {{booking_url}}\nWatch that part: {{recording_offer_url}}\n\n" + STOP),

dict(step_id="22C-4", title="No-show: FintechCircle proof", anchor="webinar_start", offset=10320, template="pw_c4", trigger=trig("C"),
 email=dict(subject="From 10,000 people reached to 30,000 invites", preheader="What kept improving from episode one to three.", eyebrow="One week on",
   headline="What Happened When FintechCircle Kept Going",
   paras=["Hi {{first_name}},"] + FINTECH + ["The recording shows the system. The call shows what it looks like for your funnel."],
   cta=BOOK, cta2=("watch the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, FintechCircle's webinar series grew from 10,000 people reached to 30,000 calendar invites by episode three, with 17 calls booked across the first three.\n\nBook: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="22C-5", title="No-show: who it fits", anchor="webinar_start", offset=15840, template="pw_c5", trigger=trig("C"),
 email=dict(subject="Is this a fit? A straight answer", preheader="Who it's for, and who it isn't.", eyebrow="Fit",
   headline="Who This Is For, and Who It Isn't",
   paras=["Hi {{first_name}},", "You haven't seen the session yet, so here's the straight version of who it's for."] + FIT,
   cta=BOOK, cta2=("start with the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, a straight answer on fit. [[offer]] is for teams that want it built with them and have [[fit_budget]] to invest in the next 12 months.\n\nIf that's you: {{booking_url}}\nIf not, the recording: {{recording_url}}\n\n" + STOP),

dict(step_id="22C-6", title="No-show: two weeks on", anchor="webinar_start", offset=20400, template="pw_c6", trigger=trig("C") + "; then item 27 weeks 3 to 6",
 email=dict(subject="Two weeks on: still worth an hour?", preheader="One honest question.", eyebrow="Two weeks on",
   headline="Is Your Pipeline Worth One Hour This Week?",
   paras=["Hi {{first_name}},", "Two weeks ago you signed up for my session and couldn't make it. Life happens.",
     "One honest question: if a lead goes quiet in your funnel this week, does anything catch it? If not, the recording is the hour that shows you how.",
     "And if you'd rather skip the hour and talk it through, book the call."],
   cta=REC, cta2=("book an evaluation call", "booking_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, two weeks since the session you missed. If a lead goes quiet this week, does anything catch it? The recording shows how: {{recording_url}}\n\nOr talk it through: {{booking_url}}\n\n" + STOP),
]

def both_links(s):
    p = []
    plain = L.email_plain(s) if "email" in s else ""
    for chan, text in (("email", plain), ("whatsapp", s.get("whatsapp", ""))):
        if not text:
            continue
        if "{{booking_url}}" not in text and "teaching email" not in s["trigger"]:
            p.append("%s %s: no booking link" % (s["step_id"], chan))
        if "{{recording_url}}" not in text and "{{recording_offer_url}}" not in text:
            p.append("%s %s: no recording link" % (s["step_id"], chan))
    return p

def main():
    problems, _ = L.build(STEPS, HERE, "22", footer_reason="You're getting this because you registered for {{webinar_title}}.",
                          gallery_title="22 Post-Webinar Emails", extra_checks=both_links,
                          wa_category="Marketing")
    for p in problems:
        print("PROBLEM", p)
    print("22 build: %d steps, %d problems" % (len(STEPS), len(problems)))
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
