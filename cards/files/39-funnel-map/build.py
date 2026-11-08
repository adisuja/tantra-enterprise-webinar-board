"""Build the funnel map (card 39) into site/. Fills the bonus password from ~/.config/tantra/keys/tantra-bonuses.env
(never committed) and stops on any em or en dash. Run: python3 build.py, then bash publish.sh."""
import re, shutil, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SITE = HERE / "site"
env = dict(l.split("=", 1) for l in (Path.home() / ".config/tantra/keys/tantra-bonuses.env").read_text().split() if "=" in l)
pw = env["BONUS_PASSWORD"].strip()
(SITE / "assets").mkdir(parents=True, exist_ok=True)
html = (HERE / "src/index.html").read_text()
data = (HERE / "src/funnel.js").read_text().replace("{{BONUS_PASSWORD}}", pw)
for name, text in (("index.html", html), ("data.js", data)):
    for bad in ("—", "–"):
        if bad in text:
            line = next(i for i, l in enumerate(text.splitlines(), 1) if bad in l)
            raise SystemExit(f"dash {bad!r} in {name} line {line}")
    (SITE / name).write_text(text)
mark = SITE / "assets/mark.png"
shutil.copy(ROOT / "context/from-workshop-project/brand/assets/tantra-mark-ink.png", mark)
subprocess.run(["sips", "-Z", "96", str(mark)], capture_output=True)
for src, dst, px in (("tantra-mark-white.png", "mark-white.png", "96"), ("tantra-word-white.png", "word-white.png", "400")):
    shutil.copy(ROOT / "context/from-workshop-project/brand/assets" / src, SITE / "assets" / dst)
    subprocess.run(["sips", "-Z", px, str(SITE / "assets" / dst)], capture_output=True)
shutil.copytree(HERE / "src/covers", SITE / "covers", dirs_exist_ok=True)
(SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
print("built", SITE)
