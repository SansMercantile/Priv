"""Doodle / whiteboard ad style -- fully local, no generative model.

The classic explainer look: a clean near-white board, our key art centred,
and hand-drawn marker doodles (underlines, arrows, circles, stars) sketching
themselves around it in navy and gold. Because the strokes are drawn frame by
frame with Pillow's line-dash trick, no GPU or model is needed -- it renders
locally in seconds and is 100% deterministic.

Each scene becomes a short clip that engine_assemble times to the voice and
wraps in the house captions / logo / CTA / end-card / -13 LUFS master.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter

import brand as B
import backgrounds as BG
import posters as P
import ads
import engine_assemble as EA

OUT_VID = ads.OUT_VID
FPS = ads.FPS
DOODLE_FPS = 12          # hand-drawn feel: lower framerate reads as sketchy
INK = B.NAVY
ACCENT = B.GOLD
PAPER = (247, 246, 241)


# ---------------------------------------------------------------- strokes --
def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _polyline(pts, t):
    """The partial path of a polyline at progress t in [0,1]."""
    if t <= 0:
        return [pts[0]]
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs) or 1.0
    want = t * total
    out = [pts[0]]
    acc = 0.0
    for i, s in enumerate(segs):
        if acc + s >= want:
            out.append(_lerp(pts[i], pts[i + 1], (want - acc) / s))
            return out
        out.append(pts[i + 1])
        acc += s
    return out


def _draw_polyline(draw, pts, t, color, width):
    path = _polyline(pts, t)
    if len(path) > 1:
        draw.line(path, fill=color, width=width, joint="curve")


def _underline(draw, cx, cy, w, t, color, width):
    pts = [(cx - w / 2, cy), (cx + w / 2, cy - int(w * 0.03)),
           (cx + w / 2, cy + 2)]
    _draw_polyline(draw, pts, t, color, width)


def _circle(draw, cx, cy, r, t, color, width):
    steps = 60
    pts = [(cx + r * math.cos(2 * math.pi * i / steps - math.pi / 2),
            cy + r * math.sin(2 * math.pi * i / steps - math.pi / 2))
           for i in range(steps + 1)]
    _draw_polyline(draw, pts, t, color, width)


def _arrow(draw, x0, y0, x1, y1, t, color, width):
    # shaft
    _draw_polyline(draw, [(x0, y0), (x1, y1)], t, color, width)
    # head appears only near the end
    if t > 0.7:
        ht = (t - 0.7) / 0.3
        ang = math.atan2(y1 - y0, x1 - x0)
        L = width * 4
        for da in (2.6, -2.6):
            tip = (x1 - L * math.cos(ang + da), y1 - L * math.sin(ang + da))
            _draw_polyline(draw, [(x1, y1), tip], ht, color, width)


def _star(draw, cx, cy, r, t, color, width):
    pts = []
    for i in range(11):
        rr = r if i % 2 == 0 else r * 0.45
        a = math.pi * i / 5 - math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    _draw_polyline(draw, pts, t, color, width)


DOODLES = {
    "underline": _underline, "circle": _circle, "arrow": _arrow,
    "star": _star,
}


# --------------------------------------------------------------- rendering --
def _scene_frame(size, art, doodles, headline, t, hand):
    """One frame: paper + art + doodles drawn to progress t."""
    w, h = size
    im = Image.new("RGB", size, PAPER)
    # faint paper texture / vignette so it isn't a flat white card
    im = B.vignette(im, 0.06).convert("RGB")

    # key art, slightly inset with a torn-paper white border
    if art is not None:
        a = art.resize((int(w * 0.6), int(h * 0.6)), Image.LANCZOS)
        ax, ay = (w - a.width) // 2, int(h * 0.16)
        border = Image.new("RGB", (a.width + 24, a.height + 24), (255, 255, 255))
        border.paste(a, (12, 12))
        im.paste(border, (ax - 12, ay - 12))

    d = ImageDraw.Draw(im)
    for item in doodles:
        kind, *args = item
        DOODLES[kind](d, *args, t, INK + (255,), max(4, int(min(size) * 0.01)))

    # headline writes on near the bottom (higher in wide so it clears the CTA)
    if headline:
        f = B.font("display", int(min(size) * 0.06))
        shown = max(1, int(len(headline) * min(1.0, t * 1.3)))
        txt = headline[:shown]
        tw = B.text_w(txt, f)
        hy = h - int(h * (0.14 if size[1] >= size[0] else 0.20))
        d.text(((w - tw) / 2, hy), txt, font=f, fill=ACCENT + (255,))
    return im


def _render_scene(spec, idx, name, size, seconds):
    """Render a scene's frames locally and encode a clip."""
    work = os.path.join(ads.TMP, f"{name}-{idx:02d}-doodle")
    os.makedirs(work, exist_ok=True)
    art = None
    if spec.get("plate"):
        art = BG.load(spec["plate"], size).convert("RGB")
    n = max(DOODLE_FPS, int(seconds * DOODLE_FPS))
    for k in range(n):
        t = k / (n - 1)
        frame = _scene_frame(size, art, spec.get("doodles", []),
                             spec.get("headline", ""), t, k)
        frame.save(os.path.join(work, f"f{k:04d}.png"))
    clip = os.path.join(ads.TMP, f"{name}-{idx:02d}-doodle.mp4")
    subprocess.run(
        [ads.FFMPEG, "-y", "-framerate", str(DOODLE_FPS),
         "-i", os.path.join(work, "f%04d.png"),
         "-vf", f"scale={size[0]}:{size[1]},setsar=1",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), clip],
        capture_output=True, text=True, check=True)
    for k in range(n):
        os.remove(os.path.join(work, f"f{k:04d}.png"))
    os.rmdir(work)
    return clip


def build(name, cfg):
    """cfg: { size, target, out, scenes:[{vo, plate?, headline?, doodles?, end?}] }."""
    scenes = cfg["scenes"]
    size = cfg["size"]
    print(f"\n=== doodle {name}  {size[0]}x{size[1]}  {len(scenes)} scenes ===")

    vo_paths, vo_dur = EA.synthesize_voice(scenes, name)

    clips = []
    for i, sc in enumerate(scenes):
        if sc.get("end"):
            clips.append(_end_card_clip(name, cfg, i))
            print(f"  scene {i + 1:02d} end-card")
            continue
        seconds = max(2.5, vo_dur[i] + 1.0)
        clips.append(_render_scene(sc, i + 1, name, size, seconds))
        print(f"  scene {i + 1:02d} doodled ({seconds:.1f}s)")

    return EA.build(name, {**cfg, "_style": "doodle",
                           "_vo_paths": vo_paths, "_vo_dur": vo_dur}, clips)


def _end_card_clip(name, cfg, idx):
    im = ads.end_card(cfg["size"])
    still = os.path.join(ads.TMP, f"{name}-{idx:02d}-endcard.jpg")
    im.save(still, quality=93)
    clip = os.path.join(ads.TMP, f"{name}-{idx:02d}-endcard.mp4")
    subprocess.run(
        [ads.FFMPEG, "-y", "-loop", "1", "-t", "4", "-i", still,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), clip],
        capture_output=True, text=True, check=True)
    return clip
