import React, { useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

export default function InsightsPage({ demoMode }) {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    if (demoMode) return;
    apiClient
      .get('/api/v1/insights')
      .then(setInsights)
      .catch(() => apiClient.get('/api/v1/market-insights').then(setInsights).catch(console.error));
  }, [demoMode]);

  if (demoMode) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-serif italic text-white">Market Insights</h1>
        <p className="text-white/50 text-xs font-mono">Demo placeholder — live insights require broker connection.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-serif italic text-white">Market Insights</h1>
      {insights ? (
        <pre className="metric-card p-4 rounded border border-white/10 text-[10px] font-mono text-white/70 overflow-auto max-h-[32rem]">
          {JSON.stringify(insights, null, 2)}
        </pre>
      ) : (
        <p className="text-xs font-mono text-white/40">Loading insights from backend…</p>
      )}
    </div>
  );
}
