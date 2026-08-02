import React, { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import {
  initiateDerivLogin,
  isDerivCallback,
  handleDerivCallback,
  fetchDerivAccounts,
  getAuthInfo as getDerivAuthInfo,
  getDerivAccounts,
  DerivOAuthError,
} from "../../lib/derivAuth";

interface LoginGateProps {
  children: React.ReactNode;
}

/** True if we have a real, non-expired Deriv session already (from a
 * previous visit). This is the source of truth for "logged in via Deriv" -
 * no separate flag needed, getAuthInfo() already checks expiry. */
function hasDerivSession(): boolean {
  return !!getDerivAuthInfo();
}

function useDerivCallbackHandler(onDone: (result: { success: boolean; message?: string }) => void) {
  const [processing, setProcessing] = useState(isDerivCallback());

  useEffect(() => {
    if (!isDerivCallback()) return;
    (async () => {
      try {
        const authInfo = await handleDerivCallback();
        await fetchDerivAccounts(authInfo);
        onDone({ success: true });
      } catch (err) {
        const message = err instanceof DerivOAuthError ? err.message : "unknown_error";
        onDone({ success: false, message });
      } finally {
        setProcessing(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return processing;
}

function LoginScreen({ derivError }: { derivError?: string | null }) {
  const { loginWithRedirect, isLoading } = useAuth0();
  const [derivLoading, setDerivLoading] = useState(false);

  const handleLogin = (connection?: string) => {
    loginWithRedirect({
      authorizationParams: connection ? { connection } : undefined,
      appState: { returnTo: window.location.pathname },
    });
  };

  const handleDerivLogin = async () => {
    setDerivLoading(true);
    await initiateDerivLogin();
  };

  return (
    <div className="min-h-screen bg-black neural-grid matrix-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-black/60 border border-white/10 rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <h1 className="text-2xl font-semibold text-white mb-1 tracking-tight">
          Sans Mercantile™
        </h1>
        <p className="text-sm text-white/50 mb-6">PRIV Core — sign in to continue</p>

        {derivError && (
          <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
            Deriv connection failed ({derivError}). Please try again.
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleDerivLogin}
            disabled={derivLoading}
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-rose-600 text-white font-medium py-2.5 px-4 hover:bg-rose-500 transition disabled:opacity-50"
          >
            {derivLoading ? "Redirecting to Deriv…" : "Continue with Deriv"}
          </button>

          <div className="flex items-center gap-3 py-1">
            <div className="h-px flex-1 bg-white/10" />
            <span className="text-xs text-white/30">or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <button
            onClick={() => handleLogin("google-oauth2")}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-white text-black font-medium py-2.5 px-4 hover:bg-white/90 transition disabled:opacity-50"
          >
            Continue with Google
          </button>

          <button
            disabled
            title="Microsoft sign-in needs a real Azure AD app registration (Auth0's dev keys don't cover this provider)"
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-[#2f2f2f]/40 text-white/40 font-medium py-2.5 px-4 cursor-not-allowed"
          >
            Continue with Microsoft (coming soon)
          </button>

          <button
            onClick={() => handleLogin("apple")}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 rounded-lg bg-white text-black font-medium py-2.5 px-4 hover:bg-white/90 transition disabled:opacity-50"
          >
            Continue with Apple
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
  const [derivConnected, setDerivConnected] = useState(hasDerivSession());
  const [derivError, setDerivError] = useState<string | null>(null);

  const derivProcessing = useDerivCallbackHandler(({ success, message }) => {
    if (success) {
      setDerivConnected(true);
    } else {
      setDerivError(message || "connection_failed");
    }
  });

  if (isLoading || derivProcessing) {
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

  if (!isAuthenticated && !derivConnected) {
    return <LoginScreen derivError={derivError} />;
  }

  return <>{children}</>;
}
