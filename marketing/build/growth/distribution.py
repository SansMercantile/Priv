"""Video distribution packs -- one ready-to-upload bundle per master.

The MP4s in `assets/videos/` are cut once and pushed everywhere: YouTube,
TikTok, Instagram Reels, Facebook, X, LinkedIn and a WhatsApp share line.
Every pack carries the public URL platforms can pull from plus native copy
composed by `social.post()`, so the compliance gate applies to video copy
exactly as it does to feed posts.

Always staged to the outbox: auto-uploading video needs platform credentials
that do not exist yet (and `CH_SOCIAL` gates the publish path regardless).
"""
import datetime
import os
import re

from . import channels, social, stats

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets")
VIDEOS = os.path.join(ASSETS, "videos")
PUBLIC = "https://priv.sansmercantile.com/marketing-assets/videos"

# angle -> (hook, body). Keys are matched against the filename.
ANGLES = {
    "custody": ("Your money never leaves your own broker.",
                "Priv connects to your own broker through official OAuth and "
                "holds no client funds. Your money stays yours."),
    "modes":   ("One market. Seven timeframes.",
                "1m to 1D on the same instrument — when they disagree, the "
                "disagreement is the signal, not a bug."),
    "signal":  ("Every ticket ships complete.",
                "Entry, TP1, TP2 and a stop that trails to breakeven — "
                "never a bare buy/sell line."),
    "hook":    ("Nobody taught you this in demo.",
                "Write the exit before the entry. Every setup ships with the "
                "stop already stated."),
    "proof":   ("Prove it before you risk it.",
                "Backtest the strategy on the same seven timeframes the desk "
                "watches, then run it. Auditable every run."),
    "desk":    ("An autonomous trading desk, in your pocket.",
                "Five deliberating agents, a 28-second decision cycle and "
                "signals delivered the moment a setup resolves."),
    "explainer": ("Priv, explained in sixty seconds.",
                "Live signals, strategy backtesting, multi-agent execution "
                "and full custody — in one app."),
    "hero":    ("Entry. Two targets. One stop.",
                "The whole ticket is stated before you enter. No bare lines, "
                "no guessing the exit."),
    "teaser":  ("Your exit is stated before you enter.",
                "Entry, two targets and a stop — the moment the setup "
                "resolves."),
    "bumper":  ("Start free. No card required.",
                "One market, seven timeframes, full custody of your money."),
}
FALLBACK = ("demo", "Most people learn this after a bad week.")

VIDEO_PLATFORMS = {
    "vertical": ["youtube", "tiktok", "instagram", "facebook", "x",
                 "linkedin", "whatsapp"],
    "wide":     ["youtube", "facebook", "x", "linkedin", "whatsapp"],
}


def _angle(name):
    for key in ANGLES:
        if key in name:
            return key
    return "hero"


def _meta(name):
    seconds = re.search(r"-(\d+)s-", name)
    return dict(
        seconds=int(seconds.group(1)) if seconds else None,
        orientation="vertical" if "vertical" in name else "wide",
        kind="ad" if name.startswith("priv-ad-") else "campaign",
    )


def pack(path):
    name = os.path.basename(path)
    m = _meta(name)
    angle = _angle(name)
    hook, body = ANGLES.get(angle, FALLBACK)
    stats.require_clean(f"{hook} {body}", where=f"video/{name}")
    url = f"{PUBLIC}/{name}"

    copy = {}
    for plat in VIDEO_PLATFORMS[m["orientation"]]:
        post = social.post(plat, hook=hook, body=body,
                           cta="Start free — no card required",
                           angle=angle, kind="product",
                           disclose=(plat == "reddit"))
        post["video"] = url                     # platforms that ingest a file
        if plat == "youtube":
            post["title"] = _trim(hook + " | Priv", 100)
        copy[plat] = post

    return dict(file=name, url=url, angle=angle, hook=hook, **m, copy=copy)


def _trim(text, limit):
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def build():
    """Compose a pack for every master and stage the bundle to the outbox."""
    if not os.path.isdir(VIDEOS):
        return dict(channel="distribution", status="skipped", packs=0,
                    reason="no videos directory")
    files = sorted(f for f in os.listdir(VIDEOS) if f.lower().endswith(".mp4"))
    packs = [pack(os.path.join(VIDEOS, f)) for f in files]
    payload = dict(generated=datetime.datetime.utcnow().isoformat() + "Z",
                   policy="Staged for upload. Copy is compliance-gated; "
                          "paste per platform or wire a publisher token.",
                   base=PUBLIC, packs=packs)
    staged = channels._stage("distribution", payload)
    return dict(channel="distribution", status="prepared", packs=len(packs),
                platforms=sorted({p for k in packs for p in k["copy"]}),
                detail=staged)
