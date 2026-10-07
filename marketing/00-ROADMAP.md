# 00 — Roadmap

**Campaign:** Priv — AI trading terminal by Sans Mercantile
**Site:** `https://priv.sansmercantile.com` · downloads `https://www.sansmercantile.com/priv`
**Owner pipeline:** EventBridge → Lambda content engines on AWS account `363234578752`

---

## Where the campaign stands

| Stage | State | Evidence |
| --- | --- | --- |
| Infrastructure reactivated | **done** | both EventBridge rules enabled, both Lambdas invoked successfully |
| Editorial backlog cleared | **done** | PRIV blog 52/52, Brigit 46/46 on the shared engine; Omega 18/52 continuing |
| LinkedIn queue drained | **done** | brigit 52, priv 52, omega 51, sans_mercantile 34 scheduled |
| Brand system for assets | **done** | `build/brand.py` — gold/navy/cyan, Segoe UI Black display, mono data type |
| Art direction plates | **done** | 18 AI plates, text-free, 5 landscape / 5 vertical / 8 portrait |
| Poster system | **done** | 14 designs × 1–4 formats = 38 files, layout audit `ALL CLEAR` |
| Video system | **done** | 5 spots (6 s → 59 s), voice-over, Ken Burns cut, −14 LUFS master |
| Storyboards | **done** | one still per scene, same compositor as the posters |
| Documentation | **done** | this file plus 01–05 |

---

## The six deliverables

1. **`00-ROADMAP.md`** — this file: status, sequencing, what is left.
2. **`01-CAMPAIGN-PLAN.md`** — positioning, pillars, channels, 6-week rollout, KPIs.
3. **`02-VIDEO-SCRIPTS-AND-STORYBOARDS.md`** — five finished spots with per-scene timings and voice-over.
4. **`03-POSTER-GALLERY.md`** — auto-index of all 38 posters with format, size and plate.
5. **`04-COPY-BANK.md`** — headlines, tier copy, captions, subject lines — the words the assets are built from.
6. **`05-ASSET-AND-PRODUCTION-GUIDE.md`** — folder map, how to re-render, QA gates, and the AWS reactivation record.

---

## Sequencing

**Week 0 — shipped (this pass)**

- AWS reactivation and bug fixes (below), so publishing keeps running unattended.
- Full asset factory: plates → posters → videos → storyboards → copy bank.
- Docs 00–05.

**Week 1 — publish**

- Drop the feed set (12 designs × 1080×1350) into the content engine's image slot.
- Ship `priv-hero-30s-1920x1080.mp4` as the homepage hero loop (muted, autoplay, playsinline).
- Ship `priv-teaser-15s-vertical-1080x1920.mp4` as the first paid-social cut.

**Week 2 — measure**

- Rotate the story set (12 × 1080×1920) through Reels/TikTok/Shorts.
- A/B the two strongest feed headlines: *Entry. Two targets. One stop.* vs *Prove it before you risk it.*
- Ship `priv-explainer-60s-1920x1080.mp4` to the landing page and to YouTube.

**Week 3–4 — extend**

- Localise the copy bank (the compositor takes any string; nothing is baked into art).
- Cut 6-second variants from the bumper for retargeting.
- Add a second plate batch if the first 18 saturate.

**Week 5–6 — compounding**

- Re-render posters from live campaign numbers (backtest runs, boards, signal counts) rather than static figures.
- Feed winning copy back into `poster_specs.py` so the two channels cannot drift.

---

## Infrastructure record (Week 0)

Two rules had drifted to `DISABLED`, which had silently stopped all publishing:

| Rule | Schedule | Target | Was | Now |
| --- | --- | --- | --- | --- |
| `pr-content-engine-3x-daily` | `rate(8 hours)`, input `{"phase":"articles"}` | `pr-content-engine` | DISABLED | **ENABLED** |
| `pr-website-blog-engine-schedule` | `rate(12 hours)` | `pr-website-blog-engine` | DISABLED | **ENABLED** |

Both Lambdas: `Active`, last invocation `Successful`, python3.12, 900 s timeout, 512 MB, `DRY_RUN=false`.

Two bugs were fixed and deployed so the backlog could actually drain:

1. **`github_client.py`** — files ≥ 1 MB (notably `blog-data.ts` at ~1.06 MB) could not be read or written through the Contents API. Added a Git Blobs API read fallback and a Git Data API write path (blob → tree → commit → ref update) with 409/422 retry.
2. **`lambda_function.py`** — blog images were fetched with `get_file(..., binary=True)`; without it the JPEG payload raised `UnicodeDecodeError`.

Both deployed (`CodeSha256 dFlx0kuzUKLMSY5D1Tx7QrmJy7WEdXy/8jeLeHzKejU=`). Round-trip and commit verified on throwaway branches, which were then deleted — `main` was never touched by the test.

Live scoped invoke `{"only_product":"priv"}` returned **PRIV Blog 52/52 complete**.

---

## Open items

- **Music beds.** The four voiced spots are voice-only. Drop a licensed bed under them at −22 LUFS if a platform wants music.
- **Portrait crops of the landscape videos.** Not needed yet: `hero-30s-vertical` is a real 1080×1920 render, not a crop.
- **Live data in stat rows.** `152 backtest runs` and `45 boards` are static copy today; wire them to the product API before they go stale.
- **Asset commit.** Everything under `marketing/` is written but not committed to the Priv repo — that is a deliberate choice, not an oversight.
