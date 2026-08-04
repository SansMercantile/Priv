// Ported/adapted from the official Deriv PrivCore_lite reference app
// (source: repos/priv_core/src/external/deriv-core/auth/oauth.ts)
// Real Deriv OAuth2 + PKCE flow, run entirely client-side (no backend
// involvement, no client secret - standard for SPA/public OAuth clients).

import { generateRandomBase64url, sha256Base64url } from "./crypto";
import {
  storeCSRFToken,
  getCSRFToken,
  clearCSRFToken,
  storeCodeVerifier,
  getCodeVerifier,
  clearCodeVerifier,
  storeAuthInfo,
  clearAllDerivAuthData,
  DerivAuthInfo,
} from "./storage";

const DERIV_APP_ID = "340CMkSyVrWLSlXnzSaIP"; // PRIVCore - real OAuth-type app, registered redirect: https://priv.sansmercantile.com
const AUTH_BASE = "https://auth.deriv.com/oauth2";
const REDIRECT_URI = window.location.origin + "/"; // must exactly match Deriv's registered Redirect URL, trailing slash included

export class DerivOAuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DerivOAuthError";
  }
}

interface CallbackParams {
  code: string | null;
  state: string | null;
  scope: string | null;
  error: string | null;
  error_description: string | null;
}

async function buildPkceParams(): Promise<URLSearchParams> {
  const csrfToken = generateRandomBase64url(32);
  const codeVerifier = generateRandomBase64url(32);
  const codeChallenge = await sha256Base64url(codeVerifier);

  storeCSRFToken(csrfToken);
  storeCodeVerifier(codeVerifier);

  return new URLSearchParams({
    // Only 'trade' is currently authorized by Deriv for this app_id, despite
    // Payments/Account management/Application insights showing checked in
    // the Deriv dashboard UI - confirmed by direct testing against
    // auth.deriv.com, which returns invalid_scope for all of those right
    // now. If Deriv's UI selection propagates/gets re-saved, widen this.
    scope: "trade",
    response_type: "code",
    client_id: DERIV_APP_ID,
    redirect_uri: REDIRECT_URI,
    state: csrfToken,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  });
}

export async function initiateDerivLogin(): Promise<void> {
  const params = await buildPkceParams();
  window.location.href = `${AUTH_BASE}/auth?${params.toString()}`;
}

export async function initiateDerivSignUp(): Promise<void> {
  const params = await buildPkceParams();
  params.set("prompt", "registration");
  window.location.href = `${AUTH_BASE}/auth?${params.toString()}`;
}

export function isDerivCallback(): boolean {
  const params = new URLSearchParams(window.location.search);
  return params.has("code") && params.has("state");
}

function parseCallbackParams(): CallbackParams {
  const params = new URLSearchParams(window.location.search);
  return {
    code: params.get("code"),
    state: params.get("state"),
    scope: params.get("scope"),
    error: params.get("error"),
    error_description: params.get("error_description"),
  };
}

function cleanupUrl(): void {
  const url = new URL(window.location.href);
  ["code", "state", "scope", "error", "error_description"].forEach((p) =>
    url.searchParams.delete(p)
  );
  window.history.replaceState(window.history.state, "", url.pathname + url.search);
}

function validateCallback(params: CallbackParams): string {
  if (params.error) {
    cleanupUrl();
    throw new DerivOAuthError(`${params.error}: ${params.error_description || ""}`);
  }
  if (!params.state) {
    clearAllDerivAuthData();
    cleanupUrl();
    throw new DerivOAuthError("Missing state parameter - possible CSRF attack");
  }
  const storedToken = getCSRFToken();
  if (!storedToken || storedToken !== params.state) {
    clearAllDerivAuthData();
    cleanupUrl();
    throw new DerivOAuthError("CSRF token mismatch - possible CSRF attack");
  }
  clearCSRFToken();
  if (!params.code) {
    throw new DerivOAuthError("Missing authorization code");
  }
  return params.code;
}

async function exchangeCodeForTokens(code: string, codeVerifier: string): Promise<DerivAuthInfo> {
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    client_id: DERIV_APP_ID,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier,
  });

  const response = await fetch(`${AUTH_BASE}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new DerivOAuthError(`Token exchange failed (${response.status}): ${errorBody}`);
  }

  const tokenData = await response.json();
  const authInfo: DerivAuthInfo = {
    access_token: tokenData.access_token,
    token_type: tokenData.token_type,
    expires_in: tokenData.expires_in,
    expires_at: tokenData.expires_at ?? Math.floor(Date.now() / 1000) + tokenData.expires_in,
    scope: tokenData.scope,
    refresh_token: tokenData.refresh_token,
  };

  storeAuthInfo(authInfo);
  clearCodeVerifier();
  return authInfo;
}

/** Full callback handling: validate -> exchange code -> return auth info.
 * Call this when isDerivCallback() is true. Cleans the URL afterward
 * regardless of success or failure. */
export async function handleDerivCallback(): Promise<DerivAuthInfo> {
  const params = parseCallbackParams();
  const code = validateCallback(params);

  const codeVerifier = getCodeVerifier();
  if (!codeVerifier) {
    throw new DerivOAuthError("Code verifier expired or missing - please try logging in again");
  }

  try {
    const authInfo = await exchangeCodeForTokens(code, codeVerifier);
    cleanupUrl();
    return authInfo;
  } catch (err) {
    cleanupUrl();
    throw err;
  }
}

export function derivLogout(): void {
  clearAllDerivAuthData();
}

export { DERIV_APP_ID };
