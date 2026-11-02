# 02 — Video scripts and storyboards

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

## hero-30s

**Output** `assets/videos/priv-hero-30s-1920x1080.mp4` — 1920 x 1080, 30 fps, **29.7 s**

**Stills** `assets/storyboards/hero-30s/scene-NN.jpg` · **VO** `assets/voiceover/hero-30s/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV — LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop, read from the market.” _(4.9 s)_ |
| 2 | 6.0 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Every strategy is backtested on real candles first.” _(5.0 s)_ |
| 3 | 12.1 s | `ps-trading-floor` · AUTONOMOUS EXECUTION | Arm it. Sleep. Let the desk work. | 3 bullets | “Or arm the desk, and let it work while you sleep.” _(5.7 s)_ |
| 4 | 19.0 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “Your account, your funds, your control.” _(3.5 s)_ |
| 5 | 23.6 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign | “Start free today. Priv, a Sans Mercantile product.” _(4.5 s)_ |

## hero-30s-vertical

**Output** `assets/videos/priv-hero-30s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, **29.7 s**

**Stills** `assets/storyboards/hero-30s-vertical/scene-NN.jpg` · **VO** `assets/voiceover/hero-30s-vertical/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

Scenes are shared with `hero-30s` and re-rendered at 1080 x 1920 so the vertical cut is not a letterboxed landscape edit.

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV — LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop, read from the market.” _(4.9 s)_ |
| 2 | 6.0 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Every strategy is backtested on real candles first.” _(5.0 s)_ |
| 3 | 12.1 s | `ps-trading-floor` · AUTONOMOUS EXECUTION | Arm it. Sleep. Let the desk work. | 3 bullets | “Or arm the desk, and let it work while you sleep.” _(5.7 s)_ |
| 4 | 19.0 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “Your account, your funds, your control.” _(3.5 s)_ |
| 5 | 23.6 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign | “Start free today. Priv, a Sans Mercantile product.” _(4.5 s)_ |

## teaser-15s-vertical

**Output** `assets/videos/priv-teaser-15s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, **15.9 s**

**Stills** `assets/storyboards/teaser-15s-vertical/scene-NN.jpg` · **VO** `assets/voiceover/teaser-15s-vertical/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `vt-holo-signal` · PRIV LIVE | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop.” _(3.7 s)_ |
| 2 | 5.0 s | `vt-desk` · AUTONOMOUS | Arm it. Sleep. Let the desk work. | — | “Arm it, and let the desk work while you sleep.” _(4.2 s)_ |
| 3 | 10.6 s | `vt-particles` · START FREE | Your edge starts here. | — | “Priv. Start free today.” _(3.5 s)_ |

## explainer-60s

**Output** `assets/videos/priv-explainer-60s-1920x1080.mp4` — 1920 x 1080, 30 fps, **63.8 s**

**Stills** `assets/storyboards/explainer-60s/scene-NN.jpg` · **VO** `assets/voiceover/explainer-60s/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-launch` · PRIV — A SANS MERCANTILE PRODUCT | Precision entries, read from the market. | stats: 45+ strategy boards · 7 timeframes · 24/7 market watch | “This is Priv. Precision entries, read from the market, not guessed at.” _(6.8 s)_ |
| 2 | 8.5 s | `ps-holo-chart` · LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Every signal ships complete. Entry, two targets, and a stop that moves to breakeven.” _(8.4 s)_ |
| 3 | 18.6 s | `ps-gold-abstract` · MULTI-TIMEFRAME READS | One market. Seven timeframes. | chips: 1m, 5m, 15m, 30m, 1H, 4H, 1D | “Seven timeframes on every market, from one minute to one day.” _(6.3 s)_ |
| 4 | 26.7 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Prove it in the strategy lab before you risk a cent.” _(6.0 s)_ |
| 5 | 34.5 s | `ps-trading-floor` · MULTI-AGENT DESK | Five agents. One quorum. | 3 agent rows | “Five agents deliberate on every order before it moves.” _(5.4 s)_ |
| 6 | 41.7 s | `ps-devices` · EVERY SCREEN YOU OWN | Your signals, on every screen you own. | 6 platform cards | “Web, desktop and mobile. One account, every screen.” _(6.3 s)_ |
| 7 | 49.7 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “And it stays yours. Your account, your funds, your control.” _(5.8 s)_ |
| 8 | 57.3 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign, $199 Autonomous | “Start free today. Priv, a Sans Mercantile product.” _(4.3 s)_ |

## bumper-6s

**Output** `assets/videos/priv-bumper-6s-1920x1080.mp4` — 1920 x 1080, 30 fps, **6.0 s**

**Stills** `assets/storyboards/bumper-6s/scene-NN.jpg` · **VO** `assets/voiceover/bumper-6s/scene-NN.wav`

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV LIVE | Entry. Two targets. One stop. | — | _(silent)_ |
| 2 | 2.9 s | `ps-gold-abstract` · SANS MERCANTILE | priv.sansmercantile.com | — | _(silent)_ |

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


| Spot | Frame | Scenes | Captions | Output | Length | Master |
| --- | --- | --- | --- | --- | --- | --- |
| `ad-hook-15s` | 1080 x 1920 vertical | 4 | 6 | `assets/videos/priv-ad-hook-15s-vertical-1080x1920.mp4` | 16.0 s | -13.3 LUFS |
| `ad-proof-30s` | 1080 x 1920 vertical | 7 | 15 | `assets/videos/priv-ad-proof-30s-vertical-1080x1920.mp4` | 33.3 s | -13.2 LUFS |
| `ad-desk-15s` | 1920 x 1080 wide | 4 | 8 | `assets/videos/priv-ad-desk-15s-wide-1920x1080.mp4` | 19.1 s | -13.2 LUFS |

### ad-hook-15s

**Output** `assets/videos/priv-ad-hook-15s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, target **15 s**

**Stills** rendered per scene in `assets/.ads/ad-hook-15s/` · **VO** `assets/voiceover/ad-hook-15s/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

Recorded takes total **15.6 s** of speech against a 15 s target, so the cut runs **16.0 s** — the solver stops shortening scenes at the 0.4 s cross-fade rather than clipping a line.

| # | Plate | Voice-over | Caption beats |
| --- | --- | --- | --- |
| 1 | `vt-neon-window` | “Nobody taught you this in demo.” _(2.8 s)_ | 2 |
| 2 | `vt-neon-desk-hands` | “Most people learn it after a bad week.” _(4.4 s)_ | 2 |
| 3 | `vt-neon-macro` | “So Priv writes the exit before the entry.” _(4.5 s)_ | 2 |
| 4 | `vt-neon-desk` | “Priv. Start free, no card required.” _(3.8 s)_ — **end card** | — |

### ad-proof-30s

**Output** `assets/videos/priv-ad-proof-30s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, target **30 s**

**Stills** rendered per scene in `assets/.ads/ad-proof-30s/` · **VO** `assets/voiceover/ad-proof-30s/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

Recorded takes total **32.3 s** of speech against a 30 s target, so the cut runs **33.3 s** — the solver stops shortening scenes at the 0.4 s cross-fade rather than clipping a line.

| # | Plate | Voice-over | Caption beats |
| --- | --- | --- | --- |
| 1 | `vt-neon-desk` | “Nobody taught you this in demo.” _(2.8 s)_ | 2 |
| 2 | `vt-neon-phone` | “One market. Seven timeframes.” _(3.8 s)_ | 2 |
| 3 | `vt-neon-window` | “When they disagree, that disagreement is the signal.” _(5.3 s)_ | 3 |
| 4 | `vt-neon-desk-hands` | “Every ticket ships entry, two targets and a stop.” _(6.0 s)_ | 3 |
| 5 | `vt-neon-coffee` | “A twenty-eight second decision cycle, audited every run.” _(5.4 s)_ | 3 |
| 6 | `vt-neon-macro` | “Your money never leaves your own broker.” _(3.9 s)_ | 2 |
| 7 | `vt-neon-desk-hands` | “Priv. Start free, no card required.” _(5.0 s)_ — **end card** | — |

### ad-desk-15s

**Output** `assets/videos/priv-ad-desk-15s-wide-1920x1080.mp4` — 1920 x 1080, 30 fps, target **15 s**

**Stills** rendered per scene in `assets/.ads/ad-desk-15s/` · **VO** `assets/voiceover/ad-desk-15s/scene-NN.m4a` — recorded takes (silence-trimmed; they set the timing)

Recorded takes total **18.6 s** of speech against a 15 s target, so the cut runs **19.1 s** — the solver stops shortening scenes at the 0.4 s cross-fade rather than clipping a line.

| # | Plate | Voice-over | Caption beats |
| --- | --- | --- | --- |
| 1 | `ls-neon-desk` | “Entry. Two targets. One stop.” _(4.6 s)_ | 3 |
| 2 | `ls-neon-window` | “Prove it before you risk it.” _(3.2 s)_ | 2 |
| 3 | `vt-neon-desk` | “Your account. Your funds. Your control.” _(3.9 s)_ | 3 |
| 4 | `ls-neon-window` | “priv dot sans mercantile dot com. Start free today.” _(6.9 s)_ — **end card** | — |

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

