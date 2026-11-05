#!/usr/bin/env python3
"""27 retargeting: copy for weeks 3 to 6 (email, WhatsApp), LinkedIn via Tantra (weeks 1 to 6)
and the Meta and LinkedIn ad texts. Weeks 1 and 2 of email and WhatsApp are item 22's tracks B and C.

Run:  python3 deliverables/27-retargeting/build.py
Writes email.csv, whatsapp.csv, linkedin.csv, ads.csv, emails/*.html, emails/index.html, COPY.md.
Offsets are minutes from webinar start.
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "15b-pre-nurture"))
import nurture_lib as L

STOP = "Reply STOP to opt out."
DAY = 1440
WHO = ("segment early_leaver or no_show, status active on the day (retarget_segments.py); email to all, WhatsApp to whatsapp_opt_in; "
       "stops on booking.created, contact.replied, contact.opted_out, deal.won, deal.lost, or a new webinar.registered")
BOOK = ("Book My Evaluation Call", "booking_url")

STEPS = [
dict(step_id="27-W3", title="Week 3: the three numbers that decide a webinar", anchor="webinar_start", offset=19 * DAY, template="rt_w3", trigger=WHO,
 email=dict(subject="The 3 numbers that decide every webinar", preheader="Reach, show-up, calls per 100 live.", eyebrow="Week 3",
   headline="The Three Numbers That Decide Every Webinar",
   paras=["Hi {{first_name}},",
     "A few weeks ago you signed up for my live session. Here's the one idea from it I'd want you to keep, even if you never watch the recording.",
     "Every webinar comes down to three numbers:",
     "1. **Reach to registration.** Of everyone who hears about it, how many sign up?\n2. **Registration to live.** Of everyone who signs up, how many show up?\n3. **Live to calls.** Of everyone in the room, how many book a call?",
     "On Growth Idea's biggest webinar with us, those were 2.0%, about 16% and about 8 calls per 100 live. Not perfect. Measured, every week, so we knew which one to fix next.",
     "Do you know yours? If not, that's the first thing we'd look at on an evaluation call."],
   cta=BOOK, cta2=("see how we measure them in the recording", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, it's [[host]]. Every webinar comes down to 3 numbers: reach to registration, registration to live, live to calls. Do you know yours?\n\nIf not, we can find them with you: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="27-W4", title="Week 4: what a done-with-you build looks like", anchor="webinar_start", offset=26 * DAY, template="rt_w4", trigger=WHO,
 email=dict(subject="What \"done with you\" actually means", preheader="Four parts, built with your team.", eyebrow="Week 4",
   headline="What \"Built With You\" Actually Means",
   paras=["Hi {{first_name}},",
     "\"Done for you\" usually means someone builds a thing, hands it over, and leaves. Six months later nobody on your team knows how it works.",
     "We do it differently. [[offer]] is built with your team:",
     "1. **[[include1]].**\n2. **[[include2]].**\n3. **[[include3]].**\n4. **[[include4]].**",
     "It's [[price]]. It fits teams that want it built with them and have [[fit_budget]] to invest in the next 12 months.",
     "It starts with a [[call_minutes]]-minute evaluation call. If it fits, you get [[proposal]]."],
   cta=BOOK, cta2=("watch the session first", "recording_url"), cta2_lead="Or"),
 ),

dict(step_id="27-W5", title="Week 5: everything we built for one client", anchor="webinar_start", offset=33 * DAY, template="rt_w5", trigger=WHO,
 email=dict(subject="Everything we built for one client, in one list", preheader="Not one tactic. A system.", eyebrow="Week 5",
   headline="Everything We Built for One Client, in One List",
   paras=["Hi {{first_name}},",
     "People sometimes ask what we actually build. So here's the full list for one client: Growth Idea, a UK business-coaching group, over 11 webinars between May 2025 and February 2026.",
     "- Calendar-invite outreach at 12,000 to 120,000 invites per webinar, plus LinkedIn event invites and email\n- Registration, with a long and a short landing page tested against each other\n- Reminders, the live session and follow-up\n- A weekly analytics sheet and a 12-item experiment log\n- Content calendars and a leads tracker",
     "Across those 11 webinars: 765,105 people reached, 6,517 registered, 1,384 live and 80 sales calls booked.",
     "Not one tactic. A system, run every week. That's what the evaluation call scopes for you."],
   cta=BOOK, cta2=("watch how it fits together", "recording_url"), cta2_lead="Or"),
 whatsapp="Hi {{first_name}}, what we built for one client over 11 webinars: calendar-invite outreach, two landing pages, reminders, follow-up and a weekly numbers sheet. Result: 6,517 registered and 80 sales calls.\n\nScope yours: {{booking_url}}\nRecording: {{recording_url}}\n\n" + STOP),

dict(step_id="27-W6", title="Week 6: last email and last WhatsApp, then I stop", anchor="webinar_start", offset=41 * DAY, template="rt_w6", trigger=WHO + "; last email and last WhatsApp of item 27, sent together on day 41; on day 42 the contact drops out of every message and audience",
 email=dict(subject="I'll stop following up after this", preheader="One last link, then the newsletter only.", eyebrow="Week 6",
   headline="This Is My Last Follow-Up",
   paras=["Hi {{first_name}},",
     "Six weeks ago you signed up for my live session. This is the last follow-up I'll send about it.",
     "If the timing isn't right, no problem at all. If you ticked the newsletter box, you'll get one breakdown of the system a week from now on, and nothing else.",
     "If the timing is right, here's the link one last time."],
   cta=BOOK, cta2=("the recording stays here", "recording_url"), cta2_lead="And"),
 whatsapp="Hi {{first_name}}, it's [[host]]. Last message from me about the session you signed up for.\n\nIf the timing's right: {{booking_url}}\nThe recording stays here: {{recording_url}}\n\nThanks either way. " + STOP),
]

LINKEDIN = [
 {"step_id": "27-L1", "trigger": "webinar_start | early_leaver or no_show with a LinkedIn profile URL, not yet connected to Adi; Tantra LinkedIn campaign on Adi's account; skip if excluded",
  "offset_minutes": 6 * DAY, "channel": "linkedin_connection", "template_name": "rt_li_connect", "subject": "",
  "body": "Hi {{linkedin_first_name}}, you signed up for my live session on the AI revenue engine. I'd like to connect here. [[host]]"},
 {"step_id": "27-L2", "trigger": "webinar_start | connected (L1 accepted or already a connection), still active; Tantra send_message step",
  "offset_minutes": 20 * DAY, "channel": "linkedin_message", "template_name": "rt_li_msg1", "subject": "",
  "body": "Thanks for connecting, {{linkedin_first_name}}. The recording of the session you signed up for is here if it's useful: {{recording_url}}\n\nIf you'd rather have the system built with your team, my team runs [[call_minutes]]-minute evaluation calls: {{booking_url}}"},
 {"step_id": "27-L3", "trigger": "webinar_start | connected, still active, no reply to L2; Tantra send_message step; last LinkedIn touch",
  "offset_minutes": 34 * DAY, "channel": "linkedin_message", "template_name": "rt_li_msg2", "subject": "",
  "body": "{{linkedin_first_name}}, one question: where do leads go quiet in your funnel right now? Registration, show-up, or after the call?\n\nIf it's worth a conversation, here's my team's calendar: {{booking_url}}"},
]

ADS_COLUMNS = ["ad_id", "platform", "audiences", "phase_days", "format", "primary_text", "headline", "description", "cta_button", "destination",
               "locations", "location_rule", "language", "ad_schedule", "budget", "creative_brief"]

# Targeting for a UK and EU audience (RETARGETING_PLAN.md, "Ad Settings"). Countries: item 2's language tiers.
from retarget_segments import GEO_TIERS
LOCATIONS = "; ".join("Tier %d: %s" % (t, ", ".join(v[0] for v in GEO_TIERS.values() if v[1] == t)) for t in (1, 2, 3))
TARGETING = {
    "meta": {"locations": LOCATIONS, "location_rule": "People living in this location",
             "language": "English (All)",
             "ad_schedule": "Lifetime budget, Run ads on a schedule: every day 07:00 to 22:00, Use viewer's time zone",
             "budget": "FILL_RETARGET_BUDGET_GBP (state it in GBP; ad account currency GBP, time zone Europe/London)"},
    "linkedin": {"locations": LOCATIONS, "location_rule": "Permanent location",
                 "language": "English (profile language)",
                 "ad_schedule": "Run continuously; if Campaign Manager offers ad scheduling, Monday to Friday 07:00 to 20:00 (unverified)",
                 "budget": "FILL_RETARGET_BUDGET_GBP (state it in GBP; ad account currency GBP)"},
}
UTM = "?utm_source=%s&utm_medium=paid&utm_campaign=tew-retarget&utm_content=%s"
ADS = []
for plat, short in (("meta", "meta"), ("linkedin", "li")):
    ADS += [
     {"ad_id": "%s-replay-1" % short, "platform": plat, "audiences": "early_leaver_replay, no_show_replay; exclude: exclude list",
      "phase_days": "0 to 13", "format": "single image",
      "primary_text": "Missed part of the live session? The full recording is up: the funnel, the RevOps OS, the traffic channels, and how we build it with your team.",
      "headline": "Watch the Full Recording", "description": "[[duration]] minutes with [[host]], founder of [[company]].",
      "cta_button": "Watch More" if plat == "meta" else "Learn more",
      "destination": "{{recording_url}}" + UTM % (plat, "%s-replay-1" % short),
      "creative_brief": "Adi's Kie.ai avatar (~/tantra-content/content/brand/people/adi/avatars/), paper #f7f8fb ground, headline in Clash Display, one volt #6d4aff accent, current Tantra mark. 1080x1080 (Meta) or 1200x627 (LinkedIn)."},
     {"ad_id": "%s-call-1" % short, "platform": plat, "audiences": "early_leaver_call, no_show_call; exclude: exclude list",
      "phase_days": "14 to 41", "format": "single image",
      "primary_text": "Want the AI revenue engine built with your team, not just explained? [[offer]]: [[inc1]], [[inc2]], and [[inc3]]. It starts with a [[call_minutes]]-minute evaluation call.",
      "headline": "Book an Evaluation Call", "description": "[[proposal]], if it fits.",
      "cta_button": "Book Now" if plat == "meta" else "Register",
      "destination": "{{booking_url}}" + UTM % (plat, "%s-call-1" % short),
      "creative_brief": "Adi's Kie.ai avatar, ink #0b0d12 ground, white headline, volt accent on 'built with your team', current Tantra mark (white)."},
     {"ad_id": "%s-call-2" % short, "platform": plat, "audiences": "early_leaver_call, no_show_call; exclude: exclude list",
      "phase_days": "14 to 41", "format": "single image",
      "primary_text": "One client webinar with us: 99,859 people reached, 1,990 registrations, 321 people live, 25 sales calls. That's the engine we build with you.",
      "headline": "See What We'd Build for You", "description": "[[call_minutes]]-minute evaluation call.",
      "cta_button": "Book Now" if plat == "meta" else "Learn more",
      "destination": "{{booking_url}}" + UTM % (plat, "%s-call-2" % short),
      "creative_brief": "Type-only proof card: the four numbers stacked, paper ground, numbers in Clash Display, volt on '25 sales calls', current Tantra mark. No client logo."},
    ]

def main():
    problems, _ = L.build(STEPS, HERE, "27", footer_reason="You're getting this because you registered for {{webinar_title}}.",
                          gallery_title="27 Retargeting Emails, Weeks 3 to 6", wa_category="Marketing")
    li_rows = []
    for r in LINKEDIN:
        row = dict(r)
        row["body"] = L.resolve(row["body"])
        row["variables"] = L.var_column(L.named_vars(row["body"]), False)
        problems += L.check_text(row["step_id"], row["body"])
        if row["channel"] == "linkedin_connection" and len(row["body"].replace("{{linkedin_first_name}}", "Alexandra")) > 300:
            problems.append("%s: connection note over 300 characters" % row["step_id"])
        li_rows.append(row)
    with open(os.path.join(HERE, "linkedin.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=L.CSV_COLUMNS); w.writeheader(); w.writerows(li_rows)
    ad_rows = []
    for a in ADS:
        row = {k: L.resolve(v) for k, v in a.items()}
        row["description"] = row["description"][0].upper() + row["description"][1:]
        problems += L.check_text(row["ad_id"], " ".join(row.values()))
        row.update(TARGETING[row["platform"]])
        if row["platform"] == "meta" and len(row["headline"]) > 40:
            problems.append("%s: Meta headline over 40 characters" % row["ad_id"])
        if row["platform"] == "linkedin" and len(row["primary_text"]) > 600:
            problems.append("%s: LinkedIn intro text over 600 characters" % row["ad_id"])
        ad_rows.append(row)
    with open(os.path.join(HERE, "ads.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ADS_COLUMNS); w.writeheader(); w.writerows(ad_rows)
    # append LinkedIn and ads to COPY.md
    with open(os.path.join(HERE, "COPY.md"), "a") as f:
        f.write("\n## LinkedIn via Tantra (from Adi's account)\n\n")
        for r in li_rows:
            f.write("### %s (%s, day %d)\n\n%s\n\n```\n%s\n```\n\n" % (r["step_id"], r["channel"], r["offset_minutes"] // DAY, r["trigger"], r["body"]))
        f.write("## Ads (Meta and LinkedIn)\n\n")
        for r in ad_rows:
            f.write("### %s (%s, days %s)\n\n- Audiences: %s\n- Primary text: %s\n- Headline: %s\n- Description: %s\n- Button: %s\n- Destination: %s\n- Locations (%s): %s\n- Language: %s\n- Schedule: %s\n- Budget: %s\n- Creative: %s\n\n" % (
                r["ad_id"], r["platform"], r["phase_days"], r["audiences"], r["primary_text"], r["headline"], r["description"], r["cta_button"], r["destination"],
                r["location_rule"], r["locations"], r["language"], r["ad_schedule"], r["budget"], r["creative_brief"]))
    for p in problems:
        print("PROBLEM", p)
    print("27 build: %d steps, %d LinkedIn, %d ads, %d problems" % (len(STEPS), len(li_rows), len(ad_rows), len(problems)))
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
