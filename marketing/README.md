# Priv campaign — marketing assets

Everything produced for the Priv launch: strategy, copy, 38 posters, 5 video
spots with voice-over, and the production toolchain that renders them.

| Doc | What it is |
| --- | --- |
| [`00-ROADMAP.md`](00-ROADMAP.md) | status, sequencing, AWS reactivation summary, what is left |
| [`01-CAMPAIGN-PLAN.md`](01-CAMPAIGN-PLAN.md) | positioning, audience, message pillars, channel matrix, KPIs |
| [`02-VIDEO-SCRIPTS-AND-STORYBOARDS.md`](02-VIDEO-SCRIPTS-AND-STORYBOARDS.md) | five finished spots, per-scene timings and voice-over |
| [`03-POSTER-GALLERY.md`](03-POSTER-GALLERY.md) | auto-index of all 38 posters |
| [`04-COPY-BANK.md`](04-COPY-BANK.md) | every headline, tier line, caption and subject line |
| [`05-ASSET-AND-PRODUCTION-GUIDE.md`](05-ASSET-AND-PRODUCTION-GUIDE.md) | folder map, commands, QA gates, pipeline notes |

## Assets at a glance

- **Plates** — `assets/backgrounds/` (18, text-free)
- **Posters** — `assets/posters/{feed,story,wide,link,thumb}/` (38 JPEGs)
- **Videos** — `assets/videos/` (5 MP4, 5.95 s → 59.16 s)
- **Storyboards** — `assets/storyboards/<spot>/scene-NN.jpg`
- **Voice-over** — `assets/voiceover/<spot>/scene-NN.wav`

## Re-render

```powershell
$py = "C:\Users\kpasc\.bridge\venv\Scripts\python.exe"
cd build
& $py run_posters.py     # posters
& $py audit.py           # must print ALL CLEAR
& $py videos.py          # videos
```

See `05-ASSET-AND-PRODUCTION-GUIDE.md` for the full pipeline, QA gates and
the AWS reactivation record.
