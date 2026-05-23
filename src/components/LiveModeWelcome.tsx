import React from 'react';
import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { getKycStatus, hasLiveSession, isProfileComplete } from '../lib/environment';

/** Subtle live-mode checklist when user is in production path without full onboarding. */
export default function LiveModeWelcome() {
  if (!hasLiveSession()) return null;

  const profileDone = isProfileComplete();
  const kyc = getKycStatus();
  const kycDone = kyc === 'submitted' || kyc === 'verified';

  if (profileDone && kycDone) return null;

  return (
    <div className="border-b border-emerald-500/20 bg-emerald-950/40 px-4 py-2 text-center text-xs text-emerald-100/90">
      <Shield className="inline h-3.5 w-3.5 mr-1 -mt-0.5 text-emerald-400" />
      Live environment — complete your{' '}
      {!profileDone && (
        <Link to="/create-profile" className="underline font-semibold text-emerald-300">
          profile
        </Link>
      )}
      {!profileDone && !kycDone && ' and '}
      {!kycDone && (
        <Link to="/verification" className="underline font-semibold text-emerald-300">
          KYC verification
        </Link>
      )}
      {' '}to unlock broker-linked market analysis.
    </div>
  );
}
