"""MiniMax H3 reference-to-video on Kie.ai (hosted): reference images + reference video + Adi's line audio.
Run: python3 kie_h3.py <keyfile.env> <job.json>
job.json: {"images": [...], "video": "vid3.mp4" | null, "audio": "U12.mp3", "prompt_file": "prompt.txt",
           "duration": 6, "resolution": "2K" | "768P", "out": "U12.mp4"}   (paths relative to job.json)
Uploads go to Kie's file store; the task id and credits are logged to <out>.log so nothing is lost.
"""
import base64, json, os, re, ssl, sys, time, urllib.request
from pathlib import Path

keyfile, jobf = sys.argv[1:3]
KEY = re.search(r"[A-Za-z0-9]{24,}", open(os.path.expanduser(keyfile)).read()).group(0)
job = json.load(open(jobf)); base = Path(jobf).parent
try:
    import certifi; CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav"}


def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                               method="POST" if body is not None else "GET",
                               headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=300, context=CTX) as resp:
        return json.loads(resp.read() or b"{}")


def upload(p):
    p = base / p
    b64 = base64.b64encode(p.read_bytes()).decode()
    res = req("https://kieai.redpandaai.co/api/file-base64-upload",
              {"base64Data": f"data:{MIME[p.suffix.lower()]};base64,{b64}", "uploadPath": "h3refs", "fileName": p.name})
    u = (res.get("data") or {}).get("downloadUrl")
    if not u:
        sys.exit(f"upload failed for {p.name}: {res}")
    return u


log = open(base / (job["out"] + ".log"), "a")
inp = {"prompt": (base / job["prompt_file"]).read_text(), "reference_image_urls": [upload(i) for i in job["images"]],
       "reference_audio_urls": [upload(job["audio"])], "aspect_ratio": "16:9", "duration": int(job["duration"]),
       "resolution": job.get("resolution", "2K")}
if job.get("video"):
    inp["reference_video_urls"] = [upload(job["video"])]
sub = req("https://api.kie.ai/api/v1/jobs/createTask", {"model": "minimax-h3/reference-to-video", "input": inp})
tid = (sub.get("data") or {}).get("taskId")
print("submit", json.dumps(sub)[:300], file=log, flush=True)
if not tid:
    sys.exit(f"not started: {sub}")
print("task", tid, flush=True)
t0 = time.time()
while time.time() - t0 < 5400:
    time.sleep(15)
    d = req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}").get("data") or {}
    st = (d.get("state") or "").lower()
    if st == "success":
        rj = d.get("resultJson"); rj = json.loads(rj) if isinstance(rj, str) else rj
        url = (rj.get("resultUrls") or [None])[0]
        with urllib.request.urlopen(url, timeout=600, context=CTX) as r:
            (base / job["out"]).write_bytes(r.read())
        msg = f"saved {job['out']} credits {d.get('creditsConsumed')} secs {round(time.time() - t0)}"
        print(msg, flush=True); print(msg, file=log, flush=True)
        break
    if st == "fail":
        msg = f"failed: {d.get('failMsg') or d.get('failCode')}"
        print(msg, file=log, flush=True); sys.exit(msg)
else:
    sys.exit("timed out")
