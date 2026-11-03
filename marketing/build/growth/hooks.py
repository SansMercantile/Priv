"""Hook library, copy frameworks, and first-3-seconds scoring.

Zeely ships "130+ smart hook formats" and exposes the frameworks by name
(AIDA, PAS, Before-After-Bridge, 4U, FAB, Problem-Solution, Three Reasons Why).
This module is the Priv equivalent: deterministic, no LLM required, so the
Lambda can generate compliant copy on every run without a model call.
"""
import re

POWER = ("steal", "secret", "mistake", "before", "stop", "nobody", "quiet",
         "missed", "hidden", "proven", "fast", "free", "sleep", "quietly",
         "actually", "worst", "best", "simple", "one")

ANGLES = ["problem", "curiosity", "contrast", "mechanism", "proof",
          "urgency", "identity", "fomo", "quantified", "objection"]

# (text, angle, kind)  -- kind: hook | claim | caption
HOOKS = [
    ("Waiting for your setup?", "problem", "hook"),
    ("Most traders react. Priv traders wait.", "contrast", "hook"),
    ("You don't need more indicators.", "problem", "hook"),
    ("Your setup already fired. You just weren't looking.", "problem", "hook"),
    ("Entry. Two targets. One stop.", "mechanism", "hook"),
    ("The stop moves the second target prints.", "mechanism", "hook"),
    ("Five agents. One quorum. No order moves alone.", "mechanism", "hook"),
    ("Prove it before you risk it.", "objection", "hook"),
    ("Arm it. Sleep. Let the desk work.", "identity", "hook"),
    ("28 seconds. That's the whole decision cycle.", "quantified", "hook"),
    ("One market. Seven timeframes.", "quantified", "hook"),
    ("Free signals every day. No card.", "urgency", "hook"),
    ("Your account. Your funds. Your control.", "objection", "hook"),
    ("The alert lands before you open the chart.", "speed", "hook"),
    ("Nobody taught you this in demo.", "curiosity", "hook"),
    ("This is what a clean risk ticket looks like.", "contrast", "hook"),
    ("Stop guessing the stop.", "problem", "hook"),
    ("You are not disciplined. You are unstructured.", "identity", "hook"),
    ("Backtest it. Then arm it.", "mechanism", "hook"),
    ("Charts don't sleep at 3am. Neither does Priv.", "proof", "hook"),
    ("Your edge is a process, not a prediction.", "identity", "hook"),
    ("Every signal ships complete.", "mechanism", "hook"),
    ("What if the desk closed its own position?", "curiosity", "hook"),
    ("The difference between a plan and a hope.", "contrast", "hook"),
    ("Risk is a number you choose, not a feeling.", "identity", "hook"),
    ("If you can't backtest it, don't trade it.", "objection", "hook"),
]

FRAMEWORKS = ("PAS", "AIDA", "BAB", "4U", "FAB", "3R", "PROBLEM_SOLUTION", "HBC")


def generate(angle=None, n=6, min_score=0):
    """Top-N hooks for an angle (or across all angles), ranked by score()."""
    pool = [h for h in HOOKS if angle is None or h[1] == angle]
    ranked = sorted(pool, key=lambda h: -score(h[0]))
    return [dict(text=t, angle=a, kind=k, score=score(t))
            for t, a, k in ranked if score(t) >= min_score][:n]


def score(text):
    """0-100 first-3-seconds score. Higher = better opener."""
    if not text:
        return 0
    words = re.findall(r"[A-Za-z0-9'$%]+", text)
    n = len(words)
    s = 0
    # length: the sweet spot is 4-11 words
    if n <= 11:
        s += 26
    elif n <= 16:
        s += 14
    # openers that pull
    if text.lstrip().startswith("?") or text.split()[0].lower() in (
            "waiting", "what", "why", "how", "stop", "nobody", "most"):
        s += 14
    if re.match(r"^\s*\d", text):
        s += 12
    if ":" in text or "." in text.rstrip() and text.count(".") >= 1 and n <= 9:
        s += 8
    # second person / specificity
    if re.search(r"\byou\b|\byour\b", text, re.I):
        s += 12
    if re.search(r"\d", text):
        s += 8
    if re.search(r"\b(never|before|already|quietly|actually|still)\b", text, re.I):
        s += 6
    # power word
    if any(w in text.lower() for w in POWER):
        s += 8
    # brand name in line one is a tax
    if re.search(r"\bpriv\b|\bsans mercantile\b", text, re.I):
        s -= 10
    # penalties
    if n > 18:
        s -= 12
    if text.endswith("!"):
        s -= 4
    return max(0, min(100, s))


def write(framework, *, problem="", agitate="", solution="", before="",
          after="", bridge="", feature="", advantage="", benefit="",
          reasons=(), hook="", cta="", proof="", audience=""):
    """Compose {hook, body, cta, full} using a named framework."""
    fw = framework.upper()
    if fw == "PAS":
        body = f"{problem} {agitate} {solution}".strip()
    elif fw == "AIDA":
        body = f"{problem} {agitate} {solution} {benefit}".strip()
    elif fw == "BAB":
        body = f"Before: {before} After: {after} Bridge: {bridge}".strip()
    elif fw == "4U":
        body = f"{benefit} for {audience or 'you'} — {proof} {agitate}".strip()
    elif fw == "FAB":
        body = f"{feature}. That means {advantage}, so {benefit}".strip()
    elif fw in ("3R", "THREE_REASONS"):
        rs = list(reasons) or ["it is structured", "it is testable",
                               "it stays yours"]
        body = "Three reasons: " + "; ".join(f"{i + 1}) {r}"
                                             for i, r in enumerate(rs[:3]))
    elif fw in ("PROBLEM_SOLUTION", "PS"):
        body = f"{problem} The fix: {solution}".strip()
    elif fw == "HBC":           # Zeely's own hook -> body -> CTA structure
        body = solution
    else:
        raise ValueError(f"unknown framework: {framework}")

    h = hook or (generate(n=1)[0]["text"] if not problem else _hook_from(problem))
    c = cta or "Start free — no card required"
    full = f"{h} {body} {c}".strip()
    return dict(framework=fw, hook=h, body=body, cta=c, full=full,
                hook_score=score(h))


def _hook_from(problem):
    p = problem.strip().rstrip(".")
    return (p.split(".")[0] + "?") if p else "Waiting for your setup?"


def variants(framework, facts, angles=ANGLES, limit=12):
    """Generate ranked framework x hook combinations for an experiment matrix."""
    out = []
    for a in angles[:limit]:
        for h in generate(angle=a, n=2):
            out.append(write(framework, hook=h["text"], **facts))
    out.sort(key=lambda d: -d["hook_score"])
    return out[:limit]


def safe_area_lines(text, max_chars=90):
    """Split a hook into caption lines that stay inside the 9:16 safe box."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines
