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
           "--batch_size", str(batch), "--temporal_overlap", "4", "--prepend_frames", "4",
           "--color_correction", "lab", "--video_backend", "ffmpeg",
           "--vae_encode_tiled", "--vae_decode_tiled", "--attention_mode", "sdpa"]
    subprocess.run(cmd, cwd=REPO, check=True)
    vol.commit()
    return Path("/tmp/out.mp4").read_bytes()


@app.local_entrypoint()
def main(src: str, out: str, res: int = 2160, model: str = "seedvr2_ema_7b_fp16.safetensors", batch: int = 33):
    data = upscale.remote(Path(src).read_bytes(), res, model, batch)
    Path(out).write_bytes(data)
    print("saved", out)
