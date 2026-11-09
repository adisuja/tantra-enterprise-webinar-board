"""Local voice step (free, Apple Silicon): Chatterbox TTS cloning Adi's voice.
Run with ~/tools/chatterbox/.venv/bin/python voice_local.py <text.txt> <out.wav> [ref.wav] [exaggeration]
"""
import sys

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS

text_file, out = sys.argv[1], sys.argv[2]
ref = sys.argv[3] if len(sys.argv) > 3 else None
exag = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
device = "mps" if torch.backends.mps.is_available() else "cpu"
_load = torch.load
torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": torch.device(device)})
model = ChatterboxTTS.from_pretrained(device=device)
text = open(text_file).read().strip()
wav = model.generate(text, audio_prompt_path=ref, exaggeration=exag, cfg_weight=0.5)
torchaudio.save(out, wav.cpu(), model.sr)
print("saved", out, round(wav.shape[-1] / model.sr, 1), "s")
