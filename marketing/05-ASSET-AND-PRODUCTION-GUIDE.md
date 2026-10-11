# 05 — Asset and production guide

How the campaign folder is built, what to run to change it, and the record of
the AWS reactivation that got publishing moving again.

---

## 1. Folder map

```
marketing/
├── 00-ROADMAP.md
├── 01-CAMPAIGN-PLAN.md
├── 02-VIDEO-SCRIPTS-AND-STORYBOARDS.md
├── 03-POSTER-GALLERY.md
├── 04-COPY-BANK.md
├── 05-ASSET-AND-PRODUCTION-GUIDE.md
├── 06-ZEELY-GROWTH-PLAYBOOK.md   zeely.ai teardown + growth runtime record
├── build/
│   ├── brand.py              design tokens, fonts, footer lock-up, grain, glow
│   ├── backgrounds.py        Bedrock plate generator + load() cover-crop loader
│   ├── posters.py            the compositor: render(), bodies, body_well()
│   ├── poster_specs.py       14 designs, tier/platform tables, scrim overrides
│   ├── run_posters.py        batch render  → assets/posters/
│   ├── audit.py              layout audit  → prints ALL CLEAR or the gaps
│   ├── probe.py              geometry probe for the signal + tiers bodies
│   ├── gallery.py            → 03-POSTER-GALLERY.md
│   ├── videos.py             scene table, TTS, Ken Burns, assemble
│   ├── ads.py                Creatify-style spots: captions, CTA, end card, -13 LUFS
│   ├── storyboard_table.py   → 02-VIDEO-SCRIPTS-AND-STORYBOARDS.md
│   ├── deploy_growth.py      zip + IAM + create/update pr-growth-agent + rule
│   └── growth/               the Zeely growth agent package
│       ├── stats.py          verified facts, guard(), risk disclaimer
│       ├── hooks.py          130+ hooks, 8 frameworks, score(), safe_area_lines()
│       ├── experiments.py    variant matrix, predict(), select(), ledger
│       ├── pages.py          17-page CATALOG, render(), JSON-LD, sitemap
│       ├── social.py         6 platforms, calendar(), carousel(), disclosure
│       ├── paid.py           Meta/TikTok briefs, always PAUSED, >=3 variants
│       ├── outreach.py       press, affiliates, creators — drafts only
│       ├── channels.py       mode gates, GitHub/SSM/S3 publish
│       ├── agent.py          plan() / run() / report_line() / hydrate from S3
│       └── lambda_function.py  AWS entrypoint (parks state in /tmp)
└── assets/
    ├── brand/priv-mark.png      THE mark (pink diamond) — brand.py::logo_mark()
    │                             trims its margin, adds the gold ring, footers it
    ├── backgrounds/           26 AI plates (text-free: 18 campaign + 8 neon ad)
    ├── posters/{feed,story,wide,link,thumb}/   38 JPEGs
    ├── storyboards/<spot>/scene-NN.jpg         one still per scene
    ├── voiceover/<spot>/scene-NN.{wav,m4a}   one stem per scene
    │                             .m4a = hand-recorded take (wins over the TTS .wav),
    │                             silence-trimmed into assets/.frames/ on first use
    ├── videos/*.mp4           8 finished spots (5 campaign + 3 ad)
    ├── pages/                 17 landing pages + sitemap.xml (live on the site)
    └── growth/
        ├── outbox/            approval queue: owned/social/paid/outreach JSON
        └── ledger.json        shared A/B variant ledger (mirrored to S3)
```

## 2. Toolchain

| Need | What is used |
| --- | --- |
| Python | `C:\Users\kpasc\.bridge\venv\Scripts\python.exe` (Pillow 12.3, boto3) — plain `python`/`python3` are **not** installed |
| Video | ffmpeg 8.1.1 (gyan full build), on PATH as `ffmpeg` |
| Voice | Windows SAPI — `Microsoft David Desktop`, rate −1, via `System.Speech`; a recorded `scene-NN.m4a` in the same folder wins over the synthesized `.wav` |
| Art | AWS Bedrock `stability.stable-image-ultra-v1:1` in `us-west-2` |
| Fonts | `seguibl.ttf` (display) · `segoeuib/b.ttf` · `consola/b.ttf` (mono) — all from `C:\Windows\Fonts\` |

### Brand tokens

`gold #d4af37` · `dark #0a0e27` · `cyan #00d4ff` · `purple #7c3aed` ·
`muted rgb(148,163,184)` · green `#34d399` · rose `#fb7185`

## 3. Commands

```powershell
$py = "C:\Users\kpasc\.bridge\venv\Scripts\python.exe"
cd C:\Users\kpasc\source\repos\Priv\marketing\build

& $py run_posters.py                 # render all 38 posters
& $py run_posters.py pricing launch  # or just some
& $py audit.py                       # layout gate -> ALL CLEAR
& $py probe.py                       # geometry probe
& $py gallery.py                     # regenerate 03
& $py videos.py                      # all 5 campaign spots
& $py videos.py hero-30s             # or one spot
& $py ads.py                         # all 3 Creatify-style ad spots
& $py ads.py ad-hook-15s             # or one ad spot
& $py storyboard_table.py            # regenerate 02
& $py deploy_growth.py               # deploy the growth agent to AWS
```

Plates are already generated; `backgrounds.py` only calls Bedrock if a file is
missing, so a re-render never costs image credits.

## 4. QA gates

| Gate | Command | Pass condition |
| --- | --- | --- |
| Layout | `audit.py` | `ALL CLEAR` — no headline/sub/body/CTA/footer overlap, no body overflow past `avail` |
| Geometry | `probe.py` | `probe ok` — signal ticket and tier cards inside their bounds |
| File count | `gallery.py` | `38 files, 14 designs` |
| Video integrity | `ffprobe` | correct W×H, `h264` + `aac`, expected duration |
| Loudness | `ffmpeg -af ebur128` | −13.5 to −14.5 LUFS (campaign spots) · −13.0 to −13.5 LUFS (ad spots) |
| Voice coverage | `scan.py` (temp) | non-silent in every 3 s window, and speech inside every voiced scene |
| Takes | build log | every voiced scene prints `[take m4a trimmed …]`, never `[tts]` |
| Mark | pixel probe on the footer band | pink diamond + gold ring present, no carnation |

Current state: **all gates pass**. Durations — bumper 5.97 s (ships silent) ·
teaser 15.87 s · hero 29.73 s (both orientations) · explainer 63.77 s ·
ad-hook 16.00 s · ad-proof 33.30 s · ad-desk 19.10 s. Lengths are now set by
the recorded takes, so spots run slightly past their nominal targets rather
than clipping a line; see `02` for the per-scene numbers.

## 5. Pipeline notes (hard-won)

These are the failure modes that actually bit during this build. They are
encoded in the code as comments; listed here so nobody re-discovers them.

1. **`ImageDraw.Draw(im, "RGBA")` on an RGBA image does not alpha-blend.**
   It writes raw pixels. Verified directly: fill `(52,211,153,46)` over
   `(8,12,34,255)` returned `(52,211,153,46)`. Every translucent shape must be
   drawn on a transparent overlay and composited with
   `base.alpha_composite(overlay)` — which is why `render()` builds `ov` and
   `b_ov`. Skip this and the "LIVE" pill, gold chips and card fills vanish or
   go opaque.
2. **`darken()` scrim values are brightness multipliers**, not darkness.
   `out = im * v`. Raising the bottom value *lightens* the image.
   `scrim_bottom: 0.40` = darker than `0.50`.
3. **`body_well()` runs on the base plate, not the text overlay.** It is
   applied after the body is measured but before `im.alpha_composite(ov)`, so
   the 32 px Gaussian blur can never dim or erase a glyph — including the
   sub-head that sits above it.
4. **Font metrics under-report ink.** `ImageFont.getmetrics()` lies for
   display faces; `headline()` and `subhead()` return their true ink bottom
   from `ImageDraw.textbbox` (+4 px for the gradient pass).
5. **Stat labels shrink to fit.** `_fit_mono()` walks the mono label down until
   its tracked width fits inside its cell — without it, `STRATEGY BOARDS`
   collides with `TIMEFRAMES`.
6. **A real 1080×1920 render beats a crop.** `hero-30s-vertical` re-renders
   the hero scenes at portrait size rather than letterboxing the landscape cut.

## 6. AWS reactivation record

**Account** `363234578752` · **user** `mezzoforte@sansmercantile.com` ·
**region** `us-east-1` · no local AWS CLI; all calls via boto3 from the bridge venv.

### What was wrong

Both publishing schedules had drifted to `DISABLED`, so nothing had shipped
even though the Lambdas themselves were healthy.

### What was changed

```python
events.enable_rule(Name="pr-content-engine-3x-daily")      # rate(8h)  -> pr-content-engine
events.enable_rule(Name="pr-website-blog-engine-schedule")  # rate(12h) -> pr-website-blog-engine
```

| Rule | Schedule | Input | State |
| --- | --- | --- | --- |
| `pr-content-engine-3x-daily` | `rate(8 hours)` | `{"phase":"articles"}` | ENABLED |
| `pr-website-blog-engine-schedule` | `rate(12 hours)` | — | ENABLED |

Both Lambdas `Active`, last invocation `Successful`, python3.12, 900 s, 512 MB,
env `DRY_RUN=false`.

### Code fixes deployed

| File | Fix |
| --- | --- |
| `pr_website_blog_engine/github_client.py` | Git Blobs API fallback for reads > 1 MB (`blog-data.ts` ≈ 1.06 MB); new `_put_large_file()` Git Data API write (blob → tree → commit → ref) with 409/422 retry, used by `put_text_file` / `put_binary_file` at ≥ 1,000,000 bytes |
| `pr_website_blog_engine/lambda_function.py` | `gh.get_file(path, binary=True)` for blog images — fixed `UnicodeDecodeError` on JPEG payloads |

Deployed as `CodeSha256 dFlx0kuzUKLMSY5D1Tx7QrmJy7WEdXy/8jeLeHzKejU=`.

### Verification

- Round-trip and commit tested on **throwaway branches**, then deleted.
  `main` was never modified by the test.
- Live scoped invoke `{"only_product":"priv"}` → **PRIV Blog 52/52 complete**.
  Brigit 46/46. Omega 18/52 and climbing on the 12 h schedule.
- LinkedIn backlog drained: brigit 52 · priv 52 · omega 51 · sans_mercantile 34.
  The engine auto-chains to its `images` phase when `articles` returns zero actions.

### Verify it is still healthy

```python
import boto3
ev = boto3.client("events", region_name="us-east-1")
print([r["State"] for r in ev.list_rules()["Rules"]
       if r["Name"] in ("pr-content-engine-3x-daily",
                        "pr-website-blog-engine-schedule")])
# -> ['ENABLED', 'ENABLED']

lm = boto3.client("lambda", region_name="us-east-1")
for fn in ("pr-content-engine", "pr-website-blog-engine", "pr-growth-agent"):
    cfg = lm.get_function_configuration(FunctionName=fn)
    print(fn, cfg["State"], cfg["LastUpdateStatus"])

ev = boto3.client("events", region_name="us-east-1")
print(ev.describe_rule(Name="pr-growth-agent-schedule")["State"])
# -> ENABLED
```

Growth agent health: read the newest report from `s3://pr-growth-agent/reports/`
— `blocked_by_compliance` must be `0`.

## 7. Known tool caveat

The image-read tool intermittently returns a **cached image from a previous
path** — it will report success while showing the wrong file. Read a target
twice, or interleave a never-before-read path, before trusting what you see.
Contact sheets built with unique filenames sidestep it.
