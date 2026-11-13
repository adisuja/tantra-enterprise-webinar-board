"""Conform a Kie H3 clip to Adi's voice.
Kie keeps the real recording but may add pauses at sentence/comma breaks (often at the in-clip shot change).
This splits our line at those breaks, finds every chunk inside Kie's track (normalised cross-correlation,
searched in order), and records each inserted pause. The clip is kept whole (no cuts inside it); the master
voice gets the same pauses (h3ups/build_timeline.py). Then every half second of the clip must match our
line-with-pauses at lag 0.
Run: python3 kie_conform.py <dir> <name> <abs_start> <abs_end>     (abs times on voice-final.wav)
Writes <name>-conf.mp4 and <name>-conf.json {"pauses": [[t_in_line, seconds], ...], "len": ...}
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

SR = 16000
d, name, A0, A1 = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
H = Path(__file__).resolve().parents[2] / "private" / "avatar-test"
W = json.load(open(H / "voice" / "upsell" / "words-final.json"))


def pcm(p):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                       capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout
    return np.frombuffer(r, "<i2").astype(np.float32) / 32768


def ncc(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


kie, ours = pcm(d / f"{name}.mp4"), pcm(d / f"{name}.wav")
L = len(ours) / SR
ws = [w for w in W if A0 <= (w["start"] + w["end"]) / 2 <= A1]
bounds, labels = [0.0], {}  # chunk boundaries at punctuated word ends (midway into the gap)
for x, y in zip(ws, ws[1:]):
    t = ((x["end"] + y["start"]) / 2) - A0
    if re.search(r"[.,!?]$", x["word"].strip()) and t - bounds[-1] > 0.35 and L - t > 0.35:
        bounds.append(t); labels[round(t, 4)] = f"{x['word'].strip()} | {y['word'].strip()}"
bounds.append(L)
shift, pauses, off0 = 0.0, [], 0.0
for i in range(len(bounds) - 1):
    s, e = bounds[i], bounds[i + 1]
    nd = ours[int(s * SR):int(e * SR)]
    best = (-1, 0)
    for k in range(int((s + shift - 0.05) * SR), int((s + shift + 1.6) * SR), 16):
        if k < 0 or k + len(nd) > len(kie):  # a chunk running past Kie's end = truncated render
            continue
        c = ncc(kie[k:k + len(nd)], nd)
        if c > best[0]:
            best = (c, k / SR)
    c, at = best
    p = at - (s + shift)
    if i == 0:
        shift = at; off0 = at
    elif p > 0.03:
        pauses.append([round(s, 4), round(p, 4), labels.get(round(s, 4), "")]); shift += p
    print(f"  chunk {s:5.2f}-{e:5.2f}: at {at:6.3f} corr {c:.2f} pause {p if i else 0:+.3f}")
    assert c > 0.6, f"{name}: chunk at {s:.2f}s not found in Kie audio (corr {c:.2f})"
total = L + sum(p for _, p, _ in pauses)
out = d / f"{name}-conf.mp4"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{off0:.4f}", "-i", str(d / f"{name}.mp4"), "-t", f"{total:.4f}",
                "-r", "24", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out)],
               check=True, stdin=subprocess.DEVNULL)
parts, pos = [], 0
for t, p, _ in pauses:
    parts += [ours[pos:int(t * SR)], np.zeros(int(round(p * SR)), np.float32)]; pos = int(t * SR)
parts.append(ours[pos:]); ref = np.concatenate(parts)
k2 = pcm(out); m = min(len(k2), len(ref)); win = []
for i in range(0, m - SR // 2, SR // 2):
    x, y = k2[i:i + SR // 2], ref[i:i + SR // 2]
    if np.sqrt((y ** 2).mean()) > 0.02:
        win.append(ncc(x, y))
ok = bool(sorted(win)[1] > 0.6 and np.median(win) > 0.8)  # one consonant-edge dip allowed
print(f"{name}-conf.mp4: {total:.3f}s, pauses {pauses}; half-second windows vs voice+pauses min {min(win):.2f} "
      f"median {np.median(win):.2f} {'PASS' if ok else 'CHECK'}")
json.dump({"pauses": pauses, "len": round(total, 4), "sync_min": round(min(win), 3), "ok": ok}, open(d / f"{name}-conf.json", "w"))
