"""Marketing Studio bridge — JSON in / JSON out, reuses the campaign compositor.

    python studio.py catalog
    python studio.py poster  --spec spec.json
    python studio.py poster  --slug launch --formats feed,story
    python studio.py video   --spec spec.json

stdout carries one JSON document; the renderers' own progress lines are
captured into the returned `log` so the API can stream them back.
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backgrounds  # noqa: E402
import poster_specs  # noqa: E402
import posters  # noqa: E402
import videos  # noqa: E402
import ads  # noqa: E402
import engine_runtime  # noqa: E402

ASSETS = os.path.abspath(os.path.join(posters.OUT, ".."))
CUSTOM_DIR = os.path.join(posters.OUT, "custom")
VIDEO_DIR = videos.OUT_VID

BODY_KINDS = {
    "signal": {"label": "Live signal ticket", "fields": {}},
    "chips": {"label": "Chips row", "fields": {
        "chips": {"type": "text[]", "max": 12},
        "chip_size": {"type": "int", "optional": True},
    }},
    "bullets": {"label": "Bullets", "fields": {
        "items": {"type": "text[]", "max": 5},
    }},
    "stats": {"label": "Stat row", "fields": {
        "stats": {"type": "[[value, label]]", "max": 4},
    }},
    "tiers": {"label": "Pricing tiers", "fields": {
        "tiers": {"type": "[{name, price, lines[], featured?}]", "max": 4},
    }},
    "platforms": {"label": "Platform grid", "fields": {
        "platforms": {"type": "[{name, meta}]", "max": 6},
    }},
    "agents": {"label": "Agent quorum", "fields": {
        "agents": {"type": "[[name, vote, reason]]", "max": 5},
    }},
    "notify": {"label": "Notification rows", "fields": {
        "items": {"type": "[[glyph, title, meta]]", "max": 5},
    }},
}


def _slug(s, fallback="custom"):
    s = re.sub(r"[^a-z0-9-]+", "-", str(s or "").lower()).strip("-")
    return (s or fallback)[:48]


def _list_plates():
    d = os.path.join(ASSETS, "backgrounds")
    if not os.path.isdir(d):
        return []
    return sorted({os.path.splitext(f)[0] for f in os.listdir(d)
                   if f.lower().endswith(".jpg")})


def _fmt_size(fmt):
    w, h = posters.FORMATS.get(fmt, posters.FORMATS["feed"])
    return [w, h]


def catalog():
    return {
        "formats": {k: _fmt_size(k) for k in posters.FORMATS},
        "plates": _list_plates(),
        "body_kinds": BODY_KINDS,
        "posters": [
            {
                "slug": slug,
                "plate": s["plate"],
                "eyebrow": s.get("eyebrow", ""),
                "headline": s.get("headline", ""),
                "sub": s.get("sub", ""),
                "body": s.get("body"),
                "cta": s.get("cta", ""),
                "hsize": s.get("hsize", 100),
                "formats": s.get("formats", ["feed"]),
                "body_well": bool(s.get("body_well")),
                "scrim_top": s.get("scrim_top"),
                "scrim_bottom": s.get("scrim_bottom"),
            }
            for slug, s in sorted(poster_specs.POSTERS.items())
        ],
        "video_spots": [
            {
                "name": name,
                "kind": "campaign",
                "size": list(cfg["size"]),
                "target": cfg.get("target"),
                "out": cfg["out"],
                "scenes": len(cfg.get("scenes")
                                or videos.SPOTS[cfg["reuse"]]["scenes"]),
                "voiced": sum(1 for sc in (cfg.get("scenes")
                                           or videos.SPOTS[cfg["reuse"]]["scenes"])
                              if sc.get("vo")),
                "reuse": cfg.get("reuse"),
            }
            for name, cfg in sorted(videos.SPOTS.items())
        ] + [
            {
                "name": name,
                "kind": "ad",
                "size": list(cfg["size"]),
                "target": cfg.get("target"),
                "out": cfg["out"],
                "scenes": len(cfg["scenes"]),
                "voiced": sum(1 for sc in cfg["scenes"] if sc.get("vo")),
                "reuse": None,
            }
            for name, cfg in sorted(ads.SPOTS.items())
        ],
        "brand": {
            "gold": getattr(posters.B, "GOLD", (212, 175, 55)),
            "dark": getattr(posters.B, "DARK", (10, 14, 39)),
            "cyan": getattr(posters.B, "CYAN", (0, 212, 255)),
            "purple": getattr(posters.B, "PURPLE", (124, 58, 237)),
        },
        "voices": [
            {"id": videos.VOICE, "label": "David — male, house default"},
            {"id": "Microsoft Zira Desktop", "label": "Zira — female"},
            {"id": "Microsoft Hazel Desktop", "label": "Hazel — female, UK"},
            {"id": "Microsoft Mark Desktop", "label": "Mark — male, AU"},
        ],
        "plate_ratios": ["16:9", "9:16", "4:5", "1:1"],
        "plate_styles": ["campaign", "ads"],
        "creative_styles": ["cartoon", "doodle", "presenter"],
        "url2video": True,
        "music_bed": True,
        "creative_gpu": {"instance": engine_runtime.GPU_INSTANCE,
                         "region": engine_runtime.REGION},
        "paths": {
            "posters": os.path.relpath(posters.OUT, ASSETS),
            "videos": os.path.relpath(VIDEO_DIR, ASSETS),
            "backgrounds": "backgrounds",
            "storyboards": "storyboards",
            "voiceover": "voiceover",
        },
        "python": sys.executable,
    }


def _render_poster(spec, fmt):
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    stamp = spec.get("_stamp") or time.strftime("%Y%m%d-%H%M%S")
    name = f"priv-{_slug(spec.get('slug'), 'custom')}-{stamp}-{fmt}.jpg"
    out = os.path.join(CUSTOM_DIR, name)
    posters.render(spec, fmt, out)
    w, h = _fmt_size(fmt)
    return {
        "format": fmt,
        "width": w,
        "height": h,
        "file": os.path.basename(out),
        "rel": os.path.relpath(out, ASSETS).replace("\\", "/"),
        "url": "/marketing-assets/" + os.path.relpath(out, ASSETS).replace("\\", "/"),
    }


def _normalise_body(body):
    """posters.render() expects tuples where the JSON carries lists."""
    if not isinstance(body, dict):
        return body
    kind = body.get("kind")
    out = dict(body)
    if kind == "stats":
        out["stats"] = [tuple(x) for x in body.get("stats", [])]
    elif kind == "agents":
        out["agents"] = [tuple(x) for x in body.get("agents", [])]
    elif kind == "notify":
        out["items"] = [tuple(x) for x in body.get("items", [])]
    elif kind == "tiers":
        out["tiers"] = [
            {**t, "lines": list(t.get("lines", []))} for t in body.get("tiers", [])
        ]
    elif kind == "platforms":
        out["platforms"] = [
            dict(p) for p in body.get("platforms", [])
        ]
    elif kind in ("chips", "bullets"):
        out["items" if kind == "bullets" else "chips"] = list(
            body.get("items" if kind == "bullets" else "chips", [])
        )
    return out


def render_poster(spec):
    if not isinstance(spec, dict):
        raise SystemExit("spec must be a JSON object")
    base = {}
    slug = spec.get("template") or spec.get("slug")
    if spec.get("template") and spec["template"] in poster_specs.POSTERS:
        base = dict(poster_specs.POSTERS[spec["template"]])
        slug = spec["template"]
    merged = {**base, **{k: v for k, v in spec.items() if k != "template"}}
    merged["slug"] = _slug(slug, "custom")
    merged["_stamp"] = time.strftime("%Y%m%d-%H%M%S")
    if not merged.get("headline"):
        raise SystemExit("headline is required")
    if not merged.get("plate"):
        raise SystemExit("plate is required")
    if not merged.get("formats"):
        merged["formats"] = ["feed"]
    if isinstance(merged.get("body"), dict):
        merged["body"] = _normalise_body(merged["body"])
    for k, v in list(merged.items()):
        if k.startswith("body_") and isinstance(v, dict) and v.get("kind"):
            merged[k] = _normalise_body(v)

    files, log = [], io.StringIO()
    with contextlib.redirect_stdout(log):
        for fmt in merged["formats"]:
            if fmt not in posters.FORMATS:
                raise SystemExit(f"unknown format: {fmt}")
            files.append(_render_poster(merged, fmt))
    return {"files": files, "log": log.getvalue().splitlines()}


def rerender_posters(slugs=None):
    made, log = [], io.StringIO()
    slugs = slugs or list(poster_specs.POSTERS)
    with contextlib.redirect_stdout(log):
        for slug in slugs:
            if slug not in poster_specs.POSTERS:
                raise SystemExit(f"unknown poster: {slug}")
            spec = poster_specs.POSTERS[slug]
            for fmt in spec["formats"]:
                out = os.path.join(posters.OUT, fmt, f"priv-{slug}-{fmt}.jpg")
                posters.render(spec, fmt, out)
                made.append({
                    "slug": slug,
                    "format": fmt,
                    "rel": os.path.relpath(out, ASSETS).replace("\\", "/"),
                    "url": "/marketing-assets/" + os.path.relpath(out, ASSETS).replace("\\", "/"),
                })
    return {"made": made, "log": log.getvalue().splitlines()}


def render_video(spec):
    if not isinstance(spec, dict):
        raise SystemExit("spec must be a JSON object")
    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise SystemExit("scenes[] is required")
    name = _slug(spec.get("name"), "custom-video")
    size = spec.get("size") or [1080, 1920]
    if isinstance(size, str):
        w, h = size.lower().split("x")
        size = [int(w), int(h)]
    cfg = {
        "size": [int(size[0]), int(size[1])],
        "fmt": spec.get("fmt") or ("wide" if int(size[0]) >= int(size[1]) else "story"),
        "margin": float(spec.get("margin", videos.MARGIN)),
        "target": spec.get("target"),
        "out": f"priv-{name}-{size[0]}x{size[1]}.mp4",
        "scenes": [],
    }
    for i, sc in enumerate(scenes, 1):
        if not isinstance(sc, dict) or not sc.get("plate"):
            raise SystemExit(f"scene {i} needs a plate")
        scene = {
            "plate": sc["plate"],
            "eyebrow": sc.get("eyebrow", ""),
            "headline": sc.get("headline", ""),
            "sub": sc.get("sub", ""),
        }
        if sc.get("body"):
            scene["body"] = _normalise_body(sc["body"])
        if sc.get("vo"):
            scene["vo"] = sc["vo"]
        if sc.get("hold"):
            scene["hold"] = float(sc["hold"])
        cfg["scenes"].append(scene)

    log = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(log):
        videos.build(name, cfg)
    out_path = os.path.join(VIDEO_DIR, cfg["out"])
    return {
        "name": name,
        "out": cfg["out"],
        "file": cfg["out"],
        "rel": os.path.relpath(out_path, ASSETS).replace("\\", "/"),
        "url": "/marketing-assets/" + os.path.relpath(out_path, ASSETS).replace("\\", "/"),
        "seconds": round(time.time() - t0, 1),
        "exists": os.path.exists(out_path),
        "log": log.getvalue().splitlines(),
    }


def _rel_url(path):
    rel = os.path.relpath(path, ASSETS).replace("\\", "/")
    return rel, "/marketing-assets/" + rel


def _sapi(text, out_wav, voice, rate):
    """One SAPI synthesis pass (the house TTS — same engine the ads used)."""
    txt = out_wav + ".txt"
    with open(txt, "w", encoding="ascii", errors="replace") as f:
        f.write(text)
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", videos.TTS_PS1, "-InFile", txt, "-Out", out_wav,
         "-Voice", voice, "-Rate", str(rate)],
        capture_output=True, text=True)
    if not os.path.exists(out_wav):
        raise SystemExit(f"TTS failed: {r.stdout}\n{r.stderr}")
    with wave.open(out_wav) as w:
        return w.getnframes() / float(w.getframerate())


def _encode_m4a(src, dst):
    r = subprocess.run(
        [videos.FFMPEG, "-y", "-i", src, "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-ac", "2", dst],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst):
        raise SystemExit(f"m4a encode failed: {r.stderr[-400:]}")


def engine_tts(spec):
    """Voice Lab: synthesize text with the local SAPI engine.

    spec: { text, voice?, rate?, spot?, scene?, install?:{spot, scene} }
    Drafts land in voiceover/generated/; install:true writes the take the
    compositor actually uses (voiceover/<spot>/scene-NN.m4a), so a Studio
    voice line can replace a recorded take per scene.
    """
    text = str(spec.get("text") or "").strip()
    if not text:
        raise SystemExit("text is required")
    voice = str(spec.get("voice") or videos.VOICE)
    rate = int(spec.get("rate", videos.RATE))
    scene = max(1, int(spec.get("scene") or 1))
    spot = _slug(spec.get("spot"), "generated")
    install = spec.get("install") if isinstance(spec.get("install"), dict) else None
    stamp = time.strftime("%Y%m%d-%H%M%S")

    gen_dir = os.path.join(ASSETS, "voiceover", "generated")
    os.makedirs(gen_dir, exist_ok=True)
    wav = os.path.join(gen_dir, f"{spot}-scene-{scene:02d}-{stamp}.wav")
    seconds = _sapi(text, wav, voice, rate)
    m4a = wav[:-4] + ".m4a"
    _encode_m4a(wav, m4a)

    wav_rel, wav_url = _rel_url(wav)
    m4a_rel, m4a_url = _rel_url(m4a)
    out = {
        "seconds": round(seconds, 2),
        "voice": voice,
        "rate": rate,
        "text": text,
        "wav": {"rel": wav_rel, "url": wav_url},
        "m4a": {"rel": m4a_rel, "url": m4a_url},
        "installed": None,
    }
    if install:
        i_spot = _slug(install.get("spot"), spot)
        i_scene = max(1, int(install.get("scene") or scene))
        vo_dir = os.path.join(ASSETS, "voiceover", i_spot)
        os.makedirs(vo_dir, exist_ok=True)
        take = os.path.join(vo_dir, f"scene-{i_scene:02d}.m4a")
        shutil.copyfile(m4a, take)
        take_rel, take_url = _rel_url(take)
        out["installed"] = {"spot": i_spot, "scene": i_scene,
                            "rel": take_rel, "url": take_url}
    return out


def engine_plate(spec):
    """Plate Foundry: one ad-hoc background plate.

    spec: { prompt, ratio?, slug?, style? } where style is "campaign" |
    "ads" | a raw style string. Uses Amazon Bedrock Stable Image Ultra
    (the same model the 26 campaign plates came from); falls back to the
    procedural brand gradient when Bedrock is unreachable.
    """
    prompt = str(spec.get("prompt") or "").strip()
    if not prompt:
        raise SystemExit("prompt is required")
    ratio = str(spec.get("ratio") or "9:16")
    style_in = spec.get("style")
    if style_in in (None, "", "campaign"):
        style = backgrounds.STYLE
    elif style_in == "ads":
        style = backgrounds.STYLE_ADS
    else:
        style = str(style_in)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = f"gen-{_slug(spec.get('slug'), 'plate')}-{stamp}"

    log = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(log):
        path, provider = backgrounds.generate_one(
            prompt, ratio=ratio, name=name, style=style)
    rel, url = _rel_url(path)
    return {
        "name": name,
        "ratio": ratio,
        "provider": provider,
        "model": backgrounds.MODEL if provider == "bedrock" else "procedural",
        "rel": rel,
        "url": url,
        "seconds": round(time.time() - t0, 1),
        "exists": os.path.exists(path),
        "log": log.getvalue().splitlines(),
    }


def engine_creative(spec):
    """Creative engine: one 1-minute ad in cartoon / doodle / presenter style.

    spec: { style, name?, size?, target?, out?, seed?, scenes:[...] }
      - cartoon:   scenes carry {prompt, vo, end?}  -> AnimateDiff on the GPU
      - doodle:    scenes carry {vo, plate?, headline?, doodles?, end?} (local)
      - presenter: scenes carry {vo, end?}          -> MuseTalk on the GPU

    Everything is generated in-house (SD/AnimateDiff/MuseTalk on our A10G, the
    presenter face via Bedrock), then assembled by the house compositor into a
    -13 LUFS master in assets/videos/. Presenter masters are stamped with an
    AI-disclosure line for the platform label.
    """
    style = _slug(spec.get("style"), "")
    if style not in ("cartoon", "doodle", "presenter"):
        raise SystemExit("style must be cartoon | doodle | presenter")
    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise SystemExit("scenes[] is required")
    name = _slug(spec.get("name"), f"{style}-ad")
    size = spec.get("size") or [1080, 1920]
    if isinstance(size, str):
        w, h = size.lower().split("x")
        size = [int(w), int(h)]
    cfg = {
        "size": [int(size[0]), int(size[1])],
        "target": spec.get("target") if spec.get("target") is not None else 60,
        "out": spec.get("out") or f"priv-{name}-{size[0]}x{size[1]}.mp4",
        "seed": spec.get("seed"),
        "scenes": scenes,
    }
    if spec.get("white_at") is not None:
        cfg["white_at"] = int(spec["white_at"])

    import importlib
    mod = importlib.import_module(style)
    log = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(log):
        out_path = mod.build(name, cfg)
    rel, url = _rel_url(out_path)
    return {
        "style": style,
        "name": name,
        "out": os.path.basename(out_path),
        "rel": rel,
        "url": url,
        "size": cfg["size"],
        "target": cfg["target"],
        "seconds": round(time.time() - t0, 1),
        "exists": os.path.exists(out_path),
        "disclosure": (style == "presenter"),
        "log": log.getvalue().splitlines(),
    }


def engine_urlbrief(spec):
    """URL-to-video step 1: fetch a page and return its creative brief as JSON.

    spec: { url } -> { url, title, description, text, prices }. The API layer
    drafts the scene script from this brief (it holds the AI client), then
    hands scenes to the creative engine.
    """
    url = str(spec.get("url") or "").strip()
    if not url:
        raise SystemExit("url is required")
    import url2video
    return url2video.fetch_page(url)


def engine_image(spec):
    """Image / product-photo suite (Bedrock edit models).

    spec: { op, ... } where op is remove_background | inpaint | outpaint |
    erase_object | style_transfer | generate | product_shot. `image`/`mask`
    are asset-relative paths or absolute paths.
    """
    import image_studio

    def _resolve(p):
        if not p:
            return p
        if os.path.isabs(p) and os.path.exists(p):
            return p
        cand = os.path.join(ASSETS, str(p).lstrip("/").replace("marketing-assets/", ""))
        return cand if os.path.exists(cand) else p

    spec = dict(spec)
    for k in ("image", "mask"):
        if spec.get(k):
            spec[k] = _resolve(spec[k])
    return image_studio.run(spec)


def engine_voice_clone(spec):
    """Voice cloning: spec { path: client|inhouse, text, ref, consent, name? }.
    client = Chatterbox (MIT, client-facing); inhouse = XTTS v2 (NON-COMMERCIAL
    internal only). consent (who consented) is mandatory.
    """
    import voice_clone
    ref = spec.get("ref")
    if ref and not os.path.isabs(ref):
        cand = os.path.join(ASSETS, str(ref).lstrip("/").replace("marketing-assets/", ""))
        if os.path.exists(cand):
            spec = {**spec, "ref": cand}
    return voice_clone.run(spec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command",
                    choices=["catalog", "poster", "video", "tts", "plate",
                             "creative", "urlbrief", "image", "voiceclone"])
    ap.add_argument("--spec", help="path to a JSON spec")
    ap.add_argument("--slug", help="poster slug to re-render")
    ap.add_argument("--formats", help="comma-separated formats")
    args = ap.parse_args()

    if args.command == "catalog":
        payload = catalog()
    elif args.command == "urlbrief":
        payload = engine_urlbrief(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "image":
        payload = engine_image(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "voiceclone":
        payload = engine_voice_clone(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "poster":
        if args.slug:
            formats = [f.strip() for f in (args.formats or "").split(",") if f.strip()]
            spec = dict(poster_specs.POSTERS[args.slug])
            spec["slug"] = args.slug
            spec["formats"] = formats or spec.get("formats", ["feed"])
            spec["_stamp"] = time.strftime("%Y%m%d-%H%M%S")
            if isinstance(spec.get("body"), dict):
                spec["body"] = _normalise_body(spec["body"])
            files, log = [], io.StringIO()
            with contextlib.redirect_stdout(log):
                for fmt in spec["formats"]:
                    files.append(_render_poster(spec, fmt))
            payload = {"files": files, "log": log.getvalue().splitlines()}
        else:
            payload = render_poster(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "tts":
        payload = engine_tts(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "plate":
        payload = engine_plate(json.load(open(args.spec, encoding="utf-8-sig")))
    elif args.command == "creative":
        payload = engine_creative(json.load(open(args.spec, encoding="utf-8-sig")))
    else:
        payload = render_video(json.load(open(args.spec, encoding="utf-8-sig")))
    json.dump(payload, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
