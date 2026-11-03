"""Creatify-style ad spots.

Night-desk neon B-roll, burned-in kinetic captions (libass), brand chrome and
a -13 LUFS mastered voice-over — the house style of the reference Creatify ads.

    python ads.py                 # every spot
    python ads.py ad-hook-15s     # one spot
"""
import os
import re
import shutil
import subprocess
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import brand as B            # noqa: E402
import backgrounds as BG     # noqa: E402
import posters as P          # noqa: E402
import videos as V           # noqa: E402
from growth.stats import guard  # noqa: E402

FFMPEG = V.FFMPEG
FPS = V.FPS
XFADE = 0.40
LUFS = -13.0            # the reference ad masters at -13.1 LUFS
OUT_VID = V.OUT_VID
OUT_VO = os.path.join(B.ASSETS, "voiceover")
TMP = os.path.join(B.ASSETS, ".ads")

GOLD_ASS = "&H37AFD4&"          # brand gold #d4af37 as ASS BGR
WHITE_ASS = "&HFFFFFF&"
ACCENT = {"ENTRY", "TARGETS", "STOP", "FREE", "CUSTODY", "BROKER", "PROVE",
          "SEVEN", "TIMEFRAMES", "PRIV", "EXIT", "SIGNAL", "AUDITED",
          "DISAGREE", "NEVER"}
CAPTION_SAFE = 0.88        # fraction of the frame width captions may use

RATE = 2                   # brisk ad read (campaign spots use -1)
TTS_PS1 = V.TTS_PS1
VOICE = V.VOICE
# Ads master at the reference's -13 LUFS. Linear loudnorm is true-peak bound, so
# the crest has to come down first — see master().
COMP_STEPS = [
    "acompressor=threshold=-22dB:ratio=4:attack=5:release=150:makeup=1,"
    "alimiter=limit=0.9:level=disabled",
    "acompressor=threshold=-26dB:ratio=6:attack=4:release=130:makeup=1,"
    "alimiter=limit=0.85:level=disabled",
    "acompressor=threshold=-30dB:ratio=8:attack=3:release=120:makeup=1,"
    "alimiter=limit=0.78:level=disabled",
]

SPOTS = {
    "ad-hook-15s": dict(
        size=(1080, 1920), min_dur=3.0, margin=0.8, target=15,
        out="priv-ad-hook-15s-vertical-1080x1920.mp4",
        scenes=[
            dict(plate="vt-neon-window",
                 vo="Nobody taught you this in demo."),
            dict(plate="vt-neon-desk-hands",
                 vo="Most people learn it after a bad week."),
            dict(plate="vt-neon-macro",
                 vo="So Priv writes the exit before the entry."),
            dict(end=True, plate="vt-neon-desk",
                 vo="Priv. Start free, no card required."),
        ]),
    "ad-proof-30s": dict(
        size=(1080, 1920), min_dur=3.8, margin=1.6, target=30, white_at=4,
        out="priv-ad-proof-30s-vertical-1080x1920.mp4",
        scenes=[
            dict(plate="vt-neon-desk",
                 vo="Nobody taught you this in demo."),
            dict(plate="vt-neon-phone",
                 vo="One market. Seven timeframes."),
            dict(plate="vt-neon-window",
                 vo="When they disagree, that disagreement is the signal."),
            dict(plate="vt-neon-desk-hands",
                 vo="Every ticket ships entry, two targets and a stop."),
            dict(plate="vt-neon-coffee",
                 vo="A twenty-eight second decision cycle, audited every run."),
            dict(plate="vt-neon-macro",
                 vo="Your money never leaves your own broker."),
            dict(end=True, plate="vt-neon-desk-hands",
                 vo="Priv. Start free, no card required."),
        ]),
    "ad-desk-15s": dict(
        size=(1920, 1080), min_dur=3.0, margin=0.8, target=15, white_at=2,
        out="priv-ad-desk-15s-wide-1920x1080.mp4",
        scenes=[
            dict(plate="ls-neon-desk", vo="Entry. Two targets. One stop."),
            dict(plate="ls-neon-window", vo="Prove it before you risk it."),
            dict(plate="vt-neon-desk",
                 vo="Your account. Your funds. Your control."),
            dict(end=True, plate="ls-neon-window",
                 vo="priv dot sans mercantile dot com. Start free today."),
        ]),
    "ad-modes-15s": dict(
        size=(1080, 1920), min_dur=3.0, margin=0.8, target=15,
        out="priv-ad-modes-15s-vertical-1080x1920.mp4",
        scenes=[
            dict(plate="vt-candle-wall",
                 vo="Backtest your strategies while Autonomous is off."),
            dict(plate="vt-neon-desk",
                 vo="Star the one you prefer. Then arm it."),
            dict(plate="vt-holo-signal",
                 vo="Or pick 100% AI mode. It switches strategy as the market moves."),
            dict(end=True, plate="vt-neon-desk-hands",
                 vo="Priv. Start free, no card required."),
        ]),
    "ad-custody-15s": dict(
        size=(1080, 1920), min_dur=3.0, margin=0.8, target=15,
        out="priv-ad-custody-15s-vertical-1080x1920.mp4",
        scenes=[
            dict(plate="vt-vault-door",
                 vo="Priv trades. Your funds stay yours."),
            dict(plate="vt-neon-phone",
                 vo="Connect your own broker through official OAuth."),
            dict(plate="vt-neon-macro",
                 vo="Every order is placed in your name, and logged."),
            dict(end=True, plate="vt-neon-desk",
                 vo="Priv. Start free, no card required."),
        ]),
    "ad-signal-15s": dict(
        size=(1920, 1080), min_dur=3.0, margin=0.8, target=15, white_at=2,
        out="priv-ad-signal-15s-wide-1920x1080.mp4",
        scenes=[
            dict(plate="ls-gold-charts", vo="A direction is not a trade plan."),
            dict(plate="ls-neon-desk",
                 vo="Priv sends the entry, two targets and the stop."),
            dict(plate="ls-trading-floor", vo="Free, four signals a day."),
            dict(end=True, plate="ls-neon-window",
                 vo="priv dot sans mercantile dot com. Start free today."),
        ]),
}


# ---------------------------------------------------------------- captions --
def beats(vo, max_words=4):
    """Split a voice-over line into short caption beats."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?;,])\s+", vo.strip()) if p.strip()]
    out = []
    for p in parts:
        words = p.split()
        while len(words) > max_words:
            out.append(" ".join(words[:max_words]))
            words = words[max_words:]
        if words:
            out.append(" ".join(words))
    return [b for b in out if b]


def _accent(word):
    core = re.sub(r"[^A-Za-z]", "", word)
    return core.upper() in ACCENT


def caption_line(text):
    """ASS body for one beat: uppercase, accent words in brand gold, pop-in."""
    words = text.upper().split()
    body = []
    for w in words:
        if _accent(w):
            body.append(f"{{\\1c{GOLD_ASS}}}{w}{{\\1c{WHITE_ASS}}}")
        else:
            body.append(w)
    pop = (r"\fad(65,65)\fscx124\fscy124\t(0,110,\fscx100\fscy100)")
    return "{" + pop + "}" + " ".join(body)


def _ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(path, size, events):
    w, h = size
    fsize = int(min(w * 0.078, h * 0.072))
    outline = max(3, fsize // 11)
    margin_v = int(h * 0.30) if h > w else int(h * 0.205)
    margin_h = int(w * 0.06)
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {w}",
        f"PlayResY: {h}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Cap,Segoe UI Black,{fsize},{WHITE_ASS},&H0000FFFF,"
        f"&H00270E0A&,&H80000000&,-1,0,0,0,100,100,1,0,1,{outline},"
        f"{max(2, outline // 2)},2,{margin_h},{margin_h},{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text",
    ]
    for start, end, text in events:
        lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Cap,,"
                     f"0,0,0,,{caption_line(text)}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return fsize


# ------------------------------------------------------------------ frames --
def tts(text, out_wav):
    """Brisk ad read — same SAPI path as the campaign spots, faster rate."""
    txt = out_wav + ".txt"
    with open(txt, "w", encoding="ascii", errors="replace") as fh:
        fh.write(text)
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", TTS_PS1, "-InFile", txt, "-Out", out_wav,
         "-Voice", VOICE, "-Rate", str(RATE)],
        capture_output=True, text=True)
    if not os.path.exists(out_wav):
        raise RuntimeError(f"TTS failed: {r.stdout}\n{r.stderr}")
    with wave.open(out_wav) as w:
        return w.getnframes() / float(w.getframerate())


def end_card(size, plate=None):
    """Dark branded end card: mark, wordmark, CTA pill, URL, risk line."""
    w, h = size
    if plate:
        im = BG.load(plate, size).convert("RGB")
        im = P.darken(im, top=0.26, bottom=0.14).convert("RGB")
    else:
        im = Image.new("RGB", size, B.NAVY_DEEP)
    im = B.vignette(im, 0.78).convert("RGBA")

    small = min(w, h)
    mark = B.logo_mark(int(small * 0.36), halo=True, ring=True)
    cy = int(h * 0.30)
    im.alpha_composite(mark, ((w - mark.width) // 2, cy - mark.height // 2))

    wm_f = B.font("display", int(small * 0.095))
    wm = B.wordmark(wm_f, color=B.GOLD, tracking=int(wm_f.size * 0.36))
    im.alpha_composite(wm, ((w - wm.width) // 2, cy + int(small * 0.20)))

    d = ImageDraw.Draw(im, "RGBA")

    label = "START FREE — NO CARD REQUIRED"
    f = B.font("display", int(small * 0.036))
    pad_x, pad_y, tr = int(f.size * 0.95), int(f.size * 0.55), int(f.size * 0.26)
    asc, desc = f.getmetrics()
    pw = int(B.text_w(label, f) + tr * (len(label) - 1) + pad_x * 2)
    ph = int(asc + desc + pad_y * 2)
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    B.pill(ImageDraw.Draw(pill), (0, 0), label, f, fg=B.NAVY_DEEP, bg=B.GOLD,
           pad_x=pad_x, pad_y=pad_y, tracking=tr)
    py = cy + int(small * 0.34)
    im.alpha_composite(pill, ((w - pw) // 2, py))

    f2 = B.font("mono", int(small * 0.040))
    url = B.SITE
    tw = B.text_w(url, f2)
    uy = py + ph + int(small * 0.06)
    d.text(((w - tw) / 2 + 2, uy + 2), url, font=f2, fill=(0, 0, 0, 190))
    d.text(((w - tw) / 2, uy), url, font=f2, fill=B.MUTED + (255,))

    f3 = B.font("body", int(small * 0.026))
    risk = ("Trading involves risk. Past performance is not indicative of "
            "future results.")
    ry = h - int(h * 0.11)
    for line in B.wrap(risk, f3, int(w * 0.80)):
        lw = B.text_w(line, f3)
        d.text(((w - lw) / 2, ry), line, font=f3, fill=(148, 163, 184, 235))
        ry += int(f3.size * 1.35)
    return im.convert("RGB")


def scene_frames(name, size, scenes):
    out_dir = os.path.join(TMP, name)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, sc in enumerate(scenes):
        p = os.path.join(out_dir, f"frame-{i + 1:02d}.jpg")
        if sc.get("end"):
            im = end_card(size, sc.get("plate"))
        else:
            im = BG.load(sc["plate"], size).convert("RGB")
            im = P.darken(im, top=0.90, bottom=0.70).convert("RGB")
            im = B.vignette(im, 0.42).convert("RGB")
        im.save(p, quality=93)
        paths.append(p)
        print(f"  frame {name}/{i + 1:02d} {'end-card' if sc.get('end') else sc['plate']}")
    return paths


def logo_png(size, path):
    s = int(min(size) * 0.11)
    B.logo_mark(s, halo=True, ring=True).save(path)
    return path, s


def cta_png(size, path):
    w, h = size
    label = "START FREE — NO CARD REQUIRED"
    fs = int(min(w * 0.048, h * 0.030))
    while True:   # shrink until the pill fits inside the frame (9:16 clipped it)
        f = B.font("display", fs)
        pad_x, pad_y, tr = int(f.size * 0.95), int(f.size * 0.5), int(f.size * 0.26)
        asc, desc = f.getmetrics()
        pw = int(B.text_w(label, f) + tr * (len(label) - 1) + pad_x * 2)
        ph = int(asc + desc + pad_y * 2)
        if pw <= w * 0.92 or fs <= 14:
            break
        fs -= 2
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    B.pill(ImageDraw.Draw(img), (0, 0), label, f, fg=B.NAVY_DEEP, bg=B.GOLD,
           pad_x=pad_x, pad_y=pad_y, tracking=tr)
    img.save(path)
    return path, (pw, ph)


# --------------------------------------------------------------- assembly --
def assemble(clips, voiced, starts, total, out, ass, logo, cta, logo_end,
             cta_from, cta_end, cta_y, size, white_idx):
    w, h = size
    args = [FFMPEG, "-y"]
    for c in clips:
        args += ["-i", c]
    n = len(clips)
    args += ["-framerate", str(FPS), "-loop", "1", "-t", f"{total:.3f}", "-i", logo]
    li = n
    args += ["-framerate", str(FPS), "-loop", "1", "-t", f"{total:.3f}", "-i", cta]
    ci = n + 1
    for v, _s in voiced:
        args += ["-i", v]
    first_audio = n + 2

    parts = []
    prev = "[0:v]"
    for i in range(1, n):
        trans = "fadewhite" if i == white_idx else "fade"
        lab = f"[x{i}]"
        parts.append(f"{prev}[{i}:v]xfade=transition={trans}:"
                     f"duration={XFADE}:offset={starts[i]:.3f}{lab}")
        prev = lab
    parts.append(f"{prev}format=rgba[f0]")

    lx, ly = int(w * 0.05), int(h * 0.045)
    parts.append(f"[f0][{li}:v]overlay=x={lx}:y={ly}:"
                 f"enable='between(t,0,{logo_end:.3f})'[o1]")
    parts.append(f"[o1][{ci}:v]overlay=x=(W-w)/2:y={cta_y}:"
                 f"enable='between(t,{cta_from:.3f},{cta_end:.3f})'[o2]")

    esc = ass.replace("\\", "/").replace(":", "\\:")
    parts.append(f"[o2]ass='{esc}'[vpre]")
    parts.append("[vpre]format=yuv420p[vout]")

    if voiced:
        parts.append(f"[{first_audio}:a]aresample=44100,"
                     f"aformat=channel_layouts=mono[a0raw]")
        mixed = [f"[a0raw]adelay={int(round(voiced[0][1] * 1000))}:all=1[a0]"]
        for k, (_v, s) in enumerate(voiced[1:], start=1):
            idx = first_audio + k
            mixed.append(f"[{idx}:a]aresample=44100,"
                         f"aformat=channel_layouts=mono,"
                         f"adelay={int(round(s * 1000))}:all=1[a{k}]")
        parts += mixed
        parts.append("".join(f"[a{k}]" for k in range(len(voiced))) +
                     f"amix=inputs={len(voiced)}:normalize=0,apad[aout]")
        amap = ["-map", "[aout]"]
    else:
        amap = ["-an"]

    cmd = args + ["-filter_complex", ";".join(parts), "-map", "[vout]"] + amap + [
        "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if voiced:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]
    cmd += ["-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"assemble failed:\n{r.stderr[-3000:]}")


def loudness(path):
    m = measure(path, "loudnorm=print_format=json")
    return float(m["input_i"]) if m else None


def measure(path, af=None):
    """First pass of a two-pass loudnorm: run the chain through a null output."""
    import json
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", path, "-af",
         af or f"loudnorm=I={LUFS}:TP=-1.0:LRA=11:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr or "")
    return json.loads(m.group()) if m else None


def _ln(m, comp):
    """Two-pass loudnorm expression built from a measurement."""
    return (f"{comp},loudnorm=I={LUFS}:TP=-1.0:LRA=11"
            f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true")


def master(raw, out):
    """Second pass.

    Linear loudnorm cannot lift a file past its own crest factor
    (`out_I = -1.0 - (TP - I)`), so keep adding crest reduction until the
    measurement says the target is reachable, then normalise once.
    """
    chosen = None
    for comp in COMP_STEPS:
        m = measure(raw, f"{comp},loudnorm=I={LUFS}:TP=-1.0:LRA=11:"
                         f"print_format=json")
        if not m:
            break
        crest = float(m["input_tp"]) - float(m["input_i"])
        chosen = (comp, m, crest)
        if crest <= 12.0:
            break
    if chosen is None:
        os.replace(raw, out)
        return None
    comp, m, crest = chosen
    r = subprocess.run([FFMPEG, "-y", "-i", raw, "-af", _ln(m, comp),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-ar", "44100", "-ac", "2", "-movflags", "+faststart",
                        out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"master failed:\n{r.stderr[-2000:]}")
    os.remove(raw)
    return dict(comp=comp, crest=round(crest, 2),
                measured_i=m["input_i"], measured_tp=m["input_tp"])


# ------------------------------------------------------------------- build --
def build(name, cfg):
    size = cfg["size"]
    scenes = cfg["scenes"]
    min_dur, margin = cfg.get("min_dur", 4.0), cfg.get("margin", 1.9)
    end_idx = next((i for i, s in enumerate(scenes) if s.get("end")), None)

    print(f"\n=== {name}  {size[0]}x{size[1]}  {len(scenes)} scenes ===")
    for sc in scenes:
        bad = guard(sc.get("vo", ""))
        if bad:
            raise SystemExit(f"compliance block in VO {sc.get('vo')!r}: {bad}")

    frames = scene_frames(name, size, scenes)

    vo_dir = os.path.join(OUT_VO, name)
    os.makedirs(vo_dir, exist_ok=True)
    vo_paths, vo_dur = [], []
    for i, sc in enumerate(scenes):
        text = sc.get("vo")
        if text:
            take = V.recording(vo_dir, i + 1)
            if take:
                raw = V.audio_dur(take)
                p = V.prep_take(take)
                d = V.audio_dur(p)
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

    if cfg.get("target") and all(vo_dur):
        n = len(vo_dur)
        k = (cfg["target"] + (n - 1) * XFADE - sum(vo_dur)) / n
        # k must cover the cross-fade, otherwise scene i's tail overlaps
        # scene i+1's head and two voices speak at once.
        if k < XFADE:
            print(f"  note  takes total {sum(vo_dur):.1f}s (target "
                  f"{cfg['target']}s) — scene slack set to the {XFADE}s "
                  f"cross-fade so no take is clipped or overlapped")
            k = XFADE
        durs = [max(min_dur, v + k) for v in vo_dur]
    else:
        durs = [max(min_dur, vo_dur[i] + margin) if vo_dur[i] > 0 else
                float(scenes[i].get("hold", 4.0)) for i in range(len(scenes))]
    starts = [0.0]
    for i in range(1, len(durs)):
        starts.append(sum(durs[:i]) - i * XFADE)
    total = sum(durs) - (len(durs) - 1) * XFADE

    # captions on the output timeline, one beat at a time
    events = []
    for i, sc in enumerate(scenes):
        if sc.get("end") or not sc.get("vo"):
            continue
        bts = beats(sc["vo"])
        if not bts:
            continue
        span_s = starts[i] + 0.12
        span_e = starts[i] + min(durs[i] - 0.10, vo_dur[i] + 1.2)
        if i + 1 < len(starts):
            nxt = scenes[i + 1]
            followed = (bool(nxt.get("vo")) and not nxt.get("end")
                        and bool(beats(nxt["vo"])))
            # never run into the next beat's captions (same style, same place
            # -> they would overprint) or trail onto the end card
            span_e = min(span_e, starts[i + 1] + (0.06 if followed else -0.06))
        span_e = max(span_e, span_s + 0.20)
        weights = [max(1, len(b)) for b in bts]
        tot_w = sum(weights)
        t = span_s
        for b, wt in zip(bts, weights):
            d = (span_e - span_s) * wt / tot_w
            events.append((t, t + d, b))
            t += d

    os.makedirs(TMP, exist_ok=True)
    ass = os.path.join(TMP, f"{name}.ass")
    write_ass(ass, size, events)
    print(f"  ass  {len(events)} caption beats")

    clips = []
    for i, f in enumerate(frames):
        c = os.path.join(TMP, f"{name}-{i:02d}.mp4")
        V.clip(f, c, size, int(round(durs[i] * FPS)), zoom_in=(i % 2 == 0))
        clips.append(c)
        print(f"  clip scene-{i + 1:02d} {durs[i]:.2f}s")

    logo, _ = logo_png(size, os.path.join(TMP, f"{name}-logo.png"))
    cta, _ = cta_png(size, os.path.join(TMP, f"{name}-cta.png"))

    ec_start = starts[end_idx] if end_idx is not None else total
    cta_from = max(0.0, ec_start - 4.2)
    cta_y = int(size[1] * (0.745 if size[1] > size[0] else 0.845))
    cta_end = ec_start

    voiced = [(p, s) for p, s in zip(vo_paths, starts) if p]
    os.makedirs(OUT_VID, exist_ok=True)
    out = os.path.join(OUT_VID, cfg["out"])
    raw = os.path.join(TMP, f"{name}-raw.mp4")
    assemble(clips, voiced, starts, total, raw, ass, logo, cta,
             ec_start, cta_from, cta_end, cta_y, size,
             cfg.get("white_at", -1))
    for c in clips:
        os.remove(c)

    mb = master(raw, out)
    i = loudness(out)
    extra = f"  crest {mb['crest']}dB" if mb else ""
    print(f"  -> {out}  {total:.2f}s  loudness "
          f"{i if i is None else round(i, 1)} LUFS (target {LUFS}){extra}")


def main():
    only = sys.argv[1:] or list(SPOTS)
    for name in only:
        build(name, SPOTS[name])
    print("\ndone")


if __name__ == "__main__":
    main()
