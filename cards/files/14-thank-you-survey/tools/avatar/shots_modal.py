"""Shot-by-shot avatar pipeline on Modal (open source, commercial use allowed).

  1. gesture : Wan2.2 I2V-A14B (Apache-2.0) with the Lightning 4-step distill, 1280x720.
               Avatar still + a written gesture direction -> a 2 to 5 s moving shot.
  2. lipsync : LatentSync 1.6 (Apache-2.0), 512 px face. Redraws only the mouth area to
               match the voice line, so the gestures from step 1 stay untouched.

One-time:  modal run shots_modal.py::weights
Per shot:  modal run shots_modal.py::shot --image M-ms.png --audio S01.wav \
               --prompt "gesture direction" --out S01.mp4 [--seed 7]
"""
import subprocess
from pathlib import Path

import modal

app = modal.App("tantra-shots")
vol = modal.Volume.from_name("shots-weights", create_if_missing=True)
V = "/w"
WAN = f"{V}/Wan2.2-I2V-A14B-Lightning-Diffusers"
LS_REPO = "/opt/LatentSync"

wan_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("diffusers==0.35.2", "transformers==4.51.3", "huggingface_hub[hf_transfer]<1.0", "accelerate",
                 "ftfy", "sentencepiece", "imageio[ffmpeg]", "pillow")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

ls_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("ffmpeg", "git", "libgl1", "libglib2.0-0", "build-essential")
    .run_commands(
        f"git clone --depth 1 https://github.com/bytedance/LatentSync {LS_REPO}",
        f"cd {LS_REPO} && pip install -r requirements.txt",
    )
    .pip_install("huggingface_hub[hf_transfer]==0.30.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(image=wan_image, volumes={V: vol}, timeout=3 * 3600, cpu=4)
def download():
    from huggingface_hub import hf_hub_download, snapshot_download

    snapshot_download("magespace/Wan2.2-I2V-A14B-Lightning-Diffusers", local_dir=WAN)
    for f in ("latentsync_unet.pt", "whisper/tiny.pt"):
        hf_hub_download("ByteDance/LatentSync-1.6", f, local_dir=f"{V}/latentsync")
    vol.commit()


NEG = ("blurry, low quality, distorted face, deformed hands, extra fingers, fused fingers, "
       "morphing, flicker, jitter, cartoon, text, watermark, static, frozen")


@app.function(image=wan_image, gpu="H100", volumes={V: vol}, timeout=3600, memory=98304)
def gesture(image_bytes: bytes, prompt: str, frames: int, seed: int) -> bytes:
    import io

    import torch
    from diffusers import WanImageToVideoPipeline
    from diffusers.utils import export_to_video
    from PIL import Image

    pipe = WanImageToVideoPipeline.from_pretrained(WAN, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((1280, 720), Image.LANCZOS)
    out = pipe(image=img, prompt=prompt, negative_prompt=NEG, height=720, width=1280,
               num_frames=frames, num_inference_steps=4, guidance_scale=1.0, guidance_scale_2=1.0,
               generator=torch.Generator("cuda").manual_seed(seed)).frames[0]
    export_to_video(out, "/tmp/g.mp4", fps=16)
    return Path("/tmp/g.mp4").read_bytes()


@app.function(image=ls_image, gpu="H100", volumes={V: vol}, timeout=3600)
def lipsync(video_bytes: bytes, audio_bytes: bytes, steps: int, guidance: float) -> bytes:
    ck = Path(LS_REPO) / "checkpoints"
    if not ck.exists():
        ck.symlink_to(f"{V}/latentsync")
    Path("/tmp/in.mp4").write_bytes(video_bytes)
    Path("/tmp/in.wav").write_bytes(audio_bytes)
    # LatentSync works at 25 fps; Wan renders at 16 fps.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/in.mp4", "-vf", "fps=25",
                    "-c:v", "libx264", "-crf", "12", "/tmp/in25.mp4"], check=True)
    subprocess.run(["python", "-m", "scripts.inference",
                    "--unet_config_path", "configs/unet/stage2_512.yaml",
                    "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
                    "--inference_steps", str(steps), "--guidance_scale", str(guidance),
                    "--video_path", "/tmp/in25.mp4", "--audio_path", "/tmp/in.wav",
                    "--video_out_path", "/tmp/out.mp4"], cwd=LS_REPO, check=True)
    return Path("/tmp/out.mp4").read_bytes()


@app.local_entrypoint()
def weights():
    download.remote()


@app.local_entrypoint()
def shot(image: str, audio: str, prompt: str, out: str, seed: int = 7, frames: int = 81,
         steps: int = 30, guidance: float = 1.8, keep_gesture: bool = True):
    g = gesture.remote(Path(image).read_bytes(), prompt, frames, seed)
    if keep_gesture:
        Path(out.replace(".mp4", "-gesture.mp4")).write_bytes(g)
    Path(out).write_bytes(lipsync.remote(g, Path(audio).read_bytes(), steps, guidance))
    print(f"saved {out}")


@app.local_entrypoint()
def dub(video: str, audio: str, out: str, steps: int = 30, guidance: float = 1.8):
    """Redraw only the mouth of an existing clip to match new audio (LatentSync 1.6)."""
    Path(out).write_bytes(lipsync.remote(Path(video).read_bytes(), Path(audio).read_bytes(), steps, guidance))
    print(f"saved {out}")


@app.function(image=wan_image, volumes={V: vol}, timeout=3600, cpu=4)
def download_latentsync():
    from huggingface_hub import hf_hub_download
    for f in ("latentsync_unet.pt", "whisper/tiny.pt"):
        hf_hub_download("ByteDance/LatentSync-1.6", f, local_dir=f"{V}/latentsync")
    vol.commit()


@app.local_entrypoint()
def ls_weights():
    download_latentsync.remote()
    print("latentsync cached")


@app.function(image=ls_image, gpu="H100", volumes={V: vol}, timeout=3 * 3600)
def lipsync_batch(items: list, steps: int, guidance: float) -> list:
    """items: [(name, video_bytes, audio_bytes)] -> [(name, mp4_bytes or None)]; one container for all."""
    ck = Path(LS_REPO) / "checkpoints"
    if not ck.exists():
        ck.symlink_to(f"{V}/latentsync")
    out = []
    for name, vb, ab in items:
        Path("/tmp/in.mp4").write_bytes(vb)
        Path("/tmp/in.wav").write_bytes(ab)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/in.mp4", "-vf", "fps=25",
                        "-c:v", "libx264", "-crf", "12", "/tmp/in25.mp4"], check=True)
        r = subprocess.run(["python", "-m", "scripts.inference",
                            "--unet_config_path", "configs/unet/stage2_512.yaml",
                            "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
                            "--inference_steps", str(steps), "--guidance_scale", str(guidance),
                            "--video_path", "/tmp/in25.mp4", "--audio_path", "/tmp/in.wav",
                            "--video_out_path", "/tmp/out.mp4"], cwd=LS_REPO)
        out.append((name, Path("/tmp/out.mp4").read_bytes() if r.returncode == 0 else None))
        print("done", name, r.returncode, flush=True)
    return out


@app.local_entrypoint()
def dub_many(spec: str, steps: int = 30, guidance: float = 1.8):
    """spec json: [{"video": path, "audio": path, "out": path}] relative to the spec file."""
    import json
    base = Path(spec).parent
    jobs = json.loads(Path(spec).read_text())
    items = [(j["out"], (base / j["video"]).read_bytes(), (base / j["audio"]).read_bytes()) for j in jobs]
    for name, data in lipsync_batch.remote(items, steps, guidance):
        if data:
            (base / name).write_bytes(data)
            print("saved", name)
        else:
            print("FAILED", name)
