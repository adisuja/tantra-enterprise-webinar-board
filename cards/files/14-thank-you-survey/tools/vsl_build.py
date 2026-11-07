"""Builds the VSL documents for item 14 from vsl_scenes.py.

  python3 tools/vsl_build.py            # docs only
  python3 tools/vsl_build.py --media    # docs + reference clips and stills (needs the two videos on the Desktop)

Public (board): 4-VIDEO-SCRIPTS.md, 9-VSL-PRODUCTION-PLAN.md.
Local only (private/, git-ignored, never on the public board): reference clips, stills, transcripts, storyboard.html.
"""
import html, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vsl_scenes as S

ROOT = Path(__file__).resolve().parents[1]
PRIV = ROOT / "private" / "vsl-reference"
SRC = {"ty": Path.home() / "Desktop/thank you page 1.mp4", "up": Path.home() / "Desktop/upsell VSL.mp4"}
WPM = 188  # Adi's read after jump cuts; the references run at 218 to 223

def wc(t):
    return len(re.findall(r"[\w$%+.,']+", t))

def tc(sec):
    m, s = divmod(int(round(sec)), 60)
    return f"{m}:{s:02d}"

def timed(scenes):
    t, out = 0.0, []
    for x in scenes:
        d = wc(x["vo"]) / WPM * 60 + 0.25
        out.append((x, t, t + d))
        t += d
    return out, t

VIDEOS = [
    dict(key="ty", title="Thank-you page video", page="Thank-you page 1 (/thank-you/), above the survey", cfg="media.survey_video_url",
         scenes=S.THANK_YOU, off=S.TY_OFFSET, ref_len="2:01 (speech 0:00 to 2:01; the file adds 6 s of player pre-roll)", target="2:01 to 2:11"),
    dict(key="up", title="Upsell video: the Tantra RevOps OS", page="The upsell page (/vip/), between the survey and the confirmed page", cfg="media.vip_video_url",
         scenes=S.UPSELL, off=S.UP_OFFSET, ref_len="6:20 (the file is 8:02, but 6:21 to 8:02 is a black screen recording)", target="6:20 to 6:30"),
]

# ---------------------------------------------------------------- 4-VIDEO-SCRIPTS.md
def scripts_md():
    o = ["# Video scripts: the thank-you video and the Tantra RevOps OS upsell video", "",
         "Adi, to camera, alone. Rewritten 2026-11-08 from the two reference videos you sent, beat for beat, at the reference length (10 seconds over at most).", "",
         "How to read them: at your normal pace. The editor removes the pauses with jump cuts, as the references do, and that lands each video on its target. "
         "Before the shoot, read U13 and U14 aloud once and time it (about 60 seconds of script). Under 170 words a minute means the upsell will run long: use both tiers of cuts under 'If it runs long'. Then time your first full take. If the thank-you take runs over 2:25 raw, or the upsell over 7:00 raw, cut in the order listed.", ""]
    for v in VIDEOS:
        rows, total = timed(v["scenes"])
        words = sum(wc(x["vo"]) for x in v["scenes"])
        o += [f"## {v['title']}", "",
              f"Goes on: {v['page']} (config `{v['cfg']}`). Reference length: {v['ref_len']}. Target: {v['target']}. "
              f"This script: {words} words, about {tc(total)} after jump cuts.", "",
              "| Time | Scene | What you say | Camera |", "|---|---|---|---|"]
        for x, a, b in rows:
            vo = x["vo"]
            if x.get("vo_alt"):
                vo += f"<br><br>**Take B (no guarantee):** {x['vo_alt']}"
            o.append(f"| {tc(a)} | {x['id']} {x['beat']} | {vo} | {x['cam']} |")
        o += ["", "**Teleprompter text** (copy into the prompter; a blank line is a cut point):", "", "```text"]
        for x, _, _ in rows:
            o += [x["vo"], ""]
            if x.get("vo_alt"):
                o += ["(TAKE B) " + x["vo_alt"], ""]
        o[-1:] = ["```", ""]
        if v["key"] == "ty":
            o += ["**If it runs long**, cut in this order: T07 (the 'know your numbers' line, about 5 s), then 'Ten questions' stays but cut 'and they tell me what to cover in the workshop, so I can build it around businesses like yours' in T10 (about 5 s).", ""]
        else:
            o += ["**If it runs long**, tier 1 (about 20 s): U10 (3 s; cut it anyway if no real WhatsApp screenshots arrive), U19 (the assistant names, 3 s; they already show in U18), U27 (the recap, 9 s), the second sentence of U11 (4 s).", "", "Tier 2 (about 30 s more): the first sentence of U20 ('In the workshop, I'm teaching a whole room at once...', 6 s); in U13, cut from 'So you spent the next hour' to 'forgotten all of it' (10 s); in U25, cut 'you don't spend after the workshop' (2 s); in U21, drop the stage-four list after 'conversion mechanism' (4 s); U27 if still in.", ""]
    o += ["## Decisions before you record", "",
          "1. **Guarantee on the OS (U30).** The reference offers 7 days, money back. Record both takes: Take A with the number of days, Take B without a guarantee. Keep the one you choose.",
          "2. **What the $99 pack contains (U24, U27, U29).** The script names three parts, from your brief: the OS file pack, the setup guide and the first-build guide. If the pack holds anything else, tell me before you record.",
          "3. **The WhatsApp group name (T08).** The phone mock shows it.",
          "4. **How buyers receive the OS (U31).** The line says they get it straight away after clicking Yes. Confirm the delivery (an instant download link on the next page, or an email) before you record that clause.",
          "5. **The upsell page itself.** /vip/ still describes the older VIP seat (two private sessions). It needs rewriting for the Tantra RevOps OS at $99, with the anchor and the Yes and No buttons the video points to.", ""]
    return "\n".join(o)

# ---------------------------------------------------------------- 9-VSL-PRODUCTION-PLAN.md
STYLE = """## Look and sound (both videos)

| Element | Reference | Ours |
|---|---|---|
| Set, thank-you video | Dark bar-style room, teal cabinets, bottles, a candle, warm practicals, one camera with punch-ins | Same mood: a dark room, one warm practical lamp in frame, one violet (#6d4aff) accent light on the background wall. Seated, no desk |
| Set, upsell video | Brick wall, Edison bulbs, a desk, two cameras (a front two-shot and a side close with shallow focus) | A different look from the thank-you video, so it reads as a new message: at a desk, warm practicals, a darker wall. Two cameras: A front medium, B 45 degrees side close with shallow focus (the reference's co-host close becomes your B camera) |
| Wardrobe | Plain black crew-neck (thank-you); black overshirt over a white tee (upsell) | Plain dark crew-neck for the thank-you video; a dark overshirt or blazer for the upsell. No logos |
| Framing | WS, MS and CU, a cut every 2 to 5 s | The same three sizes. Shoot 4K so MS and CU can be punch-ins of one take |
| Captions | White semi-bold sans, two lines, a dark rounded box at about 60%, lower middle; hidden while big text is up | Inter SemiBold white, the same box, lower middle; hidden while big text is up |
| Big kinetic text | Wide display caps, built word by word with a motion blur, lower third or centre on black | Inter Black caps, the same builds. Accent colour: violet #6d4aff (thank-you, where the reference uses lime) and amber #fbbf24 (upsell, where the reference uses gold) |
| Handwritten accent line | Script font in the accent colour | Inter Italic in iris #a78bfa (brand rule: Inter only) |
| Black cards | Black, the text centre, an underline under the key word, the logo glyph low centre, a coloured light leak in one corner | The same, with the Tantra mark and a violet (thank-you) or amber (upsell) light leak |
| Graphic backgrounds | Black to accent gradient with a fine dot texture | Black to night #1a1033 gradient with a fine dot texture |
| Transitions | Hard cuts; a white flash with a ghost of the last frame before each case study | The same |
| Music | A low, steady modern bed under the voice | A royalty-free bed at about -24 LUFS under the voice; it swells on the reveal (U17) and resolves on the last line |
| Player | Autoplays muted with captions; a progress bar | Our page player already autoplays muted with an unmute button and a progress bar |

Palette: ink #0b0d12, night #1a1033, volt #6d4aff, iris #a78bfa, amber #fbbf24, white. Logo: the current Tantra mark (site/assets/img/tantra-mark-white.png). Export 1920x1080, 25 or 30 fps, H.264, captions burned in.
"""

def plan_md():
    o = ["# VSL production plan: every scene, graphic and asset", "",
         "For the shoot and the edit of both videos. Scene IDs match the scripts. Times are our cut, after jump cuts. "
         "'Reference' is where the same beat sits in the video Adi sent.", "",
         "Asset tags: **[HAVE]** in the repo (paths under deliverables/13-15a-26-20-pages/site/), **[CAPTURE]** screen-record our live page, **[MAKE]** design new, **[ADI]** only Adi can supply.", "",
         STYLE]
    for v in VIDEOS:
        rows, total = timed(v["scenes"])
        o += [f"## {v['title']} ({tc(total)})", ""]
        for x, a, b in rows:
            r0, r1 = x["ref"][0] - v["off"], x["ref"][1] - v["off"]
            o += [f"### {x['id']} · {tc(a)} to {tc(b)} · {x['beat']}", "",
                  f"**Reference {tc(max(r0,0))} to {tc(r1)}:** {x['ref_note']}", "",
                  f"**Says:** {x['vo']}", ""]
            if x.get("vo_alt"):
                o += [f"**Take B:** {x['vo_alt']}", ""]
            o += [f"**Camera:** {x['cam']} Captions: {'on' if x['captions'] else 'off while the big text is up'}.", "",
                  "**On screen:**", ""] + [f"- {g}" for g in x["gfx"]] + [""]
            if x["assets"]:
                o += ["**Assets:** " + "; ".join(x["assets"]), ""]
            o += [f"**Sound:** {x['sfx']}", ""]
    # asset checklist
    o += ["## Asset checklist", ""]
    seen = {}
    for v in VIDEOS:
        for x in v["scenes"]:
            for a in x["assets"]:
                m = re.match(r"\[(\w+)\]\s*(.*)", a)
                tag, txt = (m.group(1), m.group(2)) if m else ("NOTE", a)
                seen.setdefault(tag, []).append(f"{txt} ({x['id']})")
    names = {"ADI": "Only Adi can supply", "CAPTURE": "Screen-record from our pages", "MAKE": "Design new", "HAVE": "Already in the repo", "NOTE": "Notes"}
    for tag in ["ADI", "CAPTURE", "MAKE", "HAVE", "NOTE"]:
        if tag in seen:
            o += [f"**{names[tag]}**", ""] + [f"- {i}" for i in seen[tag]] + [""]
    o += ["## Proof used, and where it comes from", "",
          "- 400+ brands, 200,000+ webinar registrations, $300MN+ cumulative revenue, 21+ countries and 47+ industries: Adi's registration-page numbers (2026-11-07).",
          "- Growth Idea and FintechCircle figures: measured, from their trackers (data/cases.json). Both are cleared to name with first-name contacts.",
          "- Ajit (Cavli) and Tom (Growth Factors by Appster) quotes: verbatim from the registration page.",
          "- $15,000 to $25,000, $99, 100 hours, weeks to hours: Adi's brief for this video.",
          "- The 15 WhatsApp messages on the registration page are placeholder mockups with invented names. They are layout references only; the montage in U10 needs real screenshots.",
          "- Not used: the GoHighLevel invoice figure on the registration page (a replica, not a measured result).", ""]
    return "\n".join(o)

# ---------------------------------------------------------------- local media + storyboard
def media():
    PRIV.mkdir(parents=True, exist_ok=True)
    for v in VIDEOS:
        src = SRC[v["key"]]
        for x in v["scenes"]:
            a, b = x["ref"]
            clip = PRIV / "clips" / f"{x['id']}.mp4"
            clip.parent.mkdir(parents=True, exist_ok=True)
            if not clip.exists():
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a}", "-to", f"{b}", "-i", str(src),
                                "-vf", "scale=1280:-2", "-c:v", "libx264", "-crf", "26", "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", "-ac", "2", str(clip)], check=True)
            for i, t in enumerate([a + 0.6, (a + b) / 2, b - 0.6]):
                st = PRIV / "stills" / f"{x['id']}-{i+1}.jpg"
                st.parent.mkdir(parents=True, exist_ok=True)
                if not st.exists():
                    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t}", "-i", str(src), "-frames:v", "1",
                                    "-vf", "scale=640:-2", "-q:v", "3", str(st)], check=True)

FIX = {"ty": [], "up": [("Orzada", "Or Zada"), ("Michelle from India", "Mishaal from India"), ("his face online", "his face online"),
              ("E-Man's", "Iman's"), ("What are the blokes E-Man showed", "One of the blokes Iman showed"), ("from Michelle", "from Mishaal"),
              ("didn't think it was", "didn't think it twice"), ("invested at $97, became", "invested that $97 and became"), ("I crossed", "I grossed"),
              ("all-expensive paid", "all-expenses-paid"), ("end of the field, it wasn't", "end and feel it wasn't"), ("brought himself", "bought himself"),
              ("brought his family", "bought his family"), ("Zada, Angelo, and Michal", "Zada, Angelo and Mishaal")]}

def transcripts():
    for v in VIDEOS:
        segs = json.load(open(f"/tmp/vsl/{v['key']}/tx.json"))
        lines = [f"# Reference transcript: {v['title']} (the video Adi sent)", "",
                 f"Machine transcript (Whisper), corrected against the burned-in captions. Times are from the start of the video (the file's player pre-roll removed). Length {v['ref_len']}.", ""]
        for s in segs:
            t = s["text"].strip()
            if t in ("Thank you.",):
                continue
            for a, b in FIX[v["key"]]:
                t = t.replace(a, b)
            lines.append(f"**{tc(max(s['start'] - v['off'], 0))}** {t}  ")
        (PRIV / f"TRANSCRIPT-{v['key']}-reference.md").write_text("\n".join(lines) + "\n")

def storyboard():
    e = html.escape
    parts = ["""<!doctype html><meta charset="utf-8"><title>VSL storyboard (local)</title>
<style>body{font:15px/1.5 Inter,system-ui,sans-serif;background:#0b0d12;color:#e7e9ef;margin:0}main{max-width:1400px;margin:auto;padding:24px}
h1{font-size:26px}h2{font-size:21px;margin:40px 0 8px;color:#a78bfa}nav a{color:#fbbf24;margin-right:16px}
.s{display:grid;grid-template-columns:520px 1fr;gap:24px;border-top:1px solid #2a2f3a;padding:22px 0}.s video{width:100%;border-radius:8px;background:#000}
.st{display:flex;gap:6px;margin-top:6px}.st img{width:33%;border-radius:4px}.id{color:#fbbf24;font-weight:700}.vo{background:#161a24;border-left:3px solid #6d4aff;padding:10px 14px;border-radius:6px;font-size:17px}
.k{color:#aab1be;font-size:13px;text-transform:uppercase;letter-spacing:.05em;margin:12px 0 2px}ul{margin:4px 0 0 18px;padding:0}.ref{color:#aab1be}</style><main>
<h1>VSL storyboard: reference on the left, our scene on the right</h1>
<p class="ref">Local only: the reference clips are a third party's video and never go on the public board. Scripts and the plan also live on board card 14.</p>
<nav><a href="#ty">Thank-you video</a><a href="#up">Upsell video</a><a href="TRANSCRIPT-ty-reference.md">Thank-you reference transcript</a><a href="TRANSCRIPT-up-reference.md">Upsell reference transcript</a><a href="our-pages/">Our page captures (1920x1080)</a></nav>"""]
    for v in VIDEOS:
        rows, total = timed(v["scenes"])
        parts.append(f'<h2 id="{v["key"]}">{e(v["title"])} · {tc(total)} · {sum(wc(x["vo"]) for x in v["scenes"])} words</h2>')
        for x, a, b in rows:
            r0, r1 = x["ref"][0] - v["off"], x["ref"][1] - v["off"]
            stills = "".join(f'<img src="stills/{x["id"]}-{i}.jpg" loading="lazy" alt="">' for i in (1, 2, 3))
            alt = f'<p class="k">Take B</p><div class="vo">{e(x["vo_alt"])}</div>' if x.get("vo_alt") else ""
            parts.append(f'''<section class="s" id="{x["id"]}"><div><video src="clips/{x["id"]}.mp4" controls preload="none" poster="stills/{x["id"]}-2.jpg"></video><div class="st">{stills}</div>
<p class="k">Reference {tc(max(r0,0))} to {tc(r1)}</p><p class="ref">{e(x["ref_note"])}</p></div>
<div><p><span class="id">{x["id"]}</span> · {tc(a)} to {tc(b)} · <b>{e(x["beat"])}</b></p><div class="vo">{e(x["vo"])}</div>{alt}
<p class="k">Camera</p><p>{e(x["cam"])} Captions {"on" if x["captions"] else "off while the big text is up"}.</p>
<p class="k">On screen</p><ul>{"".join(f"<li>{e(g)}</li>" for g in x["gfx"])}</ul>
{"<p class='k'>Assets</p><ul>" + "".join(f"<li>{e(g)}</li>" for g in x["assets"]) + "</ul>" if x["assets"] else ""}
<p class="k">Sound</p><p>{e(x["sfx"])}</p></div></section>''')
    parts.append("</main>")
    (PRIV / "index.html").write_text("\n".join(parts))

if __name__ == "__main__":
    (ROOT / "4-VIDEO-SCRIPTS.md").write_text(scripts_md())
    (ROOT / "9-VSL-PRODUCTION-PLAN.md").write_text(plan_md())
    PRIV.mkdir(parents=True, exist_ok=True)
    transcripts()
    if "--media" in sys.argv:
        media()
    storyboard()
    for v in VIDEOS:
        rows, total = timed(v["scenes"])
        print(v["key"], sum(wc(x["vo"]) for x in v["scenes"]), "words", tc(total))
