"""Gate 1: face and mouth sharpness per clip (Laplacian variance on the detected face at 1344x768).
Pass: face >= 180 and mouth >= 250 (verified hero shots: face 205 to 280, mouth 275 to 405;
the rejected LatentSync shots measured face 55 to 85, mouth 60 to 78).
Run: ~/tools/gaze/.venv/bin/python sharpness_check.py clip1.mp4 [clip2.mp4 ...]
"""
import sys
import cv2
import mediapipe as mp
import numpy as np

fd = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.4)


def sharp(path, samples=8):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    face_v, mouth_v = [], []
    for k in np.linspace(3, max(4, n - 3), samples).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(k))
        ok, f = cap.read()
        if not ok:
            continue
        f = cv2.resize(f, (1344, 768))
        r = fd.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        if not r.detections:
            continue
        b = r.detections[0].location_data.relative_bounding_box
        h, w = f.shape[:2]
        x0, y0 = max(0, int(b.xmin * w)), max(0, int(b.ymin * h))
        x1, y1 = x0 + int(b.width * w), y0 + int(b.height * h)
        face = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        mouth = face[int(face.shape[0] * 0.6):, :]
        face_v.append(cv2.Laplacian(face, cv2.CV_64F).var())
        mouth_v.append(cv2.Laplacian(mouth, cv2.CV_64F).var())
    return (float(np.mean(face_v)) if face_v else 0.0, float(np.mean(mouth_v)) if mouth_v else 0.0, len(face_v))


ok_all = True
for p in sys.argv[1:]:
    f, m, k = sharp(p)
    ok = f >= 180 and m >= 250 and k > 0
    ok_all &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {p}  face={f:.1f}  mouth={m:.1f}  frames_with_face={k}")
sys.exit(0 if ok_all else 1)
