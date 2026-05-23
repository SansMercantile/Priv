import React, { useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

export default function AlertsPage({ demoMode }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (demoMode) {
      setAlerts([
        { id: 'DEMO-1', message: 'Sample volatility alert (demo only)', severity: 'medium' },
        { id: 'DEMO-2', message: 'Sample margin utilization (demo only)', severity: 'low' },
      ]);
      setLoading(false);
      return;
    }
    setLoading(true);
    apiClient
      .getTradeAlerts()
      .then((resp) => setAlerts(resp?.data?.alerts || resp?.alerts || []))
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false));
  }, [demoMode]);

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-serif italic text-white">Alerts & Notifications</h1>
      <p className="text-white/40 text-xs font-light">
        {demoMode ? 'Simulated alerts' : 'Live trading alerts from /api/v1/trading/alerts'}
      </p>
      {loading ? (
        <p className="text-xs font-mono text-white/40">Loading…</p>
      ) : alerts.length === 0 ? (
        <p className="text-xs font-mono text-white/40">No active alerts.</p>
      ) : (
        <ul className="space-y-2">
          {alerts.map((a, i) => (
            <li key={a.id || i} className="metric-card p-3 rounded border border-white/10 text-xs text-white/80">
              {a.message || JSON.stringify(a)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
