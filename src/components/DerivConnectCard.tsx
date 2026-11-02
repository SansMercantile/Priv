import React, { useEffect, useRef, useState } from "react";
import { useBrokerConnections } from "../lib/useBrokerConnections";
import { getAppUserId } from "../lib/appUserId";
import { initiateDerivLogin } from "../lib/derivAuth/oauth";
import apiClient from "../api/apiClient";

interface DerivAccount {
  loginid: string;
  account_type: string;
  currency: string;
  broker_id: string;
  adapter_live: boolean;
  is_default: boolean;
  category?: string; // "trading" | "wallet" (wallet = Deriv money account)
}

// Survives the post-connect reload: connect responses stash every account
// Deriv reported (trading + wallet + virtual) here so the card can show a
// "found N accounts" notice after the page comes back.
const CONNECT_RESULT_KEY = "priv_deriv_connect_result";

export function stashDerivConnectResult(d: any) {
  try {
    const found = Array.isArray(d?.accounts_found) ? d.accounts_found : [];
    if (found.length) {
      localStorage.setItem(
        CONNECT_RESULT_KEY,
        JSON.stringify({ at: Date.now(), accounts: found })
      );
    }
  } catch {
    /* localStorage unavailable */
  }
}

// One shared Deriv connect surface used by the dashboard locked screen,
// the profile brokers tab, and the first-run onboarding modal:
// every linked account with per-type defaults, PKCE connect for more,
// and an API-token fallback. Successful connects reload the page so all
// connection state refreshes.
export default function DerivConnectCard() {
  const { hasRealDeriv, hasDemoDeriv, loading, refresh } = useBrokerConnections();
  const [accounts, setAccounts] = useState<DerivAccount[]>([]);
  const [tokenOpen, setTokenOpen] = useState(false);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState("");
  const refreshedRef = useRef(false);
  const [returnError] = useState<string | null>(() => {
    try {
      const m = sessionStorage.getItem("priv_deriv_error");
      sessionStorage.removeItem("priv_deriv_error");
      return m;
    } catch (_) {
      return null;
    }
  });
  // "Found N accounts" notice from the last successful connect (stashed
  // before the reload by this card or LoginGate's PKCE return leg).
  const [foundNotice, setFoundNotice] = useState<
    { at: number; accounts: any[] } | null
  >(() => {
    try {
      const raw = localStorage.getItem(CONNECT_RESULT_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      localStorage.removeItem(CONNECT_RESULT_KEY);
      if (
        !parsed?.at ||
        Date.now() - parsed.at > 10 * 60 * 1000 ||
        !Array.isArray(parsed.accounts) ||
        !parsed.accounts.length
      )
        return null;
      return parsed;
    } catch (_) {
      return null;
    }
  });

  const loadAccounts = async () => {
    try {
      const res: any = await apiClient.getDerivAccounts();
      const list = res?.data?.data?.accounts ?? res?.data?.accounts ?? [];
      setAccounts(list);
      if (list.length > 0) {
        // The shared connections hook may have loaded before the claim
        // finished (empty), leaving "No Deriv account linked" stuck on
        // screen next to a populated list. Nudge it to re-fetch.
        refresh();
        // Same staleness one level up: LoginGate's onboarding snapshot.
        // A reload used to be the only cure; now the modal closes live.
        try {
          window.dispatchEvent(new Event("priv:deriv-linked"));
        } catch {
          /* non-DOM environment */
        }
      }
      // Empty list with a previously completed connect usually means the
      // stored OAuth session rotted (access tokens expire). One refresh
      // attempt, then show whatever survived -- never loops.
      if (list.length === 0 && !refreshedRef.current) {
        refreshedRef.current = true;
        try {
          await apiClient.refreshDerivSession();
          const retry: any = await apiClient.getDerivAccounts();
          const relist = retry?.data?.data?.accounts ?? retry?.data?.accounts ?? [];
          setAccounts(relist);
          if (relist.length > 0) refresh();
        } catch {
          /* backend unreachable or nothing stored: keep status dots only */
        }
      }
    } catch (_) {
      /* backend unreachable: keep status dots only */
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

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
      stashDerivConnectResult(d);
      const n = Array.isArray(d.accounts_found) ? d.accounts_found.length : 0;
      setDone(
        `Linked ${d.loginid || "Deriv account"} (${d.account_type || "live"})` +
          (n > 1 ? ` — found ${n} Deriv accounts` : "") +
          ". Reloading…"
      );
      setToken("");
      window.setTimeout(() => window.location.reload(), 1200);
    } catch (err: any) {
      setError(err?.message || "Deriv refused the token.");
    } finally {
      setBusy(false);
    }
  }

  const linked = accounts.length > 0 || hasRealDeriv || hasDemoDeriv;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs font-mono">
        <span
          className={`w-2 h-2 rounded-full ${
            linked ? "bg-emerald-400 animate-pulse" : "bg-red-500"
          }`}
        />
        <span className="text-zinc-300">
          {loading && accounts.length === 0
            ? "Checking Deriv connection…"
            : linked
              ? `Linked (${accounts.length || "…"} account${accounts.length === 1 ? "" : "s"})`
              : "No Deriv account linked"}
        </span>
      </div>

      {foundNotice && (
        <div
          data-testid="deriv-found-notice"
          className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs font-mono space-y-2"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="text-emerald-300">
              ✓ Found {foundNotice.accounts.length} Deriv account
              {foundNotice.accounts.length === 1 ? "" : "s"} — connected:
            </span>
            <button
              onClick={() => setFoundNotice(null)}
              className="text-[10px] text-zinc-400 underline hover:text-zinc-200 whitespace-nowrap"
            >
              dismiss
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {foundNotice.accounts.map((a: any) => (
              <span
                key={a.loginid}
                className="px-1.5 py-0.5 rounded bg-black/50 border border-white/10 text-[10px] text-white"
              >
                {a.loginid}
                {a.currency ? ` · ${a.currency}` : ""} ·{" "}
                {a.is_demo ? "demo" : "live"}
                {a.category === "wallet" ? " · wallet" : ""}
              </span>
            ))}
          </div>
        </div>
      )}

      {accounts.length > 0 && (
        <div className="space-y-1.5">
          {accounts.map((a) => (
            <div
              key={a.loginid}
              className="flex items-center justify-between gap-2 p-2 rounded-lg border border-white/10 bg-black/40 text-xs font-mono"
            >
              <div className="min-w-0">
                <span className="text-white font-bold truncate">{a.loginid}</span>{" "}
                <span
                  className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${
                    a.account_type === "demo"
                      ? "bg-sky-500/10 text-sky-400"
                      : "bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  {a.account_type}
                </span>{" "}
                {a.category === "wallet" && (
                  <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">
                    wallet
                  </span>
                )}{" "}
                {a.currency && <span className="text-zinc-500">{a.currency}</span>}
              </div>
              {/* demo/live is chosen with the sidebar toggle, not per-account
                  defaults. Wallet accounts hold balance but are never trade
                  targets; status reflects real adapter liveness. */}
              <span
                className={`text-[10px] whitespace-nowrap ${
                  a.category === "wallet"
                    ? "text-amber-400"
                    : a.adapter_live
                      ? "text-emerald-400"
                      : "text-zinc-500"
                }`}
              >
                {a.category === "wallet"
                  ? "● balance only"
                  : a.adapter_live
                    ? "● connected"
                    : "○ reconnecting"}
              </span>
            </div>
          ))}
        </div>
      )}

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

      <div className="flex flex-wrap gap-2">
        <button
          onClick={connectOAuth}
          className="px-5 py-2.5 bg-white text-black font-mono font-bold text-xs rounded-lg hover:bg-white/90 transition"
        >
          {accounts.length > 0
            ? "Connect another Deriv account"
            : "Find & connect Deriv accounts"}
        </button>
      </div>

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
