"""Paid media: campaign briefs and launch payloads for Meta and TikTok.

Zeely's paid layer = goal -> budget -> audience -> "A/B test at least 3
creatives, static + video" -> launch -> rank by CTR/CPA/ROAS.

Two hard rules here that Zeely does not have, because we sell a trading
product: (1) copy passes stats.guard() before a payload is even built, and
(2) nothing is ever spent unless CH_PAID=publish AND an ad token is present.
"""
import json

from . import experiments, stats

OBJECTIVES = ("LEADS", "TRAFFIC", "CONVERSIONS", "APP_INSTALLS")
PLATFORMS = ("META", "TIKTOK")

REQUIRED = ("objective", "daily_budget", "geo", "age_min", "age_max", "variants")


def campaign(name, *, objective, daily_budget, geo, age_min=25, age_max=54,
             audience=None, variants=None, placement=("facebook", "instagram"),
             platform="META", notes=""):
    """Build a validated campaign brief. Raises on missing gates or bad copy."""
    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {OBJECTIVES}")
    for f in REQUIRED:
        if f == "variants":
            continue
        if locals().get(f) in (None, (), []):
            raise ValueError(f"campaign.{f} is required (launch gate)")
    if int(daily_budget) < 10:
        raise ValueError("daily_budget must be >= 10 (micro-USD or USD units)")

    variants = variants or experiments.matrix(
        dict(headline="Entry. Two targets. One stop.",
             cta="Start free — no card required", format="static"),
        factors=dict(hook=[h["text"] for h in hooks_top(3)],
                     cta=["Start free — no card required",
                          "Open priv.sansmercantile.com",
                          "Connect your broker"],
                     format=["static", "video"]),
        limit=6)

    for v in variants:
        blob = " ".join(str(v.get(k, "")) for k in
                        ("hook", "headline", "body", "cta"))
        stats.require_clean(blob, where=f"variant/{v.get('id')}")

    return dict(
        name=name, platform=platform, objective=objective,
        daily_budget=int(daily_budget), currency="USD",
        geo=list(geo) if not isinstance(geo, str) else [geo],
        age_min=int(age_min), age_max=int(age_max),
        audience=audience or dict(interests=[
            dict(name="Forex trading"), dict(name="Day trading"),
            dict(name="Technical analysis"), dict(name="Algorithmic trading"),
            dict(name="Financial markets")]),
        placements=list(placement), variants=variants,
        landing=stats.SITE_FULL,
        disclaimer=stats.DISCLAIMER,
        status="ready", notes=notes,
        rules=dict(min_spend_no_conversion=3.0,
                   kill_ctr_below=0.005,
                   scale_ctr_above=0.03,
                   rotate_every_days=7),
    )


def hooks_top(n):
    from . import hooks
    return hooks.generate(n=n)


def meta_payload(brief):
    """Shaped for the Meta Marketing API (POST /act_<id>/campaigns)."""
    _check(brief, "META")
    v = brief["variants"]
    return {
        "campaign": {
            "name": brief["name"],
            "objective": brief["objective"],
            "status": "PAUSED",          # never auto-live
            "special_ad_categories": [],  # add FINANCIAL_SERVICES if required
        },
        "adset": {
            "name": f"{brief['name']} · {brief['geo']}",
            "billing_event": "IMPRESSIONS",
            "optimization_goal": ("LEAD_GENERATION"
                                  if brief["objective"] == "LEADS"
                                  else "LINK_CLICKS"),
            "daily_budget": brief["daily_budget"],
            "start_time": "now",
            "targeting": {
                "geo_locations": {"countries": brief["geo"]},
                "age_min": brief["age_min"], "age_max": brief["age_max"],
                "publisher_platforms": brief["placements"],
                "flexible_spec": [{"interests": [
                    {"id": i.get("id", i.get("name")),
                     "name": i["name"]}
                    for i in brief["audience"]["interests"]]}],
            },
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "status": "PAUSED",
        },
        "creatives": [
            {
                "name": f"{brief['name']} · {c.get('format')} · {i}",
                "creative": {
                    "object_story_spec": {
                        "page_id": "${PAGE_ID}",
                        "link_data": {
                            "message": c.get("hook") or c.get("headline", ""),
                            "name": c.get("headline", ""),
                            "description": c.get("body", "")[:150],
                            "link": brief["landing"],
                            "caption": stats.SITE,
                            "call_to_action_action_type": {
                                "static": "LEARN_MORE",
                                "video": "WATCH_MORE",
                                "carousel": "LEARN_MORE",
                            }.get(c.get("format", "static"), "LEARN_MORE"),
                        },
                    },
                    "degrees_of_freedom_spec": {
                        "creative_features_spec": {"standard_enhancements":
                                                   {"enroll_status": "OPT_OUT"}}
                    },
                },
                "status": "PAUSED",
            }
            for i, c in enumerate(v)
        ],
        "rules": brief["rules"],
        "disclaimer": brief["disclaimer"],
    }


def tiktok_payload(brief):
    _check(brief, "TIKTOK")
    return {
        "campaign": {
            "name": brief["name"], "objective": brief["objective"],
            "budget_mode": "DAILY", "budget": brief["daily_budget"],
            "status": "INACTIVE",
        },
        "adgroup": {
            "name": f"{brief['name']} · {brief['geo']}",
            "placements": ["AUTOMATIC_OFFICIAL"],
            "location": brief["geo"],
            "age": [brief["age_min"], brief["age_max"]],
            "schedule_type": "SCHEDULE_FROM_NOW",
            "status": "INACTIVE",
        },
        "ads": [
            {"ad_name": f"{brief['name']} · {c.get('format')} · {i}",
             "text": (c.get("hook") or "") + "\n" + (c.get("body") or ""),
             "landing_page": brief["landing"],
             "cta_text": {"static": "Learn More", "video": "Watch Now"}
             .get(c.get("format", "static"), "Learn More"),
             "video_spec": {"resolution": "1080x1920", "duration_max_sec": 30}
             if c.get("format") == "video" else None,
             "status": "INACTIVE"}
            for i, c in enumerate(brief["variants"])
        ],
        "disclaimer": brief["disclaimer"],
    }


def _check(brief, platform):
    if brief["platform"] != platform:
        raise ValueError(f"brief is for {brief['platform']}, not {platform}")
    if len(brief["variants"]) < 3:
        raise ValueError("Zeely rule: A/B test at least 3 creatives")
    if not any(v.get("format") == "video" for v in brief["variants"]):
        raise ValueError("Zeely rule: mix static AND video")
    blob = json.dumps(brief["variants"])
    stats.require_clean(blob, where=f"paid/{platform}")


def suggest_budget(tier="starter"):
    """Published, boring budget guidance — no projections, no promises."""
    return {
        "starter": dict(daily=20, weekly=140, note="Test budget. Learn, do not scale."),
        "growth": dict(daily=75, weekly=525, note="One winning creative, one audience."),
        "scale": dict(daily=250, weekly=1750, note="Only after a week of clean CTR."),
    }[tier]


def compliance_report(brief):
    """Zeely-style plain-language pre-flight check."""
    v = brief["variants"]
    problems = []
    if len(v) < 3:
        problems.append("Fewer than 3 variants -- you will not learn anything.")
    if not any(x.get("format") == "video" for x in v):
        problems.append("No video variant. Static alone under-tests the hook.")
    if brief["daily_budget"] > 500:
        problems.append("Daily budget above $500 before a proven winner is reckless.")
    if brief["age_min"] < 25:
        problems.append("Age floor below 25 on a trading product invites scrutiny.")
    for x in v:
        if len((x.get("hook") or "").split()) > 12:
            problems.append(f"Hook too long to survive 3 seconds: {x.get('id')}")
            break
    return problems or ["Clear to launch (still PAUSED until you flip the switch)."]
