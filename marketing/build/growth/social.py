"""Organic social: post composition, carousels, threads, and a weekly calendar.

Zeely's organic layer = "social posting / schedule and publish / TikTok trends
/ carousel posts". Ours is deterministic and disclosure-first: Reddit and
Hacker News posts are never generated without an explicit self-promotion tag,
because Zeely's loudest channel is also the one that roasted them.
"""
import datetime

from . import hooks, stats

PLATFORMS = {
    "x":       dict(name="X", limit=280, tags=4, tone="blunt"),
    "linkedin": dict(name="LinkedIn", limit=3000, tags=5, tone="professional"),
    "reddit":   dict(name="Reddit", limit=4000, tags=0, tone="plain",
                     disclose_required=True),
    "tiktok":   dict(name="TikTok", limit=2200, tags=5, tone="spoken"),
    "instagram": dict(name="Instagram", limit=2200, tags=10, tone="visual"),
    "youtube":  dict(name="YouTube", limit=5000, tags=8, tone="descriptive"),
    "facebook": dict(name="Facebook", limit=5000, tags=0, tone="conversational"),
    "whatsapp": dict(name="WhatsApp", limit=1024, tags=0, tone="spoken",
                     share_only=True),
}

TAG_SETS = {
    "trading": ["trading", "forex", "propfirms", "algotrading", "fintech"],
    "build":   ["buildinpublic", "fintech", "indiehacker", "saas"],
    "product": ["productlaunch", "markets", "technicalsanalysis"],
}

DISCLOSURE = "[I built this] "


def _tags(kind, platform):
    spec = PLATFORMS[platform]
    pool = TAG_SETS.get(kind, TAG_SETS["trading"])
    if platform == "x":
        return [f"#{t}" for t in pool[:3]]
    if platform == "reddit":
        return []
    return pool[: spec["tags"]]


def post(platform, *, hook, body, cta="", angle="", kind="trading",
         disclose=False, url=None):
    """Compose a platform-native post. Raises if compliance or rules fail."""
    if platform not in PLATFORMS:
        raise ValueError(f"unknown platform: {platform}")
    spec = PLATFORMS[platform]
    stats.require_clean(f"{hook} {body} {cta}", where=f"post/{platform}")

    if spec.get("disclose_required") and not disclose:
        raise ValueError(f"{platform} requires disclose=True (self-promotion tag)")

    tags = _tags(kind, platform)
    link = url or stats.SITE_FULL

    if platform == "x":
        text = f"{hook}\n\n{body}"
        if cta:
            text += f"\n\n{cta} → {link}"
        text += "\n" + " ".join(tags)
        text = _trim(text, spec["limit"])
    elif platform == "linkedin":
        text = f"{hook}\n\n{body}\n\n"
        if cta:
            text += f"{cta}\n{link}\n\n"
        text += "\n".join(t if t.startswith("#") else f"#{t}" for t in tags)
        text = _trim(text, spec["limit"])
    elif platform == "reddit":
        text = f"{DISCLOSURE}{hook}\n\n{body}"
        text = _trim(text, spec["limit"])
    elif platform == "tiktok":
        text = f"{hook}\n{body}"
        if cta:
            text += f"\n{cta}"
        text += "\n" + " ".join(f"#{t}" for t in tags)
        text = _trim(text, spec["limit"])
    elif platform == "instagram":
        text = f"{hook}\n\n{body}\n"
        if cta:
            text += f"🔗 {link}\n"
        text += " ".join(f"#{t}" for t in tags)
        text = _trim(text, spec["limit"])
    elif platform == "facebook":
        text = f"{hook}\n\n{body}"
        if cta:
            text += f"\n\n{cta} → {link}"
        text = _trim(text, spec["limit"])
    elif platform == "whatsapp":
        text = f"{hook}\n\n{body}"
        if cta:
            text += f"\n{cta}: {link}"
        text = _trim(text, spec["limit"])
    else:  # youtube
        text = f"{hook}\n\n{body}\n\n{cta or 'Start free'}: {link}\n\n" \
               + " ".join(f"#{t}" for t in tags)
        text = _trim(text, spec["limit"])

    return dict(platform=platform, text=text, chars=len(text), hook=hook,
                hook_score=hooks.score(hook), angle=angle,
                tags=tags, disclosed=bool(disclose and spec.get("disclose_required")))


def _trim(text, limit):
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    return cut.rsplit(" ", 1)[0] + "…"


def thread(steps, platform="x"):
    """Split a long narrative into a numbered thread."""
    out, buf, n = [], "", 1
    for s in steps:
        cand = f"{n}/{len(steps)} {s}"
        if len(buf) + len(cand) + 2 > PLATFORMS[platform]["limit"]:
            out.append(buf.strip())
            n += 1
            buf = f"{n}/{len(steps)} {s}\n"
        else:
            buf += ("\n" if buf else "") + cand
    if buf:
        out.append(buf.strip())
    return out


def carousel(title, points, platform="instagram", cta=""):
    """Slide spec list — rendering is handled by the poster engine."""
    slides = [dict(index=1, kind="cover", text=title, sub=hooks.generate(n=1)[0]["text"])]
    for i, p in enumerate(points, start=2):
        slides.append(dict(index=i, kind="point", text=p))
    slides.append(dict(index=len(points) + 2, kind="cta",
                       text=cta or "Start free — no card required",
                       sub=stats.SITE))
    for s in slides:
        stats.require_clean(s["text"], where=f"carousel/{s['index']}")
    return dict(platform=platform, slides=slides,
                caption=post(platform, hook=title,
                             body=" ".join(points[:2]), cta=cta)["text"])


ROTATION = {
    0: ("create",  "hook-of-the-day"),      # Monday
    1: ("create",  "educational"),          # Tuesday
    2: ("launch",  "product-proof"),        # Wednesday
    3: ("scale",   "social-proof"),         # Thursday
    4: ("create",  "objection-handling"),   # Friday
    5: ("launch",  "use-case"),             # Saturday
    6: ("scale",   "recap"),                # Sunday
}


def calendar(days=7, start=None):
    """A week of planned posts: Zeely's create -> launch -> scale cadence."""
    start = start or datetime.date.today()
    out = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        stage, theme = ROTATION[d.weekday()]
        h = hooks.generate(n=1)[0]
        out.append(dict(date=d.isoformat(), weekday=d.strftime("%A"),
                        stage=stage, theme=theme, hook=h["text"],
                        angle=h["angle"], score=h["score"],
                        platforms=_platforms_for(theme)))
    return out


def _platforms_for(theme):
    if theme in ("hook-of-the-day", "use-case"):
        return ["tiktok", "instagram", "x", "facebook", "whatsapp"]
    if theme == "social-proof":
        return ["linkedin", "x", "instagram", "facebook"]
    if theme == "objection-handling":
        return ["linkedin", "reddit"]
    if theme == "educational":
        return ["x", "linkedin", "youtube"]
    return ["x", "linkedin"]


def post_for(entry, kind="trading"):
    """Turn a calendar entry into concrete platform posts."""
    plan = []
    body = _BODY[entry["theme"]]
    for p in entry["platforms"]:
        plan.append(post(p, hook=entry["hook"], body=body,
                         cta="Start free — no card required", angle=entry["angle"],
                         kind=kind, disclose=(p == "reddit")))
    return plan


# NOTE: post() already renders the hook as the opening line -- these are the
# follow-on body lines, so they must not repeat it.
_BODY = {
    "hook-of-the-day": "Most people learn this after a bad week. The short "
                       "version: write the exit before the entry.",
    "educational": "Seven timeframes, one instrument — when they disagree, the "
                   "disagreement is the signal, not a bug.",
    "product-proof": "Every ticket ships entry, TP1, TP2 and a stop that trails "
                     "to breakeven. No bare buy lines.",
    "social-proof": "The part people repeat back to us is the custody line: "
                    "their money never leaves their own broker.",
    "objection-handling": "We do not claim it wins. We claim it is structured, "
                          "testable and auditable — which is rarer.",
    "use-case": "Built for the trader with a day job and thirty free minutes.",
    "recap": "A week of setups, seven timeframes, one desk. Same rules every "
             "time — that is the point.",
}
