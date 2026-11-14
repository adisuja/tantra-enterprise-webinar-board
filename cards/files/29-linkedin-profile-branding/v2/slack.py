"""Writes v2/SLACK_MESSAGES.md: one Slack message per teammate, in Adi's voice, plus one Claude Code prompt that does the
whole setup in order: (1) LinkedIn connected in the Tantra app, (2) LinkedIn profile rebrand through OpenCLI,
(3) Content Engine sign in and Team page checklist, (4) review and approve their pieces in the Engine review tab.
Titles and headlines come from gen_spec.py; the profile steps from TEAM_GUIDE.md; review links and piece counts from
tantra-content outputs/content/batch-4/engine.json (copied into REVIEW below after each engine push).
Run: python3 deliverables/29-linkedin-profile-branding/v2/slack.py"""
import pathlib, re

HERE = pathlib.Path(__file__).parent
PACK = 'https://adisuja.github.io/tantra-enterprise-webinar-pages/linkedin-profiles/v2/'
ENGINE = 'https://content.usetantra.com'
src = (HERE / 'gen_spec.py').read_text()
HEADLINES = dict(re.findall(r"\n    '(\w+)': '(.+?)',", src[src.index('HEADLINES = {'):src.index('}', src.index('HEADLINES = {'))]))
guide = (HERE / 'TEAM_GUIDE.md').read_text()
PROFILE_PROMPT = re.search(r'## The Prompt for Claude Code\n\n```text\n(.*?)```', guide, re.S).group(1)
PROFILE_PROMPT = re.sub(r'^My key is: ____.*\n\n?', '', PROFILE_PROMPT)

# One review link per piece (review_links.json, from the 13 Nov batch 4 push): /tantra/review?item=<id> opens that
# piece in the Engine for the signed in teammate, and survives the sign in redirect.
import datetime, json
LINKS = json.loads((HERE / 'review_links.json').read_text())['links']


def day(d):
    return datetime.date.fromisoformat(d).strftime('%a %-d %b') if d else 'no date'


def link_lines(k):
    return '\n'.join(f"{day(x['date'])}, {x['topic']}: {x['url']}" for x in LINKS[k])


# Engine channels on 13 Nov (GET /api/tantra/profiles): Bharath had no LinkedIn channel at all.
NO_LINKEDIN_YET = {'bharath'}

TEAM = [  # key, first name, full name, profile
    ('bhaskar', 'Bhaskar', 'Bhaskar Dev', 'https://www.linkedin.com/in/bhaskar-dev/'),
    ('nelbin', 'Nelbin', 'Nelbin Joseph', 'https://www.linkedin.com/in/nelbin-xav/'),
    ('aquila', 'Aquila', 'Aquila Eldho', 'https://www.linkedin.com/in/aquilaeldho/'),
    ('bharath', 'Bharath', 'Bharath Krishna Pai', 'https://www.linkedin.com/in/bkp31415/'),
    ('ben', 'Ben', 'Ben Basil Tomy', 'https://www.linkedin.com/in/ben-basil-tomy-5533b9218/'),
]


def start(k):
    return HEADLINES[k].split(' | ')[0]


def prompt(k, full, url):
    head = start(k)
    title = head.replace(' @ Tantra', '')
    n = len(LINKS[k])
    li_state = ('My LinkedIn is NOT connected in the Tantra app yet, so this part is required.' if k in NO_LINKEDIN_YET
                else 'My LinkedIn should already be connected in the Tantra app; check it still says Connected and reconnect it if not.')
    return f"""My key is: {k}
My name on LinkedIn: {full}
My profile: {url}
My role title at Tantra: {title}
My headline must start with: {head}
(Use the full headline from my section of PROFILE_SPEC.md exactly; it starts with the words above.)

You are setting me up end to end for Tantra, in four parts, in this order. Finish and check each part before starting the next, and give me a short status table after each part. Work in my signed-in Chrome through OpenCLI (Part B, Step 0 below sets OpenCLI up; do that setup first, before Part A). The hard rules in Part B apply to every part: never type, ask for or store a password, code or cookie; if any site asks for one, stop and tell me exactly what to do, then wait.

PART A. Connect my LinkedIn in the Tantra app (usetantra.com). {li_state}
1. Open https://usetantra.com/sign-in . If I am not signed in, ask me to sign in myself with my Tantra login, then wait.
2. Open https://usetantra.com/connectors/channels/linkedin . Read the page with opencli browser state and tell me whether my LinkedIn account ({full}) is listed and its status.
3. If it is missing or not Connected: click "Connect account" (or "Reconnect" on my row), tick LinkedIn only, continue. LinkedIn will ask me to sign in inside that window: I type my own email, password and any code. Then confirm my row says Connected.
4. Do not change any outreach limits, campaigns or other settings on that page. The Content Engine picks this connection up on its own within about 15 minutes, while you do Part B.

PART B. Rebrand my LinkedIn profile. Follow these instructions exactly:

{PROFILE_PROMPT.rstrip()}

PART C. Set me up in the Tantra Content Engine ({ENGINE}).
1. Open {ENGINE}/login and ask me to sign in with my Tantra login (the same one as usetantra.com). If it says I have no access, or asks me to set a password, tell me to use the welcome email from the Content Engine or to ask Adi for a fresh invite, then wait.
2. Open {ENGINE}/tantra/team and read my row of the "Getting set up" checklist. Report each item: Set your password, Connect your LinkedIn, Write your expertise line, Adi matches your LinkedIn account, Switch on team comments (optional), Create an API key (optional).
3. Connect your LinkedIn: it should show done after Part A (the sync runs every 15 minutes). If it is not done after 20 minutes, open {ENGINE}/accounts and tell me what the LinkedIn channels show, and tell me to message Adi; do not connect a second LinkedIn channel yourself.
4. Expertise line: draft one to three sentences in the first person from my About and role description in PROFILE_SPEC.md (what I know best, plain words, no dashes). Show it to me, and only after I say yes, paste it into the expertise box on the Team page and click Save.
5. Team comments (posting approved comments in my name) and the API key are my choice: explain each in one line and do nothing unless I say so.
6. "Adi matches your LinkedIn account" is done by Adi. If it is not done, tell me to message Adi.

PART D. Review my {n} content pieces in the Content Engine and approve them for my profile. Do this only after Part B is done, because the posts show my new headline and photo.
1. Each piece has its own link. Open them one at a time, in this order:
{link_lines(k)}
2. On each one, read the phone preview (post, first comment, images or carousel, team comments under it), the middle column (the PDF or page people get, page by page, and the public preview link), and the follow-up messages under it (email subject and body, WhatsApp, SMS, LinkedIn DM and connection note). Check: it reads like me and matches my new title and headline; no em or en dashes; no GrowthClub, no CMO, CTO or other old title; every link goes to jointantra.com, crm.usetantra.com, go.usetantra.com or the resource page and keeps its utm parameters; the follow-up messages name the right resource and link; dates and the workshop date make sense; numbers are ones I am happy to say in public.
3. Show me one table: piece id, date, first line of the post, what you checked, anything you would change. Then go through the pieces one by one with me. For each one, do exactly what I say: Approve and schedule, Request changes (type my feedback in the box), edit a follow-up message (change it in its box and click Save under it), or leave it. Never approve a piece or save a message without my yes for that piece.
4. Finish with a table of all {n} pieces and their status, and a screenshot of the Review tab. Tell me to post both screenshots (profile and Review tab) in Slack.
"""


def message(k, n_, full):
    head = start(k)
    title = head.replace(' @ Tantra', '')
    n, first = len(LINKS[k]), day(LINKS[k][0]['date'])
    li = ("Your LinkedIn isn't connected in the Tantra app yet, so that's the one thing to do first: without it the Engine can't post for you. "
          if k in NO_LINKEDIN_YET else "Your LinkedIn should already be connected there, it just checks it's still live. ")
    return (f"Hey {n_}, this gets you fully set up for Tantra in one go, about 45 minutes in total and mostly Claude doing the clicking. "
            f"Your new title is \"{title}\" and your headline starts with \"{head}\".\n\n"
            "It runs in this order. First it connects your LinkedIn in the Tantra app at usetantra.com. "
            + li +
            "Then it rebrands your LinkedIn profile: cover, photo, headline, About, role, links and Featured, all from your section of the team pack: "
            f"{PACK}\n\n"
            f"After that it signs you into the Content Engine at {ENGINE} and goes through your setup checklist on the Team page. "
            f"Last, it walks you through the {n} posts we've written for you. Each one has its own link, so you can also open them yourself "
            "(sign in with your Tantra login if it asks):\n\n"
            + link_lines(k) + "\n\n"
            "Each link shows the post as it'll look on LinkedIn, the PDF or page people get when they comment, and the email, WhatsApp, SMS and LinkedIn "
            "messages that send it to them. You can copy or edit any of those right there. "
            f"Approve the posts you're happy with and ask for changes on the rest, ideally before {first} when the first one is due. "
            "Please do this part after the profile is done, since the posts show your new headline and photo.\n\n"
            "To run it: install Claude Code if you haven't (npm install -g @anthropic-ai/claude-code) and sign in, then in Terminal run "
            "mkdir -p ~/tantra-setup && cd ~/tantra-setup && claude and paste the prompt below. "
            "Keep Chrome open with LinkedIn in front, and type any password or code yourself when a site asks. Claude never approves a post without your yes.\n\n"
            "When it's done, drop the two screenshots it gives you (your profile and your Review tab) in here. Thanks! Here's the prompt:")


out = ["# Slack Messages: Tantra Setup for Each Teammate (14 November 2026)", "",
       "Generated by `slack.py`. One message per teammate, in Adi's voice. Copy everything inside one person's outer block and paste it into their "
       "Slack DM: Slack shows the note as text and the prompt as a code block with a copy button. The prompt runs four parts in order: "
       "(A) LinkedIn connected in the Tantra app, (B) LinkedIn profile rebrand through OpenCLI, (C) Content Engine sign in and Team page checklist, "
       "(D) review and approve their pieces in the Engine's Review tab.", "",
       "| Person | Headline starts with | Pieces in review | Tantra app LinkedIn (13 Nov) |", "| --- | --- | --- | --- |"]
for k, n_, full, _ in TEAM:
    out.append(f"| {n_} | {start(k)} | {len(LINKS[k])} ({', '.join(x['id'] for x in LINKS[k])}) | {'not connected' if k in NO_LINKEDIN_YET else 'connected'} |")
out += ["", "Adi, before or while they run it: confirm each person's LinkedIn match on the Engine Team page (" + ENGINE + "/tantra/team, LinkedIn accounts) once it appears, "
        "and resend an Engine invite to anyone who cannot sign in. Bharath's match can only happen after he connects LinkedIn in the Tantra app.", ""]
for k, n_, full, url in TEAM:
    out += [f"## {n_}", "", "~~~text", message(k, n_, full), "```", prompt(k, full, url).rstrip(), "```", "~~~", ""]
text = '\n'.join(out) + '\n'
assert chr(0x2013) not in text and chr(0x2014) not in text, 'dash in Slack messages'
(HERE / 'SLACK_MESSAGES.md').write_text(text)
print('SLACK_MESSAGES.md written:', len(TEAM), 'messages')
