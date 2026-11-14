"""Writes the Slack messages for the two Evangelists (Scott, Conor; Adi 2026-11-14) to SLACK_MESSAGES_EVANGELISTS.md
and slack/<key>.txt. Same depth as slack.py: a note in Adi's voice, then one Claude Code prompt that runs, in order,
(A) LinkedIn in the Tantra app, (B) the LinkedIn profile rebrand (TEAM_GUIDE.md prompt), (C) their own Content Engine
onboarding and channels, (D) a look-only tour of the review pages and the CRM.

Secrets never go in this repo: the committed files keep placeholders. With --fill <json>, it also writes copy-ready
files with the set-password links filled in to the folder named by --out (outside git). Passwords are filled by Adi.
Never mention how anyone is paid.
Run: python3 deliverables/29-linkedin-profile-branding/v2/slack_evangelists.py [--fill links.json --out DIR]"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
PACK = 'https://adisuja.github.io/tantra-enterprise-webinar-pages/linkedin-profiles/v2/'
ENGINE = 'https://content.usetantra.com'
CRM = 'https://crm.usetantra.com/login'
guide = (HERE / 'TEAM_GUIDE.md').read_text()
PROFILE_PROMPT = re.search(r'## The Prompt for Claude Code\n\n```text\n(.*?)```', guide, re.S).group(1)
PROFILE_PROMPT = re.sub(r'^My key is: ____.*\n\n?', '', PROFILE_PROMPT)
LINKS = json.loads((HERE / 'review_links.json').read_text())['links']
SAMPLE = {x['id']: x for v in LINKS.values() for x in v}
SAMPLES = [('EA1', "an animated image post that gives away a one page PDF (Ben's)"),
           ('EC1', "a 9 page carousel (Ben's)"),
           ('RA3', "an animated giveaway that sends a 5 page prompt pack (Bharath's)")]

PEOPLE = [  # key, first name, full name, engine login email
    ('scott', 'Scott', 'Scott McArthur', 'scott@usetantra.com'),
    ('conor', 'Conor', 'Conor Norton', 'conor@usetantra.com'),
]
HEAD = {'scott': 'Evangelist @ Tantra | I help B2B founders turn cold traffic into booked sales calls with AI RevOps',
        'conor': 'Evangelist @ Tantra | AI RevOps for B2B teams: more booked calls from the traffic you already have'}
PH = {'join': '{{SET_PASSWORD_LINK}}', 'team_engine': '{{TEAM_ENGINE_PASSWORD}}', 'team_crm': '{{TEAM_CRM_PASSWORD}}', 'own_crm': '{{YOUR_CRM_PASSWORD}}'}


def samples():
    return '\n'.join(f"{what}: {SAMPLE[i]['url']}" for i, what in SAMPLES)


def message(k, first, email):
    return (f"Hey {first}! Welcome properly to the Tantra crew. I'd love to get you fully set up, and there's a lot here I think you'll enjoy playing with.\n\n"
            f"First, your LinkedIn. We're giving everyone a matching Tantra profile, and yours is ready: your title is Evangelist, and your headline starts with \"Evangelist @ Tantra\". "
            f"Your cover, About, role description, skills and links are all in your section of the team pack: {PACK}#{k}\n\n"
            "Second, the Content Engine, which we've just launched. It writes really good LinkedIn content for each of us (posts, 9 page carousels, animated image posts, "
            "giveaways that send a PDF to everyone who comments, polls, first comments and even the team comments under each post), and it publishes it on schedule from your own accounts. "
            "It's not just LinkedIn either: you can connect Facebook, Instagram, X, Threads, YouTube, Pinterest, Bluesky and more, and post everywhere from one place. "
            "I'd really love for you to let us run content for your profile too. Have a look at what it's already made for the team:\n\n"
            f"{samples()}\n\n"
            "Each of those shows the post exactly as it'll look on LinkedIn, the PDF people get, and the email, WhatsApp, SMS and LinkedIn messages that send it to them, which you can copy or edit right there.\n\n"
            f"Here's your access. Your own Content Engine login is ready: set your password here (the link works for 30 days): {PH['join']}\n"
            f"After that, sign in at {ENGINE}/login with {email}.\n\n"
            "To look around the whole team's setup, you can also use the team account:\n"
            f"Content Engine: {ENGINE}/login?password=1\n"
            "Username: team@growthclubpro.com\n"
            f"Password: {PH['team_engine']}\n\n"
            "And the Tantra CRM, which you'll be using a lot for your own pipeline and workflows:\n"
            f"CRM: {CRM}\n"
            "Team account: team@growthclubpro.com\n"
            f"Password: {PH['team_crm']}\n"
            f"Your own account: {email}\n"
            f"Password: {PH['own_crm']}\n\n"
            "In the team accounts, please just look around and don't approve, schedule, send or change anything there, since it's everyone's live setup. Your own logins are yours to play with as much as you like.\n\n"
            "The easiest way to do all of this is to let Claude Code do the clicking. Install it if you haven't (npm install -g @anthropic-ai/claude-code) and sign in, then in Terminal run "
            "mkdir -p ~/tantra-setup && cd ~/tantra-setup && claude and paste the prompt below. It connects your LinkedIn, rebrands your profile, walks you through the Content Engine onboarding "
            "and gives you a quick tour of the review pages and the CRM. Keep Chrome open with LinkedIn in front, and type any password or code yourself when a site asks. It takes about 45 minutes.\n\n"
            "One more thing, and it matters a lot to me: please use all of this properly and tell me what you think. We're moving our whole workflow onto our own infrastructure and we're in the last few steps. "
            "Any feedback, anything that feels clunky, any feature you wish it had, send it my way. If it makes sense, we can usually have it live within a couple of hours.\n\n"
            "When you're done, drop the screenshots Claude gives you in here. Thanks! Here's the prompt:")


def prompt(k, full, email):
    return f"""My key is: {k}
My name on LinkedIn: {full}
My profile: my own LinkedIn profile (https://www.linkedin.com/in/me/ opens it; opencli linkedin whoami gives the exact URL)
My role title at Tantra: Evangelist
My headline must start with: Evangelist @ Tantra
(Use the full headline from the section "{full}" in PROFILE_SPEC.md exactly. My section is the one whose heading starts with my full name.)
I have no branded profile photo in the pack: skip the photo step and keep my current photo. The links in my Links table are the full jointantra.com links: use each one exactly as listed, in every place it names, Featured included.
My Content Engine login is {email}, and I already have my set-password link from Adi's Slack message.

You are setting me up for Tantra in four parts, in this order. Finish and check each part before starting the next, and give me a short status table after each part. Work in my signed-in Chrome through OpenCLI (Part B, Step 0 below sets OpenCLI up; do that setup first, before Part A). The hard rules in Part B apply to every part: never type, ask for or store a password, code or cookie; if any site asks for one, stop and tell me exactly what to do, then wait.

PART A. Connect my LinkedIn in the Tantra app (usetantra.com).
1. Open https://usetantra.com/sign-in . If I am not signed in, ask me to sign in myself with my Tantra login, then wait.
2. Open https://usetantra.com/connectors/channels/linkedin . Read the page with opencli browser state and tell me whether my LinkedIn account ({full}) is listed and its status.
3. If it is missing or not Connected: click "Connect account" (or "Reconnect" on my row), tick LinkedIn only, continue. LinkedIn will ask me to sign in inside that window: I type my own email, password and any code. Then confirm my row says Connected.
4. Do not change any outreach limits, campaigns or other settings on that page.

PART B. Rebrand my LinkedIn profile. Follow these instructions exactly:

{PROFILE_PROMPT.rstrip()}

PART C. My own Content Engine account ({ENGINE}).
1. Ask me to open the set-password link from Adi's Slack message myself and choose a password (never type it for me). Then open {ENGINE}/login and ask me to sign in with {email}.
2. Open {ENGINE}/tantra/team and read my row of the "Getting set up" checklist. Report each item: Set your password, Connect your LinkedIn, Write your expertise line, Adi matches your LinkedIn account, Switch on team comments (optional), Set the posting days and times of each of your channels, Create an API key (optional).
3. Connect your LinkedIn: click its "Do it now" link (it opens {ENGINE}/connect/linkedin). LinkedIn asks me to sign in and approve: I do that myself. Confirm the checklist shows it done.
4. Other channels: show me the "New channel" item in the sidebar menu. It opens the channel picker (Facebook, Instagram, X, Threads, YouTube, Pinterest, Bluesky and more). Ask me which ones I want, and connect only those; I sign in to each network myself.
5. Expertise line: draft one to three sentences in the first person from my About and role description in PROFILE_SPEC.md. Show it to me, and only after I say yes, paste it into the expertise box on the Team page and click Save.
6. Posting times: open the posting times section on the Team page and set my channels to Monday to Friday at a time I choose. Ask me first.
7. Team comments and the API key are my choice: explain each in one line and do nothing unless I say so. "Adi matches your LinkedIn account" is done by Adi.

PART D. A look-only tour, so I can see what the Content Engine and the CRM can do. In the team accounts I must not approve, request changes, schedule, edit, send, delete or change anything: read only.
1. Ask me to sign out of my own Engine account and sign in at {ENGINE}/login?password=1 with team@growthclubpro.com and the password from Adi's message (I type it). Then open these three posts one at a time:
{samples()}
   For each, describe in two or three lines what I am looking at: the phone preview (post, first comment, carousel or animation, team comments), the middle column (the PDF people get, page by page, and the public preview link) and the follow-up messages (email, WhatsApp, SMS, LinkedIn). Then show me the Scheduled and Published tabs, and the Insights page, without clicking any action button.
2. Ask me to sign in at {CRM} with my own account ({email}) and the password from Adi's message (I type it). Show me around: contacts, the pipeline, sequences, booking pages, the Links page and reporting. Explain each in one line. In my own account I can try things out; never send a message to a real contact without asking me first.
3. Finish with a table: everything set up in Parts A to C (done or not, and why), and a short list of what I found interesting or confusing on the tour, so I can send it to Adi as feedback.
4. Take a screenshot of my LinkedIn profile and of my Content Engine Team page, and tell me to post both in Slack with my feedback.
"""


def build(fill=None):
    out = ["# Slack Messages: the two Evangelists (14 November 2026)", "",
           "Generated by `slack_evangelists.py`. One message per person, in Adi's voice. Before sending, replace the placeholders: "
           "`{{SET_PASSWORD_LINK}}` (from the tantra-ops run of `tasks/invite-evangelists.sh`; the copy-ready files already have it), "
           "`{{TEAM_ENGINE_PASSWORD}}`, `{{TEAM_CRM_PASSWORD}}` and `{{YOUR_CRM_PASSWORD}}`. Never commit a filled copy.", "",
           "| Person | Title | Headline starts with | Engine login | Engine workspace |", "| --- | --- | --- | --- | --- |"]
    out += [f"| {f} | Evangelist | {HEAD[k]} | {e} | {f} (created 14 Nov, review owner Adi until they join) |" for k, f, _, e in PEOPLE]
    out.append("")
    files = {}
    for k, first, full, email in PEOPLE:
        body = message(k, first, email) + "\n```\n" + prompt(k, full, email).rstrip() + "\n```"
        files[k] = body
        out += [f"## {first}", "", "~~~text", body, "~~~", ""]
    text = '\n'.join(out) + '\n'
    assert chr(0x2013) not in text and chr(0x2014) not in text, 'dash in Slack messages'
    assert 'commission' not in text.lower(), 'pay talk in Slack messages'
    (HERE / 'SLACK_MESSAGES_EVANGELISTS.md').write_text(text)
    (HERE / 'slack').mkdir(exist_ok=True)
    for k, body in files.items():
        (HERE / 'slack' / f'{k}.txt').write_text(body + '\n')
    if fill:
        links, outdir = fill
        outdir.mkdir(parents=True, exist_ok=True)
        for k, body in files.items():
            (outdir / f'{k}.txt').write_text(body.replace(PH['join'], links[k]) + '\n')
    print('evangelist messages written:', ', '.join(files), '(filled copies in ' + str(fill[1]) + ')' if fill else '')


if __name__ == '__main__':
    args = sys.argv[1:]
    fill = None
    if '--fill' in args:
        fill = (json.loads(pathlib.Path(args[args.index('--fill') + 1]).read_text()), pathlib.Path(args[args.index('--out') + 1]))
    build(fill)
