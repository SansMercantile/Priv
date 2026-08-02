// Stable, anonymous per-browser identifier used to scope broker/OAuth
// connections (Deriv, Alpaca, etc.) before or independent of Auth0 login.
// Persisted in localStorage so it survives reloads and OAuth redirects.

const STORAGE_KEY = "priv_app_user_id";

export function getAppUserId(): string {
  try {
    let id = window.localStorage.getItem(STORAGE_KEY);
    if (!id) {
      id = crypto.randomUUID();
      window.localStorage.setItem(STORAGE_KEY, id);
    }
    return id;
  } catch {
    // localStorage unavailable (private mode, etc.) - fall back to a
    // session-only id so requests still work, just won't persist.
    return "session-" + Math.random().toString(36).slice(2);
  }
}
