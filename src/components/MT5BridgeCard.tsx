import React, { useCallback, useEffect, useState } from "react";
import { Copy, CheckCircle2, Download, MonitorCog, Unplug } from "lucide-react";
import apiClient from "../api/apiClient";

// Local MT5 bridge card (Connections → Broker Connections). The bridge
// is a small script the trader runs on their own PC: it attaches to
// their installed MT5 terminal and long-polls our backend over HTTPS,
// so CFD Standard executes without any MetaApi cloud account or fee.
// Pairing code -> one-time redeem -> token stored on their machine;
// status below is a live heartbeat from the same channel.

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

  const refresh = useCallback(async () => {
    try {
      const res: any = await apiClient.get("/api/v1/mt5-bridge/status");
      setStatus(res?.data ?? null);
    } catch {
      /* backend offline: card just shows stale state */
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = window.setInterval(refresh, 8000);
    return () => window.clearInterval(t);
  }, [refresh]);

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

  const online = !!status?.online;
  const accounts = status?.accounts ?? [];
  const nonDeriv = accounts.filter(
    (a) => a.server && !a.server.toLowerCase().startsWith("deriv")
  );
  const runCmd = pairing?.run || "python mt5_bridge.py --code XXXXXXXX";

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
    </div>
  );
}
