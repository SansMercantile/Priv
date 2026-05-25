/**
 * PRIV Platform - MongoDB Trading Compartmentalization
 * 6 independent trading databases with strategic compartmentalization
 */

import { MongoClient, Db, Collection } from "mongodb";

export const TRADING_COMPARTMENTS = {
  MARKET_DATA: {
    name: "market-data-db",
    purpose: "Real-time and historical market data",
    collections: [
      "price_history",
      "indicators",
      "market_snapshots",
      "volatility_metrics",
      "correlation_matrix",
      "market_events",
    ],
  },
  PORTFOLIO: {
    name: "portfolio-db",
    purpose: "Portfolio positions and holdings",
    collections: [
      "positions",
      "holdings",
      "allocations",
      "rebalancing_history",
      "performance_tracking",
      "asset_allocation",
    ],
  },
  TRADES: {
    name: "trades-db",
    purpose: "Trade execution and order management",
    collections: [
      "executed_trades",
      "pending_orders",
      "trade_signals",
      "execution_log",
      "fill_history",
      "trade_analysis",
    ],
  },
  RISK: {
    name: "risk-db",
    purpose: "Risk analysis and monitoring",
    collections: [
      "risk_profiles",
      "var_analysis",
      "stress_tests",
      "correlation_risks",
      "drawdown_analysis",
      "exposure_tracking",
    ],
  },
  ANALYTICS: {
    name: "analytics-db",
    purpose: "Performance analytics and backtesting (90-day retention)",
    collections: [
      "performance_metrics",
      "backtest_results",
      "strategy_analysis",
      "sentiment_scores",
      "alpha_tracking",
      "system_telemetry",
    ],
  },
  OPERATIONS: {
    name: "operations-db",
    purpose: "System operations and webhooks",
    collections: [
      "api_keys",
      "broker_connections",
      "webhook_events",
      "system_logs",
      "scheduler_tasks",
      "audit_logs",
    ],
  },
};

export class PrivMongoDBCompartmentalization {
  private clients: Map<string, MongoClient> = new Map();
  private databases: Map<string, Db> = new Map();
  private uri: string;
  private options: any;

  constructor(config: { uri: string; maxPoolSize?: number; minPoolSize?: number; maxIdleTimeMS?: number }) {
    this.uri = config.uri;
    this.options = {
      maxPoolSize: config.maxPoolSize || 10,
      minPoolSize: config.minPoolSize || 5,
      maxIdleTimeMS: config.maxIdleTimeMS || 30000,
    };
  }

  async initialize(): Promise<void> {
    for (const [key, compartment] of Object.entries(TRADING_COMPARTMENTS)) {
      const client = new MongoClient(this.uri, this.options);
      await client.connect();

      const db = client.db(compartment.name);

      // Create indexes for each collection
      for (const collection of compartment.collections) {
        const col = db.collection(collection);

        // Auto-create indexes based on collection type
        if (collection === "price_history") {
          await col.createIndex({ symbol: 1, timestamp: -1 });
          await col.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 }); // 30 days
        } else if (collection === "executed_trades") {
          await col.createIndex({ symbol: 1, executionTime: -1 });
          await col.createIndex({ userId: 1, executionTime: -1 });
        } else if (collection === "trade_signals") {
          await col.createIndex({ strategy: 1, strength: -1 });
          await col.createIndex({ timestamp: 1 });
        } else if (collection === "risk_profiles") {
          await col.createIndex({ portfolioId: 1 });
          await col.createIndex({ riskLevel: 1 });
        } else if (collection === "backtest_results") {
          await col.createIndex({ strategy: 1, testDate: -1 });
          await col.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 }); // 90 days
        } else if (collection === "webhook_events") {
          await col.createIndex({ eventType: 1, timestamp: -1 });
          await col.createIndex({ timestamp: 1 }, { expireAfterSeconds: 604800 }); // 7 days
        }
      }

      this.clients.set(key, client);
      this.databases.set(key, db);
    }
  }

  getDatabase(compartment: string): Db {
    const db = this.databases.get(compartment);
    if (!db) throw new Error(`Database compartment ${compartment} not initialized`);
    return db;
  }

  // Market Data Getters
  getPriceHistoryCollection(): Collection {
    return this.getDatabase("MARKET_DATA").collection("price_history");
  }

  getIndicatorsCollection(): Collection {
    return this.getDatabase("MARKET_DATA").collection("indicators");
  }

  getMarketSnapshotsCollection(): Collection {
    return this.getDatabase("MARKET_DATA").collection("market_snapshots");
  }

  // Portfolio Getters
  getPositionsCollection(): Collection {
    return this.getDatabase("PORTFOLIO").collection("positions");
  }

  getHoldingsCollection(): Collection {
    return this.getDatabase("PORTFOLIO").collection("holdings");
  }

  getAllocationsCollection(): Collection {
    return this.getDatabase("PORTFOLIO").collection("allocations");
  }

  // Trades Getters
  getExecutedTradesCollection(): Collection {
    return this.getDatabase("TRADES").collection("executed_trades");
  }

  getPendingOrdersCollection(): Collection {
    return this.getDatabase("TRADES").collection("pending_orders");
  }

  getTradeSignalsCollection(): Collection {
    return this.getDatabase("TRADES").collection("trade_signals");
  }

  // Risk Getters
  getRiskProfilesCollection(): Collection {
    return this.getDatabase("RISK").collection("risk_profiles");
  }

  getVarAnalysisCollection(): Collection {
    return this.getDatabase("RISK").collection("var_analysis");
  }

  getStressTestsCollection(): Collection {
    return this.getDatabase("RISK").collection("stress_tests");
  }

  // Analytics Getters
  getPerformanceMetricsCollection(): Collection {
    return this.getDatabase("ANALYTICS").collection("performance_metrics");
  }

  getBacktestResultsCollection(): Collection {
    return this.getDatabase("ANALYTICS").collection("backtest_results");
  }

  getSentimentScoresCollection(): Collection {
    return this.getDatabase("ANALYTICS").collection("sentiment_scores");
  }

  // Operations Getters
  getApiKeysCollection(): Collection {
    return this.getDatabase("OPERATIONS").collection("api_keys");
  }

  getWebhookEventsCollection(): Collection {
    return this.getDatabase("OPERATIONS").collection("webhook_events");
  }

  getAuditLogsCollection(): Collection {
    return this.getDatabase("OPERATIONS").collection("audit_logs");
  }

  async healthCheck(): Promise<Record<string, boolean>> {
    const health: Record<string, boolean> = {};

    for (const [key, compartment] of Object.entries(TRADING_COMPARTMENTS)) {
      try {
        const db = this.getDatabase(key);
        await db.admin().ping();
        health[compartment.name] = true;
      } catch (error) {
        health[compartment.name] = false;
      }
    }

    return health;
  }

  async close(): Promise<void> {
    for (const client of this.clients.values()) {
      await client.close();
    }
  }
}
