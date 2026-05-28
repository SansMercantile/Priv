// High-integrity API Client for SANS PRIV Core KYC, Profile, and billing services

const BASE = (import.meta as any).env?.VITE_API_BASE_URL || "";

async function safeFetch(url: string, options?: RequestInit) {
  const fullUrl = `${BASE}${url}`;
  const response = await fetch(fullUrl, options);
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

  // KYC handlers
  getKycRecord: () => safeFetch("/api/kyc/record"),
  getKycStatus: () => safeFetch("/api/kyc/status"),
  saveKycDraft: (form: any) =>
    safeFetch("/api/kyc/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }),
  submitKyc: (form: any) =>
    safeFetch("/api/kyc/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }),

  // AI document verification (sends base64 image to Gemini via backend)
  verifyDocument: (documentBase64: string, mimeType: string, formData: any) =>
    safeFetch("/api/kyc/verify-document", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documentBase64, mimeType, formData }),
    }),

  // AI face / liveness verification
  verifyFace: (selfieBase64: string, documentBase64?: string) =>
    safeFetch("/api/kyc/verify-face", {
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
};

export default apiClient;
