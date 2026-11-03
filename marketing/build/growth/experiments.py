"""Creative experiment ledger: build the batch, predict, record, promote.

Implements Zeely's doctrine end to end:
  * Batch Mode -- one input -> up to 20 variants
  * "A/B test at least 3 creatives, mixing static and video"
  * rank by CTR / CPC / CPA / ROAS, spot early winners, detect fatigue
  * plain-language explanation of every number
"""
import json
import math
import os
import random
import time

DEFAULT_LIMIT = 20
FORMATS = ("static", "video", "carousel", "landing")
FACTORS = ("hook", "headline", "cta", "format", "angle")


def matrix(base, factors=None, limit=DEFAULT_LIMIT):
    """Cartesian creative batch. `base` supplies defaults, factors supply runs.

    factors = {"hook": [...], "cta": [...], "format": ["static","video"]}
    Keeps at least two formats (Zeely: "mix static and video").
    """
    factors = factors or {}
    keys = [k for k in FACTORS if factors.get(k)]
    variants, n = [], 0
    if not keys:
        keys, factors = ["hook"], {"hook": [base.get("hook", "Untitled")]}
    def walk(i, cur):
        nonlocal n
        if n >= limit:
            return
        if i == len(keys):
            v = dict(base, **cur)
            v["id"] = _vid(v, n)
            v["predicted"] = predict(v)
            variants.append(v)
            n += 1
            return
        k = keys[i]
        for val in factors[k]:
            walk(i + 1, dict(cur, **{k: val}))
            if n >= limit:
                return
    walk(0, {})
    variants = _enforce_formats(variants, factors)
    variants.sort(key=lambda v: -v["predicted"])
    return variants[:limit]


def _vid(v, n):
    import hashlib
    import json as _json
    # format + angle go first so they survive slug truncation (select() reads them)
    raw = (f"{v.get('format','')}|{v.get('angle','')}|{v.get('hook','')[:30]}"
           f"|{v.get('headline','')[:20]}|{v.get('cta','')[:12]}")
    slug = "".join(c if c.isalnum() else "-" for c in raw.lower()).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    digest = hashlib.md5(
        _json.dumps({k: v.get(k) for k in FACTORS}, sort_keys=True).encode()
    ).hexdigest()[:6]
    return f"{slug[:54].rstrip('-')}-{digest}"


def _enforce_formats(variants, factors):
    allowed = set(factors.get("format") or FORMATS)
    present = {v.get("format") for v in variants}
    if len(allowed) > 1 and len(present) < 2 and variants:
        want = [f for f in FORMATS if f in allowed][:2]
        for i, f in enumerate(want):
            if f not in present and i < len(variants):
                variants[i]["format"] = f
                present.add(f)
    return variants


def predict(v):
    """0-100 pre-spend score. Zeely: "predicts before you spend"."""
    from . import hooks
    s = hooks.score(v.get("hook") or v.get("headline") or "")
    h = (v.get("headline") or "")
    if 12 <= len(h.split()) <= 22:
        s += 8
    if v.get("cta"):
        s += 8
    if v.get("format") == "video":
        s += 6          # short-form video carries the hook better
    elif v.get("format") == "carousel":
        s += 3
    if v.get("angle"):
        s += 5
    return max(0, min(100, s))


# ------------------------------------------------------------------ ledger --
def default_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(here)),
                        "assets", "growth", "ledger.json")


def load(path=None):
    path = path or os.environ.get("GROWTH_LEDGER") or default_path()
    if not os.path.exists(path):
        return dict(updated=0, variants={}, meta=[])
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(ledger, path=None):
    path = path or os.environ.get("GROWTH_LEDGER") or default_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ledger["updated"] = int(time.time())
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2, sort_keys=True)
    return path


def register(variants, ledger=None, path=None):
    ledger = ledger if ledger is not None else load(path)
    for v in variants:
        ledger["variants"].setdefault(v["id"], dict(
            variant=v, created=int(time.time()), impressions=0, clicks=0,
            conversions=0, spend=0.0, revenue=0.0, history=[], status="active"))
    return ledger


def record(variant_id, impressions=0, clicks=0, conversions=0, spend=0.0,
           revenue=0.0, ledger=None, path=None):
    ledger = ledger if ledger is not None else load(path)
    e = ledger["variants"].get(variant_id)
    if not e:
        raise KeyError(variant_id)
    e["impressions"] += impressions
    e["clicks"] += clicks
    e["conversions"] += conversions
    e["spend"] += spend
    e["revenue"] += revenue
    e["history"].append(dict(t=int(time.time()), impressions=impressions,
                             clicks=clicks, conversions=conversions,
                             spend=spend, revenue=revenue))
    if e["impressions"] >= 500 and metrics(e)["ctr"] < 0.005:
        e["status"] = "fatigued"
    return ledger


def metrics(e):
    imp, clk, cv = e["impressions"], e["clicks"], e["conversions"]
    spend, rev = e["spend"], e["revenue"]
    return dict(
        ctr=(clk / imp) if imp else 0.0,
        cpc=(spend / clk) if clk else 0.0,
        cpa=(spend / cv) if cv else 0.0,
        roas=(rev / spend) if spend else 0.0,
        conversions=cv,
    )


def rank(ledger=None, path=None):
    ledger = ledger if ledger is not None else load(path)
    rows = []
    for vid, e in ledger["variants"].items():
        m = metrics(e)
        rows.append(dict(id=vid, status=e["status"], predicted=e["variant"].get("predicted", 0), **m))
    rows.sort(key=lambda r: (-_quality(r), -r["ctr"], -r["roas"]))
    return rows


def _quality(r):
    # UCB-ish: reward observed performance, keep under-tested variants alive
    base = r["ctr"] * 100 + r["roas"] * 0.5 - (r["cpa"] or 0) * 0.01
    n = max(1, r.get("conversions", 0) + int(r["ctr"] * 1000))
    return base + 0.25 * math.sqrt(math.log(n + 1) / n)


def _fmt(vid):
    for f in ("carousel", "video", "static", "landing"):
        if f in vid:
            return f
    return ""


def select(k=3, ledger=None, path=None, mix_formats=True):
    """Choose the next k variants to run: exploit the best, explore the rest."""
    rows = [r for r in rank(ledger, path) if r["status"] == "active"]
    if not rows:
        return []
    chosen = [rows[0]]
    seen = {_fmt(rows[0]["id"])}
    for r in rows[1:]:
        if len(chosen) >= k:
            break
        f = _fmt(r["id"])
        if mix_formats and len(seen) < 2 and f in seen:
            continue
        chosen.append(r)
        seen.add(f)
    return chosen[:k]


def fatigue(ledger=None, path=None):
    """Variants whose CTR decayed across the last three flights."""
    ledger = ledger if ledger is not None else load(path)
    out = []
    for vid, e in ledger["variants"].items():
        h = e.get("history") or []
        if len(h) >= 3:
            ctrs = [(x["clicks"] / x["impressions"]) if x["impressions"] else 0
                    for x in h[-3:]]
            if ctrs[0] > 0 and ctrs[-1] < ctrs[0] * 0.6:
                out.append(vid)
    return out


def explain(entry_or_row):
    """One sentence a non-marketer can act on (Zeely's 7th-grader rule)."""
    if isinstance(entry_or_row, dict) and "ctr" in entry_or_row:
        m = entry_or_row
    else:
        m = metrics(entry_or_row)
    if not m.get("ctr") and not m.get("conversions"):
        return "Not enough eyes on this one yet to say anything useful."
    if m["roas"] >= 2.0:
        return (f"For every $1 spent this returned ${m['roas']:.2f}. "
                f"Put more behind it.")
    if m["ctr"] >= 0.03 and m["cpa"] and m["cpa"] > 0:
        return ("People stop and click, but few buy afterwards -- the ad "
                "promises more than the page delivers. Fix the landing page.")
    if m["ctr"] < 0.01:
        return "Almost nobody stopped scrolling. Change the first line, keep everything else."
    return "Doing fine but not winning yet. Let it run a little longer."
