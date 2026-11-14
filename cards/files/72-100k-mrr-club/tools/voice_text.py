#!/usr/bin/env python3
"""Write the text the cloned voice reads, one file per video (Adi 2026-11-13).

Takes only the "## Voice script" section of scripts/V*.md, drops the [SLIDE n] and [SCREEN: ...] cue lines,
and writes site/voice-text/<id>.txt plus <id>.parts/NN.txt chunks of at most 2,400 characters split on
paragraph ends, for voice tools with a per request limit. Also prints a word count and a length estimate
at 130 words a minute. usage: python3 tools/voice_text.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "voice-text"
LIMIT = 2400


def voice(md: str) -> str:
    sec = re.split(r"^## ", md, flags=re.M)
    body = next((s for s in sec if s.startswith("Voice script")), "")
    body = body.split("\n", 1)[1] if "\n" in body else ""
    lines = [l for l in body.splitlines() if not re.match(r"^\s*\[(SLIDE|SCREEN)[^\]]*\]\s*$", l)]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def chunks(text: str):
    out, cur = [], ""
    for para in text.split("\n\n"):
        if cur and len(cur) + len(para) + 2 > LIMIT:
            out.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for f in sorted((ROOT / "scripts").glob("V*.md")):
        vid = f.name.split("-")[0]
        text = voice(f.read_text())
        if not text:
            print(f"{vid}: NO VOICE SCRIPT")
            continue
        (OUT / f"{vid}.txt").write_text(text + "\n")
        parts = OUT / f"{vid}.parts"
        parts.mkdir(exist_ok=True)
        for old in parts.glob("*.txt"):
            old.unlink()
        for i, c in enumerate(chunks(text), 1):
            (parts / f"{i:02d}.txt").write_text(c + "\n")
        words = len(text.split())
        total += words
        print(f"{vid}: {words} words, about {words / 130:.1f} min, {len(list(parts.glob('*.txt')))} parts")
    print(f"total: {total} words, about {total / 130 / 60:.1f} hours")


if __name__ == "__main__":
    main()
