import apiClient from "../api/apiClient";

// Web Push for position alerts (opened / TP hit / SL hit / close failed).
// The SW registration already exists (main.tsx registers public/sw.js);
// here we handle permission, PushManager subscribe with the backend's
// VAPID public key, and the subscribe/unsubscribe server calls.

export type PushState = "unsupported" | "blocked" | "off" | "on";

export function pushSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

function urlB64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
}

export async function getPushState(): Promise<PushState> {
  if (!pushSupported()) return "unsupported";
  if (Notification.permission === "denied") return "blocked";
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    return sub ? "on" : "off";
  } catch {
    return "off";
  }
}

export async function enablePush(): Promise<PushState> {
  if (!pushSupported()) return "unsupported";
  const permission = await Notification.requestPermission();
  if (permission === "denied") return "blocked";
  if (permission !== "granted") return "off";
  const res: any = await apiClient.getVapidPublicKey();
  const key: string =
    res?.data?.public_key ?? res?.public_key ?? "";
  if (!key) throw new Error("Server has no VAPID public key configured.");
  const reg = await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToUint8Array(key) as BufferSource,
    });
  }
  const json = sub.toJSON();
  await apiClient.pushSubscribe({
    endpoint: json.endpoint || "",
    keys: { p256dh: json.keys?.p256dh || "", auth: json.keys?.auth || "" },
  });
  return "on";
}

export async function disablePush(): Promise<PushState> {
  if (!pushSupported()) return "unsupported";
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (sub) {
      await apiClient.pushUnsubscribe(sub.endpoint || "").catch(() => {});
      await sub.unsubscribe();
    }
  } catch {
    /* already gone */
  }
  return "off";
}
