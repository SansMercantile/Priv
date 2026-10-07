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
├── build/
│   ├── brand.py              design tokens, fonts, footer lock-up, grain, glow
│   ├── backgrounds.py         Bedrock plate generator + load() cover-crop loader
│   ├── posters.py             the compositor: render(), bodies, body_well()
│   ├── poster_specs.py        14 designs, tier/platform tables, scrim overrides
│   ├── run_posters.py         batch render  → assets/posters/
│   ├── audit.py               layout audit  → prints ALL CLEAR or the gaps
│   ├── probe.py               geometry probe for the signal + tiers bodies
│   ├── gallery.py             → 03-POSTER-GALLERY.md
│   ├── videos.py              scene table, TTS, Ken Burns, assemble
│   └── storyboard_table.py    → 02-VIDEO-SCRIPTS-AND-STORYBOARDS.md
└── assets/
    ├── backgrounds/           18 AI plates (text-free)
    ├── posters/{feed,story,wide,link,thumb}/   38 JPEGs
    ├── storyboards/<spot>/scene-NN.jpg         one still per scene
    ├── voiceover/<spot>/scene-NN.wav           one stem per scene
    └── videos/*.mp4           5 finished spots
```

## 2. Toolchain

| Need | What is used |
| --- | --- |
| Python | `C:\Users\kpasc\.bridge\venv\Scripts\python.exe` (Pillow 12.3, boto3) — plain `python`/`python3` are **not** installed |
| Video | ffmpeg 8.1.1 (gyan full build), on PATH as `ffmpeg` |
| Voice | Windows SAPI — `Microsoft David Desktop`, rate −1, via `System.Speech` |
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
& $py videos.py                      # all 5 spots
& $py videos.py hero-30s             # or one spot
& $py storyboard_table.py            # regenerate 02
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
| Loudness | `ffmpeg -af ebur128` | −14 to −16 LUFS integrated |
| Voice coverage | `scan.py` (temp) | non-silent in every 3 s window |

Current state: **all gates pass**. Durations — bumper 5.95 s · teaser 14.73 s ·
hero 30.15 s (both orientations) · explainer 59.16 s.

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
for fn in ("pr-content-engine", "pr-website-blog-engine"):
    cfg = lm.get_function_configuration(FunctionName=fn)
    print(fn, cfg["State"], cfg["LastUpdateStatus"])
```

## 7. Known tool caveat

The image-read tool intermittently returns a **cached image from a previous
path** — it will report success while showing the wrong file. Read a target
twice, or interleave a never-before-read path, before trusting what you see.
Contact sheets built with unique filenames sidestep it.
