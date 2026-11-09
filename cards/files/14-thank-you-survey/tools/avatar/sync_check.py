"""Gate 2: offset between the audio H3 returns inside each clip and the line audio we sent.
Run: python3 sync_check.py h3full/R1a.mp4 [...]   (line audio = same stem .wav next to the clip)
Pass: |offset| < half a frame at 24 fps (0.021 s), reported to 3 decimals. Exits non-zero on any FAIL.
"""
import subprocess, sys
from pathlib import Path
import numpy as np

SR = 16000


def pcm(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<i2").astype(np.float32) / 32768


def offset(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    c = np.concatenate([c[-(len(b) - 1):], c[:len(a)]])
    lag = int(np.argmax(c)) - (len(b) - 1)
    peak = c.max() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
    return lag / SR, peak


bad = 0
for clip in sys.argv[1:]:
    clip = Path(clip); ref = clip.with_suffix(".wav")
    off, peak = offset(pcm(clip), pcm(ref))
    ok = abs(off) < 0.021 and peak > 0.5
    bad += not ok
    print(f"{clip.name}: offset {off:+.3f} s  corr {peak:.2f}  {'PASS' if ok else 'FAIL'}")
sys.exit(1 if bad else 0)
