"""KEV growth cycle: one create → launch → scale loop for the immersive school.

Runs the shared growth-engine modules inside ``products.use("kev")`` so every
claim resolves against KEV's verified registry and child-safe compliance guard.
Unlike the Priv agent (which runs on a schedule with trading copy hard-coded),
the KEV cycle is driven by ``kev/marketing`` (copy bank + campaign plan) and is
invoked explicitly — e.g. from ``scripts/run_kev_agent.py``.

Channels (identical gates to Priv): owned pages stage to the outbox and publish
to SansMercantile/Nexus only when CH_OWNED=publish; social / paid / outreach
always stage to the outbox in dry-run. blocked_by_compliance must be 0 before
anything is released.
"""
from __future__ import annotations

import datetime
import json
import os
import time

from . import channels, experiments, hooks, indexnow, pages, paid, products, social, stats


def _today():
    return datetime.datetime.utcnow()


def _slim(res):
    out = {k: v for k, v in res.items() if k != "detail"}
    if isinstance(res.get("detail"), str):
        out["detail"] = res["detail"]
    elif isinstance(res.get("detail"), list):
        out["detail"] = str(res["detail"])[:300]
    return out


def _tally(report, res):
    st = res.get("status")
    if st == "published":
        report["published"] += 1
    elif st == "prepared":
        report["prepared"] += 1
    elif st in ("blocked", "error"):
        report["blocked_by_compliance"] += 1


def run(local_ledger=None):
    """One KEV create → launch → scale cycle, inside the KEV product context.

    The experiment ledger is KEV-specific (``ledger-kev.json``) so the Priv
    schedule's ledger is never touched; the caller may override with
    ``local_ledger``.
    """
    with products.use("kev"):
        t0 = time.time()
        if local_ledger is None and not os.environ.get("GROWTH_LEDGER"):
            assets = os.path.join(os.path.dirname(channels.outbox_dir()))
            os.makedirs(assets, exist_ok=True)
            local_ledger = os.path.join(assets, "ledger-kev.json")
        report = dict(started=int(t0), utc=_today().isoformat() + "Z",
                      product="kev", results=[], created=0, published=0,
                      prepared=0, blocked_by_compliance=0, notes=[])

        ledger = experiments.load(local_ledger)

        # ---------------------------------------------------------- CREATE --
        # Experiment matrix from the KEV hook library (Batch Mode).
        try:
            batch = experiments.matrix(
                dict(headline="Walk to class through a 3D campus.",
                     body="Eleven floors, 199 rooms and 14 bookable facilities — "
                          "the whole school, explorable and gated to your role.",
                     cta="Start free — walk the campus"),
                factors=dict(
                    hook=[h["text"] for h in hooks.generate(n=6, min_score=40)],
                    format=["static", "video", "carousel"],
                    angle=["mechanism", "contrast", "identity", "proof"],
                ),
                limit=experiments.DEFAULT_LIMIT)
            ledger = experiments.register(batch, ledger)
            report["created"] += len(batch)
            report["results"].append(dict(action="hooks_batch", status="created",
                                          count=len(batch),
                                          top=batch[0]["id"] if batch else None,
                                          top_predicted=batch[0]["predicted"] if batch else 0))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="hooks_batch", status="error",
                                          error=str(e)[:300]))

        # Programmatic landing pages (6 pillars + 3 audiences + privacy) → Nexus.
        try:
            written = pages.build_all()
            owned = {}
            for rel in written:
                if not rel.endswith(".html"):
                    continue
                with open(os.path.join(pages.OUT, rel), encoding="utf-8") as fh:
                    owned[rel.replace("\\", "/")] = fh.read()
            sitemap_path = os.path.join(pages.OUT, "sitemap.xml")
            if os.path.exists(sitemap_path):
                with open(sitemap_path, encoding="utf-8") as fh:
                    owned["sitemap.xml"] = fh.read()
            res = channels.publish_site(
                owned, f"kev growth: {len(owned)} landing pages "
                       f"({_today().date().isoformat()})")
            report["created"] += len(owned)
            _tally(report, res)
            report["results"].append(dict(action="pages", **_slim(res)))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="pages", status="error",
                                          error=str(e)[:300]))

        # Instant indexing for the pages just staged.
        try:
            import re as _re
            sitemap_path = os.path.join(pages.OUT, "sitemap.xml")
            urls = []
            if os.path.exists(sitemap_path):
                with open(sitemap_path, encoding="utf-8") as fh:
                    urls = _re.findall(r"<loc>([^<]+)</loc>", fh.read())
            res = indexnow.submit(urls)
            report["results"].append(dict(action="indexnow", **_slim(res)))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="indexnow", status="error",
                                          error=str(e)[:300]))

        # Today's organic posts from the KEV copy bank (per pillar).
        try:
            posts = _social_today()
            res = channels.publish_social(posts)
            report["created"] += len(posts)
            _tally(report, res)
            report["results"].append(dict(action="social_today", count=len(posts),
                                          **_slim(res)))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="social_today", status="error",
                                          error=str(e)[:300]))

        # ---------------------------------------------------------- LAUNCH --
        # A validated KEV paid brief (education audience, PAUSED by design).
        try:
            brief = paid.campaign(
                f"kev-growth-{_today().date().isoformat()}",
                objective="LEADS", daily_budget=20, geo=["US", "CA", "GB", "AU"],
                age_min=25, age_max=54, placement=("facebook", "instagram"),
                audience=dict(interests=[
                    dict(name="Educational technology"),
                    dict(name="Homeschooling"),
                    dict(name="E-learning"),
                    dict(name="Parenting"),
                    dict(name="STEM education")]))
            preflight = paid.compliance_report(brief)
            payload = paid.meta_payload(brief)
            res = channels.publish_paid(payload, "META")
            _tally(report, res)
            report["results"].append(dict(action="paid_brief",
                                          variants=len(brief["variants"]),
                                          preflight=preflight, **_slim(res)))
        except Exception as e:                     # noqa: BLE001
            report["blocked_by_compliance"] += 1
            report["results"].append(dict(action="paid_brief", status="blocked",
                                          error=str(e)[:300]))

        # ----------------------------------------------------------- SCALE --
        try:
            rows = experiments.rank(ledger)
            chosen = experiments.select(3, ledger)
            report["active_variants"] = len(rows)
            report["results"].append(dict(
                action="rank_and_select",
                top=[dict(id=r["id"], ctr=round(r["ctr"], 4),
                          explain=experiments.explain(r)) for r in chosen[:3]],
                fatigued=experiments.fatigue(ledger),
            ))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="rank_and_select", status="error",
                                          error=str(e)[:300]))

        # -------------------------------------------------------- OUTREACH --
        # Draft-only (never auto-sent): a KEV media kit, review invite and
        # educator-outreach notes — assembled from the KEV registry.
        try:
            items = _outreach()
            res = channels.publish_outreach(items)
            _tally(report, res)
            report["results"].append(dict(action="outreach", **_slim(res)))
        except Exception as e:                     # noqa: BLE001
            report["results"].append(dict(action="outreach", status="error",
                                          error=str(e)[:300]))

        path = experiments.save(ledger, local_ledger)
        report["ledger"] = path
        report["seconds"] = round(time.time() - t0, 2)
        report["summary"] = _summary(report)
        _store(report)
        return report


# ------------------------------------------------------------------ helpers --
_COPY_BANK = [
    # (hook, body) pairs drawn from kev/marketing/02-COPY-BANK.md — the school's
    # real pillars, no outcome claims. Each passes stats.require_clean.
    ("Walk to class through a 3D campus.",
     "Eleven floors, 199 rooms and 14 bookable facilities — every one a door "
     "into a working room, gated to your role."),
    ("Dissect the human body. Then the engine.",
     "A Human Atlas of 2,234 structures and a 334-piece EV cutaway — explode, "
     "isolate and inspect any part."),
    ("A tutor for every subject, at every level.",
     "Socratic, level-adaptive tutors across 185+ subjects — live online, "
     "cached and offline guidance when you're not."),
    ("The classroom that works with no internet.",
     "Every 3D model precached, so the full labs run offline on first visit — "
     "notes and chat replay on reconnect."),
    ("PE that reads your movement, not your data.",
     "Dance and cardio games read your movement on-device — frames never "
     "uploaded. Add a smartwatch pulse over standard Bluetooth."),
    ("Steer the fourth dimension. Watch an optimizer think.",
     "A real Ising solver replays an optimizer cooling into a solution, and a "
     "real 4D tesseract projects to 3D — advanced ideas, made playable and honest."),
]


def _social_today():
    posts = []
    for hook, body in _COPY_BANK:
        for platform in ("linkedin", "x", "instagram", "facebook"):
            posts.append(social.post(
                platform, hook=hook, body=body,
                cta="Start free — walk the campus",
                angle="mechanism", kind="education",
                disclose=False, url=stats.SITE_FULL))
        # One batch of four platforms per pillar is enough per cycle; rotate
        # pillars across runs by the day number so coverage is even.
        break
    day = _today().toordinal()
    pillar = _COPY_BANK[day % len(_COPY_BANK)]
    posts = []
    for platform in ("linkedin", "x", "instagram", "facebook"):
        posts.append(social.post(
            platform, hook=pillar[0], body=pillar[1],
            cta="Start free — walk the campus",
            angle="mechanism", kind="education",
            disclose=False, url=stats.SITE_FULL))
    return posts


def _outreach():
    kit = {
        "name": "KEV media kit",
        "category": stats.CATEGORY.title(),
        "tagline": stats.ONE_LINER,
        "parent": "Sans Mercantile",
        "website": stats.SITE_FULL,
        "facts": [stats.line(k, with_source=True)
                  for k in ("floors", "rooms", "facilities", "atlas", "labs",
                            "subjects", "languages", "offline") if stats.get(k)],
        "assets": ["logo pack", "product screenshots (unaltered)",
                   "honest-note line (must accompany every claim)"],
        "note": "KEV is educational software; no learning-outcome or "
                "performance claims. Immersive scenes are teaching "
                "visualisations; Motion Gym is on-device analysis.",
    }
    return [
        dict(kind="press", item="KEV media kit refresh", payload=kit),
        dict(kind="press", item="educator outreach: 3 school / MAT innovation leads"),
        dict(kind="review", item="invite pilot families to review (no incentives)"),
        dict(kind="article", item="first LinkedIn article -> ClickUp review queue for Pascaline"),
    ]


def _summary(report):
    best = ""
    for r in report["results"]:
        if r.get("action") == "rank_and_select" and r.get("top"):
            best = r["top"][0].get("explain", "")
    return (f"KEV: created {report['created']} assets, "
            f"{report['published']} published, {report['prepared']} staged for "
            f"approval, {report['blocked_by_compliance']} blocked by compliance."
            + (f" {best}" if best else ""))


def _store(report):
    payload = json.dumps(report, indent=2, default=str)
    path = None
    if os.environ.get("GROWTH_S3", "auto") != "off":
        try:
            import boto3
            bucket = os.environ.get("GROWTH_BUCKET", "pr-growth-agent")
            s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
            key = f"reports/kev/{_today().strftime('%Y-%m-%dT%H%MZ')}.json"
            s3.put_object(Bucket=bucket, Key=key, Body=payload.encode())
            path = f"s3://{bucket}/{key}"
        except Exception as e:                     # noqa: BLE001
            path = f"local (s3 unavailable: {str(e)[:80]})"
    if path is None or path.startswith("local"):
        d = os.path.join(os.path.dirname(channels.outbox_dir()), "reports")
        os.makedirs(d, exist_ok=True)
        lp = os.path.join(d, f"kev-{_today().strftime('%Y%m%dT%H%M%S')}.json")
        with open(lp, "w", encoding="utf-8") as fh:
            fh.write(payload)
        path = path or lp
    report["report"] = path
    return path
