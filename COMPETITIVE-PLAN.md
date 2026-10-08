# Priv vs. the field — competitive plan

_Sources: botvio.live, traderframe.io, nextrader.live (fetched 2026-10-08). Status column updated as we ship._

## 1. What each competitor actually has

### botvio.live — content & trust moat
- AI signals (forex, gold, crypto, indices, Deriv synthetics), signal history, copy trading, AI bots, broker hub + broker reviews, gold (XAUUSD) research, market intelligence, learn/blog, FAQ.
- Trust surface: Trust Center, Methodology, Performance Transparency, Editorial Policy, Affiliate Disclosure, Risk Disclaimer.
- Positioning: independent education/research platform — explicitly *not a broker*, doesn't hold funds, doesn't execute.
- **Edge:** organic acquisition (SEO + review/affiliate ecosystem) and borrowed credibility. **Weakness:** the product is largely a marketing shell — no execution kernel, no risk management, disclaimers distance them from real trading.

### traderframe.io — integrations & polish moat
- **Pip AI**: AI PineScript generator (describe strategy → writes, checks, backtests Pine code).
- **AI Trade Agent**: reads every candle close, proposes trades within limits, records reasoning.
- Signal sources: TradingView webhook, MT4/MT5, Telegram, Discord; copy trading with **no copy fees**; trading journal (Notion-style); leaderboard with TDF score; broker-reported fills; 89ms latency claim; every refusal logged with a reason.
- Venues: 9 crypto exchanges + MT5 + IBKR (futures/options) + Deriv; demo/live labeling.
- **Edge:** breadth of ingestion, trust/transparency artifacts, polished funnel. **Weakness:** an integration layer, not an engine — no own backtest depth, no portfolio/risk stack, generic across brokers.

### nextrader.live — Deriv niche depth + free funnel
- 4 free tools: (1) AI signals — 11 strategies, 89 Deriv markets, **non-repaint, closed-candle-only**, confidence score + written reasoning, S/R + pivot overlays, quick-trade panel; (2) Bot Hub — 747 free ready-made bots + drag-and-drop builder; (3) live digit analyzer; (4) affiliate program.
- Deriv OAuth login, no subscription, demo-account support, Android app.
- **Edge:** free forever funnel, Deriv-specific depth, mobile. **Weakness:** shallow single-candle analysis, no SL/TP discipline, no portfolio construction, no cross-broker story.

## 2. Priv's moats (none of the three have these)
- **Full execution kernel**: own adapters (Deriv ×2, MT5 local bridge, MetaApi, IB, Alpaca, Binance, XM), SL/TP monitors with 10-attempt retry ladder, idempotent close handling, settlement verification before declaring failure (hardened 2026-10-08).
- **Proven backtest engine**: portfolio strategies with verified runs (`portfolio_ex_crypto` +793% local / +702% prod; ex-crypto row +$68.5M math).
- **Multi-agent layer**: risk agent, arbitrage scanner, FOMC awareness; 36-tool support AI with real account access.
- Emotional check-ins, push/email/feed notifications, KYC (real AI verification), payments (PayFast), referral codes, signals history API (`GET /history`), autotrader with strategy catalog.
- Mobile app build pipeline exists (android/ios scripts) — ships as P3.

## 3. Gap matrix

| # | Capability | botvio | traderframe | nextrader | Priv | Priority |
|---|---|---|---|---|---|---|
| 1 | Transparency artifacts (methodology, performance, refusal/audit log) | trust pages | refusal log | — | **real data, no surface** | **P0 — build now** |
| 2 | Non-repaint / closed-candle guarantee | — | candle-close agent | **flagship claim** | verify + claim | **P1** |
| 3 | AI strategy generator (plain English → backtest → deploy) | — | PineScript (writes code *for another platform*) | — | Strategy Tester exists, no generation layer | **P1** |
| 4 | External signal ingestion (TradingView webhook, Telegram) | — | **4 sources** | — | none | **P1** |
| 5 | Trading journal (entry/exit/reason/P&L) | — | Notion-style | — | position_events feed exists → evolve | **P1** |
| 6 | Copy trading | yes | yes, no fees | — | none | P1 (M/L effort) |
| 7 | Signal history | yes | leaderboard | yes | API + MySignals UI exist → market it | P2 |
| 8 | Confidence + written reasoning on every signal | analysis-ish | yes | **flagship** | signal `basis` exists → surface consistently | P2 |
| 9 | Digit analyzer (Deriv) | — | — | yes | none (small) | P2 |
| 10 | Free tier / demo funnel | — | demo labeling | **free forever** | demo exists → make free tier obvious | P2 (billing call) |
| 11 | Affiliate program (aggressive rev share) | disclosure | — | **80%** | referral codes exist → upgrade terms | P2 |
| 12 | Education/blog/SEO | **strong** | marketing site | tools-as-content | none public | P2 (content) |
| 13 | No-code bot builder | bots page | — | **747 bots + drag-drop** | autotrader + catalog, no visual builder | P3 (L) |
| 14 | Leaderboard | — | TDF score | — | none | P3 |
| 15 | Broker hub / reviews | yes | venue breadth | Deriv-only | connection hub (11+) exists, no review content | P3 |

## 4. Positioning — how we beat each
- **vs botvio:** they educate, we execute. Copy their *trust artifacts* but back them with audited, real numbers (our engine is verifiable; theirs is disclaimers). "Signals you can't act on" vs Priv's closed loop: signal → autotrader → SL/TP monitor → audit trail.
- **vs traderframe:** they're plumbing between other people's engines. Preempt with **AI strategy generator** — describe a strategy and Priv backtests it *and* can deploy it here; PineScript output is a dead end by comparison. Adopt their refusal-logging idea: every monitor action/refusal visible with reason.
- **vs nextrader:** free + Deriv depth. Answer with (a) free/demo clarity, (b) an explicit non-repaint guarantee (we must actually verify closed-candle discipline first), (c) our SL/TP/audit discipline vs their quick-trade panel, (d) digit analyzer as a cheap parity feature.

## 5. Build order

| # | Initiative | Size | Status |
|---|---|---|---|
| B1 | Natural narrator voices (voice picker, emoji/emoticon stripping, trading shorthand) | S | **DONE 2026-10-08** (`1ad25c1`, `5fe4153`, live on prod) |
| B2 | **Trade Audit panel** — API surfacing monitor attempts, last_close_error, close outcomes, refusal reasons (position_events + order_manager state) + in-app view; foundation for the performance-transparency page | M | **DONE 2026-10-08** (`/api/v1/audit/*` + History section; backend 066c0fb1c, Priv f006c12) |
| B3 | Closed-candle / non-repaint verification in the signal engine + guarantee copy | S-M | pending |
| B4 | AI strategy generator: plain English → spec → run backtest → hand off to autotrader | M-L | pending |
| B5 | TradingView webhook ingestion (`POST /api/v1/ingest/tv` + secret flow) | M | pending |
| B6 | Copy trading v1: leader publishes, follower enables with per-trade risk caps | L | pending |
| B7 | Digit analyzer parity (Deriv digits) | S | pending |
| B8 | Public performance-transparency page fed by real run data | M | after B2 |

Sequence rationale: B2 anchors on the close-failure bug we just fixed (fresh, real data, differentiating) and feeds B8. B3 is cheap trust with high conversion value. B4 is the strategic preempt against traderframe. B5/B6 open acquisition loops.

## 6. Risks / don't-break list
- Copy trading + affiliate rev-share touch billing/compliance — needs a product call before build.
- Non-repaint claim must be verified against the engine (closed candles) **before** marketing it — never claim what we haven't tested.
- Do not regress the hardened close path (8 regression tests in `test_monitor_close_failures.py` are the contract).
- Competitor claims (89ms, 80%, 89% confidence) are marketing numbers — verify before countering with our own.
