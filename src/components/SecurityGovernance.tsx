import React, { useState, useEffect } from "react";
import { ShieldCheck, ShieldAlert, RefreshCw, AlertTriangle, Scale, Fingerprint } from "lucide-react";

export const SecurityGovernance: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/v1/governance/surveillance/status");
      const data = await res.json();
      if (res.ok) {
        setStatus(data.data || data);
        setStatusError(null);
      } else {
        setStatusError(data.detail || "Could not reach the governance engine.");
      }
    } catch (err: any) {
      setStatusError(err.message || "Could not reach the governance engine.");
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  // ── Fraud check tool ────────────────────────────────────────────────
  const [txAmount, setTxAmount] = useState<number>(1000);
  const [txUserId, setTxUserId] = useState("");
  const [fraudResult, setFraudResult] = useState<any>(null);
  const [fraudLoading, setFraudLoading] = useState(false);
  const [fraudError, setFraudError] = useState<string | null>(null);

  const runFraudCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setFraudLoading(true);
    setFraudError(null);
    setFraudResult(null);
    try {
      const res = await fetch("/api/v1/governance/fraud/check-transaction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount: txAmount,
          user_id: txUserId || "unspecified",
          timestamp: new Date().toISOString(),
        }),
      });
      const data = await res.json();
      if (res.ok) setFraudResult(data.data || data);
      else setFraudError(data.detail || "Fraud check failed.");
    } catch (err: any) {
      setFraudError(err.message || "Fraud check failed.");
    } finally {
      setFraudLoading(false);
    }
  };

  // ── Ethics assessment tool ──────────────────────────────────────────
  const [scenario, setScenario] = useState("");
  const [ethicsResult, setEthicsResult] = useState<any>(null);
  const [ethicsLoading, setEthicsLoading] = useState(false);
  const [ethicsError, setEthicsError] = useState<string | null>(null);

  const runEthicsAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scenario.trim()) return;
    setEthicsLoading(true);
    setEthicsError(null);
    setEthicsResult(null);
    try {
      const res = await fetch("/api/v1/governance/ethics/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: scenario }),
      });
      const data = await res.json();
      if (res.ok) setEthicsResult(data.data || data);
      else setEthicsError(data.detail || "Ethics assessment failed.");
    } catch (err: any) {
      setEthicsError(err.message || "Ethics assessment failed.");
    } finally {
      setEthicsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Security &amp; Governance</h1>
          <p className="text-white/40 text-xs mt-1 font-light font-sans">
            Live status and analysis tools from Priv's fraud, compliance, and ethics engines.
          </p>
        </div>
        <span
          className={`flex items-center gap-1.5 font-mono text-[10px] uppercase px-3 py-1.5 rounded border ${
            loadingStatus
              ? "bg-zinc-500/5 text-zinc-400 border-zinc-500/30"
              : statusError
              ? "bg-red-500/5 text-red-500 border-red-500/30"
              : "bg-emerald-500/5 text-emerald-400 border-emerald-500/30"
          }`}
        >
          {loadingStatus ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : statusError ? <ShieldAlert className="w-3.5 h-3.5" /> : <ShieldCheck className="w-3.5 h-3.5" />}
          {loadingStatus ? "Checking..." : statusError ? "Offline" : "Live"}
        </span>
      </div>

      <div className="metric-card rounded p-6 border-white/10">
        <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
          <Fingerprint className="w-4 h-4 mr-2 text-white/55" />
          Surveillance Status
        </h3>
        {statusError ? (
          <div className="p-4 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {statusError}
          </div>
        ) : (
          <pre className="p-4 bg-neutral-950 border border-white/5 rounded text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap">
            {status ? JSON.stringify(status, null, 2) : "Loading..."}
          </pre>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <ShieldAlert className="w-4 h-4 mr-2 text-white/55" />
            Fraud Check
          </h3>
          <form onSubmit={runFraudCheck} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Amount</label>
                <input
                  type="number"
                  value={txAmount}
                  onChange={(e) => setTxAmount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">User ID</label>
                <input
                  type="text"
                  value={txUserId}
                  onChange={(e) => setTxUserId(e.target.value)}
                  placeholder="optional"
                  className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={fraudLoading}
              className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2.5 rounded"
            >
              {fraudLoading ? "ANALYZING..." : "RUN FRAUD CHECK"}
            </button>
          </form>
          {fraudError && <p className="mt-3 text-xs font-mono text-red-400">{fraudError}</p>}
          {fraudResult && (
            <pre className="mt-3 p-3 bg-neutral-950 border border-white/5 rounded text-[10px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(fraudResult, null, 2)}
            </pre>
          )}
        </div>

        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <Scale className="w-4 h-4 mr-2 text-white/55" />
            Ethics Assessment
          </h3>
          <form onSubmit={runEthicsAssessment} className="space-y-3">
            <textarea
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="Describe the scenario to assess..."
              rows={4}
              className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono resize-none"
            />
            <button
              type="submit"
              disabled={ethicsLoading || !scenario.trim()}
              className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2.5 rounded"
            >
              {ethicsLoading ? "ASSESSING..." : "RUN ASSESSMENT"}
            </button>
          </form>
          {ethicsError && <p className="mt-3 text-xs font-mono text-red-400">{ethicsError}</p>}
          {ethicsResult && (
            <pre className="mt-3 p-3 bg-neutral-950 border border-white/5 rounded text-[10px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(ethicsResult, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
