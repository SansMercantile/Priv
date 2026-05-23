import React from 'react';
import UserProfileEditor from '../components/profile/UserProfileEditor';

export default function ProfilePage({ demoMode }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-serif italic text-white">Profile & Trading Preferences</h1>
        <p className="text-white/40 text-xs mt-1 font-light">
          {demoMode
            ? 'Demo profile — changes are not persisted to a live account.'
            : 'Legal identity, trading knowledge, risk appetite, goals, and profile photo (KYC-aligned).'}
        </p>
      </div>
      <div className="metric-card rounded border border-white/10 p-4">
        <UserProfileEditor demoMode={demoMode} />
      </div>
    </div>
  );
}
