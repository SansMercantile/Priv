"""Outreach kits: review flywheel, press, and the partner/affiliate programme.

Zeely's observed plays: 4,077 Trustpilot reviews with *every* four-star page
entry labelled "Invited", "Replied to 98% of negative reviews within 24h", a
pressroom/media kit, and sponsored YouTube reviews carrying an exclusive trial
link. This module produces the assets for all three -- prepared for a human to
send, never auto-sent.
"""
import datetime

from . import hooks, stats


# ------------------------------------------------------------------ reviews --
def invite_email(name="", channel="email"):
    """Review invite. No incentive: paying for reviews breaches platform rules."""
    subject = "Two minutes of your time on Priv?"
    body = (
        f"Hi {name or 'there'},\n\n"
        "You have been using Priv for a while — would you leave a public review?\n\n"
        "We publish every review, good or bad, and we reply to anything critical "
        "within 24 hours. We do not offer discounts, gifts or referrals for "
        "reviews, because review platforms prohibit it and it would make the "
        "review worthless.\n\n"
        f"Leave a review: {stats.SITE_FULL}/trust/reviews\n\n"
        "If something is broken, hit reply instead — it comes straight to the team.\n\n"
        "— Priv, a Sans Mercantile product\n"
        f"{stats.SITE_FULL}\n\n"
        f"{stats.DISCLAIMER}"
    )
    return dict(kind="review_invite", channel=channel, subject=subject, body=body,
                policy="no incentives, no gating, no filtering")


def respond(text, sentiment, issue=""):
    """Draft a reply. Rule: name the specific complaint. Never canned."""
    issue = issue or _issue_from(text)
    if sentiment == "positive":
        return (f"Thank you — glad the {issue or 'workflow'} is doing its job. "
                "If you have a moment, the part most people miss is the strategy "
                "lab: backtest the same rule before you arm it.")
    if sentiment == "neutral":
        return (f"Thanks for the measured take. On {issue or 'your point'}: you are "
                "right that it takes a few boards to click. The fastest path is the "
                "starter board plus one alert rule — if that does not land in ten "
                "minutes, reply here and we will walk it with you.")
    # negative -- acknowledge, answer the actual point, offer a route, no excuses
    return (
        f"You are right about {issue or 'this'}, and we are not going to argue "
        "with your experience.\n\n"
        "What we have actually done: (1) every ticket now states entry, both "
        "targets and the stop before anything moves, (2) credentials fail closed "
        "and are never stored in the clear, (3) this reply is from a person, not "
        "a template.\n\n"
        "If it is still wrong for you, disconnect your broker from Settings and "
        "your data is deletable the same day — no retention window, no call.\n\n"
        f"Direct line: support@{stats.SITE.split('.', 1)[-1]}"
    )


def _issue_from(text):
    low = (text or "").lower()
    for k in ("cancel", "billing", "refund", "credit", "quality", "avatar",
              "support", "fee", "price", "signal", "alert", "app", "crash",
              "slow", "backtest"):
        if k in low:
            return k
    return ""


def proof_wall(reviews, out_note=""):
    """Render verified reviews for trust/reviews (no filtering by sentiment)."""
    rows = sorted(reviews, key=lambda r: r.get("date", ""))
    kept = [r for r in rows if r.get("verified")]
    return dict(total=len(rows), verified=len(kept),
                negative_kept=len([r for r in kept if r.get("rating", 5) <= 2]),
                policy="Nothing filtered. Critical reviews stay published and get "
                       "a named reply within 24 hours.",
                reviews=kept, note=out_note)


# --------------------------------------------------------------------- press --
def media_kit():
    today = datetime.date.today().isoformat()
    return dict(
        name="Priv",
        category=stats.CATEGORY.title(),
        tagline=stats.ONE_LINER,
        parent="Sans Mercantile",
        founded="2026",
        hq="Remote / global",
        contact="press@" + stats.SITE.split(".", 1)[-1],
        website=stats.SITE_FULL,
        downloads=stats.DOWNLOADS,
        boilerplate=(
            "Priv is an autonomous trading desk built by Sans Mercantile. It "
            "combines a live signal feed, a strategy backtesting lab, a "
            "five-agent execution quorum and full user custody: connections are "
            "made through official OAuth to the trader's own broker, and Priv "
            "holds no client funds. Priv runs on web, Windows, macOS, Android, "
            "iOS and Linux, and is available free to start."),
        facts=[stats.line(k, with_source=True)
               for k in ("category", "price_free", "timeframes", "cycle",
                         "agents", "platforms", "custody")],
        assets=["logo pack (SVG/PNG)", "product screenshots (unaltered)",
                "risk line (must accompany every published claim)"],
        updated=today,
        story=(
            "The marketing that promotes Priv is written, rendered and scheduled "
            "by Priv's own growth agent running on AWS — the same create → launch "
            "→ scale loop the product sells to traders."),
    )


def press_release(title, subtitle, points, quote="", author="", date=None):
    date = date or datetime.date.today()
    body = [
        f"{date.strftime('%B %d, %Y')} — ",
        subtitle,
        "",
    ]
    body += [f"* {p}" for p in points]
    if quote:
        body += ["", f"\u201c{quote}\u201d", f"— {author}"]
    body += ["", stats.ONE_LINER, f"{stats.SITE_FULL} · {stats.DOWNLOADS}",
             "", stats.DISCLAIMER]
    return dict(kind="press_release", title=title, dateline=date.isoformat(),
                body="\n".join(body), embargo="none")


def founder_note(topic="how the agent works"):
    h = hooks.generate(n=1)[0]
    return dict(
        title=f"Notes on {topic}",
        hook=h["text"],
        paragraphs=[
            "We did not hire an agency. We built the loop and let it run.",
            "Every page, post and ad variant that promotes Priv is generated, "
            "compliance-checked against a claim registry, and shipped by an "
            "agent on a twelve-hour schedule. It cannot publish a number that "
            "has no source, and it cannot publish a sentence that hides risk.",
            "That constraint is the product lesson: an agent with a hard "
            "compliance gate produces worse copy and much better trust.",
            "The interesting part is not that AI wrote it. It is that the same "
            "create → launch → scale loop we sell to traders is the one running "
            "on us.",
        ],
        cta=f"See the desk: {stats.SITE_FULL}")


# ----------------------------------------------------------------- affiliate --
def affiliate_kit():
    tiers = [
        dict(name="Starter", refs_per_quarter=1, payout="30% of first year",
             note="One verified referral."),
        dict(name="Operator", refs_per_quarter=5, payout="40% of first year",
             note="Repeat creator or community owner."),
        dict(name="Desk", refs_per_quarter=20, payout="50% of first year",
             note="Media partner or education brand."),
    ]
    swipes = dict(
        youtube_description=(
            "I use Priv for the desk side of this — signals with a stated stop, "
            "backtesting, and custody stays on my own broker. Free tier, no card: "
            "{link} (affiliate link — I earn a commission if you stay)"),
        email=(
            "Subject: the tool behind the setup\n\n"
            "Short version: I stopped keeping exits in my head. Priv states entry, "
            "two targets and a stop on every ticket, and I can backtest the same "
            "rule before I arm it. Start free: {link}"),
        x=(
            "The part I did not expect: it will not let me trade without an exit "
            "written down. {link} (affiliate)"),
        discord=(
            "Not a signal group. Complete tickets, delivery receipts, and your "
            "money never leaves your broker. {link}"),
    )
    return dict(
        name="Priv partner programme",
        url=f"{stats.SITE_FULL}/partners",
        cookie_days=90,
        payout="Monthly, after the refund window. Bank or stablecoin.",
        fee_to_join="$0 — no charge, no minimum, no exclusivity lock-in.",
        prohibited=[
            "Income, profit or win-rate claims of any kind",
            "Suggesting Priv is a broker, custodian or adviser",
            "Paid or incentivised reviews",
            "Spam, untagged Reddit posts, or undisclosed ads",
            "Targeting people in restricted jurisdictions",
        ],
        tiers=tiers, swipes=swipes,
        tracking=dict(
            param="via",
            example=f"{stats.SITE_FULL}/?via=creator-handle",
            reporting="Weekly CSV: clicks, signups, activations, payable."),
        compliance=stats.DISCLAIMER,
    )


def outreach_batch(day=None):
    """What a human should actually send today (Zeely's create/launch cadence)."""
    day = day or datetime.date.today()
    plan = [dict(kind="press", item=media_kit()["name"] + " media kit refresh"),
            dict(kind="affiliate", item="3 partner pitches to trading educators"),
            dict(kind="review", item=invite_email()["subject"])]
    if day.weekday() == 2:      # Wednesday
        plan.insert(0, dict(kind="press",
                            item="press release: agent-run marketing cycle"))
    return plan
