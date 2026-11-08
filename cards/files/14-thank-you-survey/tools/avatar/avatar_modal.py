"""Free AI avatar video pipeline on Modal ($30 free compute a month).

Two steps, both open source and licensed for commercial use:
  1. voice : Chatterbox TTS (MIT). Script text -> WAV. Optional 10-20 s reference
             WAV of Adi's voice for cloning; without it the default voice is used.
  2. talk  : InfiniteTalk (Apache-2.0, on Wan2.1-I2V-14B) + lightx2v 4-step LoRA.
             Avatar still (from Kie.ai) + WAV -> lip-synced talking MP4.

One-time:  modal run avatar_modal.py::download      (pulls ~90 GB of weights into a Modal volume)
Per scene: modal run avatar_modal.py::voice --text-file T01.txt --out T01.wav [--ref adi.wav]
           modal run avatar_modal.py::talk  --image avatar.png --audio T01.wav --out T01.mp4 [--size 720]

Keep each scene at 40 s of speech or less: InfiniteTalk holds identity best under ~1 minute.
"""
import json
import subprocess
from pathlib import Path

import modal

app = modal.App("tantra-avatar")
weights = modal.Volume.from_name("infinitetalk-weights", create_if_missing=True)
W = "/weights"
REPO = "/opt/InfiniteTalk"
LORA = "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"

FLASH = (
    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/"
    "flash_attn-2.7.4.post1+cu12torch2.4cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
)

talk_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.4.1", "torchvision==0.19.1", "torchaudio==2.4.1",
        index_url="https://download.pytorch.org/whl/cu121",
    )
    .pip_install("xformers==0.0.28", index_url="https://download.pytorch.org/whl/cu121")
    .pip_install("misaki[en]", "ninja", "psutil", "packaging", "wheel", FLASH)
    .run_commands(
        f"git clone --depth 1 https://github.com/MeiGen-AI/InfiniteTalk {REPO}",
        f"cd {REPO} && pip install -r requirements.txt",
    )
    .pip_install("librosa", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

voice_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install("chatterbox-tts", "torchaudio")
)


@app.function(image=talk_image, volumes={W: weights}, timeout=3 * 3600, cpu=4)
def download_weights():
    from huggingface_hub import hf_hub_download, snapshot_download

    snapshot_download("Wan-AI/Wan2.1-I2V-14B-480P", local_dir=f"{W}/Wan2.1-I2V-14B-480P")
    snapshot_download("TencentGameMate/chinese-wav2vec2-base", local_dir=f"{W}/chinese-wav2vec2-base")
    hf_hub_download("TencentGameMate/chinese-wav2vec2-base", "model.safetensors",
                    revision="refs/pr/1", local_dir=f"{W}/chinese-wav2vec2-base")
    snapshot_download("MeiGen-AI/InfiniteTalk", local_dir=f"{W}/InfiniteTalk",
                      allow_patterns=["single/*", "*.json", "*.md"])
    hf_hub_download("Kijai/WanVideo_comfy", LORA, local_dir=W)
    weights.commit()
    print(subprocess.run(["du", "-sh", W], capture_output=True, text=True).stdout)


@app.function(image=talk_image, gpu="H100", volumes={W: weights}, timeout=2 * 3600)
def generate_talk(image_bytes: bytes, image_ext: str, audio_bytes: bytes,
                  prompt: str, size: str) -> bytes:
    work = Path("/tmp/job")
    work.mkdir(exist_ok=True)
    img = work / f"avatar{image_ext}"
    wav = work / "voice.wav"
    img.write_bytes(image_bytes)
    wav.write_bytes(audio_bytes)
    (work / "in.json").write_text(json.dumps(
        {"prompt": prompt, "cond_video": str(img), "cond_audio": {"person1": str(wav)}}
    ))
    cmd = [
        "python", "generate_infinitetalk.py",
        "--ckpt_dir", f"{W}/Wan2.1-I2V-14B-480P",
        "--wav2vec_dir", f"{W}/chinese-wav2vec2-base",
        "--infinitetalk_dir", f"{W}/InfiniteTalk/single/infinitetalk.safetensors",
        "--lora_dir", f"{W}/{LORA}", "--lora_scale", "1.0",
        "--input_json", str(work / "in.json"),
        "--size", f"infinitetalk-{size}",
        "--sample_text_guide_scale", "1.0", "--sample_audio_guide_scale", "2.0",
        "--sample_steps", "4", "--sample_shift", "2",
        "--mode", "streaming", "--motion_frame", "9", "--max_frame_num", "1500",
        "--save_file", str(work / "out"),
    ]
    subprocess.run(cmd, cwd=REPO, check=True)
    return (work / "out.mp4").read_bytes()


@app.function(image=voice_image, gpu="L4", timeout=1800)
def generate_voice(text: str, ref_bytes: bytes | None, exaggeration: float) -> bytes:
    import io

    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device="cuda")
    ref = None
    if ref_bytes:
        ref = "/tmp/ref.wav"
        Path(ref).write_bytes(ref_bytes)
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=exaggeration, cfg_weight=0.5)
    buf = io.BytesIO()
    torchaudio.save(buf, wav, model.sr, format="wav")
    return buf.getvalue()


@app.local_entrypoint()
def download():
    download_weights.remote()


DEFAULT_PROMPT = (
    "A man in a plain dark crew-neck sits in a dark room with a warm practical lamp and a violet "
    "accent light on the wall, talking straight to camera with natural hand gestures and calm, "
    "confident expressions. Static camera, medium shot."
)


@app.local_entrypoint()
def talk(image: str, audio: str, out: str, size: str = "480", prompt: str = DEFAULT_PROMPT):
    p = Path(image)
    mp4 = generate_talk.remote(p.read_bytes(), p.suffix, Path(audio).read_bytes(), prompt, size)
    Path(out).write_bytes(mp4)
    print(f"saved {out}")


@app.local_entrypoint()
def voice(text_file: str, out: str, ref: str = "", exaggeration: float = 0.5):
    text = Path(text_file).read_text().strip()
    wav = generate_voice.remote(text, Path(ref).read_bytes() if ref else None, exaggeration)
    Path(out).write_bytes(wav)
    print(f"saved {out}")
