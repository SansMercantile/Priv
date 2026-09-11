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
