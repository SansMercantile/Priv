"""Voice cloning -- two clearly-separated paths on the GPU box.

Per the licence rules (same trap as Wav2Lip):

  - "client"   -> Chatterbox (ResembleAI, MIT code + weights, built-in PerTh
                  watermark). The ONLY path allowed for client-facing output.
  - "inhouse"  -> XTTS v2 (Coqui Public Model License, NON-COMMERCIAL ONLY).
                  For internal/in-house experimentation only -- never for
                  anything that ships. Coqui closed, so no commercial licence
                  exists.

A consent gate applies to BOTH: we only clone voices we have rights to (our
own recordings). The engine refuses to proceed without `consent: true` naming
who consented. And a cloned take still loses to a recorded human take
everywhere, by design (videos.recording() wins).
"""
import base64
import json
import os
import time

import engine_runtime as R

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "voiceover", "cloned")

MODELS = {
    "client": dict(
        repo="ResembleAI/chatterbox",
        license="MIT (code + weights, PerTh watermark)",
        commercial=True,
    ),
    "inhouse": dict(
        repo="coqui/XTTS-v2",
        license="Coqui Public Model License (NON-COMMERCIAL ONLY)",
        commercial=False,
    ),
}

# GPU-side cloner. Runs Chatterbox or XTTS in its own venv; reference voice +
# text in, cloned wav out.
_CLONE_PY = r"""
import json
import os
import sys

spec = json.load(open(sys.argv[1]))
path = spec["path"]
text = spec["text"]
ref = spec["ref"]
out = spec["out"]
model = "/opt/priv/models/voice"

if path == "client":
    # Chatterbox (MIT) -- client-facing, watermarked
    import torch
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(model + "/chatterbox", device="cuda")
    wav = m.generate(text, audio_prompt_path=ref)
    import torchaudio
    torchaudio.save(out, wav, m.sr)
else:
    # XTTS v2 (CPML, non-commercial) -- in-house only
    from TTS.api import TTS
    tts = TTS(model + "/xtts_v2", gpu=True)
    tts.tts_to_file(text=text, file_path=out, speaker_wav=ref, language="en")

print("wrote", out)
"""

INSTALL_SH = r"""
set -euo pipefail
PY=/opt/pytorch/bin/python
M=/opt/priv/models/voice
mkdir -p "$M"
$PY -m pip install --quiet --upgrade pip
# client-facing: Chatterbox (MIT). in-house: coqui-tts (XTTS, Idiap fork).
$PY -m pip install --quiet chatterbox-tts coqui-tts torchaudio 2>&1 | tail -5 || true
$PY - <<'PY'
import os
from huggingface_hub import snapshot_download
M = "/opt/priv/models/voice"
def snap(repo, target):
    p = os.path.join(M, target)
    if os.path.exists(os.path.join(p, ".done")):
        print("skip", target); return
    snapshot_download(repo_id=repo, local_dir=p)
    open(os.path.join(p, ".done"), "w").close()
    print("done", target)
snap("ResembleAI/chatterbox", "chatterbox")
snap("coqui/XTTS-v2", "xtts_v2")
print("VOICE_MODELS_READY")
PY
"""


def ensure_installed():
    """Upload + run the one-time model install (idempotent)."""
    R.write_file(f"{R.GPU_WORK}/install_voice.sh", INSTALL_SH)
    status, out, err = R.run(
        f"bash {R.GPU_WORK}/install_voice.sh", timeout=1800, poll=15)
    if "VOICE_MODELS_READY" not in (out or ""):
        raise RuntimeError(f"voice model install failed: {(err or out)[-600:]}")


def voices():
    """The two clone paths, with their licence terms, for the catalog."""
    return {k: dict(repo=v["repo"], license=v["license"],
                    commercial=v["commercial"]) for k, v in MODELS.items()}


def clone(text, ref_audio, path, name=None, consent=None):
    """Clone `ref_audio` reading `text` via the given path.

    consent must be a non-empty string naming who consented to the clone
    (e.g. "self", "founder-name"). Without it the engine refuses -- we only
    clone voices we have rights to.
    """
    if path not in MODELS:
        raise SystemExit(f"path must be one of: {', '.join(MODELS)}")
    if not consent:
        raise SystemExit(
            "consent is required: name who consented to this voice clone. "
            "We only clone voices we have rights to.")
    if not MODELS[path]["commercial"]:
        print("  NOTE: inhouse path is NON-COMMERCIAL (internal use only)")
    os.makedirs(OUT, exist_ok=True)
    name = name or f"clone-{path}-{time.strftime('%Y%m%d-%H%M%S')}"
    out_wav = os.path.join(OUT, name + ".wav")

    # stage the reference voice up, run the clone on the GPU, pull the result
    ref_box = R.stage_up(ref_audio, f"{name}-ref.wav")
    work = f"{R.GPU_WORK}/{name}"
    box_out = f"{work}/clone.wav"
    payload = dict(path=path, text=text, ref=ref_box, out=box_out)
    R.write_file(f"{work}/clone.json", json.dumps(payload))
    R.write_file(f"{work}/clone_voice.py", _CLONE_PY)
    R.run_checked(f"{R.GPU_PY} {work}/clone_voice.py {work}/clone.json",
                  timeout=600, log=None)
    R.stage_down(box_out, f"{name}-clone.wav", out_wav)

    rel = os.path.relpath(out_wav, os.path.join(os.path.dirname(OUT), "..")) \
        .replace("\\", "/")
    return {
        "path": path,
        "license": MODELS[path]["license"],
        "commercial": MODELS[path]["commercial"],
        "consent": consent,
        "text": text,
        "wav": {"rel": os.path.relpath(out_wav, os.path.dirname(OUT)).replace("\\", "/"),
                "url": "/marketing-assets/" +
                       os.path.relpath(out_wav, os.path.dirname(OUT)).replace("\\", "/")},
        "exists": os.path.exists(out_wav),
    }


def run(spec):
    return clone(text=spec["text"], ref_audio=spec["ref"], path=spec["path"],
                 name=spec.get("name"), consent=spec.get("consent"))
