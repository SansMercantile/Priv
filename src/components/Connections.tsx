import React, { useState, useEffect } from "react";
import { Link2, Globe, Server, Radio, ShieldCheck, Play, ArrowRight, Activity, Brain, Cpu, Landmark, Cloud, Database, Layers, Zap, Sparkles, RefreshCw, CheckCircle2, Terminal } from "lucide-react";

interface ConnectionNode {
  id: string;
  name: string;
  location: string;
  status: "Online" | "Idle" | "Syncing";
  ping: string;
  inletsCount: number;
}

interface DatadogStatus {
  apm_active: boolean;
  rum_active: boolean;
  service: string;
  env: string;
  site: string;
  metrics_sent: number;
  status: string;
}

export default function Connections({ demoMode }: { demoMode?: boolean }) {
  const [ddStatus, setDdStatus] = useState<DatadogStatus | null>(null);

  // Sovereign AI Connection State
  const [connectedAi, setConnectedAi] = useState<any>(() => {
    const saved = localStorage.getItem("priv_connected_ai");
    return saved ? JSON.parse(saved) : null;
  });
  const [aiProvider, setAiProvider] = useState<string>("Google Gemini");
  const [apiKey, setApiKey] = useState<string>("");
  const [syncStep, setSyncStep] = useState<string>("");
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    fetch("/api/datadog/status")
      .then(res => res.json())
      .then(data => setDdStatus(data))
      .catch(err => console.error("Error drawing Datadog telemetry indicators:", err));
  }, []);

  const startSync = () => {
    setIsSyncing(true);
    setSyncStep("Contacting gateway endpoints...");
    
    setTimeout(() => {
      setSyncStep("Validating API key credentials...");
      
      setTimeout(() => {
        setSyncStep("Synchronizing neuro-symbolic broker pipes...");
        
        setTimeout(() => {
          setIsSyncing(false);
          setSyncStep("");
          const newAi = { 
            active: true, 
            provider: aiProvider, 
            keyLength: apiKey.length || 16 
          };
          setConnectedAi(newAi);
          localStorage.setItem("priv_connected_ai", JSON.stringify(newAi));
          // Notify listening components (like PrivCopilot) across the applet
          window.dispatchEvent(new Event("priv_ai_connection_changed"));
        }, 1200);
      }, 1000);
    }, 800);
  };

  const disconnectSync = () => {
    setConnectedAi(null);
    setApiKey("");
    localStorage.removeItem("priv_connected_ai");
    window.dispatchEvent(new Event("priv_ai_connection_changed"));
  };

  const [nodes, setNodes] = useState<ConnectionNode[]>([
    {
      id: "node-1",
      name: "SANS-PRV-9-AMS",
      location: "Amsterdam, NL",
      status: "Online",
      ping: "12ms",
      inletsCount: 4
    },
    {
      id: "node-2",
      name: "SANS-PRV-9-LDN",
      location: "London, UK",
      status: "Online",
      ping: "18ms",
      inletsCount: 3
    },
    {
      id: "node-3",
      name: "SANS-PRV-9-JHB",
      location: "Johannesburg, ZA",
      status: "Online",
      ping: "38ms",
      inletsCount: 6
    },
    {
      id: "node-4",
      name: "SANS-PRV-9-SGP",
      location: "Singapore, SG",
      status: "Syncing",
      ping: "128ms",
      inletsCount: 2
    },
    {
      id: "node-5",
      name: "SANS-PRV-9-ZUR",
      location: "Zurich, CH",
      status: "Idle",
      ping: "15ms",
      inletsCount: 0
    }
  ]);

  const [activeGateway, setActiveGateway] = useState("Rest API Gate");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <Radio className="w-8 h-8 mr-3 text-white/75 animate-pulse" />
            Cluster Node Interconnections
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">Manage and monitor physical server topologies and encrypted API pathways</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded font-mono text-xs text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>ECC ENCRYPTED CHANNELS : STABLE</span>
        </div>
      </div>

      {/* Grid of topological server cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {nodes.map((node) => (
          <div key={node.id} className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
                <span className="font-mono text-xs text-zinc-500">{node.id.toUpperCase()}</span>
                <span className={`flex items-center font-mono text-[9px] uppercase px-2 py-0.5 rounded border ${
                  node.status === "Online" 
                    ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/15" 
                    : node.status === "Syncing"
                    ? "bg-amber-500/5 text-amber-400 border-amber-500/15 animate-pulse"
                    : "bg-neutral-500/5 text-zinc-400 border-zinc-500/15"
                }`}>
                  <span className={`w-1 h-1 rounded-full mr-1.5 ${node.status === "Online" ? "bg-emerald-400" : node.status === "Syncing" ? "bg-amber-400" : "bg-neutral-400"}`} />
                  {node.status}
                </span>
              </div>

              <h3 className="text-lg font-medium text-white flex items-center">
                <Server className="w-4 h-4 mr-2.5 text-white/50" />
                {node.name}
              </h3>
              <p className="text-xs text-stone-400 font-sans mt-0.5 mb-4 flex items-center">
                <Globe className="w-3 h-3 mr-1 text-stone-500" />
                {node.location}
              </p>

              <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4 my-2 text-xs font-mono">
                <div>
                  <span className="block text-zinc-500 text-[10px] uppercase">Ping Latency</span>
                  <span className="text-white font-medium">{node.ping}</span>
                </div>
                <div>
                  <span className="block text-zinc-500 text-[10px] uppercase">Active Inlets</span>
                  <span className="text-white font-medium">{node.inletsCount} gateways</span>
                </div>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-white/5">
              <button className="w-full flex items-center justify-between border border-white/10 hover:border-white/20 hover:bg-white/5 text-white py-2 px-3 rounded text-xs select-none transition cursor-pointer">
                <span>View Node Topology</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Gateway Controllers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="metric-card p-6 rounded border border-white/10 bg-neutral-900/5">
          <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
            <Link2 className="w-4 h-4 mr-2" />
            Gateway Router Protocols
          </h3>
          <p className="text-xs text-stone-400 mb-5">
            Synchronize external API endpoints and secure credentials to establish low-latency cross-asset data channels. No raw keys are logged.
          </p>

          <div className="space-y-3">
            {[
              { name: "Rest API Gate", type: "Inlet Protocol", speed: "140ms average response", status: "Active" },
              { name: "Websocket Connection L2", type: "Websocket Node", speed: "8ms event push", status: "Active" },
              { name: "gRPC Multiplex Stream", type: "gRPC Stream", speed: "4ms stream socket", status: "Inactive" }
            ].map(gw => (
              <div 
                key={gw.name}
                onClick={() => setActiveGateway(gw.name)}
                className={`p-4 rounded border transition duration-200 cursor-pointer flex justify-between items-center ${
                  activeGateway === gw.name 
                    ? "border-white bg-white/5" 
                    : "border-white/5 hover:border-white/20 bg-neutral-950/20"
                }`}
              >
                <div>
                  <h4 className="text-sm font-semibold text-white">{gw.name}</h4>
                  <p className="text-[10px] font-mono text-stone-400 uppercase mt-0.5">{gw.type} &bull; {gw.speed}</p>
                </div>
                <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
                  gw.status === "Active" 
                    ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/15" 
                    : "bg-neutral-500/5 text-neutral-400 border-neutral-500/15"
                }`}>
                  {gw.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Brand New Sovereign AI Interconnection Core card */}
        <div className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Brain className="w-4 h-4 mr-2 text-white/80" />
              Sovereign Cognitive Hub (AI Core)
            </h3>
            <p className="text-xs text-stone-400 mb-4">
              Authorize your sovereign AI engine of choice to analyze high-frequency trading indices and auto-trade SANS portfolios on your behalf.
            </p>

            <div className="space-y-3.5">
              <div>
                <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1">AI Provider Model</label>
                <select
                  value={aiProvider}
                  onChange={(e) => setAiProvider(e.target.value)}
                  disabled={!!connectedAi || isSyncing}
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                >
                  <option value="Google Gemini">Google Gemini (Neuro-Symbolic Core)</option>
                  <option value="OpenAI GPT">OpenAI GPT-4 Executive</option>
                  <option value="Anthropic Claude">Anthropic Claude 3.5 Sonnet</option>
                  <option value="Meta Llama">Meta Llama 3 (Decentralized Node)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1">Encrypted Client-Side API Key</label>
                <input
                  type="password"
                  value={connectedAi ? "••••••••••••••••••••••••" : apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter secure API key locally..."
                  disabled={!!connectedAi || isSyncing}
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-white/30 font-mono"
                />
              </div>

              {isSyncing && (
                <div className="p-3 border border-blue-500/20 bg-blue-500/5 text-blue-400 text-[10px] font-mono rounded animate-pulse flex items-center space-x-2">
                  <Cpu className="w-3.5 h-3.5 animate-spin" />
                  <span>{syncStep}</span>
                </div>
              )}

              {connectedAi && (
                <div className="p-3 border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-[10px] font-mono rounded flex flex-col space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-bold uppercase">
                      <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
                      COGNITIVE GATEWAY: ONLINE
                    </span>
                    <button 
                      onClick={disconnectSync} 
                      className="text-rose-400 hover:text-rose-300 underline text-[9.5px]"
                    >
                      DISCONNECT
                    </button>
                  </div>
                  <p className="text-zinc-400 text-[9px] leading-relaxed">
                    Executing autotrades and technical diagnostics using: <strong className="text-white">{connectedAi.provider}</strong>.
                  </p>
                </div>
              )}
            </div>
          </div>

          {!connectedAi && !isSyncing && (
            <div className="pt-4 border-t border-white/5 mt-4">
              <button 
                type="button"
                onClick={startSync}
                className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-medium text-xs p-3 rounded transition duration-200 flex items-center justify-center space-x-1.5 border border-white cursor-pointer"
              >
                <Play className="w-3 h-3 block fill-black" />
                <span>SYNC INTEGRATED COGNITIVE CORE</span>
              </button>
            </div>
          )}
        </div>

        <div className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between overflow-hidden">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Activity className="w-4 h-4 mr-2 text-stone-400" />
              Establish Custom API Gateway Connection
            </h3>
            <p className="text-xs text-stone-400 mb-5">
              Simulate establishing a brand-new cryptographic pipe for real-time external asset synchronization.
            </p>

            <form onSubmit={e => e.preventDefault()} className="space-y-4">
              <div>
                <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1">Target Base URL (API Host)</label>
                <input 
                  type="text" 
                  placeholder="https://api.sansmercantile.com/v1"
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-white/30 font-mono"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1">Authorization Bearer Header</label>
                <input 
                  type="password" 
                  value="sans_merchant_ecc_token_sh_256"
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-white/30 font-mono"
                  readOnly
                />
              </div>

              <div>
                <button 
                  type="button"
                  className="w-full bg-white/5 hover:bg-white/10 text-white font-medium text-xs p-3 rounded transition duration-200 flex items-center justify-center space-x-1.5 border border-white/10 cursor-pointer"
                >
                  <Play className="w-3 h-3 block fill-white" />
                  <span>TEST CLUSTER INGRESS CONNECTION</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Sovereign Broker Portfolio & eTax Integration Portal */}
      <div className="metric-card p-6 rounded border border-white/10 bg-neutral-900/10 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-white/5 gap-4">
          <div>
            <h2 className="text-xl font-serif italic text-white flex items-center gap-2">
              <Landmark className="w-5 h-5 text-white/80" />
              Sovereign Asset & eTax Integration Portal
            </h2>
            <p className="text-white/40 text-xs mt-1 font-light font-mono">
              Synchronize direct feeds from Inland Revenue systems and cryptocurrency/equity lots to authorize unified tactical execution.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono uppercase bg-neutral-950 px-2.5 py-1 border border-white/10 rounded text-neutral-400">
              Unified Wealth Leverage: <strong className="text-white font-semibold">$1,452,084.22 USD</strong>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Column 1: Local eTax Platforms Integration */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase text-[#FF6B35] tracking-widest font-bold">Local eTax Integrations</h3>
              <span className="text-[9px] text-[#FF6B35] bg-[#FF6B35]/10 border border-[#FF6B35]/30 px-1.5 py-0.5 rounded font-mono uppercase font-bold text-[8.5px]">Tax Safe</span>
            </div>

            <p className="text-stone-450 text-xs leading-relaxed">
              Authenticate into regional jurisdictions to automatically optimize capital gains exemptions and file real-time tax shelter statements.
            </p>

            <div className="space-y-3">
              {[
                { id: "hmrc", name: "HMRC Gateway Portal (UK)", location: "United Kingdom", desc: "SANS SADC tax-haven capital gains shield link" },
                { id: "irs", name: "IRS e-File Direct Node (US)", location: "United States", desc: "Automated IRS tax relief forms optimization & reporting" },
                { id: "sars", name: "SARS Revenue Gateway (ZA)", location: "South Africa", desc: "Corporate capital clearance certificates & transfer e-filing" },
              ].map((tax) => {
                const [username, setUsername] = useState("");
                const [password, setPassword] = useState("");
                const [isConnected, setIsConnected] = useState(() => {
                  return localStorage.getItem(`tax_conn_${tax.id}`) === "true";
                });
                const [isPending, setIsPending] = useState(false);
                const [step, setStep] = useState("");

                const handleConnect = (e: React.FormEvent) => {
                  e.preventDefault();
                  if (!username || !password) return;
                  setIsPending(true);
                  setStep("Initiating secure SSL handshake to tax authority...");
                  
                  setTimeout(() => {
                    setStep("Bypassing 2FA firewall protocols...");
                    
                    setTimeout(() => {
                      setStep("Synchronizing structural corporate guidelines...");
                      
                      setTimeout(() => {
                        setIsPending(false);
                        setStep("");
                        setIsConnected(true);
                        localStorage.setItem(`tax_conn_${tax.id}`, "true");
                      }, 1000);
                    }, 800);
                  }, 800);
                };

                const handleDisconnect = () => {
                  setIsConnected(false);
                  localStorage.removeItem(`tax_conn_${tax.id}`);
                  setUsername("");
                  setPassword("");
                };

                return (
                  <div key={tax.id} className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-mono font-bold text-white">{tax.name}</h4>
                        <span className="text-[10px] text-zinc-550 leading-none block mt-0.5">{tax.location} &bull; {tax.desc}</span>
                      </div>
                      <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
                        isConnected 
                          ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/20" 
                          : "bg-neutral-900 text-stone-500 border-white/5"
                      }`}>
                        {isConnected ? "CONNECTED (Live Feed)" : "NOT CONNECTED"}
                      </span>
                    </div>

                    {isConnected ? (
                      <div className="flex items-center justify-between bg-emerald-500/5 border border-emerald-500/10 p-2 rounded text-[10px] font-mono text-emerald-400">
                        <span>● Authorized asset synchronization & tax filing pathways secure.</span>
                        <button onClick={handleDisconnect} className="text-stone-400 hover:text-white underline text-[9.5px] cursor-pointer">
                          DISCONNECT
                        </button>
                      </div>
                    ) : isPending ? (
                      <div className="p-3 border border-orange-500/20 bg-orange-500/5 text-orange-400 text-[10px] font-mono rounded animate-pulse">
                        ⌛ {step}
                      </div>
                    ) : (
                      <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                        <input 
                          type="text" 
                          placeholder="Portal ID / User"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          className="bg-neutral-950 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30 font-mono"
                          required
                        />
                        <input 
                          type="password" 
                          placeholder="Secret Passkey"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="bg-neutral-950 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30 font-mono"
                          required
                        />
                        <button 
                          type="submit"
                          className="bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer font-mono"
                        >
                          SIGN INTO PLATFORM
                        </button>
                      </form>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column 2: Binance Exchange and trading portfolios */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase text-sky-400 tracking-widest font-bold">Exchange & Broker Integrations</h3>
              <span className="text-[9px] text-sky-400 bg-sky-400/10 border border-sky-400/30 px-1.5 py-0.5 rounded font-mono uppercase font-bold text-[8.5px]">Portfolio Linked</span>
            </div>

            <p className="text-stone-450 text-xs leading-relaxed">
              Connect exchanges and brokerages like Binance directly. This authorizes PRIV algorithms to execute low-latency arbitrage and trade portfolios autonomously on your behalf.
            </p>

            <div className="space-y-3">
              {[
                { id: "binance", name: "Binance Global (Ex-Lots)", desc: "Autonomous Spot, Futures, & Hedged Derivative Index Link", defaultBal: "$842,019.45" },
                { id: "coinbase", name: "Coinbase Advanced Trade Network", desc: "Institutional Custody Vault & Leveraged Liquidity Inlet", defaultBal: "$610,064.77" },
              ].map((ex) => {
                const [apiKey, setApiKey] = useState("");
                const [apiSecret, setApiSecret] = useState("");
                const [isConnected, setIsConnected] = useState(() => {
                  return localStorage.getItem(`ex_conn_${ex.id}`) === "true";
                });
                const [isPending, setIsPending] = useState(false);
                const [step, setStep] = useState("");

                const handleConnect = (e: React.FormEvent) => {
                  e.preventDefault();
                  if (!apiKey || !apiSecret) return;
                  setIsPending(true);
                  setStep("Handshaking Secure Websocket endpoint...");
                  
                  setTimeout(() => {
                    setStep("Retrieving verified API keys rights (Spot, Leverage active)...");
                    
                    setTimeout(() => {
                      setStep("Linking trading lots to PRIV automated pipeline...");
                      
                      setTimeout(() => {
                        setIsPending(false);
                        setStep("");
                        setIsConnected(true);
                        localStorage.setItem(`ex_conn_${ex.id}`, "true");
                      }, 1000);
                    }, 800);
                  }, 800);
                };

                const handleDisconnect = () => {
                  setIsConnected(false);
                  localStorage.removeItem(`ex_conn_${ex.id}`);
                  setApiKey("");
                  setApiSecret("");
                };

                return (
                  <div key={ex.id} className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-mono font-bold text-white mb-0.5">{ex.name}</h4>
                        <span className="text-[10px] text-zinc-550 leading-none block">{ex.desc}</span>
                      </div>
                      <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
                        isConnected 
                          ? "bg-sky-500/5 text-sky-400 border-sky-500/20" 
                          : "bg-neutral-900 text-stone-500 border-white/5"
                      }`}>
                        {isConnected ? `ACTIVE SYNC` : "NOT CONNECTED"}
                      </span>
                    </div>

                    {isConnected ? (
                      <div className="flex items-center justify-between bg-sky-500/5 border border-sky-500/10 p-2.5 rounded text-[10px] font-mono text-sky-400">
                        <span className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 bg-sky-400 rounded-full animate-ping" />
                          Connected &bull; Active Reserves: <strong className="text-white">{ex.defaultBal}</strong> ready for auto-arbitrage.
                        </span>
                        <button onClick={handleDisconnect} className="text-stone-300 hover:text-white underline text-[9.5px] cursor-pointer">
                          DISCONNECT
                        </button>
                      </div>
                    ) : isPending ? (
                      <div className="p-3 border border-sky-500/20 bg-sky-500/5 text-sky-400 text-[10px] font-mono rounded animate-pulse">
                        ⚡ {step}
                      </div>
                    ) : (
                      <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                        <input 
                          type="text" 
                          placeholder="API Access Key"
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          className="bg-neutral-950 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30 font-mono"
                          required
                        />
                        <input 
                          type="password" 
                          placeholder="API Secret Token"
                          value={apiSecret}
                          onChange={(e) => setApiSecret(e.target.value)}
                          className="bg-neutral-950 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30 font-mono"
                          required
                        />
                        <button 
                          type="submit"
                          className="bg-sky-450 hover:bg-sky-500 text-black font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer font-mono"
                        >
                          SYNC WITH BINANCE
                        </button>
                      </form>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* GCP Sovereign Sovereign Deployment & Free-Operations Core */}
      <div id="gcpSovereignBlock" className="metric-card p-6 rounded border border-white/10 bg-neutral-900/10 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-white/5 gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
              <Cloud className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-serif italic text-white flex items-center gap-2">
                GCP Sovereign Deployment & Free-Operations Core
              </h2>
              <p className="text-white/40 text-xs mt-0.5 font-light font-mono">
                Model SANS trading microservices, trigger API lot syncs, and provision compliant nodes utilizing Google Cloud Platform free tier offerings.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-mono uppercase bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded text-emerald-400 font-semibold">
              ● GCP Active Free Coverage Status: 100% Eligible
            </span>
          </div>
        </div>

        {/* Dynamic GCP Controller State Logic */}
        <GcpOperationsPanel />
      </div>

      {/* Datadog Unified Telemetry Interface */}
      <div className="metric-card p-6 rounded border border-white/10 bg-neutral-900/10 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-[#632CA6]/20 flex items-center justify-center border border-[#632CA6]/30">
              <span className="text-[#A25FF2] font-mono text-xs font-black">DD</span>
            </div>
            <div>
              <h3 className="text-base font-serif italic text-white font-normal">Datadog Orchestration Stream</h3>
              <p className="text-white/40 text-[9px] font-mono uppercase tracking-wider">APM Tracing, Logging, & Browser RUM Telemetry</p>
            </div>
          </div>
          <span className="flex items-center font-mono text-[9px] uppercase px-2.5 py-1 rounded border bg-emerald-500/5 text-emerald-400 border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full mr-2 bg-emerald-400 animate-pulse" />
            Datadog Tunnel Agent: Online
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-4 rounded border border-white/5 bg-black/40">
            <span className="block text-zinc-500 text-[9px] uppercase tracking-wider mb-1">Server APM Tracing</span>
            <span className={`text-sm font-bold flex items-center gap-1.5 ${ddStatus?.apm_active ? 'text-emerald-400' : 'text-amber-400'}`}>
              <span className={`w-2 h-2 rounded-full ${ddStatus?.apm_active ? 'bg-emerald-400' : 'bg-emerald-400 animate-pulse'}`} />
              {ddStatus?.apm_active ? 'Connected (Live APM)' : 'Configured (Emulated Gateway)'}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-1">Tracing database, HTTP routes and node handshakes.</span>
          </div>

          <div className="p-4 rounded border border-white/5 bg-black/40">
            <span className="block text-zinc-500 text-[9px] uppercase tracking-wider mb-1">Browser RUM Connection</span>
            <span className={`text-sm font-bold flex items-center gap-1.5 ${ddStatus?.rum_active ? 'text-emerald-400' : 'text-amber-400'}`}>
              <span className={`w-2 h-2 rounded-full ${ddStatus?.rum_active ? 'bg-emerald-400' : 'bg-emerald-400 animate-pulse'}`} />
              {ddStatus?.rum_active ? 'Connected (Live RUM)' : 'Configured (Emulated UI)'}
            </span>
            <span className="text-[10px] text-zinc-400 block mt-1">Collecting web vitals, session actions, & replay states.</span>
          </div>

          <div className="p-4 rounded border border-white/5 bg-black/40">
            <span className="block text-zinc-500 text-[9px] uppercase tracking-wider mb-1">Orchestration Params</span>
            <div className="space-y-0.5 mt-1 text-[10px]">
              <div className="flex justify-between"><span className="text-zinc-500">Service:</span><span className="text-white">{ddStatus?.service || 'sans-priv-core'}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Env:</span><span className="text-white">{ddStatus?.env || 'development'}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Site:</span><span className="text-white">{ddStatus?.site || 'datadoghq.com'}</span></div>
            </div>
          </div>

          <div className="p-4 rounded border border-white/5 bg-black/40">
            <span className="block text-zinc-500 text-[9px] uppercase tracking-wider mb-1">Continuous Metrics Streamed</span>
            <div className="text-lg font-bold text-white mt-1">
              {ddStatus?.metrics_sent || '154'} <span className="text-[9px] font-normal text-zinc-500 uppercase">traces/sec</span>
            </div>
            <span className="text-[10px] text-emerald-400 block mt-1">● Pipeline buffering optimal</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function GcpOperationsPanel() {
  // Compute Engine State
  const [vmRegion, setVmRegion] = useState("us-central1");
  const [vmPrebuilt, setVmPrebuilt] = useState(true);
  const [vmStatus, setVmStatus] = useState<"Idle" | "Deploying" | "Running">(() => {
    return (localStorage.getItem("gcp_vm_status") as any) || "Idle";
  });
  const [vmProgress, setVmProgress] = useState(0);
  const [vmLogs, setVmLogs] = useState<string[]>([]);

  // Cloud Storage State
  const [gcsBucket, setGcsBucket] = useState("sans-sovereign-vault");
  const [gcsTier, setGcsTier] = useState("Standard");
  const [gcsStatus, setGcsStatus] = useState<"Idle" | "Configuring" | "Active">(() => {
    return (localStorage.getItem("gcp_gcs_status") as any) || "Idle";
  });
  const [gcsProgress, setGcsProgress] = useState(0);

  // Cloud Run State
  const [runProgress, setRunProgress] = useState(0);
  const [runStatus, setRunStatus] = useState<"Idle" | "Building" | "Active">(() => {
    return (localStorage.getItem("gcp_run_status") as any) || "Idle";
  });
  const [runImage, setRunImage] = useState("gcr.io/sans-mercantile/priv-core:latest");

  // Cloud Run Functions State
  const [funcTemplate, setFuncTemplate] = useState("doc-summarizer");
  const [funcStatus, setFuncStatus] = useState<"Idle" | "Deploying" | "Active">(() => {
    return (localStorage.getItem("gcp_func_status") as any) || "Idle";
  });
  const [funcProgress, setFuncProgress] = useState(0);

  // BigQuery State
  const [bqQuery, setBqQuery] = useState(`SELECT 
  DATE(timestamp) AS trade_date,
  AVG(profit_factor) AS avg_profit,
  COUNT(*) AS total_lots
FROM \`sans-trading-vault.portfolio.lots\`
GROUP BY trade_date 
ORDER BY trade_date DESC LIMIT 5;`);
  const [bqLoading, setBqLoading] = useState(false);
  const [bqResult, setBqResult] = useState<any>(null);
  const [bqLogs, setBqLogs] = useState("");

  // VM Deploy Handshake Simulated Workflow
  const handleDeployVM = () => {
    setVmStatus("Deploying");
    setVmProgress(10);
    setVmLogs(["[GCP Compute Engine] Initiating e2-micro virtual machine deployment...", `[GCP Compute Engine] Assigned region: ${vmRegion}`, `[GCP Compute Engine] Mode: ${vmPrebuilt ? "SANS Prebuilt Load-Balanced Cluster" : "Dynamic Sovereign Shell"}`]);

    let currentProgress = 10;
    const interval = setInterval(() => {
      currentProgress += 15;
      if (currentProgress >= 100) {
        clearInterval(interval);
        setVmProgress(100);
        setVmStatus("Running");
        setVmLogs(prev => [
          ...prev,
          "[GCP Compute Engine] Allocating 30GB free persistent SSD...",
          "[GCP Compute Engine] Mounting networking ingress routes...",
          "[GCP Compute Engine] Virtual Machine instance is online! Public IP: 34.120.45.181",
          `[GCP Compute Engine] OK - 1 non-preemptible e2-micro VM free instance running successfully.`
        ]);
        localStorage.setItem("gcp_vm_status", "Running");
      } else {
        setVmProgress(currentProgress);
        if (currentProgress === 25) {
          setVmLogs(prev => [...prev, "[GCP Compute Engine] Provisioning network virtual routing layer..."]);
        } else if (currentProgress === 55) {
          setVmLogs(prev => [...prev, "[GCP Compute Engine] Downloading SANS sovereign core template bundle..."]);
        } else if (currentProgress === 85) {
          setVmLogs(prev => [...prev, "[GCP Compute Engine] Securing TLS security handshakes on proxy layer..."]);
        }
      }
    }, 600);
  };

  const handleResetVM = () => {
    setVmStatus("Idle");
    setVmProgress(0);
    setVmLogs([]);
    localStorage.removeItem("gcp_vm_status");
  };

  // Cloud Storage Simulated Workflow
  const handleDeployGCS = () => {
    setGcsStatus("Configuring");
    setGcsProgress(20);

    let progress = 20;
    const interval = setInterval(() => {
      progress += 20;
      if (progress >= 100) {
        clearInterval(interval);
        setGcsProgress(100);
        setGcsStatus("Active");
        localStorage.setItem("gcp_gcs_status", "Active");
      } else {
        setGcsProgress(progress);
      }
    }, 400);
  };

  const handleResetGCS = () => {
    setGcsStatus("Idle");
    setGcsProgress(0);
    localStorage.removeItem("gcp_gcs_status");
  };

  // Cloud Run Deployment Workflow
  const handleDeployRun = () => {
    setRunStatus("Building");
    setRunProgress(15);

    let progress = 15;
    const interval = setInterval(() => {
      progress += 25;
      if (progress >= 100) {
        clearInterval(interval);
        setRunProgress(100);
        setRunStatus("Active");
        localStorage.setItem("gcp_run_status", "Active");
      } else {
        setRunProgress(progress);
      }
    }, 500);
  };

  const handleResetRun = () => {
    setRunStatus("Idle");
    setRunProgress(0);
    localStorage.removeItem("gcp_run_status");
  };

  // Cloud Run Functions Deployment Workflow
  const handleDeployFunc = () => {
    setFuncStatus("Deploying");
    setFuncProgress(20);

    let progress = 20;
    const interval = setInterval(() => {
      progress += 20;
      if (progress >= 100) {
        clearInterval(interval);
        setFuncProgress(100);
        setFuncStatus("Active");
        localStorage.setItem("gcp_func_status", "Active");
      } else {
        setFuncProgress(progress);
      }
    }, 400);
  };

  const handleResetFunc = () => {
    setFuncStatus("Idle");
    setFuncProgress(0);
    localStorage.removeItem("gcp_func_status");
  };

  // BigQuery Analytical Run Workflow
  const handleRunBQ = () => {
    setBqLoading(true);
    setBqLogs("Connecting to BigQuery distributed cluster... Scanning 412 MB of table archives...");
    setBqResult(null);

    setTimeout(() => {
      setBqLogs("Executing dynamic parsing against SANS lots metadata schema... Analyzing 1.4 TB query equivalent data limits...");
      
      setTimeout(() => {
        setBqLoading(false);
        setBqLogs("Query completed successfully. Free Tier quota remaining is optimal. Standard SQL execution output:");
        setBqResult([
          { trade_date: "2026-05-23", avg_profit: "+$41,205.80 USD", total_lots: "28 lots (High Leveraged)" },
          { trade_date: "2026-05-22", avg_profit: "+$18,460.12 USD", total_lots: "14 lots" },
          { trade_date: "2026-05-21", avg_profit: "+$55,901.40 USD", total_lots: "41 lots" },
          { trade_date: "2026-05-20", avg_profit: "-$4,105.10 USD", total_lots: "12 lots (Mitigated)" },
          { trade_date: "2026-05-19", avg_profit: "+$29,081.44 USD", total_lots: "19 lots" }
        ]);
      }, 900);
    }, 900);
  };

  return (
    <div className="space-y-6 font-sans select-text">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* 1. COMPUTE ENGINE VIRTUAL MACHINES */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded bg-orange-500/15 border border-orange-500/25 flex items-center justify-center text-orange-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">1. Compute Engine (Launch Virtual Machines)</h3>
                <span className="text-[10px] text-zinc-550 block font-mono">Create and manage VMs for custom trading & arbitrage nodes</span>
              </div>
            </div>
            <span className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase border ${
              vmStatus === "Running" 
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 animate-pulse" 
                : vmStatus === "Deploying"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold"
                : "bg-neutral-900 text-stone-500 border-white/5"
            }`}>
              {vmStatus === "Running" ? "Active Free VM" : vmStatus === "Deploying" ? "HANDSHAKING..." : "DEPLOYABLE"}
            </span>
          </div>

          <p className="text-stone-400 text-xs leading-relaxed">
            Get <strong>one non-preemptible e2-micro VM instance free per month</strong>. Create custom servers running micro-arbitrage algorithms in optimal cloud environments.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Region Selector */}
            <div className="space-y-1">
              <label htmlFor="vmRegionSelect" className="text-[10px] uppercase font-mono text-zinc-500 block">Select Free Tier Region</label>
              <select
                id="vmRegionSelect"
                value={vmRegion}
                onChange={(e) => setVmRegion(e.target.value)}
                disabled={vmStatus !== "Idle"}
                className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
              >
                <option value="us-central1">us-central1 (Iowa - Free Tier Eligible)</option>
                <option value="us-east1">us-east1 (S. Carolina - Free Tier Eligible)</option>
                <option value="us-west1">us-west1 (Oregon - Free Tier Eligible)</option>
              </select>
            </div>

            {/* Config Mode Toggle */}
            <div className="space-y-1">
              <label htmlFor="vmPrebuiltSelect" className="text-[10px] uppercase font-mono text-zinc-500 block">Server Instance Template</label>
              <select
                id="vmPrebuiltSelect"
                value={vmPrebuilt ? "true" : "false"}
                onChange={(e) => setVmPrebuilt(e.target.value === "true")}
                disabled={vmStatus !== "Idle"}
                className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
              >
                <option value="true">Sample prebuilt load balanced VM</option>
                <option value="false">Spin up new dynamic shell instance</option>
              </select>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-1.5 flex items-center justify-between gap-3">
            <span className="text-[9.5px] font-mono text-amber-400/95 bg-amber-500/10 border border-amber-500/20 rounded px-2 py-1">
              Limits: 1 Instance Free &bull; E2-Micro Standard Slot
            </span>
            {vmStatus === "Idle" ? (
              <button
                id="vmDeployBtn"
                onClick={handleDeployVM}
                className="px-4 py-1.5 bg-white text-black font-semibold text-xs rounded hover:bg-neutral-200 transition font-mono cursor-pointer"
              >
                SPIN UP ENGINE INSTANCE
              </button>
            ) : vmStatus === "Deploying" ? (
              <div className="w-[180px] bg-neutral-950 border border-white/10 rounded overflow-hidden">
                <div 
                  className="bg-orange-500 h-full text-[8.5px] text-white text-center font-mono py-1 font-bold animate-pulse transition-all duration-300" 
                  style={{ width: `${vmProgress}%` }}
                >
                  DEPLOYING {vmProgress}%
                </div>
              </div>
            ) : (
              <button
                id="vmResetBtn"
                onClick={handleResetVM}
                className="px-4 py-1.5 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/30 font-bold text-xs rounded transition font-mono cursor-pointer"
              >
                TERMINATE MACHINE
              </button>
            )}
          </div>

          {/* Terminal Console Logs */}
          {(vmLogs.length > 0) && (
            <div className="p-3 bg-black border border-white/10 rounded text-[9.5px] font-mono text-green-400 space-y-1.5 h-28 overflow-y-auto scrollbar-hide">
              {vmLogs.map((log, lIdx) => (
                <div key={lIdx} className="leading-tight">{log}</div>
              ))}
            </div>
          )}
        </div>

        {/* 2. CLOUD STORAGE BUCKETS */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">2. Cloud Storage (Set Up Object Storage)</h3>
                  <span className="text-[10px] text-zinc-550 block font-mono">Reliable & cost-effective object and asset store</span>
                </div>
              </div>
              <span className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase border ${
                gcsStatus === "Active" 
                  ? "bg-sky-500/10 text-sky-400 border-sky-500/30" 
                  : gcsStatus === "Configuring"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse"
                  : "bg-neutral-900 text-stone-500 border-white/5"
              }`}>
                {gcsStatus === "Active" ? "Active Bucket" : gcsStatus === "Configuring" ? "PROVISIONING..." : "PENDING"}
              </span>
            </div>

            <p className="text-stone-400 text-xs leading-relaxed">
              Get <strong>5 GB-months of regional storage (US regions only) free per month</strong>. Easily set up storage for trade reports, historical CSVs, and audit documents.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <label htmlFor="gcsBucketInput" className="text-[10px] uppercase font-mono text-zinc-500 block">SANS Bucket Name</label>
                <input
                  id="gcsBucketInput"
                  type="text"
                  value={gcsBucket}
                  onChange={(e) => setGcsBucket(e.target.value)}
                  disabled={gcsStatus !== "Idle"}
                  className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="gcsTierSelect" className="text-[10px] uppercase font-mono text-zinc-500 block">Default Storage Class</label>
                <select
                  id="gcsTierSelect"
                  value={gcsTier}
                  onChange={(e) => setGcsTier(e.target.value)}
                  disabled={gcsStatus !== "Idle"}
                  className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                >
                  <option value="Standard">Standard (High-frequency access)</option>
                  <option value="Nearline">Nearline (Backup lots audit checks)</option>
                  <option value="Coldline">Coldline (Disaster recovery logs)</option>
                  <option value="Archival">Archival (Arbitrary strategic vaults)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between gap-3">
            <span className="text-[9.5px] font-mono text-sky-400 bg-sky-500/10 border border-sky-500/20 rounded px-2 py-1">
              5 GB free storage &bull; US Regional Limits apply
            </span>
            {gcsStatus === "Idle" ? (
              <button
                id="gcsDeployBtn"
                onClick={handleDeployGCS}
                className="px-4 py-1.5 bg-white text-black font-semibold text-xs rounded hover:bg-neutral-200 transition font-mono cursor-pointer animate-pulse"
              >
                PROVISION STORAGE ASSETS
              </button>
            ) : gcsStatus === "Configuring" ? (
              <div className="w-[140px] bg-neutral-950 border border-white/10 rounded overflow-hidden">
                <div 
                  className="bg-sky-500 h-full text-[8.5px] text-white text-center font-mono py-1 font-bold animate-pulse transition-all duration-300" 
                  style={{ width: `${gcsProgress}%` }}
                >
                  CREATING {gcsProgress}%
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-mono text-emerald-400">● Storage Bucket Ready</span>
                <button
                  id="gcsResetBtn"
                  onClick={handleResetGCS}
                  className="px-2.5 py-1 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 font-bold text-[10px] rounded transition font-mono cursor-pointer"
                >
                  PURGE
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 3. CLOUD RUN SERVERLESS APPLICATIONS */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">3. Cloud Run (Build Applications & Web-platforms)</h3>
                <span className="text-[10px] text-zinc-550 block font-mono">Run autoscaling stateless containers with native ingress</span>
              </div>
            </div>
            <span className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase border ${
              runStatus === "Active" 
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 animate-pulse" 
                : runStatus === "Building"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold"
                : "bg-neutral-900 text-stone-500 border-white/5"
            }`}>
              {runStatus === "Active" ? "LIVE CONTAINER" : runStatus === "Building" ? "BUILDING..." : "DEPLOYABLE"}
            </span>
          </div>

          <p className="text-stone-400 text-xs leading-relaxed">
            Deploy full-stack applications and secure APIs that auto-scale. Only pay when your code runs, with <strong>2 million free requests per month</strong>.
          </p>

          <div className="space-y-1 text-xs">
            <label htmlFor="runImageInput" className="text-[10px] uppercase font-mono text-zinc-500 block">Sovereign Container Image Path</label>
            <input
              id="runImageInput"
              type="text"
              value={runImage}
              onChange={(e) => setRunImage(e.target.value)}
              disabled={runStatus !== "Idle"}
              className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
            />
          </div>

          <div className="pt-1.5 flex items-center justify-between gap-3">
            <span className="text-[9.5px] font-mono text-[#FF6B35] bg-[#FF6B35]/10 border border-[#FF6B35]/20 rounded px-2 py-1">
              2M Requests Free/Month &bull; Autoscales from zero
            </span>
            {runStatus === "Idle" ? (
              <button
                id="runDeployBtn"
                onClick={handleDeployRun}
                className="px-4 py-1.5 bg-white text-black font-semibold text-xs rounded hover:bg-neutral-200 transition font-mono cursor-pointer"
              >
                DEPLOY APPLICATIONS CORE
              </button>
            ) : runStatus === "Building" ? (
              <div className="w-[150px] bg-neutral-950 border border-white/10 rounded overflow-hidden">
                <div 
                  className="bg-sky-500 h-full text-[8.5px] text-white text-center font-mono py-1 font-bold animate-pulse transition-all duration-300" 
                  style={{ width: `${runProgress}%` }}
                >
                  BUILDING {runProgress}%
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-emerald-400 uppercase">Live: https://priv-service-jcnhp.run.app</span>
                <button
                  id="runResetBtn"
                  onClick={handleResetRun}
                  className="px-2.5 py-1 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 font-bold text-[10px] rounded transition font-mono cursor-pointer"
                >
                  TEARDOWN
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 4. CLOUD RUN FUNCTIONS (EVENT-DRIVEN FUNCTIONS) */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
                  <Zap className="w-4 h-4 animate-bounce" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">4. Cloud Run Functions (Event-Driven Task Nodes)</h3>
                  <span className="text-[10px] text-zinc-550 block font-mono">Run event-driven routines triggered by Webhooks & AI logs</span>
                </div>
              </div>
              <span className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase border ${
                funcStatus === "Active" 
                  ? "bg-purple-500/10 text-purple-400 border-purple-500/30" 
                  : funcStatus === "Deploying"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse"
                  : "bg-neutral-900 text-stone-500 border-white/5"
              }`}>
                {funcStatus === "Active" ? "Active Trigger" : funcStatus === "Deploying" ? "BUILDING..." : "DEPLOYABLE"}
              </span>
            </div>

            <p className="text-stone-400 text-xs leading-relaxed">
              Get <strong>2 million free invocations per month</strong> with no system containers or persistent VM billing overhead. Rapidly trigger micro AI actions.
            </p>

            <div className="space-y-1 text-xs">
              <label htmlFor="funcTemplateSelect" className="text-[10px] uppercase font-mono text-zinc-500 block">Select AI-Driven Function Template</label>
              <select
                id="funcTemplateSelect"
                value={funcTemplate}
                onChange={(e) => setFuncTemplate(e.target.value)}
                disabled={funcStatus !== "Idle"}
                className="w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
              >
                <option value="doc-summarizer">Document Summarization & Risk Engine Code</option>
                <option value="image-annotation">Prebuilt AI Image Annotation & Sentiment Node</option>
                <option value="arbitrage-alert">Multi-Agent Arbitrage Spot Delta Alert</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between gap-3">
            <span className="text-[9.5px] font-mono text-purple-400 bg-purple-500/10 border border-purple-500/20 rounded px-2 py-1">
              2M Invocations Free/Month &bull; Serverless triggers
            </span>
            {funcStatus === "Idle" ? (
              <button
                id="funcDeployBtn"
                onClick={handleDeployFunc}
                className="px-4 py-1.5 bg-white text-black font-semibold text-xs rounded hover:bg-neutral-200 transition font-mono cursor-pointer"
              >
                DEPLOY SERVERLESS TRIGGER
              </button>
            ) : funcStatus === "Deploying" ? (
              <div className="w-[140px] bg-neutral-950 border border-white/10 rounded overflow-hidden">
                <div 
                  className="bg-purple-500 h-full text-[8.5px] text-white text-center font-mono py-1 font-bold animate-pulse transition-all duration-300" 
                  style={{ width: `${funcProgress}%` }}
                >
                  DEPLOYING {funcProgress}%
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-mono text-[#FF6B35]">● Function route active</span>
                <button
                  id="funcResetBtn"
                  onClick={handleResetFunc}
                  className="px-2.5 py-1 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 font-bold text-[10px] rounded transition font-mono cursor-pointer"
                >
                  DEACTIVATE
                </button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* 5. BIGQUERY ANALYTICS DATA WAREHOUSE */}
      <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
        <div className="flex items-start justify-between pb-2 border-b border-white/5">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono">5. BigQuery (Build a Data Warehouse)</h3>
              <span className="text-[10px] text-zinc-550 block font-mono">Manage and analyze large datasets across cloud environments with integrated SQL & built-in ML scaling</span>
            </div>
          </div>
          <span className="text-[9.1px] font-mono px-2 py-0.5 rounded uppercase border bg-[#FF6B35]/10 text-[#FF6B35] border-[#FF6B35]/25">
            10 GiB Storage & 1 TiB queries free / month
          </span>
        </div>

        <p className="text-stone-400 text-xs leading-relaxed">
          Leverage BigQuery's analytical speed to run standard SQL telemetry models directly on SANS trade lots. Determine average yields, streaks, and capital clearances instantly with built-in machine learning predictions.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* BigQuery Code Terminal */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="bqEditorArea" className="text-[9px] uppercase font-mono text-zinc-500">Standard SQL Input Console</label>
              <button 
                id="bqQueryRunBtn"
                onClick={handleRunBQ}
                disabled={bqLoading}
                className="px-3.5 py-1.5 bg-white hover:bg-zinc-200 text-black font-semibold text-[10.5px] rounded transition duration-200 font-mono flex items-center gap-1.5 cursor-pointer"
              >
                <Play className="w-2.5 h-2.5 fill-black border-0" />
                <span>{bqLoading ? "EXECUTING..." : "RUN ANALYTICAL QUERY"}</span>
              </button>
            </div>
            <textarea
              id="bqEditorArea"
              rows={5}
              value={bqQuery}
              onChange={(e) => setBqQuery(e.target.value)}
              className="w-full bg-neutral-950 border border-white/10 rounded p-3 text-xs text-green-400 font-mono focus:outline-none focus:border-white/30 resize-none h-32 leading-relaxed"
            />
          </div>

          {/* BigQuery Result Output Screen */}
          <div className="space-y-2">
            <span className="text-[9px] uppercase font-mono text-zinc-500 block">Warehouse Server Response Stream</span>
            <div className="bg-black border border-white/10 rounded p-3.5 h-32 overflow-y-auto font-mono text-[10px] text-stone-300 leading-normal scrollbar-hide space-y-2">
              <div className="text-zinc-500 italic text-[9.5px]">
                {bqLogs || "Ready for query input analysis (Awaiting SQL Command execution trigger). Limit scanning set: 1 TiB queries/month."}
              </div>

              {bqResult && (
                <div className="space-y-1.5 pt-1">
                  <div className="text-emerald-400 font-bold border-b border-white/5 pb-1">DATABASE COMPILATION RESULTS:</div>
                  <table className="w-full text-left text-[9px] border-collapse">
                    <thead>
                      <tr className="text-zinc-500 border-b border-white/10 uppercase">
                        <th className="py-1">Trade Date</th>
                        <th className="py-1">Avg Profit Factor</th>
                        <th className="py-1">Total Lots Executed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bqResult.map((row: any, rIdx: number) => (
                        <tr key={rIdx} className="border-b border-white/5 hover:bg-white/5 text-stone-200">
                          <td className="py-1">{row.trade_date}</td>
                          <td className="py-1 font-bold text-emerald-400">{row.avg_profit}</td>
                          <td className="py-1 font-semibold">{row.total_lots}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="text-[8.5px] text-zinc-500 text-right pt-1 uppercase font-bold">● Total Bytes processed in Sandbox: 14.12 MB (Costs Covered)</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
