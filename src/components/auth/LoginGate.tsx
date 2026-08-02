import React, { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import apiClient from "../../api/apiClient";

interface LoginGateProps {
  children: React.ReactNode;
}

const DERIV_SESSION_KEY = "priv_deriv_connected";

function isOAuthCallbackPath() {
  return window.location.pathname === "/oauth/callback";
}

/** Processes ?broker=deriv&status=success|error redirects from the backend
 * OAuth callback, then cleans the URL. Returns while still processing. */
function useOAuthCallbackHandler(onDone: (result: { success: boolean; message?: string }) => void) {
  const [processing, setProcessing] = useState(isOAuthCallbackPath());

  useEffect(() => {
    if (!isOAuthCallbackPath()) return;
    const params = new URLSearchParams(window.location.search);
    const broker = params.get("broker");
    const status = params.get("status");
    const message = params.get("message") || undefined;

    if (broker === "deriv" && status === "success") {
      try {
        window.localStorage.setItem(DERIV_SESSION_KEY, "1");
      } catch {
        // ignore storage failures, session check will just re-verify via API
      }
      onDone({ success: true });
    } else {
      onDone({ success: false, message: message || status || "unknown_error" });
    }
    window.history.replaceState({}, document.title, "/dashboard");
    setProcessing(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return processing;
}

/** True if we previously saw a successful Deriv connect. This is optimistic
 * (persisted locally); the real source of truth is the backend's
 * /api/v1/auth/connections list, which the app re-checks after landing. */
function hasLocalDerivSession(): boolean {
  try {
    return window.localStorage.getItem(DERIV_SESSION_KEY) === "1";
  } catch {
    return false;
  }
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

  const handleDerivLogin = () => {
    setDerivLoading(true);
    // Relative path - goes through the Vercel proxy straight to the backend,
    // which redirects to Deriv's own login/signup page (Deriv handles new
    // account creation itself; every new account gets a demo/virtual
    // account automatically).
    window.location.href = "/api/v1/auth/deriv/login?account_type=demo";
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
  const [derivChecked, setDerivChecked] = useState(false);
  const [derivConnected, setDerivConnected] = useState(hasLocalDerivSession());
  const [derivError, setDerivError] = useState<string | null>(null);

  const oauthProcessing = useOAuthCallbackHandler(({ success, message }) => {
    if (success) {
      setDerivConnected(true);
    } else {
      setDerivError(message || "connection_failed");
      try {
        window.localStorage.removeItem(DERIV_SESSION_KEY);
      } catch {
        /* ignore */
      }
    }
  });

  // Re-verify against the backend (source of truth) once, on load, so a
  // stale/cleared localStorage flag doesn't wrongly gate someone out, and a
  // revoked connection doesn't wrongly leave someone in.
  useEffect(() => {
    let cancelled = false;
    apiClient
      .getBrokerConnections()
      .then(({ data }) => {
        if (cancelled) return;
        const hasDeriv = (data?.data?.connections || []).some((c: any) => c.broker === "deriv");
        setDerivConnected(hasDeriv);
        try {
          if (hasDeriv) window.localStorage.setItem(DERIV_SESSION_KEY, "1");
          else window.localStorage.removeItem(DERIV_SESSION_KEY);
        } catch {
          /* ignore */
        }
      })
      .catch(() => {
        // Backend unreachable - fall back to whatever we had locally rather
        // than locking the user out.
      })
      .finally(() => !cancelled && setDerivChecked(true));
    return () => {
      cancelled = true;
    };
  }, []);

  if (isLoading || oauthProcessing || !derivChecked) {
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
