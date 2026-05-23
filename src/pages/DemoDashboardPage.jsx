
import React, { useState } from 'react';
import RealTimeDashboard from '../components/dashboard/RealTimeDashboard';

// Extensive mock data generator
function generateDemoData() {
  // 5 days (120 hours) of hourly positions
  const hours = 24 * 5;
  const positions = [];
  let baseValue = 100000;
  for (let i = 0; i < hours; i++) {
    const value = baseValue + Math.sin(i / 12) * 2000 + Math.random() * 500 - 250;
    const sentiment = 0.5 + 0.4 * Math.sin(i / 18) + (Math.random() - 0.5) * 0.1;
    positions.push({
      symbol: ['AAPL', 'TSLA', 'GOOG', 'MSFT', 'AMZN'][i % 5],
      quantity: 10 + (i % 50),
      currentPrice: value / 1000 + (i % 5) * 2,
      pnl: value - baseValue,
      changePercent: ((value - baseValue) / baseValue) * 100,
      value,
      sentiment: Math.max(0, Math.min(1, sentiment)),
    });
    baseValue = value;
  }
  // Extensive agent decisions
  const decisions = Array.from({ length: 20 }, (_, i) => ({
    agent: ['AlphaTrader', 'BetaBot', 'GammaAI', 'DeltaCore'][i % 4],
    action: ['BUY', 'SELL'][i % 2],
    symbol: ['AAPL', 'TSLA', 'GOOG', 'MSFT', 'AMZN'][i % 5],
    confidence: 0.7 + Math.random() * 0.3,
    timestamp: Date.now() - i * 3600 * 1000,
  }));
  // Extensive alerts
  const alerts = [
    { message: 'TSLA volatility spike', severity: 'warning', timestamp: Date.now() },
    { message: 'AAPL earnings report', severity: 'info', timestamp: Date.now() },
    { message: 'GOOG regulatory news', severity: 'critical', timestamp: Date.now() },
    { message: 'MSFT dividend update', severity: 'info', timestamp: Date.now() },
    { message: 'AMZN supply chain issue', severity: 'warning', timestamp: Date.now() },
  ];
  return {
    portfolio: {
      totalValue: positions[positions.length - 1].value,
      dailyChange: positions[positions.length - 1].value - positions[positions.length - 25].value,
      dailyChangePercent: ((positions[positions.length - 1].value - positions[positions.length - 25].value) / positions[positions.length - 25].value) * 100,
      positions,
    },
    market: {
      indices: [
        { name: 'S&P 500', value: 4500, change: 0.5 },
        { name: 'NASDAQ', value: 15000, change: 0.7 }
      ],
      alerts,
      sentiment: positions[positions.length - 1].sentiment > 0.7 ? 'bullish' : positions[positions.length - 1].sentiment < 0.3 ? 'bearish' : 'neutral',
    },
    agents: {
      active: 3,
      total: 5,
      performance: 0.92,
      decisions,
    },
    system: {
      health: 'good',
      uptime: 86400,
      threats: 0,
      performance: 0.99
    }
  };
}

export default function DemoDashboardPage({ user, signOutUser }) {
  const [demoData] = useState(generateDemoData());
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 bg-gray-100 border-b">
        <h2 className="text-xl font-bold">Demo Mode</h2>
        <span className="text-sm font-medium text-green-600">Simulated Data</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        <RealTimeDashboard demoMode={true} demoData={demoData} />
      </div>
    </div>
  );
}
