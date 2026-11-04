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
# MuseTalk reads the task from a YAML (video_path/audio_path), not CLI args,
# so we emit a per-scene config and point --inference_config at it.
_PRESENTER_PY = r"""
import glob
import json
import os
import shutil
import subprocess
import sys

spec = json.load(open(sys.argv[1]))
CODE = "/opt/priv/code/MuseTalk"
os.environ["PYTHONPATH"] = CODE + os.pathsep + os.environ.get("PYTHONPATH", "")

out_dir = os.path.dirname(spec["out"]) or "/tmp"
os.makedirs(out_dir, exist_ok=True)

# per-scene task config (MuseTalk's expected schema)
task_cfg = os.path.join(out_dir, "task.yaml")
with open(task_cfg, "w") as fh:
    fh.write("task_0:\n")
    fh.write(f' video_path: "{spec["portrait"]}"\n')
    fh.write(f' audio_path: "{spec["audio"]}"\n')
    fh.write(" preparation: True\n")
    fh.write(" bbox_shift: 5\n")

PY311 = os.environ.get("MUSETALK_PY", "/opt/priv/venv-musetalk/bin/python")
cmd = [
    PY311, os.path.join(CODE, "scripts", "inference.py"),
    "--inference_config", task_cfg,
    "--unet_config", os.path.join(CODE, "models", "musetalkV15", "musetalk.json"),
    "--unet_model_path", os.path.join(CODE, "models", "musetalkV15", "unet.pth"),
    "--whisper_dir", os.path.join(CODE, "models", "whisper"),
    "--version", "v15",
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
    """One MuseTalk scene -> a local clip. Idempotent: reuse a clip staged by
    an earlier (interrupted) run instead of re-rendering on the GPU."""
    work = f"{R.GPU_WORK}/{name}"
    box_clip = f"{work}/presenter-{idx:02d}.mp4"
    local = os.path.join(ads.TMP, f"{name}-{idx:02d}-presenter.mp4")
    if os.path.exists(local):
        print(f"  scene {idx:02d} cached")
        return local
    payload = dict(portrait=portrait_box, audio=wav_box, out=box_clip, fps=25)
    R.write_file(f"{work}/presenter-{idx:02d}.json", json.dumps(payload))
    R.run_checked(f"{R.GPU_PY} {R.GPU_WORK}/gen_presenter.py "
                  f"{work}/presenter-{idx:02d}.json", timeout=420, log=None)
    R.stage_down(box_clip, f"{name}-presenter-{idx:02d}.mp4", local)
    return local


def _disclose(clip, size, tag):
    """Stamp the AI-disclosure onto every frame.

    ffmpeg's drawtext needs fontconfig, which is not configured on this host's
    build (it crashes with exit 3221225477). Render the label as a transparent
    PNG with our brand font once, then overlay it -- identical result, no
    fontconfig dependency.
    """
    import subprocess

    from PIL import Image, ImageDraw

    import brand as B

    w, h = size
    fs = int(min(size) * 0.035)
    f = B.font("mono", fs)
    label = DISCLOSURE
    tw = B.text_w(label, f)
    asc, desc = f.getmetrics()
    pad = int(fs * 0.6)
    overlay = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle((0, 0, overlay.width - 1, overlay.height - 1),
                fill=(0, 0, 0, 115))
    d.text((pad, pad), label, font=f, fill=(255, 255, 255, 255))
    ov = os.path.join(ads.TMP, f"{tag}-disclosure.png")
    overlay.save(ov)

    x = (w - overlay.width) // 2
    y = int(h * 0.04)
    out = os.path.join(ads.TMP, f"{tag}-disclosed.mp4")
    subprocess.run(
        [ads.FFMPEG, "-y", "-i", clip, "-i", ov,
         "-filter_complex", f"[0:v][1:v]overlay={x}:{y}",
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
