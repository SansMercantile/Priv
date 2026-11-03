"""Channel publishers. Every channel has an explicit mode gate.

    CH_OWNED     = off | prepare | publish     (default publish)
    CH_SOCIAL    = off | prepare | publish     (default prepare)
    CH_PAID      = off | prepare | publish     (default prepare -- never spends
                                                 money unattended)
    CH_OUTREACH  = off | prepare | publish     (default prepare: drafts only)
    DRY_RUN      = true  forces every channel to `prepare`

`prepare` writes a launch pack to disk/S3; `publish` also fires the API call.
Missing credentials degrade `publish` back to `prepare` instead of failing.
"""
import datetime
import json
import os
import urllib.request
import urllib.error

API = "https://api.github.com"
GITHUB_OWNER = os.environ.get("GROWTH_GH_OWNER", "SansMercantile")
GITHUB_REPO = os.environ.get("GROWTH_GH_REPO", "Nexus")
GITHUB_BRANCH = os.environ.get("GROWTH_GH_BRANCH", "main")
PREFIX = os.environ.get("GROWTH_PREFIX", "public/growth")
DRY = os.environ.get("DRY_RUN", "false").lower() == "true"

SSM = {  # logical name -> SSM parameter
    "github": "/sans-mercantile/github-pat",
    "x": "/sans-mercantile/x-bearer-token",
    "linkedin": "/sans-mercantile/linkedin-access-token",
    "reddit": "/sans-mercantile/reddit-refresh-token",
    "meta": "/sans-mercantile/meta-access-token",
    "tiktok": "/sans-mercantile/tiktok-access-token",
    "meta_ad_account": "/sans-mercantile/meta-ad-account-id",
    # organic publishers (degrade to `prepare` until these exist)
    "facebook": "/sans-mercantile/facebook-page-token",
    "instagram": "/sans-mercantile/instagram-access-token",
    "youtube": "/sans-mercantile/youtube-access-token",
}


def mode(channel):
    raw = os.environ.get(f"CH_{channel}", "").strip().lower()
    if not raw:
        raw = {"OWNED": "publish", "SOCIAL": "prepare", "PAID": "prepare",
               "OUTREACH": "prepare"}[channel]
    if DRY and raw == "publish":
        return "prepare"
    if raw not in ("off", "prepare", "publish"):
        raise ValueError(f"CH_{channel} must be off|prepare|publish")
    return raw


def secret(logical, required=False):
    """Env var first (local dev), then SSM (Lambda)."""
    env = os.environ.get(f"GROWTH_{logical.upper()}")
    if env:
        return env
    try:
        import boto3
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        return ssm.get_parameter(Name=SSM[logical], WithDecryption=True)["Parameter"]["Value"]
    except Exception:
        if required:
            raise
        return None


def _http_h(method, url, payload=None, headers=None):
    """Like `_http` but also returns the response headers (needed for the
    YouTube resumable-upload handshake, which hands back a Location URL)."""
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Content-Type": "application/json", "User-Agent": "pr-growth-agent"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {}), dict(r.headers)
    except urllib.error.HTTPError as e:
        return (e.code,
                {"error": e.read().decode("utf-8", "replace")[:400]},
                dict(e.headers or {}))


def _http(method, url, payload=None, headers=None):
    status, body, _ = _http_h(method, url, payload, headers)
    return status, body


def outbox_dir():
    d = os.environ.get("GROWTH_OUTBOX") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "assets", "growth", "outbox")
    os.makedirs(d, exist_ok=True)
    return d


def _stage(name, payload):
    path = os.path.join(outbox_dir(), f"{name}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    return os.path.relpath(path)


# ------------------------------------------------------------------- owned --
def publish_site(files, message):
    """files = {relative_path: text_content} -> one GitHub commit."""
    m = mode("OWNED")
    if m == "off":
        return dict(channel="owned", status="skipped", files=len(files))
    staged = {f"{PREFIX}/{k.lstrip('/')}": v for k, v in files.items()}
    manifest = dict(message=message, files=sorted(staged),
                    target=f"{GITHUB_OWNER}/{GITHUB_REPO}@{GITHUB_BRANCH}")
    if m == "prepare":
        manifest["staged_to"] = _stage("owned", manifest)
        return dict(channel="owned", status="prepared", files=len(staged),
                    detail=manifest["staged_to"])

    token = secret("github", required=True)
    sha_map = {}
    for path in staged:
        sha_map[path] = _blob_sha(path, token)
    tree, commit = _commit(staged, sha_map, message, token)
    return dict(channel="owned", status="published", files=len(staged),
                detail=dict(commit=commit, tree=tree, paths=sorted(staged)))


def _gh(method, path, payload, token):
    status, body = _http(method, f"{API}{path}", payload,
                         {"Authorization": f"Bearer {token}",
                          "Accept": "application/vnd.github+json",
                          "X-GitHub-Api-Version": "2022-11-28"})
    if status >= 400:
        raise RuntimeError(f"GitHub {method} {path} -> {status}: {body}")
    return body


def _blob_sha(path, token):
    try:
        r = _gh("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
                       f"?ref={GITHUB_BRANCH}", None, token)
        return r.get("sha")
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise


def _commit(staged, sha_map, message, token):
    ref = _gh("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/ref/heads/"
                     f"{GITHUB_BRANCH}", None, token)
    parent = ref["object"]["sha"]
    pc = _gh("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/commits/{parent}",
             None, token)
    tree_entries = []
    blobs = {}
    for path, text in staged.items():
        blob = _gh("POST", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/blobs",
                   {"content": _b64(text), "encoding": "base64"}, token)
        blobs[path] = blob["sha"]
        e = {"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]}
        tree_entries.append(e)
    tree = _gh("POST", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/trees",
               {"base_tree": pc["tree"]["sha"], "tree": tree_entries}, token)
    commit = _gh("POST", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/commits",
                 {"message": message, "tree": tree["sha"], "parents": [parent]},
                 token)
    _gh("PATCH", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs/heads/{GITHUB_BRANCH}",
        {"sha": commit["sha"]}, token)
    return tree["sha"], commit["sha"]


def _b64(text):
    import base64
    return base64.b64encode(text.encode()).decode()


# ------------------------------------------------------------------ social --
def publish_social(posts):
    m = mode("SOCIAL")
    if m == "off":
        return dict(channel="social", status="skipped", posts=0)
    manifest = dict(generated=datetime.datetime.utcnow().isoformat() + "Z",
                    posts=posts)
    if m == "prepare":
        manifest["staged_to"] = _stage("social", manifest)
        return dict(channel="social", status="prepared", posts=len(posts),
                    detail=manifest["staged_to"])

    results = []
    for p in posts:
        results.append(_post_one(p))
    return dict(channel="social", status="published", posts=len(posts),
                detail=results)


def _post_one(p):
    """Post to one platform. Missing credentials degrade to `prepared`."""
    plat = p.get("platform")
    text = p.get("text", "")
    try:
        if plat == "x":
            return _post_x(text)
        if plat == "linkedin":
            return _post_linkedin(text)
        if plat == "reddit":
            return _post_reddit(p, text)
        if plat == "facebook":
            return _post_facebook(p, text)
        if plat == "instagram":
            return _post_instagram(p, text)
        if plat == "tiktok":
            return _post_tiktok(p, text)
        if plat == "youtube":
            return _post_youtube(p, text)
        if plat == "whatsapp":
            return _post_whatsapp(p, text)
        return dict(platform=plat, status="prepared", reason="no publisher")
    except Exception as e:                       # noqa: BLE001 -- one bad post
        return dict(platform=plat, status="error",  # must never kill the batch
                    error=str(e)[:200])


def _post_x(text):
    tok = secret("x")
    if not tok:
        return dict(platform="x", status="prepared", reason="no token")
    st, body = _http("POST", "https://api.twitter.com/2/tweets",
                     {"text": text}, {"Authorization": f"Bearer {tok}"})
    return dict(platform="x", status="published" if st < 300 else "error",
                id=body.get("data", {}).get("id"), http=st)


def _post_linkedin(text):
    tok = secret("linkedin")
    if not tok:
        return dict(platform="linkedin", status="prepared", reason="no token")
    st, body = _http(
        "POST", "https://api.linkedin.com/rest/posts",
        {"author": os.environ.get("LINKEDIN_PERSON_URN", "urn:li:person:me"),
         "commentary": text, "visibility": "PUBLIC",
         "distribution": {"feedDistribution": "MAIN_FEED",
                          "targetEntities": [], "thirdPartyDistribution": []}},
        {"Authorization": f"Bearer {tok}",
         "LinkedIn-Version": "202506", "X-Restli-Protocol-Version": "2.0.0"})
    return dict(platform="linkedin", status="published" if st < 300 else "error",
                http=st, body=str(body)[:200])


def _post_reddit(p, text):
    if not p.get("disclosed"):
        return dict(platform="reddit", status="blocked",
                    reason="reddit posts require disclosure")
    tok = secret("reddit")
    if not tok:
        return dict(platform="reddit", status="prepared", reason="no token")
    st, body = _http(
        "POST", "https://oauth.reddit.com/api/submit",
        {"api_type": "json", "kind": "self",
         "sr": os.environ.get("REDDIT_SUB", "algotrading"),
         "title": text.split("\n", 1)[0][:100], "text": text},
        {"Authorization": f"Bearer {tok}", "User-Agent": "pr-growth-agent/1.0"})
    return dict(platform="reddit", status="published" if st < 300 else "error",
                http=st)


# ------------------------------------------------- new organic publishers --
def _post_facebook(p, text):
    """Page feed post (message + link). Needs a Page access token."""
    tok = secret("facebook")
    page = os.environ.get("FACEBOOK_PAGE_ID")
    if not tok:
        return dict(platform="facebook", status="prepared", reason="no token")
    if not page:
        return dict(platform="facebook", status="prepared",
                    reason="no FACEBOOK_PAGE_ID")
    link = p.get("link") or "https://priv.sansmercantile.com"
    st, body = _http("POST", f"https://graph.facebook.com/v21.0/{page}/feed",
                     {"message": text, "link": link},
                     {"Authorization": f"Bearer {tok}"})
    return dict(platform="facebook", status="published" if st < 300 else "error",
                http=st, id=body.get("id"), body=str(body)[:200])


def _post_instagram(p, text):
    """Graph content-publishing: image is 2-step, reels needs a status poll."""
    tok = secret("instagram")
    user = os.environ.get("INSTAGRAM_USER_ID")
    if not tok:
        return dict(platform="instagram", status="prepared", reason="no token")
    if not user:
        return dict(platform="instagram", status="prepared",
                    reason="no INSTAGRAM_USER_ID")
    media = p.get("image") or p.get("video")
    if not media:
        return dict(platform="instagram", status="prepared",
                    reason="no image/video url attached")
    h = {"Authorization": f"Bearer {tok}"}
    is_video = str(media).lower().split("?")[0].endswith((".mp4", ".mov"))
    payload = {"caption": text}
    if is_video:
        payload.update(media_type="REELS", video_url=media)
    else:
        payload.update(image_url=media)
    st, c = _http("POST", f"https://graph.facebook.com/v21.0/{user}/media",
                  payload, h)
    if st >= 300 or not c.get("id"):
        return dict(platform="instagram", status="error", http=st,
                    body=str(c)[:200])
    cid = c["id"]
    if not is_video:
        st, pub = _http("POST",
                        f"https://graph.facebook.com/v21.0/{user}/media_publish",
                        {"creation_id": cid}, h)
        return dict(platform="instagram",
                    status="published" if st < 300 else "error",
                    http=st, id=pub.get("id"), body=str(pub)[:200])
    # video containers process async -- poll briefly, else hand the container
    # id back so a later run can finish the publish
    import time as _time
    for _ in range(10):
        st, state = _http("GET",
                          f"https://graph.facebook.com/v21.0/{cid}"
                          "?fields=status_code", None, h)
        code = state.get("status_code")
        if code == "FINISHED":
            st, pub = _http("POST",
                            f"https://graph.facebook.com/v21.0/{user}/media_publish",
                            {"creation_id": cid}, h)
            return dict(platform="instagram",
                        status="published" if st < 300 else "error",
                        http=st, id=pub.get("id"))
        if code in ("ERROR", "EXPIRED"):
            return dict(platform="instagram", status="error",
                        reason=f"container {code}")
        _time.sleep(3)
    return dict(platform="instagram", status="prepared", container_id=cid,
                reason="video still processing -- publish container next run")


def _post_tiktok(p, text):
    """Content Posting API, pull-from-URL (platform ingests our MP4)."""
    tok = secret("tiktok")
    video = p.get("video")
    if not tok:
        return dict(platform="tiktok", status="prepared", reason="no token")
    if not video:
        return dict(platform="tiktok", status="prepared",
                    reason="no video url attached")
    payload = {
        "post_info": {
            "title": text[:2200],
            "privacy_level": os.environ.get("TIKTOK_PRIVACY_LEVEL",
                                            "PUBLIC_TO_EVERYONE"),
            "disable_duet": False, "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {"source": "PULL_FROM_URL", "video_url": video},
    }
    st, body = _http("POST",
                     "https://open.tiktokapis.com/v2/post/publish/video/init/",
                     payload, {"Authorization": f"Bearer {tok}"})
    return dict(platform="tiktok", status="published" if st < 300 else "error",
                http=st, id=(body.get("data") or {}).get("publish_id"),
                body=str(body)[:200])


def _post_youtube(p, text):
    """Resumable upload: metadata handshake, then PUT the video bytes."""
    tok = secret("youtube")
    video = p.get("video")
    if not tok:
        return dict(platform="youtube", status="prepared", reason="no token")
    if not video:
        return dict(platform="youtube", status="prepared",
                    reason="no video url attached")
    title = str(p.get("title") or text.split("\n", 1)[0])[:100]
    meta = {
        "snippet": {"title": title, "description": text[:4800],
                    "categoryId": os.environ.get("YOUTUBE_CATEGORY_ID", "22")},
        "status": {"privacyStatus": os.environ.get("YOUTUBE_PRIVACY", "public"),
                   "selfDeclaredMadeForKids": False},
    }
    st, body, hdr = _http_h(
        "POST",
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        meta, {"Authorization": f"Bearer {tok}",
               "Content-Type": "application/json; charset=UTF-8"})
    location = hdr.get("Location") or hdr.get("location")
    if st >= 300 or not location:
        return dict(platform="youtube", status="error", http=st,
                    body=str(body)[:200])
    with urllib.request.urlopen(video, timeout=300) as r:
        blob = r.read()
    req = urllib.request.Request(location, data=blob, method="PUT",
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "video/mp4"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            st2, res = r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        st2, res = e.code, {"error": e.read().decode("utf-8", "replace")[:300]}
    return dict(platform="youtube", status="published" if st2 < 300 else "error",
                http=st2, id=res.get("id"), bytes=len(blob))


def _post_whatsapp(p, text):
    """WhatsApp has no organic broadcast API -- stage a tap-to-send link."""
    import urllib.parse
    link = "https://wa.me/?text=" + urllib.parse.quote(text[:1800])
    return dict(platform="whatsapp", status="prepared", share_link=link,
                reason="share link only -- WhatsApp has no organic post API")


# -------------------------------------------------------------------- paid --
def publish_paid(payload, platform="META"):
    m = mode("PAID")
    if m == "off":
        return dict(channel="paid", status="skipped")
    manifest = dict(platform=platform, payload=payload,
                    note="All objects are PAUSED/INACTIVE by design.")
    if m == "prepare":
        manifest["staged_to"] = _stage(f"paid_{platform.lower()}", manifest)
        return dict(channel="paid", status="prepared", platform=platform,
                    detail=manifest["staged_to"])

    if platform == "META":
        tok = secret("meta")
        acct = secret("meta_ad_account")
        if not tok or not acct:
            return dict(channel="paid", status="prepared",
                        reason="missing meta token or ad account")
        return _launch_meta(payload, tok, acct)
    if platform == "TIKTOK":
        tok = secret("tiktok")
        if not tok:
            return dict(channel="paid", status="prepared",
                        reason="missing tiktok token")
        st, body = _http(
            "POST", "https://business-api.tiktok.com/open_api/v1.3/campaign/create/",
            payload["campaign"], {"Access-Token": tok})
        return dict(channel="paid", platform=platform,
                    status="published" if st < 300 else "error", http=st,
                    body=str(body)[:300])
    raise ValueError(platform)


def _launch_meta(payload, tok, acct):
    base = f"https://graph.facebook.com/v21.0/act_{acct}"
    h = {"Authorization": f"Bearer {tok}"}
    out = []
    st, c = _http("POST", f"{base}/campaigns", payload["campaign"], h)
    out.append(dict(step="campaign", http=st, id=c.get("id"), err=c.get("error")))
    if st >= 300:
        return dict(channel="paid", platform="META", status="error", detail=out)
    st, a = _http("POST", f"{base}/adsets",
                  dict(payload["adset"], campaign_id=c["id"]), h)
    out.append(dict(step="adset", http=st, id=a.get("id"), err=a.get("error")))
    return dict(channel="paid", platform="META",
                status="published" if st < 300 else "error", detail=out,
                note="Created PAUSED. Nothing spends until you flip status.")


# ---------------------------------------------------------------- outreach --
def publish_outreach(items):
    m = mode("OUTREACH")
    if m == "off":
        return dict(channel="outreach", status="skipped", items=0)
    payload = dict(generated=datetime.datetime.utcnow().isoformat() + "Z",
                   policy="Prepared for a human to send. Never auto-sent.",
                   items=items)
    if m == "prepare":
        payload["staged_to"] = _stage("outreach", payload)
        return dict(channel="outreach", status="prepared", items=len(items),
                    detail=payload["staged_to"])
    # `publish` for outreach still means "queue to the send API" if one exists;
    # there is deliberately no blind-send implementation.
    payload["staged_to"] = _stage("outreach", payload)
    return dict(channel="outreach", status="prepared", items=len(items),
                detail=payload["staged_to"],
                note="Outreach has no auto-send path by design.")
