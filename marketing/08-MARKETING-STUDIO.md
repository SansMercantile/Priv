# 08 — Marketing Studio

**What:** an in-house marketing engine — posters, videos, voice-over, scripts, background plates, animated/doodle/presenter ads, URL-to-video, image/product-photo editing, and consent-gated voice cloning — reachable at `/dashboard/marketing` in the Priv webapp. Built to cover the competitor's (Creatify's) feature surface entirely on our own stack: local Pillow/ffmpeg compositor, our own AWS GPU box (AnimateDiff + MuseTalk), Amazon Bedrock for images, the app's own AI provider for copy.
**Where:** `dashboard/marketing` (admin-only) · API under `/api/marketing/*` · assets under `/marketing-assets/*`
**Depends on:** `marketing/build/studio.py` (compositor + engine bridge) and the AWS GPU box. Nothing else.

---

## How the pieces fit

```
/dashboard/marketing  (MarketingStudio.tsx, 4 tabs)
        │
        ▼
/api/marketing/*      (server/marketing/routes.ts, GPU work serialised by a mutex)
   ├─ compositor ──► server/marketing/local.ts ──► studio.py ──► Pillow + ffmpeg
   │                 (catalog / posters / videos / audit, .studio spec files)
   └─ engine ──────► generation, all in-house:
        ├─ scripts      → the app's own AI provider (Bedrock or Gemini via getAIClient)
        ├─ voice        → local SAPI; + voice cloning (Chatterbox MIT / XTTS in-house) on the GPU box
        ├─ plates       → Amazon Bedrock Stable Image Ultra (boto3, us-west-2)
        ├─ images       → Bedrock edit models (remove-bg / inpaint / outpaint / style-transfer)
        ├─ creative ads → cartoon (AnimateDiff) + doodle (local) + presenter (MuseTalk) on the A10G
        └─ url-to-video → scrape page → AI script → creative render
/marketing-assets/*   static over marketing/assets (traversal-guarded)
```

No competitor API, key or MCP anywhere in the stack. Recorded voice-over takes (`scene-NN.m4a`) still win over synthesized TTS everywhere, enforced by `videos.recording()`. Licence rules are enforced in code: Wav2Lip/XTTS-style non-commercial models are never used for client-facing output.

---

## The four tabs

| Tab | What it does |
| --- | --- |
| **Library** | Every rendered asset — posters, custom posters, videos, storyboards, plates, brand marks — with size, open and copy-URL. |
| **Poster Studio** | Clone any of the 14 designs (or start blank), pick a plate + formats, render feed/story/wide/thumb/link instantly. Re-render all 38 and run the layout audit (`ALL CLEAR`) in one click. |
| **Video Studio** | All campaign/ad spots (kind-tagged) with one-click re-render via the takes pipeline, plus a freeform JSON composer for one-off cuts. |
| **Engine** | The generation layer: **Script Writer** (hook / caption / headline / script / email), **Voice Lab** (SAPI synthesis + take-install), **Plate Foundry** (one-off Bedrock plates), **URL-to-Video** (paste a link → rendered ad), **Creative Ad Lab** (cartoon / doodle / presenter 1-minute ads, MusicGen score). Status line shows AI provider, TTS engine, plate model, renderer, creative styles and the GPU instance. |

---

## API reference

All routes return the house envelope `{ success, data }` (or `{ success: false, error, detail }`).

### Compositor

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/marketing/catalog` | formats, plates, poster designs, spots, voices, plate ratios/styles, body kinds, creative styles, url2video + music-bed flags, brand colours |
| GET | `/api/marketing/library?kind=` | one folder or all (`posters`, `posters/custom`, `videos`, `storyboards`, `backgrounds`, `brand`) |
| GET | `/api/marketing/file?path=` | validated single-file stream (400 on any `..`) |
| POST | `/api/marketing/posters/render` | `{ spec }` → clones `template` if given |
| POST | `/api/marketing/posters/slug` | `{ slug, formats? }` re-render one shipped design |
| POST | `/api/marketing/posters/rerender` | `{ slug? }` → the full `run_posters.py` pass |
| POST | `/api/marketing/posters/audit` | layout audit; `clear: true` ⇔ `ALL CLEAR` |
| POST | `/api/marketing/videos/render` | `{ spot }` for campaign spots (`videos.py`, takes pipeline) |
| POST | `/api/marketing/ads/render` | `{ spot }` for the caption-led ad spots (`ads.py`, −13 LUFS) |
| POST | `/api/marketing/videos/custom` | `{ spec }` → freeform multi-scene cut |

### Engine (all in-house)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/marketing/engine/status` | `{ python, ai, tts, plates, creative:{styles, gpu, musicBed, url2video} }` |
| POST | `/api/marketing/engine/script` | `{ kind, topic, detail? }` — kinds: `hook`, `caption`, `headline`, `script`, `email`. App's own AI provider. |
| POST | `/api/marketing/engine/tts` | `{ spec:{ text, voice?, rate?, install? } }` — local SAPI; `install` writes a take the compositor uses. |
| POST | `/api/marketing/engine/plate` | `{ prompt, ratio?, style?, slug? }` — one-off plate via Bedrock Stable Image Ultra. |
| POST | `/api/marketing/engine/creative` | `{ style: cartoon|doodle|presenter, scenes:[...], size?, target?, avatar? }` → a mastered ad. **Mutex-gated.** Presenter takes `avatar` and stamps the AI-disclosure. |
| POST | `/api/marketing/engine/url2video` | `{ url, style?, scenes? }` → scrape the page → AI-drafted compliance-gated scene script → creative render. **Mutex-gated.** |
| POST | `/api/marketing/engine/image` | `{ op, ... }` — Bedrock edit models: `remove_background` / `inpaint` / `outpaint` / `erase_object` / `style_transfer` / `generate` / `product_shot`. |
| POST | `/api/marketing/engine/voiceclone` | `{ path: client|inhouse, text, ref, consent, name? }` — `client`=Chatterbox (MIT, watermarked, client-facing); `inhouse`=XTTS v2 (**NON-COMMERCIAL**, internal only). `consent` is mandatory. **Mutex-gated.** |
| GET | `/api/marketing/health` | `{ ok, engine:"in-house", python, assets }` |

---

## The engine's own stack

| Capability | Provider | Notes |
| --- | --- | --- |
| Poster + video compositing | local Pillow + ffmpeg | same code path as `run_posters.py` / `videos.py` / `ads.py` |
| Script / copy writing | the app's AI provider | reuses `getAIClient()` (Bedrock or Gemini); one credential path |
| Voice-over (TTS) | local SAPI (`System.Speech`) | David (default), Zira, Hazel, Mark; drafts + take-install |
| Voice cloning | Chatterbox (client) / XTTS v2 (in-house) | on the GPU box; consent-gated; non-commercial models never ship |
| Background plates | Amazon Bedrock Stable Image Ultra | `backgrounds.py::generate_one`, us-west-2 |
| Image editing | Bedrock edit models | remove-background / inpaint / outpaint / erase-object / style-transfer |
| Animated ads (cartoon) | AnimateDiff + SD1.5 | on our A10G GPU via diffusers |
| Talking presenter | MuseTalk 1.5 | on the A10G; synthetic Bedrock face; **not** Wav2Lip (non-commercial) |
| Doodle / whiteboard ads | local Pillow (deterministic) | no model needed |
| Music bed | MusicGen (own T4 box) | ducked under the VO; degrades to VO-only if unreachable |
| GPU orchestration | SSM + S3 shuttle | `engine_runtime.py`; transient-failure retry; renders serialised via a server-side mutex |

---

## GPU box

The creative engine renders on our own EC2 GPU instance (the A10G, `mezzo-wav2lip-render`). Root volume expanded 160 GB → 250 GB (the recurring disk wall is gone). A stopped `wav2lip-render-dedicated` (T4) is kept as a spare. A `musicgen-dedicated` (T4) serves background scores (`POST /invocations`, SageMaker TorchServe). All heavy renders serialise through a server-side promise-chain mutex so one job runs at a time.

**Self-healing:** the boxes' snap `amazon-ssm-agent` used to wedge under load (ConnectionLost, needed an EC2 reboot). A cron watchdog (`marketing/build/ssm_agent_watchdog.sh`, installed on both boxes) now detects a dead/wedged agent locally and restarts the snap service within ~60s — proven live (stopped the agent, watchdog restarted it and SSM came back Online unaided). Restarts log to `/var/log/ssm-watchdog.log`.

---

## Verified

- `npm run lint` + `npm run build` pass.
- Full ad library rendered in-house: 3 styles (cartoon/doodle/presenter) × 2 orientations (9:16/16:9) × 2 lengths (15s/60s) + a second objection-handler angle — all ~-13.4 LUFS, house voice, compliance-gated.
- Voice cloning: Chatterbox client clone (watermarked) and XTTS in-house clone (non-commercial warning printed) both render on the GPU box.
- URL-to-video: `studio.py urlbrief` reduces a live page to a creative brief; the API drafts the scene script with the app's AI provider and renders it.
