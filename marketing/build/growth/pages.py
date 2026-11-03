"""Programmatic SEO pages -- Zeely's "one landing page per job-to-be-done".

Renders self-contained HTML (brand tokens, hero, proof block, Before/After
table, FAQ with FAQPage JSON-LD, CTA, risk disclosure) plus og:/twitter: cards
and a sitemap. No templating dependency: pure string building, so it runs in
Lambda with the standard library only.
"""
import datetime
import html
import json
import os

from . import stats

ASSETS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "assets")
OUT = os.environ.get("GROWTH_PAGES_OUT") or os.path.join(ASSETS, "pages")
BASE = os.environ.get("GROWTH_BASE_URL", "https://www.sansmercantile.com/growth").rstrip("/")
PREFIX = os.environ.get("GROWTH_PREFIX", "public/growth")


def url(spec):
    """Canonical URL where this page will actually be served.

    Files are written as `<slug>.html` under `public/growth/` and Next.js
    serves them with the extension, so the canonical/sitemap URL must carry
    `.html` too -- extensionless URLs 404.
    """
    return f"{BASE}/{spec['slug']}.html"

CSS = """
:root{--gold:#d4af37;--navy:#0a0e27;--deep:#050715;--cyan:#00d4ff;--muted:#94a3b8;--white:#f8fafc}
*{box-sizing:border-box}body{margin:0;background:var(--deep);color:var(--white);
font:16px/1.65 "Segoe UI",system-ui,sans-serif}
a{color:var(--gold)} .wrap{max-width:1040px;margin:0 auto;padding:0 24px}
header{padding:22px 0;border-bottom:1px solid rgba(212,175,55,.18)}
.brand{font-weight:800;letter-spacing:.34em;color:var(--gold);text-decoration:none}
nav{float:right;font-size:14px}nav a{color:var(--muted);margin-left:18px;text-decoration:none}
.hero{padding:76px 0 54px;background:radial-gradient(1000px 420px at 78% 8%,rgba(212,175,55,.14),transparent 70%),var(--navy)}
.eyebrow{font:700 12px/1 Consolas,monospace;letter-spacing:.32em;color:var(--gold);text-transform:uppercase}
h1{font-size:clamp(32px,5vw,54px);line-height:1.08;margin:18px 0 14px;font-weight:800}
.sub{font-size:19px;color:#cbd5e1;max-width:44ch}
.proof{display:flex;flex-wrap:wrap;gap:26px;margin-top:34px}
.proof b{display:block;font-size:30px;color:var(--gold);font-weight:800}
.proof span{font-size:13px;color:var(--muted)}
.btn{display:inline-block;margin-top:30px;background:var(--gold);color:#0a0e27;
padding:15px 30px;border-radius:999px;font-weight:800;text-decoration:none}
.btn.ghost{background:transparent;color:var(--gold);border:1px solid var(--gold)}
section{padding:56px 0;border-top:1px solid rgba(148,163,184,.14)}
h2{font-size:26px;margin:0 0 18px}
table{width:100%;border-collapse:collapse;font-size:15px}
th,td{padding:13px 14px;text-align:left;border-bottom:1px solid rgba(148,163,184,.16)}
th{font:700 12px/1 Consolas,monospace;letter-spacing:.16em;color:var(--gold);text-transform:uppercase}
td.bad{color:#f87171}td.good{color:#4ade80}
.faq details{border-bottom:1px solid rgba(148,163,184,.16);padding:14px 0}
.faq summary{cursor:pointer;font-weight:700;font-size:17px}
.faq p{color:#cbd5e1;margin:10px 0 0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px}
.card{background:rgba(11,16,44,.72);border:1px solid rgba(212,175,55,.28);
border-radius:16px;padding:22px}
.card h3{margin:0 0 8px;font-size:18px}
.card p{color:var(--muted);font-size:14px;margin:0}
mark.pop{background:var(--gold);color:#0a0e27;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:800}
.risk{font-size:12.5px;color:var(--muted);background:rgba(5,7,21,.9);
border-top:1px solid rgba(148,163,184,.2);padding:22px 0;margin:0}
footer{padding:34px 0;color:var(--muted);font-size:13px;border-top:1px solid rgba(148,163,184,.14)}
"""


def esc(t):
    return html.escape(str(t or ""))


def render(kind, spec):
    """kind in {feature, compare, usecase, tool, affiliate, press, trust}."""
    title = spec["title"]
    desc = spec["desc"]
    faqs = spec.get("faq", [])
    before_after = spec.get("before_after", [])
    cards = spec.get("cards", [])
    proof_keys = spec.get("proof", ["price_free", "timeframes", "cycle", "custody"])

    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Priv",
        "applicationCategory": stats.CATEGORY.title(),
        "operatingSystem": "Web, Windows, macOS, Android, iOS, Linux",
        "description": desc,
        "url": url(spec),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD",
                   "description": "Free tier. Paid plans from $29/month."},
        "publisher": {"@type": "Organization", "name": "Sans Mercantile"},
    }
    if faqs:
        ld["subjectOf"] = {
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in faqs]}

    faq_html = "".join(
        f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
        for q, a in faqs) or ""

    ba_html = ""
    if before_after:
        rows = "".join(
            f"<tr><td class=\"bad\">{esc(b)}</td><td class=\"good\">{esc(a)}</td></tr>"
            for b, a in before_after)
        ba_html = (f"<section><h2>{esc(spec.get('ba_title','Before / after'))}</h2>"
                   f"<table><thead><tr><th>Without Priv</th><th>With Priv</th></tr>"
                   f"</thead><tbody>{rows}</tbody></table></section>")

    card_html = "".join(
        f"<div class=\"card\"><h3>{esc(c.get('h',''))}</h3>"
        f"<p>{esc(c.get('p',''))}</p></div>" for c in cards)

    proof_html = "".join(
        f"<div><b>{esc(stats.get(k)['value'])}</b>"
        f"<span>{esc(stats.get(k)['label'])}</span></div>"
        for k in proof_keys if stats.get(k))

    today = datetime.date.today().isoformat()
    html_doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow"><link rel="canonical" href="{url(spec)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Priv">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url(spec)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#050715">
<script type="application/ld+json">{json.dumps(ld)}</script>
<style>{CSS}</style></head>
<body>
<header><div class="wrap"><a class="brand" href="{stats.SITE_FULL}">PRIV</a>
<nav><a href="{stats.SITE_FULL}">Product</a><a href="{stats.SITE_FULL}#pricing">Pricing</a>
<a href="{BASE}/trust/reviews">Reviews</a><a href="{stats.DOWNLOADS}">Download</a></nav></div></header>
<div class="hero"><div class="wrap">
<p class="eyebrow">{esc(spec.get('eyebrow', stats.CATEGORY))}</p>
<h1>{esc(spec['h1'])}</h1>
<p class="sub">{esc(spec.get('lead',''))}</p>
<a class="btn" href="{esc(spec.get('cta_href', stats.SITE_FULL))}">{esc(spec.get('cta','Start free — no card required'))}</a>
<div class="proof">{proof_html}</div>
</div></div>
<main>
{f'<section><h2>{esc(spec.get("section_title",""))}</h2><div class="cols">{card_html}</div></section>' if card_html else ''}
{ba_html}
{f'<section class="faq"><h2>{esc(spec.get("faq_title","Questions people actually ask"))}</h2>{faq_html}</section>' if faq_html else ''}
<section><h2>Start free</h2>
<p class="sub">No card for the free tier. Connect your own broker through official OAuth —
funds never leave your account.</p>
<a class="btn" href="{stats.SITE_FULL}">Open {stats.SITE}</a>
<a class="btn ghost" href="{stats.DOWNLOADS}">Download the app</a></section>
</main>
<p class="risk">{esc(stats.DISCLAIMER)} Priv holds no client funds and stores no broker
credentials in the clear. <a href="{stats.SITE_FULL}/risk">Full risk disclosure</a>.</p>
<footer><div class="wrap">© {today[:4]} Sans Mercantile · {esc(stats.SITE)} ·
A Sans Mercantile fintech product</div></footer>
</body></html>"""
    return html_doc


# ------------------------------------------------------------------ catalog --
CATALOG = {
    "feature": [
        dict(slug="features/live-signals", title="Live trading signals — entry, TP1, TP2, stop",
             h1="Every signal ships complete.",
             lead="Entry, two targets and a stop that trails to breakeven — delivered the moment the setup resolves.",
             desc="Priv live signals: entry, take-profit 1, take-profit 2 and a trailing stop on every setup, delivered by email, SMS or WhatsApp.",
             section_title="What lands in your feed", cards=[
                 dict(h="Complete tickets", p="Entry, TP1, TP2 and stop — never a bare buy/sell line."),
                 dict(h="Three channels", p="Email, SMS or WhatsApp, sent the moment the setup completes."),
                 dict(h="Seven timeframes", p="1m to 1D on the same instrument, divergences surfaced.")],
             before_after=[("A one-line 'buy now' with no stop", "A full ticket with entry, two targets and a stop"),
                           ("You guess the exit", "The exit is stated before you enter"),
                           ("Alerts you notice an hour late", "Delivered the second the setup completes")],
             faq=[("Do Priv signals guarantee a win?",
                   "No. Signals are setups the system reads from price action; trading involves risk and past performance is not indicative of future results."),
                  ("How are signals delivered?",
                   "By email, SMS or WhatsApp — you pick the channel per alert rule."),
                  ("Which markets are covered?",
                   "Indices, synthetics, commodities and shares, watched around the clock.")]),
        dict(slug="features/strategy-lab", title="Strategy lab — backtest before you risk capital",
             h1="Prove it before you risk it.",
             lead="Pinned boards, run history and reproducible parameters on real candles.",
             desc="Backtest any strategy on real candles with pinned boards, run history and reproducible parameters in the Priv strategy lab.",
             section_title="What the lab gives you", cards=[
                 dict(h="Pinned boards", p="Keep the variants worth arguing about on one board."),
                 dict(h="Run history", p="Every run stored with its parameters, so results reproduce."),
                 dict(h="Seven timeframes", p="Test the same idea from one minute to one day.")],
             before_after=[("Trusting a backtest nobody can rerun", "Parameters stored with every run"),
                           ("Changing three things at a time", "One variable per board"),
                           ("Demo-account confidence", "Real candles, real spread assumptions")],
             faq=[("Does a backtest predict future returns?",
                   "No. It shows how a rule would have behaved historically. Past performance is not indicative of future results."),
                  ("Can I share a board?", "Yes — boards are shareable with your own account.")]),
        dict(slug="features/autonomous-execution", title="Autonomous execution — arm it and let the desk work",
             h1="Arm it. Sleep. Let the desk work.",
             lead="A 28-second decision cycle, five deliberating agents, fail-closed on credentials.",
             desc="Priv autonomous execution: a 28-second decision cycle with a five-agent quorum, tier-gated and fail-closed on credentials.",
             section_title="How an order actually moves", cards=[
                 dict(h="28-second cycle", p="Scan, deliberate, size, route — audited every run."),
                 dict(h="Five agents", p="Technical, quantitative, risk, compliance and ethical agents vote."),
                 dict(h="Fail-closed", p="No credential, no cycle. Never a partial or blind order.")],
             before_after=[("Manual entries at the worst hour", "A rule that runs every 28 seconds"),
                           ("One brain, one bias", "Five agents, quorum required"),
                           ("Credentials shared with a bot", "Official OAuth, fail-closed")],
             faq=[("Can it trade without me approving?",
                   "Only if you arm it, on a tier you paid for, against your own broker connection. You can disarm it in one tap."),
                  ("What happens if a credential breaks?", "The cycle fails closed and raises an alert. It never retries blind.")]),
        dict(slug="features/custody-and-control", title="Custody and control — your account, your funds",
             h1="Your account. Your funds. Your control.",
             lead="Official OAuth to your own broker. Priv holds zero client funds.",
             desc="Priv connects to your broker through official OAuth and holds no client funds. Credentials fail closed and are never stored in the clear.",
             section_title="What we never hold", cards=[
                 dict(h="$0 held", p="Priv is not a custodian. Money never moves through us."),
                 dict(h="Official OAuth", p="Broker-sanctioned connect, revocable from your side."),
                 dict(h="Fail-closed secrets", p="Encrypted at rest, never logged, never shared.")],
             before_after=[("Depositing into an unknown wallet", "Funds stay at your broker"),
                           ("API keys pasted into a form", "Official OAuth you can revoke"),
                           ("Trust us", "Verify: we hold nothing")],
             faq=[("Does Priv ever hold my money?",
                   "No. Priv holds no client funds at any point."),
                  ("How do I disconnect?", "Revoke the OAuth grant from your broker, or disconnect from Priv in one tap.")]),
        dict(slug="features/platforms", title="One account, every screen you own",
             h1="Your desk, on every screen.",
             lead="Web, Windows, macOS, Android, iOS and Linux from one account.",
             desc="Priv runs on Web, Windows, macOS, Android, iOS and Linux from a single account.",
             section_title="Where Priv runs", cards=[
                 dict(h="Web", p="Nothing to install."),
                 dict(h="Desktop", p="Windows, macOS and Linux builds."),
                 dict(h="Mobile", p="Android and iOS, plus home-screen install.")],
             faq=[("Is it one account across platforms?", "Yes — same account, same live feed.")]),
    ],
    "compare": [
        dict(slug="compare/priv-vs-manual-trading",
             title="Priv vs manual trading", h1="Manual trading vs a desk that never sleeps.",
             lead="The honest comparison — including where doing it yourself still wins.",
             desc="A fair comparison of manual trading against Priv's automated trading desk: speed, discipline, custody and where manual still wins.",
             section_title="Where each one wins", cards=[
                 dict(h="Manual wins", p="Discretionary judgement on a one-off event. Priv will not out-discretion you."),
                 dict(h="Priv wins", p="Consistency at 3am, on the seventh timeframe, on your fourth board."),
                 dict(h="Both", p="You still choose the risk. Priv just writes it down.")],
             before_after=[("Checking charts at 3am", "A cycle that runs at 3am for you"),
                           ("Moving your stop because it feels bad", "The stop is stated before entry"),
                           ("Six tabs, three brokers, no log", "One audited run history")],
             faq=[("Is manual trading worse?",
                   "No. It is different. If you trade a few times a month on discretionary calls, you may not need automation at all."),
                  ("Will Priv out-perform me?", "We do not claim that, and no system can guarantee it.")]),
        dict(slug="compare/priv-vs-copy-trading",
             title="Priv vs copy trading", h1="Copying a stranger vs running your own desk.",
             lead="Copy trading hands someone else the trigger. Priv hands you the process.",
             desc="How Priv's signals, backtesting and autonomous execution differ from copy trading: custody, transparency and control.",
             section_title="The real difference", cards=[
                 dict(h="Copy trading", p="You inherit someone else's risk, sizing and timing, unexplained."),
                 dict(h="Priv", p="Every ticket states entry, targets and stop before anything moves."),
                 dict(h="Either way", p="The money stays in your broker account.")],
             before_after=[("Opaque reasons for someone else's entry", "A stated ticket before entry"),
                           ("No way to test the strategy", "Backtest the same rule yourself"),
                           ("Their sizing, your drawdown", "Your cap, your brake")],
             faq=[("Is copy trading a scam?", "No, but it hides its reasoning. Priv shows the reasoning.")]),
        dict(slug="compare/priv-vs-signal-groups",
             title="Priv vs signal Telegram groups",
             h1="A chat message vs a complete ticket.",
             lead="Most signal groups send a line. Priv sends entry, two targets, a stop and a delivery receipt.",
             desc="Priv versus signal chat groups: complete tickets, delivery receipts, backtesting and no custody transfer.",
             section_title="What separates them", cards=[
                 dict(h="Complete or nothing", p="No bare buy lines. Every ticket has an exit."),
                 dict(h="Delivered, not posted", p="Email, SMS or WhatsApp with a completion time."),
                 dict(h="Testable", p="The same rule lives in the strategy lab.")],
             before_after=[("A screenshot in a chat", "A timestamped ticket"),
                           ("Silence after the entry", "A delivery receipt"),
                           ("Trust the admin", "Run the backtest yourself")],
             faq=[("Are signal groups legitimate?",
                   "Some are. The difference is whether you can see the exit and rerun the rule. Priv shows both.")]),
    ],
    "usecase": [
        dict(slug="usecase/swing-trader", title="Priv for swing traders",
             h1="Hold the position. Automate the patience.",
             lead="Daily and 4H reads, alerts that do not fire forty times a day, a stop that trails.",
             desc="Priv for swing traders: daily and 4H multi-timeframe reads, filtered alerts and a trailing stop.",
             section_title="What changes", cards=[
                 dict(h="Higher timeframes", p="1H, 4H and 1D reads without the 1m noise."),
                 dict(h="Quiet alerts", p="Rules you set, not a firehose."),
                 dict(h="Trailing stop", p="Moves to breakeven when the first target prints.")],
             faq=[("Can I disable intraday alerts?", "Yes — per instrument, per timeframe.")]),
        dict(slug="usecase/night-shift", title="Priv when you cannot watch the charts",
             h1="You sleep. The desk does not.",
             lead="Arm a rule and let the 28-second cycle run while you are asleep.",
             desc="Priv for traders who cannot watch charts: arm an autonomous rule and let the 28-second decision cycle run overnight.",
             section_title="Overnight, handled", cards=[
                 dict(h="24/7 watch", p="Indices, synthetics and commodities around the clock."),
                 dict(h="Audited runs", p="Every cycle logged, every morning."),
                 dict(h="Fail-closed", p="If a credential breaks, nothing trades blind.")],
             faq=[("Does it trade while I sleep?",
                   "Only if you arm it. Otherwise Priv watches and alerts you.")]),
        dict(slug="usecase/part-time-trader", title="Priv for part-time traders",
             h1="Full-time job. Part-time market.",
             lead="One desk that reads seven timeframes so your thirty minutes go further.",
             desc="Priv for part-time traders: multi-timeframe reads, complete signal tickets and a strategy lab you can use in minutes.",
             section_title="Made for scarce time", cards=[
                 dict(h="Read it in a minute", p="Tickets arrive complete — no research spiral."),
                 dict(h="Test on demand", p="Backtest a board between meetings."),
                 dict(h="Free to start", p="$0 tier, no card.")],
             faq=[("How long does setup take?", "Connect the broker, pick alert channels, done.")]),
    ],
    "tool": [
        dict(slug="tool/backtest-explainer", title="How to read a backtest honestly",
             h1="How to read a backtest without lying to yourself.",
             lead="Sample size, slippage, the regime you tested in, and what a good curve actually proves.",
             desc="A practical guide to reading strategy backtests honestly: sample size, slippage, regime fit and what a good equity curve does not prove.",
             section_title="Four checks before you believe it", cards=[
                 dict(h="Sample size", p="Under a few hundred trades it is noise."),
                 dict(h="Costs", p="Spread and swap decide whether the edge survives."),
                 dict(h="Regime", p="A bull-market backtest is a bull-market result.")],
             faq=[("What is a good win rate?", "There is no universal number. Risk/reward and drawdown matter more than win rate.")]),
        dict(slug="tool/timeframe-picker", title="Which timeframe should you trade?",
             h1="Which timeframe actually fits your life?",
             lead="Match the chart to the hours you have, not the excitement you want.",
             desc="How to choose a trading timeframe based on the time you actually have each day, from 1 minute to 1 day.",
             section_title="A quick map", cards=[
                 dict(h="1m–15m", p="Needs you at the screen. High noise."),
                 dict(h="30m–4H", p="The practical band for most people."),
                 dict(h="1D", p="Decisions once a day, held for days.")],
             faq=[("Can I watch several timeframes at once?",
                   "Yes — Priv reads the same instrument across all seven and surfaces disagreements.")]),
    ],
    "affiliate": [
        dict(slug="partners", title="Priv partner programme",
             h1="Introduce traders to a desk you would use yourself.",
             lead="Flat, published commissions. No %-of-spend surprises.",
             desc="Join the Priv partner programme: published commission tiers, a 90-day cookie and creative that already ships in six formats.",
             section_title="How it pays", cards=[
                 dict(h="Tiered", p="Published rates by verified referrals per quarter."),
                 dict(h="90-day cookie", p="Long attribution window, no dark patterns."),
                 dict(h="Assets included", p="Static, video, carousel and landing packs.")],
             faq=[("Is there a fee to join?", "No. There is no charge and no minimum."),
                  ("How and when are payouts made?", "Monthly, after the refund window, by bank or stablecoin.")]),
    ],
    "press": [
        dict(slug="press/media-kit", title="Priv media kit",
             h1="Priv media kit.",
             lead="Boilerplate, facts, product description and logo usage — everything a journalist needs.",
             desc="Priv media kit: company boilerplate, verified product facts, founder notes and logo usage.",
             section_title="Boilerplate", cards=[
                 dict(h="One paragraph", p=stats.ONE_LINER),
                 dict(h="Category", p=stats.CATEGORY.title() + " — a Sans Mercantile fintech product."),
                 dict(h="Contact", p="press@" + stats.SITE.split(".", 1)[-1])],
             faq=[("Can we publish screenshots?", "Yes, of the public product UI, unaltered, with the risk line intact.")]),
    ],
    "trust": [
        dict(slug="trust/reviews", title="What traders say about Priv",
             h1="What traders say — unedited.",
             lead="Verified reviews, good and bad, with a reply to every one.",
             desc="Verified Priv customer reviews, with responses to every critical review.",
             section_title="Our review policy", cards=[
                 dict(h="We reply in 24h", p="To every critical review, addressing the specific issue."),
                 dict(h="No incentives", p="We do not pay or discount for reviews — it breaches platform rules."),
                 dict(h="Bad reviews stay up", p="If it happened, it stays published.")],
             faq=[("Are these reviews paid for?", "No. Never.")]),
        dict(slug="risk", title="Risk disclosure", h1="Risk disclosure.",
             lead="Read this before you trade anything, anywhere.",
             desc="Priv risk disclosure: trading involves risk, past performance is not indicative of future results, Priv holds no client funds.",
             section_title="What you must accept", cards=[
                 dict(h="You can lose money", p="Every trade can go against you, including automated ones."),
                 dict(h="Past performance", p="Historical results never guarantee future results."),
                 dict(h="No custody", p="Priv holds no funds and is not a broker.")],
             faq=[("Is Priv financial advice?",
                   "No. Priv is software. Nothing it produces is investment advice.")]),
    ],
}


def build_all(out=OUT):
    os.makedirs(out, exist_ok=True)
    written = []
    for kind, specs in CATALOG.items():
        for spec in specs:
            path = os.path.join(out, *spec["slug"].split("/")) + ".html"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(render(kind, spec))
            written.append(os.path.relpath(path, out))
    written.append(write_sitemap(out))
    return written


def write_sitemap(out=OUT):
    today = datetime.date.today().isoformat()
    urls = [f"<url><loc>{stats.SITE_FULL}</loc><changefreq>weekly</changefreq></url>"]
    for specs in CATALOG.values():
        for spec in specs:
            urls.append(
                f"<url><loc>{url(spec)}</loc>"
                f"<lastmod>{today}</lastmod><priority>0.8</priority></url>")
    doc = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
           "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
           + "\n".join(urls) + "\n</urlset>\n")
    path = os.path.join(out, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return "sitemap.xml"
