# Priv campaign — marketing assets

Everything produced for the Priv launch: strategy, copy, 38 posters, 8 video
spots with voice-over, a live growth agent on AWS, and the production
toolchain that renders them.

| Doc | What it is |
| --- | --- |
| [`00-ROADMAP.md`](00-ROADMAP.md) | status, sequencing, AWS reactivation summary, what is left |
| [`01-CAMPAIGN-PLAN.md`](01-CAMPAIGN-PLAN.md) | positioning, audience, message pillars, channel matrix, KPIs |
| [`02-VIDEO-SCRIPTS-AND-STORYBOARDS.md`](02-VIDEO-SCRIPTS-AND-STORYBOARDS.md) | eight finished spots, per-scene timings and voice-over |
| [`03-POSTER-GALLERY.md`](03-POSTER-GALLERY.md) | auto-index of all 38 posters |
| [`04-COPY-BANK.md`](04-COPY-BANK.md) | every headline, tier line, caption and subject line |
| [`05-ASSET-AND-PRODUCTION-GUIDE.md`](05-ASSET-AND-PRODUCTION-GUIDE.md) | folder map, commands, QA gates, pipeline notes |
| [`06-ZEELY-GROWTH-PLAYBOOK.md`](06-ZEELY-GROWTH-PLAYBOOK.md) | the zeely.ai strategy teardown, module map and AWS runtime |
| [`07-PRODUCT-FACT-SHEET.md`](07-PRODUCT-FACT-SHEET.md) | the product facts every channel copy is checked against |
| [`08-MARKETING-STUDIO.md`](08-MARKETING-STUDIO.md) | the in-app Marketing Studio at `/dashboard/marketing` — in-house engine (local compositor, SAPI voice, Bedrock plates, app AI scripts) |

## Assets at a glance

- **Brand mark** — `assets/brand/priv-mark.png` (pink diamond; `brand.py::logo_mark()` trims, gold-rings and footers it onto every asset)
- **Plates** — `assets/backgrounds/` (26, text-free — 18 campaign + 8 neon ad)
- **Posters** — `assets/posters/{feed,story,wide,link,thumb}/` (38 JPEGs)
- **Videos** — `assets/videos/` (8 MP4: 5 campaign spots + 3 Creatify-style ad spots, 5.97 s → 63.77 s)
- **Storyboards** — `assets/storyboards/<spot>/scene-NN.jpg`
- **Voice-over** — `assets/voiceover/<spot>/scene-NN.m4a` (your recorded takes; they win over the synthesized `scene-NN.wav` and set every scene length)
- **Growth pages** — `assets/pages/` (17 landing pages + `sitemap.xml`, live at `www.sansmercantile.com/growth/`)
- **Approval queue** — `assets/growth/outbox/` (owned / social / paid / outreach packs)
- **Variant ledger** — `assets/growth/ledger.json`

## Re-render

```powershell
$py = "C:\Users\kpasc\.bridge\venv\Scripts\python.exe"
cd build
& $py run_posters.py     # posters
& $py audit.py           # must print ALL CLEAR
& $py videos.py      # 5 campaign spots
& $py ads.py         # 3 Creatify-style ad spots (captions, CTA, end card)
```

## Growth agent

```powershell
# one local cycle, dry (nothing publishes)
& $py C:\Users\kpasc\.agents\skills\priv-growth-agent\scripts\run_agent.py

# deploy / update the AWS agent + EventBridge rule
& $py build\deploy_growth.py                 # live: owned=publish, rest=prepare
& $py build\deploy_growth.py --dry --no-rule # DRY_RUN=true, rule untouched
```

The agent runs unattended every 12 hours from `pr-growth-agent-schedule`.
See `06-ZEELY-GROWTH-PLAYBOOK.md` for the full runtime record.

See `05-ASSET-AND-PRODUCTION-GUIDE.md` for the full pipeline, QA gates and
the AWS reactivation record.
