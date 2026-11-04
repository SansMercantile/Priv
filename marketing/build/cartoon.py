"""Cartoon ad style -- AnimateDiff on the GPU box.

Open text-to-video models emit 2-4s clips, so a 1-minute cartoon is a sequence
of short animated scenes. Each scene is one AnimateDiff generation (a motion
module over Stable Diffusion 1.5) driven by a prompt; clips come back over the
S3 shuttle and are handed to engine_assemble.build, which times them to the
voice-over and adds captions / logo / CTA / end-card / the -13 LUFS master.

In-house: SD1.5 + AnimateDiff run on our own A10G via diffusers. No paid API.
"""
import json
import os

import ads
import engine_assemble as EA
import engine_runtime as R

OUT_VID = ads.OUT_VID

# AnimateDiff is happiest at 16 frames / small canvas; the A10G (23GB) holds
# SD1.5 + the motion adapter at 512x288 and we scale up in the compositor.
# The canvas is chosen per render: a square-ish frame reads better cropped to
# 9:16 vertical; a landscape frame is native for 16:9 wide.
GEN = dict(width=512, height=288, frames=16, steps=25, guidance=7.5, fps=8)


def _gen_for(size):
    w, h = size
    if h > w:                                  # vertical target -> taller canvas
        return {**GEN, "width": 448, "height": 448}
    return dict(GEN)                           # landscape target -> 16:9 canvas

STYLE = ("clean 2D flat cartoon, bold navy and gold palette, simple geometric "
         "shapes, smooth looping motion, explainer-animation look, high quality")
NEG = ("photoreal, realistic person, human face, blurry, watermark, text, "
       "letters, words, signature, nsfw, low quality")

# GPU-side generator: one scene spec in, one mp4 out. Uploaded once per run.
# The official guoyww/animatediff repo ships raw motion-module .ckpt files, so
# the adapter loads via from_single_file; SD1.5 is the full diffusers tree.
_SCENE_PY = r"""
import json, sys, torch
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
from diffusers.utils import export_to_video

spec = json.load(open(sys.argv[1]))
M = "/opt/priv/models"
adapter = MotionAdapter.from_single_file(f"{M}/animatediff/v3_sd15_mm.ckpt",
                                         torch_dtype=torch.float16)
pipe = AnimateDiffPipeline.from_pretrained(
    f"{M}/sd15", motion_adapter=adapter, torch_dtype=torch.float16)
pipe.scheduler = DDIMScheduler.from_config(
    pipe.scheduler.config, clip_sample=False, beta_schedule="linear")
pipe = pipe.to("cuda")
pipe.vae.enable_slicing()
g = torch.Generator("cuda").manual_seed(spec.get("seed", 42))
out = pipe(prompt=spec["prompt"], negative_prompt=spec.get("negative", ""),
           num_frames=spec["frames"], num_inference_steps=spec["steps"],
           guidance_scale=spec["guidance"], width=spec["width"],
           height=spec["height"], generator=g)
export_to_video(out.frames[0], spec["out"], fps=spec.get("fps", 8))
print("wrote", spec["out"])
"""


def _upload_generator():
    R.write_file(f"{R.GPU_WORK}/gen_scene.py", _SCENE_PY)


def _render_scene(spec, idx, name, seed, size):
    """One AnimateDiff scene -> a local mp4 clip path.

    Idempotent: if the clip is already staged locally from an earlier
    (interrupted) run, reuse it instead of regenerating on the GPU.
    """
    work = f"{R.GPU_WORK}/{name}"
    box_clip = f"{work}/scene-{idx:02d}.mp4"
    local = os.path.join(ads.TMP, f"{name}-{idx:02d}-cartoon.mp4")
    if os.path.exists(local):
        print(f"  scene {idx:02d} cached")
        return local
    prompt = f"{spec['prompt']}, {STYLE}"
    payload = dict(prompt=prompt, negative=NEG, out=box_clip,
                   seed=seed + idx, **_gen_for(size))
    R.write_file(f"{work}/scene-{idx:02d}.json", json.dumps(payload))
    R.run_checked(f"{R.GPU_PY} {R.GPU_WORK}/gen_scene.py "
                  f"{work}/scene-{idx:02d}.json", timeout=900, poll=8, log=None)
    R.stage_down(box_clip, f"{name}-scene-{idx:02d}.mp4", local)
    return local


def build(name, cfg):
    """cfg: { size, target, out, scenes:[{prompt, vo, end?}], seed? } -> path."""
    scenes = cfg["scenes"]
    seed = int(cfg.get("seed", 7))
    _upload_generator()
    print(f"\n=== cartoon {name}  {cfg['size'][0]}x{cfg['size'][1]}  "
          f"{len(scenes)} scenes ===")

    clips = []
    for i, sc in enumerate(scenes):
        if sc.get("end"):
            # end-card is rendered locally as a still->clip by the compositor
            clips.append(_end_card_clip(name, cfg, i))
            print(f"  scene {i + 1:02d} end-card")
            continue
        clips.append(_render_scene(sc, i + 1, name, seed, cfg["size"]))
        print(f"  scene {i + 1:02d} generated")

    return EA.build(name, cfg, clips)


def _end_card_clip(name, cfg, idx):
    """Render the end-card as a short still clip via the compositor's own
    end_card art, so the final beat carries the branded CTA."""
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
