"""CPU-only app: pulls the InfiniteTalk weights into the Modal volume. Kept apart from
avatar_modal.py because Modal refuses to start an app that defines GPU functions
until the workspace has a payment method.

Run: modal run avatar_weights.py
"""
import subprocess

import modal

app = modal.App("tantra-avatar-weights")
weights = modal.Volume.from_name("infinitetalk-weights", create_if_missing=True)
W = "/weights"
LORA = "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(image=image, volumes={W: weights}, timeout=3 * 3600, cpu=4)
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


@app.local_entrypoint()
def main():
    download_weights.remote()
