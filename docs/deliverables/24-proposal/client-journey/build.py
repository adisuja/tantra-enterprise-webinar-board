#!/usr/bin/env python3
"""Builds index.html from src.html: fills {{config.path}} tokens from funnel-config.json,
embeds the fonts and the Tantra mark, so the page is one self-contained file.
usage: python3 build.py   (run from anywhere)"""
import base64, io, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CFG = json.loads((ROOT / "deliverables/_shared/funnel-config.json").read_text())
FONT_DIRS = [pathlib.Path.home() / "tantra-content/content/brand/fonts", ROOT / "deliverables/24-proposal/assets/fonts"]
FONTS = [("Clash Display", "clash-600.woff2", "600"), ("Inter", "inter-var.woff2", "100 900"),
         ("JetBrains Mono", "jetbrains-mono-var.woff2", "100 800")]


def font_css():
    out = []
    for family, name, weight in FONTS:
        f = next((d / name for d in FONT_DIRS if (d / name).exists()), None)
        if not f:
            sys.exit(f"missing font {name}")
        b64 = base64.b64encode(f.read_bytes()).decode()
        out.append(f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{b64}) format('woff2');"
                   f"font-weight:{weight};font-display:swap}}")
    return "\n".join(out)


def logo_uri():
    from PIL import Image
    im = Image.open(ROOT / CFG["brand"]["logo_light"]).convert("RGBA")
    im.thumbnail((96, 96))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def value(path):
    if path == "offer.price":
        return f"${CFG['offer']['price_usd']:,}"
    if path.startswith("closer."):
        return CFG["booking"]["closers"][int(path.split(".")[1])]["name"]
    node = CFG
    for key in path.split("."):
        node = node[key]
    text = str(node)
    if text.startswith("FILL_"):
        return '<span class="fill">FILL</span>'
    return text


src = (HERE / "src.html").read_text()
html = src.replace("/*FONTS*/", font_css()).replace("{{LOGO}}", logo_uri())
html = re.sub(r"\{\{([a-z0-9_.]+)\}\}", lambda m: value(m.group(1)), html)
left = re.findall(r"\{\{[^}]+\}\}", html)
if left:
    sys.exit(f"unfilled tokens: {left}")
(HERE / "index.html").write_text(html)
print(f"wrote {HERE / 'index.html'} ({len(html) // 1024} KB)")
