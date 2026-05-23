import React, { useState, useEffect } from "react";
import { History as HistoryIcon, Search, Calendar, FileText, Download, ShieldAlert, ArrowUpRight } from "lucide-react";
import apiClient from "../api/apiClient";
import { DEMO_HISTORY_RECORDS } from "../data/demoMocks";

interface Record {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: "Success" | "Flagged" | "Exception";
  executionTime: string;
  node: string;
}

export default function History({ demoMode }: { demoMode?: boolean }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [records, setRecords] = useState<Record[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      if (demoMode) {
        if (!cancelled) {
          setRecords(DEMO_HISTORY_RECORDS);
          setLoading(false);
        }
        return;
      }
      try {
        const resp = await apiClient.get("/api/v1/history-new/activity", { limit: 50 });
        const items = resp?.activities || resp?.data?.activities || [];
        const mapped: Record[] = items.map((item: Record<string, string>) => ({
          id: item.id || item.transaction_id || "—",
          timestamp: item.timestamp || item.date || "",
          agent: item.type || item.agent || "System",
          action: item.description || item.action || item.type || "",
          status: (item.status === "Flagged" || item.status === "Exception"
            ? item.status
            : "Success") as Record["status"],
          executionTime: item.executionTime || item.execution_time || "—",
          node: item.node || "LIVE",
        }));
        if (!cancelled) setRecords(mapped);
      } catch (e) {
        console.error(e);
        if (!cancelled) {
          setRecords([]);
          setError("Connect a broker account to load your audit trail from the backend.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [demoMode]);

  const filteredRecords = records.filter((rec) => {
    const matchesSearch =
      rec.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.agent.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.action.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || rec.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <HistoryIcon className="w-8 h-8 mr-3 text-white/75" />
            History & Audit Trail
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            {demoMode ? "Demo audit log (simulated agent actions)" : "Live execution and compliance audit from your connected accounts"}
          </p>
        </div>
        <button
          type="button"
          className="flex items-center space-x-2 px-4 py-2 bg-white/5 border border-white/10 rounded text-xs font-mono text-white/70 hover:bg-white/10"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export CSV</span>
        </button>
      </div>

      {error && (
        <p className="text-amber-400/90 text-xs font-mono border border-amber-500/30 rounded px-3 py-2">{error}</p>
      )}

      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by ID, agent, action..."
            className="w-full bg-neutral-950 border border-white/10 rounded pl-9 pr-4 py-2 text-xs text-white placeholder-stone-600 focus:outline-none focus:border-white/30 font-mono"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-white/40" />
          {["All", "Success", "Flagged", "Exception"].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded text-[10px] font-mono border ${
                statusFilter === s
                  ? "bg-white/10 border-white/25 text-white"
                  : "border-white/10 text-zinc-500 hover:text-white"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="metric-card rounded border border-white/10 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-white/40 font-mono text-xs">Loading audit records…</div>
        ) : filteredRecords.length === 0 ? (
          <div className="p-8 text-center text-white/40 font-mono text-xs">
            No records yet. {demoMode ? "Demo data unavailable." : "Complete KYC and connect a broker to populate history."}
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredRecords.map((rec) => (
              <div key={rec.id} className="p-4 hover:bg-white/[0.02] transition flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="flex items-start space-x-3 min-w-0">
                  <FileText className="w-4 h-4 text-white/30 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono text-[10px] text-white/50">{rec.id}</span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                          rec.status === "Success"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : rec.status === "Flagged"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </div>
                    <p className="text-xs text-white/80 truncate">{rec.action}</p>
                    <p className="text-[10px] font-mono text-white/40 mt-1">
                      {rec.agent} · {rec.node} · {rec.executionTime}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-[10px] font-mono text-white/40 shrink-0">
                  <span>{rec.timestamp}</span>
                  <ArrowUpRight className="w-3 h-3" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {!demoMode && (
        <div className="flex items-center space-x-2 text-[10px] font-mono text-emerald-500/80">
          <ShieldAlert className="w-3 h-3" />
          <span>Immutable audit chain · Backend /api/v1/history-new</span>
        </div>
      )}
    </div>
  );
}
