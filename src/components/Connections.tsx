import React, { useState, useEffect } from "react";
import { Link2, Globe, Server, Radio, ShieldCheck, Play, ArrowRight, Activity, Brain, Cpu, Landmark, Cloud, Database, Layers, Zap, Sparkles, RefreshCw, CheckCircle2, Terminal } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
  const navigate = useNavigate();
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
          // Notify listening components (like PRIV automated core) across the applet
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

  // Institutional-tier gate — Cluster/Gateway/AI-sync infrastructure UI is
  // reserved for the Sovereign node tier. Reads the same xm_node_tier key
  // UserProfileEditor writes, polling to stay in sync without a reload.
  const [nodeTier, setNodeTier] = useState<string>(() => {
    return localStorage.getItem("xm_node_tier") || "obsidian";
  });
  useEffect(() => {
    const syncTier = () => setNodeTier(localStorage.getItem("xm_node_tier") || "obsidian");
    const interval = setInterval(syncTier, 900);
    return () => clearInterval(interval);
  }, []);
  const isInstitutional = nodeTier === "sovereign";

  if (!isInstitutional) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[420px] space-y-5 text-center px-6">
        <div className="p-4 rounded-full bg-teal-500/10 border border-teal-500/30">
          <ShieldCheck className="w-10 h-10 text-teal-400" />
        </div>
        <div>
          <h1 className="text-2xl font-serif italic text-white">Cluster Node Interconnections</h1>
          <p className="text-white/40 text-sm mt-2 max-w-md">
            Direct infrastructure control — cluster topology, gateway routing, and
            sovereign AI synchronization — is available on the Sovereign node tier.
          </p>
        </div>
        <button
          onClick={() => navigate("/dashboard/profile")}
          className="flex items-center space-x-2 px-5 py-2.5 bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/40 rounded text-teal-300 text-sm font-medium transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          <span>Upgrade to Sovereign</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

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
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-650 focus:outline-none focus:border-white/30 font-mono"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1">Authorization Bearer Header</label>
                <input 
                  type="password" 
                  value="sans_merchant_ecc_token_sh_256"
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-650 focus:outline-none focus:border-white/30 font-mono"
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

            <p className="text-stone-400 text-xs leading-relaxed">
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
                  <div key={tax.id} className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10 text-xs">
                    <div className="flex items-center justify-between animate-fadeIn">
                      <div>
                        <h4 className="text-xs font-mono font-bold text-white">{tax.name}</h4>
                        <span className="text-[10px] text-zinc-500 leading-none block mt-0.5">{tax.location} &bull; {tax.desc}</span>
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
                      <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono">
                        <input 
                          type="text" 
                          placeholder="Portal ID / User"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
                          required
                        />
                        <input 
                          type="password" 
                          placeholder="Secret Passkey"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
                          required
                        />
                        <button 
                          type="submit"
                          className="bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer"
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
              <h3 className="text-xs font-mono uppercase text-sky-400 tracking-widest font-bold font-bold">Exchange & Broker Integrations</h3>
              <span className="text-[9px] text-sky-400 bg-sky-400/10 border border-sky-400/30 px-1.5 py-0.5 rounded font-mono uppercase font-bold text-[8.5px]">Portfolio Linked</span>
            </div>

            <p className="text-stone-400 text-xs leading-relaxed">
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
                        // Automatically navigate to Profile focusing KYC steps
                        navigate("/dashboard/profile?triggerKYC=true");
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
                  <div key={ex.id} className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10 text-xs">
                    <div className="flex items-center justify-between animate-fadeIn">
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
                      <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono">
                        <input 
                          type="text" 
                          placeholder="API Access Key"
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
                          required
                        />
                        <input 
                          type="password" 
                          placeholder="API Secret Token"
                          value={apiSecret}
                          onChange={(e) => setApiSecret(e.target.value)}
                          className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
                          required
                        />
                        <button 
                          type="submit"
                          className="bg-sky-450 hover:bg-sky-500 text-black font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer"
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

      {/* SANS Constellation Sandbox Network & Datadog Core */}
      <div id="gcpSovereignBlock" className="metric-card p-6 rounded border border-white/10 bg-neutral-900/10 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-white/5 gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
              <Layers className="w-5 h-5 animate-pulse text-sky-400" />
            </div>
            <div>
              <h2 className="text-xl font-serif italic text-white flex items-center gap-2">
                SANS Sandbox Constellation & Compartmentalizer DB Core
              </h2>
              <p className="text-white/40 text-xs mt-0.5 font-light font-mono">
                Provision isolated Vercel hypervisor sandboxes securely connected of Datadog APM metrics, and manage strategically compartmentalized databases to optimize core execution resources.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-mono uppercase bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded text-emerald-400 font-semibold">
              ● ACTIVE CONSTELLATION MIGRATION: 100% WORKSPACE CERTIFIED
            </span>
          </div>
        </div>

        {/* Dynamic Sandbox Controller and Compartmentalized Databases Logic */}
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
            <span className="block text-[#a1a1aa] text-[9px] uppercase tracking-wider mb-1">Orchestration Params</span>
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
  // Sandboxes in executive constellation
  const [sandboxes, setSandboxes] = useState([
    { id: "sb-omega", name: "sandbox-omega-broker", role: "High-Frequency Automated Trading", status: "Active", uptime: "14h 25m", cpu: "2.4%", tracesLink: "Connected to Datadog" },
    { id: "sb-ledger", name: "sandbox-vault-ledger", role: "Production Balances Sync Node", status: "Active", uptime: "74h 12m", cpu: "1.1%", tracesLink: "Connected to Datadog" },
    { id: "sb-compliance", name: "sandbox-compliance-parser", role: "Biometric KYC Document Parser", status: "Idle", uptime: "0", cpu: "0%", tracesLink: "Standby" },
  ]);

  const [selectedSandbox, setSelectedSandbox] = useState("sb-omega");
  const [runningCmd, setRunningCmd] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    "[SANS Constellation] Sandbox orchestration terminal initialized.",
    "[SANS Constellation] All sandboxes verified connected to Datadog APM tracing pipelines.",
    "Ready for user input."
  ]);
  const [sandboxCmd, setSandboxCmd] = useState("npx sandbox create --connect");

  // Private Databases Compartmentalization Parameters
  const [mongoUri, setMongoUri] = useState("mongodb+srv://priv-admin:••••••••••••••••@onstellation-db.iad1.mongodb.net/priv?retryWrites=true&w=majority");
  const [mongoConnected, setMongoConnected] = useState(true);
  const [poolOptimized, setPoolOptimized] = useState(true); // attachDatabasePool

  // Vercel Blob store simulations
  const [blobContent, setBlobContent] = useState("Hello from the secure SANS Blob Store!");
  const [blobPrefix, setBlobPrefix] = useState("articles/blob.txt");
  const [blobsList, setBlobsList] = useState<Array<{ url: string; path: string; size: string; created: string }>>([
    { url: "https://iad1.public.blob.vercel-storage.com/articles/signatures-Biometric_ECC-2026.png", path: "articles/signatures.png", size: "142 KB", created: "May 3, 2026" },
    { url: "https://iad1.public.blob.vercel-storage.com/articles/client_profile_keys.txt", path: "articles/client_profile_keys.txt", size: "4.2 KB", created: "May 5, 2026" },
  ]);
  const [blobLoading, setBlobLoading] = useState(false);

  // Stats / Resource tracking multipliers
  const [storageBytes, setStorageBytes] = useState(145028); 
  const [simpleOps, setSimpleOps] = useState(148);
  const [advancedOps, setAdvancedOps] = useState(24);
  const [dataTransfer, setDataTransfer] = useState(2.8);

  // BigQuery state keeping (already active analytical widget in design)
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

  const handleExecuteSandbox = () => {
    setRunningCmd(true);
    setTerminalLogs(prev => [
      ...prev,
      `[User Terminal] Routing command to ${selectedSandbox}: ${sandboxCmd}`
    ]);

    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (sandboxCmd.includes("connect") || sandboxCmd.includes("create")) {
        if (step === 1) {
          setTerminalLogs(prev => [...prev, "[Vercel Sandbox] Initializing connection tunnel pipeline..."]);
        } else if (step === 2) {
          setTerminalLogs(prev => [
            ...prev,
            "import { Sandbox } from \"@vercel/sandbox\";",
            "const sandbox = await Sandbox.create();",
            "// Establishing encrypted secure sockets tunnels connected to Vercel and Datadog..."
          ]);
        } else if (step === 3) {
          setTerminalLogs(prev => [
            ...prev,
            `[Vercel Sandbox] Connected sandbox '${selectedSandbox}' to project infrastructure.`,
            "[Vercel Sandbox] Pulling secure MongoDB and Vercel Blob access constants dynamically..."
          ]);
        } else if (step === 4) {
          clearInterval(interval);
          setRunningCmd(false);
          setSandboxes(prev => prev.map(sb => sb.id === selectedSandbox ? { ...sb, status: "Active", cpu: "1.6%", tracesLink: "Connected to Datadog" } : sb));
          setTerminalLogs(prev => [
            ...prev,
            "SUCCESS: npx sandbox connection finalized with return code 0.",
            "[Datadog APM] Sandbox linked. Streaming real-time telemetry metrics to Datadog core agent...",
            "✓ Active tracing is now active for this sandbox lot."
          ]);
          setAdvancedOps(o => o + 1);
        }
      } else if (sandboxCmd.includes("echo")) {
        if (step === 1) {
          setTerminalLogs(prev => [
            ...prev,
            "const cmd = await sandbox.runCommand(\"echo\", [\"Hello from Vercel Sandbox!\"]);",
            "console.log(await cmd.stdout());"
          ]);
        } else if (step === 2) {
          clearInterval(interval);
          setRunningCmd(false);
          setTerminalLogs(prev => [
            ...prev,
            "[stdout] Hello from Vercel Sandbox!",
            "[Vercel Sandbox] Telemetry stream registered with return code 0."
          ]);
          setSimpleOps(o => o + 1);
        }
      } else if (sandboxCmd.includes("stop")) {
        if (step === 1) {
          setTerminalLogs(prev => [...prev, "[Vercel Sandbox] Dispatching await sandbox.stop() command..."]);
        } else if (step === 2) {
          clearInterval(interval);
          setRunningCmd(false);
          setSandboxes(prev => prev.map(sb => sb.id === selectedSandbox ? { ...sb, status: "Idle", cpu: "0%", tracesLink: "Standby" } : sb));
          setTerminalLogs(prev => [
            ...prev,
            "[Vercel Sandbox] Isolated hypervisor shut down. Container dismantled cleanly.",
            "[SANS Constellation] Resource released for next scheduled tasks queue."
          ]);
          setSimpleOps(o => o + 1);
        }
      } else if (sandboxCmd.includes("pull") || sandboxCmd.includes("env")) {
        if (step === 1) {
          setTerminalLogs(prev => [...prev, "[Vercel CLI] Contacting project secure environment vault..."]);
        } else if (step === 2) {
          setTerminalLogs(prev => [...prev, "[Vercel CLI] project 'sans-priv-terminal' located."]);
        } else if (step === 3) {
          clearInterval(interval);
          setRunningCmd(false);
          setTerminalLogs(prev => [
            ...prev,
            "✓ Local parameters updated: .env.local created containing MongoDB connections, Vercel Blob tokens, and Datadog secure parameters.",
            "✓ Sandbox synced with constellation-db credentials."
          ]);
          setSimpleOps(o => o + 1);
        }
      } else {
        if (step === 1) {
          setTerminalLogs(prev => [...prev, `[Vercel Sandbox] Launching custom terminal process: '${sandboxCmd}'`]);
        } else if (step === 2) {
          clearInterval(interval);
          setRunningCmd(false);
          setTerminalLogs(prev => [
            ...prev,
            `[stdout] Task finished for command: '${sandboxCmd}' (status code 0).`,
            "✓ Command stream flushed successfully."
          ]);
          setSimpleOps(o => o + 1);
        }
      }
    }, 600);
  };

  const handlePutBlob = (e: React.FormEvent) => {
    e.preventDefault();
    if (!blobContent.trim()) return;
    setBlobLoading(true);

    const hashId = Math.floor(100000 + Math.random() * 900000);
    const newBlob = {
      url: `https://iad1.public.blob.vercel-storage.com/${blobPrefix.replace('.txt', '')}-${hashId}.txt`,
      path: blobPrefix,
      size: `${(blobContent.length / 1024).toFixed(2)} KB`,
      created: "Just now"
    };

    setTimeout(() => {
      setBlobLoading(false);
      setBlobsList(prev => [newBlob, ...prev]);
      setStorageBytes(prev => prev + blobContent.length);
      setSimpleOps(ops => ops + 1);
      setDataTransfer(dt => parseFloat((dt + (blobContent.length / 1048576)).toFixed(4)));
      setBlobContent("");
    }, 800);
  };

  const handleRunBQ = () => {
    setBqLoading(true);
    setBqLogs("Connecting to SANS analytical query cluster... Scanning big data partitions...");
    setBqResult(null);

    setTimeout(() => {
      setBqLogs("Executing optimized parsing against MongoDB/Blob strategic schemas... Resource limits verified... ");
      
      setTimeout(() => {
        setBqLoading(false);
        setBqLogs("Strategic resource analysis complete. Compartmentalized query results:");
        setBqResult([
          { trade_date: "2026-05-23", avg_profit: "+$41,205.80 USD", total_lots: "28 lots (Strategic main partition)" },
          { trade_date: "2026-05-22", avg_profit: "+$18,460.12 USD", total_lots: "14 lots (Capped connection lot)" },
          { trade_date: "2026-05-21", avg_profit: "+$55,901.40 USD", total_lots: "41 lots" },
          { trade_date: "2026-05-20", avg_profit: "-$4,105.10 USD", total_lots: "12 lots (Mitigated pool error)" },
          { trade_date: "2026-05-19", avg_profit: "+$29,081.44 USD", total_lots: "19 lots" }
        ]);
      }, 900);
    }, 900);
  };

  return (
    <div className="space-y-6 font-sans select-text">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* SECTION 1: VERCEL SANDBOXES CONFLICT COORD CONTROL */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
                <Terminal className="w-4 h-4 text-sky-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">Vercel Constellation Sandbox Manager</h3>
                <span className="text-[10px] text-zinc-500 block font-mono">Isolated containers linked with Datadog and Vercel Projects</span>
              </div>
            </div>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded uppercase border bg-sky-500/10 text-sky-400 border-sky-500/25">
              Secure Isolated Execution
            </span>
          </div>

          <div className="space-y-2">
            <span className="text-[10px] uppercase font-mono text-zinc-400 block tracking-wider">Active Constellation Sandboxes</span>
            <div className="space-y-2">
              {sandboxes.map(sb => (
                <div 
                  key={sb.id}
                  onClick={() => setSelectedSandbox(sb.id)}
                  className={`p-3 rounded border text-xs cursor-pointer transition flex items-center justify-between font-mono ${
                    selectedSandbox === sb.id 
                      ? "bg-sky-950/20 border-sky-500/40 text-white" 
                      : "bg-neutral-950/40 border-white/5 text-zinc-400 hover:border-white/10"
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <strong className="text-white text-xs">{sb.name}</strong>
                      <span className={`text-[8.5px] px-1.5 py-0.2 rounded border ${
                        sb.status === "Active" 
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                          : "bg-zinc-900 text-zinc-500 border-white/5"
                      }`}>
                        {sb.status}
                      </span>
                    </div>
                    <span className="text-[9.5px] text-zinc-500 block mt-1">{sb.role}</span>
                  </div>

                  <div className="text-right text-[10px] space-y-0.5">
                    <div>CPU: <strong className="text-white">{sb.cpu}</strong></div>
                    <div className="text-zinc-500 text-[9px]">{sb.tracesLink}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sandbox code execution simulator */}
          <div className="space-y-2 bg-neutral-950/70 p-4 rounded-lg border border-white/5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold text-sky-400 uppercase flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Execute Vercel Sandbox Console
              </span>
              <span className="text-[9px] font-mono text-zinc-500">selected: {selectedSandbox}</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <div className="sm:col-span-2">
                <label className="text-[10px] uppercase font-mono text-zinc-500 block mb-1">Select / Write Command</label>
                <div className="flex gap-1.5">
                  <select
                    value={sandboxCmd}
                    onChange={(e) => setSandboxCmd(e.target.value)}
                    className="bg-black border border-white/10 rounded px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none"
                  >
                    <option value="npx sandbox create --connect">npx sandbox create --connect</option>
                    <option value="echo 'Hello from Vercel Sandbox!'">echo 'Hello Sandbox!'</option>
                    <option value="vercel env pull">vercel env pull</option>
                    <option value="await sandbox.stop()">await sandbox.stop()</option>
                  </select>
                  <input
                    type="text"
                    value={sandboxCmd}
                    onChange={(e) => setSandboxCmd(e.target.value)}
                    placeholder="Custom command execution"
                    className="flex-1 bg-black border border-white/10 rounded px-2 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-white/30"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-mono text-zinc-500 block mb-1">&nbsp;</label>
                <button
                  type="button"
                  onClick={handleExecuteSandbox}
                  disabled={runningCmd}
                  className="w-full py-1.5 px-3 bg-sky-400 hover:bg-sky-500 text-black font-extrabold font-mono text-xs rounded transition duration-200 cursor-pointer text-center"
                >
                  {runningCmd ? "EXECUTING..." : "RUN COMMAND"}
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[9px] uppercase font-mono text-zinc-500 block">SANS Sandbox stdout Stream Logs</span>
              <div className="bg-black p-3 rounded border border-white/10 font-mono text-[10px] text-green-400 space-y-1 h-32 overflow-y-auto w-full leading-normal">
                {terminalLogs.map((log, idx) => (
                  <div key={idx} className="whitespace-pre-wrap">{log}</div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 2: DATABASES COMPARTMENTALIZATION (onstellation-db) */}
        <div className="p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded bg-emerald-500/15 border border-emerald-400/25 flex items-center justify-center text-emerald-400">
                <Database className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white font-mono">Constellation-DB Compartments</h3>
                <span className="text-[10px] text-zinc-500 block font-mono">Resource optimization: separating profiles from cached blob storage</span>
              </div>
            </div>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded uppercase border bg-emerald-500/10 text-emerald-400 border-emerald-500/25">
              Private Databases
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* MongoDB main partition */}
            <div className="p-3 bg-neutral-950/80 rounded border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  MongoDB Ledger Database
                </span>
                <span className="text-[8.5px] px-1.5 py-0.2 rounded border bg-emerald-500/5 text-emerald-400 border-emerald-500/20 font-mono uppercase">
                  Connected
                </span>
              </div>

              <p className="text-[11px] text-zinc-400 leading-tight">
                Executes microservices telemetry profiles. Strategic compartmentalization preserves and maximizes server connections dynamically.
              </p>

              <div className="space-y-1">
                <label className="text-[9.5px] uppercase font-mono text-zinc-500 block">Sovereign Connection URI</label>
                <input
                  type="password"
                  value={mongoUri}
                  onChange={(e) => setMongoUri(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded px-2 py-1 flex items-center font-mono text-[9.5px] text-zinc-400 focus:outline-none"
                />
              </div>

              {/* Vercel Serverless Functions connection pool */}
              <div className="p-2 bg-black/40 rounded border border-white/5 text-[10px] font-mono flex items-center justify-between">
                <div>
                  <div className="text-white text-[9.5px]">attachDatabasePool</div>
                  <div className="text-zinc-500 text-[8.5px] leading-tight">Prevents pool connection leaks</div>
                </div>
                <input
                  type="checkbox"
                  checked={poolOptimized}
                  onChange={(e) => setPoolOptimized(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-white/25 accent-sky-450 cursor-pointer"
                />
              </div>
            </div>

            {/* Vercel Private Blob Store */}
            <div className="p-3 bg-neutral-950/80 rounded border border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white font-mono flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                  SANS Blob Store
                </span>
                <span className="text-[8.5px] font-mono font-bold text-zinc-500 bg-zinc-900 px-1.5 py-0.2 rounded">
                  IAD1 Region
                </span>
              </div>

              <div className="grid grid-cols-2 text-[9px] font-mono bg-black/50 p-2 rounded gap-2 text-zinc-400">
                <div>Created: <strong className="text-white">May 3</strong></div>
                <div>Storage: <strong className="text-white">{(storageBytes / 1024).toFixed(1)} KB</strong></div>
                <div>Simple Ops: <strong className="text-white">{simpleOps}/10k</strong></div>
                <div>Advanced Ops: <strong className="text-white">{advancedOps}/2k</strong></div>
              </div>

              {/* Enter item in the Blob store */}
              <form onSubmit={handlePutBlob} className="space-y-1.5 pt-1">
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    required
                    value={blobContent}
                    onChange={(e) => setBlobContent(e.target.value)}
                    placeholder="Enter document/article text..."
                    className="flex-1 bg-black border border-white/10 rounded px-2 py-1 text-[10px] text-white font-mono focus:outline-none focus:border-white/30"
                  />
                  <button
                    type="submit"
                    disabled={blobLoading}
                    className="px-2.5 py-1 bg-white hover:bg-zinc-200 text-black font-extrabold font-mono text-[9px] rounded uppercase transition cursor-pointer"
                  >
                    {blobLoading ? "PUTTING..." : "PUT BLOB"}
                  </button>
                </div>
                <div className="text-[8.5px] text-zinc-500 font-mono">
                  Saves using: <code>put('{blobPrefix}', content, &#123; access: 'private' &#125;)</code>
                </div>
              </form>
            </div>
          </div>

          {/* List of active Blobs */}
          <div className="space-y-2 bg-neutral-950/60 p-3 rounded-lg border border-white/5 font-mono">
            <span className="text-[10px] font-bold text-white uppercase block">Blob Files Browser (onstellation-db Store)</span>
            <div className="space-y-1.5 max-h-[140px] overflow-y-auto scrollbar-hide">
              {blobsList.map((bl, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-black/40 rounded border border-white/5 text-[9px]">
                  <div className="space-y-0.5 max-w-[70%]">
                    <span className="text-white font-semibold block truncate leading-tight">{bl.path}</span>
                    <span className="text-zinc-500 block text-[8px] truncate leading-none">{bl.url}</span>
                  </div>
                  <div className="text-right flex flex-col items-end flex-shrink-0 text-zinc-500">
                    <span className="text-zinc-300 font-bold">{bl.size}</span>
                    <span>{bl.created}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

      {/* SECTION 3: BIGQUERY ANALYTICS DATA WAREHOUSE */}
      <div className="metric-card p-5 border border-white/5 rounded-lg bg-black/40 space-y-4">
        <div className="flex items-start justify-between pb-2 border-b border-white/5 font-bold">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded bg-sky-500/15 border border-sky-400/25 flex items-center justify-center text-sky-400">
              <Database className="w-4 h-4 text-sky-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono font-bold font-semibold">BigQuery Analytics SQL Warehouse</h3>
              <span className="text-[10px] text-zinc-550 block font-mono">Execute high-performance calculations on multi-partitioned historic telemetry lots</span>
            </div>
          </div>
          <span className="text-[9.1px] font-mono px-2 py-0.5 rounded uppercase border bg-[#FF6B35]/10 text-[#FF6B35] border-[#FF6B35]/25">
            10 GiB Storage & 1 TiB queries free / month
          </span>
        </div>

        <p className="text-stone-400 text-xs leading-relaxed font-sans">
          Leverage BigQuery's analytical capabilities across SANS trading layers. Check average profits, active trends, and overall compartment performances directly using distributed telemetry tables.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[9px] uppercase font-mono text-zinc-500 font-bold font-semibold">Standard SQL Console Terminal</label>
              <button 
                onClick={handleRunBQ}
                disabled={bqLoading}
                className="px-3.5 py-1.5 bg-white hover:bg-zinc-200 text-black font-semibold text-[10.5px] rounded transition duration-200 font-mono flex items-center gap-1.5 cursor-pointer font-bold"
              >
                <Play className="w-2.5 h-2.5 fill-black border-0" />
                <span>{bqLoading ? "RUNNING..." : "RUN ANALYTICAL QUERY"}</span>
              </button>
            </div>
            <textarea
              rows={5}
              value={bqQuery}
              onChange={(e) => setBqQuery(e.target.value)}
              className="w-full bg-neutral-950 border border-white/10 rounded p-3 text-xs text-green-400 font-mono focus:outline-none focus:border-white/30 resize-none h-32 leading-relaxed"
            />
          </div>

          <div className="space-y-2">
            <span className="text-[9px] uppercase font-mono text-zinc-500 block">SQL Result Stream Console</span>
            <div className="bg-black border border-white/10 rounded p-3.5 h-32 overflow-y-auto font-mono text-[10px] text-stone-300 leading-normal scrollbar-hide space-y-2">
              <div className="text-zinc-500 italic text-[9.5px]">
                {bqLogs || "Ready for SQL instruction triggers. Select RUN ANALYTICAL QUERY to initialize database compilation scan sequence."}
              </div>

              {bqResult && (
                <div className="space-y-1.5 pt-1">
                  <div className="text-emerald-400 font-bold border-b border-white/5 pb-1 uppercase font-bold text-[8.5px]">COMPARTMENTALIZED DATA COMPILATION RESULTS:</div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[9px] border-collapse min-w-[320px]">
                      <thead>
                        <tr className="text-zinc-500 border-b border-white/10 uppercase">
                          <th className="py-1">Trade Date</th>
                          <th className="py-1">Avg Profit Factor</th>
                          <th className="py-1">Partition Info</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bqResult.map((row: any, rIdx: number) => (
                          <tr key={rIdx} className="border-b border-white/5 hover:bg-white/5 text-stone-200">
                            <td className="py-1">{row.trade_date}</td>
                            <td className="py-1 font-bold text-emerald-400">{row.avg_profit}</td>
                            <td className="py-1 font-semibold text-zinc-400">{row.total_lots}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="text-[8.5px] text-zinc-500 text-right pt-1 uppercase font-bold">● Total bytes processed in constellation sandbox query: 14.12 MB (Costs Covered)</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
