#!/usr/bin/env python3
"""Builds item 4 from one source: 6 profile markdowns, the Tantra CSVs, the manual InMail file and note-check.md.

usage: python3 deliverables/04-linkedin-templates/build.py

Copy is written with short slots, filled here:
  [first] -> {{firstName}}   [co] -> {{company}}   [topic] -> {{custom.post_topic}}   (Tantra fills these)
  [host] [brand] [min] [qa]  -> brand.host_name, brand.company, webinar.duration_minutes, webinar.qa_minutes
                                from deliverables/_shared/funnel-config.json
  [link] -> registration URL from funnel-config (domains.funnel_domain + domains.paths.registration) plus UTMs
  [me]   -> the sender's first name from profiles.json
{{firstName}} and {{company}} are the tags documented on Tantra's help page
(https://usetantra.com/help/templates-and-ai/merge-tags-and-spintax); an unknown tag renders blank.
A FILL_ config value stays as a {{token}} and is listed as NOT READY. Exit 1 on any failed check.
"""
import csv, json, re, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONFIG = json.loads((ROOT / "deliverables/_shared/funnel-config.json").read_text())
PROFILES = json.loads((HERE / "profiles.json").read_text())["profiles"]

TYPES = ["content_engagement", "inmail", "connector", "messenger"]
UTM_MEDIUM = {"content_engagement": "engagement", "inmail": "inmail", "connector": "connector", "messenger": "messenger"}
TANTRA_ACTIONS = {"visit_profile", "connection_request", "send_message"}   # CHANNEL_ACTIONS.linkedin in Tantra's source
WORST = {"{{firstName}}": 15, "{{company}}": 35, "{{custom.post_topic}}": 40}
WEEKLY_CAP = 180   # lower of 180 (launch-kit.md:38, Tantra default) and 200 (linkedin.md:26)
BANNED = ["leverage", "unlock", "seamless", "game-changer", "game changer", "supercharge", "fast-paced",
          "end to end", "end-to-end", "engineered system", "delve", "robust", "elevate", "no " + "pitch",
          "nothing to " + "buy", "100% " + "free", "400+", "$100k to $300k", "guarantee",
          "hope all is", "hope things are", "thought of you", "you'd get a lot", "{{custom.company}}"]

V, C, M, I = "visit_profile", "connection_request", "send_message", "manual_inmail"

def step(action, delay, message="", subject="", track=None, when=""):
    return {"action": action, "delay": delay, "message": message.strip(), "subject": subject, "track": track, "when": when}

# ---------------------------------------------------------------------------------------------
# COPY. Delays are days after the previous step.
# content_engagement: track "2nd/3rd" connects first, track "1st" messages straight away.
# inmail: step 1 is sent by hand in Sales Navigator; tracks "followup" run in Tantra for non-repliers.
# Every opening is different across senders (LinkedIn flags the same template on several accounts).
# ---------------------------------------------------------------------------------------------
COPY = {}

COPY["adi"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="Hi [first], you engaged with my post on [topic]. I go much deeper on it in a live session I host every week. Glad to connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Thanks for connecting, [first].

My post on [topic] was one slice. Live, I walk through the whole revenue engine behind it: the funnel, the RevOps system that runs it and the AI that does the busywork.

It runs every week, [min] minutes. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], one example I break down in the session.

For FintechCircle, a London fintech network, outreach grew from 10,000 to 20,046 to 30,000 calendar invites across three episodes. Those three episodes booked 17 sales calls.

I show how it was built, stage by stage: [link]"""),
  step(M, 0, track="1st", message="""
Hi [first], thanks for engaging with my post on [topic].

I unpack the full system behind it live every week: funnel, RevOps, AI and the channels that feed it. [min] minutes.

Want a seat? [link]"""),
  step(M, 4, track="1st", message="[first], quick follow-up. If [topic] is on your plate this quarter, the session shows the full build behind it: [link]"),
 ],
 "inmail": [
  step(I, 0, subject="[first], a question about pipeline at [co]", message="""
Hi [first],

Quick question: could you predict next quarter's booked sales calls at [co] today?

Most founders I speak with can't. Leads come from referrals, a good month on ads, a lucky post. Nothing they can measure and repeat.

I've spent 10+ years building the other kind of pipeline for 250+ brands. Every week I teach the whole system live: the funnel, the RevOps system behind it and the AI that runs the busywork.

[min] minutes. Save your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="Hi [first], I sent you an InMail last week about the session I host on building a pipeline you can measure. Connecting either way, as our work overlaps."),
  step(M, 1, track="followup", when="1 day after they accept", message="""
Thanks for connecting, [first]. Here's the session link I mentioned: [link]

It runs every week, so pick whichever week suits you."""),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], does pipeline at [co] come from a system you can read every week, or from referrals and luck? I've spent 10+ years building the first kind for 250+ brands. Glad to connect."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Thanks for connecting, [first].

One pattern I see in almost every founder-led company: the problem isn't traffic. It's that nobody can see where a cold prospect drops out between first touch and a booked call.

Fix that view and the next hire, channel or budget decision gets obvious.

How does [co] track it today?"""),
  step(M, 3, message="""
[first], I teach this live every week.

In [min] minutes I walk through the whole revenue engine: the funnel, the RevOps system behind it, the AI that does the busywork and the traffic channels that fill it.

Bring your numbers. You'll leave knowing which stage to fix first.

Save your seat: [link]"""),
  step(M, 4, message="""
This isn't theory, [first].

For Growth Idea, a UK business-coaching group, one webinar reached 99,859 people. 1,990 registered, 321 came live and 25 booked sales calls.

Their first webinar got 30 registrations. Every stage was measured, so every week got better.

I show the exact build here: [link]"""),
  step(M, 6, message="""
Last note from me, [first].

If a predictable pipeline is on this year's list for [co], the session runs every week: [link]

If not, no hard feelings. Good luck with the quarter."""),
 ],
 "messenger": [
  step(M, 0, message="""
[first], quick question: how much of [co]'s pipeline last quarter came from referrals you couldn't have planned for?

For most founders I talk to, it's most of it. I now host a live session every week on building the other kind: a funnel, a RevOps system and AI on the busywork, measured stage by stage. It's the playbook from 250+ brands I've worked with.

Want a seat? [link]"""),
  step(M, 4, message="""
[first], one number from the session that tends to land: a UK coaching group went from 30 registrations on their first webinar to 1,990 on their best.

Same team. The difference was measuring every stage and fixing the weakest one each week.

Seat's here if useful: [link]"""),
  step(M, 5, message="""
Last nudge, [first]. It runs every week, so any week works: [link]

And if a quick chat about [co] would help more than a session, just reply here."""),
 ],
}

COPY["bharath"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="[first], saw you on my post about [topic]. The stack behind it gets a full walkthrough in a weekly live session. Happy to connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Good to be connected, [first].

The post on [topic] showed one piece of the stack. The weekly session shows how it all connects: funnel, CRM, outreach and AI agents, with every stage measured.

[host], our founder, hosts it, and the stack I build is part of what he shows. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], a number for scale: across 11 webinars for a UK coaching group, outreach reached 765,105 people and 80 sales calls were booked.

The wiring behind that is in the session: [link]"""),
  step(M, 0, track="1st", message="""
[first], saw you on my post about [topic].

If you want the full stack behind it, [host], our founder, walks through it live every week: [link]"""),
  step(M, 4, track="1st", message="[first], if you'd rather see the wiring behind [topic] than read about it, this week's session is the place: [link]"),
 ],
 "inmail": [
  step(I, 0, subject="The revenue stack at [co]", message="""
[first],

I'm the CTO at [brand]. One question about [co]: when a lead goes quiet, can you see which tool dropped it?

In most companies the funnel, the CRM, outreach and the calendar each hold a piece of the truth, and nobody owns the joins between them.

[host], our founder, hosts a live session every week on fixing that: one revenue engine, AI agents on the busywork, every stage measured. The stack I build is part of what he shows.

[min] minutes, including [qa] minutes of Q&A. Seat's here: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="[first], following my InMail on the revenue stack and AI agents: connecting either way. Always glad to know people who build."),
  step(M, 1, track="followup", when="1 day after they accept", message="Good to be connected, [first]. The stack session I wrote about is here: [link]\n\nA new one runs each week."),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], I'm CTO at [brand]. Most revenue stacks I see are five tools held together by hope. I build the version where AI agents run the busywork. Glad to connect."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Good to be connected, [first].

A question I ask every technical founder: how many tools touch a lead between first click and booked call at [co]?

The honest answer is usually "more than we'd like", with nobody owning the joins. That's where leads go missing, not in the ads."""),
  step(M, 3, message="""
[first], this is exactly what [host], our founder, teaches live every week, and the stack I build is a big part of it.

It covers how the funnel, the CRM, calendar and email outreach and the AI agents connect, so every lead is tracked from first touch to booked call.

[min] minutes, including [qa] minutes of Q&A: [link]"""),
  step(M, 4, message="""
A number from the build, [first].

In one webinar for Growth Idea, 98,000 of the 99,859 people reached came through calendar invites. 1,990 registered.

How it's wired is in the session: [link]"""),
  step(M, 6, message="""
Last one from me, [first]. If cleaning up the revenue stack at [co] is on the roadmap, the session runs every week: [link]

Happy to answer a stack question here too, no session needed."""),
 ],
 "messenger": [
  step(M, 0, message="""
[first], a stack question: when a lead goes cold at [co], can your tools tell you where it stalled?

[host], our founder, hosts a live session every week on building a revenue engine where AI agents do the busywork and every stage is tracked. It covers the part I build: what connects to what, and where leads get lost.

Seat's here: [link]"""),
  step(M, 4, message="""
[first], the engineering takeaway: one view of every lead from first touch to booked call, with each stage measured. No more guessing which tool dropped it.

Seat's here if useful: [link]"""),
  step(M, 5, message="[first], last note on this. If a stack question is easier than a session, ask it here. Otherwise the link stands: [link]"),
 ],
}

COPY["bhaskar"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="Thanks for weighing in on my [topic] post, [first]. Turning content into pipeline gets a full session every week. Would be glad to connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Appreciate the connect, [first].

That post on [topic] was one piece of the system. The weekly session shows the whole path from content to booked call, with a number on every stage.

[host], our founder, hosts it. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], a single episode for a London fintech network went out as 38,138 calendar invites and drew 187 Yes and 221 Maybe RSVPs.

The setup behind it is in the session: [link]"""),
  step(M, 0, track="1st", message="""
Thanks for weighing in on my [topic] post, [first].

[host], our founder, runs a live session every week on the full path from content to booked call: [link]"""),
  step(M, 4, track="1st", message="One more thought, [first]: if [topic] matters to your pipeline this quarter, the session ties it to booked calls. [link]"),
 ],
 "inmail": [
  step(I, 0, subject="Content that books calls at [co]", message="""
Hello [first],

I lead marketing at [brand]. One question: of everything [co] published last quarter, do you know which pieces booked sales calls?

Most teams can show reach. Very few can show pipeline. The fix is a funnel where every stage, from post to calendar invite to call, is measured.

[host], our founder, teaches the full system live every week, including the content and pipeline side I run.

[min] minutes. Your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="Hi [first], my InMail on content that books sales calls may have landed in a busy week. Connecting either way, as we work on the same problem."),
  step(M, 1, track="followup", when="1 day after they accept", message="Appreciate the connect, [first]. For when you have a free slot, here's the content-to-pipeline session: [link]"),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], I run marketing at [brand]. Most teams I meet can report on content reach but not on the pipeline it creates. That gap is what I work on. Glad to connect."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Appreciate the connect, [first].

A question I ask every marketing lead: which channel booked last month's sales calls at [co], and could you prove it to your CEO?

If the honest answer is "roughly", the content isn't the problem. The missing link between content, the funnel and the calendar is."""),
  step(M, 3, message="""
That link is the whole topic of a live session [host], our founder, runs every week, [first]: how content, outreach and webinars feed one pipeline you can measure stage by stage.

If content is your job, it's the most useful session I can point you to. [min] minutes. Your seat: [link]"""),
  step(M, 4, message="""
One example, [first].

For FintechCircle, a London fintech network, outreach grew from 10,000 to 20,046 to 30,000 calendar invites across three episodes. Those three episodes booked 17 sales calls.

Each week's numbers told us what to change next. The session shows how: [link]"""),
  step(M, 6, message="""
Last note, [first]. If pipeline you can attribute is a goal for [co] this year, the session runs every week: [link]

If not, all good."""),
 ],
 "messenger": [
  step(M, 0, message="""
[first], honest question: of the content [co] put out last quarter, which pieces booked a sales call?

Most marketing teams can show reach, not pipeline. [host], our founder, hosts a live session every week on closing that gap: content, outreach and webinars feeding one pipeline you can measure.

Seat's here: [link]"""),
  step(M, 4, message="""
[first], the practical takeaway for marketers: which stage of the funnel to fix first, with the numbers to back it in front of the CEO.

[link]"""),
  step(M, 5, message="Closing the loop, [first]. The session repeats weekly, so next week works as well as this one: [link]"),
 ],
}

COPY["nelbin"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="Hi [first], good to see you on my post about [topic]. The process behind it is covered step by step in a weekly session. Glad to connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Glad we're connected, [first].

My post on [topic] covered one step. The weekly session covers the whole process: who owns each stage, what gets measured weekly and what the AI handles.

[host], our founder, hosts it. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], a process example from the session.

In one logged experiment for a UK coaching group, a 100,000-invite calendar push aimed for 250 attendees and got 441. Logging it is what made it repeatable.

The full checklist is here: [link]"""),
  step(M, 0, track="1st", message="""
[first], good to see you on my [topic] post.

[host], our founder, runs a live session every week on building revenue as a repeatable process: [link]"""),
  step(M, 4, track="1st", message="[first], following up once. The session turns [topic] into a weekly checklist you can run: [link]"),
 ],
 "inmail": [
  step(I, 0, subject="Who owns the pipeline at [co]?", message="""
Hi [first], a blunt question from an ops person.

I run operations at [brand]. Who owns each stage of the pipeline at [co], from first touch to signed client?

In most companies the answer is "sort of everyone", which means nobody. Leads stall in the handoffs.

[host], our founder, hosts a live session every week on running the revenue engine as a process: an owner, a weekly number and a checklist for every stage, with AI on the routine work. It's how I run operations here.

[min] minutes. Your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="[first], I wrote to you about running the pipeline as a process. Whether or not it's a fit, ops people should know each other. Glad to connect."),
  step(M, 1, track="followup", when="1 day after they accept", message="Glad we're connected, [first]. The process session I mentioned is here, and it repeats weekly: [link]"),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], I run operations at [brand]. Most growth problems I see are process problems: no owner, no checklist, no weekly number. That's my patch. Glad to connect."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Glad we're connected, [first].

A question from the ops side: if your best salesperson left [co] tomorrow, would the pipeline keep running?

When the answer is no, the pipeline lives in someone's head. The fix is a written process with an owner and a number for every step."""),
  step(M, 3, message="""
[first], that written process is what [host], our founder, teaches in a live session every week: who owns each stage, what gets measured weekly and what the AI handles.

It's the same process I run here. [min] minutes. Your seat: [link]"""),
  step(M, 4, message="""
A process example, [first].

Over 11 webinars for Growth Idea, a UK coaching group, we built a weekly analytics sheet and a 12-item experiment log. The totals: 6,517 registered, 1,384 came live, 80 sales calls booked.

No heroics, just the same checklist every week. The session walks through it: [link]"""),
  step(M, 6, message="I'll stop here, [first]. If a pipeline that runs without heroics is on the list for [co], the session runs every week: [link]"),
 ],
 "messenger": [
  step(M, 0, message="""
[first], an ops question: is there one written process at [co] for what happens between a sign-up and a booked call?

When there isn't, leads stall in the handoffs. [host], our founder, hosts a live session every week on running revenue as a repeatable process, with AI on the routine steps.

Seat's here: [link]"""),
  step(M, 4, message="""
[first], the ops takeaway: a weekly scorecard for every stage of the funnel, so you fix the weakest step instead of guessing.

[link]"""),
  step(M, 5, message="[first], one final reminder and then I'll leave it. New session every week: [link]"),
 ],
}

COPY["aquila"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="[first], noticed you on my post about [topic]. The automations behind it are shown live in a weekly session. Let's connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Thanks for accepting, [first].

That post on [topic] was a single automation. The weekly session shows the whole chain: invites, reminders, follow-ups and handoffs that run without someone remembering.

[host], our founder, hosts it. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], here's what that looks like at scale: for a UK coaching group we built calendar-invite outreach at 12,000 to 120,000 invites per webinar, plus the reminders and follow-up around it.

The session shows the flow: [link]"""),
  step(M, 0, track="1st", message="""
Hi [first], noticed you on my post about [topic].

[host], our founder, runs a live session every week on the revenue engine, including the automations I build: [link]"""),
  step(M, 4, track="1st", message="[first], a last pointer: the session shows which parts of [topic] to automate first. [link]"),
 ],
 "inmail": [
  step(I, 0, subject="The manual steps in your funnel", message="""
Hey [first],

I build automations at [brand]. One question: how many steps between a sign-up and a booked call at [co] still depend on someone remembering to do them?

Every manual step is a place a lead waits. Reminders, follow-ups and handoffs are where most of the drop-off hides.

[host], our founder, hosts a live session every week on the full revenue engine, including the automation layer I build: what to automate, in what order, and what to keep human.

[min] minutes. Your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="Hi [first], after my note on automating the funnel, a connection made more sense than another InMail. Always keen to know people who automate."),
  step(M, 1, track="followup", when="1 day after they accept", message="Thanks for accepting, [first]. Here's the automation session from my InMail: [link]\n\nAny week works."),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], I build automations at [brand]: the reminders, follow-ups and handoffs nobody should do by hand. Always keen to connect with people who think about this too."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Thanks for accepting, [first].

Quick one from the automation side: how many steps between a sign-up and a booked call at [co] still need someone to remember them?

Every manual step is a place a lead waits."""),
  step(M, 3, message="""
Taking those steps out is part of a live session [host], our founder, runs every week, [first]. It includes the automation layer I build: what to automate, in what order, and what to keep human.

[min] minutes. Your seat: [link]"""),
  step(M, 4, message="""
Here's a real one, [first].

For FintechCircle's second episode, 20,046 calendar invites went out, 117 people came live and 9 sales calls were booked.

Behind numbers like that is a chain of invites, reminders and follow-ups that has to fire on time, every week. The session shows the flow: [link]"""),
  step(M, 6, message="Wrapping up, [first]. If taking the manual steps out of the funnel at [co] is on the list, the session runs every week: [link]"),
 ],
 "messenger": [
  step(M, 0, message="""
[first], how many reminders and follow-ups at [co] still go out only when someone remembers?

Each one is a place a lead waits. [host], our founder, hosts a live session every week on the revenue engine, including the automation layer I build: reminders, follow-ups and handoffs that run on time.

Seat's here: [link]"""),
  step(M, 4, message="""
[first], the practical bit: a map of which funnel steps to automate first and which to keep human.

[link]"""),
  step(M, 5, message="Final one from me, [first]. If the timing's off, any later week works: [link]"),
 ],
}

COPY["ben"] = {
 "content_engagement": [
  step(V, 0, track="2nd/3rd", when="same day the engager list is imported"),
  step(C, 0, track="2nd/3rd", message="Hi [first], appreciate you engaging with my [topic] post. The build behind it is shown in a weekly live session. Glad to connect."),
  step(M, 1, track="2nd/3rd", when="1 day after they accept", message="""
Nice to connect, [first].

My [topic] post was one part of the build. The weekly session covers the rest: pages, forms, tracking and the tests that decide what stays.

[host], our founder, hosts it. Your seat: [link]"""),
  step(M, 4, track="2nd/3rd", message="""
[first], one test from the session: a long landing page was expected to bring 70 registrations and brought 96.

We only knew because both pages were tracked. The setup is here: [link]"""),
  step(M, 0, track="1st", message="""
[first], appreciate you engaging with my post on [topic].

[host], our founder, runs a live session every week on the full revenue engine, including the build side I work on: [link]"""),
  step(M, 4, track="1st", message="[first], last one from me: the session shows how to test [topic] with real numbers. [link]"),
 ],
 "inmail": [
  step(I, 0, subject="Your sign-up page at [co]", message="""
Hi [first], a question from the build side.

I build the pages, forms and tracking behind [brand]'s funnels. What share of people who land on your sign-up page at [co] register, and do you know why the rest leave?

Most teams track the click, not the drop-off. The page is usually the cheapest fix in the funnel.

[host], our founder, hosts a live session every week on the full revenue engine, including the build side I work on: pages, tracking and the tests that decide what stays.

[min] minutes. Your seat: [link]

[me]"""),
  step(C, 0, track="followup", when="import 5 days after the InMail, non-repliers only", message="[first], I reached out by InMail about the pages and tracking behind a funnel. Connecting either way, as we build similar things."),
  step(M, 1, track="followup", when="1 day after they accept", message="Nice to connect, [first]. The link to the session I wrote about: [link]\n\nIt runs every week."),
 ],
 "connector": [
  step(V, 0),
  step(C, 1, message="Hi [first], I build the pages, forms and tracking behind [brand]'s funnels, and test what makes people sign up. Glad to connect with people who build too."),
  step(M, 1, when="1 day after they accept; no link yet", message="""
Nice to connect, [first].

A question from the build side: when someone lands on your sign-up page at [co], do you know what share register, and why the rest leave?

Most teams track the click, not the drop-off. The page is usually the cheapest fix in the whole funnel."""),
  step(M, 3, message="""
[first], the drop-off is one of the things [host], our founder, takes apart in a weekly live session. It includes the build side I work on: pages, forms, tracking and the tests that decide what stays.

[min] minutes. Your seat: [link]"""),
  step(M, 4, message="""
One build example, [first].

For Growth Idea, a UK coaching group, the registration rate went from 0.23% on the first webinar to 2.0% on the best one, with a long and a short landing page tested against each other.

The session shows what changed: [link]"""),
  step(M, 6, message="Final message from me, [first]. If your sign-up page at [co] could work harder, the session runs every week: [link]"),
 ],
 "messenger": [
  step(M, 0, message="""
[first], a build question: do you know what share of visitors to [co]'s sign-up page actually register?

Most teams track the click, not the drop-off. [host], our founder, hosts a live session every week on the full revenue engine, including the build side I work on: pages, forms, tracking and the tests that decide what stays.

Seat's here: [link]"""),
  step(M, 4, message="""
[first], the builder's takeaway: how to tell, with numbers, which version of a page to keep.

[link]"""),
  step(M, 5, message="[first], that's my last message on this. The session is weekly, so pick any week that suits: [link]"),
 ],
}

# ---------------------------------------------------------------------------------------------
# LIMITS per LinkedIn account, shared by every campaign on that account. Monday to Friday.
# Start: the agreed T-057 ramp, 20 to 25 a day (launch-kit.md:39). Raise 5 a day only after two clean
# weeks, never above 35 a weekday (175 a week, under the 180 a week cap).
# ---------------------------------------------------------------------------------------------
TIERS = {
 "new":         {"connect": 20, "ce_connect": 5, "max_connect": 25, "visits": 30, "messages": 25, "messenger_first": 10, "inmail": "0, or up to 5 Open Profile InMails"},
 "established": {"connect": 25, "ce_connect": 8, "max_connect": 35, "visits": 40, "messages": 50, "messenger_first": 25, "inmail": "up to 10 (1 to 2 on credits, the rest Open Profile)"},
 "mature":      {"connect": 25, "ce_connect": 8, "max_connect": 35, "visits": 50, "messages": 75, "messenger_first": 50, "inmail": "up to 30 (2 on credits, the rest Open Profile)"},
}

def get(path):
    cur = CONFIG
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def is_fill(v):
    return isinstance(v, str) and v.startswith("FILL_")

def reg_url(profile, ctype):
    dom = get("domains.funnel_domain")
    path = get("domains.paths.registration") or "/"
    q = f"?utm_source=linkedin&utm_medium={UTM_MEDIUM[ctype]}&utm_campaign=enterprise-webinar&utm_content={profile}"
    if is_fill(dom) or not dom:
        return "{{domains.funnel_domain}}" + path + q
    dom = re.sub(r"^https?://", "", dom).rstrip("/")
    return f"https://{dom}{path}{q}"

unresolved, fails = set(), []
names = {p["key"]: p for p in PROFILES}
SLOTS = {"[first]": "{{firstName}}", "[co]": "{{company}}", "[topic]": "{{custom.post_topic}}",
         "[host]": "brand.host_name", "[brand]": "brand.company", "[min]": "webinar.duration_minutes", "[qa]": "webinar.qa_minutes"}

def render(text, profile, ctype):
    text = text.replace("[link]", reg_url(profile, ctype)).replace("[me]", names[profile]["name"])
    for slot, val in SLOTS.items():
        if val.startswith("{{"):
            text = text.replace(slot, val)
        elif slot in text:
            v = get(val)
            if v is None or is_fill(v):
                unresolved.add(val)
                v = "{{" + val + "}}"
            text = text.replace(slot, str(v))
    if "{{domains.funnel_domain}}" in text:
        unresolved.add("domains.funnel_domain")
    left = re.findall(r"\[[a-z]+\]", text)
    if left:
        fails.append(f"{profile} {ctype}: unknown slot {left}")
    return text

def worst_len(text):
    for tag, n in WORST.items():
        text = text.replace(tag, "X" * n)
    return len(text)

def norm(text, profile):
    """Text with this sender's own link and name removed, for the cross-sender duplicate check."""
    t = text
    for ct in TYPES:
        t = t.replace(reg_url(profile, ct), "<LINK>")
    return re.sub(r"\s+", " ", t.replace(names[profile]["name"], "<ME>")).strip().lower()

# CSV groups: Tantra imports (actions Tantra accepts) and the manual Sales Navigator file.
GROUPS = {"content_engagement": [], "connector": [], "messenger": [], "inmail_followup": [], "inmail_manual_step1": []}
notes, seen_full, seen_open = [], {}, {}

assert set(names) == set(COPY), f"profiles and copy differ: {set(names) ^ set(COPY)}"
for p in PROFILES:
    k = p["key"]
    assert set(COPY[k]) == set(TYPES), f"{k} is missing a campaign type"
    for ctype in TYPES:
        counters = {}
        for s in COPY[k][ctype]:
            if ctype == "inmail":
                ct = "inmail_manual_step1" if s["action"] == I else "inmail_followup"
            elif ctype == "content_engagement":
                ct = "content_engagement_1st" if s["track"] == "1st" else "content_engagement"
            else:
                ct = ctype
            counters[ct] = counters.get(ct, 0) + 1
            msg, subj = render(s["message"], k, ctype), render(s["subject"], k, ctype)
            n = worst_len(msg)
            s.update(r_message=msg, r_subject=subj, n=n, no=counters[ct], ct=ct)
            if s["action"] == C:
                notes.append((p["name"], ct, counters[ct], n))
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
            if msg:
                full, opening = norm(msg, k), norm(msg, k)[:60]
                for key, store in ((full, seen_full), (opening, seen_open)):
                    other = store.setdefault(key, k)
                    if other != k:
                        what = "message" if store is seen_full else "opening (first 60 characters)"
                        fails.append(f"{k} {ct} step {counters[ct]}: same {what} as {other}; every sender needs their own version")
            row = {"profile": k, "campaign_type": ct, "step": counters[ct], "delay_days": s["delay"],
                   "action": s["action"], "subject": subj, "message": msg, "char_count": n if msg else 0}
            group = "content_engagement" if ct.startswith("content_engagement") else ct
            GROUPS[group].append(row)
        if not any(reg_url(k, ctype) in s["r_message"] for s in COPY[k][ctype]):
            fails.append(f"{k} {ctype}: no registration link")

for g, rows in GROUPS.items():
    if g != "inmail_manual_step1":
        bad = [r for r in rows if r["action"] not in TANTRA_ACTIONS]
        if bad:
            fails.append(f"{g}.csv: actions Tantra rejects: {sorted({r['action'] for r in bad})}")

# ---- CSVs
cols = ["profile", "campaign_type", "step", "delay_days", "action", "subject", "message", "char_count"]
(HERE / "csv").mkdir(exist_ok=True)
old = HERE / "csv" / "inmail.csv"
if old.exists():
    old.unlink()
for g, rows in GROUPS.items():
    with open(HERE / "csv" / f"{g}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

# ---- note check
lines = ["# Connection Note Check", "",
         "Generated by build.py. Each note is counted with merge fields at worst-case length "
         f"(firstName {WORST['{{firstName}}']}, company {WORST['{{company}}']}, custom.post_topic {WORST['{{custom.post_topic}}']} characters). "
         "LinkedIn's limit is 300. A free LinkedIn account allows 200 and only a few notes a month, so every sender should be on Premium or Sales Navigator.", "",
         "| Profile | Campaign | Step | Worst-case chars | Under 300 | Under 200 |", "|---|---|---|---|---|---|"]
for name, ct, no, n in notes:
    lines.append(f"| {name} | {ct} | {no} | {n} | {'yes' if n < 300 else 'NO'} | {'yes' if n <= 200 else 'no'} |")
lines += ["", f"Result: {sum(1 for x in notes if x[3] < 300)} of {len(notes)} notes under 300 characters; {sum(1 for x in notes if x[3] <= 200)} under 200."]
(HERE / "note-check.md").write_text("\n".join(lines) + "\n")

# ---- profile markdowns
TITLES = {"content_engagement": "Content Engagement (Likers and Commenters of Each Post)",
          "inmail": "InMail (Sent by Hand in Sales Navigator, Follow-Ups in Tantra)",
          "connector": "Connector (Connection Request, Then Follow-Ups)",
          "messenger": "Messenger (1st-Degree Connections)"}
WHO = {
 "content_engagement": "People who liked or commented on one of this profile's own posts. One campaign per post, started within 24 hours of the post. Split the engager export by degree: 2nd and 3rd degree run the connect track, 1st degree the message track.",
 "inmail": "Prospects in this profile's audience who are not connected and are worth a credit: Open Profiles first (no credit used), then the best fits on credits. Needs Sales Navigator or Premium. Step 1 is sent by hand in Sales Navigator, so Tantra cannot see replies: 5 days later, import **only the people who did not reply** into the follow-up campaign.",
 "connector": "Cold prospects in this profile's audience (2nd and 3rd degree). Only people who accept get the messages.",
 "messenger": "This profile's own 1st-degree connections who match the audience and are owned by no other profile.",
}
FIELDS = {
 "content_engagement": "`{{firstName}}` and `{{custom.post_topic}}` (a 2 to 6 word phrase for the post, the same value on every row of that post's export). If the test message shows `{{custom.post_topic}}` blank, type the phrase into the step text instead: each post has its own campaign.",
 "inmail": "`{{firstName}}` and `{{company}}`. Step 1 goes out by hand in Sales Navigator, which does not fill Tantra tags: type the first name and company in place of the tags before sending. The follow-up steps run in Tantra, which fills them. The sign-off is the sender's name, already in the text.",
 "connector": "`{{firstName}}` and `{{company}}`.",
 "messenger": "`{{firstName}}` and `{{company}}`.",
}
ACTION_LABEL = {V: "Visit profile", C: "Connection request with note", M: "Message", I: "InMail, sent by hand in Sales Navigator"}

def limit_line(t, ctype):
    if ctype == "connector":
        return f"{t['connect'] - t['ce_connect']} connection requests a day (the rest of the {t['connect']} a day budget goes to content engagement), {t['visits']} profile visits a day."
    if ctype == "content_engagement":
        return f"{t['ce_connect']} connection requests a day from the {t['connect']} a day budget; messages come out of the {t['messages']} a day message budget."
    if ctype == "inmail":
        return f"InMail {t['inmail']} a day. Credits: Sales Navigator 50 a month, Premium Business 15, Premium Career 5, free none. The follow-up connection requests count toward the {t['connect']} a day budget."
    return f"{t['messenger_first']} first messages a day; all messages on this account, every campaign together, stay under {t['messages']} a day."

TRACK = {"1st": "1st degree", "2nd/3rd": "2nd/3rd degree", "followup": "Tantra follow-up"}
link_note = ("{{domains.funnel_domain}} is still FILL_ in funnel-config.json: **do not load these steps into Tantra until it is filled and build.py has run again**, "
             "because Tantra renders an unknown tag as blank text.") if "domains.funnel_domain" in unresolved else "Built from funnel-config.json."

for p in PROFILES:
    k = p["key"]
    t = TIERS[p["account_tier"].split()[0]]
    out = [f"# {p['name']}: LinkedIn Outreach Templates", "",
           f"Role: **{p['role']}**. Voice: {p['voice']}", "",
           "| Field | Value |", "|---|---|",
           f"| LinkedIn URL | {p['linkedin_url']} |",
           f"| Title on LinkedIn | {p['title']} |",
           f"| LinkedIn plan | {p['linkedin_plan']} |",
           f"| Account tier for limits | {p['account_tier']} |",
           f"| Audience (only this profile contacts them) | {p['audience']} |",
           f"| UTM code | `utm_content={k}` on every link |", "",
           "## Daily Limits For This Profile", "",
           "Per LinkedIn account, across all four campaigns together, Monday to Friday. Set them in Tantra on the account: Connectors, Channels, LinkedIn, the account row, **Set daily and weekly sending limits**.", "",
           "| Limit | Value |", "|---|---|",
           f"| Connection requests | Start at {t['connect']} a day (connector {t['connect'] - t['ce_connect']}, content engagement and InMail follow-ups {t['ce_connect']}). Raise by 5 a day only after two clean weeks, up to {t['max_connect']}. Never above {WEEKLY_CAP} a week |",
           f"| Messages | {t['messages']} a day, all campaigns |",
           f"| Profile visits | {t['visits']} a day |",
           f"| InMail | {t['inmail']} a day |", "",
           "A clean week means no LinkedIn warning and a steady acceptance rate. On any warning, drop back to the last clean week's numbers.", ""]
    for i, ctype in enumerate(TYPES, 1):
        out += [f"## Set {i}: {TITLES[ctype]}", "",
                f"**Who:** {WHO[ctype]}", "",
                f"**Personalisation fields:** {FIELDS[ctype]}", "",
                f"**Registration link (the exact text in the copy):** `{reg_url(k, ctype)}`. {link_note}", "",
                f"**Daily limit:** {limit_line(t, ctype)}", "",
                "**Stop rules:** a reply, a registration from any source (CRM `webinar.registered`) or a do-not-contact request removes the person from every LinkedIn campaign the same day.", "",
                "| Track | Step | Wait (days after previous step) | Action | Chars (worst case) |", "|---|---|---|---|---|"]
        for s in COPY[k][ctype]:
            track = TRACK.get(s["track"], "manual" if s["action"] == I else "main")
            when = f" ({s['when']})" if s["when"] else ""
            out.append(f"| {track} | {s['no']} | {s['delay']}{when} | {ACTION_LABEL[s['action']]} | {s['n'] if s['r_message'] else 'n/a'} |")
        out.append("")
        for s in COPY[k][ctype]:
            if s["action"] == V:
                continue
            prefix = TRACK.get(s["track"], "Manual" if s["action"] == I else "")
            out += [f"### {prefix + ', ' if prefix else ''}Step {s['no']}: {ACTION_LABEL[s['action']]}", ""]
            if s["r_subject"]:
                out += [f"Subject: `{s['r_subject']}`", ""]
            out += ["```text", s["r_message"], "```", ""]
    (HERE / "profiles").mkdir(exist_ok=True)
    (HERE / "profiles" / f"{k}.md").write_text("\n".join(out))

print(f"sets: {sum(len(COPY[k]) for k in COPY)} (6 profiles x 4 types)")
print(f"connection notes: {len(notes)}, longest worst case {max(x[3] for x in notes)} chars")
print("csv rows: " + ", ".join(f"{g} {len(r)}" for g, r in GROUPS.items()))
print(f"distinct across senders: {len(seen_full)} messages, {len(seen_open)} openings")
if unresolved:
    print("NOT READY to import: still FILL_ in funnel-config.json: " + ", ".join(sorted(unresolved)))
for f in fails:
    print("FAIL " + f)
if fails:
    sys.exit(1)
print("checks: 0 failures")
