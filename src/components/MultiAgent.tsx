import React, { useState, useEffect } from "react";
import {
  Users,
  CheckCircle,
  AlertTriangle,
  Zap,
  TrendingUp,
  Database,
  Coins,
  Cpu,
  Scale,
  Search
} from "lucide-react";
import { Agent } from "../types";

export const MultiAgent: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentsError, setAgentsError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [adkAgents, setAdkAgents] = useState<any[]>([]);
  const [swarmRunning, setSwarmRunning] = useState(false);
  const [swarmResult, setSwarmResult] = useState<any>(null);
  const [swarmError, setSwarmError] = useState<string | null>(null);

  // Fetch Google ADK agents from backend
  useEffect(() => {
    fetch("/api/v1/agents/google-adk")
      .then(r => r.json())
      .then(d => { if (d.success) setAdkAgents(d.agents); })
      .catch(() => {});
  }, []);

  // Dispatch the ADK swarm analysis. NOTE: this hits the Express route in
  // server.ts (POST /api/v1/agents/swarm), not the Python backend -- the
  // contract audit flagged it as a 404 only because it checked the Python
  // OpenAPI. Kept on the Express route; failures are surfaced, not hidden.
  const runSwarmAnalysis = async () => {
    setSwarmRunning(true);
    setSwarmResult(null);
    setSwarmError(null);
    try {
      const r = await fetch("/api/v1/agents/swarm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: "XAUUSD", price: 3320, balance: 50000,
          news: [{ title: "Fed holds rates, gold surges on risk-off sentiment" }],
          riskAppetite: "Aggressive", tradingGoal: "Capital Expansion",
          leverage: 20,
        }),
      });
      if (!r.ok) {
        const detail = await r.json().catch(() => null);
        throw new Error(detail?.detail || detail?.error || `HTTP ${r.status}`);
      }
      const data = await r.json();
      if (!data?.success && !data?.synthesis) {
        throw new Error("Swarm returned an unexpected payload.");
      }
      setSwarmResult(data);
    } catch (e: any) {
      console.warn("Swarm dispatch failed:", e);
      setSwarmError(e?.message || "Swarm dispatch failed.");
    } finally {
      setSwarmRunning(false);
    }
  };

  // Live multi-agent statuses from the FastAPI backend. A 500+ line block
  // of hardcoded showcase agents (REAL_PRIV_AGENTS_BACKUP) plus a random
  // peer-arbitration log generator and a setTimeout C-suite escalation
  // theater used to live here; all removed -- the hub now renders exactly
  // what the orchestrator reports, or an honest empty/error state.
  useEffect(() => {
    let isMounted = true;
    const fetchAgents = async () => {
      try {
        const response = await fetch("/api/v1/agents/status_with_reputation");
        if (!response.ok) {
          throw new Error(`Agent status endpoint returned ${response.status}.`);
        }
        const result = await response.json();
        if (!isMounted) return;
        if (result.success && Array.isArray(result.data?.agents)) {
          const mapped: Agent[] = result.data.agents.map((fa: any, i: number) => {
            const acc = fa.performance?.accuracy;
            const rep = fa.reputation;
            const status = fa.status === "active" ? "active"
              : fa.status === "idle" ? "monitoring"
              : "offline";
            return {
              id: i + 1,
              name: fa.name || fa.id || `Agent ${i + 1}`,
              type: fa.type || "unknown",
              status,
              performance: typeof acc === "number" ? acc : 0,
              reputation: typeof rep === "number" ? Math.round(rep * 100) : 0,
              iconName: "Cpu",
              color: "blue",
              specialty: String(fa.type || "unknown").replace(/_/g, " "),
              decisions: typeof fa.tasks_completed === "number" ? fa.tasks_completed : 0,
              accuracy: typeof acc === "number" ? acc : 0,
              lastAction: fa.last_activity
                ? `Last activity ${fa.last_activity}`
                : "No recorded activity yet.",
            };
          });
          setAgents(mapped);
          setAgentsError(null);
        } else {
          setAgents([]);
          setAgentsError(result?.data?.summary?.system_status === "orchestrator_unavailable"
            ? "Agent orchestrator is not running in this process."
            : "Agent status payload was malformed.");
        }
      } catch (error: any) {
        if (isMounted) {
          setAgents([]);
          setAgentsError(error?.message || "Agent status endpoint unreachable.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Helper styles
  const getBadgeColor = (status: string) => {
    if (status === "active") return "bg-emerald-950/40 text-emerald-400 border-emerald-500/20";
    if (status === "monitoring") return "bg-amber-950/40 text-amber-400 border-amber-500/20";
    return "bg-neutral-900 text-neutral-400 border-neutral-800";
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case "quantitative":
      case "forex":
      case "commodity":
      case "arbitrage":
      case "synthetic_markets":
      case "technical":
        return <TrendingUp className="w-5.5 h-5.5 text-emerald-400" />;
      case "risk":
      case "compliance":
      case "ethical_arbiter":
      case "regulatory_arbiter":
      case "legal":
      case "credit":
        return <Scale className="w-5.5 h-5.5 text-sky-400" />;
      case "execution":
      case "futures":
      case "options":
        return <Zap className="w-5.5 h-5.5 text-amber-400" />;
      case "alternative_data":
      case "news_analysis":
      case "sentiment":
      case "social_media":
      case "research":
      case "political":
      case "fomc":
        return <Database className="w-5.5 h-5.5 text-purple-400" />;
      case "yield_optimizer":
      case "portfolio_manager":
        return <Coins className="w-5.5 h-5.5 text-yellow-400" />;
      case "tax":
      case "audit":
        return <CheckCircle className="w-5.5 h-5.5 text-indigo-400" />;
      case "ai_ops":
      case "core":
      case "ml":
      case "sensory":
        return <Cpu className="w-5.5 h-5.5 text-teal-400" />;
      default:
        return <Users className="w-5.5 h-5.5 text-zinc-400" />;
    }
  };

  // Category Tabs
  const CATEGORIES = [
    { id: "all", label: "All Agents", count: agents.length },
    { id: "execution", label: "Execution & Arbitrage", count: agents.filter(a => ["quantitative", "execution", "forex", "futures", "options", "arbitrage", "commodity", "synthetic_markets", "technical"].includes(a.type)).length },
    { id: "risk", label: "Risk & Compliance", count: agents.filter(a => ["risk", "compliance", "legal", "audit", "ethical_arbiter", "regulatory_arbiter", "credit", "c_suite"].includes(a.type)).length },
    { id: "data", label: "Data & Sentiment", count: agents.filter(a => ["news_analysis", "alternative_data", "sentiment", "sensory", "social_media", "research", "political", "fomc"].includes(a.type)).length },
    { id: "operations", label: "Operations & Yield", count: agents.filter(a => ["tax", "ai_ops", "yield_optimizer", "portfolio_manager", "notification", "contact", "pr", "economic", "ml", "strategist", "core"].includes(a.type)).length }
  ];

  const filteredAgents = agents.filter(agent => {
    if (activeTab === "execution" && !["quantitative", "execution", "forex", "futures", "options", "arbitrage", "commodity", "synthetic_markets", "technical"].includes(agent.type)) return false;
    if (activeTab === "risk" && !["risk", "compliance", "legal", "audit", "ethical_arbiter", "regulatory_arbiter", "credit", "c_suite"].includes(agent.type)) return false;
    if (activeTab === "data" && !["news_analysis", "alternative_data", "sentiment", "sensory", "social_media", "research", "political", "fomc"].includes(agent.type)) return false;
    if (activeTab === "operations" && !["tax", "ai_ops", "yield_optimizer", "portfolio_manager", "notification", "contact", "pr", "economic", "ml", "strategist", "core"].includes(agent.type)) return false;

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return agent.name.toLowerCase().includes(q) || agent.specialty.toLowerCase().includes(q) || agent.type.toLowerCase().includes(q);
    }

    return true;
  });

  const activeCount = agents.filter(a => a.status === "active").length;

  return (
    <div className="space-y-6">
      {/* Head section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-5">
        <div>
          <div className="flex items-center space-x-2 text-[10px] font-mono tracking-widest uppercase">
            <span className={`w-1.5 h-1.5 rounded-full ${loading ? "bg-amber-400 animate-pulse" : agentsError ? "bg-rose-500" : "bg-emerald-400"}`} />
            <span className={loading ? "text-amber-400" : agentsError ? "text-rose-400" : "text-emerald-400"}>
              {loading
                ? "Connecting to agent orchestrator..."
                : agentsError
                  ? "Agent orchestrator unavailable"
                  : `Live orchestrator: ${agents.length} agents (${activeCount} active)`}
            </span>
          </div>
          <h1 className="text-3xl font-serif italic text-white mt-1">Multi-Agent System & Reputations</h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            Live agent registry from the backend orchestrator with on-chain-style reputation scores
          </p>
        </div>
      </div>

      {/* Filter and Search Bar Row */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 bg-neutral-900/30 p-2.5 rounded border border-white/5">
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveTab(cat.id)}
              className={`px-3 py-1.5 rounded text-xs font-mono transition duration-150 flex items-center space-x-1.5 border cursor-pointer ${
                activeTab === cat.id
                  ? "bg-white text-neutral-950 border-white font-semibold shadow"
                  : "bg-white/5 text-zinc-400 border-white/5 hover:bg-white/10 hover:text-white"
              }`}
            >
              <span>{cat.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-sans ${activeTab === cat.id ? "bg-black/10 text-neutral-950" : "bg-white/10 text-white"}`}>
                {cat.count}
              </span>
            </button>
          ))}
        </div>

        <div className="relative max-w-md w-full xl:w-72">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search specialties, actions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 pl-9 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-white/30 font-mono"
          />
        </div>
      </div>

      {/* Agents Card List */}
      {loading ? (
        <div className="p-12 text-center rounded border border-dashed border-white/10 bg-neutral-900/10">
          <p className="text-sm font-serif italic text-white font-normal">Loading live agent registry...</p>
        </div>
      ) : agentsError ? (
        <div className="p-12 text-center rounded border border-dashed border-rose-500/30 bg-rose-950/10">
          <AlertTriangle className="w-8 h-8 text-rose-500/60 mx-auto mb-2" />
          <p className="text-sm font-serif italic text-white font-normal">Agent registry unavailable</p>
          <p className="text-xs text-zinc-500 font-mono mt-1">{agentsError}</p>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="p-12 text-center rounded border border-dashed border-white/10 bg-neutral-900/10">
          <AlertTriangle className="w-8 h-8 text-amber-500/60 mx-auto mb-2" />
          <p className="text-sm font-serif italic text-white font-normal">
            {agents.length === 0
              ? "No agents are currently registered with the orchestrator."
              : "No agents found matching the active parameters"}
          </p>
          <p className="text-xs text-zinc-500 font-mono mt-1">
            {agents.length === 0
              ? "Agents appear here once the backend orchestrator is running."
              : "Try resetting the filter tabs or clear your search"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <div key={agent.id} className="relative group bg-gradient-to-b from-neutral-900/60 to-neutral-950 border border-white/10 rounded-lg p-5 flex flex-col justify-between hover:border-white/20 transition-all duration-300 shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
              {/* Highlight flare for the active status */}
              <div className="absolute top-0 left-12 right-12 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              <div>
                <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2.5">
                  <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded-full border tracking-wide font-medium ${getBadgeColor(agent.status)}`}>
                    ● {agent.status}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500">ID: {agent.id}</span>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="p-2.5 bg-white/5 border border-white/10 rounded-lg shrink-0">
                    {getAgentIcon(agent.type)}
                  </div>
                  <div>
                    <h3 className="text-base font-serif italic text-white flex items-center group-hover:text-amber-400 transition-colors duration-150">
                      {agent.name}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 font-medium tracking-wider uppercase mt-0.5">{agent.type}</p>
                  </div>
                </div>

                <div className="space-y-2 text-xs border-y border-white/5 py-4 my-4 font-mono">
                  <div className="flex justify-between items-start">
                    <span className="text-zinc-500">Specialty</span>
                    <span className="text-zinc-300 font-medium text-right max-w-[170px] leading-snug" title={agent.specialty}>
                      {agent.specialty}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Rep Score</span>
                    <span className="text-emerald-400 font-semibold">{agent.reputation.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Tasks completed</span>
                    <span className="text-white/90">{agent.decisions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Accuracy</span>
                    <span className="text-white/90">
                      {agent.accuracy > 0 ? `${agent.accuracy.toFixed(1)}%` : "not reported"}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <div className="p-3 bg-neutral-950 border border-white/5 rounded text-[10px] font-mono text-zinc-400 leading-relaxed">
                  <span className="text-emerald-400/80 mr-1.5 font-bold">[STATUS]:</span>
                  {agent.lastAction}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Google ADK Agent Swarm Panel */}
      <div className="bg-gradient-to-b from-neutral-900/20 to-neutral-950/40 border border-white/10 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
          <h3 className="text-base font-serif italic text-white flex items-center font-normal">
            <Cpu className="w-4 h-4 mr-2 text-emerald-400" />
            Google ADK Agent Swarm
          </h3>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/20">
            {adkAgents.length > 0 ? `${adkAgents.length} AGENTS LOADED` : "NONE REGISTERED"}
          </span>
        </div>

        {/* ADK Agent cards */}
        {adkAgents.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
            {adkAgents.map(a => (
              <div key={a.id} className="bg-black/30 border border-white/10 rounded p-2 text-[10px] font-mono">
                <p className="text-emerald-400 font-bold truncate">{a.name}</p>
                <p className="text-zinc-500 uppercase tracking-wide">{a.category}</p>
                <p className="text-zinc-400 mt-1 leading-snug truncate" title={a.capability}>{a.capability.slice(0,45)}...</p>
              </div>
            ))}
          </div>
        )}

        {/* Swarm dispatch button */}
        <button
          onClick={runSwarmAnalysis}
          disabled={swarmRunning}
          className="w-full py-2.5 bg-emerald-900/40 hover:bg-emerald-800/50 border border-emerald-500/30 hover:border-emerald-400/50 text-emerald-300 font-mono text-xs rounded-lg transition disabled:opacity-40 flex items-center justify-center gap-2"
        >
          {swarmRunning ? (
            <><span className="animate-spin">⟳</span> Running Swarm Analysis...</>
          ) : (
            <><Cpu className="w-3.5 h-3.5" /> Dispatch Full ADK Swarm Analysis</>
          )}
        </button>

        {/* Swarm result */}
        {swarmError && (
          <div className="bg-rose-950/20 border border-rose-900/40 rounded-lg p-3 font-mono text-xs text-rose-400 mt-4">
            Swarm dispatch failed: {swarmError}
          </div>
        )}
        {swarmResult && (
          <div className="bg-black/40 border border-emerald-500/20 rounded-lg p-4 font-mono text-xs space-y-2 mt-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-2">
              <span className="text-emerald-400 font-bold">SWARM SYNTHESIS</span>
              <span className="text-zinc-500">{swarmResult.successful_agents}/{swarmResult.swarm_size} agents · {swarmResult.execution_time_ms}ms</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-white/5 rounded p-2">
                <p className="text-zinc-500">Final Action</p>
                <p className={`font-bold text-sm ${swarmResult.synthesis?.final_action === 'BUY' ? 'text-emerald-400' : swarmResult.synthesis?.final_action === 'SELL' ? 'text-rose-400' : 'text-amber-400'}`}>
                  {swarmResult.synthesis?.final_action || 'HOLD'}
                </p>
              </div>
              <div className="bg-white/5 rounded p-2">
                <p className="text-zinc-500">Confidence</p>
                <p className="font-bold text-white">{swarmResult.synthesis?.confidence || 0}%</p>
              </div>
              <div className="bg-white/5 rounded p-2">
                <p className="text-zinc-500">Consensus</p>
                <p className="font-bold text-sky-400 capitalize">{swarmResult.synthesis?.consensus_strength || 'weak'}</p>
              </div>
            </div>
            {swarmResult.synthesis?.execution_recommendation && (
              <p className="text-zinc-300 bg-white/5 rounded p-2 leading-relaxed">
                {swarmResult.synthesis.execution_recommendation}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiAgent;
