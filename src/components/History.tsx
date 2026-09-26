import React, { useState, useEffect } from "react";
import { History as HistoryIcon, Search, RefreshCw, AlertTriangle, BarChart2 } from "lucide-react";
import Analytics from "./Analytics";

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
    </div>
  );
}
