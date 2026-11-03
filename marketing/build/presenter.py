"""Talking-presenter ad style -- MuseTalk lip-sync on the GPU box.

A synthetic presenter introduces the product on camera: one synthetic face
(rendered in-house by Bedrock Stable Image Ultra) is lip-synced to each
voice-over line by MuseTalk 1.5 (MIT-licensed, commercial OK). We do NOT use
Wav2Lip -- the open checkpoint is non-commercial, so it is barred from ads.

Two compliance rules are baked in, per Meta/YouTube/TikTok AI policy:
  * the face must be synthetic, never a real/identifiable person, and
  * every realistic presenter master is stamped with a visible
    "AI-generated presenter" disclosure line and flagged for the platform
    AI-content label.

The result is a per-scene talking-head clip that engine_assemble times to the
voice and wraps in the house captions / logo / CTA / end-card / master.
"""
import json
import os

import backgrounds
import ads
import engine_assemble as EA
import engine_runtime as R

OUT_VID = ads.OUT_VID

DISCLOSURE = "AI-generated presenter"

# GPU-side MuseTalk driver: one portrait + one audio -> one talking clip.
# Calls the MuseTalk inference entrypoint from the cloned code tree, pointed
# at the pre-downloaded weights. Output lands at spec['out'].
_PRESENTER_PY = r"""
import glob
import json
import os
import shutil
import subprocess
import sys

spec = json.load(open(sys.argv[1]))
CODE = "/opt/priv/code/MuseTalk"
MODELS = "/opt/priv/models/musetalk"
os.environ.setdefault("MUSETALK_MODEL_DIR", MODELS)
# the MuseTalk package isn't pip-installed; run with the code tree on the path
sys.path.insert(0, CODE)
os.environ["PYTHONPATH"] = CODE + os.pathsep + os.environ.get("PYTHONPATH", "")

out_dir = os.path.dirname(spec["out"]) or "/tmp"
os.makedirs(out_dir, exist_ok=True)

# MuseTalk's own realtime inference entrypoint, run under its Python 3.11 venv.
PY311 = os.environ.get("MUSETALK_PY", "/opt/priv/venv-musetalk/bin/python")
cmd = [
    PY311, os.path.join(CODE, "scripts", "inference.py"),
    "--inference_config", os.path.join(CODE, "configs", "inference", "realtime.yaml"),
    "--video_path", spec["portrait"],
    "--audio_path", spec["audio"],
    "--result_dir", out_dir,
    "--fps", str(spec.get("fps", 25)),
    "--batch_size", "1",
]
r = subprocess.run(cmd, capture_output=True, text=True, cwd=CODE)
print(r.stdout[-1500:])
# MuseTalk names its own output file; move the newest mp4 to spec['out']
if not os.path.exists(spec["out"]):
    cands = sorted(glob.glob(os.path.join(out_dir, "**", "*.mp4"),
                             recursive=True), key=os.path.getmtime)
    if cands:
        shutil.copy(cands[-1], spec["out"])
if r.returncode != 0 or not os.path.exists(spec["out"]):
    sys.stderr.write(r.stderr[-2000:])
    raise SystemExit(1)
print("wrote", spec["out"])
"""

FACE_PROMPT = (
    "professional presenter head-and-shoulders portrait, facing camera, "
    "neutral confident expression, studio key light, deep navy backdrop with "
    "soft gold rim light, editorial advertising photography, photorealistic, "
    "symmetrical, mouth closed, clearly a composite studio portrait"
)


def _make_portrait(name, size, seed):
    """Render the synthetic presenter face in-house via Bedrock."""
    ratio = "9:16" if size[1] >= size[0] else "16:9"
    path, provider = backgrounds.generate_one(
        FACE_PROMPT, ratio=ratio, name=f"{name}-presenter", seed=seed)
    print(f"  portrait {os.path.basename(path)} [{provider}]")
    return path


def _render_scene(portrait_box, wav_box, idx, name):
    work = f"{R.GPU_WORK}/{name}"
    box_clip = f"{work}/presenter-{idx:02d}.mp4"
    payload = dict(portrait=portrait_box, audio=wav_box, out=box_clip, fps=25)
    R.write_file(f"{work}/presenter-{idx:02d}.json", json.dumps(payload))
    R.run_checked(f"{R.GPU_PY} {R.GPU_WORK}/gen_presenter.py "
                  f"{work}/presenter-{idx:02d}.json", timeout=420, log=None)
    local = os.path.join(ads.TMP, f"{name}-{idx:02d}-presenter.mp4")
    R.stage_down(box_clip, f"{name}-presenter-{idx:02d}.mp4", local)
    return local


def _disclose(clip, size, tag):
    """Burn the AI-disclosure line into the clip (top-centre, small, always on)."""
    import subprocess
    out = os.path.join(ads.TMP, f"{tag}-disclosed.mp4")
    y = int(size[1] * 0.04)
    subprocess.run(
        [ads.FFMPEG, "-y", "-i", clip,
         "-vf", "drawtext=text='" + DISCLOSURE + "':"
                f"fontcolor=white:fontsize={int(min(size) * 0.035)}:"
                f"box=1:boxcolor=black@0.45:boxborderw=8:"
                f"x=(w-text_w)/2:y={y}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", out],
        capture_output=True, text=True, check=True)
    return out


def build(name, cfg):
    """cfg: { size, target, out, scenes:[{vo, end?}], seed?, portrait? }."""
    scenes = cfg["scenes"]
    size = cfg["size"]
    seed = int(cfg.get("seed", 11))
    R.write_file(f"{R.GPU_WORK}/gen_presenter.py", _PRESENTER_PY)
    print(f"\n=== presenter {name}  {size[0]}x{size[1]}  "
          f"{len(scenes)} scenes ===")

    # voice first: the same takes drive both lip-sync and scene timing
    vo_paths, vo_dur = EA.synthesize_voice(scenes, name)

    # one synthetic portrait for the whole spot (consistency), unless the
    # caller supplied one
    portrait = cfg.get("portrait") or _make_portrait(name, size, seed)
    portrait_box = R.stage_up(portrait, f"{name}-portrait.jpg")

    clips = []
    for i, sc in enumerate(scenes):
        if sc.get("end"):
            clips.append(_end_card_clip(name, cfg, i))
            print(f"  scene {i + 1:02d} end-card")
            continue
        if not vo_paths[i]:
            continue
        wav_box = R.stage_up(vo_paths[i], f"{name}-vo-{i + 1:02d}.wav")
        clip = _render_scene(portrait_box, wav_box, i + 1, name)
        clips.append(_disclose(clip, size, f"{name}-{i + 1:02d}"))
        print(f"  scene {i + 1:02d} presenter+disclosure")

    # voice is already synthesized; tell the assembler to reuse it
    return EA.build(name, {**cfg, "_vo_paths": vo_paths, "_vo_dur": vo_dur},
                    clips)


def _end_card_clip(name, cfg, idx):
    im = ads.end_card(cfg["size"])
    still = os.path.join(ads.TMP, f"{name}-{idx:02d}-endcard.jpg")
    im.save(still, quality=93)
    clip = os.path.join(ads.TMP, f"{name}-{idx:02d}-endcard.mp4")
    import subprocess
    subprocess.run(
        [ads.FFMPEG, "-y", "-loop", "1", "-t", "4", "-i", still,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(ads.FPS), clip],
        capture_output=True, text=True, check=True)
    return clip
