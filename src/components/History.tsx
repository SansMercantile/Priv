import React, { useState } from "react";
import { History as HistoryIcon, Search, Calendar, FileText, Download, ShieldAlert, ArrowUpRight } from "lucide-react";

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

  const records: Record[] = [
    {
      id: "TX-9081",
      timestamp: "2026-05-20 11:42:15",
      agent: "Quant-Alpha-7",
      action: "Autonomous triangular Arbitrage execution on USDT/ZAR layout",
      status: "Success",
      executionTime: "82ms",
      node: "SM-PRV-9"
    },
    {
      id: "TX-9080",
      timestamp: "2026-05-20 11:39:04",
      agent: "Tax-Shield",
      action: "SARS corporate transfer clearance e-Filing certificate authentication",
      status: "Success",
      executionTime: "340ms",
      node: "SM-PRV-9"
    },
    {
      id: "TX-9079",
      timestamp: "2026-05-20 10:14:55",
      agent: "Risk-Guardian",
      action: "Volatility limit threshold verification: spot exposure limited to 2x leverage limit",
      status: "Flagged",
      executionTime: "12ms",
      node: "SM-PRV-9"
    },
    {
      id: "TX-9078",
      timestamp: "2026-05-20 09:51:22",
      agent: "Sentiment-Oracle",
      action: "Ingested FOMC policy speech transcript. Stance coefficient updated to +0.84",
      status: "Success",
      executionTime: "1.24s",
      node: "SM-PRV-9-CLUSTER"
    },
    {
      id: "TX-9077",
      timestamp: "2026-05-20 08:31:10",
      agent: "Execution-Lightning",
      action: "Route block commodity spread order validation (SARS/SADC exemption checked)",
      status: "Success",
      executionTime: "95ms",
      node: "SM-PRV-9"
    },
    {
      id: "TX-9076",
      timestamp: "2026-05-20 07:11:03",
      agent: "Risk-Guardian",
      action: "Exception triggered on alternative commodities arbitrage node line coupling feed",
      status: "Exception",
      executionTime: "22ms",
      node: "SM-PRV-5"
    }
  ];

  const downloadDocument = (type: "audit" | "plan") => {
    let filename = "";
    let content = "";
    
    if (type === "audit") {
      filename = "SANS_PRIV_TRUST_AUDIT_Q2_2026.txt";
      content = `================================================================================
                    SANS MERCANTILE CO. - PRIV CORE TRUST AUDIT
                        QUARTER 2, 2026 OFFICIAL LEDGER
================================================================================
Report ID      : SANS-PRV-AUDIT-449102-Q2
Timestamp      : 2026-05-23 10:00:00 UTC
Status         : COMPLIANT & SECURE
Certifying Body: Gibraltar Sovereign Trust Custodians & Zurich Capital Cleave
Unified Engine : PRIV Neuro-Symbolic Execution Node

--------------------------------------------------------------------------------
I. ASSETS UNDER COMPLIANCE & ESCROW RESERVES
--------------------------------------------------------------------------------
- Traditional Sovereign Metals Pool: $420,500,000.00 USD
- Cryptographic Derivative Lots  : $280,119,450.00 USD
- SADC Regional Trade Liquidity   : $112,000,000.00 USD
- Offshore Discretionary Trust    : $639,464,770.00 USD

TOTAL SECURE COMPLIANT HOLDINGS : $1,452,084,220.00 USD

--------------------------------------------------------------------------------
II. AUTONOMOUS AUDITING TRAIL (NODE CHECKSUM)
--------------------------------------------------------------------------------
[TX-9081] - Triangular Arbitrage USDT/ZAR verification - OK
[TX-9080] - SARS Corporate clearance check - OK
[TX-9079] - Volatility limit Risk-Guardian trigger audit - OK
[TX-9078] - Sentiment-Oracle transcript compilation digest - OK

--------------------------------------------------------------------------------
III. SECURITY SIGN-OFF CHECKSUM
--------------------------------------------------------------------------------
SHA-256 Digest: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Status: ALL SYSTEMS NOMINAL

This document serves as an official compliant certificate of SANS Mercantile Co. SANS-PRIV cryptographic networks remain locked, encrypted, and stable.
================================================================================`;
    } else {
      filename = "PRIV_STRATEGIC_PLAN_2026_2030.txt";
      content = `================================================================================
                  SANS MERCANTILE - PRIV LONG-TERM STRATEGIC PLAN
                            PROJECTED HORIZON 2026 - 2030
================================================================================
Classification: PROPRIETARY SOVEREIGN EXECUTIVE BRIEF
Platform      : PRIV Automated Intelligence Engine

--------------------------------------------------------------------------------
I. THE CORE THESIS: QUANTUM ASSET LEVERAGE
--------------------------------------------------------------------------------
PRIV leverages multi-jurisdictional tax-haven pipelines with high-frequency 
volatility arbitrage models in crypto and traditional equity lots. This plan 
empowers users to automate spot wealth leverage safely by delegating direct API 
execution to SANS' neural-symbolic cluster nodes.

--------------------------------------------------------------------------------
II. STRATEGIC PHASE TIMELINES
--------------------------------------------------------------------------------
Phase 1: Ingress & Harmonization (2026)
  - Seamless local eTax platform logins (HMRC, IRS, SARS) to prevent double-taxation.
  - Integration of client-side exchange channels (Binance API, Coinbase Vaults) to leverage existing capital pools.

Phase 2: Decentralized Triangular Arbitrage Scale (2027)
  - Run high-fidelity multi-agent setups to cross-reference exchange spreads 24/7.
  - Auto-exploit volatility gaps in regional fiat anchors (USDT/ZAR, EUR/CHF).

Phase 3: Sovereign Sovereign Lending Core (2028-2029)
  - Introduce private-debt automated lots for corporate merchants in the SADC zone.
  - Establish self-repaying sovereign loans linked directly to collateral.

Phase 4: Global Wealth Transcendence (2030)
  - Full AGI orchestration targeting 35% compound average growth rates.
  - Absolute algorithmic governance with zero custody risk.

--------------------------------------------------------------------------------
III. EXPECTED GROWTH TARGETS (COMPOUNDS)
--------------------------------------------------------------------------------
- conservative target: +18.5% annualized
- balanced portfolio : +28.2% annualized
- maximum leverage   : +42.0% annualized

================================================================================
Approved by the Board of Directors, Sans Mercantile Trust. SANS PRIV Core active.
================================================================================`;
    }
    
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredRecords = records.filter(rec => {
    const matchesSearch = rec.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          rec.agent.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          rec.action.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || rec.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: Record["status"]) => {
    if (status === "Success") {
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    }
    if (status === "Flagged") {
      return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    }
    return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <HistoryIcon className="w-8 h-8 mr-3 text-white/70" />
            Execution Logs & Audit History
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">Chronological ledger of sovereign node decisions, task executions, and clearances</p>
        </div>
        <button className="flex items-center space-x-2 px-3.5 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-neutral-200 transition select-none cursor-pointer">
          <Download className="w-3.5 h-3.5" />
          <span>EXPORT SYSTEM AUDIT SHEET</span>
        </button>
      </div>

      {/* Strategic Vault & Trust Audits */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Trust Audit Certificate */}
        <div className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-2 py-0.5 rounded font-bold">
                AUDIT CERTIFIED
              </span>
              <span className="text-[10px] text-zinc-500 font-mono">Q2 2026</span>
            </div>
            
            <h3 className="text-lg font-serif italic text-white mt-3 font-medium">SANS Trust Audit Certificate</h3>
            <p className="text-xs text-stone-400 mt-1 leading-relaxed">
              Sovereign verified proof of reserve ledger holding verified capital balances across Gibraltar, Zurich and Singapore vaults. Registered status compliant.
            </p>
          </div>

          <div className="pt-2 border-t border-white/5 flex items-center justify-between gap-3">
            <span className="text-[10px] font-mono text-stone-500 truncate">SANS_PRIV_TRUST_AUDIT_Q2_2026.txt</span>
            <button 
              onClick={() => downloadDocument("audit")}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-neutral-900 hover:bg-neutral-800 border border-white/10 rounded font-mono text-xs text-white hover:border-white/20 transition cursor-pointer select-none whitespace-nowrap"
            >
              <Download className="w-3.5 h-3.5" />
              <span>DOWNLOAD AUDIT</span>
            </button>
          </div>
        </div>

        {/* Card 2: Strategic Wealth Plan */}
        <div className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase bg-sky-500/10 text-sky-400 border border-sky-500/25 px-2 py-0.5 rounded font-bold">
                TACTICAL VISION
              </span>
              <span className="text-[10px] text-zinc-500 font-mono">2026 - 2030</span>
            </div>

            <h3 className="text-lg font-serif italic text-white mt-3 font-medium">SANS Strategic Wealth Plan</h3>
            <p className="text-xs text-stone-400 mt-1 leading-relaxed">
              Deep-neural macro optimization plan targeting synchronized interest gains, automated exchange arbitrage execution, and dual-core asset growth pipelines.
            </p>
          </div>

          <div className="pt-2 border-t border-white/5 flex items-center justify-between gap-3">
            <span className="text-[10px] font-mono text-stone-500 truncate">PRIV_STRATEGIC_PLAN_2026_2030.txt</span>
            <button 
              onClick={() => downloadDocument("plan")}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white text-black hover:bg-stone-200 rounded font-mono text-xs font-semibold transition cursor-pointer select-none whitespace-nowrap"
            >
              <Download className="w-3.5 h-3.5" />
              <span>DOWNLOAD PLAN</span>
            </button>
          </div>
        </div>
      </div>

      {/* Control row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 flex gap-2">
          {["All", "Success", "Flagged", "Exception"].map(st => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3.5 py-1.5 rounded text-xs transition font-mono ${
                statusFilter === st 
                  ? "bg-white text-black font-semibold border border-white" 
                  : "bg-neutral-900 text-stone-400 border border-white/5 hover:text-white"
              }`}
            >
              {st.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
          <input
            type="text"
            placeholder="Search by ID, agent, action..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-neutral-950 border border-white/10 rounded pl-9 pr-4 py-2 text-xs text-white placeholder-stone-600 focus:outline-none focus:border-white/30 font-mono"
          />
        </div>
      </div>

      {/* Grid of logs */}
      <div className="metric-card rounded border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-white/10 bg-neutral-900/40 text-gray-500 text-[10px] uppercase font-bold tracking-wider">
                <th className="p-4">Timestamp</th>
                <th className="p-4">Tx ID</th>
                <th className="p-4">Arbiter Agent</th>
                <th className="p-4">Autonomous Directive</th>
                <th className="p-4">Execution Time</th>
                <th className="p-4 text-center">Status</th>
                <th className="p-4">Cluster Node</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-stone-500">
                    No matching audit logs found in the selected ledger epoch.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-white/2 transition">
                    <td className="p-4 text-neutral-400 whitespace-nowrap">{rec.timestamp}</td>
                    <td className="p-4 text-white font-semibold">{rec.id}</td>
                    <td className="p-4 text-zinc-300">{rec.agent}</td>
                    <td className="p-4 text-stone-400 max-w-[280px] truncate" title={rec.action}>{rec.action}</td>
                    <td className="p-4 text-gray-400 whitespace-nowrap">{rec.executionTime}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(rec.status)}`}>
                        {rec.status}
                      </span>
                    </td>
                    <td className="p-4 text-zinc-500 whitespace-nowrap">{rec.node}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
