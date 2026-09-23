import React, { useState } from "react";
import { useBrokerConnections } from "../lib/useBrokerConnections";
import { getAppUserId } from "../lib/appUserId";
import { initiateDerivLogin } from "../lib/derivAuth/oauth";
import apiClient from "../api/apiClient";

// One shared Deriv connect surface used by the dashboard locked screen,
// the profile brokers tab, and the first-run onboarding modal:
// live connection status, PKCE connect (auth.deriv.com login + consent),
// and an API-token fallback for when Deriv's OAuth app misbehaves.
// Successful connects reload the page so all connection state refreshes.
export default function DerivConnectCard() {
  const { hasRealDeriv, hasDemoDeriv, loading } = useBrokerConnections();
  const [tokenOpen, setTokenOpen] = useState(false);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState("");
  const [returnError] = useState<string | null>(() => {
    try {
      const m = sessionStorage.getItem("priv_deriv_error");
      sessionStorage.removeItem("priv_deriv_error");
      return m;
    } catch (_) {
      return null;
    }
  });

  async function connectOAuth() {
    setError(null);
    try {
      await initiateDerivLogin();
    } catch (e: any) {
      setError(e?.message || "Could not start Deriv login.");
    }
  }

  async function connectToken(e: React.FormEvent) {
    e.preventDefault();
    const t = token.trim();
    if (!t || busy) return;
    setBusy(true);
    setError(null);
    setDone("");
    try {
      const res: any = await apiClient.post("/api/v1/auth/deriv/connect-token", {
        api_token: t,
        user_id: getAppUserId(),
      });
      const d = res?.data?.data ?? res?.data ?? {};
      setDone(`Linked ${d.loginid || "Deriv account"} (${d.account_type || "live"}). Reloading…`);
      setToken("");
      window.setTimeout(() => window.location.reload(), 1200);
    } catch (err: any) {
      setError(err?.message || "Deriv refused the token.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs font-mono">
        <span
          className={`w-2 h-2 rounded-full ${
            hasRealDeriv || hasDemoDeriv ? "bg-emerald-400 animate-pulse" : "bg-red-500"
          }`}
        />
        <span className="text-zinc-300">
          {loading
            ? "Checking Deriv connection…"
            : hasRealDeriv
              ? "Deriv REAL account linked"
              : hasDemoDeriv
                ? "Deriv DEMO account linked"
                : "No Deriv account linked"}
        </span>
      </div>

      {(returnError || error) && (
        <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-mono">
          Deriv connection failed: {returnError || error}
        </div>
      )}
      {done && (
        <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-xs font-mono">
          {done}
        </div>
      )}

      {!hasRealDeriv && (
        <button
          onClick={connectOAuth}
          className="px-5 py-2.5 bg-white text-black font-mono font-bold text-xs rounded-lg hover:bg-white/90 transition"
        >
          Connect Deriv account
        </button>
      )}

      <div>
        <button
          onClick={() => setTokenOpen((o) => !o)}
          className="text-[11px] font-mono text-zinc-500 underline hover:text-zinc-300"
        >
          {tokenOpen ? "Hide API-token option" : "Deriv page not redirecting back? Use an API token instead"}
        </button>
        {tokenOpen && (
          <form onSubmit={connectToken} className="mt-2 space-y-2">
            <p className="text-[11px] text-zinc-400 font-mono leading-relaxed">
              Deriv → Account settings → API token → Create (Trade + Account
              management, ≤ 90 days) → paste below. Validated securely, never
              stored in the browser.
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Deriv API token"
                autoComplete="off"
                className="flex-1 bg-black border border-white/10 rounded p-2 text-xs text-white font-mono focus:outline-none focus:border-white/30"
              />
              <button
                type="submit"
                disabled={busy || !token.trim()}
                className="px-4 py-2 bg-white text-black font-mono text-xs font-bold rounded disabled:opacity-40"
              >
                {busy ? "Validating…" : "Link token"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
