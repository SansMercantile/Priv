// High-integrity API Client for SANS PRIV Core KYC, Profile, and billing services using lightweight fetch

export const apiClient = {
  // Direct REST methods emulating axios return schema (with data property)
  get: async (url: string) => {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return { data };
  },

  post: async (url: string, bodyData?: any) => {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: bodyData ? JSON.stringify(bodyData) : undefined,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return { data };
  },

  // Dedicated KYC handlers as requested in KycVerificationPage
  getKycRecord: async () => {
    const response = await fetch("/api/kyc/record");
    return response.json();
  },

  getKycStatus: async () => {
    const response = await fetch("/api/kyc/status");
    return response.json();
  },

  saveKycDraft: async (form: any) => {
    const response = await fetch("/api/kyc/draft", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(form),
    });
    return response.json();
  },

  submitKyc: async (form: any) => {
    const response = await fetch("/api/kyc/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(form),
    });
    return response.json();
  },

  submitKYCDocument: async (file: File, docType: string) => {
    // Return direct data mock block
    return {
      data: {
        filename: file.name,
        document_type: docType,
        url: URL.createObjectURL(file),
        status: "uploaded"
      }
    };
  }
};

export default apiClient;
