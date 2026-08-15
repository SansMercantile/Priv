// Ported/adapted from the official Deriv PrivCore_lite reference app
// (source: repos/priv_core/src/external/deriv-core/auth/storage.ts and types/auth.ts)

export interface DerivAuthInfo {
  access_token: string;
  token_type: string;
  expires_in: number;
  expires_at: number;
  scope?: string;
  refresh_token?: string;
}

export interface DerivAccount {
  account_id: string;
  account_type: "demo" | "real" | string;
  currency?: string;
  balance?: string; // real balance, returned directly by Deriv's /accounts endpoint
  [key: string]: unknown;
}

const CSRF_TOKEN_KEY = "deriv_oauth_csrf_token";
const CODE_VERIFIER_KEY = "deriv_oauth_code_verifier";
const AUTH_INFO_KEY = "deriv_auth_info";
const ACCOUNTS_KEY = "deriv_accounts";
const ACTIVE_LOGINID_KEY = "deriv_active_loginid";
const ACCOUNT_TYPE_KEY = "deriv_account_type";

const TOKEN_MAX_AGE_MS = 10 * 60 * 1000; // 10 minutes

interface StoredWithTimestamp {
  value: string;
  createdAt: number;
}

export function storeCSRFToken(token: string): void {
  const stored: StoredWithTimestamp = { value: token, createdAt: Date.now() };
  sessionStorage.setItem(CSRF_TOKEN_KEY, JSON.stringify(stored));
}

export function getCSRFToken(): string | null {
  const raw = sessionStorage.getItem(CSRF_TOKEN_KEY);
  if (!raw) return null;
  const stored: StoredWithTimestamp = JSON.parse(raw);
  if (Date.now() - stored.createdAt > TOKEN_MAX_AGE_MS) {
    clearCSRFToken();
    return null;
  }
  return stored.value;
}

export function clearCSRFToken(): void {
  sessionStorage.removeItem(CSRF_TOKEN_KEY);
}

export function storeCodeVerifier(verifier: string): void {
  const stored: StoredWithTimestamp = { value: verifier, createdAt: Date.now() };
  sessionStorage.setItem(CODE_VERIFIER_KEY, JSON.stringify(stored));
}

export function getCodeVerifier(): string | null {
  const raw = sessionStorage.getItem(CODE_VERIFIER_KEY);
  if (!raw) return null;
  const stored: StoredWithTimestamp = JSON.parse(raw);
  if (Date.now() - stored.createdAt > TOKEN_MAX_AGE_MS) {
    clearCodeVerifier();
    return null;
  }
  return stored.value;
}

export function clearCodeVerifier(): void {
  sessionStorage.removeItem(CODE_VERIFIER_KEY);
}

export function storeAuthInfo(authInfo: DerivAuthInfo): void {
  localStorage.setItem(AUTH_INFO_KEY, JSON.stringify(authInfo));
}

export function getAuthInfo(): DerivAuthInfo | null {
  const raw = localStorage.getItem(AUTH_INFO_KEY);
  if (!raw) return null;
  const authInfo: DerivAuthInfo = JSON.parse(raw);
  if (authInfo.expires_at && Date.now() > authInfo.expires_at * 1000) {
    return null;
  }
  return authInfo;
}

export function clearAuthInfo(): void {
  localStorage.removeItem(AUTH_INFO_KEY);
}

export function storeDerivAccounts(accounts: DerivAccount[]): void {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
}

export function getDerivAccounts(): DerivAccount[] | null {
  const raw = localStorage.getItem(ACCOUNTS_KEY);
  if (!raw) return null;
  return JSON.parse(raw);
}

export function clearDerivAccounts(): void {
  localStorage.removeItem(ACCOUNTS_KEY);
}

export function setActiveLoginId(loginId: string): void {
  localStorage.setItem(ACTIVE_LOGINID_KEY, loginId);
}

export function getActiveLoginId(): string | null {
  return localStorage.getItem(ACTIVE_LOGINID_KEY);
}

export function setAccountType(type: "demo" | "real" | string): void {
  localStorage.setItem(ACCOUNT_TYPE_KEY, type);
}

export function getAccountType(): string | null {
  return localStorage.getItem(ACCOUNT_TYPE_KEY);
}

export function clearAllDerivAuthData(): void {
  clearCSRFToken();
  clearCodeVerifier();
  clearAuthInfo();
  clearDerivAccounts();
  localStorage.removeItem(ACTIVE_LOGINID_KEY);
  localStorage.removeItem(ACCOUNT_TYPE_KEY);
}
