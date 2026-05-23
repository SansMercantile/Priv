/** Demo vs live environment helpers (client-side). */

export const DEMO_MODE_STORAGE_KEY = 'demoMode';
export const PROFILE_COMPLETE_KEY = 'privProfileComplete';
export const KYC_STATUS_KEY = 'privKycStatus';
export const SESSION_KEY = 'privSession';

export type KycStatus = 'none' | 'pending' | 'submitted' | 'verified';

export function readDemoMode(): boolean {
  if (typeof window === 'undefined') return false;
  const saved = localStorage.getItem(DEMO_MODE_STORAGE_KEY);
  return saved ? JSON.parse(saved) : false;
}

export function writeDemoMode(enabled: boolean): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(DEMO_MODE_STORAGE_KEY, JSON.stringify(enabled));
  if (window.ENV) {
    window.ENV.DEMO_MODE = enabled;
  }
}

export function isProfileComplete(): boolean {
  return localStorage.getItem(PROFILE_COMPLETE_KEY) === 'true';
}

export function setProfileComplete(complete: boolean): void {
  localStorage.setItem(PROFILE_COMPLETE_KEY, complete ? 'true' : 'false');
}

export function getKycStatus(): KycStatus {
  const raw = localStorage.getItem(KYC_STATUS_KEY);
  if (raw === 'pending' || raw === 'submitted' || raw === 'verified') return raw;
  return 'none';
}

export function setKycStatus(status: KycStatus): void {
  localStorage.setItem(KYC_STATUS_KEY, status);
}

export function hasLiveSession(): boolean {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return false;
    const session = JSON.parse(raw);
    return Boolean(session?.email || session?.uid);
  } catch {
    return false;
  }
}

export function setLiveSession(session: { email?: string; uid?: string; displayName?: string } | null): void {
  if (!session) {
    localStorage.removeItem(SESSION_KEY);
    return;
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function canAccessLiveDashboard(): boolean {
  return hasLiveSession() && isProfileComplete() && getKycStatus() !== 'none';
}

export function getSessionUserId(): string | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw);
    return session?.uid || session?.email || null;
  } catch {
    return null;
  }
}
