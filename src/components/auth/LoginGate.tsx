import React from "react";
import { useAuth0 } from "@auth0/auth0-react";

interface LoginGateProps {
  children: React.ReactNode;
}

function LoginScreen() {
  const { loginWithRedirect, isLoading } = useAuth0();

  const handleLogin = (connection?: string) => {
    loginWithRedirect({
      authorizationParams: connection ? { connection } : undefined,
      appState: { returnTo: window.location.pathname },
    });
  };

  return (
    <div className="min-h-screen bg-black neural-grid matrix-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-black/60 border border-white/10 rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <h1 className="text-2xl font-semibold text-white mb-1 tracking-tight">
          Sans Mercantile™
        </h1>
        <p className="text-sm text-white/50 mb-8">PRIV Core — sign in to continue</p>

        <div className="space-y-3">
          <button
            onClick={() => handleLogin("google-oauth2")}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-white text-black font-medium py-2.5 px-4 hover:bg-white/90 transition disabled:opacity-50"
          >
            Continue with Google
          </button>

          <button
            disabled
            title="Microsoft sign-in is being configured"
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-[#2f2f2f]/40 text-white/40 font-medium py-2.5 px-4 cursor-not-allowed"
          >
            Continue with Microsoft (coming soon)
          </button>

          <div className="flex items-center gap-3 py-2">
            <div className="h-px flex-1 bg-white/10" />
            <span className="text-xs text-white/30">or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <button
            onClick={() => handleLogin()}
            disabled={isLoading}
            className="w-full rounded-lg border border-white/15 text-white font-medium py-2.5 px-4 hover:bg-white/5 transition disabled:opacity-50"
          >
            Continue with email
          </button>
        </div>

        <p className="text-xs text-white/30 mt-8 text-center">
          By continuing you agree to Sans Mercantile's Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}

export default function LoginGate({ children }: LoginGateProps) {
  const { isAuthenticated, isLoading, error } = useAuth0();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white/40 text-sm font-mono">Loading…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center px-4">
        <div className="text-rose-300 text-sm font-mono max-w-md text-center">
          Authentication error: {error.message}
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return <>{children}</>;
}
