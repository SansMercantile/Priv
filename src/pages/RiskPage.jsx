import React, { useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

export default function RiskPage({ demoMode }) {
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(!demoMode);

  useEffect(() => {
    if (demoMode) return;
    setLoading(true);
    apiClient
      .getRiskAnalysis()
      .then(setRisk)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [demoMode]);

  if (demoMode) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-serif italic text-white">Risk Analysis</h1>
        <p className="text-white/50 text-xs font-mono">
          Demo mode — connect a live account for real exposures via /api/v1/risk.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-serif italic text-white">Risk Analysis</h1>
      {loading ? (
        <p className="text-white/40 text-xs font-mono">Loading risk metrics…</p>
      ) : risk ? (
        <pre className="metric-card p-4 rounded border border-white/10 text-[10px] font-mono text-white/70 overflow-auto max-h-96">
          {JSON.stringify(risk, null, 2)}
        </pre>
      ) : (
        <p className="text-amber-400/90 text-xs font-mono">
          No risk data yet. Connect a broker account to enable portfolio risk analysis.
        </p>
      )}
    </div>
  );
}
