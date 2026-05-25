import React from 'react';
import UserProfileEditor from './UserProfileEditor';

interface ProfilePageProps {
  demoMode?: boolean;
}

export default function ProfilePage({ demoMode = false }: ProfilePageProps) {
  return (
    <div className="space-y-6">
      {/* Page Title & Slogan descriptor */}
      <div>
        <h1 className="text-3xl font-serif italic text-white">Profile & Trading Preferences</h1>
        <p className="text-white/40 text-xs mt-1 font-light">
          {demoMode
            ? 'Demo profile — changes are loaded and cached within temporary session frames.'
            : 'Legal identity, trading knowledge, risk appetite, goals, and profile photo (KYC-aligned).'}
        </p>
      </div>

      {/* Primary Card */}
      <div className="bg-zinc-950/20 rounded-xl border border-white/10 p-5 backdrop-blur-md">
        <UserProfileEditor demoMode={demoMode} />
      </div>
    </div>
  );
}
