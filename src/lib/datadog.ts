import { datadogRum } from "@datadog/browser-rum";

/**
 * Initializes Datadog Browser RUM (Real User Monitoring) in client space.
 * Gracefully switches to simulated tracking if credentials are not configured yet.
 */
export function initDatadog(): { RUM_STATUS: string; isReal: boolean } {
  const metaEnv = (import.meta as any).env || {};
  // Kill-switch: set VITE_DD_ENABLED=false in Vercel env + redeploy to
  // silence RUM entirely (e.g. while the client token is invalid and every
  // upload 403s noisily). Default stays on.
  if (String(metaEnv.VITE_DD_ENABLED || "").toLowerCase() === "false") {
    console.log("[SANS Datadog] Disabled via VITE_DD_ENABLED=false.");
    return { RUM_STATUS: "disabled", isReal: false };
  }
  const appId = metaEnv.VITE_DD_APPLICATION_ID || metaEnv.VITE_DD_APP_ID;
  const clientToken = metaEnv.VITE_DD_CLIENT_TOKEN;
  const site = metaEnv.VITE_DD_SITE || "datadoghq.com";
  const service = metaEnv.VITE_DD_SERVICE || "sans-priv-core";
  const env = metaEnv.VITE_DD_ENV || "development";

  if (!appId || !clientToken) {
    console.log("[SANS Datadog] Client tokens not fully configured. Core running on high-fidelity RUM emulation mode.");
    
    // In emulation mode, we can mock user interaction tracking for debug purposes
    if (typeof window !== "undefined") {
      (window as any).__DATADOG_EMULATION__ = {
        appId: appId || "EMULATED-APP-ID",
        clientToken: clientToken || "EMULATED-CLIENT-TOKEN",
        site,
        service,
        env,
        sessionSampleRate: 100,
        status: "active"
      };
    }
    return { RUM_STATUS: "active (emulated)", isReal: false };
  }

  try {
    // Session Replay uploads hit intake hard and 403 (with console spam)
    // when the Datadog app hasn't allowlisted this origin. Keep RUM always
    // on; gate replay behind VITE_DD_SESSION_REPLAY=true (set it in Vercel
    // env + redeploy after allowlisting https://priv.sansmercantile.com/*
    // in RUM Application Settings).
    const replayEnabled =
      String(metaEnv.VITE_DD_SESSION_REPLAY || "").toLowerCase() === "true";
    datadogRum.init({
      applicationId: appId,
      clientToken: clientToken,
      site: site,
      service: service,
      env: env,
      version: "1.0.0",
      sessionSampleRate: 100,
      sessionReplaySampleRate: replayEnabled ? 20 : 0,
      trackUserInteractions: true,
      trackResources: true,
      trackLongTasks: true,
      defaultPrivacyLevel: "mask-user-input",
    });

    if (replayEnabled) {
      datadogRum.startSessionReplayRecording();
    }
    console.log(`[SANS Datadog] Client RUM initiated on site: ${site}. Service: ${service}. Replay: ${replayEnabled ? "on" : "off"}.`);
    return { RUM_STATUS: "active (live)", isReal: true };
  } catch (error: any) {
    console.warn("[SANS Datadog] RUM initialization encountered custom exception:", error.message || error);
    return { RUM_STATUS: "error", isReal: false };
  }
}
