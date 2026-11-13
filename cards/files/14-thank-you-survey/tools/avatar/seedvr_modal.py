"""SeedVR2 7B (ByteDance, Apache-2.0) video upscaler on one Modal H100, via the
numz ComfyUI-SeedVR2_VideoUpscaler standalone CLI. Models auto-download into a volume.

Run: modal run seedvr_modal.py --src in.mp4 --out out-4k.mp4 [--res 2160] [--model seedvr2_ema_7b_fp16.safetensors]
"""
import subprocess
from pathlib import Path

import modal

app = modal.App("tantra-seedvr")
vol = modal.Volume.from_name("seedvr-models", create_if_missing=True)
REPO = "/opt/seedvr"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", index_url="https://download.pytorch.org/whl/cu124")
    .run_commands(
        f"git clone --depth 1 https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler {REPO}",
        f"cd {REPO} && pip install -r requirements.txt huggingface_hub",
    )
)


@app.function(image=image, gpu="H100", volumes={"/models": vol}, timeout=3 * 3600, memory=98304)
def upscale(video: bytes, res: int, model: str, batch: int) -> bytes:
    Path("/tmp/in.mp4").write_bytes(video)
    cmd = ["python", "inference_cli.py", "/tmp/in.mp4", "--output", "/tmp/out.mp4",
           "--model_dir", "/models", "--dit_model", model, "--resolution", str(res),
           "--batch_size", str(batch), "--temporal_overlap", "4",
           "--color_correction", "lab", "--video_backend", "ffmpeg",
           "--vae_encode_tiled", "--vae_decode_tiled", "--attention_mode", "sdpa"]
    subprocess.run(cmd, cwd=REPO, check=True)
    vol.commit()
    return Path("/tmp/out.mp4").read_bytes()


@app.function(image=image, gpu="H100", volumes={"/models": vol}, timeout=5 * 3600, memory=98304)
def upscale_many(items: list, res: int, model: str, batch: int, tag: str) -> list:
    """Same CLI and settings as upscale(), one container for many pieces; each output is saved to
    the volume (outputs/<tag>/<name>) the moment it finishes."""
    outs = []
    dest = Path(f"/models/outputs/{tag}"); dest.mkdir(parents=True, exist_ok=True)
    for name, video in items:
        Path("/tmp/in.mp4").write_bytes(video)
        cmd = ["python", "inference_cli.py", "/tmp/in.mp4", "--output", "/tmp/out.mp4",
               "--model_dir", "/models", "--dit_model", model, "--resolution", str(res),
               "--batch_size", str(batch), "--temporal_overlap", "4",
               "--color_correction", "lab", "--video_backend", "ffmpeg",
               "--vae_encode_tiled", "--vae_decode_tiled", "--attention_mode", "sdpa"]
        subprocess.run(cmd, cwd=REPO, check=True)
        data = Path("/tmp/out.mp4").read_bytes()
        (dest / name).write_bytes(data); vol.commit()
        print("stored", f"outputs/{tag}/{name}", flush=True)
        outs.append(data)
    return outs


@app.local_entrypoint()
def many(srcs: str, outdir: str, tag: str, res: int = 2160, model: str = "seedvr2_ema_7b_fp16.safetensors", batch: int = 49):
    """srcs: comma-separated input mp4 paths; outputs <outdir>/<stem>-4k.mp4."""
    paths = [Path(x) for x in srcs.split(",")]
    items = [(p.stem + "-4k.mp4", p.read_bytes()) for p in paths]
    for (name, _), data in zip(items, upscale_many.remote(items, res, model, batch, tag)):
        (Path(outdir) / name).write_bytes(data); print("saved", name)


@app.local_entrypoint()
def main(src: str, out: str, res: int = 2160, model: str = "seedvr2_ema_7b_fp16.safetensors", batch: int = 33):
    data = upscale.remote(Path(src).read_bytes(), res, model, batch)
    Path(out).write_bytes(data)
    print("saved", out)


@app.function(image=image, volumes={"/models": vol}, timeout=3600, cpu=4)
def fetch_models(model: str = "seedvr2_ema_7b_fp16.safetensors"):
    """CPU-only pre-download so no GPU time is spent fetching weights."""
    from huggingface_hub import hf_hub_download
    for f in (model, "ema_vae_fp16.safetensors"):
        hf_hub_download("numz/SeedVR2_comfyUI", f, local_dir="/models")
    vol.commit()


@app.local_entrypoint()
def prefetch():
    fetch_models.remote()
    print("models cached")
