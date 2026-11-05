"""URL-to-video: paste a product/page link, get a rendered ad.

Creatify's flagship, rebuilt in-house. The flow is entirely our own stack:

  1. fetch the page (title, meta description, hero text, price-ish signals)
  2. our Script Writer turns that brief into a scene-by-scene ad script
  3. the creative engine (cartoon / doodle / presenter) renders it to a master

No third-party creative API. The script passes the same compliance guard as
every other line we ship, and the caller picks the style + orientation.
"""
import html
import json
import os
import re
import urllib.error
import urllib.request

import ads
import engine_assemble as EA  # noqa: F401  (kept for parity with styles)

UA = ("Mozilla/5.0 (compatible; Priv-URL2Video/1.0; "
      "+https://priv.sansmercantile.com)")


def fetch_page(url, timeout=25):
    """Pull the page and reduce it to a compact creative brief."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(400000).decode("utf-8", "replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"could not fetch {url}: {e}") from e

    def _meta(name):
        m = re.search(
            rf'<meta[^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\']'
            rf'[^>]+content=["\']([^"\']+)["\']', raw, re.I)
        if not m:  # content-first attribute order
            m = re.search(
                rf'<meta[^>]+content=["\']([^"\']+)["\']'
                rf'[^>]+(?:name|property)=["\'](?:og:)?{re.escape(name)}["\']',
                raw, re.I)
        return html.unescape(m.group(1)).strip() if m else ""

    title = _meta("title") or _title(raw)
    desc = _meta("description")
    # visible text: strip scripts/styles/tags, collapse whitespace
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    body = html.unescape(re.sub(r"\s+", " ", body)).strip()
    # price-ish signals help the script writer anchor on the offer
    prices = re.findall(r"\$\s?\d+(?:\.\d{2})?", body)[:6]

    return {
        "url": url,
        "title": title[:160],
        "description": desc[:400],
        "text": body[:4000],
        "prices": prices,
    }


def _title(raw):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


# prompt the Script Writer with the brief; it returns a scene list JSON.
_SCRIPT_PROMPT = """You are the in-house copywriter for a video ad.
Write a {scenes}-scene {style} ad script for this product/offer, as strict JSON
only (no preamble, no markdown fences): an array of {{"vo": "..."}} objects,
each `vo` a short punchy spoken line (5-12 words). End with a final scene whose
`vo` is a call to action and which also has "end": true.

House voice: confident, concrete, no hype, short sentences, trading-native.
Never claim guaranteed wins, risk-free profit, or a win rate.

PRODUCT BRIEF:
Title: {title}
Description: {description}
Key page text: {text}
Prices seen: {prices}
URL: {url}

Return ONLY the JSON array."""


def draft_script(brief, style, scenes, generate):
    """Turn the brief into a scene list via the app's AI provider."""
    prompt = _SCRIPT_PROMPT.format(
        scenes=scenes, style=style, title=brief["title"],
        description=brief["description"], text=brief["text"][:2500],
        prices=", ".join(brief["prices"]) or "none visible", url=brief["url"])
    text = generate(prompt)
    return _parse_scenes(text)


def _parse_scenes(text):
    """Tolerant JSON-array extraction from the model's reply."""
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        raise RuntimeError("script writer returned no scene array")
    data = json.loads(m.group(0))
    scenes = []
    for s in data:
        if not isinstance(s, dict) or not s.get("vo"):
            continue
        sc = {"vo": str(s["vo"]).strip()}
        if s.get("end"):
            sc["end"] = True
        scenes.append(sc)
    if not scenes:
        raise RuntimeError("script writer returned an empty scene list")
    # every line must pass the compliance guard before it is rendered
    from growth.stats import require_clean
    for sc in scenes:
        require_clean(sc["vo"], where="url2video")
    return scenes


def build(url, cfg, generate):
    """Full URL->master. cfg carries style/size/target/out/name/seed; generate
    is the app's AI text generator (setEngineAI closure)."""
    style = cfg.get("style", "doodle")
    import importlib
    mod = importlib.import_module(style)

    print(f"\n=== url2video {url}  [{style}] ===")
    brief = fetch_page(url)
    print(f"  brief  {brief['title'][:60]!r}  ({len(brief['text'])} chars)")
    scenes = draft_script(brief, style, int(cfg.get("scenes", 5)), generate)
    print(f"  script {len(scenes)} scenes")
    for i, sc in enumerate(scenes, 1):
        print(f"    {i:02d} {'END ' if sc.get('end') else '    '}{sc['vo'][:70]}")

    out_cfg = dict(cfg)
    out_cfg["scenes"] = scenes
    out_cfg.setdefault("target", 30)
    return mod.build(cfg.get("name") or f"url2video-{style}", out_cfg)
