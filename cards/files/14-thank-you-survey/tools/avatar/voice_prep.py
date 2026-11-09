"""Clean and transcribe a recorded voice memo so its sentences can drive H3 (audio-locked).

Run with the mlx-whisper venv:
  ~/tools/whisper/.venv/bin/python voice_prep.py <memo.m4a> <out_dir>
Writes: <out_dir>/voice-clean.wav (48 kHz mono, denoised, loudness-normalised),
        <out_dir>/words.json (word timings), <out_dir>/sentences.txt (start end text).
Cut lines with: ffmpeg -ss START -to END -i voice-clean.wav line.wav
"""
import json
import subprocess
import sys
from pathlib import Path

import mlx_whisper

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
clean = out / "voice-clean.wav"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "48000",
                "-af", "highpass=f=70,afftdn=nf=-25:tn=1,deesser,loudnorm=I=-16:TP=-1.5:LRA=9",
                str(clean)], check=True)
r = mlx_whisper.transcribe(str(clean), path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                           word_timestamps=True, language="en", condition_on_previous_text=False)
words = [w for s in r["segments"] for w in s.get("words", [])]
(out / "words.json").write_text(json.dumps(words, indent=1))
with open(out / "sentences.txt", "w") as f:
    for s in r["segments"]:
        f.write(f"{s['start']:.2f}\t{s['end']:.2f}\t{s['text'].strip()}\n")
print((out / "sentences.txt").read_text())
