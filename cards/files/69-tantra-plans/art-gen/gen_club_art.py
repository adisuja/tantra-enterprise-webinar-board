"""Kie.ai artwork for the Tantra plan pages (cloud version of gen_plans_art.py).
Auth: the cloud session's network proxy injects the Kie.ai key for api.kie.ai and kieai.redpandaai.co,
so no key file is read. Reference: ref/tantra.png (the real Tantra mark). No text in the art.
usage: python3 -I gen_club_art.py [name ...]   -> art/<name>.png, then webp 800/1200/1800 into
       13-15a-26-20-pages/src/assets/img/plans/<name>-<w>.webp
       python3 -I gen_club_art.py --webp [name ...]  -> only (re)convert existing pngs
"""
import base64, json, pathlib, ssl, sys, time, urllib.request, concurrent.futures as cf

HERE = pathlib.Path(__file__).parent
ART = HERE / 'art'
OUT = HERE.parent.parent / '13-15a-26-20-pages' / 'src' / 'assets' / 'img' / 'plans'
CTX = ssl.create_default_context()
H = {'Authorization': 'Bearer proxy-injected', 'Content-Type': 'application/json'}

def post(url, body):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method='POST'), timeout=180, context=CTX))

def get(path):
    return json.load(urllib.request.urlopen(urllib.request.Request('https://api.kie.ai' + path, headers=H), timeout=120, context=CTX))

AVATAR = HERE.parent.parent / '13-15a-26-20-pages' / 'src' / 'assets' / 'img' / 'adi-avatar.jpg'

def upload(path=HERE / 'ref' / 'tantra.png'):
    mime = 'image/jpeg' if path.suffix.lower() in ('.jpg', '.jpeg') else 'image/png'
    b64 = base64.b64encode(path.read_bytes()).decode()
    return post('https://kieai.redpandaai.co/api/file-base64-upload', {'base64Data': f'data:{mime};base64,{b64}', 'uploadPath': 'tantra-plans-ref', 'fileName': path.name})['data']['downloadUrl']

BASE = ("The reference image is the Tantra logo (a circuit tree growing out of a glowing head): reproduce it faithfully where it appears, never invent a different logo. "
        "Absolutely no text, letters, words, numbers or watermark anywhere. Premium 3D product render, cinematic studio lighting, ultra clean, "
        "Apple keynote and luxury brand campaign quality, shallow depth of field, near-black ink background (#0b0d12), generous dark margins, subject centred. ")
JOBS = {
    'pay-full': BASE + ("Palette: deep violet (#6d4aff) with warm champagne gold accents. Subject: a six-month membership pass: a heavy matte black metal pass card "
                        "with a bevelled champagne gold edge, the Tantra logo embossed in gold on it, standing at a slight angle on a dark polished stone plinth. Beside it, "
                        "exactly six small square tiles of frosted glass in a short neat horizontal row like six months, every one of them lit from within with a warm violet-gold glow. "
                        "The card and all six tiles sit fully inside the frame with dark space on both sides, nothing cropped. Reflections on the plinth. Commitment, value, a complete set, quietly luxurious."),
    'pay-monthly': BASE + ("Palette: deep violet (#6d4aff) and soft lilac (#a78bfa) light. Subject: the same heavy matte black metal pass card with a fine bevelled edge, "
                           "the Tantra logo embossed on it, resting at an angle on a dark polished plinth. Beside it a calendar-like row of small square frosted-glass tiles: "
                           "only the first tile glows bright lilac, the rest wait softly dim and translucent in sequence, ready to light one by one. "
                           "Flexible, light, month by month, calm and premium."),
    'academy': BASE + ("Palette: deep violet (#6d4aff) with soft lilac highlights. Subject: an online academy: a floating dark smoked-glass screen with a thin brushed graphite "
                       "frame, hovering at a slight three-quarter angle. On it, a wordless video player: a large soft violet gradient frame with a glowing play triangle, "
                       "beneath it a row of five lesson thumbnails shown as abstract rounded shapes and gradients, and a slim glowing violet progress bar two thirds full. "
                       "The Tantra logo glows small on the lower bezel of the frame. Focused, modern learning."),
    'funnel-os': BASE + ("Palette: deep violet (#6d4aff) and electric cyan (#22d3ee) light. Subject: a funnel built from stacked translucent glass rings, widest at the top and "
                         "narrowing downward, each ring edge-lit in violet and cyan. Streams of fine light particles flow down through the rings into a glowing core sphere at "
                         "the bottom, where the Tantra logo shines. Small wordless frosted-glass page cards (abstract layout blocks only) orbit the funnel on thin light paths. "
                         "Engineered, precise, flowing."),
    'content-os': BASE + ("Palette: deep violet (#6d4aff) with warm amber (#fbbf24) light. Subject: a content engine: a sleek rounded glass and graphite device like a premium "
                          "printer, glowing amber from inside, the Tantra logo glowing on its front. Out of its slot fly neat stacks of abstract post cards and swiping "
                          "carousel panels (only colour blocks and soft gradients, no writing), arcing upward toward a few small floating glass orbs holding simple generic "
                          "icons: a heart, a play triangle, a chat bubble, a share arrow, no brand logos. Energetic yet orderly."),
    'coaching-group': BASE + ("Palette: deep violet (#6d4aff) with one warm gold (#f5c76b) accent. Subject: a weekly group coaching call: a floating dark smoked-glass panel "
                              "holding a clean 3 by 2 video-call grid of six rounded tiles, each with a soft abstract silhouette avatar (head and shoulders shapes only, no faces) "
                              "in gentle violet gradients. One tile is highlighted with a glowing gold ring, the person on their hot seat. A subtle thin luminous clock ring "
                              "arcs around the whole panel, a quarter of it brighter. Warm, focused, collaborative."),
    'coaching-1to1': BASE + ("Palette: rich gold (#f5c76b) and deep violet (#6d4aff). Subject: a one to one strategy session: two premium sculptural chairs of dark glass and "
                             "brushed gold facing each other across a low polished black stone table. Hovering above the table between them, a glowing hologram of a rising "
                             "revenue chart: elegant gold bars and a violet curve climbing upward, no numbers or labels. The Tantra logo inlaid in gold on the table top. "
                             "Intimate, senior, high-stakes, private office mood."),
    'dfy-team': BASE + ("Palette: rich polished gold (#f5c76b, #e0a94a) with faint violet depth. Subject: a world-class implementation team at work: three precise matte black "
                        "robotic arms with gold joints and glowing tool tips assembling a golden revenue engine made of stacked layers of dark glass and polished gold, "
                        "warm light flowing up through its core, the Tantra logo glowing gold at its centre. Fine sparks of gold light fly where the tools touch. "
                        "Craftsmanship, precision, done for you."),
    'community': BASE + ("Palette: deep violet (#6d4aff) and soft lilac (#a78bfa) with a hint of warm gold. Subject: a private members' circle: a perfect ring of twelve small "
                         "glowing frosted-glass orbs floating in the dark, each connected to its neighbours and to the centre by delicate threads of light, forming a "
                         "constellation. At the centre the Tantra logo glows on a small polished disc. Soft bloom, warm, exclusive, belonging."),
}

WIDE = ("The reference image is the Tantra logo (a circuit tree growing out of a glowing head): reproduce it faithfully where it appears, never invent a different logo. "
        "Absolutely no text, letters, words, numbers or watermark anywhere. No people, no faces. Cinematic wide establishing shot, premium 3D architectural render, "
        "Apple keynote and luxury brand campaign quality, anamorphic lens, volumetric light, subtle film grain, shallow depth of field, "
        "near-black ink background (#07080c) that fades smoothly to pure dark at every edge so it melts into a near-black web page. Full-bleed image filling the entire frame edge to edge: no letterbox bars, no black borders, no frames. "
        "The Tantra logo is always seen from the front and symmetrical: a small glowing head at the bottom with circuit branches fanning out above it like a tree in blue, pink, green and gold, never a side profile. ")
LEFT = " The left third of the frame is calm, almost empty dark negative space for headline text; the subject sits in the right two thirds."
JOBS.update({
    'hero-100k-banner': WIDE + ("Palette: deep violet (#6d4aff) and warm champagne gold (#f5c76b). Subject: a private members' club for builders at night: a dark luxurious "
                                "lounge with low sculptural leather seating, warm violet wall washes and polished black stone floors. A long low table of smoked black glass "
                                "runs into the depth of the room; floating above it a glowing holographic revenue funnel of translucent violet and gold rings, fine light "
                                "particles flowing down through it. On the black glass back wall the Tantra logo glows softly in champagne gold. Intimate, exclusive, warm." + LEFT),
    'hero-5m-banner': WIDE + ("Palette: rich polished gold (#f5c76b, #e0a94a) with deep violet (#6d4aff) shadows. Subject: a world-class implementation studio at night: a vast dark "
                              "glass atrium with tall slender black steel columns. In it rises a golden revenue engine: stacked layers of dark glass and polished gold like a "
                              "funnel turned into a skyscraper, warm light flowing up through its core. Several precise matte black robotic arms with gold joints and glowing "
                              "tool tips assemble its upper layers, fine sparks of golden light. At its crown the Tantra logo glows gold. Monumental, precise, done for you." + LEFT),
    'hero-10m-banner': WIDE + ("Palette: platinum silver and polished gold (#f5c76b) with cool white highlights. Subject: an eight figure revenue command centre: a monumental "
                               "sculpture of interlocking platinum and gold glass rings like a gyroscope, slowly turning. Dozens of fine streams of light converge into it "
                               "from all directions across the dark. Far behind, a hazy night skyline of glass towers. At the very centre of the rings the Tantra logo glows. "
                               "Commanding, rare, elite scale." + LEFT),
    'week-banner': WIDE + ("Palette: deep violet (#6d4aff) and soft lilac (#a78bfa). Subject: exactly seven thick slabs of frosted glass forming a staircase that rises from "
                           "lower left to upper right across a dark space, each step lit from within and each one brighter than the one before, the last glowing strongly. "
                           "A small luminous violet orb is climbing the steps, leaving a soft light trail. Reflections on a dark polished floor. Calm, progressive, momentum, minimal."),
    'ninety-banner': WIDE + ("Palette: rich warm gold (#f5c76b, #e0a94a) on black. Subject: a precise golden timeline: a long slim rail of dark smoked glass with a gold edge "
                             "running horizontally across the frame in gentle perspective. Along it stand exactly five polished gold milestone pillars of growing height, "
                             "left lowest, right tallest. A stream of golden light flows along the rail through them into a glowing compact gold engine of stacked glass "
                             "layers at the right end. Precise, deliberate, engineered, luxurious."),
    'specialists': BASE + ("The Tantra logo is seen from the front and symmetrical, never a side profile. " "Palette: deep violet (#6d4aff) with warm gold (#f5c76b) accents. Subject: four premium dark smoked-glass workstations with brushed graphite "
                           "and gold trim, arranged in a gentle arc around a central polished black disc where the Tantra logo glows. Above each workstation floats a different "
                           "wordless hologram: a strategy map of connected shapes, a node network graph, a glowing waveform like a recorded sales call, and a pipeline of "
                           "small cards moving along lanes. Bespoke sculptural furniture like a luxury design studio, not office furniture, soft volumetric light, empty seats, no people. A team of specialists, calm expertise. Wide view, the whole arc inside the frame."),
    'score-gauge': BASE + ("Palette: deep violet (#6d4aff) and electric cyan (#22d3ee). Subject: a premium circular gauge dial of dark smoked glass set in a brushed metal bezel, "
                           "with fine tick marks but no numbers; a glowing violet to cyan arc fills about three quarters of the dial. From the base of the dial three thin "
                           "glowing route paths branch out across a dark polished floor toward three tall slim doors standing in the distance: one of graphite, one of "
                           "violet anodised metal, one of polished gold, each slightly ajar with warm light spilling from behind, sculptural and luxurious, set in a dark marble hall with soft volumetric haze. The gauge is a jewel-like instrument like a luxury watch face. Diagnostic, precise, a choice of paths."),
    'proof-wall': BASE + ("Palette: deep violet (#6d4aff) with warm gold (#f5c76b). Subject: a dark gallery wall of floating rectangular frosted-glass panels in a neat "
                          "staggered grid of about nine panels, all fully inside the frame with dark space around the group, each with real glass thickness, bevelled edges and depth, softly backlit and each showing a different abstract rising chart drawn in light: a climbing curve, ascending bars, a "
                          "stepped line, a growth arc, rendered as luminous 3D light trails with soft bloom, not flat icons, no axes, labels or numbers. Gentle museum spotlights from above like an award wall. In the centre of the wall the "
                          "Tantra logo glows small in gold. Proof, results, quiet confidence."),
    'join-banner': WIDE + ("Palette: deep violet (#6d4aff) with warm champagne gold (#f5c76b). Subject: a heavy matte black metal membership pass with a bevelled gold edge and "
                           "the Tantra logo embossed in gold, sliding out of a slim dark smoked-glass sleeve, soft violet light spilling out of the sleeve opening and across "
                           "a polished black surface. Close, elegant product shot placed in the right half. A sense of being welcomed in, an invitation." +
                           " The left half of the frame is calm dark negative space."),
})

# Tantra Academy module set: one consistent studio, one hero object each, no logo, no charts.
ACADEMY = ("Absolutely no text, letters, words, numbers, symbols, logos or watermark anywhere, no screens with writing, no charts, no arrows, no floating UI. "
           "Ultra-premium 3D product still, like a luxury watch or Apple product campaign photograph: one single hero object, a clear focal point, restraint and calm. "
           "Always the same dark studio: a near-black seamless background (#07080c) that falls off to pure black at every edge, the hero object resting on a low "
           "dark honed basalt stone plinth with a subtle soft reflection, seen from a low camera angle slightly below eye level, 85mm lens, shallow depth of field. "
           "Lighting identical in every image of the set: a deep violet (#6d4aff) key light from the upper left, a thin warm champagne gold rim light from behind right "
           "tracing the edges, faint haze, velvet shadows. Real materials only: smoked and clear optical glass, dark brushed titanium, matte black metal, polished stone, "
           "fine gold details. Generous dark space around the object, nothing cropped, 4:3 frame. Subject: ")
JOBS.update({
    'academy-m1': ACADEMY + ("a precise low control console of dark brushed titanium with a row of five small rounded glass modules shaped like miniature mailboxes plugged into it, "
                             "each linked to the console by a neat, gently curved glowing violet cable, the cables tidy and parallel. A single small gold key rests on top of the console. "
                             "Order, everything set up and connected."),
    'academy-m2': ACADEMY + ("a thick slab of dark smoked glass lying at a slight angle, with a fine glowing violet line diagram engraved inside it like an architectural blueprint "
                             "of interlocking rectangles and circles (pure geometry, no writing). A precise brushed-steel drafting compass stands open on the slab, and a single "
                             "polished gold pin marks one point of the diagram. Deciding, designing with intent."),
    'academy-m3': ACADEMY + ("a tall thin slab of clear glass standing upright on the plinth like a small monolith or a page, inside it one softly glowing rounded rectangle shape "
                             "like an empty form field and a smaller glowing pill shape beneath it, nothing written. Around it, four or five small smooth glass speech-bubble "
                             "shapes float in one gentle graceful arc, catching the champagne rim light. Welcome, conversation, nurture."),
    'academy-m4': ACADEMY + ("side by side on the plinth: a round sleek glass dial like a premium rotary booking knob with a dark titanium core and fine unnumbered tick marks, and a "
                             "matte black metal payment card standing on its edge with a bevelled gold edge, blank. A single thin golden thread of light arcs from the dial to "
                             "the card, connecting them. Conversion, a booking becoming revenue, elegant and quiet."),
    'academy-m5': ACADEMY + ("a single precision optical glass lens shaped like a shallow funnel, held in a slim dark titanium ring on a short stand. Five thin, clean beams of "
                             "light (violet, lilac and champagne) arrive from different directions out of the darkness and enter the lens, and they converge into one single "
                             "intensely bright small point of light just below it, on the plinth. Focus, many sources into one."),
    'academy-m6': ACADEMY + ("a heavy dark smoked-glass launch switch block with a single large round push button ringed by a glowing violet light ring. Beside it a short neat "
                             "vertical column of exactly five small round glass indicator lights set in a slim titanium strip, every one of them lit warm and steady, none dark. "
                             "Ready, everything checked, the moment before launch."),
    'academy-m7': ACADEMY + ("a precision instrument: a round dial gauge of dark brushed titanium with fine unnumbered tick marks and a single glowing violet segment on its arc, "
                             "standing beside a small sculptural model of a pipeline made of glowing glass tubes and small glass nodes. A round magnifying lens in a thin gold "
                             "frame hovers over one node of the pipeline, enlarging it. Running, measuring, refining."),
    'adi-coach': ("The reference image is a photograph of a real man named Adi. Create a new premium portrait photograph of exactly this same man: keep his face, facial "
                  "structure, skin tone, eyes, nose, beard shape, hairline and hairstyle, age and ethnicity exactly as in the reference, photorealistic, no beautifying, "
                  "no smoothing, no changes to his identity. Only one person in the image. Chest-up portrait, body at a slight three-quarter angle, face toward the camera, "
                  "confident and warm natural smile. He wears dark smart-casual clothing: a charcoal-black knit or open-collar dark shirt under a dark tailored jacket. "
                  "Dark studio with a near-black background (#07080c) fading to black at the edges, a warm soft key light on his face from the front left, a violet (#6d4aff) "
                  "rim light from behind outlining his hair and shoulders, soft depth of field, 85mm lens, editorial magazine portrait quality, real skin texture. "
                  "Absolutely no logo, no text, letters, numbers or watermark. 4:3 landscape frame with him slightly right of centre."),
})

def refs(job, logo):
    if job == 'adi-coach':
        return [upload(AVATAR)]
    return [] if job.startswith('academy-m') else [logo]

def run(name, url):
    job = name.split('.')[0]
    t = post('https://api.kie.ai/api/v1/jobs/createTask', {'model': 'nano-banana-pro', 'input': {'prompt': JOBS[job], 'image_input': refs(job, url), 'aspect_ratio': '16:9' if job.endswith('-banner') else '4:3', 'resolution': '2K', 'output_format': 'png'}})
    if not t.get('data'):
        return False, f'{name} create failed {t}'
    tid = t['data']['taskId']
    for _ in range(150):
        time.sleep(6)
        d = get(f'/api/v1/jobs/recordInfo?taskId={tid}')['data']
        if d['state'] == 'success':
            (ART / f'{name}.png').write_bytes(urllib.request.urlopen(json.loads(d['resultJson'])['resultUrls'][0], timeout=180, context=CTX).read())
            return True, f'{name} ok'
        if d['state'] == 'fail':
            return False, f'{name} fail {d.get("failMsg")}'
    return False, f'{name} timeout'

def safe(name, url):
    for attempt in (1, 2):
        try:
            ok, msg = run(name, url)
        except Exception as e:
            ok, msg = False, f'{name} error {e!r}'
        print(msg + ('' if ok else f' (attempt {attempt})'), flush=True)
        if ok:
            return True
    return False

def webp(name, src=None):
    from PIL import Image
    im = Image.open(src or ART / f'{name}.png').convert('RGB')
    OUT.mkdir(parents=True, exist_ok=True)
    for w in (800, 1200, 1800):
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(OUT / f'{name}-{w}.webp', 'WEBP', quality=82, method=6)

if __name__ == '__main__':
    args = sys.argv[1:]
    only_webp = '--webp' in args
    names = [a for a in args if a != '--webp'] or list(JOBS)
    ART.mkdir(exist_ok=True)
    if not only_webp:
        url = upload()
        with cf.ThreadPoolExecutor(max(9, len(names))) as ex:
            done = dict(zip(names, ex.map(lambda n: safe(n, url), names)))
        names = [n for n in names if done[n]]
    for n in names:
        if '.' not in n:
            webp(n)
