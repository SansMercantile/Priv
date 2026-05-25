/**
 * PRIV Platform - Vercel Blob Management for Trading Data
 * 8 strategic directories for trading-specific data organization
 */

import { put, list, del, copy } from "@vercel/blob";

export const TRADING_BLOB_DIRECTORIES = {
  MARKET_DATA: "/market-data/",
  TRADE_LOGS: "/trade-logs/",
  BACKTEST_RESULTS: "/backtest-results/",
  RISK_REPORTS: "/risk-reports/",
  PORTFOLIO_SNAPSHOTS: "/portfolio-snapshots/",
  STRATEGY_CONFIG: "/strategy-config/",
  MODEL_WEIGHTS: "/model-weights/",
  BACKUP: "/backup/",
};

export class PrivBlobManager {
  async uploadMarketData(symbol: string, data: string): Promise<void> {
    const date = new Date().toISOString().split("T")[0];
    const path = `${TRADING_BLOB_DIRECTORIES.MARKET_DATA}${symbol}/${date}.json`;

    await put(path, data, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadTradeLog(tradeId: string, data: string): Promise<void> {
    const timestamp = new Date().toISOString();
    const path = `${TRADING_BLOB_DIRECTORIES.TRADE_LOGS}${tradeId}/${timestamp}.json`;

    await put(path, data, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadBacktestResults(strategy: string, results: string): Promise<void> {
    const testDate = new Date().toISOString().split("T")[0];
    const path = `${TRADING_BLOB_DIRECTORIES.BACKTEST_RESULTS}${strategy}/${testDate}.json`;

    await put(path, results, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadRiskReport(reportType: string, data: string): Promise<void> {
    const date = new Date().toISOString().split("T")[0];
    const path = `${TRADING_BLOB_DIRECTORIES.RISK_REPORTS}${reportType}/${date}.json`;

    await put(path, data, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadPortfolioSnapshot(portfolioId: string, snapshot: string): Promise<void> {
    const timestamp = new Date().toISOString();
    const path = `${TRADING_BLOB_DIRECTORIES.PORTFOLIO_SNAPSHOTS}${portfolioId}/${timestamp}.json`;

    await put(path, snapshot, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadStrategyConfig(strategy: string, version: string, config: string): Promise<void> {
    const path = `${TRADING_BLOB_DIRECTORIES.STRATEGY_CONFIG}${strategy}/v${version}.json`;

    await put(path, config, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async uploadModelWeights(modelName: string, version: string, weights: string): Promise<void> {
    const path = `${TRADING_BLOB_DIRECTORIES.MODEL_WEIGHTS}${modelName}/v${version}.bin`;

    await put(path, weights, {
      access: "private",
      addRandomSuffix: false,
    });
  }

  async listSymbolData(symbol: string): Promise<any[]> {
    const { blobs } = await list({
      prefix: `${TRADING_BLOB_DIRECTORIES.MARKET_DATA}${symbol}/`,
    });
    return blobs;
  }

  async archiveOldTradingData(days: number = 30): Promise<number> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    let archived = 0;

    const directories = Object.values(TRADING_BLOB_DIRECTORIES);
    for (const dir of directories) {
      const { blobs } = await list({ prefix: dir });

      for (const blob of blobs) {
        if (new Date(blob.uploadedAt) < cutoffDate) {
          const archivePath = `${TRADING_BLOB_DIRECTORIES.BACKUP}${blob.pathname}`;
          await copy({
            fromPathname: blob.pathname,
            toPathname: archivePath,
          });
          await del(blob.url);
          archived++;
        }
      }
    }

    return archived;
  }

  async getTradingStorageStats(): Promise<
    Record<string, { count: number; totalSize: number }>
  > {
    const stats: Record<string, { count: number; totalSize: number }> = {};

    for (const [key, dir] of Object.entries(TRADING_BLOB_DIRECTORIES)) {
      const { blobs } = await list({ prefix: dir });

      stats[key] = {
        count: blobs.length,
        totalSize: blobs.reduce((sum, blob) => sum + (blob.size || 0), 0),
      };
    }

    return stats;
  }
}
