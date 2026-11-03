"""Proof-claim registry and compliance guard.

Zeely's copy works because every paragraph carries a number. For a trading
product the same discipline has a second job: no claim may ship without a
source, and no risk-hiding language may ship at all.
"""
import os
import re

SITE = "priv.sansmercantile.com"
SITE_FULL = "https://priv.sansmercantile.com"
DOWNLOADS = "https://www.sansmercantile.com/priv"
DISCLAIMER = ("Trading involves risk. Past performance is not indicative of "
              "future results.")

CATEGORY = "autonomous trading desk"
ONE_LINER = ("Priv is an autonomous trading desk: live signals, strategy "
             "backtesting, multi-agent execution and full custody, in one app.")

# ---------------------------------------------------------------- proof stack
# verified=True  -> readable out of the shipped product / pricing page
# verified=False -> illustrative number used in creative; must never be
#                   presented as an audited statistic.
STATS = {
    "category":      dict(value="Autonomous trading desk", label="category",
                          source="positioning", verified=True),
    "price_free":    dict(value="$0", label="to start",
                          source="Landing.tsx tier grid", verified=True),
    "price_pro":     dict(value="$29", label="Pro / month",
                          source="Landing.tsx tier grid", verified=True),
    "price_elite":   dict(value="$79", label="Elite / month",
                          source="Landing.tsx tier grid", verified=True),
    "price_sov":     dict(value="$149", label="Sovereign / month",
                          source="Landing.tsx tier grid", verified=True),
    "price_auto":    dict(value="$199", label="Autonomous / month",
                          source="Landing.tsx tier grid", verified=True),
    "timeframes":    dict(value="7", label="timeframes per market",
                          source="product: 1m/5m/15m/30m/1H/4H/1D", verified=True),
    "cycle":         dict(value="28s", label="decision cycle",
                          source="autotrader run loop", verified=True),
    "agents":        dict(value="5", label="deliberating agents",
                          source="quorum design", verified=True),
    "boards":        dict(value="45+", label="strategy boards",
                          source="marketing creative (illustrative)",
                          verified=False),
    "runs":          dict(value="152", label="backtest runs",
                          source="marketing creative (illustrative)",
                          verified=False),
    "markets":       dict(value="24/7", label="market watch",
                          source="index + synthetic + commodity + share coverage",
                          verified=True),
    "platforms":     dict(value="6", label="platforms",
                          source="Web/Windows/macOS/Android/iOS/Linux",
                          verified=True),
    "channels":      dict(value="3", label="delivery channels",
                          source="email, SMS, WhatsApp", verified=True),
    "custody":       dict(value="0", label="funds held by Priv",
                          source="OAuth to your own broker", verified=True),
}

# ------------------------------------------------------- compliance guard ----
# Phrases that generated Zeely's loudest one-star reviews, plus the language
# that would get a trading product rejected by Meta / App Store / Trustpilot.
BANNED = [
    "guaranteed", "guarantee", "risk-free", "risk free", "no risk",
    "can't lose", "cannot lose", "never lose", "always wins", "always win",
    "99% win", "99% accuracy", "double your money", "double your account",
    "risk-free profit", "passive income", "get rich", "financial freedom in",
    "free money", "profit potential", "win rate of", "secret strategy",
    "forbidden knowledge", "100% profit", "money back", "free trial",
    "cancel anytime", "as seen on", "no downside", "beats the market",
    "set and forget", "print money", "life-changing returns",
]

# Numeric claims require a registry key (Zeely-style proof must be sourced).
_NUM_CLAIM = re.compile(r"(\d+(?:\.\d+)?\s*%|\$\d|\b\d{2,}[xX]\b)")


def get(key):
    return STATS.get(key)


def line(key, with_source=False):
    s = STATS.get(key)
    if not s:
        raise KeyError(key)
    out = f"{s['value']} {s['label']}".strip()
    if with_source:
        out += f"  [{s['source']}]"
    return out


def proof(keys, sep=" · "):
    return sep.join(line(k) for k in keys)


def verified_stats():
    return {k: v for k, v in STATS.items() if v["verified"]}


def guard(text, allow_numbers=False):
    """Return a list of compliance violations in `text`. Empty list == pass."""
    low = (text or "").lower()
    hits = [b for b in BANNED if b in low]
    if not allow_numbers:
        for m in _NUM_CLAIM.finditer(text or ""):
            if not _sourced(m.group(0)):
                hits.append(f"unsourced number: {m.group(0)}")
    return hits


def _sourced(token):
    t = token.replace("%", "").replace("$", "").strip().lower()
    for s in STATS.values():
        v = str(s["value"]).replace("%", "").replace("$", "").lower()
        if v and v in t:
            return True
        if str(s["value"]).lower() in t:
            return True
    return False


def require_clean(text, where=""):
    v = guard(text)
    if v:
        raise ValueError(f"compliance block{' on ' + where if where else ''}: "
                         + "; ".join(v))
    return text


def risk_block(kind="page"):
    if kind == "ad":
        return DISCLAIMER
    return (f"<p class=\"risk\">{DISCLAIMER} Priv connects to your own broker "
            f"through official OAuth and holds no client funds. "
            f"<a href=\"{SITE_FULL}/risk\">Read the full risk disclosure</a>.</p>")
