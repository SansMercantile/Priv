// Authenticated headers for every backend call: the verified Bearer
// token (when signed in) plus the browser id. The old version sent
// X-User-Id only, so every call resolved the anonymous key -- whose
// records were claimed away at login -- and callers fell back to the
// shared desk (a LIVE account) in every mode, including demo.
import { getAppUserId } from "./appUserId";
import { getAuthToken } from "./authToken";

export async function userHeader(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  try {
    headers["X-User-Id"] = getAppUserId();
  } catch (_) {
    /* ignore */
  }
  try {
    const token = await getAuthToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  } catch (_) {
    /* ignore */
  }
  return headers;
}
