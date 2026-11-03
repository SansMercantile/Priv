"""Generate 02-VIDEO-SCRIPTS-AND-STORYBOARDS.md from the rendered assets."""
import glob
import os
import re
import subprocess
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ads as A  # noqa: E402
import videos as V  # noqa: E402

MIN_DUR, XFADE = V.MIN_DUR, V.XFADE

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "02-VIDEO-SCRIPTS-AND-STORYBOARDS.md")

INTRO = """\
Eight finished spots: five campaign pieces cut from full-frame stills rendered
by the same compositor as the posters, and three Creatify-style ad cuts, so
type scale, scrim, logo lock-up and gold are identical across still and moving
work.

**What ships per spot**

| Asset | Path |
| --- | --- |
| Finished MP4 (H.264 + AAC) | `assets/videos/<name>.mp4` |
| Storyboard stills (1 per scene) | `assets/storyboards/<name>/scene-NN.jpg` |
| Voice-over stems (1 per scene) | `assets/voiceover/<name>/scene-NN.{wav,m4a}` |

**Voice-over** is Windows SAPI (`Microsoft David Desktop`, rate −1), written to
22.05 kHz mono WAV per scene, then delayed onto the cut with ffmpeg `adelay`.
A hand-recorded take in `scene-NN.m4a` (or mp4/mp3/aac/ogg/flac/wma) wins over
the synthesized WAV wherever one exists: it is silence-trimmed head and tail
once, cached in `assets/.frames/`, and then drives scene length, the audio
delay and every duration printed below. Scene length is derived from the take:
`max(3.5 s, VO + margin)`, so no line is ever clipped by the cross-fade that
follows it.

**Pictures** are a slow Ken Burns push (`zoompan`, alternating in/out, 8.5 %
over the scene) cut with a 0.45 s `xfade` — no hard cuts, no motion the
compositor did not author.

**Master loudness** is −14 LUFS integrated (measured), which is the target most
paid-social and YouTube placements normalise to.

**The 6 s bumper ships silent** on purpose: it is a brand sting meant to be
laid under a platform sound bed or an existing campaign track.
"""

TAIL = """\
## Production notes

- Re-render any campaign spot with `python videos.py <spot>` (or no argument for
  all five). Frames, stems and the MP4 are rebuilt from the spec table in
  `build/videos.py`.
- Re-render any ad spot with `python ads.py <spot>` (or no argument for all
  three). Captions, CTA and end card come from `build/ads.py::SPOTS`.
- Changing a line re-speaks it: durations, scene starts and the audio delays
  are all recomputed, so the cut re-times itself.
- Every scene is also a poster-format composition. If a headline changes in
  `build/poster_specs.py`, update the matching scene dict in
  `build/videos.py` so the two channels do not drift.
- Bumper frames are shared with the poster set (same plate, same lock-up);
  only the copy differs.
- The mark on every frame, badge and end card is `assets/brand/priv-mark.png`,
  drawn by `brand.py::logo_mark()` — swap the file to re-brand all eight spots.
"""

ADS_INTRO = """\
## Ad spots (Creatify style)

Three paid-social cuts built from the eight neon plates. Same compositor and
lock-up as the campaign spots, different grammar: night-desk B-roll, burned-in
kinetic captions (libass — uppercase, accent words in brand gold, pop-in),
a corner mark badge, an end card with the CTA pill, and a brisker read
(SAPI rate +2 against the campaign's −1). Hand-recorded takes in
`assets/voiceover/<spot>/scene-NN.m4a` win over that synthesized read: each is
silence-trimmed once and then sets scene length, the audio delay and the length
of the finished cut.

**Masters:** the reference ads sit at −13.1 LUFS, so these are mastered to
**−13 LUFS** (ads.py::LUFS). Linear loudnorm is true-peak bound — it cannot
lift a file past its own crest — so `master()` measures the crest first and
applies escalating `acompressor`/`alimiter` steps until the target is
reachable, then does the two-pass linear normalise.

**Aspect cuts:** one wide (1920 x 1080) for YouTube/LinkedIn, two vertical
(1080 x 1920) for Reels/TikTok/Shorts. Captions sit above the CTA band on
both (0.30 h of the frame vertically in portrait, 0.205 h in landscape).

"""

BUILT = """\
### How an ad spot is built

1. `scene_frames()` renders each plate darkened + vignetted — the end scene
   becomes a branded end card (`end_card()`: mark, wordmark, CTA pill, URL,
   risk line).
2. `tts()` speaks each line at rate +2 into `assets/voiceover/<spot>/` — unless
   a recorded take (`scene-NN.m4a`) is present, which is trimmed and used as-is.
3. Scene lengths are solved to hit the spot's target length: the slack over
   `target` is spread across scenes so the VO never gets clipped. The spread is
   floored at the 0.4 s `xfade`, so takes run back to back and never overlap —
   if they overrun the target the spot runs long instead of clipping a line.
4. `beats()` splits each line into ≤4-word caption beats; `write_ass()` emits
   the libass file (pop-in, gold accent words, safe-area margins).
5. `assemble()` cuts the Ken Burns clips with `xfade` (`fadewhite` on the
   scripted beat), overlays the corner mark badge and the CTA pill (inside
   the 4.2 s before the end card), then burns the captions.
6. `master()` and `loudness()` bring the mix to −13 LUFS integrated.
"""


def vo_dur(vo_dir, idx):
    """Seconds for scene NN — the silence-trimmed take the renderer used."""
    take = V.recording(vo_dir, idx)
    if take:
        return V.audio_dur(V.prep_take(take))
    path = os.path.join(vo_dir, f"scene-{idx:02d}.wav")
    if not os.path.exists(path):
        return 0.0
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def vo_src(vo_dir, name):
    """Markdown for a spot's voice-over line — records win over TTS stems."""
    ext, take = "wav", False
    for e in V.RECORDING_EXTS:
        if glob.glob(os.path.join(vo_dir, f"scene-*{e}")):
            ext, take = e.lstrip("."), True
            break
    s = f"**VO** `assets/voiceover/{name}/scene-NN.{ext}`"
    if take:
        s += " — recorded takes (silence-trimmed; they set the timing)"
    return s


def probe(path):
    """(duration seconds, integrated LUFS) for a rendered MP4."""
    r = subprocess.run([V.FFMPEG, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr or "")
    dur = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
           if m else None)
    lufs = A.loudness(path) if os.path.exists(path) else None
    return dur, lufs


def ad_lines():
    lines = [ADS_INTRO,
             "| Spot | Frame | Scenes | Captions | Output | Length | Master |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, cfg in A.SPOTS.items():
        out = os.path.join(A.OUT_VID, cfg["out"])
        dur, lufs = probe(out)
        beats_n = sum(len(A.beats(sc["vo"])) for sc in cfg["scenes"]
                      if sc.get("vo") and not sc.get("end"))
        w, h = cfg["size"]
        lines.append(
            f"| `{name}` | {w} x {h} {'vertical' if h > w else 'wide'} | "
            f"{len(cfg['scenes'])} | {beats_n} | `assets/videos/{cfg['out']}` | "
            f"{dur:.1f} s | {round(lufs, 1) if lufs else '—'} LUFS |"
            if dur and lufs else
            f"| `{name}` | {w} x {h} | {len(cfg['scenes'])} | {beats_n} | "
            f"`assets/videos/{cfg['out']}` | — | — |")
    lines.append("")

    for name, cfg in A.SPOTS.items():
        w, h = cfg["size"]
        vo_dir = os.path.join(A.OUT_VO, name)
        vo_list = [vo_dur(vo_dir, i + 1) for i in range(len(cfg["scenes"]))]
        speech = sum(vo_list)
        lines += [f"### {name}", "",
                  f"**Output** `assets/videos/{cfg['out']}` — {w} x {h}, "
                  f"30 fps, target **{cfg['target']} s**", "",
                  f"**Stills** rendered per scene in `assets/.ads/{name}/` · "
                  f"{vo_src(vo_dir, name)}", ""]
        if speech > cfg["target"] + 0.5:
            cut, _ = probe(os.path.join(A.OUT_VID, cfg["out"]))
            lines += [f"Recorded takes total **{speech:.1f} s** of speech against "
                      f"a {cfg['target']} s target, so the cut runs "
                      f"**{cut:.1f} s** — the solver stops shortening scenes at "
                      f"the 0.4 s cross-fade rather than clipping a line.", ""]
        lines += ["| # | Plate | Voice-over | Caption beats |",
                  "| --- | --- | --- | --- |"]
        for i, sc in enumerate(cfg["scenes"]):
            vo = sc.get("vo") or ""
            d = vo_list[i]
            vt = f"“{vo}” _({d:.1f} s)_" if vo else "_(silent)_"
            if sc.get("end"):
                vt += " — **end card**"
            n = len(A.beats(vo)) if vo and not sc.get("end") else 0
            lines.append(f"| {i + 1} | `{sc['plate']}` | {vt} | "
                         f"{n or '—'} |")
        lines.append("")

    lines += [BUILT]
    return lines


def main():
    lines = ["# 02 — Video scripts and storyboards", "", INTRO]

    for name, cfg in V.SPOTS.items():
        if cfg.get("reuse"):
            base = V.SPOTS[cfg["reuse"]]
            scenes = base["scenes"]
            size = cfg.get("size", base["size"])
            margin = cfg.get("margin", base.get("margin", V.MARGIN))
            shared = cfg["reuse"]
        else:
            scenes, size = cfg["scenes"], cfg["size"]
            margin = cfg.get("margin", V.MARGIN)
            shared = None

        vo_dir = os.path.join(V.OUT_VO, name)
        durs, starts, vos = [], [0.0], []
        for i, sc in enumerate(scenes):
            d = vo_dur(vo_dir, i + 1)
            vos.append(d)
            if d > 0:
                durs.append(max(MIN_DUR, d + margin))
            else:
                durs.append(float(sc.get("hold", 4.0)))
        for i in range(1, len(durs)):
            starts.append(sum(durs[:i]) - i * XFADE)
        total = sum(durs) - (len(durs) - 1) * XFADE

        lines += [f"## {name}", "",
                  f"**Output** `assets/videos/{cfg['out']}` — {size[0]} x {size[1]}, "
                  f"30 fps, **{total:.1f} s**", "",
                  f"**Stills** `assets/storyboards/{name}/scene-NN.jpg` · "
                  f"{vo_src(vo_dir, name)}", ""]
        if shared:
            lines.append(f"Scenes are shared with `{shared}` and re-rendered at "
                         f"{size[0]} x {size[1]} so the vertical cut is not a "
                         f"letterboxed landscape edit.\n")

        lines += ["| # | In | Scene | Headline | On-screen body | Voice-over |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for i, sc in enumerate(scenes):
            v = sc.get("vo")
            if v:
                vo_txt = f"“{v}” _({vos[i]:.1f} s)_"
            else:
                vo_txt = "_(silent)_"
            body = sc.get("body")
            if body:
                b = body["kind"]
                if b == "signal":
                    b = "live signal ticket"
                elif b == "chips":
                    b = "chips: " + ", ".join(sc["body"]["chips"])
                elif b == "stats":
                    b = "stats: " + " · ".join(f"{a} {c}" for a, c in sc["body"]["stats"])
                elif b == "bullets":
                    b = f"{len(sc['body']['items'])} bullets"
                elif b == "platforms":
                    b = f"{len(sc['body']['platforms'])} platform cards"
                elif b == "agents":
                    b = f"{len(sc['body']['agents'])} agent rows"
            else:
                b = "—"
            plate = sc["plate"]
            lines.append(f"| {i + 1} | {starts[i]:.1f} s | `{plate}` · "
                         f"{sc['eyebrow']} | {sc['headline']} | {b} | {vo_txt} |")
        lines.append("")

    lines += ad_lines()
    lines += [TAIL]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
