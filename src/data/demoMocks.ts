/**
 * Centralized mock data — import ONLY from demo-mode code paths.
 */

export const DEMO_HISTORY_RECORDS = [
  {
    id: 'TX-9081',
    timestamp: '2026-05-20 11:42:15',
    agent: 'Quant-Alpha-7',
    action: 'Autonomous triangular Arbitrage execution on USDT/ZAR layout',
    status: 'Success' as const,
    executionTime: '82ms',
    node: 'SM-PRV-9',
  },
  {
    id: 'TX-9080',
    timestamp: '2026-05-20 11:39:04',
    agent: 'Tax-Shield',
    action: 'SARS corporate transfer clearance e-Filing certificate authentication',
    status: 'Success' as const,
    executionTime: '340ms',
    node: 'SM-PRV-9',
  },
  {
    id: 'TX-9079',
    timestamp: '2026-05-20 10:14:55',
    agent: 'Risk-Guardian',
    action: 'Volatility limit threshold verification: spot exposure limited to 2x leverage limit',
    status: 'Flagged' as const,
    executionTime: '12ms',
    node: 'SM-PRV-9',
  },
  {
    id: 'TX-9078',
    timestamp: '2026-05-20 09:51:22',
    agent: 'Sentiment-Oracle',
    action: 'Ingested FOMC policy speech transcript. Stance coefficient updated to +0.84',
    status: 'Success' as const,
    executionTime: '1.24s',
    node: 'SM-PRV-9-CLUSTER',
  },
  {
    id: 'TX-9077',
    timestamp: '2026-05-20 08:31:10',
    agent: 'Execution-Lightning',
    action: 'Route block commodity spread order validation (SARS/SADC exemption checked)',
    status: 'Success' as const,
    executionTime: '95ms',
    node: 'SM-PRV-9',
  },
  {
    id: 'TX-9076',
    timestamp: '2026-05-20 07:11:03',
    agent: 'Risk-Guardian',
    action: 'Exception triggered on alternative commodities arbitrage node line coupling feed',
    status: 'Exception' as const,
    executionTime: '22ms',
    node: 'SM-PRV-5',
  },
];

export const DEMO_CONNECTION_NODES = [
  { id: 'node-1', name: 'SANS-PRV-9-AMS', location: 'Amsterdam, NL', status: 'Online' as const, ping: '12ms', inletsCount: 4 },
  { id: 'node-2', name: 'SANS-PRV-9-LDN', location: 'London, UK', status: 'Online' as const, ping: '18ms', inletsCount: 3 },
  { id: 'node-3', name: 'SANS-PRV-9-JHB', location: 'Johannesburg, ZA', status: 'Online' as const, ping: '38ms', inletsCount: 6 },
  { id: 'node-4', name: 'SANS-PRV-9-SGP', location: 'Singapore, SG', status: 'Syncing' as const, ping: '128ms', inletsCount: 2 },
  { id: 'node-5', name: 'SANS-PRV-9-ZUR', location: 'Zurich, CH', status: 'Idle' as const, ping: '15ms', inletsCount: 0 },
];

export const DEMO_NEWS_ARTICLES = [
  {
    id: 1,
    title: 'Global Supply Chain Congestion Prompts Autonomous Arbitrage Influx',
    source: 'SANS Intelligence Branch',
    time: '12m ago',
    sentiment: 'Bullish' as const,
    summary: 'Quantitative Arbitrage clusters initiated short-term spread maneuvers across SADC maritime carriers.',
    readTime: '3 min read',
    tags: ['Arbitrage', 'Logistics', 'Volume'],
  },
  {
    id: 2,
    title: 'Federal Reserve Board Signals Volatility Constraints Adjustment',
    source: 'Financial Times Core',
    time: '1h ago',
    sentiment: 'Neutral' as const,
    summary: 'Simulated market strategies predict micro-adjustments following adjusted inflation outlooks.',
    readTime: '5 min read',
    tags: ['Macro', 'Execution', 'Fed'],
  },
  {
    id: 3,
    title: 'GRA Announces Algorithmic Custom Exemption Verification Standard',
    source: 'Ghana Revenue Service Gate',
    time: '3h ago',
    sentiment: 'Bullish' as const,
    summary: 'New algorithmic customs declarations allow local nodes to autonomously apply for tax clearance exemptions.',
    readTime: '4 min read',
    tags: ['Tax', 'Compliance', 'GRA'],
  },
  {
    id: 4,
    title: 'Unprecedented Volume Spike Detected in Synthetic Bond Swaps',
    source: 'SANS Sovereign Node 3',
    time: '5h ago',
    sentiment: 'Bullish' as const,
    summary: 'Alternative Sentiment models captured rapid reallocation patterns into collateralized sovereign yielding assets.',
    readTime: '2 min read',
    tags: ['Volume', 'Bonds', 'Sovereign'],
  },
];

export const DEMO_TERMINAL_ARTICLES = [
  { title: 'EUR/USD consolidates ahead of ECB', source: 'Demo Feed', time: '5m ago', snip: 'Range-bound ahead of policy decision.' },
  { title: 'Gold holds support at key level', source: 'Demo Feed', time: '12m ago', snip: 'Safe-haven bid on macro uncertainty.' },
  { title: 'Tech sector leads risk-on session', source: 'Demo Feed', time: '28m ago', snip: 'Index futures track higher in pre-market.' },
];

export const DEMO_TWITTER_FEEDS = [
  { username: 'ZeroHedge', content: 'Macro liquidity stress thresholds — demo only.', time: '4m ago', sentiment: 'Bearish' },
  { username: 'XM_Markets', content: 'FOMC forecast demo headline.', time: '18m ago', sentiment: 'Neutral' },
  { username: 'SANS_Mercantile', content: 'PRIV Core demo execution logs.', time: '1h ago', sentiment: 'Bullish' },
];

export const DEMO_DASHBOARD_STATS = {
  totalProfit: 2847392.45,
  dailyReturn: 12.34,
  activeAgents: 12,
  dataPoints: 847392,
  riskScore: 23.5,
  executionSpeed: 0.003,
};

export const DEMO_POSITIONS = [
  { instrument: 'S&P 500 CFD', type: 'Buy', quantity: 1225, entryPrice: 4100.5, currentPrice: 4150.2, profitLoss: 6570 },
  { instrument: 'EUR/USD', type: 'Sell', quantity: 100000, entryPrice: 1.105, currentPrice: 1.095, profitLoss: 1000 },
];
