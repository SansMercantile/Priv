/**
 * Data Fetcher Utility
 * Intelligently routes data requests to mock data (demo) or real APIs (live)
 * This ensures demo data is ONLY available in demo mode
 */

import {
  DEMO_HISTORY_RECORDS,
  DEMO_CONNECTION_NODES,
  DEMO_NEWS_ARTICLES,
  DEMO_DASHBOARD_STATS,
  DEMO_POSITIONS,
  DEMO_ALERTS,
  DEMO_BROKER_CONNECTIONS,
  DEMO_TRADING_HISTORY,
  DEMO_RISK_ANALYSIS,
  DEMO_USER_PROFILE,
  DEMO_KYC_STATUS,
} from '../data/demoMocks';

export interface DataFetchOptions {
  demoMode: boolean;
  apiBaseUrl?: string;
  userId?: string;
  timeout?: number;
}

/**
 * Fetch portfolio positions
 * In demo mode: returns mock data
 * In live mode: calls backend API
 */
export async function fetchPortfolioPositions(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_POSITIONS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/portfolio/positions`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching portfolio positions:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch trading history
 */
export async function fetchTradingHistory(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_TRADING_HISTORY };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/portfolio/history`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching trading history:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch risk analysis
 */
export async function fetchRiskAnalysis(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_RISK_ANALYSIS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/risk/analysis`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching risk analysis:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch alerts
 */
export async function fetchAlerts(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_ALERTS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/trading/alerts`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch user profile
 */
export async function fetchUserProfile(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_USER_PROFILE };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/profile`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch KYC status
 */
export async function fetchKycStatus(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_KYC_STATUS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/kyc/status`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching KYC status:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch broker connections
 */
export async function fetchBrokerConnections(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_BROKER_CONNECTIONS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/trading/connections`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching broker connections:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch connection nodes
 */
export async function fetchConnectionNodes(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_CONNECTION_NODES };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/system/nodes`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching connection nodes:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch execution history (transactions)
 */
export async function fetchExecutionHistory(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_HISTORY_RECORDS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/history`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching execution history:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch news articles
 */
export async function fetchNews(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_NEWS_ARTICLES };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/news`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching news:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Fetch dashboard statistics
 */
export async function fetchDashboardStats(options: DataFetchOptions) {
  if (options.demoMode) {
    return { success: true, data: DEMO_DASHBOARD_STATS };
  }
  
  try {
    const response = await fetch(`${options.apiBaseUrl || '/api/v1'}/portfolio/stats`, {
      headers: { 'X-User-Id': options.userId || 'anonymous' },
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}
