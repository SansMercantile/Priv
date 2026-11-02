# 04 — Copy bank

Every string the campaign renders, in one place. The compositor takes plain
text — nothing is baked into the art — so this file is the single place to
change words before re-rendering.

Source of truth for tier features: `Priv\src\pages\Landing.tsx` (tier cards).
Live prices come from `GET /api/v1/payment/plans`.

---

## 1. Headlines

| Use | Line |
| --- | --- |
| Lead (paid) | Entry. Two targets. One stop. |
| Lead (proof) | Prove it before you risk it. |
| Lead (custody) | Your account. Your funds. Your control. |
| Lead (reach) | Your signals, on every screen you own. |
| Lead (pricing) | One plan for every pace. |
| Lead (autonomy) | Arm it. Sleep. Let the desk work. |
| Lead (brand) | Built for traders who want the edge, not the noise. |
| Lead (delivery) | The setup lands before you look. |
| Lead (security) | Fail-closed. By design. |
| Lead (research) | Precision entries, read from the market. |
| Lead (coverage) | One market. Seven timeframes. |
| Lead (agents) | Five agents. One quorum. |
| Thumb (signals) | ENTRY. TWO TARGETS. ONE STOP. |
| Thumb (autotrader) | IT TRADED WHILE YOU SLEPT. |

## 2. Eyebrows (tracked, gold)

`PRIV — LIVE SIGNAL FEED` · `PRIV LIVE` · `LIVE SIGNAL FEED` · `STRATEGY LAB` ·
`AUTONOMOUS EXECUTION` · `MULTI-AGENT DESK` · `CUSTODY & CONTROL` · `SECURITY` ·
`EVERY SCREEN YOU OWN` · `DELIVERY` · `MULTI-TIMEFRAME READS` · `PRICING` ·
`SANS MERCANTILE` · `START FREE`

## 3. Sub-heads

- Priv reads price action across indices, synthetics, commodities and shares —
  then hands you the entry, two targets and a stop that trails to breakeven.
- Every setup ships complete: entry, TP1, TP2 and a stop that moves to
  breakeven the moment the first target prints.
- Every strategy backtested on real candles — pinned boards, run history and
  reproducible parameters.
- The same instrument read from one minute to one day — divergent reads
  surfaced, not hidden.
- Your main strategy drives every cycle; the multi-agent quorum backstops it.
- Technical, quantitative, risk, compliance and ethical agents deliberate
  before a single order moves.
- One account, one live feed — from a full desk setup to your pocket.
- Priv connects to your own broker through official OAuth.
- Entry, both targets and the stop — pushed the moment they complete.
- Start free. Upgrade when the signals start paying for themselves.
  Sovereign $149 · Autonomous $199.
- Independently audited, then audited again.
- Priv is the AI trading terminal from Sans Mercantile — signals, strategy
  testing, autonomous execution and full custody in one desk.

## 4. Calls to action

| Tone | CTA |
| --- | --- |
| Neutral | Start free — no card required |
| Signal-led | See today's signals |
| Product | Open the Strategy Lab · Watch the quorum decide · Watch one market resolve |
| Conversion | Compare every plan · Connect your account · Download Priv |
| Risk-aware | Read the security posture · Turn on position alerts |
| Tier-specific | Autonomous — $199 / month |
| Short (thumb/bumper) | Start free |

## 5. Plans (single source of truth)

| Plan | Price | Lines shown on the poster |
| --- | --- | --- |
| Free | $0 | 4 signals / day · Synthetics only · Email or SMS · Manual execution |
| Pro | $29 | 8 signals / day · All categories · Email, SMS, WhatsApp · Manual execution |
| Elite | $79 | 16 signals / day · All categories · Priority routing · Manual execution |
| Sovereign | $149 | 32 signals / day · Event setups · Prop-firm params · Priority delivery |
| Autonomous | $199 | 28-second cycle · Portfolio mode · Multi-agent quorum · Fail-closed |

Feed poster shows three cards (Pro featured). Wide poster shows four.
Link card reduces to `$0 free · $29 pro · $79 elite`.

## 6. Feature lines

**Signal ticket** — `VOLATILITY 100 INDEX` · `BUY · 1H` · `ENTRY` ·
`TAKE PROFIT 1` · `TAKE PROFIT 2` · `STOP LOSS` · `LIVE`

**Autotrader**
- 28-second decision cycle, audited every run
- Tier-gated and fail-closed on credentials
- Portfolio mode: positions, gross caps, drawdown brake

**Control**
- Funds never leave your broker
- Orders are placed in your name, always logged
- Credentials fail closed — never shared, never stored in the clear

**Security**
- 51 GitHub security findings cleared to zero
- KYC documents offloaded to encrypted, versioned storage
- Rate limits, exact-origin CORS and host allowlists on every edge

**Agents** — Technical `BUY` "+2 confirmations · trend + momentum" ·
Quantitative `BUY` "ATR bands · mean reversion filter" ·
Compliance `HOLD` "restricted symbols clear" ·
Ethical `BUY` "no conflict · disclosure clean"

**Delivery** — `E` Signal emailed to you · `S` SMS when the level fills ·
`W` WhatsApp authentication template · `P` Browser push on every device
(with the delivery meta lines on the poster)

**Platforms** — Web (no install) · Windows (91 MB) · macOS (177 MB) ·
Linux (107 MB) · Android (221 KB) · iOS (home screen)

**Timeframes** — `1m` `5m` `15m` `30m` `1H` `4H` `1D`

**Product chips** — Signals · Terminal · Strategy Lab · Autotrader · MT5 bridge

**Stats** — `45+` strategy boards · `7` timeframes · `24/7` market watch ·
`152` backtest runs · `45` boards · `24/7` market watch

---

## 7. Social captions

**A — the setup**
> Entry. Two targets. One stop. Every Priv setup ships complete: entry, TP1,
> TP2, and a stop that trails to breakeven the moment the first target prints.
> Free tier: 4 signals a day. priv.sansmercantile.com

**B — proof**
> Most signals never get tested. Ours do — 152 backtest runs across 45 boards
> and 7 timeframes, on real candles, before anyone risks a cent.
> Strategy Lab is in every plan.

**C — autonomy**
> Arm it. Sleep. Let the desk work. A 28-second decision cycle, audited every
> run, fail-closed on credentials — with your main strategy driving and a
> five-agent quorum backstopping.

**D — custody**
> Your account. Your funds. Your control. Priv connects to your own broker
> through official OAuth. Credentials fail closed. Funds never leave your
> broker. Orders are placed in your name, always logged.

**E — reach**
> Your signals, on every screen you own. Web, Windows, macOS, Linux, Android,
> iOS — one account, one live feed, from a full desk setup to your pocket.

**F — plans**
> One plan for every pace. Free $0 · Pro $29 · Elite $79 · Sovereign $149 ·
> Autonomous $199. Start free, upgrade when the signals start paying for
> themselves.

**Short (thumb / bumper)**
> Entry. Two targets. One stop. — priv.sansmercantile.com

## 8. Email

| Subject | Preview |
| --- | --- |
| Entry, two targets, one stop | The whole setup, before you look |
| Prove it before you risk it | 152 backtest runs, one click |
| Your funds never leave your broker | How Priv connects — and fails closed |
| One plan for every pace | Free is free. Upgrade when it pays. |
| It traded while you slept | A 28-second cycle, audited every run |

## 9. Hashtags

`#trading #signals #forex #futures #propfirms #algorithmictrading
#quant #backtesting #cryptography-not-financial-advice` — keep to three per
post, and never on the image itself.

## 10. Voice-over lines (as spoken)

- **hero-30s / hero-30s-vertical:** "Entry, two targets, one stop, read from
  the market." → "Every strategy is backtested on real candles first." →
  "Or arm the desk, and let it work while you sleep." → "Your account, your
  funds, your control." → "Start free today. Priv, a Sans Mercantile product."
- **teaser-15s-vertical:** "Entry, two targets, one stop." → "Arm it, and let
  the desk work while you sleep." → "Priv. Start free today."
- **explainer-60s:** "This is Priv. Precision entries, read from the market,
  not guessed at." → "Every signal ships complete. Entry, two targets, and a
  stop that moves to breakeven." → "Seven timeframes on every market, from one
  minute to one day." → "Prove it in the strategy lab before you risk a cent."
  → "Five agents deliberate on every order before it moves." → "Web, desktop
  and mobile. One account, every screen." → "And it stays yours. Your account,
  your funds, your control." → "Start free today. Priv, a Sans Mercantile
  product."
- **bumper-6s:** silent by design.
