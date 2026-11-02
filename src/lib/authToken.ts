// Lets apiClient.ts (a plain module, outside the React tree) obtain the
// current Auth0 access token without importing React hooks. LoginGate.tsx
// registers the real getter (Auth0's getAccessTokenSilently) once a user
// is authenticated; until then, or if it's never registered, getAuthToken
// resolves to null and callers fall back to the anonymous flow.

type TokenGetter = () => Promise<string | null>;

let tokenGetter: TokenGetter | null = null;

export function setAuthTokenGetter(fn: TokenGetter | null): void {
  tokenGetter = fn;
}

export async function getAuthToken(): Promise<string | null> {
  if (!tokenGetter) return null;
  try {
    return await tokenGetter();
  } catch {
    // Not authenticated, token expired with no refresh available, etc. --
    // treat identically to "no token", let callers fall back.
    return null;
  }
}

// The OIDC id_token (JWT) from Auth0. Unlike the access token (minted for
// the API audience and rejected by Auth0's /userinfo), the id_token carries
// verified `email` / `email_verified` claims the backend can verify locally
// against the tenant JWKS (aud = client_id). The backend uses it to resolve
// the caller's real email for admin gating (whoami / require_admin) --
// without it every admin surface hid, because /userinfo failed on the
// custom-audience access token.
type IdTokenGetter = () => Promise<string | null>;

let idTokenGetter: IdTokenGetter | null = null;

export function setIdTokenGetter(fn: IdTokenGetter | null): void {
  idTokenGetter = fn;
}

export async function getIdToken(): Promise<string | null> {
  if (!idTokenGetter) return null;
  try {
    return await idTokenGetter();
  } catch {
    return null;
  }
}
