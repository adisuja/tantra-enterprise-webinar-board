"""Kling AI Avatar 2.0 on Kie.ai: avatar still + voice -> talking video (pro = 1080p 48 fps).
Run: KIE_API_KEY=... python3 kie_avatar.py <image> <audio> <out.mp4> "<prompt>" [pro|standard]
"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.expanduser("~/tantra-content/kits/content"))
import image as kie  # reuses the content kit's Kie.ai request + upload helpers

img, aud, out, prompt = sys.argv[1:5]
tier = sys.argv[5] if len(sys.argv) > 5 else "pro"
inp = {"image_url": kie.upload(img), "audio_url": kie.upload(aud), "prompt": prompt}
sub = kie.req("/api/v1/jobs/createTask", {"model": f"kling/ai-avatar-{tier}", "input": inp})
tid = (sub.get("data") or {}).get("taskId")
if not tid:
    sys.exit(f"not started: {sub}")
print("task", tid, flush=True)
t0 = time.time()
while time.time() - t0 < 3600:
    time.sleep(10)
    d = kie.req(f"/api/v1/jobs/recordInfo?taskId={tid}").get("data") or {}
    st = (d.get("state") or "").lower()
    if st == "success":
        rj = d.get("resultJson"); rj = json.loads(rj) if isinstance(rj, str) else rj
        url = (rj.get("resultUrls") or [None])[0]
        with urllib.request.urlopen(url, timeout=300, context=kie.ctx()) as r, open(out, "wb") as f:
            f.write(r.read())
        print("saved", out, "credits", d.get("creditsConsumed"), "secs", round(time.time() - t0))
        break
    if st == "fail":
        sys.exit(f"failed: {d.get('failMsg') or d.get('failCode')}")
