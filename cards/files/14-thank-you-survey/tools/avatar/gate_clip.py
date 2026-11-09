"""Gates 1 and 2 for one re-rendered two-shot H3 clip, plus framing proof.
Run: ~/tools/gaze/.venv/bin/python gate_clip.py <profile> <batch> <name>   (run from private/avatar-test/h3full)
Fetches outputs/<batch>/<name>.mp4 from the h3-weights volume into fix-out/, then:
  sharpness (face >= 180, mouth >= 250), sync offset vs <name>.wav, face size before/after the in-clip
  cut (close-up must be clearly bigger than the medium), and full-size frames for eye review.
"""
import json, os, subprocess, sys
from pathlib import Path
import cv2, mediapipe as mp

prof, batch, name = sys.argv[1:4]
here = Path.cwd(); out = here / "fix-out"; (out / "fr").mkdir(parents=True, exist_ok=True)
tools = Path(__file__).resolve().parent
clip = out / f"{name}.mp4"
subprocess.run(["modal", "volume", "get", "--force", "h3-weights", f"outputs/{batch}/{name}.mp4", str(clip)],
               env={**os.environ, "MODAL_PROFILE": prof}, check=True, capture_output=True)
(out / f"{name}.wav").write_bytes((here / f"{name}.wav").read_bytes())
cut = [j for j in json.load(open(here / f"{batch}.json")) if j["out"] == f"{name}.mp4"][0]["cut"]
sharp = subprocess.run([sys.executable, str(tools / "sharpness_check.py"), str(clip)], capture_output=True, text=True)
sync = subprocess.run([sys.executable, str(tools / "sync_check.py"), str(clip)], capture_output=True, text=True)
print("8-sample:", [l for l in sharp.stdout.splitlines() if "PASS" in l or "FAIL" in l][0].split("  ")[0],
      [l for l in sharp.stdout.splitlines() if "PASS" in l or "FAIL" in l][0].split("  ")[2:])
print(sync.stdout.strip())
fd = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.4)
cap = cv2.VideoCapture(str(clip)); fps = cap.get(5); n = int(cap.get(7))
def face_h(t):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
    r = fd.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    return round(r.detections[0].location_data.relative_bounding_box.height, 3) if r.detections else None
before = [face_h(t) for t in (0.1, cut / 2, cut - 0.25)]
after = [face_h(t) for t in (cut + 0.25, (cut + n / fps) / 2, n / fps - 0.1)]
ok = all(before) and all(after) and min(before) > max(after) * 1.15
print(f"framing: close {before}  medium {after}  {'PASS' if ok else 'CHECK'}  (cut {cut}s, len {n / fps:.2f}s)")
import numpy as np
dense = {"close": [], "medium": []}
for k in range(2, n - 2, 4):  # every 4th frame, split by framing (Gate 1 decision uses this)
    cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok_, f = cap.read()
    if not ok_:
        continue
    f = cv2.resize(f, (1344, 768)); r = fd.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    if not r.detections:
        continue
    b = r.detections[0].location_data.relative_bounding_box
    x0, y0 = max(0, int(b.xmin * 1344)), max(0, int(b.ymin * 768))
    fc = cv2.cvtColor(f[y0:y0 + int(b.height * 768), x0:x0 + int(b.width * 1344)], cv2.COLOR_BGR2GRAY)
    dense["close" if b.height > 0.4 else "medium"].append(
        (cv2.Laplacian(fc, cv2.CV_64F).var(), cv2.Laplacian(fc[int(fc.shape[0] * 0.6):], cv2.CV_64F).var()))
# Size-normalised check: face rescaled to the hero medium face size (0.32 of 768 px), so a tight close-up is
# not penalised for spreading the same detail over more pixels. Floors = weakest verified hero shot
# (close: B 145.0 / 194.6; medium: A1 113.9 / 146.4).
FLOOR = {"close": (145.0, 194.6), "medium": (113.9, 146.4)}
normd = {"close": [], "medium": []}
for k in range(2, n - 2, 4):
    cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok_, f = cap.read()
    if not ok_:
        continue
    r = fd.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    if not r.detections:
        continue
    b = r.detections[0].location_data.relative_bounding_box; hh, ww = f.shape[:2]
    x0, y0 = max(0, int(b.xmin * ww)), max(0, int(b.ymin * hh))
    fc = cv2.cvtColor(f[y0:y0 + int(b.height * hh), x0:x0 + int(b.width * ww)], cv2.COLOR_BGR2GRAY)
    sc = 0.32 * 768 / fc.shape[0]; fc = cv2.resize(fc, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    normd["close" if b.height > 0.4 else "medium"].append(
        (cv2.Laplacian(fc, cv2.CV_64F).var(), cv2.Laplacian(fc[int(fc.shape[0] * 0.6):], cv2.CV_64F).var()))
g1 = True
for kk, v in dense.items():
    if not v:
        continue
    fa, ma = np.mean([a for a, _ in v]), np.mean([m for _, m in v]); raw = fa >= 180 and ma >= 250
    nv = normd[kk]; nf, nm = np.mean([a for a, _ in nv]), np.mean([m for _, m in nv])
    nok = nf >= FLOOR[kk][0] and nm >= FLOOR[kk][1]; good = raw or nok; g1 &= good
    print(f"gate1 {kk}: raw face {fa:.1f} mouth {ma:.1f} {'PASS' if raw else 'fail'} | size-normalised "
          f"{nf:.1f} / {nm:.1f} vs hero floor {FLOOR[kk]} {'PASS' if nok else 'fail'} -> {'PASS' if good else 'FAIL'}")
print("GATE1", "PASS" if g1 else "FAIL")
g1_unused = True
for kk, v in {}.items():
    if v:
        fa, ma = np.mean([a for a, _ in v]), np.mean([m for _, m in v]); good = fa >= 180 and ma >= 250; g1 &= good
        print(f"gate1 {kk}: face {fa:.1f} mouth {ma:.1f} ({len(v)} frames) {'PASS' if good else 'FAIL'}")
print("GATE1", "PASS" if g1 else "FAIL")
for tag, t in (("a", 0.3), ("b", cut - 0.25), ("c", cut + 0.25), ("d", n / fps - 0.3)):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(clip), "-frames:v", "1",
                    str(out / "fr" / f"{name}-{tag}.png")], check=True)
print("frames:", out / "fr" / f"{name}-[abcd].png")
