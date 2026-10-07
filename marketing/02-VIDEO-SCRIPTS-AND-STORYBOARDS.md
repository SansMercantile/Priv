# 02 — Video scripts and storyboards

Five finished spots, each cut from full-frame stills rendered by the same
compositor as the posters, so type scale, scrim, logo lock-up and gold are
identical across still and moving work.

**What ships per spot**

| Asset | Path |
| --- | --- |
| Finished MP4 (H.264 + AAC) | `assets/videos/<name>.mp4` |
| Storyboard stills (1 per scene) | `assets/storyboards/<name>/scene-NN.jpg` |
| Voice-over stems (1 per scene) | `assets/voiceover/<name>/scene-NN.wav` |

**Voice-over** is Windows SAPI (`Microsoft David Desktop`, rate −1), written to
22.05 kHz mono WAV per scene, then delayed onto the cut with ffmpeg `adelay`.
Scene length is derived from the take: `max(3.5 s, VO + margin)`, so no line is
ever clipped by the cross-fade that follows it.

**Pictures** are a slow Ken Burns push (`zoompan`, alternating in/out, 8.5 %
over the scene) cut with a 0.45 s `xfade` — no hard cuts, no motion the
compositor did not author.

**Master loudness** is −14 LUFS integrated (measured), which is the target most
paid-social and YouTube placements normalise to.

**The 6 s bumper ships silent** on purpose: it is a brand sting meant to be
laid under a platform sound bed or an existing campaign track.

## hero-30s

**Output** `assets/videos/priv-hero-30s-1920x1080.mp4` — 1920 x 1080, 30 fps, **30.2 s**

**Stills** `assets/storyboards/hero-30s/scene-NN.jpg` · **VO** `assets/voiceover/hero-30s/scene-NN.wav`

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV — LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop, read from the market.” _(5.5 s)_ |
| 2 | 6.6 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Every strategy is backtested on real candles first.” _(4.5 s)_ |
| 3 | 12.2 s | `ps-trading-floor` · AUTONOMOUS EXECUTION | Arm it. Sleep. Let the desk work. | 3 bullets | “Or arm the desk, and let it work while you sleep.” _(4.1 s)_ |
| 4 | 17.5 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “Your account, your funds, your control.” _(4.2 s)_ |
| 5 | 22.9 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign | “Start free today. Priv, a Sans Mercantile product.” _(5.7 s)_ |

## hero-30s-vertical

**Output** `assets/videos/priv-hero-30s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, **30.2 s**

**Stills** `assets/storyboards/hero-30s-vertical/scene-NN.jpg` · **VO** `assets/voiceover/hero-30s-vertical/scene-NN.wav`

Scenes are shared with `hero-30s` and re-rendered at 1080 x 1920 so the vertical cut is not a letterboxed landscape edit.

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV — LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop, read from the market.” _(5.5 s)_ |
| 2 | 6.6 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Every strategy is backtested on real candles first.” _(4.5 s)_ |
| 3 | 12.2 s | `ps-trading-floor` · AUTONOMOUS EXECUTION | Arm it. Sleep. Let the desk work. | 3 bullets | “Or arm the desk, and let it work while you sleep.” _(4.1 s)_ |
| 4 | 17.5 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “Your account, your funds, your control.” _(4.2 s)_ |
| 5 | 22.9 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign | “Start free today. Priv, a Sans Mercantile product.” _(5.7 s)_ |

## teaser-15s-vertical

**Output** `assets/videos/priv-teaser-15s-vertical-1080x1920.mp4` — 1080 x 1920, 30 fps, **14.7 s**

**Stills** `assets/storyboards/teaser-15s-vertical/scene-NN.jpg` · **VO** `assets/voiceover/teaser-15s-vertical/scene-NN.wav`

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `vt-holo-signal` · PRIV LIVE | Entry. Two targets. One stop. | live signal ticket | “Entry, two targets, one stop.” _(4.0 s)_ |
| 2 | 5.3 s | `vt-desk` · AUTONOMOUS | Arm it. Sleep. Let the desk work. | — | “Arm it, and let the desk work while you sleep.” _(3.9 s)_ |
| 3 | 10.6 s | `vt-particles` · START FREE | Your edge starts here. | — | “Priv. Start free today.” _(2.3 s)_ |

## explainer-60s

**Output** `assets/videos/priv-explainer-60s-1920x1080.mp4` — 1920 x 1080, 30 fps, **59.2 s**

**Stills** `assets/storyboards/explainer-60s/scene-NN.jpg` · **VO** `assets/voiceover/explainer-60s/scene-NN.wav`

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-launch` · PRIV — A SANS MERCANTILE PRODUCT | Precision entries, read from the market. | stats: 45+ strategy boards · 7 timeframes · 24/7 market watch | “This is Priv. Precision entries, read from the market, not guessed at.” _(5.7 s)_ |
| 2 | 7.5 s | `ps-holo-chart` · LIVE SIGNAL FEED | Entry. Two targets. One stop. | live signal ticket | “Every signal ships complete. Entry, two targets, and a stop that moves to breakeven.” _(7.4 s)_ |
| 3 | 16.6 s | `ps-gold-abstract` · MULTI-TIMEFRAME READS | One market. Seven timeframes. | chips: 1m, 5m, 15m, 30m, 1H, 4H, 1D | “Seven timeframes on every market, from one minute to one day.” _(5.1 s)_ |
| 4 | 23.5 s | `ps-strategy` · STRATEGY LAB | Prove it before you risk it. | stats: 152 backtest runs · 45 boards · 7 timeframes | “Prove it in the strategy lab before you risk a cent.” _(4.0 s)_ |
| 5 | 29.2 s | `ps-trading-floor` · MULTI-AGENT DESK | Five agents. One quorum. | 3 agent rows | “Five agents deliberate on every order before it moves.” _(4.3 s)_ |
| 6 | 35.3 s | `ps-devices` · EVERY SCREEN YOU OWN | Your signals, on every screen you own. | 6 platform cards | “Web, desktop and mobile. One account, every screen.” _(6.1 s)_ |
| 7 | 43.1 s | `ps-security` · CUSTODY & CONTROL | Your account. Your funds. Your control. | — | “And it stays yours. Your account, your funds, your control.” _(6.4 s)_ |
| 8 | 51.3 s | `ps-gold-abstract` · START FREE | One plan for every pace. | chips: Free, $29 Pro, $79 Elite, $149 Sovereign, $199 Autonomous | “Start free today. Priv, a Sans Mercantile product.” _(5.7 s)_ |

## bumper-6s

**Output** `assets/videos/priv-bumper-6s-1920x1080.mp4` — 1920 x 1080, 30 fps, **6.0 s**

**Stills** `assets/storyboards/bumper-6s/scene-NN.jpg` · **VO** `assets/voiceover/bumper-6s/scene-NN.wav`

| # | In | Scene | Headline | On-screen body | Voice-over |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 s | `ps-holo-chart` · PRIV LIVE | Entry. Two targets. One stop. | — | _(silent)_ |
| 2 | 2.9 s | `ps-gold-abstract` · SANS MERCANTILE | priv.sansmercantile.com | — | _(silent)_ |

## Production notes

- Re-render any spot with `python videos.py <spot>` (or no argument for all
  five). Frames, stems and the MP4 are rebuilt from the spec table in
  `build/videos.py`.
- Changing a line re-speaks it: durations, scene starts and the audio delays
  are all recomputed, so the cut re-times itself.
- Every scene is also a poster-format composition. If a headline changes in
  `build/poster_specs.py`, update the matching scene dict in
  `build/videos.py` so the two channels do not drift.
- Bumper frames are shared with the poster set (same plate, same lock-up);
  only the copy differs.

