# Social Publisher Token Setup (organic CH_SOCIAL=publish)

The 8-platform organic publishers in `channels.py` read OAuth tokens from AWS
SSM (`/sans-mercantile/*`) and a few non-secret IDs from env vars. The SSM
parameters now exist as `REPLACE_ME` placeholders — paste the real token into
each to bring that platform live. Until a token is real, that platform stays in
`prepare` (staged, nothing posts).

Per the hard rules: **CH_PAID and CH_OUTREACH never publish without explicit
approval**; only CH_SOCIAL is being armed here, and only organic (free) posts.

## SSM parameters to fill (us-east-1)

| Platform | SSM parameter | How to get the token |
|----------|---------------|----------------------|
| X (Twitter) | `/sans-mercantile/x-bearer-token` | developer.x.com → your app → Keys & Tokens → Bearer Token (or OAuth2 user token) |
| LinkedIn | `/sans-mercantile/linkedin-access-token` | linkedin.com/developers → your app → OAuth 2.0 `w_member_social` token |
| Reddit | `/sans-mercantile/reddit-refresh-token` | reddit.com/prefs/apps → script app → OAuth refresh token |
| Meta (FB/IG ads+pages) | `/sans-mercantile/meta-access-token` | developers.facebook.com → System User long-lived token (`pages_manage_posts`,`instagram_content_publish`) |
| Facebook page | `/sans-mercantile/facebook-page-token` | Graph API `/me/accounts` → Page Access Token for the Priv page |
| Instagram | `/sans-mercantile/instagram-access-token` | Same Meta token with `instagram_content_publish` scope |
| TikTok | `/sans-mercantile/tiktok-access-token` | developers.tiktok.com → `video.publish` OAuth token |
| YouTube | `/sans-mercantile/youtube-access-token` | Google Cloud Console → YouTube Data API v3 OAuth refresh token (`youtube.upload`) |
| Meta ad account | `/sans-mercantile/meta-ad-account-id` | `act_XXXXXXXXXX` (paid stays PAUSED regardless) |

To set one (example for X):

```powershell
& "C:\Users\kpasc\.bridge\venv\Scripts\python.exe" -c "import boto3; boto3.client('ssm',region_name='us-east-1').put_parameter(Name='/sans-mercantile/x-bearer-token', Value='REAL_TOKEN_HERE', Type='SecureString', Overwrite=True)"
```

## Env vars also needed (non-secret, Lambda env / .env)

| Var | Value | Where used |
|-----|-------|-----------|
| `FACEBOOK_PAGE_ID` | the numeric FB Page id | `channels.py` FB publisher |
| `INSTAGRAM_USER_ID` | the IG business account id | `channels.py` IG publisher |
| `YOUTUBE_CATEGORY_ID` | e.g. `22` (People & Blogs) | `channels.py` YouTube upload |
| `LINKEDIN_PERSON_URN` | `urn:li:person:<id>` | `channels.py` LinkedIn author |
| `TIKTOK_PRIVACY_LEVEL` | `PUBLIC_TO_EVERYONE` (or as needed) | `channels.py` TikTok |

## Flip it live

Once the tokens you want are real (leave others as `REPLACE_ME` to keep those
staged), set `CH_SOCIAL=publish` on the growth Lambda / in `.env`. The
`mode()` gate in `channels.py` then lets organic posts publish; `DRY_RUN=true`
still forces `prepare` as a safety. Paid stays `prepare` (staged, PAUSED) per
the no-paid-spend rule.
