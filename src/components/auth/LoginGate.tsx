import React, { useEffect, useRef, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { getAppUserId } from "../../lib/appUserId";
import { setAuthTokenGetter } from "../../lib/authToken";
import {
  isDerivCallback,
  handleDerivCallback,
  DerivOAuthError,
} from "../../lib/derivAuth/oauth";
import apiClient from "../../api/apiClient";

interface LoginGateProps {
  children: React.ReactNode;
}

// NOTE (AWS migration): backend calls go same-origin (/api/* proxy);
// the retired Azure VITE_API_BASE_URL host is no longer referenced.

/**
 * Deriv connection now goes entirely through the backend's legacy
 * app_id OAuth flow (backend/trading_engine/oauth_api.py), which is the
 * only flow that lets the backend actually execute trades -- the
 * previous client-side PKCE flow (src/lib/derivAuth) kept the token in
 * the browser only, with no route to the backend, and is retired from
 * this login screen. Deriv is now purely a BROKER connection made via
 * getAppUserId() (the same anonymous per-browser id already used to
 * scope broker connections independent of Auth0 -- see appUserId.ts),
 * not an app-identity/login method the way it briefly was.
 */
async function checkDerivConnected(): Promise<boolean> {
  try {
    const { data } = await apiClient.getBrokerConnections();
    const connections = data?.data?.connections || [];
    return connections.some((c: { broker: string }) => c.broker === "deriv");
  } catch {
    return false;
  }
}

/** Detects the backend's generic OAuth redirect (?broker=...&status=...),
 * used by Deriv and Alpaca alike (see oauth_api.py _redirect_frontend).
 * Cleans the URL afterward regardless of outcome. */
function useBrokerOAuthCallbackHandler(onDone: (result: { broker: string; success: boolean; message?: string }) => void) {
  const [processing, setProcessing] = useState(() => new URLSearchParams(window.location.search).has("broker"));

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const broker = params.get("broker");
    if (!broker) return;

    const status = params.get("status");
    const message = params.get("message") || undefined;

    const url = new URL(window.location.href);
    ["broker", "status", "message"].forEach((p) => url.searchParams.delete(p));
    window.history.replaceState(window.history.state, "", url.pathname + url.search);

    onDone({ broker, success: status === "success", message });
    setProcessing(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return processing;
}

function LoginScreen({ derivError, onDerivLogin, derivLoading }: {
  derivError?: string | null;
  onDerivLogin: () => void;
  derivLoading: boolean;
}) {
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
        <p className="text-sm text-white/50 mb-6">PRIV Core — sign in to continue</p>

        {derivError && (
          <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
            Deriv connection failed ({derivError}). Please try again.
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={onDerivLogin}
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
  const { isAuthenticated, isLoading, error, getAccessTokenSilently } = useAuth0();
  const [derivConnected, setDerivConnected] = useState(false);
  const [derivChecked, setDerivChecked] = useState(false);
  const [derivError, setDerivError] = useState<string | null>(null);
  const [derivLoading, setDerivLoading] = useState(false);
  const linkedAnonymousRef = useRef(false);

  // Registers the real token getter for apiClient.ts (a plain module that
  // can't call useAuth0() itself) as soon as it's available, and clears it
  // on logout so requests fall back to the anonymous flow rather than
  // sending a stale/invalid token.
  useEffect(() => {
    if (!isAuthenticated) {
      setAuthTokenGetter(null);
      return;
    }
    setAuthTokenGetter(() => getAccessTokenSilently());
    // One-time per session: claim any broker connections made before
    // login under the verified identity. Safe to call repeatedly (it's
    // idempotent server-side) but there's no reason to.
    if (!linkedAnonymousRef.current) {
      linkedAnonymousRef.current = true;
      apiClient.linkAnonymousConnections().catch(() => {
        // Non-fatal -- worst case a pre-login Deriv connection stays
        // anonymous and the user reconnects it manually.
        linkedAnonymousRef.current = false;
      });
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  const callbackProcessing = useBrokerOAuthCallbackHandler(({ broker, success, message }) => {
    if (broker !== "deriv") return;
    if (success) {
      setDerivConnected(true);
    } else {
      setDerivError(message || "connection_failed");
    }
  });

  useEffect(() => {
    if (callbackProcessing) return; // avoid a redundant check right before the callback sets it directly
    checkDerivConnected().then((connected) => {
      setDerivConnected(connected);
      setDerivChecked(true);
    });
  }, [callbackProcessing]);

  const handleDerivLogin = () => {
    setDerivLoading(true);
    setDerivError(null);
    // Client-side PKCE via auth.deriv.com (the working August flow -- the
    // backend-driven oauth.deriv.com route is bounced to marketing by Deriv).
    // Deriv shows login/signup, then the connect-consent screen, then sends
    // the browser back here with ?code&state, handled below.
    initiateDerivLoginSafe();
  };

  async function initiateDerivLoginSafe() {
    try {
      const { initiateDerivLogin } = await import("../../lib/derivAuth/oauth");
      await initiateDerivLogin();
    } catch (e: any) {
      setDerivLoading(false);
      setDerivError(e?.message || "deriv_init_failed");
    }
  }

  // PKCE return leg: Deriv redirected back with ?code&state. Exchange the
  // code (proves the user consented at Deriv), hand the access token to the
  // backend so execution/adapters are real, then reload into the app.
  useEffect(() => {
    if (!isDerivCallback()) return;
    let cancelled = false;
    (async () => {
      try {
        const authInfo = await handleDerivCallback();
        if (cancelled) return;
        await apiClient.post("/api/v1/auth/deriv/connect-token", {
          api_token: authInfo.access_token,
          user_id: getAppUserId(),
        });
        window.location.reload();
      } catch (e: any) {
        if (cancelled) return;
        const msg = e instanceof DerivOAuthError
          ? e.message
          : (e?.message || "deriv_callback_failed");
        setDerivError(msg);
        setDerivChecked(true);
        try {
          // The locked dashboard screen (mounted when still unconnected)
          // reads and clears this to show the failure inline.
          sessionStorage.setItem("priv_deriv_error", msg);
        } catch (_) {
          /* ignore */
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (isLoading || callbackProcessing || (!derivChecked && !derivConnected)) {
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
    return <LoginScreen derivError={derivError} onDerivLogin={handleDerivLogin} derivLoading={derivLoading} />;
  }

  return <>{children}</>;
}
