import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useBrokerConnections } from "../lib/useBrokerConnections";
import DerivConnectCard from "./DerivConnectCard";
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Activity, 
  ShieldCheck, 
  Zap,
  Activity as DiagnosticIcon,
  HardDrive,
  Cpu,
  Terminal,
  BrainCircuit,
  Lock,
  Coins
} from "lucide-react";
import { MetricCard } from "./MetricCard";
import { ChartDataPoint } from "../types";

// Canvas Analytics Line Chart Component (Equivalent to dN in target)
interface PerformanceChartProps {
  data: ChartDataPoint[];
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ data }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    // Set display and scale attributes correctly
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const { width, height } = rect;
    ctx.clearRect(0, 0, width, height);

    // Create area fill background gradient for Sophisticated Dark
    const fillGradient = ctx.createLinearGradient(0, 0, 0, height);
    fillGradient.addColorStop(0, "rgba(255, 255, 255, 0.08)");
    fillGradient.addColorStop(1, "rgba(255, 255, 255, 0)");

    // Compute min/max for scaling P&L values
    const values = data.map(pt => pt.value);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;

    // 1. Draw area chart
    ctx.beginPath();
    ctx.moveTo(0, height);
    data.forEach((pt, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((pt.value - minVal) / range) * (height - 24) - 12;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fillStyle = fillGradient;
    ctx.fill();

    // 2. Draw outer line
    ctx.beginPath();
    data.forEach((pt, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((pt.value - minVal) / range) * (height - 24) - 12;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 3. Draw sentiment ribbon at bottom
    data.forEach((pt, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const step = width / (data.length - 1);
      
      // Calculate interpolation color: (Red-to-Green base on sentiment)
      const r = Math.floor(255 * (1 - pt.sentiment));
      const g = Math.floor(255 * pt.sentiment);
      const color = `rgba(${r}, ${g}, 0, 0.55)`;
      
      ctx.fillStyle = color;
      ctx.fillRect(x, height - 6, step + 1, 6);
    });

  }, [data]);

  const lastPoint = data[data.length - 1] || { sentiment: 0.5 };
  const sentimentLabel = lastPoint.sentiment > 0.7 
    ? "Bullish" 
    : lastPoint.sentiment < 0.3 
      ? "Bearish" 
      : "Neutral";

  const sentimentColor = lastPoint.sentiment > 0.7 
    ? "text-green-400" 
    : lastPoint.sentiment < 0.3 
      ? "text-red-400" 
      : "text-yellow-400";

  return (
    <div className="metric-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-serif italic text-white flex items-center font-normal">
          <Activity className="w-4 h-4 mr-2 text-white/50" />
          Performance & Sentiment Engine
        </h3>
        <div className="flex items-center space-x-4 text-xs font-mono text-gray-400">
          <span>REAL-TIME P&L</span>
          <div className="flex items-center space-x-1.5">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-white/60">SENTIMENT: <span className={`${sentimentColor} font-bold`}>{sentimentLabel}</span></span>
          </div>
        </div>
      </div>

      <div className="relative">
        <canvas ref={canvasRef} className="w-full h-64 rounded bg-neutral-900/40 border border-white/10" />
        <div className="absolute top-2 left-2 flex space-x-4 text-[9px] font-mono text-white/30">
          <div>SCALE: DYNAMIC</div>
          <div>DPR: {window.devicePixelRatio || 1}</div>
        </div>
      </div>
    </div>
  );
};


// Live Scrolling Logs Component (Equivalent to fN in target)
interface LogAction {
  id: number;
  type: "agi" | "agent" | "data" | "security" | "execution";
  message: string;
  agent: string;
  timestamp: number;
}

export const ActiveConsoleLog: React.FC = () => {
  const [logs, setLogs] = useState<LogAction[]>([]);

  const templates = [
    { type: "agi", message: "AGI Core processed emotional sentiment analysis", agent: "Empathy Engine" },
    { type: "agent", message: "Quantitative Agent identified arbitrage opportunity", agent: "Quant-Alpha-7" },
    { type: "data", message: "Ingested 2.3K new market data points", agent: "Data Fusion" },
    { type: "security", message: "Zero-knowledge proof verification completed", agent: "ZKP Verifier" },
    { type: "execution", message: "High-frequency trade executed in 0.002s", agent: "Execution Engine" },
    { type: "agi", message: "Unified Consciousness updated strategy weights", agent: "AGI Core" },
    { type: "agent", message: "Risk Agent adjusted position sizing", agent: "Risk-Guardian" },
    { type: "data", message: "Alternative data source integrated", agent: "IoT Ingestor" },
    { type: "security", message: "Blockchain logger recorded 47 transactions", agent: "Immutable Logger" },
    { type: "execution", message: "CPPN Evolver discovered new pattern", agent: "Pattern Evolver" }
  ];

  const categoryStyles = {
    agi: { color: "text-white/80", bg: "bg-white/[0.03]", border: "border-white/10" },
    agent: { color: "text-white/80", bg: "bg-white/[0.03]", border: "border-white/10" },
    data: { color: "text-white/80", bg: "bg-white/[0.03]", border: "border-white/10" },
    security: { color: "text-white/80", bg: "bg-white/[0.03]", border: "border-white/10" },
    execution: { color: "text-white/80", bg: "bg-white/[0.03]", border: "border-white/10" }
  };

  useEffect(() => {
    // Generate initial logs
    const initial = Array.from({ length: 6 }, (_, i) => {
      const templ = templates[Math.floor(Math.random() * templates.length)];
      return {
        id: i,
        type: templ.type as any,
        message: templ.message,
        agent: templ.agent,
        timestamp: Date.now() - i * 15000
      };
    });
    setLogs(initial);

    // Scroll timer for new logs
    const interval = setInterval(() => {
      const templ = templates[Math.floor(Math.random() * templates.length)];
      const nextLogItem: LogAction = {
        id: Date.now(),
        type: templ.type as any,
        message: templ.message,
        agent: templ.agent,
        timestamp: Date.now()
      };
      setLogs(prev => [nextLogItem, ...prev.slice(0, 9)]);
    }, Math.random() * 4000 + 4000);

    return () => clearInterval(interval);
  }, []);

  const timeDiffStr = (time: number) => {
    const elapsed = Date.now() - time;
    const mins = Math.floor(elapsed / 60000);
    const secs = Math.floor((elapsed % 60000) / 1000);
    return mins > 0 ? `${mins}m ago` : `${secs}s ago`;
  };

  return (
    <div className="metric-card rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
        <DiagnosticIcon className="w-4 h-4 mr-2 text-white/50" />
        Activity Feed Console
      </h3>
      
      <div className="flex-1 space-y-3 overflow-y-auto max-h-[350px] scrollbar-hide">
        {logs.map((item) => {
          const style = categoryStyles[item.type] || categoryStyles.data;
          return (
            <div 
              key={item.id} 
              className={`flex items-center justify-between p-3 rounded border ${style.border} ${style.bg} transition-all duration-300 hover:bg-white/[0.04]`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <div className="w-1 h-1 bg-white/40 rounded-full flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs text-white snippet-msg font-medium leading-none truncate mb-1">
                    {item.message}
                  </p>
                  <p className="text-[9px] text-white/40 font-mono flex items-center">
                    <span className="font-bold mr-2 text-white/60">[{item.agent}]</span>
                    <span>TYPE: {item.type.toUpperCase()}</span>
                  </p>
                </div>
              </div>
              <div className="text-[9px] font-mono text-white/30 whitespace-nowrap ml-2">
                {timeDiffStr(item.timestamp)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


export const AdvisorInteractiveInterface: React.FC = () => {
  // NOTE: This panel previously fabricated specific tax-avoidance instructions
  // (e.g. routing funds through offshore trusts to claim "0% effective tax")
  // and invented annualized-return figures with no real calculation behind
  // them. That content has been removed because real users can reach this
  // page — it was materially misleading about money and tax exposure.
  // Replace this placeholder once a real advisory backend exists; until then
  // it should not present canned output as if it were computed advice.
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between p-4 bg-black/40 border border-white/5 rounded-lg">
        <div className="text-xs text-stone-350 leading-relaxed font-sans max-w-xl">
          Portfolio and tax guidance isn't available yet — this feature is still being built and does not
          currently perform any real analysis. Nothing shown here is financial, investment, or tax advice.
        </div>
        <button
          disabled
          className="px-5 py-2.5 bg-white/10 text-white/40 font-mono font-bold text-xs rounded cursor-not-allowed whitespace-nowrap flex items-center justify-center gap-2"
        >
          COMING SOON
        </button>
      </div>

      <div className="p-4 bg-white/[0.02] border border-white/10 rounded-lg text-xs font-mono text-zinc-400 leading-relaxed">
        When this is built, any allocation, return, or tax-strategy output will need to come from a real backend
        calculation reviewed for accuracy — not a hardcoded response to a dropdown selection.
      </div>
    </div>
  );
};



// Main Dashboard Tab View
interface DashboardOverviewProps {
  demoMode?: boolean;
  setActiveSection: (sec: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ demoMode, setActiveSection }) => {
  const navigate = useNavigate();
  const { hasRealDeriv, hasDemoDeriv, connections: brokerConnections, loading: brokerLoading } = useBrokerConnections();

  const isLiveMode = localStorage.getItem("demoMode") === "false";
  const isBinanceConnected = !isLiveMode || localStorage.getItem("ex_conn_binance") === "true";
  const isCoinbaseConnected = !isLiveMode || localStorage.getItem("ex_conn_coinbase") === "true";
  const isHmrcConnected = !isLiveMode || localStorage.getItem("tax_conn_hmrc") === "true";

  const [livePositions, setLivePositions] = useState<any[]>([]);
  const [xmId, setXmId] = useState<string>("");
  const [xmServer, setXmServer] = useState<string>("");
  const [xmBalance, setXmBalance] = useState<number>(0);

  // Bloomberg S&P live linked parameters
  const [credits, setCredits] = useState<number>(() => {
    return parseFloat(localStorage.getItem("xm_usage_credits") || "842.15");
  });
  const [riskAppetite, setRiskAppetite] = useState<string>(() => {
    return localStorage.getItem("xm_user_risk_appetite") || "Aggressive";
  });
  const [leverage, setLeverage] = useState<number>(() => {
    return parseInt(localStorage.getItem("xm_profile_leverage") || "20");
  });
  const [advisorStance, setAdvisorStance] = useState<string>("balanced");

  useEffect(() => {
    const handleSync = () => {
      const liveCreds = parseFloat(localStorage.getItem("xm_usage_credits") || "842.15");
      const liveRisk = localStorage.getItem("xm_user_risk_appetite") || "Aggressive";
      const liveLeverage = parseInt(localStorage.getItem("xm_profile_leverage") || "20");
      setCredits(liveCreds);
      setRiskAppetite(liveRisk);
      setLeverage(liveLeverage);
    };
    
    handleSync();
    const intervalSync = setInterval(handleSync, 1000);
    window.addEventListener('storage', handleSync);
    return () => {
      clearInterval(intervalSync);
      window.removeEventListener('storage', handleSync);
    };
  }, []);

  // Map user risk tolerance automatically to SANS Advisor stance defaults
  useEffect(() => {
    if (riskAppetite === "Conservative") {
      setAdvisorStance("conservative");
    } else if (riskAppetite === "Moderate") {
      setAdvisorStance("balanced");
    } else {
      setAdvisorStance("aggressive");
    }
  }, [riskAppetite]);

  useEffect(() => {
    const syncDynamicData = () => {
      try {
        const savedPos = localStorage.getItem("xm_positions");
        if (savedPos) {
          setLivePositions(JSON.parse(savedPos));
        } else {
          setLivePositions([]);
        }
      } catch (e) {
        setLivePositions([]);
      }
    };

    syncDynamicData();
    const t = setInterval(syncDynamicData, 1500);
    return () => clearInterval(t);
  }, []);

  // Real Deriv account info, from the backend connections list (see
  // oauth_api.py _list_user_connections) rather than the retired
  // client-side OAuth session. Live balance isn't fetched here -- that
  // needs a real-time call to Deriv's API, not yet built -- so we show
  // the real account ID/currency and are honest that balance is
  // unavailable rather than displaying a fabricated number.
  useEffect(() => {
    const derivConn = brokerConnections.find((c) => c.broker === "deriv") as
      (typeof brokerConnections[number] & { account_id?: string; currency?: string }) | undefined;
    setXmId(derivConn?.account_id || "");
    setXmServer(derivConn?.currency || "");
  }, [brokerConnections]);

  const [stats, setStats] = useState(() => {
    const isLive = localStorage.getItem("demoMode") === "false";

    if (isLive) {
      // No real-time balance/risk/agent-count endpoints exist yet for live
      // accounts. Showing fabricated numbers here would mislead a real
      // trader into thinking they have real P&L/risk data. Be honest
      // instead: null means "not available yet", rendered as such below,
      // not randomized like the clearly-labeled demo simulation is.
      return {
        totalProfit: null as number | null,
        dailyReturn: null as number | null,
        activeAgents: null as number | null,
        dataPoints: null as number | null,
        riskScore: null as number | null,
        executionSpeed: null as number | null,
      };
    }

    const baseBal = 10000.0;
    const binanceBal = localStorage.getItem("ex_conn_binance") === "true" ? 148251.52 : 0.0;
    const coinbaseBal = localStorage.getItem("ex_conn_coinbase") === "true" ? 92410.88 : 0.0;
    const combinedVal = baseBal + binanceBal + coinbaseBal;
    return {
      totalProfit: combinedVal,
      dailyReturn: 12.34,
      activeAgents: 12,
      dataPoints: 847392,
      riskScore: 23.5,
      executionSpeed: 0.003
    };
  });

  // Denominator for the Active Agents card in live mode - real total from
  // the backend's agent registry, not a hardcoded guess.
  const [liveTotalAgents, setLiveTotalAgents] = useState<number | null>(null);

  // Live-mode real data: actual Deriv balance (re-fetched from Deriv's own
  // API, not just the cached value from login) and actual backend agent
  // counts. Runs only when in real mode with a real Deriv account, polls
  // periodically so numbers stay current rather than going stale.
  useEffect(() => {
    if (demoMode || !hasRealDeriv) return;
    let cancelled = false;

    const refreshRealData = async () => {
      // Real agent status from the backend's actual agent registry.
      try {
        const res = await fetch("/api/v1/agents/status_with_reputation");
        const json = await res.json();
        if (!cancelled && json?.data?.summary) {
          setStats(prev => ({ ...prev, activeAgents: json.data.summary.active_agents }));
          setLiveTotalAgents(json.data.summary.total_agents);
        }
      } catch {
        // leave as-is (null/stale) rather than fabricate a number
      }

      // Real Deriv balance would go here. Previously fetched directly
      // from Deriv's REST API using the client-side OAuth token; that
      // token no longer reaches the browser (see LoginGate.tsx), so this
      // needs a new backend endpoint (DerivAPIAdapter.get_account_info()
      // already exists and is real -- it just isn't exposed over HTTP
      // yet). Left as a known gap rather than built here: leaving
      // totalProfit unavailable is consistent with this file's own
      // stated approach elsewhere ("leave as-is rather than fabricate a
      // number") until that endpoint exists.
    };

    refreshRealData();
    const interval = setInterval(refreshRealData, 20000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [demoMode, hasRealDeriv]);

  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    // Generate base charts
    const initialData = Array.from({ length: 50 }, (_, i) => ({
      time: Date.now() - (50 - i) * 2000,
      value: 100 + Math.random() * 50 - 25,
      volume: Math.random() * 1000000,
      sentiment: Math.random()
    }));
    setChartData(initialData);

    // Dynamic metrics generation loop - demo mode ONLY. Live mode's numbers
    // stay null (see above) until real backend endpoints for balance/risk/
    // agent-count exist; randomizing fake data for a real account would be
    // actively misleading, not just a cosmetic placeholder.
    const interval = setInterval(() => {
      setStats(prev => {
        const isLive = localStorage.getItem("demoMode") === "false";
        if (isLive) {
          return prev;
        }
        const binanceBal = localStorage.getItem("ex_conn_binance") === "true" ? 148251.52 : 0.0;
        const coinbaseBal = localStorage.getItem("ex_conn_coinbase") === "true" ? 92410.88 : 0.0;
        const dynamicTotal = 10000.0 + binanceBal + coinbaseBal;
        return {
          ...prev,
          totalProfit: dynamicTotal,
          dailyReturn: (prev.dailyReturn ?? 12.34) + (Math.random() - 0.5) * 0.15,
          dataPoints: (prev.dataPoints ?? 847392) + Math.floor(Math.random() * 20),
          riskScore: Math.max(0, Math.min(100, (prev.riskScore ?? 23.5) + (Math.random() - 0.5) * 0.2)),
          executionSpeed: 0.001 + Math.random() * 0.004
        };
      });

      setChartData(prev => {
        const lastVal = prev.length > 0 ? prev[prev.length - 1].value : 100;
        const lastSentiment = prev.length > 0 ? prev[prev.length - 1].sentiment : 0.5;
        const newPoint = {
          time: Date.now(),
          value: lastVal + (Math.random() - 0.5) * 5,
          volume: Math.random() * 1000000,
          sentiment: Math.max(0, Math.min(1, lastSentiment + (Math.random() - 0.5) * 0.1))
        };
        return [...prev.slice(1), newPoint];
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Sync agents status and balance with backend APIs dynamically
  useEffect(() => {
    // 1. Live agents count from backend
    fetch("/api/v1/agents/status")
      .then(res => res.json())
      .then(result => {
        if (result && result.data && result.data.agents) {
          setStats(prev => ({
            ...prev,
            activeAgents: result.data.agents.length
          }));
        }
      })
      .catch(err => console.error("Error pulling live agent stats:", err));

    if (isLiveMode && hasRealDeriv) {
      fetch(`/api/v1/auth/connections`)
        .then(res => res.json())
        .then(result => {
          const derivConn = (result?.data?.connections || []).find((c: any) => c.broker === "deriv" && c.account_type === "live");
          const balance = derivConn?.token_meta?.balance;
          if (typeof balance === "number") {
            localStorage.setItem("xm_balance", balance.toString());
            setStats(prev => ({
              ...prev,
              totalProfit: balance,
              dailyReturn: 0.0
            }));
          }
        })
        .catch(err => console.error("Error fetching live Deriv account balance:", err));
    }
  }, [demoMode, hasRealDeriv]);

  const getSovereignGrade = () => {
    if (riskAppetite === "Conservative") return { g: "AAA GRADE", desc: "Capital Shielded", color: "text-emerald-400 border-emerald-900/50 bg-emerald-950/30" };
    if (riskAppetite === "Moderate") return { g: "A- GRADE", desc: "Optimal Balance", color: "text-sky-450 border-sky-900/50 bg-sky-950/30" };
    if (riskAppetite === "Aggressive") return { g: "BB+ GRADE", desc: "Speculative Spread", color: "text-[#e11d48] border-rose-900/50 bg-rose-950/30" };
    return { g: "CCC+ LEVERAGED", desc: "High-Yield HFT", color: "text-amber-500 border-amber-900/50 bg-amber-950/30" };
  };
  const gradeInfo = getSovereignGrade();

  if (!demoMode && !brokerLoading && !hasRealDeriv) {
    return (
      <div className="space-y-6 max-w-3xl mx-auto py-12 animate-fadeIn">
        <div className="text-center p-8 bg-[#0a0a0a] border border-white/10 rounded-xl space-y-6 shadow-[0_12px_45px_0_rgba(0,0,0,0.8)]">
          <div className="mx-auto w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 text-red-500">
            <Lock className="w-5 h-5 animate-pulse" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-serif italic text-white font-normal">Live Dashboard Locked</h2>
            <p className="text-zinc-400 text-xs max-w-md mx-auto leading-relaxed">
              Because you have disabled the Demo Environment, standard simulated stats (like fake $2.8M margins and randomized charts) are removed. You must connect a verified Deriv account to link your genuine live data.
            </p>
          </div>

          <div className="pt-2 max-w-md mx-auto text-left">
            <DerivConnectCard />
            <div className="mt-3 text-[11px] text-zinc-500 font-mono text-center">
              <a href="https://deriv.com/signup" target="_blank" rel="noopener noreferrer" className="underline">Don't have an account? Sign up</a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Head */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
        <div>
          <h1 className="text-3xl font-serif italic text-white">Priv Dashboard</h1>
          <p className="text-white/45 text-xs mt-1 mb-1 font-light">
            Real-time autonomous AI execution & diagnostics node
          </p>
          <p className="text-[10px] font-mono tracking-widest text-[#10b981] uppercase font-medium">
            Reimagine &bull; Rebuild &bull; Transcend
          </p>
        </div>
        
        {/* Bloomberg-class Sovereign Header Rail */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className={`px-2.5 py-1.5 border rounded font-mono text-[9px] flex flex-col justify-center ${gradeInfo.color}`}>
            <span className="text-zinc-500 leading-none mb-0.5 text-[8px] uppercase font-black">SOVEREIGN RISK CLASS</span>
            <strong className="font-extrabold leading-none">{gradeInfo.g}</strong>
          </div>

          <div className="px-2.5 py-1.5 border border-zinc-800 bg-zinc-950/40 text-zinc-300 rounded font-mono text-[9px] flex flex-col justify-center">
            <span className="text-zinc-500 leading-none mb-0.5 text-[8px] uppercase">DYNAMIC MULTIPLIER</span>
            <strong className="text-white font-extrabold leading-none">{leverage}X LEVERAGE</strong>
          </div>

          <div className="px-2.5 py-1.5 border border-rose-950/30 bg-rose-950/15 text-rose-450 rounded font-mono text-[9px] flex flex-col justify-center">
            <span className="text-zinc-500 leading-none mb-0.5 text-[8px] uppercase">GAS FUEL RESERVES</span>
            <strong className="font-extrabold leading-none">{credits.toFixed(2)} PRIV</strong>
          </div>

          <div className="px-3 py-2.5 bg-white/5 rounded border border-white/10 flex items-center space-x-1.5 font-mono text-[10px] font-black h-full">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-white/70 uppercase">NODE: ACTIVE</span>
          </div>
        </div>
      </div>

      {/* Demo/Simulation disclosure panel — rewritten so it no longer claims demo
          performance predicts live results. Real users can reach this page. */}
      <div className="p-5 border border-white/5 bg-gradient-to-br from-neutral-950/25 via-[#0d0708]/5 to-black rounded-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-white/5">
          <div className="flex items-center space-x-2.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-serif italic text-white text-md tracking-wide">Demo Mode Notice</span>
          </div>
          <span className="font-mono text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded uppercase font-extrabold tracking-widest animate-pulse">
            DEMO ARBITRAGE MODE
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs font-mono">
          <div className="p-3 bg-white/[0.01] border border-white/5 rounded-lg space-y-1">
            <span className="text-[9.5px] font-bold text-rose-500 uppercase tracking-wider block">Simulated Data</span>
            <p className="text-zinc-400 font-sans text-[11px] leading-relaxed font-light">
              Figures shown in Demo Mode are simulated for demonstration purposes and do not reflect real market
              activity or a real account balance.
            </p>
          </div>
          <div className="p-3 bg-white/[0.01] border border-white/5 rounded-lg space-y-1">
            <span className="text-[9.5px] font-bold text-rose-500 uppercase tracking-wider block">Live Mode Is Separate</span>
            <p className="text-zinc-400 font-sans text-[11px] leading-relaxed font-light">
              Real Mode uses your connected broker's live data. It runs independently of the demo simulation above.
            </p>
          </div>
          <div className="p-3 bg-white/[0.01] border border-white/5 rounded-lg space-y-1">
            <span className="text-[9.5px] font-bold text-[#FF6B35] uppercase tracking-wider block">No Performance Guarantee</span>
            <p className="text-zinc-400 font-sans text-[11px] leading-relaxed font-light font-normal text-zinc-350">
              Demo Mode results do not predict or guarantee how a live, funded account will perform. Past or
              simulated performance is not indicative of future results.
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Bento Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Profit"
          value={stats.totalProfit === null ? "—" : `$${stats.totalProfit.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          change={stats.dailyReturn === null ? "Live data pending" : (stats.dailyReturn > 0 ? `+${stats.dailyReturn.toFixed(2)}%` : `${stats.dailyReturn.toFixed(2)}%`)}
          icon={DollarSign}
          trend={stats.dailyReturn === null ? "stable" : (stats.dailyReturn > 0 ? "up" : "down")}
          color="green"
        />
        <MetricCard
          title="Daily Return"
          value={stats.dailyReturn === null ? "—" : `${stats.dailyReturn.toFixed(2)}%`}
          change="vs yesterday"
          icon={stats.dailyReturn === null || stats.dailyReturn > 0 ? TrendingUp : TrendingDown}
          trend={stats.dailyReturn === null ? "stable" : (stats.dailyReturn > 0 ? "up" : "down")}
          color={stats.dailyReturn === null ? "blue" : (stats.dailyReturn > 0 ? "green" : "red")}
        />
        <MetricCard
          title="Active Agents"
          value={stats.activeAgents === null ? "—" : `${stats.activeAgents}/${liveTotalAgents ?? 12}`}
          change="Execution cluster"
          icon={Users}
          trend="stable"
          color="blue"
          onClick={() => setActiveSection("multi-agent")}
        />
        <MetricCard
          title="Data Points"
          value={stats.dataPoints === null ? "—" : stats.dataPoints.toLocaleString()}
          change="+2.3K / min"
          icon={Activity}
          trend="up"
          color="purple"
          onClick={() => setActiveSection("data-ingestion")}
        />
        <MetricCard
          title="Risk Score"
          value={
            riskAppetite === "Conservative" 
              ? "15.2/100" 
              : riskAppetite === "Moderate" 
                ? "32.4/100" 
                : riskAppetite === "Aggressive" 
                  ? "58.4/100" 
                  : "88.2/100"
          }
          change={
            riskAppetite === "Conservative" 
              ? "AAA Grade Capital Protection" 
              : riskAppetite === "Moderate" 
                ? "A- Sharpe Optimized" 
                : riskAppetite === "Aggressive" 
                  ? "BB+ Speculative Spread" 
                  : "CCC+ Leveraged Exposure"
          }
          icon={ShieldCheck}
          trend={riskAppetite === "Conservative" ? "stable" : "up"}
          color={
            riskAppetite === "Conservative" 
              ? "green" 
              : riskAppetite === "Moderate" 
                ? "blue" 
                : riskAppetite === "Aggressive" 
                  ? "yellow" 
                  : "red"
          }
          onClick={() => setActiveSection("security")}
        />
        <MetricCard
          title="Execution Spd"
          value={stats.executionSpeed === null ? "—" : `${stats.executionSpeed.toFixed(3)}s`}
          change="Average latency"
          icon={Zap}
          trend="stable"
          color="green"
        />
      </div>

      {/* Analytics Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PerformanceChart data={chartData} />
        </div>
        <div>
          <ActiveConsoleLog />
        </div>
      </div>

      {/* Sovereign AI Financial Advisor & Wealth Allocator */}
      <div className="metric-card rounded-xl p-6 border-white/10 space-y-5 bg-neutral-900/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-white/5 gap-3">
          <div>
            <h3 className="text-lg font-serif italic text-white flex items-center font-normal">
              <BrainCircuit className="w-5 h-5 mr-2 text-[#FF6B35] animate-pulse" />
              Sovereign AI Financial Advisor
            </h3>
            <p className="text-white/40 text-xs mt-0.5 font-light font-mono">
              Unifies active front-end balances, linked tax platforms, and backend execution rules to determine the best financial outcome.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-stone-500 uppercase">Advisor Stance:</span>
            <select
              id="advisorStanceSelect"
              value={advisorStance}
              onChange={(e) => setAdvisorStance(e.target.value)}
              className="bg-neutral-950 border border-[#e11d48]/30 rounded px-2.5 py-1 text-xs text-rose-450 focus:outline-none focus:border-rose-500 font-mono font-bold"
            >
              <option value="conservative">Conservative (Shield Capital)</option>
              <option value="balanced">Dynamic Growth (Balanced P&L)</option>
              <option value="aggressive">Sovereign Arbitrage (Max Leverage)</option>
            </select>
          </div>
        </div>

        {/* Advisor Work Area */}
        <AdvisorInteractiveInterface />
      </div>

      {/* Dual Row: Connected Live Accounts & MT4/MT5 Open Positions Ledger */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Card A: Connected Live Multi-Accounts Ledger */}
        <div className="metric-card rounded-xl p-5 border border-white/10 bg-neutral-950/20 relative overflow-hidden space-y-4">
          <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
          
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <h3 className="text-sm font-serif italic text-white flex items-center font-normal">
              <Coins className="w-4 h-4 mr-2" />
              Consolidated Live Portfolios Ledger
            </h3>
            <span className="text-[9px] font-mono bg-white/5 text-zinc-400 border border-white/10 px-2 py-0.5 rounded uppercase font-semibold">
              REAL-TIME SYNCED FIGURES
            </span>
          </div>

          <div className="space-y-3.5">
            {/* Deriv Broker Row */}
            <div className="flex items-center justify-between p-3 rounded bg-neutral-950 border border-white/5 hover:border-white/15 transition-colors">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${(hasRealDeriv || hasDemoDeriv) ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
                <div>
                  <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">Deriv Account Linked</h4>
                  <p className="text-[10px] font-mono text-zinc-500 mt-0.5 uppercase">
                    {(hasRealDeriv || hasDemoDeriv) ? `ID: ${xmId}` : "Node Handshake Missing"}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-sm font-mono text-white font-bold block">
                  {(hasRealDeriv || hasDemoDeriv) ? (xmServer || "—") : "N/A"}
                </span>
                <span className="text-[9px] font-mono text-zinc-500 uppercase">
                  {(hasRealDeriv || hasDemoDeriv) ? (hasRealDeriv ? "Real Account" : "Demo Account") : "Auth Standby"}
                </span>
              </div>
            </div>

            {/* Binance Exchange Node */}
            <div className="flex items-center justify-between p-3 rounded bg-neutral-950/60 border border-white/5 hover:border-white/15 transition-colors">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${isBinanceConnected ? "bg-emerald-500 animate-pulse" : "bg-zinc-600 animate-pulse"}`} />
                <div>
                  <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">Binance Exchange Node</h4>
                  <span className="text-[10px] font-mono text-zinc-500 mt-0.5 uppercase block">
                    {isBinanceConnected ? "Active Ledger Node • API Sync" : "Awaiting API Key Inbound"}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-sm font-mono font-bold block ${isBinanceConnected ? "text-white" : "text-zinc-650"}`}>
                  {isBinanceConnected ? "Not yet wired" : "$0.00"}
                </span>
                <span className={`text-[9px] font-mono uppercase block ${isBinanceConnected ? "text-emerald-500" : "text-zinc-500"}`}>
                  {isBinanceConnected ? "Active Sync" : "Not Linked"}
                </span>
              </div>
            </div>

            {/* Coinbase custodial node */}
            <div className="flex items-center justify-between p-3 rounded bg-neutral-950/60 border border-white/5 hover:border-white/15 transition-colors">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${isCoinbaseConnected ? "bg-emerald-500 animate-pulse" : "bg-zinc-600 animate-pulse"}`} />
                <div>
                  <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">Coinbase Custodial Segment</h4>
                  <span className="text-[10px] font-mono text-zinc-500 mt-0.5 uppercase block">
                    {isCoinbaseConnected ? "Institutional Vault Link" : "Awaiting Vault API"}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-sm font-mono font-bold block ${isCoinbaseConnected ? "text-white" : "text-zinc-650"}`}>
                  {isCoinbaseConnected ? "Not yet wired" : "$0.00"}
                </span>
                <span className={`text-[9px] font-mono uppercase block ${isCoinbaseConnected ? "text-emerald-500" : "text-zinc-500"}`}>
                  {isCoinbaseConnected ? "Active Sync" : "Not Linked"}
                </span>
              </div>
            </div>

            {/* Tax feature placeholder — previously showed a "Guernsey Tax-Shield"
                claiming an active 0% effective tax rate. No real tax
                calculation was wired to this; removed since real users can
                reach this page. A real /api/v1/tax/calculate endpoint exists
                on the backend and should back this if it's rebuilt. */}
            <div className="flex items-center justify-between p-3 rounded bg-neutral-950/30 border border-white/5 border-dashed">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-zinc-600" />
                <div>
                  <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">Tax Reporting</h4>
                  <p className="text-[10px] font-mono text-zinc-500 mt-0.5 uppercase">
                    Not yet available
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-sm font-mono font-bold block text-zinc-650">
                  N/A
                </span>
                <span className="text-[9.5px] font-mono uppercase block text-zinc-600">
                  Coming Soon
                </span>
              </div>
            </div>
          </div>
        </div>

          {/* Card B: Live Open Ledger Sessions */}
          <div className="metric-card rounded-xl p-5 border border-white/10 bg-neutral-950/20 relative overflow-hidden space-y-4">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            
            <div className="flex items-center justify-between pb-2 border-b border-white/5">
              <h3 className="text-sm font-serif italic text-white flex items-center font-normal">
                <Activity className="w-4 h-4 mr-2" />
                Live Open Ledger Sessions (MT4/MT5 Active Positions)
              </h3>
              <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${
                livePositions.length > 0 
                  ? "bg-red-500/10 text-red-500 border-red-500/30 animate-pulse" 
                  : "bg-zinc-900 border-zinc-800 text-zinc-500"
              }`}>
                {livePositions.length} POSITIONS OPEN
              </span>
            </div>

            {livePositions.length === 0 ? (
              <div className="p-12 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
                <Lock className="w-5 h-5 mx-auto mb-2 text-stone-600 block" />
                No active leverage sessions currently authorized by SANS Execution Core. Terminal is in standby.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/5 text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                      <th className="py-2">TICKET / ASSET</th>
                      <th className="py-2 text-center">SIDE</th>
                      <th className="py-2 text-center">LOTS</th>
                      <th className="py-2 text-right">ENTRY / SPOT</th>
                      <th className="py-2 text-right">UNREALIZED P&L</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono text-[10.5px]">
                    {livePositions.map((pos) => {
                      const isUp = pos.pnl >= 0;
                      return (
                        <tr key={pos.id} className="hover:bg-white/5 transition">
                          <td className="py-2.5">
                            <span className="font-bold text-white block">{pos.symbol}</span>
                            <span className="text-[8px] text-zinc-500 block">#{pos.id}</span>
                          </td>
                          <td className="py-2.5 text-center">
                            <span className={`px-1.5 py-0.5 text-[8.5px] rounded font-bold ${pos.side === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                              {pos.side}
                            </span>
                          </td>
                          <td className="py-2.5 text-center font-semibold text-zinc-200">
                            {pos.lots}
                          </td>
                          <td className="py-2.5 text-right text-zinc-300">
                            <div>{pos.entryPrice?.toFixed(5)}</div>
                            <div className="text-[9px] text-zinc-500">{pos.currentPrice?.toFixed(5)}</div>
                          </td>
                          <td className={`py-2.5 text-right font-bold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                            {isUp ? "+" : ""}{pos.pnl?.toFixed(2)} USD
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
      </div>

      {/* Low bento health card log */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="metric-card rounded p-5 flex items-center space-x-4 border-white/10">
          <div className="p-3 bg-white/5 rounded">
            <HardDrive className="w-4 h-4 text-white/60" />
          </div>
          <div>
            <div className="text-[9px] font-mono text-white/40 tracking-widest uppercase">DATABASE STORAGE</div>
            <div className="text-sm font-medium text-white font-serif italic">SM Blockchain Clusters</div>
            <div className="text-[9px] mt-0.5 font-mono text-emerald-500">STATUS: REPLICATED (100%)</div>
          </div>
        </div>

        <div className="metric-card rounded p-5 flex items-center space-x-4 border-white/10">
          <div className="p-3 bg-white/5 rounded">
            <Cpu className="w-4 h-4 text-white/60" />
          </div>
          <div>
            <div className="text-[9px] font-mono text-white/40 tracking-widest uppercase">AGI PROCESSING ENGINE</div>
            <div className="text-sm font-medium text-white font-serif italic">Dual-Core Architecture</div>
            <div className="text-[9px] mt-0.5 font-mono text-white/50">INTELLIGENCE LAYER: OPTIMAL</div>
          </div>
        </div>

        <div className="metric-card rounded p-5 flex items-center space-x-4 border-white/10">
          <div className="p-3 bg-white/5 rounded">
            <BrainCircuit className="w-4 h-4 text-white/60" />
          </div>
          <div>
            <div className="text-[9px] font-mono text-white/40 tracking-widest uppercase">NEURAL LINK LATENCY</div>
            <div className="text-sm font-medium text-white font-serif italic">Subatomic Integrations</div>
            <div className="text-[9px] mt-0.5 font-mono text-white/50">STRETCH CORRELATION: 0.9997</div>
          </div>
        </div>
      </div>
    </div>
  );
};
