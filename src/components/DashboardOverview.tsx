import React, { useState, useEffect, useRef } from "react";
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
  BrainCircuit
} from "lucide-react";
import { MetricCard } from "./MetricCard";
import { ChartDataPoint } from "../types";
import apiClient from "../api/apiClient";
import { DEMO_DASHBOARD_STATS } from "../data/demoMocks";

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


// Main Dashboard Tab View
interface DashboardOverviewProps {
  setActiveSection: (sec: string) => void;
  demoMode?: boolean;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ setActiveSection, demoMode = false }) => {
  const [stats, setStats] = useState({
    totalProfit: 2847392.45,
    dailyReturn: 12.34,
    activeAgents: 12,
    dataPoints: 847392,
    riskScore: 23.5,
    executionSpeed: 0.003
  });

  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;

    const seedChart = () =>
      Array.from({ length: 50 }, (_, i) => ({
        time: Date.now() - (50 - i) * 2000,
        value: 100 + Math.random() * 50 - 25,
        volume: Math.random() * 1000000,
        sentiment: Math.random(),
      }));

    async function bootstrap() {
      if (demoMode) {
        setStats(DEMO_DASHBOARD_STATS);
        setChartData(seedChart());
        interval = setInterval(() => {
          setStats((prev) => ({
            ...prev,
            totalProfit: prev.totalProfit + (Math.random() - 0.5) * 1000,
            dailyReturn: prev.dailyReturn + (Math.random() - 0.5) * 0.15,
            dataPoints: prev.dataPoints + Math.floor(Math.random() * 20),
            riskScore: Math.max(0, Math.min(100, prev.riskScore + (Math.random() - 0.5) * 0.2)),
            executionSpeed: 0.001 + Math.random() * 0.004,
          }));
          setChartData((prev) => {
            const lastVal = prev.length > 0 ? prev[prev.length - 1].value : 100;
            const lastSentiment = prev.length > 0 ? prev[prev.length - 1].sentiment : 0.5;
            const newPoint = {
              time: Date.now(),
              value: lastVal + (Math.random() - 0.5) * 5,
              volume: Math.random() * 1000000,
              sentiment: Math.max(0, Math.min(1, lastSentiment + (Math.random() - 0.5) * 0.1)),
            };
            return [...prev.slice(1), newPoint];
          });
        }, 2000);
        return;
      }

      try {
        const [portfolio, agents, health] = await Promise.all([
          apiClient.getPortfolioPositions(),
          apiClient.getAgentStatus(),
          apiClient.getSystemHealth(),
        ]);
        setStats({
          totalProfit: portfolio.totalValue || 0,
          dailyReturn: portfolio.dailyChangePercent || 0,
          activeAgents: agents.active || 0,
          dataPoints: Math.floor((health.performance || 0) * 10000) || 0,
          riskScore: (health.threats || 0) * 10 + 15,
          executionSpeed: 0.003,
        });
      } catch (e) {
        console.error("Dashboard live metrics failed", e);
      }
      setChartData(seedChart());
    }

    bootstrap();
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [demoMode]);

  return (
    <div className="space-y-6">
      {/* Overview Head */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white">Priv Core Dashboard</h1>
          <p className="text-white/45 text-xs mt-1 mb-1 font-light">
            Real-time autonomous AI execution & diagnostics node
          </p>
          <p className="text-[10px] font-mono tracking-widest text-[#10b981] uppercase font-medium">
            Reimagine &bull; Rebuild &bull; Transcend
          </p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10">
          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-white/60 text-[9px] font-mono tracking-widest uppercase mb-0">Node: Active</span>
        </div>
      </div>

      {/* Metrics Bento Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Profit"
          value={`$${stats.totalProfit.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          change={stats.dailyReturn > 0 ? `+${stats.dailyReturn.toFixed(2)}%` : `${stats.dailyReturn.toFixed(2)}%`}
          icon={DollarSign}
          trend={stats.dailyReturn > 0 ? "up" : "down"}
          color="green"
        />
        <MetricCard
          title="Daily Return"
          value={`${stats.dailyReturn.toFixed(2)}%`}
          change="vs yesterday"
          icon={stats.dailyReturn > 0 ? TrendingUp : TrendingDown}
          trend={stats.dailyReturn > 0 ? "up" : "down"}
          color={stats.dailyReturn > 0 ? "green" : "red"}
        />
        <MetricCard
          title="Active Agents"
          value={`${stats.activeAgents}/12`}
          change="Execution cluster"
          icon={Users}
          trend="stable"
          color="blue"
          onClick={() => setActiveSection("multi-agent")}
        />
        <MetricCard
          title="Data Points"
          value={stats.dataPoints.toLocaleString()}
          change="+2.3K / min"
          icon={Activity}
          trend="up"
          color="purple"
          onClick={() => setActiveSection("data-ingestion")}
        />
        <MetricCard
          title="Risk Score"
          value={`${stats.riskScore.toFixed(1)}/100`}
          change="Safe parameters"
          icon={ShieldCheck}
          trend="stable"
          color="yellow"
          onClick={() => setActiveSection("security")}
        />
        <MetricCard
          title="Execution Spd"
          value={`${stats.executionSpeed.toFixed(3)}s`}
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
