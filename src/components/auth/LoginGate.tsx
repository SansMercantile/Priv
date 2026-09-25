import React, { useEffect, useRef, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { getAppUserId } from "../../lib/appUserId";
import { setAuthTokenGetter } from "../../lib/authToken";
import {
  isDerivCallback,
  derivReturnEmpty,
  clearDerivPending,
  markDerivDone,
  handleDerivCallback,
  DerivOAuthError,
} from "../../lib/derivAuth/oauth";
import DerivConnectCard from "../DerivConnectCard";
import apiClient from "../../api/apiClient";

interface LoginGateProps {
  children: React.ReactNode;
}

// NOTE (AWS migration): backend calls go same-origin (/api/* proxy);
// the retired Azure VITE_API_BASE_URL host is no longer referenced.

/**
 * Auth0 is the one login. Deriv is a BROKER connection made inside the
 * app (profile brokers tab, dashboard locked screen, first-run onboarding)
 * via the client-side PKCE flow (src/lib/derivAuth, auth.deriv.com), with
 * tokens handed to the backend for real execution. Deriv never logs anyone
 * into Priv itself.
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

function LoginScreen({ derivError }: {
  derivError?: string | null;
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
  const { isAuthenticated, isLoading, error, user, getAccessTokenSilently } = useAuth0();
  const [derivConnected, setDerivConnected] = useState(false);
  const [derivChecked, setDerivChecked] = useState(false);
  const [derivError, setDerivError] = useState<string | null>(null);
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

  // PKCE return leg: Deriv redirected back with ?code&state. Exchange the
  // code (proves the user consented at Deriv), hand the access token to the
  // backend so execution/adapters are real, then reload into the app.
  useEffect(() => {
    if (window.location.pathname !== "/") return;
    if (!isDerivCallback()) {
      // A previous Connect attempt never produced a Deriv callback (user
      // abandoned the Deriv tab, or Deriv bounced to marketing instead of
      // authorizing). Say so plainly instead of silent nothing.
      if (derivReturnEmpty()) {
        const msg =
          "Returned from Deriv without credentials — the Deriv tab was closed, or Deriv did not authorize this app. Try Connect again, or use the API-token option.";
        setDerivError(msg);
        setDerivChecked(true);
        try {
          sessionStorage.setItem("priv_deriv_error", msg);
        } catch (_) {
          /* ignore */
        }
      }
      return;
    }
    let cancelled = false;
    // Genuine Deriv return: the pending flag has served its purpose.
    clearDerivPending();
    // Fire-and-forget stage telemetry so a stuck return leg is diagnosable
    // server-side (stage only, no user data). Never throws.
    const ping = (stage: string, detail?: string) => {
      try {
        const body = JSON.stringify({ stage, detail, user_id: getAppUserId() });
        if (navigator.sendBeacon) {
          navigator.sendBeacon(
            "/api/v1/auth/deriv/callback-ping",
            new Blob([body], { type: "application/json" })
          );
        } else {
          fetch("/api/v1/auth/deriv/callback-ping", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body,
            keepalive: true,
          }).catch(() => {});
        }
      } catch (_) {
        /* telemetry must never break the flow */
      }
    };
    (async () => {
      try {
        ping("started");
        const authInfo = await handleDerivCallback();
        if (cancelled) return;
        ping("exchanged");
        await apiClient.post("/api/v1/auth/deriv/connect-token", {
          api_token: authInfo.access_token,
          user_id: getAppUserId(),
        });
        if (cancelled) return;
        ping("posted");
        markDerivDone();
        window.location.reload();
      } catch (e: any) {
        if (cancelled) return;
        const msg = e instanceof DerivOAuthError
          ? e.message
          : (e?.message || "deriv_callback_failed");
        ping("failed", msg);
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

  // First-run onboarding: right after Auth0 sign-in, if this identity
  // has never linked Deriv (and hasn't dismissed this), pop the connect
  // card first -- demo mode runs on their real Deriv demo once linked.
  const onboardKey =
    `priv-onboarded-deriv:${user?.sub || getAppUserId()}`;
  const [onboarding, setOnboarding] = useState(() => {
    try {
      return !localStorage.getItem(onboardKey);
    } catch (_) {
      return false;
    }
  });
  const dismissOnboarding = () => {
    try {
      localStorage.setItem(onboardKey, new Date().toISOString());
    } catch (_) {
      /* ignore */
    }
    setOnboarding(false);
  };
  const showOnboarding =
    onboarding && isAuthenticated && derivChecked && !derivConnected;

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
    return <LoginScreen derivError={derivError} />;
  }

  return (
    <>
      {children}
      {showOnboarding && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md bg-zinc-950 border border-white/10 rounded-2xl p-6 space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Connect your Deriv account</h2>
              <p className="text-xs text-zinc-400 font-mono mt-1 leading-relaxed">
                One last step: click below, log in (or sign up) on Deriv's
                site in any tab, approve the connect screen, and you'll land
                back here linked. Then pick demo or live under Profile →
                Broker Connections.
              </p>
            </div>
            <DerivConnectCard />
            <button
              onClick={dismissOnboarding}
              className="w-full py-2 text-xs font-mono text-zinc-500 hover:text-zinc-300 underline"
            >
              Skip for now
            </button>
          </div>
        </div>
      )}
    </>
  );
}
