"""AWS entrypoint for the Priv growth agent.

Scheduled by EventBridge rule `pr-growth-agent-schedule` (rate 12 hours).

Env:
    DRY_RUN=true       force every channel to `prepare`
    CH_OWNED           off | prepare | publish   (default publish)
    CH_SOCIAL          off | prepare | publish   (default prepare)
    CH_PAID            off | prepare | publish   (default prepare)
    CH_OUTREACH        off | prepare | publish   (default prepare)
    GROWTH_BUCKET       s3 bucket for ledger + reports (default pr-growth-agent)
"""
import json
import os
import sys
import tempfile

# `growth/` is zipped at the archive root alongside this module.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from growth import agent  # noqa: E402


def handler(event=None, context=None):
    event = event or {}
    if isinstance(event, str):
        event = json.loads(event)

    # Lambda's filesystem is read-only outside /tmp -- park all writable state
    # there and hydrate the shared ledger before the run.
    ledger = (os.environ.get("GROWTH_LEDGER")
              or os.path.join(tempfile.gettempdir(), "growth-ledger.json"))
    os.environ["GROWTH_LEDGER"] = ledger
    os.environ.setdefault("GROWTH_PAGES_OUT",
                          os.path.join(tempfile.gettempdir(), "growth-pages"))
    os.environ.setdefault("GROWTH_OUTBOX",
                          os.path.join(tempfile.gettempdir(), "growth-outbox"))

    if event.get("hydrate", True):
        agent.hydrate_ledger_from_s3(ledger)

    report = agent.run(ledger)
    print(json.dumps(report, indent=2, default=str))
    return {
        "statusCode": 200,
        "body": json.dumps({"summary": report.get("summary"),
                            "created": report.get("created"),
                            "published": report.get("published"),
                            "prepared": report.get("prepared"),
                            "blocked": report.get("blocked_by_compliance"),
                            "seconds": report.get("seconds")},
                           default=str),
    }
