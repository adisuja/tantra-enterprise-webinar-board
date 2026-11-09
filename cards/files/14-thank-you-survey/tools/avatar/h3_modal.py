"""MiniMax H3 Ref2VA on Modal (vLLM-Omni), audio-locked to our own voice file.

Layout follows vLLM-Omni's validated two-80GB-GPU recipe: TP2 DiT + VAEs resident,
Qwen3-VL text encoder streamed layer by layer from host memory. Speed: LightX2V
Ref2VA Turbo 8-step adapter (8 steps, flow_shift 6). Lip sync: audio_mode=lock_source
keeps our waveform clean in the audio latent so the video is driven by it.

One-time:  modal run h3_modal.py::weights
Batch:     modal run h3_modal.py::render --jobs jobs.json
  jobs.json = [{"image": "...png", "audio": "...wav", "prompt": "...", "out": "...mp4",
                "seed": 7, "duration": 9.5}, ...]   (duration 4 to 15 s, >= audio length)
"""
import base64
import json
import subprocess
import time
from pathlib import Path

import modal

app = modal.App("tantra-h3")
vol = modal.Volume.from_name("h3-weights", create_if_missing=True)
W = "/w"
MODEL = f"{W}/MiniMax-H3"
TURBO = "minimax_h3_ref2v_turbo_8step_v1.0_768p_bf16.safetensors"
LORA = f"{W}/turbo/{TURBO}"
OMNI = "/opt/vllm-omni"

image = (
    modal.Image.from_registry("nvidia/cuda:13.0.1-devel-ubuntu24.04", add_python="3.12")
    .apt_install("git", "ffmpeg", "curl", "libgl1", "libglib2.0-0")
    .pip_install("uv")
    .run_commands(
        "uv pip install --system --torch-backend=cu130 vllm==0.33.0",
        f"git clone --depth 1 https://github.com/vllm-project/vllm-omni {OMNI}",
        f"cd {OMNI} && uv pip install --system -e .",
        "uv pip install --system 'huggingface_hub[hf_transfer]' requests",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HUB_OFFLINE": "0"})
)


@app.function(image=image, volumes={W: vol}, timeout=5 * 3600, cpu=8)
def download():
    from huggingface_hub import hf_hub_download, snapshot_download

    snapshot_download("MiniMaxAI/MiniMax-H3", local_dir=MODEL,
                      allow_patterns=["model_index.json", "Ref2VA/*", "Ref2VA/**"])
    hf_hub_download("lightx2v/Minimax-h3-Turbo", TURBO, local_dir=f"{W}/turbo")
    vol.commit()
    print(subprocess.run(f"du -sh {MODEL} {W}/turbo", shell=True, capture_output=True, text=True).stdout)


def _serve() -> subprocess.Popen:
    env = {"VLLM_WORKER_MULTIPROC_METHOD": "spawn", "VLLM_OMNI_VIDEO_SYNC_TIMEOUT": "3600",
           "VLLM_OMNI_DLO_DP_WAVE_TIMEOUT": "3600", "HF_HUB_OFFLINE": "1",
           "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
    import os
    cmd = ["vllm", "serve", MODEL, "--omni", "--host", "127.0.0.1", "--port", "8091",
           "--trust-remote-code", "--task-type", "ref2va", "--num-gpus", "2",
           "--tensor-parallel-size", "2", "--usp", "1", "--ring", "1", "--text-encoder-tp-size", "2",
           "--vae-patch-parallel-size", "2", "--vae-parallel-mode", "tile", "--vae-use-tiling",
           "--diffusion-attention-backend", "FLASH_ATTN",
           "--diffusion-offload-config", '{"mode":"layer","components":["text_encoder"]}',
           "--lora-backend", "peft", "--lora-path", LORA]
    return subprocess.Popen(cmd, env={**os.environ, **env})


@app.function(image=image, gpu="H100:2", volumes={W: vol}, timeout=4 * 3600,
              memory=262144, cpu=16)
def render_batch(jobs: list) -> list:
    import requests

    proc = _serve()
    t0 = time.time()
    while True:
        try:
            if requests.get("http://127.0.0.1:8091/health", timeout=5).status_code == 200:
                break
        except Exception:
            pass
        if proc.poll() is not None:
            raise RuntimeError("vllm serve exited during startup")
        if time.time() - t0 > 3600:
            raise RuntimeError("server did not start in 60 min")
        time.sleep(10)
    print(f"server ready in {time.time() - t0:.0f}s", flush=True)

    outs = []
    for j in jobs:
        audio_url = "data:audio/wav;base64," + base64.b64encode(j["audio_bytes"]).decode()
        extra = {"task": "ref2va", "duration": j["duration"], "audio_mode": "lock_source",
                 "audio_flow_shift": 3.0}
        data = {
            "prompt": j["prompt"], "width": "1344", "height": "768", "fps": "24",
            "num_inference_steps": "8", "flow_shift": "6", "seed": str(j.get("seed", 7)),
            "extra_params": json.dumps(extra),
            "audio_reference": json.dumps({"audio_url": audio_url}),
            "lora": json.dumps({"name": "h3-ref2v-turbo", "path": LORA, "scale": 1.0}),
        }
        files = {"input_reference": ("ref.png", j["image_bytes"], "image/png")}
        t1 = time.time()
        r = requests.post("http://127.0.0.1:8091/v1/videos/sync", data=data, files=files, timeout=3600)
        print(f"job {j['out']}: HTTP {r.status_code} in {time.time() - t1:.0f}s", flush=True)
        if r.status_code != 200:
            print(r.text[:2000], flush=True)
            outs.append(None)
        else:
            outs.append(r.content)
    proc.terminate()
    return outs


@app.local_entrypoint()
def weights():
    download.remote()


@app.local_entrypoint()
def render(jobs: str):
    spec = json.loads(Path(jobs).read_text())
    base = Path(jobs).parent
    payload = []
    for j in spec:
        payload.append({**j, "image_bytes": (base / j["image"]).read_bytes(),
                        "audio_bytes": (base / j["audio"]).read_bytes()})
    for j, out in zip(spec, render_batch.remote(payload)):
        if out:
            (base / j["out"]).write_bytes(out)
            print("saved", j["out"])
        else:
            print("FAILED", j["out"])
