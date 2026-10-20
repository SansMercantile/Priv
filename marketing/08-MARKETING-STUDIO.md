# 08 — Marketing Studio

**What:** an in-house marketing engine — posters, videos, voice-over, scripts and background plates — reachable at `/dashboard/marketing` in the Priv webapp. Built to replace the competitor tooling entirely: every generation path runs on our own stack (local Pillow/ffmpeg compositor, local SAPI voice, Amazon Bedrock for images, the app's own AI provider for copy).
**Where:** `dashboard/marketing` (admin-only) · API under `/api/marketing/*` · assets under `/marketing-assets/*`
**Depends on:** `marketing/build/studio.py` (compositor + engine bridge). Nothing else.

---

## How the pieces fit

```
/dashboard/marketing  (MarketingStudio.tsx, 4 tabs)
        │
        ▼
/api/marketing/*      (server/marketing/routes.ts)
   ├─ compositor ──► server/marketing/local.ts ──► studio.py ──► Pillow + ffmpeg
   │                 (catalog / posters / videos / audit, .studio spec files)
   └─ engine ──────► generation, all in-house:
        ├─ scripts  → the app's own AI provider (Bedrock or Gemini via getAIClient)
        ├─ voice    → local SAPI synthesizer (System.Speech), same engine the ads used
        └─ plates   → Amazon Bedrock Stable Image Ultra (boto3, us-west-2)
/marketing-assets/*   static over marketing/assets (traversal-guarded)
```

No competitor API, key or MCP anywhere in the stack. Recorded voice-over takes (`scene-NN.m4a`) still win over synthesized TTS everywhere, enforced by `videos.recording()`.

---

## The four tabs

| Tab | What it does |
| --- | --- |
| **Library** | Every rendered asset — posters, custom posters, videos, storyboards, plates, brand marks — with size, open and copy-URL. |
| **Poster Studio** | Clone any of the 14 designs (or start blank), pick a plate + formats, render feed/story/wide/thumb/link instantly. Re-render all 38 and run the layout audit (`ALL CLEAR`) in one click. |
| **Video Studio** | All 8 campaign/ad spots (kind-tagged) with one-click re-render via the takes pipeline, plus a freeform JSON composer for one-off cuts (`plate/eyebrow/headline/sub/vo/hold` scenes, any size, auto-target duration). |
| **Engine** | The generation layer: **Script Writer** (hook / caption / headline / script / email via the app's AI provider), **Voice Lab** (SAPI synthesis, optionally installed as a scene take), **Plate Foundry** (one-off Bedrock plates). Status line shows which AI provider, TTS engine, plate model and renderer are live. |

---

## API reference

All routes return the house envelope `{ success, data }` (or `{ success: false, error, detail }`).

### Compositor

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/marketing/catalog` | formats, 26 plates, 14 poster designs, 8 spots (5 campaign + 3 ad), voices, plate ratios/styles, body kinds, brand colours |
| GET | `/api/marketing/library?kind=` | one folder or all (`posters`, `posters/custom`, `videos`, `storyboards`, `backgrounds`, `brand`) |
| GET | `/api/marketing/file?path=` | validated single-file stream (400 on any `..`) |
| POST | `/api/marketing/posters/render` | `{ spec }` → clones `template` if given, writes `posters/custom/priv-{slug}-{stamp}-{fmt}.jpg` |
| POST | `/api/marketing/posters/slug` | `{ slug, formats? }` re-render one shipped design |
| POST | `/api/marketing/posters/rerender` | `{ slug? }` → the full `run_posters.py` pass, log echoed |
| POST | `/api/marketing/posters/audit` | layout audit; `clear: true` ⇔ `ALL CLEAR` |
| POST | `/api/marketing/videos/render` | `{ spot }` for campaign spots (`videos.py`, takes pipeline) |
| POST | `/api/marketing/ads/render` | `{ spot }` for `ad-hook-15s` / `ad-proof-30s` / `ad-desk-15s` (`ads.py`, −13 LUFS) |
| POST | `/api/marketing/videos/custom` | `{ spec }` → freeform multi-scene cut |

### Engine (all in-house)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/marketing/engine/status` | `{ python, ai:{provider,ready}, tts:{engine}, plates:{provider,model,region} }` |
| POST | `/api/marketing/engine/script` | `{ kind, topic, detail? }` — kinds: `hook`, `caption`, `headline`, `script`, `email`. Talks to whichever AI provider the server already has wired (Bedrock or Gemini); no separate studio credential. |
| POST | `/api/marketing/engine/tts` | `{ spec:{ text, voice?, rate?, install?:{spot,scene} } }` — local SAPI synthesis. Draft lands in `voiceover/generated/`; `install` writes the take (`voiceover/<spot>/scene-NN.m4a`) the compositor uses on the next render. |
| POST | `/api/marketing/engine/plate` | `{ prompt, ratio?, style?, slug? }` — one-off plate via Amazon Bedrock Stable Image Ultra (`stability.stable-image-ultra-v1:1`, us-west-2). `style`: `campaign` | `ads` | a raw style string. Falls back to the procedural brand gradient if Bedrock is unreachable. |
| GET | `/api/marketing/health` | `{ ok, engine:"in-house", python, assets }` |

---

## The engine's own stack

| Capability | Provider | Notes |
| --- | --- | --- |
| Poster + video compositing | local Pillow + ffmpeg | same code path as `run_posters.py` / `videos.py` / `ads.py`; masters land in the documented folders |
| Script / copy writing | the app's AI provider | reuses `getAIClient()` from `server.ts` (AWS Bedrock if configured, else Gemini via API key or Vertex ADC). One credential path for the whole app. |
| Voice-over | local SAPI (`System.Speech`) | the same synthesizer the ads were cut with (`tts.ps1`); voices: David (default), Zira, Hazel, Mark. Drafts + optional take-install. |
| Background plates | Amazon Bedrock Stable Image Ultra | `boto3` in `backgrounds.py::generate_one`; the same model that produced the 26 campaign plates. |

To make the script writer live, either set a valid `GEMINI_API_KEY` or AWS Bedrock credentials (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` + `BEDROCK_REGION`) in the server's environment — whichever provider the rest of the app uses. Voice and plates need only the Python venv and AWS creds that already render the campaign.

---

## Local renderer notes

- Interpreter: `PRIV_PYTHON` env or `C:\Users\kpasc\.bridge\venv\Scripts\python.exe`; run timeout `STUDIO_TIMEOUT_MS` (default 15 min — a full re-render pass needs minutes, not seconds).
- Specs are written to `marketing/build/.studio/spec-*.json` and read with `utf-8-sig`; renderers capture their own stdout into the returned `log`.
- Custom posters inherit every field of the cloned template; body blocks accept the eight kinds (`signal`, `chips`, `bullets`, `stats`, `tiers`, `platforms`, `agents`, `notify`) — tuples are normalised server-side (`_normalise_body`).
- Masters land exactly where the docs say: `assets/videos/priv-{spot}-*.mp4`, `assets/posters/…`, `assets/posters/custom/…` — the Library tab and `/marketing-assets/*` pick them up on refresh.
- Security: `/marketing-assets` is a static mount with `index: false`; the `/file` endpoint rejects any path outside `marketing/assets` (verified: `..%2F..%2Fpackage.json` → 400).

---

## Verified

- `npm run lint` (tsc) and `npm run build` (vite + esbuild, `dist/server.cjs` bundles the studio) pass.
- Live smoke test: `/health` → `engine:"in-house"`, `python:true`, `assets:true`; catalog → 5 formats · 26 plates · 14 posters · 8 spots (5 campaign + 3 ad) · 4 voices; library → 8 videos listed; poster render via `POST /posters/render` produced `feed` + `story` JPEGs served at `/marketing-assets/posters/custom/…` (HTTP 200, `image/jpeg`); traversal blocked (400).
- Engine: `GET /engine/status` → `ai.provider:"Google Gemini"`, `tts.engine:"local SAPI"`, `plates.provider:"Amazon Bedrock"`. `POST /engine/tts` → 2.54 s clip (wav + m4a). `POST /engine/plate` → 11.9 s Bedrock render (`gen-beam-http-*.jpg`). `POST /engine/script` correctly surfaces the upstream provider error when the configured key is invalid.
