# 06 — Zeely Growth Playbook

Research teardown of **Zeely.ai** (`zeely.ai` — "AI Marketing Intelligence Platform",
founded 2022 Ukraine, 2M+ claimed users, $1M from Deel 2026, Meta Business Partner),
and exactly how each of their plays is implemented inside the Priv growth engine
(`build/growth/`).

Everything below is implemented in code unless marked **[not built]**.

---

## 1. Positioning: own a category name, not a feature list

Zeely stopped calling itself an "ad generator" and rebranded to
**"AI Marketing Intelligence Platform"** (their pressroom media kit literally
lists `Category: AI Marketing Intelligence Platform`).

*Why it works:* a category name lets you set the comparison set, own the
definition, and get written up as "the first/only" rather than "another AI ad tool".

**Priv version** → `stats.CATEGORY = "Autonomous trading desk"` and every page
opens with the same three-word definition. Implemented in `growth/pages.py`
(`<meta name="description">`, JSON-LD `applicationCategory`, hero eyebrow).

## 2. The full-cycle story: create → launch → scale

Every Zeely surface maps to one of three verbs:

| Verb | Zeely | Priv growth engine |
|---|---|---|
| **Create** | URL → product card → creative batches | `hooks.py` + `experiments.py` → copy, ads, pages |
| **Launch** | one-click Meta campaigns, 1–6h review | `paid.py` + `channels.py` |
| **Scale** | rank by CTR/CPA/ROAS, kill fatigue | `experiments.py` ledger → `select()` |

`growth/agent.py::plan()` returns actions tagged `create` / `launch` / `scale`
and always spends budget on **at least one of each per run** — that is the whole
loop in one sentence.

## 3. Proof stack: every paragraph carries a number

Zeely repeats the same ~10 numbers on every page: `2M+ users`, `650k+ sellers`,
`2,000+ industries`, `$1B+ in tested templates`, `+318% sales growth`,
`2× lower CPC`, `167% higher conversion on hooked videos`, `20× cheaper`,
`97% faster`, `1–6h Meta review vs 24h`, `6× YoY`.

**Implemented:** `growth/stats.py` — a claims registry where **no number may be
emitted without a `source` and a `verified` flag**.

```python
STATS["timeframes"] = dict(value="7", label="timeframes per market",
                           source="Landing.tsx + product UI", verified=True)
```

*The compliance twist Zeely does not have:* Priv is a trading product, so
`stats.guard(text)` also rejects risk-hiding language before anything ships:

```
BANNED = ["guaranteed", "risk-free", "no risk", "always wins", "99% win",
          "double your money", "profit", "passive income", "can't lose", ...]
```

Every generated asset runs through `guard()`; violations abort the action.

## 4. Copy frameworks sold as product features

Zeely's AI CMO page lists them by name: **AIDA, PAS, Before-After-Bridge, 4U,
FAB, Problem-Solution, Three Reasons Why** — plus "130+ smart hook formats".

**Implemented:** `growth/hooks.py::FRAMEWORKS` with `write(framework, **facts)`
returning `{hook, body, cta, full}`.

```
PAS  → problem / agitate / solve
AIDA → attention / interest / desire / action
BAB  → before / after / bridge
4U   → useful / urgent / unique / ultra-specific
FAB  → feature / advantage / benefit
3R   → three reasons why
HBC  → Zeely's own hook → body → CTA video structure
```

## 5. First-3-seconds doctrine

Zeely: *"first-3-seconds optimization"*, *"safe zones, pacing"*, *"insert a
3-sec opener proven to double CTR"*, *"hook headlines with emoji + font/color
controls kept inside the safe area"*.

**Implemented:**

* `hooks.score(text)` → 0–100 **first-3-seconds score**: length (≤9 words wins),
  opens with a question/number/contrast, second-person pronoun, specificity,
  power word, no brand name in line 1.
* `pages.py` + `social.py` put hook text **above the fold and inside safe zones**
  (9:16 captions stay between 14% and 84% height — see `build/ads.py` caption
  block anchor `h - 0.155h`).
* `experiments.py` treats hook as the highest-weight factor in the matrix.

## 6. Batch + "test at least 3" doctrine

Zeely repeats it on every page: *"A/B test at least 3 creatives — mixing static
and video"*, *"Batch Mode generates up to 20"*, *"one product → 100+ templates"*.

**Implemented:** `experiments.matrix(base, factors, limit=20)` builds the
hook × headline × CTA × format grid, scores each, and picks the top `N`
spanning **at least 2 formats** (static + video) exactly as Zeely prescribes.

## 7. Programmatic SEO: one page per job-to-be-done

Zeely owns a landing page for every phrase a buyer might type:
`ai-ad-generator`, `ugc-video-ad-creator`, `url-to-video-ad-maker`,
`ai-marketing-video-maker`, `ai-cmo`, `ai-employee`, `ai-youtube-video-ad-maker`,
`social-media-ad-maker`, `automated-ad-creation`, `ai-batch-mode`, `pressroom`.

**Implemented:** `growth/pages.py::CATALOG` — the same treatment for Priv:

```
feature/     signals · strategy-lab · autotrader · alerts · custody · platforms
compare/     priv-vs-manual-trading · priv-vs-copy-trading · priv-vs-raw-signal-group
usecase/     swing-trader · prop-firm-desk · night-shift · part-time-trader
tool/        backtest-explainer · timeframe-picker · risk-calculator   [briefs only]
affiliate/   partners
press/       media-kit · releases
trust/       reviews · security
```

Each page emits: brand-token CSS, hero + proof block, **Before/After table**,
FAQ block, CTA, risk disclaimer, `og:`/`twitter:` cards, and JSON-LD
(`SoftwareApplication` + `FAQPage`). `pages.build_all()` also writes `sitemap.xml`.

## 8. Comparison + pricing teardowns

Zeely's blog runs `how-much-does-zeely-cost-in-2026`, `zeely-pricing` teardowns,
and competitor comparisons; Creatify publishes `zeely-pricing-(2026)`. They trade
shots. It works: the pricing-teardown SERP is where high-intent buyers land.

**Implemented:** `pages.py::CATALOG["compare"]` with a `vs` block and an honest
"where Priv is not the right tool" section (Zeely's own pages never admit this —
their Trustpilot negatives show what happens when the page over-promises).

## 9. Review flywheel

Observed: **4,077 Trustpilot reviews, 4.3 score, 65% five-star**, *every* review
on the 4-star filter labelled **"Invited"**, and a banner **"Replied to 98% of
negative reviews, typically within 24 hours."**

**Implemented:** `growth/outreach.py`

* `invite_email()` — plain-language review invite (no incentives: that violates
  Trustpilot's guidelines and is exactly what gets companies penalised).
* `respond(review, sentiment)` — positive / neutral / negative drafts that
  **answer the specific complaint, no canned text**, matching Zeely's 98% rule.
* `proof_wall()` — pulls verified reviews into a `trust/reviews` page.

## 10. Partnership badges + press

Zeely leans on **Meta Business Partner** ("reviews clear in 1–6h vs 24h") and
floods tech press: TechUkraine, Dealroom, ain.ua, Deel $1M announcement.

**Implemented:** `outreach.py::media_kit()` (boilerplate, founder story, facts,
logo usage) and `outreach.py::press_release()` (headline / subhead / dateline /
quotes / stats / boilerplate). `pages.py` renders `press/media-kit`.

## 11. Influencer + affiliate

Zeely sponsors YouTube reviews with an exclusive trial link
(`Software Scope`, `Moe Lueker` — "7 days free through the creator's link") and
runs blog content on *affiliate marketing automation*.

**Implemented:** `outreach.py::affiliate_kit()` — tier list, commission terms,
90-day cookie, swipe copy (email / X / YouTube description / Discord), and a
tracking link format `priv.sansmercantile.com/?via=<creator>`.

## 12. Paid social saturation

"I keep seeing ads for them" (r/shopify) — Zeely runs its own product as its
acquisition loop, plus retargeting on Meta and TikTok.

**Implemented:** `growth/paid.py::campaign()` builds the brief and
`meta_payload()` / `tiktok_payload()` emit Marketing API shaped JSON;
`channels.py::publish_paid()` only fires when `META_ACCESS_TOKEN` (or
`TIKTOK_ACCESS_TOKEN`) is present **and** `CH_PAID=publish`. Default is
`prepare` — the engine will never spend money unattended.

**Honest constraint:** Meta restricts financial-services advertising. `paid.py`
runs `stats.guard()` on every copy and rejects anything with performance
claims; the brief is written for **broker-tools / education** positioning, not
income claims. Budget, geo and age gates are mandatory fields.

## 13. Pricing psychology

Zeely: struck-through anchor (`$49.95 → $29.95`), **"Most popular"** on the
middle tier, paid trials that auto-renew to Growth, an add-on **Booster** that
cuts a %-of-spend fee, weekly billing options.

**Priv version (honest variant):** `Landing.tsx` tiers `Free / $29 / $79 /
$149 / $199` get the same anchor-and-highlight treatment in `pages.py`
(`<mark class="popular">`), **but no auto-renew trap and no %-of-spend fee** —
which the comparison page says out loud, because the Zeely billing complaints
are the single loudest negative in their review corpus.

## 14. Plain-language reporting

Zeely's design rules, verbatim: *"Marketing screens should be easy to explain
to a 7th grader"*, *"Numbers that show performance matter more than fancy
labels"*, *"a limited set of metrics and avoids cluttered dashboards"*.

**Implemented:** the agent's run report exposes exactly five numbers —
`created`, `published`, `ctr`, `best_hook`, `blocked_by_compliance` — and
`experiments.explain()` returns one 7th-grader sentence per variant.

## 15. Before/After tables

Zeely's About page ships a literal `Before Zeely | With Zeely` table. Cheap,
and it converts.

**Implemented:** `pages.py::before_after(rows)` renders the same block on every
feature and comparison page.

## 16. Founder/team narrative + vision teasing

Zeely: *"engineers write over 60% of code with AI"*, *"our own marketing runs
through the same agentic workflows we sell to users"*, and "Zeely 2.0 agentic
layer coming" used to drive press and the Deel win.

**Priv version:** this engine *is* the story — `press/founder-note` template
opens with "the marketing that promotes Priv is written, rendered and scheduled
by Priv's own agent on AWS". `outreach.py::founder_note()`.

## 17. Community seeding — and how not to do it

Zeely gets posted about constantly on r/shopify, r/ecommerce, r/EtsySellers,
r/AskAIapp. The threads are **50/50 and often brutal**: trial billing, credit
drain, "AI works terribly", moderation gate, 12% fee opacity.

**Lesson encoded:** `social.py` *never* astroturfs. `post()` refuses
`platform="reddit"` unless `disclose=True`, and prepends the required
`[I built this]` disclosure. `stats.guard()` blocks the exact phrases that
generate Zeely's one-star reviews: hidden fees, "free trial", "cancel anytime"
without the terms.

## 18. The five things Zeely gets wrong (we skip all of them)

| Zeely failure mode | Evidence | How Priv avoids it |
|---|---|---|
| Trial → forced renewal | Trustpilot 1-star cluster, r/EtsySellers | No paid trial; Free tier is free |
| Opaque %-of-spend fee | 12% / 6% Booster, Terms 4.11 ambiguity | Published flat pricing only |
| Credits drain, renders stuck | 6/74 review sources | No credit metering on owned channels |
| Output quality misses | 16/74 "AI-looking ads" | Every asset passes `audit.py`/`guard()`/brand tokens |
| Canned support replies | "AI bots, no real customer service" | `respond()` must quote the reviewer's specific issue |

---

## Module map

| Module | Zeely primitive | Key functions |
|---|---|---|
| `stats.py` | proof stack + claims | `STATS`, `line()`, `guard()` |
| `hooks.py` | 130+ hooks, AIDA/PAS/… | `generate()`, `write()`, `score()` |
| `experiments.py` | Batch Mode + A/B | `matrix()`, `select()`, `record()`, `explain()` |
| `pages.py` | programmatic SEO | `build_all()`, `render(kind, spec)` |
| `social.py` | organic posting + trends | `post()`, `calendar()`, `carousel()` |
| `paid.py` | Meta/TikTok launch | `campaign()`, `meta_payload()`, `tiktok_payload()` |
| `outreach.py` | reviews/press/affiliate | `respond()`, `media_kit()`, `affiliate_kit()` |
| `channels.py` | the launcher | `publish()` per channel, all DRY_RUN-gated |
| `agent.py` | **agentic layer (Zeely 2.0)** | `plan()`, `run()`, `report()` |
| `lambda_function.py` | AWS entrypoint | `handler()` |

## AWS runtime — deployed 2026-10-08

| Resource | Value |
|---|---|
| **Function** | `pr-growth-agent` — python3.12, `lambda_function.handler`, 512 MB, 900 s, stdlib + boto3 |
| **Schedule** | `pr-growth-agent-schedule` → `rate(12 hours)`, **ENABLED**, targets the function with `{"source":"eventbridge","hydrate":true}` |
| **Role** | `sans-mercantile-clickup-monitor-role` + inline `growth-agent-s3` (GetObject/PutObject on `pr-growth-agent/*`, ListBucket) |
| **State** | S3 `pr-growth-agent/ledger.json` (shared across runs) + `reports/<ts>.json` (one per run) |
| **Secrets** | SSM `/sans-mercantile/github-pat`, `/sans-mercantile/clickup-api-token`, social tokens |
| **Env** | `DRY_RUN=false`, `CH_OWNED=publish`, `CH_SOCIAL/CH_PAID/CH_OUTREACH=prepare`, `GROWTH_BUCKET=pr-growth-agent`, `GROWTH_S3=auto`, `GROWTH_PREFIX=public/growth`, `GROWTH_BASE_URL=https://www.sansmercantile.com/growth`, `GROWTH_LEDGER=/tmp/growth-ledger.json`, `GROWTH_PAGES_OUT=/tmp/growth-pages`, `GROWTH_OUTBOX=/tmp/growth-outbox` |

The three `/tmp` paths are required: a Lambda's filesystem is read-only
everywhere else.

Deploy / re-deploy (boto3 only — no local AWS CLI):

```powershell
$py = "C:\Users\kpasc\.bridge\venv\Scripts\python.exe"
& $py C:\Users\kpasc\source\repos\Priv\marketing\build\deploy_growth.py
& $py C:\Users\kpasc\source\repos\Priv\marketing\build\deploy_growth.py --dry --no-rule --invoke
```

`deploy_growth.py` builds the zip (`growth/**` + `lambda_function.py` at the
archive root), ensures the bucket and the IAM inline policy, create/updates the
function, then wires the rule. `--dry` sets `DRY_RUN=true`; `--invoke` runs one
synchronous cycle.

**First live run (2026-10-08 09:02 UTC):** `created 40, published 1, prepared 3,
blocked 0, 11.83 s` — the owned channel committed
`growth: refresh 18 landing pages (2026-10-08)` to `SansMercantile/Nexus` `main`
under `public/growth/`, serving `https://www.sansmercantile.com/growth/…`.
Every other channel staged to the outbox for review, exactly as designed.

**Skill:** `C:\Users\kpasc\.agents\skills\priv-growth-agent\SKILL.md` (mirrored
to `.desktop-commander\skills\`) — workflow, channel-mode rules, module map and
AWS runtime reference.
