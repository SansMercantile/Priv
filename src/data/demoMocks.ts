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

/**
 * Demo User Profile - Only used in DEMO MODE
 */
export const DEMO_USER_PROFILE = {
  id: 'demo-user-123',
  email: 'demo@sansmercantile.com',
  full_name: 'Demo User',
  display_name: 'Demo Trader',
  preferred_agents: ['Quant-Alpha-7', 'Risk-Guardian', 'Tax-Shield'],
  tax_residency: 'ZA',
  trading_knowledge: 'Intermediate',
  trading_appetite: 'Moderate',
  goals: ['Long-term growth', 'Passive income'],
  profile_picture: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="%23FF6B35"/></svg>',
  kyc_status: 'verified',
  account_type: 'demo',
};

/**
 * Demo KYC Status - Only used in DEMO MODE
 */
export const DEMO_KYC_STATUS = {
  status: 'verified',
  verification_date: '2026-05-15',
  personal_info_verified: true,
  identity_document_verified: true,
  address_verified: true,
  financial_profile_verified: true,
  trading_profile_verified: true,
};

/**
 * Demo Portfolio Alerts
 */
export const DEMO_ALERTS = [
  {
    id: 'alert-001',
    type: 'price_movement',
    symbol: 'SPX',
    message: 'S&P 500 reached support level',
    severity: 'warning',
    timestamp: '2026-05-20 14:30:00',
    read: false,
  },
  {
    id: 'alert-002',
    type: 'agent_action',
    message: 'Risk-Guardian executed volatility hedge',
    severity: 'info',
    timestamp: '2026-05-20 14:15:00',
    read: false,
  },
  {
    id: 'alert-003',
    type: 'system',
    message: 'Demo mode data refreshed (15 min delayed)',
    severity: 'info',
    timestamp: '2026-05-20 14:00:00',
    read: true,
  },
];

/**
 * Demo Broker Connections
 */
export const DEMO_BROKER_CONNECTIONS = [
  {
    id: 'broker-demo-1',
    broker_name: 'Interactive Brokers',
    account_type: 'Paper Trading',
    account_number: 'DEMO123456',
    status: 'connected',
    connected_date: '2026-05-15',
    is_demo: true,
  },
];

/**
 * Demo Trading History
 */
export const DEMO_TRADING_HISTORY = [
  {
    id: 'trade-001',
    symbol: 'SPX',
    direction: 'BUY',
    quantity: 10,
    entry_price: 4100.5,
    exit_price: 4150.2,
    profit_loss: 497.0,
    date: '2026-05-18',
    agent: 'Quant-Alpha-7',
  },
  {
    id: 'trade-002',
    symbol: 'EURUSD',
    direction: 'SELL',
    quantity: 100000,
    entry_price: 1.105,
    exit_price: 1.095,
    profit_loss: 1000.0,
    date: '2026-05-17',
    agent: 'Sentiment-Oracle',
  },
  {
    id: 'trade-003',
    symbol: 'GOLD',
    direction: 'BUY',
    quantity: 100,
    entry_price: 1960.1,
    exit_price: 1975.5,
    profit_loss: 1540.0,
    date: '2026-05-16',
    agent: 'Risk-Guardian',
  },
];

/**
 * Demo Risk Analysis
 */
export const DEMO_RISK_ANALYSIS = {
  portfolio_var: 15234.50,
  value_at_risk_percentage: 2.3,
  max_drawdown: -12.5,
  sharpe_ratio: 1.85,
  diversification_score: 82,
  largest_position: 'S&P 500 CFD',
  largest_position_pct: 45.2,
  concentration_risk: 'Moderate',
  leverage_used: 1.5,
  margin_available: 250000,
};
