// High-integrity API Client for SANS PRIV Core KYC, Profile, and billing services
import { getAppUserId } from "../lib/appUserId";
import { getAuthToken } from "../lib/authToken";

// NOTE (AWS migration): all calls go same-origin through the /api/*
// proxy to the live backend. The retired Azure host previously read from
// VITE_API_BASE_URL is deliberately no longer used.

// X-User-Id is always sent (it's what the pre-login Deriv-connect flow
// relies on), but when a verified Auth0 session exists we also send the
// access token. The backend (oauth_api.py _resolve_user_id) always
// prefers the verified Bearer token over X-User-Id when both are
// present, so a signed-in user's identity can't be overridden by
// tampering with the anonymous header.
async function withUserHeader(headers?: HeadersInit): Promise<HeadersInit> {
  const merged: Record<string, string> = { ...(headers as Record<string, string> || {}), "X-User-Id": getAppUserId() };
  const token = await getAuthToken();
  if (token) merged["Authorization"] = `Bearer ${token}`;
  return merged;
}

async function safeFetch(url: string, options?: RequestInit) {
  const fullUrl = url;
  const response = await fetch(fullUrl, { ...options, headers: await withUserHeader(options?.headers) });
  const contentType = response.headers.get("content-type") || "";
  // Guard: if server returns HTML (404 page, error page) instead of JSON,
  // throw a human-readable error instead of "Unexpected token 'T'..."
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    throw new Error(
      `Server returned non-JSON (HTTP ${response.status}): ${text.slice(0, 120)}`
    );
  }
  const data = await response.json();
  if (!response.ok) {
    throw Object.assign(
      new Error(data?.detail || data?.error || `HTTP ${response.status}`),
      { response: { data, status: response.status } }
    );
  }
  return data;
}

// Broker/OAuth calls always use a relative path so they go through the
// same-origin /api/* proxy to the live backend, never a cross-origin host.
async function safeFetchRelative(url: string, options?: RequestInit) {
  const response = await fetch(url, { ...options, headers: await withUserHeader(options?.headers) });
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    throw new Error(
      `Server returned non-JSON (HTTP ${response.status}): ${text.slice(0, 120)}`
    );
  }
  const data = await response.json();
  if (!response.ok) {
    throw Object.assign(
      new Error(data?.detail || data?.error || `HTTP ${response.status}`),
      { response: { data, status: response.status } }
    );
  }
  return data;
}

export const apiClient = {
  get: async (url: string) => {
    const data = await safeFetch(url);
    return { data };
  },

  post: async (url: string, bodyData?: any) => {
    const data = await safeFetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: bodyData ? JSON.stringify(bodyData) : undefined,
    });
    return { data };
  },

  put: async (url: string, bodyData?: any) => {
    const data = await safeFetch(url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: bodyData ? JSON.stringify(bodyData) : undefined,
    });
    return { data };
  },

  delete: async (url: string) => {
    const data = await safeFetch(url, { method: "DELETE" });
    return { data };
  },

  // KYC handlers (relative: served by kyc_compat_api.py, mounted at
  // /api/kyc in main.py -- confirmed live: GET /api/kyc/status -> 401
  // (route exists, needs auth), not 404. Do NOT change these to
  // /api/v1/kyc/* -- that's a DIFFERENT, older router (kyc_api.py) that
  // lacks /record, /verify-document, and /verify-face entirely.
  getKycRecord: () => safeFetchRelative("/api/kyc/record"),
  getKycStatus: () => safeFetchRelative("/api/kyc/status"),
  saveKycDraft: (form: any) =>
    safeFetchRelative("/api/kyc/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }),
  submitKyc: (form: any) =>
    safeFetchRelative("/api/kyc/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }),

  // Provider-neutral address autocomplete / geocode (AWS Location Service
  // via backend/api/location_api.py, mounted at /api/v1/location). Never
  // call a maps provider directly from the browser.
  addressAutocomplete: (q: string, limit = 8) =>
    safeFetchRelative(`/api/v1/location/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`),
  addressGeocode: (label: string) =>
    safeFetchRelative("/api/v1/location/geocode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label }),
    }),

  // AI document verification (sends base64 image to Gemini via backend).
  // NOTE: confirmed live this currently returns 501 "Document
  // verification not configured (Bedrock vision unavailable)" -- the
  // route exists and is wired correctly, but its backend dependency
  // (AWS Bedrock vision) isn't configured in this environment. Frontend
  // callers should handle a 501 gracefully rather than treating it as a
  // generic failure.
  verifyDocument: (documentBase64: string, mimeType: string, formData: any) =>
    safeFetchRelative("/api/kyc/verify-document", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documentBase64, mimeType, formData }),
    }),

  // AI face / liveness verification
  verifyFace: (selfieBase64: string, documentBase64?: string) =>
    safeFetchRelative("/api/kyc/verify-face", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selfieBase64, documentBase64, mimeType: "image/jpeg" }),
    }),

  submitKYCDocument: async (file: File, docType: string) => ({
    data: {
      filename: file.name,
      document_type: docType,
      url: URL.createObjectURL(file),
      status: "uploaded",
    },
  }),

  // Broker OAuth / connections (Deriv, Alpaca, etc.) - always relative,
  // always hits the EC2 backend via the /api/* proxy, never the Azure BASE.
  getBrokerConnections: () => safeFetchRelative("/api/v1/auth/connections"),
  getBrokerCatalog: () => safeFetchRelative("/api/v1/auth/brokers"),
  disconnectBroker: (broker: string, accountType: string = "live") =>
    safeFetchRelative(`/api/v1/auth/connections/${broker}?account_type=${accountType}`, { method: "DELETE" }),

  // Claims any broker connections made before login (anonymous, keyed by
  // getAppUserId()) onto the now-verified Auth0 identity. Call once per
  // session right after isAuthenticated becomes true (see LoginGate.tsx).
  linkAnonymousConnections: () =>
    safeFetchRelative("/api/v1/auth/link-anonymous", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anonymous_id: getAppUserId() }),
    }),

  // Multi-account Deriv management: every linked loginid, per-type
  // defaults, and the resolved active account for a mode.
  getDerivAccounts: () => safeFetchRelative("/api/v1/auth/deriv/accounts"),
  // Real per-account balances (demo + live), resolved server-side
  // through the linked adapters. balance=null means unreachable,
  // never zero-filled.
  getDerivBalances: () => safeFetchRelative("/api/v1/auth/deriv/balances"),
  // Self-heal for rotted OAuth sessions: renews stored sessions via
  // refresh_token and re-registers adapters. No-ops when nothing is
  // stored. Called once when the account list comes back empty.
  refreshDerivSession: () =>
    safeFetchRelative("/api/v1/auth/deriv/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }),
  setDerivDefault: (loginid: string) =>
    safeFetchRelative("/api/v1/auth/deriv/default-account", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ loginid }),
    }),
  getActiveDerivAccount: (mode: "demo" | "live") =>
    safeFetchRelative(`/api/v1/auth/deriv/active-account?mode=${mode}`),

  // Billing / PayFast. payment_api.router is mounted at /api/v1/payment
  // in main.py (fixed: it was previously mounted with no prefix at all,
  // making it unreachable through the vercel /api/* proxy -- confirmed
  // live: GET /plans -> 200 with real data, but GET /api/plans -> 404
  // before this fix). Always relative, through the same proxy as
  // everything else above -- never the retired Azure BASE. The backend
  // resolves the paying user from the verified Auth0 Bearer token sent
  // by withUserHeader() above, never from a client-supplied user id.
  getPlans: () => safeFetchRelative("/api/v1/payment/plans"),
  getMySubscription: () => safeFetchRelative("/api/v1/payment/subscriptions/me"),
  createPayfastSubscription: (payload: {
    plan_id: string;
    return_url: string;
    cancel_url: string;
    notify_url: string;
    user_email?: string;
    user_first_name?: string;
    user_last_name?: string;
    billing_frequency?: string;
  }) =>
    safeFetchRelative("/api/v1/payment/payfast/create-subscription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  createPayfastPayment: (payload: {
    plan_id: string;
    return_url: string;
    cancel_url: string;
    notify_url: string;
    user_email?: string;
    user_first_name?: string;
    user_last_name?: string;
  }) =>
    safeFetchRelative("/api/v1/payment/payfast/create-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  cancelPayfastSubscription: (subscriptionId: string) =>
    safeFetchRelative(`/api/v1/payment/payfast/cancel-subscription/${subscriptionId}`, { method: "POST" }),

  // Subscriber signals (mounted at /api/v1/signals). Preferences choose
  // the instruments per paid tier; history mixes the caller's issued
  // signals with the global landing-ticket archive.
  getSignalTiers: () => safeFetchRelative("/api/v1/signals/tiers"),
  getSignalCategories: () => safeFetchRelative("/api/v1/signals/categories"),
  getSignalPreferences: () => safeFetchRelative("/api/v1/signals/preferences"),
  setSignalPreferences: (payload: {
    category: string;
    instruments: string[];
    delivery_channel: string;
    contact_email?: string;
    contact_phone?: string;
    broker?: string;
  }) =>
    safeFetchRelative("/api/v1/signals/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getSignalHistory: (limit: number = 50) =>
    safeFetchRelative(`/api/v1/signals/history?limit=${limit}`),
  getCurrentSignal: () => safeFetchRelative("/api/signals/current"),
  // In-app signal notifications: items + unread count (signals issued
  // after the last read), and the read-ack that advances the marker.
  getSignalNotifications: (limit: number = 25) =>
    safeFetchRelative(`/api/v1/signals/notifications?limit=${limit}`),
  markSignalNotificationsRead: () =>
    safeFetchRelative("/api/v1/signals/notifications/read", { method: "POST" }),
  // Web push for position alerts (opened / TP hit / SL hit) on this device.
  getVapidPublicKey: () =>
    safeFetchRelative("/api/v1/signals/push/vapid-public-key"),
  pushSubscribe: (subscription: { endpoint: string; keys: { p256dh: string; auth: string } }) =>
    safeFetchRelative("/api/v1/signals/push/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(subscription),
    }),
  pushUnsubscribe: (endpoint: string) =>
    safeFetchRelative("/api/v1/signals/push/unsubscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ endpoint }),
    }),
  testPush: () => safeFetchRelative("/api/v1/signals/push/test", { method: "POST" }),

  // Contact OTP verification + emotion check-in log (backend/api/verify_api.py).
  getVerifiedContacts: () => safeFetchRelative("/api/v1/verify/contacts"),
  requestOtp: (channel: string, contact: string) =>
    safeFetchRelative("/api/v1/verify/otp/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel, contact }),
    }),
  confirmOtp: (channel: string, contact: string, code: string) =>
    safeFetchRelative("/api/v1/verify/otp/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel, contact, code }),
    }),
  // Server-side profile (client_profiles row + verified contacts). The
  // single source of truth so data follows the account across devices;
  // localStorage is only a fast-paint cache (backend/api/identity_sync_api.py).
  getMyProfile: () => safeFetchRelative("/api/v1/identity/me"),
  updateMyProfile: (fields: {
    email?: string; // accepted only when the account has no email yet
    given_name?: string;
    family_name?: string;
    phone?: string;
    country?: string;
    experience?: string;
    trading_goal?: string;
    risk_appetite?: string;
    leverage?: number;
    node_tier?: string;
  }) =>
    safeFetchRelative("/api/v1/identity/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fields),
    }),
  getEmotionHistory: (days: number = 30) =>
    safeFetchRelative(`/api/v1/verify/emotion/history?days=${days}`),
  getEmotionCheckin: (id: number) =>
    safeFetchRelative(`/api/v1/verify/emotion/checkin/${id}`),
  deleteEmotionCheckin: (id: number) =>
    safeFetchRelative(`/api/v1/verify/emotion/checkin/${id}`, { method: "DELETE" }),

  // Referrals: own code/link/count + one-time bind of a landing ?ref=.
  getMyReferral: () => safeFetchRelative("/api/v1/referrals/me"),
  bindReferral: (code: string) =>
    safeFetchRelative("/api/v1/referrals/bind", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    }),

  // Tax: full eTax country registry + the caller's own country.
  getTaxCountries: () => safeFetchRelative("/api/v1/tax/supported_countries"),
  getMyTaxCountry: () => safeFetchRelative("/api/v1/tax/my-country"),

  // Signal broker directory (Deriv OAuth + XM/IFX/FBS affiliate links).
  getSignalBrokers: () => safeFetchRelative("/api/v1/signals/brokers"),
};

export default apiClient;
