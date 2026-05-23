import React, { useState, useEffect } from "react";
import { Link2, Globe, Server, Radio, ShieldCheck, Play, ArrowRight, Activity } from "lucide-react";
import apiClient from "../api/apiClient";
import { DEMO_CONNECTION_NODES } from "../data/demoMocks";

interface ConnectionNode {
  id: string;
  name: string;
  location: string;
  status: "Online" | "Idle" | "Syncing";
  ping: string;
  inletsCount: number;
}

export default function Connections({ demoMode }: { demoMode?: boolean }) {
  const [nodes, setNodes] = useState<ConnectionNode[]>([]);
  const [activeGateway, setActiveGateway] = useState("Rest API Gate");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      if (demoMode) {
        if (!cancelled) {
          setNodes(DEMO_CONNECTION_NODES);
          setLoading(false);
        }
        return;
      }
      try {
        const resp = await apiClient.getBrokerConnections();
        const brokers = resp?.data?.brokers || resp?.brokers || [];
        const mapped: ConnectionNode[] = brokers.map(
          (b: { id?: string; broker_name?: string; status?: string; region?: string }, i: number) => ({
            id: b.id || `broker-${i}`,
            name: b.broker_name || "Broker",
            location: b.region || "Connected",
            status: b.status === "connected" ? "Online" : b.status === "syncing" ? "Syncing" : "Idle",
            ping: "—",
            inletsCount: 1,
          })
        );
        if (!cancelled) setNodes(mapped);
      } catch (e) {
        console.error(e);
        if (!cancelled) setNodes([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [demoMode]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <Radio className="w-8 h-8 mr-3 text-white/75 animate-pulse" />
            Cluster Node Interconnections
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            {demoMode
              ? "Simulated SANS network topology"
              : "Live broker and API gateway connections from /api/v1/connections"}
          </p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded font-mono text-xs text-emerald-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{demoMode ? "DEMO TOPOLOGY" : "LIVE CONNECTIONS"}</span>
        </div>
      </div>

      {!demoMode && nodes.length === 0 && !loading && (
        <div className="metric-card p-6 rounded border border-amber-500/30 text-amber-200/90 text-sm">
          No broker connected yet.{" "}
          <a href="/dashboard/broker-connect" className="underline font-semibold">
            Connect your trading account
          </a>{" "}
          (live or broker demo) to enable market analysis and execution routing.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 text-center text-white/40 font-mono text-xs py-8">Loading connections…</div>
        ) : (
          nodes.map((node) => (
            <div key={node.id} className="metric-card p-6 rounded border border-white/10 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-mono text-sm text-white font-bold">{node.name}</h3>
                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded ${
                      node.status === "Online"
                        ? "bg-emerald-500/10 text-emerald-400"
                        : node.status === "Syncing"
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-zinc-500/10 text-zinc-400"
                    }`}
                  >
                    {node.status}
                  </span>
                </div>
                <p className="text-xs text-white/50 flex items-center mb-2">
                  <Globe className="w-3 h-3 mr-1" />
                  {node.location}
                </p>
                <p className="text-[10px] font-mono text-white/40">Ping: {node.ping}</p>
              </div>
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                <span className="text-[10px] font-mono text-white/50">{node.inletsCount} active inlets</span>
                <Activity className="w-4 h-4 text-white/30" />
              </div>
            </div>
          ))
        )}
      </div>

      <div className="metric-card p-6 rounded border border-white/10">
        <h3 className="text-sm font-serif italic text-white mb-4 flex items-center">
          <Server className="w-4 h-4 mr-2" />
          Gateway Router Protocols
        </h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {["Rest API Gate", "WebSocket Stream", "FIX 4.4", "OAuth Broker"].map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => setActiveGateway(g)}
              className={`px-3 py-1.5 rounded text-[10px] font-mono border ${
                activeGateway === g ? "bg-white/10 border-white/25 text-white" : "border-white/10 text-zinc-500"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between text-xs text-white/50 font-mono">
          <span className="flex items-center">
            <Link2 className="w-3 h-3 mr-1" />
            Active: {activeGateway}
          </span>
          <button type="button" className="flex items-center text-white hover:text-white/80">
            <Play className="w-3 h-3 mr-1" />
            Test handshake
            <ArrowRight className="w-3 h-3 ml-1" />
          </button>
        </div>
        {!demoMode && (
          <input
            placeholder="https://api.sansmercantile.com/v1"
            className="w-full mt-4 bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-white/30 font-mono"
            defaultValue={import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000"}
            readOnly
          />
        )}
      </div>
    </div>
  );
}
