import React, { useEffect, useState } from "react";
import { ClipboardList, RefreshCw, AlertTriangle } from "lucide-react";
import apiClient from "../api/apiClient";

// Trade Audit (competitive build item B2): the lifecycle trail behind
// the transactions table -- SL/TP watchdog monitors (close attempts,
// last broker error, refusal reasons) plus the position event feed
// (opened / tp_hit / sl_hit / closed / close_failed) and 30-day
// aggregates. Same-page companion to History; data is scoped to the
// caller by the backend (require_verified_user_id).

interface AuditEvent {
  id?: number | null;
  kind?: string | null;
  symbol?: string | null;
  side?: string | null;
  contract_id?: string | null;
  event_price?: number | null;
  entry_price?: number | null;
  stake?: number | null;
  pnl?: number | null;
  detail?: string | null;
  created_at?: string | null;
}

interface AuditMonitor {
  id?: string | null;
  contract_id?: string | null;
  symbol?: string | null;
  side?: string | null;
  status?: string | null;
  entry_price?: number | null;
  sl?: number | null;
  tp?: number | null;
  pnl?: number | null;
  close_reason?: string | null;
  close_attempts?: number | null;
  last_close_error?: string | null;
  created_at?: string | null;
  closed_at?: string | null;
}

const KIND_CLS: Record<string, string> = {
  opened: "border-sky-500/40 bg-sky-500/10 text-sky-300",
  tp_hit: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  sl_hit: "border-rose-500/40 bg-rose-500/10 text-rose-300",
  closed: "border-zinc-500/40 bg-zinc-500/10 text-zinc-300",
  close_failed: "border-amber-500/40 bg-amber-500/10 text-amber-300",
  test: "border-white/15 bg-white/5 text-zinc-400",
};

const statusCls = (s?: string | null) => {
  const v = (s || "").toUpperCase();
  if (v === "ACTIVE") return "border-sky-500/40 bg-sky-500/10 text-sky-300";
  if (v.startsWith("CLOSED")) return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (v === "EXPIRED") return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  if (v === "REMOVED") return "border-zinc-500/40 bg-zinc-500/10 text-zinc-400";
  return "border-white/15 bg-white/5 text-zinc-400";
};

const fmtWhen = (iso?: string | null) => {
  if (!iso) return "—";
  const t = new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);
  return Number.isNaN(t.getTime()) ? "—" : t.toLocaleString();
};

const fmtNum = (v?: number | null, d = 2) =>
  v === undefined || v === null || Number.isNaN(Number(v))
    ? "—"
    : Number(v).toFixed(d);

const fmtPnl = (pnl?: number | null) => {
  if (pnl == null) return "—";
  const s = `${Math.abs(pnl).toFixed(2)}`;
  return `${pnl >= 0 ? "+" : "-"}$${s}`;
};

export default function TradeAudit() {
  const [summary, setSummary] = useState<any>(null);
  const [monitors, setMonitors] = useState<AuditMonitor[]>([]);
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = async (manual = false) => {
    if (manual) setLoading(true);
    const [s, m, t] = await Promise.allSettled([
      apiClient.get("/api/v1/audit/summary?days=30"),
      apiClient.get("/api/v1/audit/monitors"),
      apiClient.get("/api/v1/audit/timeline?limit=50"),
    ]);
    const firstErr = [s, m, t].find((r) => r.status === "rejected") as
      PromiseRejectedResult | undefined;
    if (s.status === "fulfilled") setSummary(s.value?.data?.data ?? null);
    if (m.status === "fulfilled") setMonitors(m.value?.data?.data?.monitors ?? []);
    if (t.status === "fulfilled") setItems(t.value?.data?.data?.items ?? []);
    if (firstErr) {
      const e: any = firstErr.reason;
      const detail = e?.response?.data?.detail;
      setErr(
        e?.response?.status === 401
          ? "Sign in to see your trade audit."
          : typeof detail === "string"
            ? detail
            : e?.message || "Could not load trade audit."
      );
    } else {
      setErr(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mon = summary?.monitors ?? {};
  const ev = summary?.events ?? {};
  const cards: Array<{ label: string; value: string; sub: string }> = [
    {
      label: "Realized P&L (30d)",
      value: summary?.pnl_realized == null ? "—" : fmtPnl(summary.pnl_realized),
      sub: `${summary?.pnl_events ?? 0} settled events`,
    },
    {
      label: "Position events",
      value: String((ev.opened ?? 0) + (ev.closed ?? 0) + (ev.close_failed ?? 0)),
      sub: `${ev.opened ?? 0} opened · ${ev.closed ?? 0} closed`,
    },
    {
      label: "Close failures",
      value: String(ev.close_failed ?? 0),
      sub: `${mon.close_attempts_total ?? 0} close attempts`,
    },
    {
      label: "Monitors",
      value: String(mon.active ?? 0),
      sub: `${mon.closed ?? 0} closed · ${mon.expired ?? 0} expired`,
    },
    {
      label: "Worst close run",
      value: String(mon.close_attempts_max ?? 0),
      sub: `${mon.with_last_close_error ?? 0} with broker error`,
    },
  ];

  return (
    <section className="pt-4 border-t border-white/10 space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-serif italic text-white flex items-center">
            <ClipboardList className="w-5 h-5 mr-2 text-white/70" />
            Trade Audit
          </h2>
          <p className="text-white/40 text-[11px] mt-1 font-light">
            What actually happened to every position: SL/TP watchdog attempts, close
            outcomes, broker refusal reasons and the full lifecycle event trail.
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-neutral-200 transition disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {err && (
        <div className="p-3 rounded border border-amber-500/20 bg-amber-500/5 text-amber-400 text-xs font-mono flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {err}
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
          {cards.map((c) => (
            <div key={c.label} className="border border-white/10 rounded-xl bg-black/30 p-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                {c.label}
              </div>
              <div className="text-xl font-black text-white mt-1 tracking-tight">
                {c.value}
              </div>
              <div className="text-[10px] font-mono text-zinc-500 mt-1">{c.sub}</div>
            </div>
          ))}
        </div>
      )}

      {/* SL/TP monitors: attempts, refusal reasons, last broker error */}
      <div className="border border-white/10 rounded-xl overflow-hidden">
        <div className="px-4 py-2.5 bg-white/5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
          SL/TP monitors ({monitors.length})
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono">
            <thead>
              <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[9px]">
                <th className="py-2 px-3">Symbol</th>
                <th className="py-2 px-3">Side</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3 text-right">Entry</th>
                <th className="py-2 px-3 text-right">SL / TP</th>
                <th className="py-2 px-3 text-right">P&L</th>
                <th className="py-2 px-3 text-right">Attempts</th>
                <th className="py-2 px-3">Outcome / refusal</th>
                <th className="py-2 px-3">Closed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading && monitors.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-6 text-center text-[11px] text-zinc-500">
                    <RefreshCw className="w-3.5 h-3.5 inline animate-spin text-rose-500 mr-2" />
                    LOADING AUDIT...
                  </td>
                </tr>
              )}
              {!loading && monitors.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-6 text-center text-[11px] text-zinc-600">
                    No SL/TP monitors yet -- watchdog state appears once positions
                    with a stop-loss or take-profit are armed.
                  </td>
                </tr>
              )}
              {monitors.map((m) => (
                <tr key={m.id || m.contract_id} className="hover:bg-white/[0.03]">
                  <td className="py-2 px-3 text-xs text-white font-bold">
                    {m.symbol || "—"}
                    <div className="text-[9px] text-zinc-600 font-normal" title={m.contract_id || ""}>
                      {m.contract_id || ""}
                    </div>
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400">{m.side || "—"}</td>
                  <td className="py-2 px-3">
                    <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded-full border ${statusCls(m.status)}`}>
                      {m.status || "—"}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400 text-right">
                    {fmtNum(m.entry_price)}
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-500 text-right">
                    {fmtNum(m.sl)} / {fmtNum(m.tp)}
                  </td>
                  <td
                    className={`py-2 px-3 text-[10px] font-bold text-right ${
                      m.pnl == null ? "text-zinc-500" : m.pnl >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {m.pnl == null ? "—" : fmtPnl(m.pnl)}
                  </td>
                  <td className="py-2 px-3 text-[10px] text-right">
                    <span
                      className={
                        (m.close_attempts ?? 0) >= 3
                          ? "text-amber-400 font-bold"
                          : (m.close_attempts ?? 0) > 0
                            ? "text-zinc-300"
                            : "text-zinc-600"
                      }
                      title={m.last_close_error || undefined}
                    >
                      {m.close_attempts ?? 0}
                    </span>
                  </td>
                  <td
                    className="py-2 px-3 text-[10px] text-zinc-500 max-w-[280px] truncate"
                    title={m.last_close_error || m.close_reason || ""}
                  >
                    {m.last_close_error
                      ? `ERR: ${m.last_close_error}`
                      : m.close_reason || "—"}
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-600 whitespace-nowrap">
                    {fmtWhen(m.closed_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Lifecycle event trail */}
      <div className="border border-white/10 rounded-xl overflow-hidden">
        <div className="px-4 py-2.5 bg-white/5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
          Lifecycle events ({items.length})
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono">
            <thead>
              <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[9px]">
                <th className="py-2 px-3">When</th>
                <th className="py-2 px-3">Event</th>
                <th className="py-2 px-3">Symbol</th>
                <th className="py-2 px-3">Side</th>
                <th className="py-2 px-3 text-right">Entry</th>
                <th className="py-2 px-3 text-right">Event px</th>
                <th className="py-2 px-3 text-right">Stake</th>
                <th className="py-2 px-3 text-right">P&L</th>
                <th className="py-2 px-3">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-6 text-center text-[11px] text-zinc-600">
                    No position lifecycle events recorded yet.
                  </td>
                </tr>
              )}
              {items.map((e) => (
                <tr key={e.id ?? `${e.created_at}-${e.kind}`} className="hover:bg-white/[0.03]">
                  <td className="py-2 px-3 text-[10px] text-zinc-500 whitespace-nowrap">
                    {fmtWhen(e.created_at)}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded-full border ${KIND_CLS[e.kind || ""] || KIND_CLS.test}`}>
                      {(e.kind || "—").replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-xs text-white font-bold">{e.symbol || "—"}</td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400">{e.side || "—"}</td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400 text-right">
                    {fmtNum(e.entry_price)}
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400 text-right">
                    {fmtNum(e.event_price)}
                  </td>
                  <td className="py-2 px-3 text-[10px] text-zinc-400 text-right">
                    {fmtNum(e.stake)}
                  </td>
                  <td
                    className={`py-2 px-3 text-[10px] font-bold text-right ${
                      e.pnl == null ? "text-zinc-500" : e.pnl >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {e.pnl == null ? "—" : fmtPnl(e.pnl)}
                  </td>
                  <td
                    className="py-2 px-3 text-[10px] text-zinc-500 max-w-[320px] truncate"
                    title={e.detail || ""}
                  >
                    {e.detail || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
