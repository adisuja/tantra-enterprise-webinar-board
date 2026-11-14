#!/usr/bin/env python3
"""Voice the course videos with Adi's cloned voice (ElevenLabs text to speech), card 72 and 74.

Reads site/voice-text/<id>.parts/NN.txt (run tools/voice_text.py first), sends each part to ElevenLabs with the text
before and after it for steady intonation, and writes site/voice-mp3/<id>.mp3 (parts joined in order; with ffmpeg on
the machine they are joined cleanly, otherwise byte-joined, which plays fine in editors).

The key is never stored in the repo: in a cloud session the network adds it (any placeholder works), on a Mac it comes
from ELEVENLABS_API_KEY or ~/.config/tantra/keys/elevenlabs.env.

usage: python3 tools/voice_generate.py --voice-id <id> [--only V01,V10] [--model eleven_multilingual_v2] [--dry-run]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "site" / "voice-text"
OUT = ROOT / "site" / "voice-mp3"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_192"


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    f = Path.home() / ".config/tantra/keys/elevenlabs.env"
    if not k and f.exists():
        for line in f.read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                k = line.split("=", 1)[1].strip()
    return k or "proxy-injected"


def speak(voice, model, text, prev, nxt):
    body = {"text": text, "model_id": model, "previous_text": prev[-1000:] or None, "next_text": nxt[:1000] or None,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True}}
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key(), "content-type": "application/json", "accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise SystemExit(f"ElevenLabs {e.code}: {e.read()[:300]!r}")


def join(parts, dest):
    if shutil.which("ffmpeg"):
        with tempfile.TemporaryDirectory() as d:
            lst = Path(d) / "list.txt"
            files = []
            for i, b in enumerate(parts):
                p = Path(d) / f"{i:02d}.mp3"
                p.write_bytes(b)
                files.append(p)
            lst.write_text("".join(f"file '{p}'\n" for p in files))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dest)], check=True)
    else:
        dest.write_bytes(b"".join(parts))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--voice-id", required=True)
    a.add_argument("--only", default="")
    a.add_argument("--model", default="eleven_multilingual_v2")
    a.add_argument("--dry-run", action="store_true")
    o = a.parse_args()
    want = {x.strip().upper() for x in o.only.split(",") if x.strip()}
    dirs = sorted(d for d in TEXT.glob("V*.parts") if not want or d.name.split(".")[0] in want)
    if not dirs:
        sys.exit("no voice text: run python3 tools/voice_text.py first")
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for d in dirs:
        vid = d.name.split(".")[0]
        texts = [p.read_text().strip() for p in sorted(d.glob("*.txt"))]
        chars = sum(len(t) for t in texts)
        total += chars
        if o.dry_run:
            print(f"{vid}: {len(texts)} parts, {chars} characters")
            continue
        audio = [speak(o.voice_id, o.model, t, texts[i - 1] if i else "", texts[i + 1] if i + 1 < len(texts) else "") for i, t in enumerate(texts)]
        join(audio, OUT / f"{vid}.mp3")
        print(f"{vid}: {len(texts)} parts, {chars} characters -> site/voice-mp3/{vid}.mp3")
    print(f"total: {total} characters")


if __name__ == "__main__":
    main()
