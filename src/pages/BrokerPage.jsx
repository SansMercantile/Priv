import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/apiClient';

const BROKER_OPTIONS = [
  { id: 'xm', name: 'XM Global', types: ['live', 'demo'] },
  { id: 'alpaca', name: 'Alpaca', types: ['live', 'paper'] },
  { id: 'binance', name: 'Binance', types: ['live', 'testnet'] },
  { id: 'deriv', name: 'Deriv', types: ['live', 'demo'] },
];

export default function BrokerPage({ demoMode }) {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (demoMode) {
      setConnections([
        { broker_name: 'XM Global (Demo)', status: 'connected', account_type: 'demo' },
      ]);
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const resp = await apiClient.getBrokerConnections();
        setConnections(resp?.data?.brokers || resp?.brokers || []);
      } catch (e) {
        console.error(e);
        setConnections([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [demoMode]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-serif italic text-white">Broker & Trading Accounts</h1>
        <p className="text-white/40 text-xs mt-1 font-light">
          {demoMode
            ? 'Simulated broker linkage for the terminal UI.'
            : 'Connect a live or broker-provided demo account so Priv can run market analysis, risk, and execution.'}
        </p>
      </div>

      {!demoMode && (
        <Link
          to="/dashboard/broker-connect"
          className="inline-flex items-center px-4 py-2 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 text-xs font-mono font-semibold hover:bg-emerald-500/20"
        >
          Connect API keys →
        </Link>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {BROKER_OPTIONS.map((b) => (
          <div key={b.id} className="metric-card p-5 rounded border border-white/10">
            <h3 className="font-mono text-sm text-white font-bold">{b.name}</h3>
            <p className="text-[10px] text-white/40 mt-1 font-mono">
              Supports: {b.types.join(', ')}
            </p>
          </div>
        ))}
      </div>

      <div className="metric-card p-6 rounded border border-white/10">
        <h3 className="text-sm font-serif italic text-white mb-4">Active connections</h3>
        {loading ? (
          <p className="text-xs font-mono text-white/40">Loading…</p>
        ) : connections.length === 0 ? (
          <p className="text-xs font-mono text-amber-400/90">
            No broker connected. Use Broker Connect to add credentials (stored as masked metadata server-side).
          </p>
        ) : (
          <ul className="space-y-2">
            {connections.map((c, i) => (
              <li key={i} className="flex justify-between text-xs font-mono text-white/70 border-b border-white/5 pb-2">
                <span>{c.broker_name}</span>
                <span className="text-emerald-400">{c.status || 'connected'}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
