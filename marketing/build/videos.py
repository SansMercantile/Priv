"""Priv campaign video factory.

Renders one full-frame still per scene (also the storyboard), speaks each
scene's line with Windows SAPI, then assembles Ken Burns + cross-fade cuts
and a delayed voice-over track with ffmpeg.
"""
import os
import re
import shutil
import subprocess
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand as B  # noqa: E402
import posters  # noqa: E402

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
TTS_PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts.ps1")
FPS = 30
XFADE = 0.45          # cross-fade seconds
MARGIN = 1.8          # slack added to every voiced scene
MIN_DUR = 3.5
VOICE = "Microsoft David Desktop"
RATE = -1

OUT_VID = os.path.join(B.ASSETS, "videos")
OUT_VO = os.path.join(B.ASSETS, "voiceover")
OUT_SB = os.path.join(B.ASSETS, "storyboards")
TMP = os.path.join(B.ASSETS, ".frames")

SITE_SPEC = dict(eyebrow="PRIV — A SANS MERCANTILE PRODUCT",
                 headline="priv.sansmercantile.com",
                 sub="Signals, strategy testing, autonomous execution and full "
                     "custody — in one desk.",
                 cta="Start free — no card required",
                 hsize=104)

SPOTS = {
    "hero-30s": dict(
        size=(1920, 1080), fmt="wide", margin=1.6,
        out="priv-hero-30s-1920x1080.mp4",
        scenes=[
            dict(plate="ps-holo-chart", eyebrow="PRIV — LIVE SIGNAL FEED",
                 headline="Entry. Two targets. One stop.",
                 sub="Every setup ships complete: entry, TP1, TP2 and a stop "
                     "that trails to breakeven.",
                 body={"kind": "signal"}, hsize=96,
                 vo="Entry, two targets, one stop, read from the market."),
            dict(plate="ps-strategy", eyebrow="STRATEGY LAB",
                 headline="Prove it before you risk it.",
                 sub="Every strategy backtested on real candles — pinned "
                     "boards, run history, reproducible parameters.",
                 body={"kind": "stats", "stats": [("152", "backtest runs"),
                                                  ("45", "boards"),
                                                  ("7", "timeframes")]},
                 hsize=96, body_well=True, scrim_bottom=0.4,
                 vo="Every strategy is backtested on real candles first."),
            dict(plate="ps-trading-floor", eyebrow="AUTONOMOUS EXECUTION",
                 headline="Arm it. Sleep. Let the desk work.",
                 sub="A twenty-eight second decision cycle, audited every "
                     "run, fail-closed on credentials.",
                 body={"kind": "bullets", "items": [
                     "28-second decision cycle, audited every run",
                     "Tier-gated and fail-closed on credentials",
                     "Portfolio mode: positions, gross caps, drawdown brake"]},
                 hsize=96,
                 vo="Or arm the desk, and let it work while you sleep."),
            dict(plate="ps-security", eyebrow="CUSTODY & CONTROL",
                 headline="Your account. Your funds. Your control.",
                 sub="Priv connects to your own broker through official OAuth. "
                     "Funds never leave your broker.",
                 hsize=96,
                 vo="Your account, your funds, your control."),
            dict(plate="ps-gold-abstract", eyebrow="START FREE",
                 headline="One plan for every pace.",
                 sub="Free signals every day. Upgrade when the signals start "
                     "paying for themselves.",
                 body={"kind": "chips", "chips": ["Free", "$29 Pro", "$79 Elite",
                                                  "$149 Sovereign"]},
                 cta="priv.sansmercantile.com", hsize=96,
                 vo="Start free today. Priv, a Sans Mercantile product."),
        ]),
    "hero-30s-vertical": dict(
        size=(1080, 1920), fmt="story",
        out="priv-hero-30s-vertical-1080x1920.mp4",
        reuse="hero-30s"),
    "teaser-15s-vertical": dict(
        size=(1080, 1920), fmt="story",
        out="priv-teaser-15s-vertical-1080x1920.mp4",
        scenes=[
            dict(plate="vt-holo-signal", eyebrow="PRIV LIVE",
                 headline="Entry. Two targets. One stop.",
                 sub="The setup lands before you look.",
                 body={"kind": "signal"}, hsize=96,
                 vo="Entry, two targets, one stop."),
            dict(plate="vt-desk", eyebrow="AUTONOMOUS",
                 headline="Arm it. Sleep. Let the desk work.",
                 sub="A twenty-eight second decision cycle, fail-closed.",
                 hsize=96,
                 vo="Arm it, and let the desk work while you sleep."),
            dict(plate="vt-particles", eyebrow="START FREE",
                 headline="Your edge starts here.",
                 sub="priv.sansmercantile.com",
                 cta="Start free — no card required", hsize=104,
                 vo="Priv. Start free today."),
        ]),
    "explainer-60s": dict(
        size=(1920, 1080), fmt="wide", margin=2.2,
        out="priv-explainer-60s-1920x1080.mp4",
        scenes=[
            dict(plate="ps-launch", eyebrow="PRIV — A SANS MERCANTILE PRODUCT",
                 headline="Precision entries, read from the market.",
                 sub="Priv reads price action across indices, synthetics, "
                     "commodities and shares.",
                 body={"kind": "stats", "stats": [("45+", "strategy boards"),
                                                  ("7", "timeframes"),
                                                  ("24/7", "market watch")]},
                 hsize=92, body_well=True, scrim_bottom=0.4,
                 vo="This is Priv. Precision entries, read from the market, "
                    "not guessed at."),
            dict(plate="ps-holo-chart", eyebrow="LIVE SIGNAL FEED",
                 headline="Entry. Two targets. One stop.",
                 sub="A stop that trails to breakeven the moment the first "
                     "target prints.",
                 body={"kind": "signal"}, hsize=96,
                 vo="Every signal ships complete. Entry, two targets, and a "
                    "stop that moves to breakeven."),
            dict(plate="ps-gold-abstract", eyebrow="MULTI-TIMEFRAME READS",
                 headline="One market. Seven timeframes.",
                 sub="The same instrument read from one minute to one day — "
                     "divergent reads surfaced, not hidden.",
                 body={"kind": "chips",
                       "chips": ["1m", "5m", "15m", "30m", "1H", "4H", "1D"]},
                 hsize=96, body_well=True, scrim_bottom=0.4,
                 vo="Seven timeframes on every market, from one minute to one "
                    "day."),
            dict(plate="ps-strategy", eyebrow="STRATEGY LAB",
                 headline="Prove it before you risk it.",
                 sub="Pinned boards, run history and reproducible parameters.",
                 body={"kind": "stats", "stats": [("152", "backtest runs"),
                                                  ("45", "boards"),
                                                  ("7", "timeframes")]},
                 hsize=96, body_well=True, scrim_bottom=0.4,
                 vo="Prove it in the strategy lab before you risk a cent."),
            dict(plate="ps-trading-floor", eyebrow="MULTI-AGENT DESK",
                 headline="Five agents. One quorum.",
                 sub="Technical, quantitative, risk, compliance and ethical "
                     "agents deliberate before a single order moves.",
                 body={"kind": "agents", "agents": [
                     ("Technical agent", "BUY", "+2 confirmations · trend"),
                     ("Quantitative agent", "BUY", "ATR bands · reversion"),
                     ("Risk agent", "HOLD", "exposure cap clear")]},
                 hsize=96,
                 vo="Five agents deliberate on every order before it moves."),
            dict(plate="ps-devices", eyebrow="EVERY SCREEN YOU OWN",
                 headline="Your signals, on every screen you own.",
                 sub="One account, one live feed — from a full desk setup to "
                     "your pocket.",
                 body={"kind": "platforms", "platforms": [
                     {"name": "Web", "meta": "no install"},
                     {"name": "Windows", "meta": "91 MB"},
                     {"name": "macOS", "meta": "177 MB"},
                     {"name": "Android", "meta": "221 KB"},
                     {"name": "iOS", "meta": "home screen"},
                     {"name": "Linux", "meta": "107 MB"}]},
                 hsize=92, body_well=True, scrim_bottom=0.4,
                 vo="Web, desktop and mobile. One account, every screen."),
            dict(plate="ps-security", eyebrow="CUSTODY & CONTROL",
                 headline="Your account. Your funds. Your control.",
                 sub="Official OAuth to your own broker. Credentials fail "
                     "closed — never shared, never stored in the clear.",
                 hsize=96,
                 vo="And it stays yours. Your account, your funds, your "
                    "control."),
            dict(plate="ps-gold-abstract", eyebrow="START FREE",
                 headline="One plan for every pace.",
                 sub="Free signals today. Upgrade when they start paying for "
                     "themselves.",
                 body={"kind": "chips",
                       "chips": ["Free", "$29 Pro", "$79 Elite",
                                 "$149 Sovereign", "$199 Autonomous"]},
                 cta="priv.sansmercantile.com", hsize=96,
                 vo="Start free today. Priv, a Sans Mercantile product."),
        ]),
    "bumper-6s": dict(
        size=(1920, 1080), fmt="wide",
        out="priv-bumper-6s-1920x1080.mp4",
        scenes=[
            dict(plate="ps-holo-chart", eyebrow="PRIV LIVE",
                 headline="Entry. Two targets. One stop.",
                 sub=None, hsize=124, show_logo=True, hold=3.4),
            dict(plate="ps-gold-abstract", eyebrow="SANS MERCANTILE",
                 headline="priv.sansmercantile.com", sub=None,
                 cta="Start free", hsize=96, hold=3.0),
        ]),
}


# A hand-recorded take in any of these containers wins over the TTS .wav.
RECORDING_EXTS = (".m4a", ".mp4", ".mp3", ".aac", ".ogg", ".flac", ".wma")


def recording(vo_dir, idx):
    """Path of a recorded take for scene NN, or None if only TTS exists."""
    for ext in RECORDING_EXTS:
        p = os.path.join(vo_dir, f"scene-{idx:02d}{ext}")
        if os.path.exists(p):
            return p
    return None


def audio_dur(path):
    """Duration in seconds for .wav (fast path) or any ffmpeg-readable file."""
    if path.lower().endswith(".wav"):
        with wave.open(path) as w:
            return w.getnframes() / float(w.getframerate())
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr or "")
    if not m:
        raise RuntimeError(f"cannot read duration of {path}")
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60
            + float(m.group(3)))


def silence_bounds(path, noise="-45dB", mind=0.25):
    """(start, end) of the audible region — head/tail silence is dropped."""
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", path, "-af",
         f"silencedetect=noise={noise}:d={mind}", "-f", "null", "-"],
        capture_output=True, text=True)
    starts = [float(x) for x in
              re.findall(r"silence_start: (-?[\d.]+)", r.stderr or "")]
    ends = [float(x) for x in
            re.findall(r"silence_end: ([\d.]+)", r.stderr or "")]
    dur = audio_dur(path)
    t0 = ends[0] if ends and starts and starts[0] <= 0.10 else 0.0
    t1 = dur
    if starts and ends and starts[-1] >= ends[-1] and dur - starts[-1] >= mind:
        t1 = starts[-1]
    return max(0.0, t0 - 0.05), min(dur, t1 + 0.05)


def prep_take(path):
    """Trim a recorded take's head/tail silence into TMP (original untouched)."""
    t0, t1 = silence_bounds(path)
    if t0 <= 0.02 and audio_dur(path) - t1 <= 0.02:
        return path
    os.makedirs(TMP, exist_ok=True)
    spot = os.path.basename(os.path.dirname(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    stamp = int(os.path.getmtime(path))
    out = os.path.join(TMP, f"{spot}-{stem}-{stamp}.wav")
    if not os.path.exists(out):
        r = subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", path,
             "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}",
             "-ar", "48000", "-ac", "2", out],
            capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError(f"trim failed for {path}: {r.stderr[-500:]}")
    return out


def tts(text, out_wav):
    txt = out_wav + ".txt"
    with open(txt, "w", encoding="ascii", errors="replace") as f:
        f.write(text)
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", TTS_PS1, "-InFile", txt, "-Out", out_wav,
         "-Voice", VOICE, "-Rate", str(RATE)],
        capture_output=True, text=True)
    if not os.path.exists(out_wav):
        raise RuntimeError(f"TTS failed: {r.stdout}\n{r.stderr}")
    with wave.open(out_wav) as w:
        return w.getnframes() / float(w.getframerate())


def build_frames(spot, name, size, fmt, scenes):
    sb = os.path.join(OUT_SB, name)
    os.makedirs(sb, exist_ok=True)
    paths = []
    for i, sc in enumerate(scenes):
        spec = dict(sc)
        spec.pop("vo", None)
        spec.pop("hold", None)
        spec.setdefault("show_logo", True)
        spec.setdefault("url", B.SITE)
        p = os.path.join(sb, f"scene-{i + 1:02d}.jpg")
        posters.render(spec, fmt, p, force_size=size)
        paths.append(p)
        print(f"  frame {name}/scene-{i + 1:02d} {size[0]}x{size[1]}")
    return paths


def clip(src, dst, size, frames, zoom_in=True):
    w2, h2 = size[0] * 2, size[1] * 2
    n = max(2, frames)
    if zoom_in:
        z = f"1+0.085*on/{n}"
    else:
        z = f"1.085-0.085*on/{n}"
    vf = (f"scale={w2}:{h2}:flags=lanczos,"
          f"zoompan=z='{z}':d={n}:x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':s={size[0]}x{size[1]}:fps={FPS},"
          f"format=yuv420p")
    cmd = [FFMPEG, "-y", "-framerate", str(FPS), "-i", src,
           "-vf", vf, "-frames:v", str(n),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-an", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"clip failed:\n{r.stderr[-2500:]}")


def assemble(clips, voiced, starts, total, out):
    args = [FFMPEG, "-y"]
    for c in clips:
        args += ["-i", c]
    for v, _s in voiced:
        args += ["-i", v]

    n = len(clips)
    parts = []
    vlabel = "[0:v]"
    prev = "[0:v]"
    for i in range(1, n):
        # scene i begins on the output timeline at starts[i]
        label = f"[v{i}]" if i < n - 1 else "[vout]"
        parts.append(f"{prev}[{i}:v]xfade=transition=fade:"
                     f"duration={XFADE}:offset={starts[i]:.3f}{label}")
        prev = label
        vlabel = label

    if voiced:
        parts.append(f"[{n}:a]aresample=44100,"
                     f"aformat=channel_layouts=mono[a0raw]")
        mixed = [f"[a0raw]adelay={int(round(voiced[0][1] * 1000))}:all=1[a0]"]
        for k, (_v, s) in enumerate(voiced[1:], start=1):
            idx = n + k
            mixed.append(f"[{idx}:a]aresample=44100,"
                         f"aformat=channel_layouts=mono,"
                         f"adelay={int(round(s * 1000))}:all=1[a{k}]")
        parts += mixed
        parts.append("".join(f"[a{k}]" for k in range(len(voiced))) +
                     f"amix=inputs={len(voiced)}:normalize=0,"
                     f"loudnorm=I=-16:TP=-1.5:LRA=11,"
                     f"volume=3dB,alimiter=limit=0.9,apad[aout]")
        amap = ["-map", "[aout]"]
    else:
        amap = ["-an"]

    cmd = args + ["-filter_complex", ";".join(parts),
                  "-map", vlabel] + amap + [
        "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if voiced:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]
    cmd += ["-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"assemble failed:\n{r.stderr[-3000:]}")


def build(name, cfg):
    if cfg.get("reuse"):
        base = SPOTS[cfg["reuse"]]
        scenes = base["scenes"]
        size = cfg.get("size", base["size"])
        fmt = cfg.get("fmt", base["fmt"])
        margin = cfg.get("margin", base.get("margin", MARGIN))
    else:
        size, fmt, scenes = cfg["size"], cfg["fmt"], cfg["scenes"]
        margin = cfg.get("margin", MARGIN)

    print(f"\n=== {name}  {size[0]}x{size[1]}  {len(scenes)} scenes ===")
    frames = build_frames(name, name, size, fmt, scenes)

    vo_dir = os.path.join(OUT_VO, name)
    os.makedirs(vo_dir, exist_ok=True)
    vo_paths, vo_dur = [], []
    for i, sc in enumerate(scenes):
        text = sc.get("vo")
        if text:
            take = recording(vo_dir, i + 1)
            if take:
                raw = audio_dur(take)
                p = prep_take(take)
                d = audio_dur(p)
                src = f"take {os.path.splitext(take)[1][1:]}" + (
                    f" trimmed {raw - d:+.2f}s" if abs(raw - d) > 0.02 else "")
            else:
                p = os.path.join(vo_dir, f"scene-{i + 1:02d}.wav")
                d, src = tts(text, p), "tts"
            vo_paths.append(p)
            vo_dur.append(d)
            print(f"  vo   scene-{i + 1:02d} {d:.2f}s  [{src}]")
        else:
            vo_paths.append(None)
            vo_dur.append(0.0)

    durs = []
    for i, sc in enumerate(scenes):
        if vo_dur[i] > 0:
            d = max(MIN_DUR, vo_dur[i] + margin)
        else:
            d = float(sc.get("hold", 4.0))
        durs.append(d)

    starts = [0.0]
    for i in range(1, len(durs)):
        starts.append(sum(durs[:i]) - i * XFADE)
    total = sum(durs) - (len(durs) - 1) * XFADE

    os.makedirs(TMP, exist_ok=True)
    clips = []
    for i, f in enumerate(frames):
        c = os.path.join(TMP, f"{name}-{i:02d}.mp4")
        clip(f, c, size, int(round(durs[i] * FPS)), zoom_in=(i % 2 == 0))
        clips.append(c)
        print(f"  clip scene-{i + 1:02d} {durs[i]:.2f}s")

    voiced = [(p, s) for p, s in zip(vo_paths, starts) if p]
    os.makedirs(OUT_VID, exist_ok=True)
    out = os.path.join(OUT_VID, cfg["out"])
    assemble(clips, voiced, starts, total, out)
    for c in clips:
        os.remove(c)
    print(f"  -> {out}  ({total:.2f}s)")


def main():
    only = sys.argv[1:] or list(SPOTS)
    for name in only:
        build(name, SPOTS[name])
    print("\ndone")


if __name__ == "__main__":
    main()
