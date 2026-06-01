"""
XM Login Helper (template)

Purpose:
- Local helper to assist testing programmatic login to XM (my.xm.com).
- Runs locally, attempts to GET the login page to capture any hidden inputs, then POST credentials.

Caveats:
- XM's login page is client-rendered and may rely on JavaScript, CSRF tokens, or MFA. This script is a template and may need adjustments.
- Use locally and never commit real credentials. Prefer testing with a throwaway account.

Usage:
  python tools/xm_login_helper.py --username YOU --password PWD

Requirements:
  - Python 3.8+
  - requests (`pip install requests`)

This script prints a cookie header you can paste into `xm_session_token` in the app for local testing.
"""

import re
import sys
import argparse
import requests
from urllib.parse import urljoin

LOGIN_URL = "https://my.xm.com/member/login"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()

    s = requests.Session()
    print("[xm_helper] GET login page to capture hidden fields and cookies...")
    r = s.get(LOGIN_URL, timeout=20)
    if r.status_code != 200:
        print(f"[xm_helper] Failed to GET login page: {r.status_code}")
        sys.exit(1)

    html = r.text
    # Try to capture a form action and hidden inputs (best-effort)
    form_action = None
    m = re.search(r'<form[^>]+action=[\"\']([^\"\']+)[\"\']', html, re.IGNORECASE)
    if m:
        form_action = m.group(1)
        if not form_action.startswith('http'):
            form_action = urljoin(LOGIN_URL, form_action)
    else:
        print("[xm_helper] Could not detect form action; will attempt to POST to the login URL directly.")
        form_action = LOGIN_URL

    hidden_inputs = dict(re.findall(r'<input[^>]+type=[\"\']hidden[\"\'][^>]*name=[\"\']([^\"\']+)[\"\'][^>]*value=[\"\']([^\"\']*)[\"\']', html, re.IGNORECASE))
    print(f"[xm_helper] Hidden inputs found: {list(hidden_inputs.keys())}")

    # Heuristic field names (may need to be adjusted)
    payload = {}
    payload.update(hidden_inputs)
    # Try common username/password field names
    candidate_user_fields = ['username', 'email', 'login', 'account']
    candidate_pass_fields = ['password', 'passwd', 'pass']

    # Find input names if present
    user_field = None
    pass_field = None
    for name in re.findall(r'<input[^>]+name=[\"\']([^\"\']+)[\"\']', html, re.IGNORECASE):
        lname = name.lower()
        if not user_field and any(c in lname for c in candidate_user_fields):
            user_field = name
        if not pass_field and any(c in lname for c in candidate_pass_fields):
            pass_field = name

    if not user_field:
        user_field = 'username'
    if not pass_field:
        pass_field = 'password'

    payload[user_field] = args.username
    payload[pass_field] = args.password

    print(f"[xm_helper] POSTing to {form_action} with fields: {list(payload.keys())}")
    post = s.post(form_action, data=payload, timeout=20, allow_redirects=True)
    print(f"[xm_helper] POST status: {post.status_code}")
    if post.history:
        print(f"[xm_helper] Redirect chain: {[r.status_code for r in post.history]} -> {post.status_code}")

    # Print cookies for manual paste
    cookies = s.cookies.get_dict()
    print("\n=== Session Cookies (paste as xm_session_token) ===")
    print('; '.join([f"{k}={v}" for k, v in cookies.items()]))
    print("=== End ===\n")

    # Minimal guidance
    if post.status_code == 200 and cookies:
        print("[xm_helper] If login appears successful, copy the cookie string above and paste it into the Trading Terminal session token field.")
    else:
        print("[xm_helper] Login may have failed or the site requires JS/MFA. Inspect response content or try using a browser and copy cookies manually.")


if __name__ == '__main__':
    main()
