// Help & Learn content: FAQ, glossary and tutorial steps for Priv.
//
// Single source of truth the HelpCenter searches. Every entry carries
// keywords so a user can find it from many phrasings ("what is a good
// score", "when do I get signals", "why did my trade close", ...).

export interface FaqEntry {
  id: string;
  category: string;
  question: string;
  answer: string;
  keywords: string[];
}

export interface GlossaryEntry {
  term: string;
  definition: string;
  keywords: string[];
}

export interface TutorialStep {
  id: string;
  title: string;
  body: string[];
  keywords: string[];
}

export const FAQ_CATEGORIES = [
  "Signals & Scores",
  "Conviction Score",
  "Take Profit & Stop Loss",
  "Autotrader",
  "Tiers & Delivery",
  "Account & Security",
] as const;

export const FAQS: FaqEntry[] = [
  // --- Signals & Scores ---------------------------------------------
  {
    id: "what-is-a-signal",
    category: "Signals & Scores",
    question: "What is a signal?",
    answer:
      "A signal is a trade idea our AI produces for a market you follow. " +
      "It tells you the direction (BUY or SELL), the entry price, a stop loss " +
      "and take-profit targets, and — importantly — a conviction score (0–100) " +
      "so you can judge how strong the setup is before you act on it. Signals " +
      "are never fabricated: they are computed from real market data (the " +
      "fuzzy-logic indicator plus the bullish/bearish power composite) with " +
      "ATR-based stop and target distances.",
    keywords: ["signal", "what is", "trade idea", "buy", "sell", "meaning"],
  },
  {
    id: "how-often-signals",
    category: "Signals & Scores",
    question: "How often do I get signals?",
    answer:
      "Signals are generated on a schedule (roughly every 15 minutes the engine " +
      "checks your followed instruments). How many you actually receive per day " +
      "depends on your tier: Free 4/day, Pro 8/day, Elite 16/day, Sovereign 32/day, " +
      "Autonomous effectively uncapped. The daily cap is spread across the day so " +
      "you don't get them all at once. Note: the strong-conviction gate means you " +
      "may receive FEWER than your cap on quiet days — we only send setups with " +
      "real edge, never filler to hit a quota.",
    keywords: ["how often", "how many", "frequency", "daily", "cap", "when", "schedule", "quota"],
  },
  {
    id: "why-no-signals",
    category: "Signals & Scores",
    question: "Why am I not receiving signals?",
    answer:
      "The most common reasons: (1) Your delivery contact isn't verified — " +
      "signals only send to an email/phone you verified in Profile. (2) You're " +
      "outside your delivery window, if you set one. (3) You hit your tier's " +
      "daily cap. (4) The market simply has no strong-conviction setups right " +
      "now — the conviction gate holds back weak signals. (5) A policy gate " +
      "(dead hour / blocked direction) is active. Every signal is also visible " +
      "immediately in My Signals even if the external send is skipped, so check " +
      "there first.",
    keywords: ["not receiving", "no signals", "missing", "didn't get", "where are", "delivery", "held"],
  },
  {
    id: "signal-vs-trade",
    category: "Signals & Scores",
    question: "What's the difference between a signal and a trade?",
    answer:
      "A signal is a RECOMMENDATION — an idea with entry, stop, target and a " +
      "conviction score. You decide whether to act on it. A trade is an actual " +
      "position opened on your broker account (either by you clicking Trade on " +
      "a signal, or by the autotrader if you've armed it). Signals are free to " +
      "ignore; trades risk real capital. One click on a live signal ships it to " +
      "the terminal prefilled with symbol, side, stop loss and take profit.",
    keywords: ["difference", "signal vs trade", "recommendation", "position", "act on"],
  },

  // --- Conviction Score ---------------------------------------------
  {
    id: "what-is-score",
    category: "Conviction Score",
    question: "What is the conviction score?",
    answer:
      "The conviction score is a number from 0 to 100 that tells you how strong " +
      "a setup is. It combines the bullish/bearish power composite (45 points), " +
      "higher-timeframe trend alignment (25), chart-pattern agreement (15) and " +
      "news/event risk (15), then an AI risk-analyst review adjusts it. Higher " +
      "score = more evidence pointing the same way. The score is DIRECTIONAL: " +
      "for a BUY signal a high score means strong bullish conviction; for a SELL " +
      "signal it means strong bearish conviction.",
    keywords: ["score", "conviction", "what is", "number", "0-100", "rating", "strength", "confidence"],
  },
  {
    id: "good-score",
    category: "Conviction Score",
    question: "What is a good score? When should I take a signal?",
    answer:
      "A score of 80 or above is a STRONG-conviction setup — that is the only " +
      "kind we issue and the only kind the autotrader will trade. Between 55 and " +
      "80 there is some edge but not enough to risk capital on. Below 55 is weak " +
      "— a coin-flip — and we never send those. Because we now only issue " +
      "strong-conviction signals (80+), any signal you receive has already " +
      "cleared the bar. You can still use the score to size your conviction: 95 " +
      "is stronger than 82.",
    keywords: ["good score", "when to take", "80", "strong", "threshold", "should i trade", "best"],
  },
  {
    id: "score-80-20",
    category: "Conviction Score",
    question: "Why do you only take scores of 80+ (or 20 and below)?",
    answer:
      "Because weak setups are what lose money. We reviewed a bad trading day and " +
      "found the account had been entering trades on mediocre signals (scores in " +
      "the 30s and 40s) — coin-flips that churned and lost. The fix: only trade " +
      "high-conviction setups. On the 0–100 power composite, 80+ means strong " +
      "bullish conviction (for a long) and 20 or below means strong bearish " +
      "conviction (for a short). Both are expressed as a single directional score " +
      "of 80+ in the trade's direction. Fewer trades, but each one backed by real " +
      "evidence.",
    keywords: ["80", "20", "why only", "high conviction", "weak", "bad day", "churn", "losses", "strong only"],
  },
  {
    id: "score-vs-win",
    category: "Conviction Score",
    question: "Does a high score guarantee a win?",
    answer:
      "No. A high score means the technical evidence strongly favours the " +
      "direction — it is a measure of edge, not certainty. Markets can always " +
      "move against you (news, manipulation, black swans). The score improves " +
      "your odds over many trades; it does not make any single trade safe. That " +
      "is why every signal still carries a stop loss and why you should never " +
      "risk more than you can afford to lose. Think of the score as 'how much " +
      "of the evidence agrees', not 'will this win'.",
    keywords: ["guarantee", "always win", "sure", "risk", "certainty", "safe", "lose"],
  },
  {
    id: "verified-signal",
    category: "Conviction Score",
    question: "What does a VERIFIED mark on a signal mean?",
    answer:
      "VERIFIED means our AI's read and the human trading crowd's published " +
      "reasoning (community ideas) agree on the direction. The system reads real " +
      "traders' own stated case for the symbol and compares it with its analysis; " +
      "when enough of them (5+ ideas) lean the same way the AI does, the setup is " +
      "marked VERIFIED. It's a human-in-the-loop cross-check on top of the " +
      "mechanical score — extra confirmation, not a separate signal.",
    keywords: ["verified", "mark", "crowd", "community", "human", "ideas", "agree", "cross-check"],
  },

  // --- TP & SL ------------------------------------------------------
  {
    id: "what-is-tp-sl",
    category: "Take Profit & Stop Loss",
    question: "What are Take Profit (TP) and Stop Loss (SL)?",
    answer:
      "Take Profit (TP) is the price where the trade closes to lock in a win. " +
      "Stop Loss (SL) is the price where the trade closes to cap a loss. Every " +
      "Priv signal gives you both, computed from the market's ATR (average true " +
      "range — a volatility measure), so the distances reflect how much the " +
      "market actually moves. TP1 is the first target; TP2 is a further stretch " +
      "target. A take-profit close can NEVER be negative — if a target would " +
      "close below breakeven it is treated and labelled as a stop, not a win.",
    keywords: ["take profit", "stop loss", "tp", "sl", "what is", "target", "exit", "atr"],
  },
  {
    id: "trailing-stop",
    category: "Take Profit & Stop Loss",
    question: "How does the trailing stop work?",
    answer:
      "Once your trade reaches Take Profit 1, the stop loss automatically moves " +
      "to your entry price (breakeven) — from that point you can't lose on the " +
      "trade. As price moves further in your favour the stop keeps trailing " +
      "behind it, locking in more and more profit. Stops only ever move in your " +
      "favour, never against you. This runs continuously whether you're online " +
      "or not.",
    keywords: ["trailing", "trailing stop", "breakeven", "move stop", "lock profit", "tp1"],
  },
  {
    id: "why-trade-closed",
    category: "Take Profit & Stop Loss",
    question: "Why did my trade close?",
    answer:
      "A trade closes for one of these reasons, always labelled honestly: TP hit " +
      "(price reached the target — a win), SL hit (price reached the stop — a " +
      "loss), trailing-stop / breakeven protect (after TP1, price came back to " +
      "the trailed stop), an AI-managed exit (the higher-timeframe trend turned " +
      "against the position, or a profit-protect rule fired), or you closed it " +
      "manually. The close reason and realized profit/loss are shown in My " +
      "Signals position alerts and in History — losses are never hidden behind a " +
      "generic 'closed' label.",
    keywords: ["why closed", "trade closed", "close reason", "exit", "stopped out", "hit"],
  },

  // --- Autotrader ---------------------------------------------------
  {
    id: "what-is-autotrader",
    category: "Autotrader",
    question: "What is the autotrader?",
    answer:
      "The autotrader is an optional feature that trades for you around the " +
      "clock. Instead of you clicking Trade on each signal, the autotrader " +
      "analyzes the market itself, opens positions on your linked broker " +
      "account, and manages the exits. It runs on our servers (not your " +
      "browser), so it keeps working when your laptop is closed. You stay in " +
      "control: you arm it, choose the strategy and risk, and can disarm it at " +
      "any time.",
    keywords: ["autotrader", "auto trade", "automatic", "bot", "arm", "24/7", "what is"],
  },
  {
    id: "autotrader-score",
    category: "Autotrader",
    question: "How does the autotrader decide what to trade?",
    answer:
      "Every candidate goes through the same rigorous analysis as a signal and " +
      "gets a conviction score (0–100). The autotrader now ONLY opens trades " +
      "scoring 80 or above — strong-conviction setups. It also enforces a " +
      "per-symbol cooldown (after closing a symbol it waits 30 minutes before " +
      "re-entering it, so it can't churn one market), a 30-day re-evaluation " +
      "rule for old positions, and spreads its attention across the 33 available " +
      "markets rather than fixating on one. Weak setups are skipped and logged.",
    keywords: ["autotrader decide", "how decide", "entry", "score", "80", "cooldown", "churn"],
  },
  {
    id: "autotrader-safe",
    category: "Autotrader",
    question: "Is the autotrader safe to use?",
    answer:
      "It is built fail-closed and you stay in control, but all trading carries " +
      "risk. Safeguards: it re-checks your subscription tier every cycle and " +
      "disarms if you downgrade; it requires a live broker connection; stakes " +
      "are capped (a fixed % of your balance per trade, never more); and it only " +
      "takes strong-conviction setups. It runs on a demo account by default so " +
      "you can watch it prove itself before risking real money. Never arm it on " +
      "a live account with money you can't afford to lose.",
    keywords: ["autotrader safe", "safe", "risk", "control", "demo", "live", "lose money"],
  },

  // --- Tiers & Delivery ---------------------------------------------
  {
    id: "tiers",
    category: "Tiers & Delivery",
    question: "What are the tiers and what do they give me?",
    answer:
      "Tiers control how many signals you get, which markets you can follow, how " +
      "many instruments, and which delivery channels you can use. Free: 4/day, " +
      "limited categories, email only. Pro, Elite, Sovereign: progressively more " +
      "signals (8/16/32 per day), more categories and instruments, and SMS/" +
      "WhatsApp delivery. Sovereign adds event-driven signals (NFP/CPI/opening " +
      "bell). Autonomous unlocks the autotrader and effectively uncapped signals. " +
      "See Billing for current pricing.",
    keywords: ["tier", "plan", "free", "pro", "elite", "sovereign", "autonomous", "upgrade", "price"],
  },
  {
    id: "delivery-channels",
    category: "Tiers & Delivery",
    question: "How do I get signals — email, SMS or WhatsApp?",
    answer:
      "You choose a delivery channel in My Signals: email is available on every " +
      "tier; SMS and WhatsApp require a paid tier. Whichever you pick, the " +
      "contact must be one you already verified in Profile (we only send to " +
      "proven addresses/numbers). Every signal also appears instantly in the app " +
      "under My Signals regardless of the external channel, and you can enable " +
      "browser push alerts for opens and TP/SL hits.",
    keywords: ["delivery", "channel", "email", "sms", "whatsapp", "push", "how to get", "contact"],
  },
  {
    id: "verify-contact",
    category: "Tiers & Delivery",
    question: "Why do I need to verify my email or phone?",
    answer:
      "So signals actually reach you and only you. We send a one-time code (OTP) " +
      "to the address or number; entering it proves you own it. Signals are then " +
      "only sent to verified contacts — this prevents signals going to a typo'd " +
      "address and protects your account. Verification happens once, in Profile, " +
      "and My Signals then lets you pick any verified contact.",
    keywords: ["verify", "verification", "otp", "code", "email", "phone", "why verify"],
  },

  // --- Account & Security -------------------------------------------
  {
    id: "link-broker",
    category: "Account & Security",
    question: "How do I connect my broker (Deriv)?",
    answer:
      "Go to Broker Terminal or SANS Network Link and connect your Deriv account " +
      "via the secure OAuth flow — you log in on Deriv's site and grant access; " +
      "we never see your password. Once linked, you can trade signals, see your " +
      "balance and positions, and arm the autotrader. You can link both a demo " +
      "and a real account and switch between them with the account switcher in " +
      "the sidebar.",
    keywords: ["connect broker", "link", "deriv", "oauth", "login", "account", "setup"],
  },
  {
    id: "is-money-safe",
    category: "Account & Security",
    question: "Is my money and data safe?",
    answer:
      "Your money stays at your broker — we never hold your funds. We connect " +
      "via OAuth tokens and never see your broker password. Identity (KYC) " +
      "documents are encrypted and stored in a private vault, not in our main " +
      "database. Signals and trades are scoped to your account only — no other " +
      "user's data is ever visible to you, and yours is never shared. Start on " +
      "a demo account to build confidence before using real funds.",
    keywords: ["safe", "money", "security", "data", "privacy", "kyc", "funds", "trust"],
  },
  {
    id: "kyc",
    category: "Account & Security",
    question: "What is KYC and why do you need it?",
    answer:
      "KYC (Know Your Customer) is identity verification — a photo ID and a " +
      "selfie — required by financial regulations before certain features " +
      "(like live trading and withdrawals) are enabled. It protects you and the " +
      "platform from fraud. Your documents are encrypted and stored in a " +
      "dedicated vault, reviewed by an admin, and once approved your Identity " +
      "status stays valid for 12 months before needing renewal.",
    keywords: ["kyc", "identity", "verify identity", "id", "selfie", "document", "approval"],
  },
];

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "Signal",
    definition:
      "A trade idea the AI produces: direction (BUY/SELL), entry, stop loss, " +
      "take-profit targets and a conviction score. A recommendation, not an " +
      "automatic trade.",
    keywords: ["signal"],
  },
  {
    term: "Conviction score",
    definition:
      "A 0–100 rating of how much evidence supports a setup. Directional: " +
      "≥80 = strong conviction in the trade's direction (≥80 bullish for a " +
      "long, ≤20 bearish for a short). Only 80+ setups are issued or traded.",
    keywords: ["score", "conviction", "rating"],
  },
  {
    term: "Bullish / Bearish power composite",
    definition:
      "The 0–100 indicator at the heart of the score, built from many technical " +
      "factors. Above 50 leans bullish, below 50 leans bearish; far from 50 in " +
      "either direction = strong conviction.",
    keywords: ["power", "composite", "bullish", "bearish"],
  },
  {
    term: "VERIFIED",
    definition:
      "A mark meaning the AI's analysis and the human trading crowd's published " +
      "reasoning agree on the direction — an extra human-in-the-loop cross-check.",
    keywords: ["verified", "crowd", "agree"],
  },
  {
    term: "Entry",
    definition: "The price at which a trade is opened.",
    keywords: ["entry", "open", "price"],
  },
  {
    term: "Stop Loss (SL)",
    definition:
      "The price where a trade closes automatically to cap a loss. Set from the " +
      "market's ATR so it reflects real volatility.",
    keywords: ["stop loss", "sl", "loss"],
  },
  {
    term: "Take Profit (TP)",
    definition:
      "The price where a trade closes automatically to lock in a win. TP1 is the " +
      "first target, TP2 a further one. A take-profit close is never negative.",
    keywords: ["take profit", "tp", "target", "win"],
  },
  {
    term: "ATR (Average True Range)",
    definition:
      "A volatility measure — how much a market typically moves. Used to set " +
      "sensible stop-loss and take-profit distances for each signal.",
    keywords: ["atr", "average true range", "volatility"],
  },
  {
    term: "Trailing stop",
    definition:
      "A stop loss that moves in your favour as the trade profits — first to " +
      "breakeven after TP1, then locking in more as price advances. Never moves " +
      "against you.",
    keywords: ["trailing", "trailing stop", "breakeven"],
  },
  {
    term: "Breakeven",
    definition:
      "Your entry price. Once a trade reaches TP1 the stop moves here so the " +
      "trade can't turn into a loss.",
    keywords: ["breakeven", "break even"],
  },
  {
    term: "Autotrader",
    definition:
      "The optional feature that analyzes, opens and manages trades for you " +
      "24/7 on your linked broker account. Only trades strong-conviction (80+) " +
      "setups; you arm/disarm it and set the risk.",
    keywords: ["autotrader", "bot", "auto"],
  },
  {
    term: "Cooldown",
    definition:
      "A 30-minute pause after a position closes before the same symbol can be " +
      "re-entered — prevents churning one market and forces use of the other 32.",
    keywords: ["cooldown", "cool down", "churn"],
  },
  {
    term: "Tier",
    definition:
      "Your subscription level (Free, Pro, Elite, Sovereign, Autonomous). Sets " +
      "how many signals you get, which markets, and which delivery channels.",
    keywords: ["tier", "plan", "subscription"],
  },
  {
    term: "KYC",
    definition:
      "Know Your Customer — identity verification (photo ID + selfie) required " +
      "for live features. Documents are encrypted and stored in a private vault.",
    keywords: ["kyc", "identity", "verification"],
  },
  {
    term: "Pip",
    definition:
      "The standard unit of price movement in a market. Results are often " +
      "expressed in pips won or lost.",
    keywords: ["pip", "pips", "point"],
  },
  {
    term: "Leverage / Multiplier",
    definition:
      "Trading with borrowed exposure so a small stake controls a larger " +
      "position. Amplifies both gains and losses — use with care.",
    keywords: ["leverage", "multiplier", "margin"],
  },
];

export const TUTORIAL: TutorialStep[] = [
  {
    id: "welcome",
    title: "Welcome to Priv — the 60-second tour",
    body: [
      "Priv is an AI-driven trading assistant. It does two main things: it sends " +
      "you trade SIGNALS (ideas with a conviction score), and it can optionally " +
      "TRADE for you via the autotrader.",
      "You always stay in control. Signals are recommendations you can act on or " +
      "ignore. The autotrader only runs when you arm it, and you can stop it any " +
      "time.",
      "The most important idea on the whole platform is the CONVICTION SCORE — a " +
      "0–100 rating of how strong each setup is. We only ever send or trade " +
      "strong-conviction setups (score 80+). Everything else in this tutorial " +
      "builds on that.",
    ],
    keywords: ["welcome", "start", "intro", "overview", "tour", "beginner"],
  },
  {
    id: "setup",
    title: "Step 1 — Set up your account",
    body: [
      "1. Create your account and sign in.",
      "2. Open Identity & Profile and verify your email and/or phone (one-time " +
      "code). Signals only deliver to verified contacts.",
      "3. Complete KYC (photo ID + selfie) when you're ready for live features — " +
      "documents are encrypted and stored in a private vault.",
      "4. Connect your Deriv broker account from Broker Terminal or SANS Network " +
      "Link (secure OAuth — we never see your password). Start with the DEMO " +
      "account so you can learn risk-free.",
    ],
    keywords: ["setup", "account", "sign up", "verify", "kyc", "connect broker", "deriv", "getting started"],
  },
  {
    id: "signals",
    title: "Step 2 — Understand your signals",
    body: [
      "Open My Signals. Each signal card shows: the market, the direction " +
      "(BUY or SELL), the entry price, take-profit (TP) and stop-loss (SL) " +
      "levels, and the conviction SCORE badge.",
      "The score badge is colour-coded: green 80+ = strong bullish conviction, " +
      "red ≤20 = strong bearish conviction, amber in between = weak (we don't " +
      "send those anymore). A VERIFIED mark means the human crowd's reasoning " +
      "agrees with the AI — extra confirmation.",
      "Only strong-conviction (80+) signals are issued, so anything you receive " +
      "has already cleared the quality bar.",
    ],
    keywords: ["signals", "my signals", "read signal", "score badge", "verified", "understand"],
  },
  {
    id: "trade-signal",
    title: "Step 3 — Act on a signal",
    body: [
      "To take a signal, click the Trade button on a live (non-archived) signal. " +
      "It opens the Broker Terminal prefilled with the symbol, direction, stop " +
      "loss and take profit — review and confirm.",
      "Once open, the trade manages itself: reaching TP1 moves your stop to " +
      "breakeven (you can't lose from there), and the stop then trails to lock " +
      "in more profit as price advances. TP and SL hits alert you in My Signals " +
      "and by browser push.",
      "You can close a trade manually at any time from the terminal or your " +
      "broker.",
    ],
    keywords: ["trade", "act on", "take signal", "execute", "place trade", "terminal"],
  },
  {
    id: "autotrader",
    title: "Step 4 — Let the autotrader work (optional)",
    body: [
      "Prefer hands-off? Arm the autotrader and it trades for you 24/7 on our " +
      "servers — no need to keep a browser open.",
      "It follows the same strong-conviction rule: only setups scoring 80+ are " +
      "traded. It also waits 30 minutes before re-entering a symbol it just " +
      "closed (no churning), re-evaluates positions older than 30 days, and " +
      "spreads across 33 markets instead of fixating on one.",
      "Choose your strategy and risk, arm it on the DEMO account first, watch it " +
      "prove itself, then consider live. Disarm any time.",
    ],
    keywords: ["autotrader", "arm", "hands off", "automatic", "24/7", "enable"],
  },
  {
    id: "risk",
    title: "Step 5 — Manage your risk",
    body: [
      "Never risk money you can't afford to lose. Start on demo.",
      "Every signal and autotrader trade carries a stop loss — respect it. The " +
      "score improves your odds over many trades but no single trade is " +
      "guaranteed.",
      "Stake sizing is capped (a fixed % of balance per trade). Prefer smaller " +
      "stakes while you learn how the scores and exits behave.",
      "Review your History & Audit regularly: it shows every trade's close " +
      "reason and realized profit/loss, honestly labelled — wins and losses " +
      "alike.",
    ],
    keywords: ["risk", "manage risk", "money", "stake", "loss", "safe", "position size"],
  },
  {
    id: "faq-pointer",
    title: "Step 6 — Find answers fast",
    body: [
      "Use the FAQ tab on this page and the search box above — type any word " +
      "('score', 'stop loss', 'delivery', 'autotrader') and matching answers, " +
      "glossary terms and tutorial steps filter instantly.",
      "The Glossary tab defines every term in plain language.",
      "Still stuck? Ask the Priv assistant (the chat bubble) — it can explain " +
      "any signal, score or feature in the context of your own account.",
    ],
    keywords: ["faq", "help", "search", "find", "glossary", "answers", "support"],
  },
];

// Unified searchable index: one list the HelpCenter filters, each item
// tagged with where it lives so the UI can route the user to the tab.
export type SearchResult =
  | { kind: "faq"; entry: FaqEntry }
  | { kind: "glossary"; entry: GlossaryEntry }
  | { kind: "tutorial"; entry: TutorialStep };

export function searchHelp(query: string): SearchResult[] {
  const q = (query || "").trim().toLowerCase();
  if (!q) return [];
  const terms = q.split(/\s+/).filter(Boolean);
  const matches = (hay: string[]) =>
    terms.every((t) => hay.some((h) => h.toLowerCase().includes(t)));

  const out: SearchResult[] = [];
  for (const entry of FAQS) {
    if (matches([entry.question, entry.answer, entry.category, ...entry.keywords])) {
      out.push({ kind: "faq", entry });
    }
  }
  for (const entry of GLOSSARY) {
    if (matches([entry.term, entry.definition, ...entry.keywords])) {
      out.push({ kind: "glossary", entry });
    }
  }
  for (const entry of TUTORIAL) {
    if (matches([entry.title, entry.body.join(" "), ...entry.keywords])) {
      out.push({ kind: "tutorial", entry });
    }
  }
  return out;
}
