import React, { useState, useEffect } from "react";
import { Terminal, Play, Activity, CheckCircle, TrendingUp, ShieldAlert, Newspaper, RefreshCw } from "lucide-react";

interface Workflow {
  workflow_id?: string;
  id?: string;
  status?: string;
  [key: string]: any;
}

export const AutomationAutonomy: React.FC = () => {
  const [registry, setRegistry] = useState<any>(null);
  const [registryError, setRegistryError] = useState<string | null>(null);
  const [loadingRegistry, setLoadingRegistry] = useState(true);

  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);

  const [log, setLog] = useState<string[]>([]);
  const pushLog = (msg: string) =>
    setLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50));

  const fetchRegistry = async () => {
    try {
      const res = await fetch("/api/v1/orchestration/registry/status");
      const data = await res.json();
      if (res.ok) {
        setRegistry(data.data || data);
        setRegistryError(null);
      } else {
        setRegistryError(data.detail || "Agent registry unavailable.");
      }
    } catch (err: any) {
      setRegistryError(err.message || "Agent registry unavailable.");
    } finally {
      setLoadingRegistry(false);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const res = await fetch("/api/v1/orchestration/workflows");
      const data = await res.json();
      if (res.ok) {
        const list = (data.data && data.data.workflows) || data.workflows || [];
        setWorkflows(Array.isArray(list) ? list : []);
      }
    } catch {
      /* silent - retried on next poll */
    } finally {
      setLoadingWorkflows(false);
    }
  };

  useEffect(() => {
    fetchRegistry();
    fetchWorkflows();
    const interval = setInterval(() => {
      fetchRegistry();
      fetchWorkflows();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const [tradeSymbols, setTradeSymbols] = useState("R_100, frxEURUSD");
  const [tradeStrategy, setTradeStrategy] = useState("momentum");
  const [startingTrade, setStartingTrade] = useState(false);

  const startTradeWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    setStartingTrade(true);
    try {
      const res = await fetch("/api/v1/orchestration/trade-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: tradeSymbols.split(",").map((s) => s.trim()).filter(Boolean),
          strategy: tradeStrategy,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        pushLog(`Trade workflow started: ${JSON.stringify(data.data)}`);
        fetchWorkflows();
      } else {
        pushLog(`Trade workflow failed: ${data.detail || "Unknown error"}`);
      }
    } catch (err: any) {
      pushLog(`Trade workflow failed: ${err.message || err}`);
    } finally {
      setStartingTrade(false);
    }
  };

  const [riskSymbols, setRiskSymbols] = useState("R_100, frxEURUSD");
  const [riskPortfolioId, setRiskPortfolioId] = useState("priv_deriv");
  const [startingRisk, setStartingRisk] = useState(false);

  const startRiskWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    setStartingRisk(true);
    try {
      const res = await fetch("/api/v1/orchestration/risk-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: riskSymbols.split(",").map((s) => s.trim()).filter(Boolean),
          portfolio_id: riskPortfolioId,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        pushLog(`Risk workflow started: ${JSON.stringify(data.data)}`);
        fetchWorkflows();
      } else {
        pushLog(`Risk workflow failed: ${data.detail || "Unknown error"}`);
      }
    } catch (err: any) {
      pushLog(`Risk workflow failed: ${err.message || err}`);
    } finally {
      setStartingRisk(false);
    }
  };

  const [startingNews, setStartingNews] = useState(false);

  const startNewsWorkflow = async () => {
    setStartingNews(true);
    try {
      const res = await fetch("/api/v1/orchestration/news-workflow", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        pushLog(`News workflow started: ${JSON.stringify(data.data)}`);
        fetchWorkflows();
      } else {
        pushLog(`News workflow failed: ${data.detail || "Unknown error"}`);
      }
    } catch (err: any) {
      pushLog(`News workflow failed: ${err.message || err}`);
    } finally {
      setStartingNews(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Automation &amp; Agent Orchestration</h1>
          <p className="text-white/40 text-xs mt-1 font-light font-sans">
            Live agent registry status and workflow orchestration - trade, risk, and news analysis coordinated across Priv's agent network.
          </p>
        </div>
        <span
          className={`flex items-center gap-1.5 font-mono text-[10px] uppercase px-3 py-1.5 rounded border ${
            loadingRegistry
              ? "bg-zinc-500/5 text-zinc-400 border-zinc-500/30"
              : registryError
              ? "bg-red-500/5 text-red-500 border-red-500/30"
              : "bg-emerald-500/5 text-emerald-400 border-emerald-500/30"
          }`}
        >
          {loadingRegistry ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
          {loadingRegistry ? "Checking..." : registryError ? "Registry Offline" : "Registry Live"}
        </span>
      </div>

      <div className="metric-card rounded p-6 border-white/10">
        <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
          <Terminal className="w-4 h-4 mr-2 text-white/55" />
          Agent Registry Status
        </h3>
        {registryError ? (
          <div className="p-4 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{registryError}</div>
        ) : (
          <pre className="p-4 bg-neutral-950 border border-white/5 rounded text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap">
            {registry ? JSON.stringify(registry, null, 2) : "Loading..."}
          </pre>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="metric-card rounded p-5 border-white/10">
          <h3 className="text-sm font-serif italic text-white mb-3 flex items-center font-normal">
            <TrendingUp className="w-4 h-4 mr-2 text-white/55" />
            Trade Workflow
          </h3>
          <form onSubmit={startTradeWorkflow} className="space-y-2.5">
            <input
              type="text"
              value={tradeSymbols}
              onChange={(e) => setTradeSymbols(e.target.value)}
              placeholder="Symbols, comma-separated"
              className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white font-mono"
            />
            <input
              type="text"
              value={tradeStrategy}
              onChange={(e) => setTradeStrategy(e.target.value)}
              placeholder="Strategy"
              className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white font-mono"
            />
            <button
              type="submit"
              disabled={startingTrade}
              className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2 rounded flex items-center justify-center gap-1.5"
            >
              <Play className="w-3 h-3" /> {startingTrade ? "STARTING..." : "START"}
            </button>
          </form>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <h3 className="text-sm font-serif italic text-white mb-3 flex items-center font-normal">
            <ShieldAlert className="w-4 h-4 mr-2 text-white/55" />
            Risk Workflow
          </h3>
          <form onSubmit={startRiskWorkflow} className="space-y-2.5">
            <input
              type="text"
              value={riskSymbols}
              onChange={(e) => setRiskSymbols(e.target.value)}
              placeholder="Symbols, comma-separated"
              className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white font-mono"
            />
            <input
              type="text"
              value={riskPortfolioId}
              onChange={(e) => setRiskPortfolioId(e.target.value)}
              placeholder="Portfolio ID"
              className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white font-mono"
            />
            <button
              type="submit"
              disabled={startingRisk}
              className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2 rounded flex items-center justify-center gap-1.5"
            >
              <Play className="w-3 h-3" /> {startingRisk ? "STARTING..." : "START"}
            </button>
          </form>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <h3 className="text-sm font-serif italic text-white mb-3 flex items-center font-normal">
            <Newspaper className="w-4 h-4 mr-2 text-white/55" />
            News Workflow
          </h3>
          <p className="text-[10px] text-zinc-500 font-mono mb-3 leading-relaxed">
            Coordinates news-analysis agents across Priv's tracked instruments. No parameters required.
          </p>
          <button
            onClick={startNewsWorkflow}
            disabled={startingNews}
            className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2 rounded flex items-center justify-center gap-1.5"
          >
            <Play className="w-3 h-3" /> {startingNews ? "STARTING..." : "START"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <Activity className="w-4 h-4 mr-2 text-white/55" />
            Active Workflows ({workflows.length})
          </h3>
          {loadingWorkflows ? (
            <div className="py-8 text-center font-mono text-[11px] text-zinc-600">Loading...</div>
          ) : workflows.length === 0 ? (
            <div className="py-8 text-center font-mono text-[11px] text-zinc-600">No active workflows.</div>
          ) : (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {workflows.map((wf, i) => (
                <pre
                  key={wf.workflow_id || wf.id || i}
                  className="p-3 bg-neutral-950 border border-white/5 rounded text-[10px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap"
                >
                  {JSON.stringify(wf, null, 2)}
                </pre>
              ))}
            </div>
          )}
        </div>

        <div className="metric-card rounded p-6 border-white/10">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <Terminal className="w-4 h-4 mr-2 text-white/55" />
            Dispatch Log
          </h3>
          <div className="space-y-1.5 max-h-[300px] overflow-y-auto font-mono text-[10px] text-zinc-400">
            {log.length === 0 ? (
              <div className="text-zinc-600">No workflow activity yet.</div>
            ) : (
              log.map((l, i) => <div key={i}>{l}</div>)
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
