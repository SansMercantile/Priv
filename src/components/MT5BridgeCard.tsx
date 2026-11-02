import React, { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Copy, CheckCircle2, Download, MonitorCog, Unplug } from "lucide-react";
import apiClient from "../api/apiClient";

// Local MT5 bridge card (Connections → Broker Connections). The bridge
// is a small script the trader runs on their own PC: it attaches to
// their installed MT5 terminal and long-polls our backend over HTTPS,
// so CFD Standard executes without any MetaApi cloud account or fee.
// Pairing code -> one-time redeem -> token stored on their machine;
// status below is a live heartbeat from the same channel.
//
// Pairing hands out an execution-capable token, so the card is visible
// only to Autonomous subscribers (and admins) -- the same gate the
// backend enforces on POST /api/v1/mt5-bridge/code. When an eligible
// user's bridge is offline, a dismissible prompt pops up once per
// session so pairing can't be missed.

interface BridgeAccount {
  loginid: string;
  server: string;
  currency: string;
  account_type: string;
  adapter_live?: boolean;
}

interface BridgeStatus {
  online: boolean;
  last_seen: string | null;
  accounts: BridgeAccount[];
}

interface PairingCode {
  code: string;
  run: string;
  expires_at: string;
}

export default function MT5BridgeCard() {
  const [status, setStatus] = useState<BridgeStatus | null>(null);
  const [pairing, setPairing] = useState<PairingCode | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState(false);
  // null = still checking; hidden until proven eligible (no flash for
  // free/pro/elite/sovereign tiers, who must never see pairing UI).
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [promptOpen, setPromptOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      let ok = false;
      try {
        // whoami is anon-safe (never 401): admin gets the card outright.
        const res: any = await apiClient.get("/api/v1/admin/whoami");
        ok = !!res?.data?.data?.admin;
      } catch (_) {
        /* stay non-admin */
      }
      if (!ok) {
        try {
          // safeFetchAuthed short-circuits without a network call when
          // signed out, so this never produces a console 401.
          const body: any = await apiClient.getMySubscription();
          const sub =
            body?.subscription ?? (body && typeof body === "object" ? body : null);
          ok = !!sub && sub.tier === "autonomous";
        } catch (_) {
          /* signed out or no subscription -> no pairing UI */
        }
      }
      if (!cancelled) setAllowed(ok);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    try {
      const res: any = await apiClient.get("/api/v1/mt5-bridge/status");
      setStatus(res?.data ?? null);
    } catch {
      /* backend offline: card just shows stale state */
    }
  }, []);

  useEffect(() => {
    if (allowed !== true) return;
    refresh();
    const t = window.setInterval(refresh, 8000);
    return () => window.clearInterval(t);
  }, [refresh, allowed]);

  // Auto prompt: eligible user + bridge offline + not dismissed this
  // session -> pop the pairing prompt once. Comes back after a browser
  // refresh only if they never dismissed it; closes itself when online.
  useEffect(() => {
    if (allowed !== true || !status) return;
    if (status.online) {
      setPromptOpen(false);
      return;
    }
    try {
      if (window.sessionStorage.getItem("priv_pair_prompt_dismissed") !== "1") {
        setPromptOpen(true);
      }
    } catch {
      /* sessionStorage blocked: don't nag */
    }
  }, [allowed, status]);

  const dismissPrompt = () => {
    setPromptOpen(false);
    try {
      window.sessionStorage.setItem("priv_pair_prompt_dismissed", "1");
    } catch {
      /* ignore */
    }
  };

  const generate = async () => {
    setBusy(true);
    setError("");
    try {
      const res: any = await apiClient.post("/api/v1/mt5-bridge/code");
      setPairing(res?.data ?? null);
    } catch (e: any) {
      setError(e?.message || "Could not generate a pairing code.");
    } finally {
      setBusy(false);
    }
  };

  const link = async () => {
    setBusy(true);
    setError("");
    try {
      await apiClient.post("/api/v1/mt5-bridge/link");
      await refresh();
    } catch (e: any) {
      setError(e?.message || "Bridge not reachable yet.");
    } finally {
      setBusy(false);
    }
  };

  const unlink = async () => {
    setBusy(true);
    setError("");
    try {
      await apiClient.post("/api/v1/mt5-bridge/unlink");
      setPairing(null);
      await refresh();
    } catch (e: any) {
      setError(e?.message || "Unlink failed.");
    } finally {
      setBusy(false);
    }
  };

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  const copyInstalled = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCmd(true);
      window.setTimeout(() => setCopiedCmd(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  const online = !!status?.online;
  const accounts = status?.accounts ?? [];
  const nonDeriv = accounts.filter(
    (a) => a.server && !a.server.toLowerCase().startsWith("deriv")
  );
  const runCmd = pairing?.run || "python mt5_bridge.py --code XXXXXXXX";
  const installedCmd = pairing
    ? `"C:\\Program Files\\Priv\\Core\\priv-core.exe" --code ${pairing.code} --pair-only`
    : `"C:\\Program Files\\Priv\\Core\\priv-core.exe" --code XXXXXXXX --pair-only`;

  if (allowed !== true) return null; // not Autonomous/admin: no pairing surface

  return (
    <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              online ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"
            }`}
          />
          <span className="text-zinc-300">
            MT5 Bridge (local) — trade from your own PC, no MetaApi fee
          </span>
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">
          {online ? "online" : "offline"}
        </span>
      </div>

      <p className="text-[11px] text-zinc-500 font-mono leading-relaxed">
        Runs on your Windows PC next to MetaTrader 5. It connects out to us over HTTPS (no
        ports opened, your MT5 password never leaves your machine) and executes CFD Standard
        orders from the terminal here.
      </p>

      {accounts.length > 0 && (
        <div className="space-y-1">
          {accounts.map((a) => (
            <div
              key={a.loginid}
              className="flex items-center justify-between gap-2 px-3 py-1.5 rounded border border-white/10 bg-neutral-950/60 text-[11px] font-mono"
            >
              <span className="text-white">
                {a.loginid} <span className="text-zinc-500">· {a.account_type} · {a.currency || "—"}</span>
              </span>
              <span className={a.adapter_live ? "text-emerald-400" : "text-amber-400"}>
                {a.adapter_live ? "live" : a.adapter_live === false ? "bridge idle" : "—"}
              </span>
            </div>
          ))}
        </div>
      )}

      {nonDeriv.length > 0 && (
        <div className="px-3 py-2 rounded border border-red-500/40 bg-red-500/10 text-[11px] font-mono text-red-300 leading-relaxed">
          MT5 login {nonDeriv[0].loginid} is on “{nonDeriv[0].server}” (non-Deriv).
          The autotrader is blocked for this account regardless of your plan —
          contact an administrator.
        </div>
      )}

      {error && <p className="text-[11px] font-mono text-red-400">{error}</p>}

      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          <a
            href="/api/v1/mt5-bridge/download"
            className="inline-flex items-center gap-1.5 px-4 py-2 border border-white/20 text-white font-mono text-xs rounded-lg hover:bg-white/10 transition"
          >
            <Download className="w-3.5 h-3.5" /> 1. Download mt5_bridge.py
          </a>
          <button
            onClick={generate}
            disabled={busy}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-black font-mono font-bold text-xs rounded-lg hover:bg-white/90 transition disabled:opacity-50"
          >
            <MonitorCog className="w-3.5 h-3.5" /> 2. Generate pairing code
          </button>
        </div>

        {pairing && (
          <div className="p-3 rounded border border-amber-500/30 bg-amber-500/5 space-y-2">
            <p className="text-[11px] font-mono text-amber-300">
              Code <span className="text-white font-bold">{pairing.code}</span> — single-use,
              expires in 10 min. On your PC:
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 truncate px-3 py-2 bg-black border border-white/10 rounded text-xs text-white font-mono">
                pip install MetaTrader5 && {runCmd}
              </code>
              <button
                onClick={() => copy(`pip install MetaTrader5 && ${runCmd}`)}
                className="shrink-0 px-3 py-2 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition flex items-center gap-1.5"
              >
                {copied ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="text-[10px] font-mono text-zinc-500">
              Keep MetaTrader 5 open and logged in once; the script pairs and then stays
              connected. Pairing again from a new PC replaces the old bridge.
            </p>
            <p className="text-[11px] font-mono text-amber-300/80 pt-1">
              Installed the Priv Core app instead? No Python needed:
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 truncate px-3 py-2 bg-black border border-white/10 rounded text-xs text-white font-mono">
                {installedCmd}
              </code>
              <button
                onClick={() => copyInstalled(installedCmd)}
                className="shrink-0 px-3 py-2 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition flex items-center gap-1.5"
              >
                {copiedCmd ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                {copiedCmd ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="text-[10px] font-mono text-zinc-500">
              --pair-only saves the pairing and exits; Priv Core starts at sign-in
              (or open it once from the Start menu to come online now).
            </p>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <button
            onClick={link}
            disabled={busy || !online}
            className="px-4 py-2 border border-white/20 text-white font-mono text-xs rounded-lg hover:bg-white/10 transition disabled:opacity-40"
          >
            {accounts.length ? "Re-link account" : "3. Link MT5 account"}
          </button>
          {(online || accounts.length > 0) && (
            <button
              onClick={unlink}
              disabled={busy}
              className="inline-flex items-center gap-1.5 px-4 py-2 border border-red-500/30 text-red-300 font-mono text-xs rounded-lg hover:bg-red-500/10 transition disabled:opacity-40"
            >
              <Unplug className="w-3.5 h-3.5" /> Unlink
            </button>
          )}
        </div>
        {!online && (
          <p className="text-[10px] font-mono text-zinc-600">
            Link activates once the bridge is running (status flips to online above).
          </p>
        )}
      </div>

      {promptOpen &&
        createPortal(
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
            role="dialog"
            aria-modal="true"
            aria-label="Pair your MT5 bridge"
          >
            <div className="w-full max-w-md rounded-xl border border-white/10 bg-zinc-950 p-5 space-y-3 shadow-2xl">
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-300">
                <MonitorCog className="w-4 h-4 text-rose-400" />
                MT5 Bridge pairing
              </div>
              <h3 className="text-base font-serif italic text-white">
                Your bridge is offline
              </h3>
              <p className="text-[11px] font-mono text-zinc-400 leading-relaxed">
                Pair this account with the bridge on your PC so Priv can read your
                MT5 terminal and execute there. Generate a single-use code (10 min),
                run the one command on your PC, and the status flips to online.
              </p>
              <div className="flex flex-wrap gap-2 pt-1">
                <button
                  onClick={() => {
                    void generate().then(dismissPrompt);
                  }}
                  disabled={busy}
                  className="px-4 py-2 bg-white text-black font-mono font-bold text-xs rounded-lg hover:bg-white/90 transition disabled:opacity-50"
                >
                  Generate pairing code
                </button>
                <button
                  onClick={dismissPrompt}
                  className="px-4 py-2 border border-white/20 text-white font-mono text-xs rounded-lg hover:bg-white/10 transition"
                >
                  Not now
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
}
