// Shared admin-identity probe with one retry.
//
// GET /admin/whoami resolves the caller's email via Auth0 /userinfo
// server-side. A single transient failure used to leave admin surfaces
// hidden or bounce the admin off admin-only pages for the whole session
// ("admin buttons sometimes do not reflect"). The backend now retries
// and caches too; this covers browser/network-level blips and a stale
// negative right after sign-in or a token refresh.
import apiClient from "./apiClient";

export async function probeAdmin(retries = 1): Promise<boolean> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res: any = await apiClient.get("/api/v1/admin/whoami");
      if (res?.data?.data?.admin) return true;
    } catch (_) {
      // network/server blip -- retry below
    }
    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, 800));
    }
  }
  return false;
}
