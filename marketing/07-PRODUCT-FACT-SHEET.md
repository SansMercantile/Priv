# 07 — Product fact sheet

**Product:** Priv — AI trading terminal / Autonomous Trading Desk
**Publisher:** Sans Mercantile (fintech product)
**Primary URL:** `https://priv.sansmercantile.com` · downloads `https://www.sansmercantile.com/priv`
**Press contact:** press@sansmercantile.com
**Last verified:** 2026-10-08

Every figure below is quotable as-is. Sources are listed in §10 — if a number
moves, update the source first, then here. **No performance claims** (campaign
guardrail, `01-CAMPAIGN-PLAN.md` §7).

---

## 1. Boilerplate (one paragraph)

> Priv is an autonomous trading desk: live signals, strategy backtesting,
> multi-agent execution and full custody control, in one app. It reads price
> action and hands you a complete trade — entry, two targets, and a stop that
> trails to breakeven — while your funds never leave your own broker.

Short form (headline-length):

> **Precision entries, read from the market — not guessed at.**

## 2. At a glance

| Fact | Value |
| --- | --- |
| Category | Autonomous Trading Desk (also described as an AI trading terminal) |
| Maker | Sans Mercantile |
| Entry price | Free tier, $0 — no card required |
| Paid plans | Pro $29 · Elite $79 · Sovereign $149 · Autonomous $199 (monthly) |
| Platforms | Web, Windows, macOS, Linux, Android, iOS — one account |
| Markets | Indices, synthetics, commodities, shares — 24/7 watch |
| Timeframes | 7 per market: 1m · 5m · 15m · 30m · 1H · 4H · 1D |
| Signal ticket | Entry + TP1 + TP2 + stop (trails to breakeven after TP1) |
| Autonomous cycle | 28 seconds, audited every run, fail-closed |
| Agents | 5-agent quorum: technical, quantitative, risk, compliance, ethical |
| Broker connections | 11+ (Deriv, MT5 via local bridge + MetaApi, Interactive Brokers, Alpaca, Binance, XM, and more) |
| Funds held by Priv | 0 — Priv never holds client funds |
| Custody model | Official OAuth to your broker; orders placed in your name |

## 3. What it does

- **Live signals** — complete tickets (entry, two targets, one stop), not
  levels to watch. Multi-timeframe reads from 1 minute to 1 day; divergent
  reads surfaced, not hidden. Delivered by email, SMS, WhatsApp and browser
  push — per alert rule.
- **Strategy Lab** — backtests on real candles with pinned boards, run history
  and reproducible parameters. 152 backtest runs across 45 strategy boards and
  7 timeframes. Available in every plan.
- **Autotrader (autonomous execution)** — 28-second decision cycle, audited
  every run. Your main strategy drives; the five-agent quorum backstops.
  Portfolio mode with position/gross caps and a drawdown brake. Tier-gated;
  fails closed on broken credentials (raises an alert, never retries blind).
- **Trade audit** — position lifecycle trail, SL/TP monitor outcomes, close
  attempts and refusal reasons visible in-app (`/api/v1/audit/*`).
- **Custody & control** — connect your own broker via official OAuth. Funds
  never leave your broker. Credentials fail closed: never shared, never stored
  in the clear. Disconnect in one tap (or revoke at the broker).
- **Support AI** — 36-tool assistant with real account access.

## 4. Plans (quotable as printed)

Source of truth for tier features: `Priv\src\pages\Landing.tsx`; live prices:
`GET /api/v1/payment/plans`. Change all together with `04-COPY-BANK.md`.

| Plan | Price | Line |
| --- | --- | --- |
| Free | $0 | 4 signals / day · Synthetics only · Email or SMS · Manual execution |
| Pro | $29 | 8 signals / day · All categories · Email, SMS, WhatsApp · Manual execution |
| Elite | $79 | 16 signals / day · All categories · Priority routing · Manual execution |
| Sovereign | $149 | 32 signals / day · Event setups · Prop-firm params · Priority delivery |
| Autonomous | $199 | 28-second cycle · Portfolio mode · Multi-agent quorum · Fail-closed |

## 5. Platforms

| Platform | Notes |
| --- | --- |
| Web | No install — `priv.sansmercantile.com` |
| Windows | 91 MB |
| macOS | 177 MB |
| Linux | 107 MB |
| Android | 221 KB |
| iOS | Home-screen install |

One account, one live feed across all six. Downloads:
`https://www.sansmercantile.com/priv`.

## 6. Security posture (approved lines)

- 51 GitHub security findings cleared to zero.
- KYC documents offloaded to encrypted, versioned storage.
- Rate limits, exact-origin CORS and host allowlists on every edge.
- Priv holds no client funds and stores no broker credentials in the clear.

## 7. Approved proof points (static figures)

Use these numbers as-is; they are the campaign's verified stats:

- **152** backtest runs · **45+** strategy boards · **7** timeframes
- **28s** autonomous decision cycle · **24/7** market watch
- **$0** to start · **0** funds held by Priv

Do **not** quote return/win-rate figures — the campaign makes no performance
claims. Backtest output is historical behaviour, not a forecast.

## 8. Risk line (must accompany product claims/screenshots)

> Trading involves risk. Past performance is not indicative of future results.
> Priv holds no client funds and stores no broker credentials in the clear.
> Priv is software; nothing it produces is investment advice.

Full disclosure: `https://priv.sansmercantile.com/risk`. Screenshots of the
public product UI are fine, unaltered, with the risk line intact.

## 9. Category language

- **Say:** "autonomous trading desk" (schema.org `applicationCategory`), "AI
  trading terminal by Sans Mercantile", "start free — no card required".
- **Don't say:** broker, exchange, custodian, guaranteed, profit claims, or
  anything implying Priv holds funds or gives financial advice.

## 10. Where facts live (update order)

| Fact | Source of truth |
| --- | --- |
| Tier features | `Priv\src\pages\Landing.tsx` |
| Live prices | `GET /api/v1/payment/plans` |
| Copy / tier lines | `marketing/04-COPY-BANK.md` |
| Positioning, pillars, guardrails | `marketing/01-CAMPAIGN-PLAN.md` |
| Boilerplate, risk line | `marketing/assets/pages/press/media-kit.html` |
| Platform sizes | `04-COPY-BANK.md` §6 / `poster_specs.py` |
| Product capability detail | `Priv\COMPETITIVE-PLAN.md` |
