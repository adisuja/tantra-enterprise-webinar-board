"""Conform a Kie H3 clip to Adi's voice by continuous alignment (v2 of kie_conform.py).
Kie keeps the real recording but adds pauses (and, given spare duration, can stretch speech). This tracks the
offset of every voiced 0.25 s window of our line inside Kie's track (monotonic search). The offset must be
piecewise constant: each step up = one inserted pause, placed at the quietest point of our audio between the
two windows. Gradual drift (stretched speech) or unmatched windows reject the clip. A tail that runs past
Kie's end is allowed only if what is lost is silence.
Run: python3 kie_conform2.py <dir> <name> <clip.mp4> <abs_start> <abs_end>
Writes <name>-conf.mp4 and <name>-conf.json {"pauses": [[t_in_line, seconds, "word | word"], ...], "len", "ok"}
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

SR, WIN = 16000, 4000  # 0.25 s windows
d, name, clip, A0, A1 = Path(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
H = Path(__file__).resolve().parents[2] / "private" / "avatar-test"
W = json.load(open(H / "voice" / "upsell" / "words-final.json"))


def pcm(p):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                       capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout
    return np.frombuffer(r, "<i2").astype(np.float32) / 32768


def ncc(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


kie, ours = pcm(d / clip), pcm(d / f"{name}.wav")
L = len(ours) / SR
rms = np.sqrt(np.convolve(ours ** 2, np.ones(320) / 320, "same"))
lag, rows = 0.0, []
for i in range(0, len(ours) - WIN, WIN):
    y = ours[i:i + WIN]
    if np.sqrt((y ** 2).mean()) < 0.03:
        continue
    best = (-1, lag)
    for k in range(int(i + (lag - 0.04) * SR), int(i + (lag + 1.6) * SR), 8):
        if k < 0 or k + WIN > len(kie):
            continue
        c = ncc(kie[k:k + WIN], y)
        if c > best[0]:
            best = (c, (k - i) / SR)
    if best[0] < 0:  # ran past Kie's end
        rows.append((i / SR, None, 0.0)); continue
    rows.append((i / SR, best[1], best[0]))
    if best[0] > 0.6:
        lag = best[1]
good = [r for r in rows if r[1] is not None and r[2] > 0.6]
frac = len(good) / max(1, len(rows))
# piecewise-constant offsets from the matched windows; steps = pauses
pauses, drift, prev = [], 0.0, None
for t, l, c in good:
    if prev is None:
        prev = (t, l); off0 = l; continue
    step = l - prev[1]
    if step > 0.06:
        a, b = int((prev[0] + 0.25) * SR), int(t * SR)
        a, b = min(a, b), max(a, b) + 1
        q = (a + int(np.argmin(rms[a:b]))) / SR if b > a + 1 else t
        w = [x for x in W if (x["start"] + x["end"]) / 2 - A0 <= q]; w2 = [x for x in W if (x["start"] + x["end"]) / 2 - A0 > q]
        lbl = f"{w[-1]['word'].strip() if w else ''} | {w2[0]['word'].strip() if w2 else ''}"
        pauses.append([round(q, 4), round(step, 4), lbl])
        prev = (t, l)
    elif abs(step) > 0.02:
        drift = max(drift, abs(step))
    else:
        prev = (t, prev[1])
total = L + sum(p for _, p, _ in pauses)
short = off0 + total - len(kie) / SR  # seconds missing at the end
lost_voiced = short > 0 and np.sqrt((ours[int((L - short) * SR):] ** 2).mean()) > 0.03
ok = frac > 0.85 and drift <= 0.05 and not lost_voiced
print(f"{name} ({clip}): matched {frac:.0%} windows, drift {drift * 1000:.0f} ms, pauses {pauses}, "
      f"tail short {max(0, short):.2f}s{' (voiced!)' if lost_voiced else ''} -> {'OK' if ok else 'REJECT'}")
if ok:
    use = min(total, len(kie) / SR - off0)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{off0:.4f}", "-i", str(d / clip), "-t", f"{use:.4f}",
                    "-vf", f"tpad=stop_mode=clone:stop_duration={max(0, total - use) + 0.1:.3f}", "-t", f"{total:.4f}",
                    "-r", "24", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", str(d / f"{name}-conf.mp4")],
                   check=True, stdin=subprocess.DEVNULL)
    json.dump({"pauses": pauses, "len": round(total, 4), "ok": True, "src": clip, "match": round(frac, 3)}, open(d / f"{name}-conf.json", "w"))
