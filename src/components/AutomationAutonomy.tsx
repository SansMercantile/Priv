import React, { useState, useEffect } from "react";
import { 
  Terminal, 
  Play, 
  RotateCcw, 
  Activity, 
  CheckCircle,
  FileCheck,
  TrendingUp,
  Sliders,
  AlertOctagon
} from "lucide-react";
import { AutomationModule, AutomationHistory } from "../types";

export const AutomationAutonomy: React.FC = () => {
  const [totalCompleted, setTotalCompleted] = useState(142478);
  const [successRate, setSuccessRate] = useState(99.98);
  const [checkInterval, setCheckInterval] = useState(30); // minutes
  const [executingTaskId, setExecutingTaskId] = useState<number | null>(null);

  const [modules, setModules] = useState<AutomationModule[]>([
    {
      id: 1,
      name: "Accounts Payable Routing Node",
      description: "Auto-routes corporate supplier expenditures against matching invoice slips.",
      status: "active",
      tasksCompleted: 4212,
      efficiency: 99.4,
      iconName: "FileCheck",
      color: "green",
      features: ["Invoice line audits", "Duplication vetting", "Instant liquidity allocation"]
    },
    {
      id: 2,
      name: "Sovereign SARS File Gateway",
      description: "Piles statutory SA tax filing documents and syncs directly with GRA/SARS portals.",
      status: "active",
      tasksCompleted: 104,
      efficiency: 98.9,
      iconName: "Terminal",
      color: "blue",
      features: ["GRA automatic clearances", "Sovereign file compiling", "e-Filing receipts registry"]
    },
    {
      id: 3,
      name: "Decentralized Liquidity Refresher",
      description: "Sweeps excess cash from checking buffers into low-variability yielding bonds.",
      status: "monitoring",
      tasksCompleted: 88,
      efficiency: 99.2,
      iconName: "TrendingUp",
      color: "purple",
      features: ["Treasury rebalancing", "Vol threshold shields", "Arbitrage margin payouts"]
    }
  ]);

  const [history, setHistory] = useState<AutomationHistory[]>([]);

  // Periodically generate automation events
  useEffect(() => {
    const baseHistory: AutomationHistory[] = [
      { id: 1, task: "Rebalanced liquidity reserve: Swept $4,500 into yields", module: "Decentralized Liquidity Refresher", duration: 0.12, status: "completed", timestamp: Date.now() - 320000 },
      { id: 2, task: "Audited AP invoice #89341 - cleared $24,800 to suppliers", module: "Accounts Payable Routing Node", duration: 0.05, status: "completed", timestamp: Date.now() - 600000 },
      { id: 3, task: "Compiled GRA provisional corporate clearance certificate", module: "Sovereign SARS File Gateway", duration: 0.42, status: "completed", timestamp: Date.now() - 950000 }
    ];
    setHistory(baseHistory);

    const timer = setInterval(() => {
      // Periodic automatic tasks
      setTotalCompleted(prev => prev + 1);
      
      const randomMod = modules[Math.floor(Math.random() * modules.length)];
      const templates = [
        "Swept excess yield margins to secure corporate checking buffer",
        "Audited recurring subatomic invoice clearance schemas",
        "Completed blockchain proof storage validation on GRA endpoints"
      ];

      const nextTask: AutomationHistory = {
        id: Date.now(),
        task: templates[Math.floor(Math.random() * templates.length)],
        module: randomMod.name,
        duration: parseFloat((Math.random() * 0.3 + 0.02).toFixed(2)),
        status: "completed",
        timestamp: Date.now()
      };

      setHistory(prev => [nextTask, ...prev.slice(0, 5)]);
    }, 12000);

    return () => clearInterval(timer);
  }, [modules]);

  // Execute manual simulation event
  const simulateTask = (moduleId: number) => {
    setExecutingTaskId(moduleId);
    
    setTimeout(() => {
      const selected = modules.find(m => m.id === moduleId);
      if (!selected) return;

      const detailLog = moduleId === 1 
        ? "Audited AP clearing: routed $4,500 corporate supplier invoice manually."
        : moduleId === 2
          ? "Manually audited GRA file gate certificates: generated SHA e-filing receipt."
          : "Executed portfolio margin rebalance manually: swept short-term bonds.";

      const nextHist: AutomationHistory = {
        id: Date.now(),
        task: detailLog,
        module: selected.name,
        duration: 0.04,
        status: "completed",
        timestamp: Date.now()
      };

      setHistory(prev => [nextHist, ...prev.slice(0, 5)]);
      setTotalCompleted(prev => prev + 1);
      
      // Level metrics increment
      setModules(prev => 
        prev.map(m => m.id === moduleId ? { ...m, tasksCompleted: m.tasksCompleted + 1 } : m)
      );

      setExecutingTaskId(null);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* Head */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Automation Suite</h1>
          <p className="text-white/40 text-[11px] mt-1 font-light font-sans">Autonomous Accounts Payable (AP) and dynamic corporate treasury rebalancing engines</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs">
          <CheckCircle className="w-3.5 h-3.5 text-white/50" />
          <span className="text-white/60 font-medium">SCHEDULERS: ACTIVE (100%)</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="metric-card rounded p-5 border-white/10">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">TOTAL CONCLUDED CONSTRAINTS</div>
          <div className="text-3xl font-light text-white">{totalCompleted.toLocaleString()}</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">PROOFS RECORDED IN LEDGER</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">AUTOMATION ACCURACY RATIO</div>
          <div className="text-3xl font-light text-white">{successRate.toFixed(2)}%</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">BREACH RATE: ZERO (0%)</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">AVERTING WORK HOURS / MO</div>
          <div className="text-3xl font-light text-white">420+ hrs</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">SAVINGS MULTIPLIER: 4.2x</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">RUNNING MICRO-VM CLIENTS</div>
          <div className="text-3xl font-light text-white">12 Clusters</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">STRENGTH PARAMETERS: STABLE</div>
        </div>
      </div>

      {/* Main Grid split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Module parameters controller (left colspan: 2) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Terminal className="w-4 h-4 mr-2 text-white/50" />
              Autonomous Active Modules
            </h3>
            <p className="text-xs text-gray-400 mb-6 col-description font-sans">
              Each module monitors business thresholds securely. Execute a manual checkup to force synchronicity or audit transaction flows.
            </p>

            <div className="space-y-4">
              {modules.map((m) => (
                <div key={m.id} className="p-5 bg-neutral-900/40 border border-white/5 rounded flex flex-col md:flex-row justify-between items-start md:items-center gap-6 transition duration-200 hover:border-white/10">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-white/70 animate-pulse" />
                      <h4 className="text-sm font-medium text-white">{m.name}</h4>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed font-sans max-w-md">{m.description}</p>
                    
                    {/* Features list bullet points */}
                    <div className="flex flex-wrap gap-2 pt-1.5">
                      {m.features.map((feat, fIdx) => (
                        <span key={fIdx} className="text-[9px] font-mono text-white/60 bg-white/5 border border-white/10 rounded px-2.5 py-0.5">
                          {feat}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center space-x-6 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 border-white/5 pt-3 md:pt-0">
                    <div className="font-mono text-right text-[9px] space-y-1">
                      <div>
                        <span className="text-gray-500">TASKS:</span> 
                        <span className="text-white font-medium ml-1">{m.tasksCompleted}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">EFFICIENCY:</span> 
                        <span className="text-white/60 ml-1 font-medium">{m.efficiency}%</span>
                      </div>
                    </div>

                    <button
                      onClick={() => simulateTask(m.id)}
                      disabled={executingTaskId === m.id}
                      className="bg-neutral-950 border border-white/15 hover:border-white/30 text-white font-medium text-xs px-4 py-2.5 rounded transition-all flex items-center space-x-2 cursor-pointer"
                    >
                      <Play className="w-3 h-3 block fill-white text-white" />
                      <span>{executingTaskId === m.id ? "CLEARING MODULE..." : "FORCE AUDIT RUN"}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Historic timeline checks */}
        <div className="space-y-6">
          
          {/* Schedulers slider */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Sliders className="w-4 h-4 mr-2 text-white/50" />
              Checkup Sweeper Rate
            </h3>
            <p className="text-xs text-stone-400 mb-6 font-sans leading-relaxed font-light">
              Define the automated sweeps boundary intervals. Slower intervals reduce block gas computations, while faster intervals pre-empt slippage.
            </p>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">SWEEP INTERVAL</span>
                <span className="text-white font-bold">{checkInterval} MINUTES</span>
              </div>
              <input 
                type="range"
                min="5"
                max="120"
                step="5"
                value={checkInterval}
                onChange={(e) => setCheckInterval(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>5 MINS (GAS INTENSE)</span>
                <span>120 MINS (AGGREGATE)</span>
              </div>
            </div>
          </div>

          {/* Historic list */}
          <div className="metric-card rounded p-6 flex flex-col h-[270px] border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Activity className="w-4 h-4 mr-2 text-white/50" />
              Automated Operations Ledger
            </h3>
            
            <div className="flex-1 space-y-3 overflow-y-auto scrollbar-hide">
              {history.map((hist, idx) => (
                <div key={idx} className="p-3 bg-neutral-950 border border-white/5 rounded font-mono text-xs">
                  <div className="flex justify-between text-[9px] text-gray-500 uppercase mb-1">
                    <span className="truncate max-w-[130px]" title={hist.module}>{hist.module}</span>
                    <span>DURATION: {hist.duration}s</span>
                  </div>
                  <div className="text-gray-300 mb-1 leading-snug">{hist.task}</div>
                  <div className="text-[9px] text-white/50 font-bold flex items-center space-x-1 uppercase">
                    <span className="w-1 h-1 bg-white/70 rounded-full inline-block animate-pulse" />
                    <span>STATUS: SUCCESSFUL COMPLETE</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
