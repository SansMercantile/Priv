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

  // KYC handlers (relative: served by our backend via the /api/* proxy,
  // never the retired Azure host)
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

  // AI document verification (sends base64 image to Gemini via backend)
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
};

export default apiClient;
