"""Generate campaign background plates with Amazon Bedrock (Stable Image Ultra).

Re-runnable: existing files are skipped. Falls back to a procedural gradient
plate if Bedrock is unavailable, so the rest of the pipeline never blocks.
"""
import base64
import json
import os
import time

from PIL import Image, ImageOps

import brand as B

OUT = os.path.join(B.ASSETS, "backgrounds")
MODEL = "stability.stable-image-ultra-v1:1"
REGION = "us-west-2"

STYLE = (
    "premium fintech advertising key art, deep midnight-navy atmosphere with "
    "metallic gold and cool cyan highlights, volumetric light, cinematic depth of field, "
    "clean negative space for headline type, high-end editorial photography, "
    "absolutely no text, no letters, no numbers, no logos, no watermark"
)

MANIFEST = [
    # --- 16:9 landscape (hero/explainer video plates) ---
    ("ls-trading-floor", "16:9",
     "vast dark trading floor at night seen from behind a single silhouetted figure, "
     "wall of abstract glowing candlestick charts in metallic gold"),
    ("ls-gold-charts", "16:9",
     "macro shot of a translucent glass panel with a rising gold candlestick chart "
     "floating above a dark reflective desk, bokeh city lights behind"),
    ("ls-city-night", "16:9",
     "aerial view of a financial district skyline at blue hour, gold window lights, "
     "faint holographic market grid projected over the buildings"),
    ("ls-particle-flow", "16:9",
     "abstract field of gold particles and thin cyan data streams flowing left to right "
     "over a dark navy void, long exposure light trails"),
    ("ls-vault", "16:9",
     "interior of a futuristic private vault corridor, brushed dark metal and gold inlay "
     "strips, soft cyan floor lighting, one point perspective"),
    # --- 9:16 vertical (short-form video plates) ---
    ("vt-candle-wall", "9:16",
     "towering wall of abstract glowing candlestick bars in gold and cyan seen from below, "
     "dark navy haze, dramatic upward perspective"),
    ("vt-holo-signal", "9:16",
     "a hand reaching toward a floating holographic trading signal ticket made of gold light "
     "in a dark room, cyan rim light, shallow depth of field"),
    ("vt-desk", "9:16",
     "a minimal dark desk at night with a single monitor glow reflecting gold charts, "
     "window showing a rainy city, moody and quiet"),
    ("vt-particles", "9:16",
     "vertical cascade of gold dust particles and thin cyan light streaks over deep navy, "
     "abstract, luxurious"),
    ("vt-vault-door", "9:16",
     "a circular brushed-metal vault door with gold concentric rings glowing softly, "
     "dark navy room, cinematic key light from the left"),
    # --- 4:5 portrait (feed posters) ---
    ("ps-trading-floor", "4:5",
     "cinematic dark trading floor with an out-of-focus wall of gold market charts, "
     "a single silhouette walking, deep navy tones"),
    ("ps-gold-abstract", "4:5",
     "abstract sculpture of interlocking gold ribbons and rings floating in a dark navy void, "
     "cyan edge lighting, luxury product photography"),
    ("ps-holo-chart", "4:5",
     "a translucent holographic candlestick chart projecting upward from a dark surface, "
     "gold and cyan glow, dust motes in the beam"),
    ("ps-skyline", "4:5",
     "low angle view of glass financial towers at night with gold lit windows and a faint "
     "holographic ticker grid in the sky"),
    ("ps-security", "4:5",
     "close up of a dark metal security keycard-sized object with fine gold engraving lines "
     "resting on black stone, cyan reflection, macro luxury shot"),
    ("ps-devices", "4:5",
     "three dark blank rectangular devices of different sizes arranged on a navy surface "
     "with gold rim light and soft cyan glow, product photography, screens off"),
    ("ps-strategy", "4:5",
     "an overhead flat lay of a dark desk with blank paper charts, a gold pen and a "
     "compass drawn in light on the surface, navy background"),
    ("ps-launch", "4:5",
     "a single gold light beam breaking upward through dark navy cloud layers, "
     "epic scale, subtle cyan stars"),
]


def _procedural(w, h, seed):
    im = B.gradient_bg(w, h)
    im = im.convert("RGB")
    from PIL import ImageDraw

    d = ImageDraw.Draw(im)
    B.draw_candles(d, [w * 0.06, h * 0.35, w * 0.94, h * 0.92], seed=seed, n=34)
    im = B.radial_glow(im.convert("RGBA"), (w // 2, int(h * 0.42)), int(min(w, h) * 0.7),
                       B.GOLD, 0.5).convert("RGB")
    return im


def generate(force=False, only=None):
    return _generate(MANIFEST, STYLE, 1000, force=force, only=only)


def _size_for(ratio):
    return {"16:9": (1920, 1080), "9:16": (1080, 1920), "4:5": (1080, 1350),
            "1:1": (1080, 1080)}[ratio]


def load(name, size):
    """Load a plate, cover-crop and upscale to `size`."""
    path = os.path.join(OUT, name + ".jpg")
    if not os.path.exists(path):
        im = _procedural(size[0], size[1], seed=abs(hash(name)) % 9999).convert("RGB")
        return im
    im = Image.open(path).convert("RGB")
    return ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.45))


STYLE_ADS = (
    "cinematic advertising key art, night apartment desk scene lit by hot magenta "
    "and pink neon rim light, warm golden city bokeh through a window, matte black "
    "hardware, moody low-key exposure, shallow depth of field, 35mm photography, "
    "clean space at the top for caption type, absolutely no text, no letters, no "
    "numbers, no logos, no watermark"
)

MANIFEST_ADS = [
    # --- 9:16 vertical (short-form ad plates) ---
    ("vt-neon-desk", "9:16",
     "an open matte black laptop on a dark wooden desk at night, screen glowing with "
     "an abstract dark trading dashboard of green and red bars, a smartphone and a "
     "ceramic mug beside it, plant silhouette and city lights behind"),
    ("vt-neon-desk-hands", "9:16",
     "over the shoulder view of hands resting near the trackpad of a matte black "
     "laptop on a night desk, screen glowing with an abstract dark analytics grid, "
     "magenta neon light spilling across the desk"),
    ("vt-neon-window", "9:16",
     "a night window view of a dense city with golden and magenta bokeh, a plant leaf "
     "in the dark foreground, soft neon reflections on the glass"),
    ("vt-neon-phone", "9:16",
     "a smartphone lying on a dark desk at night glowing with an abstract list of "
     "green and red data rows, laptop keyboard bokeh behind it, hot pink neon rim light"),
    ("vt-neon-macro", "9:16",
     "macro shot of a matte black laptop hinge and keyboard edge at night, tiny green "
     "and amber status LEDs, out of focus neon city behind, very shallow focus"),
    ("vt-neon-coffee", "9:16",
     "a dark ceramic mug steaming on a night desk with a glowing laptop screen far "
     "out of focus behind it, magenta neon glow on the rim of the mug"),
    # --- 16:9 landscape (hero / landing) ---
    ("ls-neon-desk", "16:9",
     "wide cinematic shot of a night desk with an open matte black laptop glowing "
     "with an abstract dark trading dashboard, city bokeh window behind, magenta neon "
     "rim light, coffee mug and phone on the desk"),
    ("ls-neon-window", "16:9",
     "wide night window of a city apartment, golden and magenta bokeh skyline, dark "
     "plant silhouette in the foreground, moody neon ambience"),
]


def _generate(manifest, style, seed_base, force=False, only=None):
    os.makedirs(OUT, exist_ok=True)
    client = None
    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=REGION)
    except Exception as e:  # pragma: no cover
        print("bedrock client unavailable:", e)

    made, failed = [], []
    for i, (name, ratio, prompt) in enumerate(manifest):
        if only and name not in only:
            continue
        path = os.path.join(OUT, name + ".jpg")
        if os.path.exists(path) and not force:
            continue
        if client is None:
            w, h = _size_for(ratio)
            _procedural(w, h, seed=i + 1).save(path, quality=92)
            made.append(name + " (procedural)")
            continue
        body = {
            "prompt": prompt + ", " + style,
            "negative_prompt": "text, letters, numbers, words, watermark, logo, signature, "
                               "lowres, jpeg artifacts, cluttered",
            "aspect_ratio": ratio,
            "output_format": "jpeg",
            "seed": seed_base + i * 17,
        }
        for attempt in range(4):
            try:
                t0 = time.time()
                r = client.invoke_model(
                    modelId=MODEL, contentType="application/json",
                    accept="application/json", body=json.dumps(body),
                )
                data = json.loads(r["body"].read())
                raw = base64.b64decode(data["images"][0])
                with open(path, "wb") as fh:
                    fh.write(raw)
                made.append(f"{name} ({time.time() - t0:.0f}s)")
                break
            except Exception as e:
                if attempt == 3:
                    failed.append(f"{name}: {e}")
                    w, h = _size_for(ratio)
                    _procedural(w, h, seed=i + 1).save(path, quality=92)
                    made.append(f"{name} (procedural fallback)")
                else:
                    time.sleep(4 * (attempt + 1))
    return made, failed


def generate_ads(force=False, only=None):
    """Generate the neon night-desk plates used by the caption-led ad engine."""
    return _generate(MANIFEST_ADS, STYLE_ADS, 500, force=force, only=only)


def generate_one(prompt, ratio="9:16", name=None, style=None, seed=None):
    """Marketing Studio: one ad-hoc plate from an arbitrary prompt.

    Writes backgrounds/<name>.jpg and returns (path, provider) where
    provider is "bedrock" or "procedural" (no Bedrock credentials).
    """
    import random

    os.makedirs(OUT, exist_ok=True)
    style = style or STYLE
    name = name or f"gen-{time.strftime('%Y%m%d-%H%M%S')}"
    path = os.path.join(OUT, name + ".jpg")
    body = {
        "prompt": f"{prompt}, {style}",
        "negative_prompt": "text, letters, numbers, words, watermark, logo, signature, "
                           "lowres, jpeg artifacts, cluttered",
        "aspect_ratio": ratio,
        "output_format": "jpeg",
        "seed": seed if seed is not None else random.randint(1, 2 ** 31 - 1),
    }
    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=REGION)
        r = client.invoke_model(
            modelId=MODEL, contentType="application/json",
            accept="application/json", body=json.dumps(body),
        )
        data = json.loads(r["body"].read())
        raw = base64.b64decode(data["images"][0])
        with open(path, "wb") as fh:
            fh.write(raw)
        return path, "bedrock"
    except Exception as e:
        print("plate generation fell back to procedural:", e)
        w, h = _size_for(ratio)
        _procedural(w, h, seed=body["seed"] % 9999).save(path, quality=92)
        return path, "procedural"


if __name__ == "__main__":
    made, failed = generate()
    print("generated:", len(made))
    for m in made:
        print("  -", m)
    for f in failed:
        print("  !", f)
