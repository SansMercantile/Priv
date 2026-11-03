"""IndexNow: instant indexing pings (Bing, Yandex, Naver, Seznam, ...).

Google does not read IndexNow -- this covers the rest of the search surface
and costs nothing. Each host serves its own key file at its root:

    https://priv.sansmercantile.com/<key>.txt
    https://www.sansmercantile.com/<key>.txt

Gated exactly like the owned channel (`channels.mode("OWNED")`): DRY_RUN
forces `prepare`, so a dry cycle stages the payload to the outbox and sends
nothing off the machine.
"""
import json
import os
import urllib.parse

from . import channels

ENDPOINT = os.environ.get("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow")

KEYS = {  # host -> key value (the file at the host root must match)
    "priv.sansmercantile.com": "c01372bb65ce5d28f38d3f274389183d",
    "www.sansmercantile.com": "35da07ca1bb5800545d635c7c00af62c",
}


def keys():
    raw = os.environ.get("GROWTH_INDEXNOW_KEYS")
    if raw:
        try:
            return dict(KEYS, **json.loads(raw))
        except Exception:                      # noqa: BLE001
            pass
    return dict(KEYS)


def group(urls):
    """Split URLs by the host that serves them: {host: [url, ...]}."""
    out = {}
    for u in urls:
        host = urllib.parse.urlsplit(str(u)).netloc
        if host:
            out.setdefault(host, []).append(str(u))
    return out


def submit(urls):
    """Ping IndexNow for `urls`, grouped per host. Returns a channel result."""
    grouped = group(urls)
    if not grouped:
        return dict(channel="indexnow", status="skipped", urls=0)
    m = channels.mode("OWNED")
    all_keys = keys()
    results = []
    for host in sorted(grouped):
        batch = grouped[host][:10000]           # IndexNow caps at 10k URLs
        key = all_keys.get(host)
        payload = dict(host=host, urlList=batch)
        if key:
            payload["key"] = key
            payload["keyLocation"] = f"https://{host}/{key}.txt"
        if not key:
            results.append(dict(host=host, status="prepared", urls=len(batch),
                                reason="no key for host"))
        elif m != "publish":
            staged = channels._stage(
                f"indexnow_{host.replace('.', '_')}", payload)
            results.append(dict(host=host, status="prepared", urls=len(batch),
                                reason=f"CH_{ 'OWNED' }={m}", detail=staged))
        else:
            st, body = channels._http("POST", ENDPOINT, payload)
            results.append(dict(host=host, urls=len(batch), http=st,
                                status="submitted" if st in (200, 202) else "error",
                                body=str(body)[:200]))
    statuses = {r["status"] for r in results}
    top = ("published" if "submitted" in statuses
           else "error" if "error" in statuses
           else "prepared")
    return dict(channel="indexnow", status=top,
                urls=sum(r.get("urls", 0) for r in results), detail=results)


def ping_sitemaps(paths):
    """Collect <loc> entries from local sitemap files and submit them."""
    import re
    urls = []
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as fh:
            urls.extend(re.findall(r"<loc>([^<]+)</loc>", fh.read()))
    return submit(urls)
