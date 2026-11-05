"""Shared assembly for the creative engine.

Timing model (one source of truth): voice-over sets the pace. Each scene is as
long as its spoken line plus a little slack; scenes cross-fade on the output
timeline; if a `target` duration is set, the slack is solved so the whole cut
lands on it (floor = the cross-fade, so two voices never overlap). This is the
same math the live-action ads use.

The generative styles (cartoon / doodle / presenter) each hand us a local mp4
per scene, already sized; we add voice, captions, logo/CTA/end-card and the
-13 LUFS master via the existing ads.py compositor.

Scene dict: {"vo": "spoken line", "end": False}
"""
import os

import brand as B
import ads
import engine_runtime as R

OUT_VID = ads.OUT_VID
TMP = ads.TMP
XFADE = ads.XFADE

# default score per style, ducked well under the voice. MusicGen on our T4 box;
# a None/off value ships VO-only, and any music failure degrades to VO-only
# rather than blocking the render.
MUSIC = {
    "cartoon": dict(prompt="upbeat minimal corporate explainer bed, light "
                           "marimba and soft synth pulse, no vocals, loopable",
                    level=0.16),
    "doodle": dict(prompt="gentle acoustic whiteboard explainer bed, soft "
                          "ukulele and light percussion, no vocals, loopable",
                   level=0.15),
    "presenter": dict(prompt="confident corporate underscore, subtle piano and "
                             "warm pad, no vocals, loopable",
                      level=0.12),
}


def _music_bed(cfg, name, seconds):
    """Fetch a MusicGen score for the whole cut, trimmed to length, ducked.

    Returns a local wav path or None. Never raises -- a music failure must not
    block a render.
    """
    spec = cfg.get("music", "__auto__")
    style = cfg.get("_style", "cartoon")
    if spec in (None, False, "off", "none"):
        return None
    if spec == "__auto__":
        spec = MUSIC.get(style, MUSIC["cartoon"])
    if isinstance(spec, str):
        spec = dict(prompt=spec, level=0.15)
    try:
        wav = os.path.join(TMP, f"{name}-music.wav")
        R.music(spec["prompt"], int(seconds) + 2, wav)
        print(f"  music {os.path.basename(wav)} ({spec['prompt'][:40]}...)")
        return wav, float(spec.get("level", 0.15))
    except Exception as e:                    # noqa: BLE001
        print(f"  music skipped ({str(e)[:80]})")
        return None


def synthesize_voice(scenes, name):
    """One TTS take per voiced scene (ads.tts = our house SAPI)."""
    vo_dir = os.path.join(B.ASSETS, "voiceover", name)
    os.makedirs(vo_dir, exist_ok=True)
    paths, durs = [], []
    for i, sc in enumerate(scenes):
        text = sc.get("vo", "")
        if text:
            p = os.path.join(vo_dir, f"scene-{i + 1:02d}.wav")
            durs.append(ads.tts(text, p))
            paths.append(p)
        else:
            durs.append(0.0)
            paths.append(None)
        print(f"  vo   scene-{i + 1:02d} {durs[-1]:.2f}s")
    return paths, durs


def _solve(vo_dur, cfg):
    """Scene durations, starts and total from the VO lengths + target."""
    n = len(vo_dur)
    target = cfg.get("target")
    if target and all(v > 0 for v in vo_dur):
        k = (target + (n - 1) * XFADE - sum(vo_dur)) / n
        k = max(k, XFADE)  # cross-fade floor: never clip/overlap a voice
        dd = [max(XFADE + 0.2, v + k) for v in vo_dur]
    else:
        dd = [max(3.0, v + 1.2) if v > 0 else 3.0 for v in vo_dur]
    starts = [0.0]
    for i in range(1, n):
        starts.append(sum(dd[:i]) - i * XFADE)
    return dd, starts, sum(dd) - (n - 1) * XFADE


def _captions(scenes, starts, dd, vo_dur):
    events = []
    for i, sc in enumerate(scenes):
        if sc.get("end") or not sc.get("vo"):
            continue
        bts = ads.beats(sc["vo"])
        if not bts:
            continue
        span_s = starts[i] + 0.12
        span_e = starts[i] + min(dd[i] - 0.10, vo_dur[i] + 1.2)
        if i + 1 < len(starts):
            nxt = scenes[i + 1]
            followed = bool(nxt.get("vo")) and not nxt.get("end") and \
                bool(ads.beats(nxt["vo"]))
            span_e = min(span_e, starts[i + 1] + (0.06 if followed else -0.06))
        span_e = max(span_e, span_s + 0.20)
        weights = [max(1, len(b)) for b in bts]
        tot = sum(weights)
        t = span_s
        for b, wt in zip(bts, weights):
            d = (span_e - span_s) * wt / tot
            events.append((t, t + d, b))
            t += d
    return events


def build(name, cfg, clips):
    """clips: [local mp4 per scene, already sized]. Synthesizes voice (or
    reuses cfg['_vo_paths']/cfg['_vo_dur'] when a style already made them),
    burns captions, overlays logo/CTA/end-card, masters, returns the path."""
    size = cfg["size"]
    scenes = cfg["scenes"]

    if cfg.get("_vo_paths") and cfg.get("_vo_dur"):
        vo_paths, vo_dur = cfg["_vo_paths"], cfg["_vo_dur"]
    else:
        vo_paths, vo_dur = synthesize_voice(scenes, name)
    dd, starts, total = _solve(vo_dur, cfg)

    # stretch/trim every clip to its scene window (looping short gens) so each
    # visual matches the VO-driven length the compositor expects
    fitted = [_fit(clip, dd[i], size, f"{name}-{i + 1:02d}")
              for i, clip in enumerate(clips)]

    events = _captions(scenes, starts, dd, vo_dur)
    os.makedirs(TMP, exist_ok=True)
    ass = os.path.join(TMP, f"{name}.ass")
    ads.write_ass(ass, size, events)
    print(f"  ass  {len(events)} caption beats")

    logo, _ = ads.logo_png(size, os.path.join(TMP, f"{name}-logo.png"))
    cta, _ = ads.cta_png(size, os.path.join(TMP, f"{name}-cta.png"))
    end_idx = next((i for i, s in enumerate(scenes) if s.get("end")), None)
    ec_start = starts[end_idx] if end_idx is not None else total
    cta_from = max(0.0, ec_start - 4.2)
    cta_y = int(size[1] * (0.745 if size[1] > size[0] else 0.845))

    voiced = [(p, s) for p, s in zip(vo_paths, starts) if p]
    os.makedirs(OUT_VID, exist_ok=True)
    out = os.path.join(OUT_VID, cfg["out"])
    raw = os.path.join(TMP, f"{name}-raw.mp4")
    ads.assemble(fitted, voiced, starts, total, raw, ass, logo, cta,
                 ec_start, cta_from, ec_start, cta_y, size,
                 cfg.get("white_at", -1))

    # music bed, ducked under the voice (second pass, pre-master)
    bed = _music_bed(cfg, name, total)
    if bed:
        raw = _duck_music(raw, bed, name)

    mb = ads.master(raw, out)
    loud = ads.loudness(out)
    extra = f"  crest {mb['crest']}dB" if mb else ""
    extra += "  +music" if bed else ""
    print(f"  -> {out}  {total:.2f}s  loudness "
          f"{loud if loud is None else round(loud, 1)} LUFS{extra}")
    return out


def _duck_music(raw, bed, name):
    """Mix a MusicGen score under the voice: bed at `level`, VO untouched, with
    a short fade-out on the tail. Returns the new raw path (music pass)."""
    import subprocess
    wav, level = bed
    out = os.path.join(TMP, f"{name}-raw-music.mp4")
    subprocess.run(
        [ads.FFMPEG, "-y", "-i", raw, "-i", wav,
         "-filter_complex",
         f"[1:a]volume={level},afade=t=out:st=0:d=0[m];"
         f"[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", out],
        capture_output=True, text=True, check=True)
    return out


def _fit(clip, seconds, size, tag):
    """Loop/trim a clip to exactly `seconds`, scaled to `size`."""
    import subprocess
    out = os.path.join(TMP, f"{tag}-fit.mp4")
    subprocess.run(
        [ads.FFMPEG, "-y", "-stream_loop", "-1", "-i", clip,
         "-vf", f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=increase,"
                f"crop={size[0]}:{size[1]},setsar=1",
         "-t", f"{seconds:.2f}", "-r", str(ads.FPS), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
        capture_output=True, text=True, check=True)
    return out
