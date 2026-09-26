import React, { useState, useEffect } from "react";
import { History as HistoryIcon, Search, RefreshCw, AlertTriangle, BarChart2, Camera, Trash2, Eye } from "lucide-react";
import Analytics from "./Analytics";
import apiClient from "../api/apiClient";

interface Transaction {
  id: string;
  date: string;
  type: string;
  symbol: string;
  contract_type?: string;
  price: number;
  payout?: number;
  status: string;
}

export default function History({ demoMode }: { demoMode?: boolean }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/history/transactions?limit=50&days=30");
      const data = await res.json();
      if (res.ok) {
        setTransactions(data.transactions || []);
        setNote(data.note || null);
        setError(null);
      } else {
        setError(data.detail || "Could not load transaction history.");
      }
    } catch (err: any) {
      setError(err.message || "Could not load transaction history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
    const interval = setInterval(fetchTransactions, 15000);
    return () => clearInterval(interval);
  }, []);

  const filteredRecords = transactions.filter((rec) => {
    const term = searchTerm.toLowerCase();
    return (
      (rec.id || "").toLowerCase().includes(term) ||
      (rec.symbol || "").toLowerCase().includes(term) ||
      (rec.type || "").toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <HistoryIcon className="w-8 h-8 mr-3 text-white/70" />
            Position &amp; Activity History
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            Real open positions from your live Deriv connection.
          </p>
        </div>
        <button
          onClick={fetchTransactions}
          className="flex items-center space-x-2 px-3.5 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-neutral-200 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {note && (
        <div className="p-3 rounded border border-amber-500/20 bg-amber-500/5 text-amber-400 text-xs font-mono flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {note}
        </div>
      )}
      {error && (
        <div className="p-3 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{error}</div>
      )}

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
        <input
          type="text"
          placeholder="Search by ID, symbol, type..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-neutral-950 border border-white/10 rounded pl-9 pr-4 py-2 text-xs text-white placeholder-stone-600 focus:outline-none focus:border-white/30 font-mono"
        />
      </div>

      <div className="metric-card rounded border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-white/10 bg-neutral-900/40 text-gray-500 text-[10px] uppercase font-bold tracking-wider">
                <th className="p-4">Contract ID</th>
                <th className="p-4">Symbol</th>
                <th className="p-4">Type</th>
                <th className="p-4">Stake</th>
                <th className="p-4">Payout</th>
                <th className="p-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-stone-500">Loading...</td>
                </tr>
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-stone-500">No open positions.</td>
                </tr>
              ) : (
                filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-white/2 transition">
                    <td className="p-4 text-white font-semibold">{rec.id}</td>
                    <td className="p-4 text-zinc-300">{rec.symbol}</td>
                    <td className="p-4 text-stone-400">{rec.contract_type || rec.type}</td>
                    <td className="p-4 text-gray-400">{rec.price}</td>
                    <td className="p-4 text-gray-400">{rec.payout ?? "—"}</td>
                    <td className="p-4 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                        {rec.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Diagnostics Log now lives here instead of its own sidebar tab. */}
      <div className="pt-4 border-t border-white/10">
        <h2 className="text-lg font-serif italic text-white flex items-center mb-4">
          <BarChart2 className="w-5 h-5 mr-2 text-white/70" />
          Diagnostics Log
        </h2>
        <Analytics demoMode={demoMode} />
      </div>

      <EmotionLog />
    </div>
  );
}

// Emotion check-in log: the user's own analyzed snapshots (state,
// time, trading context, chat excerpt), with on-demand snapshot view
// and per-entry delete. Scoped server-side to the caller -- this
// component only ever sees your own rows.
function EmotionLog() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [snapshot, setSnapshot] = useState<string | null>(null);
  const [snapLoading, setSnapLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const res: any = await apiClient.getEmotionHistory(30);
      const d = res?.data?.data ?? res?.data ?? {};
      setItems(d.checkins || []);
    } catch (e: any) {
      setErr(e?.message || "Could not load emotion log.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const viewSnapshot = async (id: number) => {
    if (openId === id) {
      setOpenId(null);
      setSnapshot(null);
      return;
    }
    setOpenId(id);
    setSnapshot(null);
    setSnapLoading(true);
    try {
      const res: any = await apiClient.getEmotionCheckin(id);
      const d = res?.data?.data?.checkin ?? res?.data?.checkin ?? {};
      setSnapshot(d.image_b64 || null);
    } catch {
      setSnapshot(null);
    } finally {
      setSnapLoading(false);
    }
  };

  const remove = async (id: number) => {
    try {
      await apiClient.deleteEmotionCheckin(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      if (openId === id) {
        setOpenId(null);
        setSnapshot(null);
      }
    } catch (e: any) {
      setErr(e?.message || "Could not delete entry.");
    }
  };

  const fmtTime = (iso: string | null) => {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <div className="pt-4 border-t border-white/10">
      <h2 className="text-lg font-serif italic text-white flex items-center mb-1">
        <Camera className="w-5 h-5 mr-2 text-white/70" />
        Emotion Log
      </h2>
      <p className="text-white/40 text-xs mt-1 mb-4 font-light">
        Your camera check-ins with timestamps, trading context, and what you said. Only you can see these —
        snapshots load on demand and any entry can be deleted. A weekly summary goes to your verified email.
      </p>
      {err && (
        <div className="p-3 mb-3 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{err}</div>
      )}
      {loading ? (
        <p className="text-xs text-zinc-500 font-mono">Loading…</p>
      ) : items.length === 0 ? (
        <p className="text-xs text-zinc-500 font-mono">No check-ins yet. Turn on camera check-ins in the assistant to start logging.</p>
      ) : (
        <div className="space-y-1.5">
          {items.map((c: any) => (
            <div key={c.id} className="rounded-lg border border-white/10 bg-black/40 p-2.5 text-xs font-mono">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <span className="text-white font-bold">{c.emotional_state || "unclear"}</span>{" "}
                  <span className="text-zinc-500">{fmtTime(c.created_at)}</span>
                  {c.symbol && <span className="text-sky-400 ml-2">{c.symbol}</span>}
                  {!c.usable_frame && <span className="text-amber-400 ml-2">(unclear frame)</span>}
                </div>
                <div className="flex items-center gap-1 whitespace-nowrap">
                  {c.has_snapshot && (
                    <button
                      onClick={() => viewSnapshot(c.id)}
                      title="View snapshot"
                      className="p-1.5 rounded hover:bg-white/10 text-zinc-400 hover:text-white"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={() => remove(c.id)}
                    title="Delete entry"
                    className="p-1.5 rounded hover:bg-white/10 text-zinc-400 hover:text-red-300"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              {c.trading_note && <p className="text-zinc-300 mt-1">{c.trading_note}</p>}
              {(c.context || c.chat_excerpt) && (
                <p className="text-zinc-500 mt-1 text-[11px]">
                  {[c.context, c.chat_excerpt ? `“${c.chat_excerpt}”` : null].filter(Boolean).join(" · ")}
                </p>
              )}
              {openId === c.id && (
                <div className="mt-2">
                  {snapLoading ? (
                    <p className="text-zinc-500 text-[11px]">Loading snapshot…</p>
                  ) : snapshot ? (
                    <img src={snapshot.startsWith("data:") ? snapshot : `data:image/jpeg;base64,${snapshot}`} alt="check-in snapshot" className="max-w-xs rounded border border-white/10" />
                  ) : (
                    <p className="text-zinc-500 text-[11px]">No snapshot stored.</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
