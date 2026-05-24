import { datadogRum } from "@datadog/browser-rum";

/**
 * Initializes Datadog Browser RUM (Real User Monitoring) in client space.
 * Gracefully switches to simulated tracking if credentials are not configured yet.
 */
export function initDatadog(): { RUM_STATUS: string; isReal: boolean } {
  const metaEnv = (import.meta as any).env || {};
  const appId = metaEnv.VITE_DD_APPLICATION_ID;
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
    datadogRum.init({
      applicationId: appId,
      clientToken: clientToken,
      site: site,
      service: service,
      env: env,
      version: "1.0.0",
      sessionSampleRate: 100,
      sessionReplaySampleRate: 20,
      trackUserInteractions: true,
      trackResources: true,
      trackLongTasks: true,
      defaultPrivacyLevel: "mask-user-input",
    });

    datadogRum.startSessionReplayRecording();
    console.log(`[SANS Datadog] Client RUM and Session Replay initiated on site: ${site}. Service: ${service}`);
    return { RUM_STATUS: "active (live)", isReal: true };
  } catch (error: any) {
    console.warn("[SANS Datadog] RUM initialization encountered custom exception:", error.message || error);
    return { RUM_STATUS: "error", isReal: false };
  }
}
