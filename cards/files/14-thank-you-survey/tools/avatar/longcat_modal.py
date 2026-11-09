"""LongCat-Video-Avatar 1.5 (Meituan, MIT) on Modal: avatar still + our voice WAV -> talking video.
Uses its built-in video continuation so one run covers the whole audio track without hard seams.

One-time:  modal run longcat_modal.py::weights
Per take:  modal run longcat_modal.py::talk --image M-ms.png --audio line.wav --out take.mp4 \
               --prompt "scene + performance direction" [--segments 4] [--res 720p]
"""
import glob
import json
import subprocess
from pathlib import Path

import modal

app = modal.App("tantra-longcat")
vol = modal.Volume.from_name("longcat-weights", create_if_missing=True)
W = "/weights"
REPO = "/opt/LongCat-Video"
FLASH = ("https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/"
         "flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl")

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg", "libsndfile1", "libgl1", "libglib2.0-0")
    .pip_install("torch==2.6.0", "torchvision==0.21.0", "torchaudio==2.6.0",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install(FLASH, "ninja", "packaging", "wheel")
    .run_commands(
        f"git clone --depth 1 https://github.com/meituan-longcat/LongCat-Video {REPO}",
        f"cd {REPO} && grep -v -E '^(torch|flash-attn|libsndfile1|tritonserverclient)' requirements.txt > /tmp/r1.txt"
        f" && grep -v -E '^(torch|flash-attn|libsndfile1|tritonserverclient)' requirements_avatar.txt > /tmp/r2.txt"
        " && pip install -r /tmp/r1.txt -r /tmp/r2.txt",
    )
    .pip_install("huggingface_hub[hf_transfer]<1.0")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(image=image, volumes={W: vol}, timeout=4 * 3600, cpu=4)
def download():
    from huggingface_hub import snapshot_download

    snapshot_download("meituan-longcat/LongCat-Video", local_dir=f"{W}/LongCat-Video",
                      allow_patterns=["tokenizer/*", "text_encoder/*", "vae/*", "scheduler/*", "*.json"])
    snapshot_download("meituan-longcat/LongCat-Video-Avatar-1.5", local_dir=f"{W}/LongCat-Video-Avatar-1.5")
    vol.commit()
    print(subprocess.run(f"du -sh {W}/*", shell=True, capture_output=True, text=True).stdout)


@app.function(image=image, gpu="H100", volumes={W: vol}, timeout=2 * 3600, memory=65536)
def generate(image_bytes: bytes, ext: str, audio_bytes: bytes, prompt: str, segments: int,
             res: str, steps: int, audio_cfg: float) -> bytes:
    work = Path("/tmp/job")
    work.mkdir(exist_ok=True)
    (work / f"img{ext}").write_bytes(image_bytes)
    (work / "voice.wav").write_bytes(audio_bytes)
    (work / "in.json").write_text(json.dumps({
        "prompt": prompt, "cond_image": str(work / f"img{ext}"),
        "cond_audio": {"person1": str(work / "voice.wav")}}))
    weights_dir = Path(f"{REPO}/weights")
    if not weights_dir.exists():
        weights_dir.symlink_to(W)
    cmd = ["torchrun", "--nproc_per_node=1", "run_demo_avatar_single_audio_to_video.py",
           "--context_parallel_size=1", "--checkpoint_dir=./weights/LongCat-Video-Avatar-1.5",
           "--stage_1=ai2v", f"--input_json={work / 'in.json'}", f"--resolution={res}",
           f"--num_segments={segments}", "--ref_img_index=10", "--mask_frame_range=3",
           f"--audio_guidance_scale={audio_cfg}", "--output_dir=/tmp/out",
           "--use_distill", "--model_type", "avatar-v1.5", "--use_int8"]
    if steps:
        cmd.append(f"--num_inference_steps={steps}")
    subprocess.run(cmd, cwd=REPO, check=True)
    vids = sorted(glob.glob("/tmp/out/**/*.mp4", recursive=True), key=lambda p: Path(p).stat().st_mtime)
    print("outputs:", vids)
    return Path(vids[-1]).read_bytes()


@app.local_entrypoint()
def weights():
    download.remote()


@app.local_entrypoint()
def talk(image: str, audio: str, out: str, prompt: str, segments: int = 4, res: str = "720p",
         steps: int = 0, audio_cfg: float = 4.0):
    p = Path(image)
    Path(out).write_bytes(generate.remote(p.read_bytes(), p.suffix, Path(audio).read_bytes(),
                                          prompt, segments, res, steps, audio_cfg))
    print(f"saved {out}")
