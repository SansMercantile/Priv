"""The growth agent: Zeely's agentic layer, minus the parts that cost trust.

One run = one full create -> launch -> scale loop:

  CREATE   hooks batch + experiment matrix (Batch Mode), programmatic pages,
           today's organic posts
  LAUNCH   a validated paid brief, staged or fired depending on CH_PAID
  SCALE    rank the ledger, pick the next 3, explain them in one sentence each,
           flag fatigue
  OUTREACH review invites, press kit, partner pitches -- prepared, never sent

State lives in S3 (`s3://pr-growth-agent/ledger.json`) when running in Lambda
and in `assets/growth/ledger.json` when run locally, so both share one code path.
"""
import datetime
import json
import os
import re
import time

from . import (channels, distribution, experiments, hooks, indexnow, outreach,
               pages, paid, social, stats)

REPORT_COUNTS = ("created", "published", "prepared", "blocked_by_compliance",
                 "active_variants")


def _today():
    return datetime.datetime.utcnow()


def plan(now=None):
    now = now or _today()
    week = now.isocalendar()[1]
    stage = ("create", "launch", "scale")[week % 3]
    actions = [
        dict(stage="create", action="hooks_batch", why="Batch Mode: one input, many variants"),
        dict(stage="create", action="pages", why="programmatic SEO coverage"),
        dict(stage="create", action="indexnow", why="instant indexing on every search surface that reads it"),
        dict(stage="create", action="distribution", why="video packs for YouTube/TikTok/Reels/Facebook"),
        dict(stage="create", action="social_today", why="organic cadence"),
        dict(stage="launch", action="paid_brief", why="test at least 3, static + video"),
        dict(stage="scale", action="rank_and_select", why="promote winners, kill fatigue"),
        dict(stage="create", action="outreach", why="reviews, press, partners"),
    ]
    # Zeely's rule: spend budget on at least one of each stage every run.
    return actions, stage


def run(local_ledger=None):
    t0 = time.time()
    actions, stage = plan()
    report = dict(started=int(t0), utc=_today().isoformat() + "Z",
                  focus_stage=stage, results=[], created=0, published=0,
                  prepared=0, blocked_by_compliance=0, notes=[])

    ledger = experiments.load(local_ledger)

    # ---------------------------------------------------------------- CREATE
    try:
        batch = experiments.matrix(
            dict(headline="Entry. Two targets. One stop.",
                 body="Every setup ships complete: entry, TP1, TP2 and a stop "
                      "that trails to breakeven.",
                 cta="Start free — no card required"),
            factors=dict(
                hook=[h["text"] for h in hooks.generate(n=6, min_score=40)],
                format=["static", "video", "carousel"],
                angle=["problem", "mechanism", "objection"],
            ),
            limit=experiments.DEFAULT_LIMIT)
        ledger = experiments.register(batch, ledger)
        report["created"] += len(batch)
        report["results"].append(dict(action="hooks_batch", status="created",
                                      count=len(batch),
                                      top=batch[0]["id"] if batch else None,
                                      top_predicted=batch[0]["predicted"] if batch else 0))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="hooks_batch", status="error",
                                      error=str(e)[:300]))

    # pages
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
            owned, f"growth: refresh {len(owned)} landing pages "
                   f"({_today().date().isoformat()})")
        report["created"] += len(owned)
        _tally(report, res)
        report["results"].append(dict(action="pages", **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="pages", status="error",
                                      error=str(e)[:300]))

    # instant indexing -- ping every URL we just shipped to the sitemap
    # (Bing/Yandex/Naver/Seznam via IndexNow; Google is not on IndexNow)
    try:
        sitemap_path = os.path.join(pages.OUT, "sitemap.xml")
        urls = []
        if os.path.exists(sitemap_path):
            with open(sitemap_path, encoding="utf-8") as fh:
                urls = re.findall(r"<loc>([^<]+)</loc>", fh.read())
        res = indexnow.submit(urls)
        report["results"].append(dict(action="indexnow", **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="indexnow", status="error",
                                      error=str(e)[:300]))

    # video distribution packs -- one ready-to-upload bundle per master
    try:
        res = distribution.build()
        report["created"] += res.get("packs", 0)
        _tally(report, res)
        report["results"].append(dict(action="distribution", **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="distribution", status="error",
                                      error=str(e)[:300]))

    # social today -- compose for every platform in the day's rotation so the
    # back half of the list (facebook, whatsapp, youtube) actually ships
    try:
        entry = social.calendar(days=1)[0]
        posts = social.post_for(entry) if entry["platforms"] else []
        res = channels.publish_social(posts)
        report["created"] += len(posts)
        _tally(report, res)
        report["results"].append(dict(action="social_today", theme=entry["theme"],
                                      stage=entry["stage"], **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="social_today", status="error",
                                      error=str(e)[:300]))

    # ----------------------------------------------------------------- LAUNCH
    try:
        brief = paid.campaign(
            f"priv-growth-{_today().date().isoformat()}",
            objective="LEADS", daily_budget=20, geo=["US", "CA", "GB", "AU"],
            age_min=25, age_max=54, placement=("facebook", "instagram"))
        preflight = paid.compliance_report(brief)
        payload = paid.meta_payload(brief)
        res = channels.publish_paid(payload, "META")
        _tally(report, res)
        report["results"].append(dict(action="paid_brief", variants=len(brief["variants"]),
                                      preflight=preflight, **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["blocked_by_compliance"] += 1
        report["results"].append(dict(action="paid_brief", status="blocked",
                                      error=str(e)[:300]))

    # ------------------------------------------------------------------ SCALE
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
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="rank_and_select", status="error",
                                      error=str(e)[:300]))

    # --------------------------------------------------------------- OUTREACH
    try:
        items = outreach.outreach_batch() + [
            dict(kind="review", item=outreach.invite_email()["subject"]),
            dict(kind="affiliate", item="partner swipe pack refreshed"),
        ]
        res = channels.publish_outreach(items)
        _tally(report, res)
        report["results"].append(dict(action="outreach", **_slim(res)))
    except Exception as e:                       # noqa: BLE001
        report["results"].append(dict(action="outreach", status="error",
                                      error=str(e)[:300]))

    path = experiments.save(ledger, local_ledger)
    report["ledger"] = path
    report["seconds"] = round(time.time() - t0, 2)
    report["summary"] = report_line(report)
    _store_report(report)
    return report


def _tally(report, res):
    st = res.get("status")
    if st == "published":
        report["published"] += 1
    elif st == "prepared":
        report["prepared"] += 1
    elif st in ("blocked", "error"):
        report["blocked_by_compliance"] += 1


def _slim(res):
    out = {k: v for k, v in res.items() if k != "detail"}
    if isinstance(res.get("detail"), str):
        out["detail"] = res["detail"]
    elif isinstance(res.get("detail"), list):
        out["detail"] = str(res["detail"])[:300]
    return out


def report_line(report):
    """Zeely's 7th-grader rule: five numbers, one sentence."""
    best = ""
    for r in report["results"]:
        if r.get("action") == "rank_and_select" and r.get("top"):
            best = r["top"][0].get("explain", "")
    return (f"created {report['created']} assets, "
            f"{report['published']} published, {report['prepared']} staged for "
            f"approval, {report['blocked_by_compliance']} blocked by compliance."
            + (f" {best}" if best else ""))


def _store_report(report):
    payload = json.dumps(report, indent=2, default=str)
    path = None
    if os.environ.get("GROWTH_S3", "auto") != "off":
        try:
            import boto3
            bucket = os.environ.get("GROWTH_BUCKET", "pr-growth-agent")
            s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
            key = f"reports/{_today().strftime('%Y-%m-%dT%H%MZ')}.json"
            s3.put_object(Bucket=bucket, Key=key, Body=payload.encode())
            # mirror the ledger into S3 so every run starts from shared state
            ledger_path = os.environ.get("GROWTH_LEDGER") or experiments.default_path()
            if os.path.exists(ledger_path):
                s3.put_object(Bucket=bucket, Key="ledger.json",
                              Body=open(ledger_path, "rb").read())
            path = f"s3://{bucket}/{key}"
        except Exception as e:                   # noqa: BLE001
            path = f"local (s3 unavailable: {str(e)[:80]})"
    if path is None:
        d = os.path.join(os.path.dirname(channels.outbox_dir()), "reports")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{_today().strftime('%Y%m%dT%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(payload)
    return path


def hydrate_ledger_from_s3(dest=None):
    """Pull the shared ledger down before a Lambda run."""
    if os.environ.get("GROWTH_S3", "auto") == "off":
        return None
    dest = dest or os.environ.get("GROWTH_LEDGER") or experiments.default_path()
    try:
        import boto3
        bucket = os.environ.get("GROWTH_BUCKET", "pr-growth-agent")
        s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        body = s3.get_object(Bucket=bucket, Key="ledger.json")["Body"].read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(body)
        return dest
    except Exception:                            # noqa: BLE001
        return None
