import React, { useState, useEffect } from "react";
import { AreaChart, Cpu, HardDrive, Zap, RefreshCw, BarChart2, Shield } from "lucide-react";

export default function Analytics({ demoMode }: { demoMode?: boolean }) {
  const [cpuUsage, setCpuUsage] = useState(42.4);
  const [ramUsage, setRamUsage] = useState(8.12);
  const [activeThreads, setActiveThreads] = useState(24);
  const [modelThroughput, setModelThroughput] = useState(1450);

  useEffect(() => {
    const interval = setInterval(() => {
      setCpuUsage(prev => Math.max(20, Math.min(99, prev + (Math.random() - 0.5) * 4)));
      setRamUsage(prev => Math.max(6, Math.min(16, prev + (Math.random() - 0.5) * 0.1)));
      setActiveThreads(prev => Math.max(16, Math.min(64, prev + (Math.random() > 0.5 ? 1 : -1))));
      setModelThroughput(prev => Math.max(800, Math.min(2200, prev + Math.floor((Math.random() - 0.5) * 80))));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <BarChart2 className="w-8 h-8 mr-3 text-white/75" />
            Performance & Diagnostics Analytics
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">Real-time telemetry and resource usage mapping of the sovereign AI nodes</p>
        </div>
        <button className="flex items-center space-x-2 px-3.5 py-2 hover:bg-white/10 text-white border border-white/10 rounded-lg font-mono text-xs transition select-none cursor-pointer">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>FORCE CORE POLL</span>
        </button>
      </div>

      {/* Resource Metrics Bento Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">CPU Computational Load</span>
            <Cpu className="w-4 h-4 text-stone-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">{cpuUsage.toFixed(1)}%</div>
          <p className="text-[10px] text-zinc-500 font-mono mt-2 uppercase tracking-wide">CORES ACTIVE: 12/12</p>
          <div className="w-full bg-white/5 h-1 rounded overflow-hidden mt-3">
            <div className="bg-white h-full transition-all duration-300" style={{ width: `${cpuUsage}%` }} />
          </div>
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">L2 Heap Buffer Usage</span>
            <HardDrive className="w-4 h-4 text-stone-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">{ramUsage.toFixed(2)} GB</div>
          <p className="text-[10px] text-zinc-500 font-mono mt-2 uppercase tracking-wide">ALLOCATION CAPACITY: 16.0 GB</p>
          <div className="w-full bg-white/5 h-1 rounded overflow-hidden mt-3">
            <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${(ramUsage/16)*100}%` }} />
          </div>
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">Autonomous Agent Threads</span>
            <Shield className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-mono font-medium text-emerald-400">{activeThreads}</div>
          <p className="text-[10px] text-zinc-500 font-mono mt-2 uppercase tracking-wide">SECURITY THREAD ISOLATION: LIVE</p>
          <div className="w-full bg-white/5 h-1 rounded overflow-hidden mt-3">
            <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${(activeThreads/64)*100}%` }} />
          </div>
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-900/10">
          <div className="flex items-center justify-between text-neutral-400 mb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider">Model Token Throughput</span>
            <Zap className="w-4 h-4 text-amber-500 animate-pulse" />
          </div>
          <div className="text-3xl font-mono font-medium text-white">{modelThroughput} t/s</div>
          <p className="text-[10px] text-zinc-500 font-mono mt-2 uppercase tracking-wide">AVERAGE LATENCY: 12ms</p>
          <div className="w-full bg-white/5 h-1 rounded overflow-hidden mt-3">
            <div className="bg-amber-500 h-full transition-all duration-300" style={{ width: `${(modelThroughput/2500)*100}%` }} />
          </div>
        </div>
      </div>

      {/* SVG Performance Chart Block */}
      <div className="grid grid-cols-1 gap-6">
        <div className="metric-card p-6 rounded border border-white/10 bg-neutral-900/5">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-serif italic text-white flex items-center font-normal">
                <AreaChart className="w-4 h-4 mr-2" />
                Aggregated High-Frequency Query Volume (24 Hours)
              </h3>
              <p className="text-stone-500 text-xs font-sans">Visual timeline showing aggregate transactions processed by the quantitative arbiters.</p>
            </div>
            <div className="flex space-x-2 text-[10px] font-mono border border-white/5 p-1 rounded">
              <span className="px-2 py-1 bg-white/10 rounded">LIVE INTERNET STREAM</span>
              <span className="px-2 py-1 hover:text-white text-gray-500 transition">HISTORICAL RECAP</span>
            </div>
          </div>

          {/* Inline SVG Chart */}
          <div className="h-64 w-full bg-neutral-950/20 border border-white/5 rounded-lg flex items-end relative overflow-hidden p-2">
            <div className="absolute top-2 left-4 text-[9px] font-mono text-zinc-500">TOKENS PROCESSED PER MINUTE (k)</div>
            <svg viewBox="0 0 1000 240" className="w-full h-full overflow-visible">
              <defs>
                <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ffffff" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#ffffff" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              {/* Grid lines */}
              <line x1="0" y1="60" x2="1000" y2="60" stroke="#ffffff" strokeOpacity="0.05" strokeDasharray="3 3" />
              <line x1="0" y1="120" x2="1000" y2="120" stroke="#ffffff" strokeOpacity="0.05" strokeDasharray="3 3" />
              <line x1="0" y1="180" x2="1000" y2="180" stroke="#ffffff" strokeOpacity="0.05" strokeDasharray="3 3" />
              
              {/* Area path */}
              <path 
                d="M 0,240 
                   L 0,160 
                   Q 80,140 160,180 
                   T 320,110 
                   T 480,140 
                   T 640,60 
                   T 800,120 
                   T 960,40 
                   L 1000,40 
                   L 1000,240 Z" 
                fill="url(#chartGrad)" 
              />
              
              {/* Line path */}
              <path 
                d="M 0,160 
                   Q 80,140 160,180 
                   T 320,110 
                   T 480,140 
                   T 640,60 
                   T 800,120 
                   T 960,40 
                   L 1000,40" 
                fill="none" 
                stroke="#e5e5e5" 
                strokeWidth="2" 
                strokeLinecap="round"
              />

              {/* Glowing anchor dots */}
              <circle cx="640" cy="60" r="4" fill="#ffffff" stroke="#000" strokeWidth="1" className="animate-ping" />
              <circle cx="640" cy="60" r="3.5" fill="#ffffff" />
              <circle cx="960" cy="40" r="4" fill="#ffffff" stroke="#000" strokeWidth="1" className="animate-ping" />
              <circle cx="960" cy="40" r="3.5" fill="#ffffff" />
            </svg>
            <div className="absolute bottom-2 left-3 right-3 flex justify-between font-mono text-[9px] text-zinc-500">
              <span>00:00 UTC</span>
              <span>06:00 UTC</span>
              <span>12:00 UTC</span>
              <span>18:00 UTC</span>
              <span>CURRENT</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
