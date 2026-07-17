import React, { useState, useEffect } from "react";
import { BarChart2, RefreshCw, AlertTriangle, PieChart, TrendingUp } from "lucide-react";

export default function Analytics({ demoMode }: { demoMode?: boolean }) {
  const [performance, setPerformance] = useState<any>(null);
  const [allocation, setAllocation] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [perfRes, allocRes, riskRes] = await Promise.all([
        fetch("/api/v1/analytics/portfolio/performance"),
        fetch("/api/v1/analytics/portfolio/allocation"),
        fetch("/api/v1/analytics/risk/metrics"),
      ]);
      const [perfData, allocData, riskData] = await Promise.all([perfRes.json(), allocRes.json(), riskRes.json()]);
      setPerformance(perfData);
      setAllocation(allocData);
      setRisk(riskData);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Could not load analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <BarChart2 className="w-8 h-8 mr-3 text-white/75" />
            Portfolio Analytics
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">Real portfolio value and exposure from your live Deriv connection.</p>
        </div>
        <button
          onClick={fetchAll}
          className="flex items-center space-x-2 px-3.5 py-2 hover:bg-white/10 text-white border border-white/10 rounded-lg font-mono text-xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">Current Balance</span>
            <TrendingUp className="w-4 h-4 text-stone-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">
            {performance?.metrics ? `${performance.metrics.currency} ${performance.metrics.current_value?.toLocaleString()}` : "—"}
          </div>
          {performance?.note && <p className="text-[9px] text-amber-500/70 font-mono mt-2">{performance.note}</p>}
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">Total Exposure</span>
            <PieChart className="w-4 h-4 text-stone-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">
            {allocation ? allocation.total_value?.toLocaleString() : "—"}
          </div>
          <p className="text-[10px] text-zinc-500 font-mono mt-2 uppercase tracking-wide">
            {allocation?.by_position?.length ?? 0} open position(s)
          </p>
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">Exposure % of Balance</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">
            {risk?.exposure_pct_of_balance != null ? `${risk.exposure_pct_of_balance}%` : "—"}
          </div>
          {risk?.note && <p className="text-[9px] text-amber-500/70 font-mono mt-2">{risk.note}</p>}
        </div>
      </div>

      <div className="metric-card p-6 rounded border border-white/10 bg-neutral-900/5">
        <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
          <PieChart className="w-4 h-4 mr-2" />
          Allocation by Position
        </h3>
        {!allocation?.by_position || allocation.by_position.length === 0 ? (
          <div className="py-8 text-center font-mono text-[11px] text-zinc-600">No open positions.</div>
        ) : (
          <div className="space-y-2">
            {allocation.by_position.map((p: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 bg-neutral-950 border border-white/5 rounded text-xs font-mono">
                <span className="text-white">
                  {p.symbol} <span className="text-zinc-500">({p.contract_type})</span>
                </span>
                <span className="text-zinc-300">
                  {p.value} <span className="text-zinc-500">({p.percentage}%)</span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
