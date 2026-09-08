/**
 * PRIV Platform - Complete Sandbox + Datadog + MongoDB Integration Example
 */

import { PrivSandboxDatadogIntegration } from "../lib/sandbox-datadog-integration";
import { PrivMongoDBCompartmentalization } from "../lib/mongodb-compartmentalization";
import { PrivBlobManager } from "../lib/vercel-blob-management";

async function setupPrivTradingIntegration() {
  console.log("🚀 Setting up PRIV Platform with Vercel Sandbox + Datadog + MongoDB...\n");

  // Initialize integrations
  const sandboxIntegration = new PrivSandboxDatadogIntegration();

  const mongoDb = new PrivMongoDBCompartmentalization({
    uri: process.env.MONGODB_URI!,
    maxPoolSize: 10,
    minPoolSize: 5,
  });

  const blobManager = new PrivBlobManager();

  try {
    // Step 1: Initialize MongoDB compartments
    console.log("📦 Initializing MongoDB trading compartments...");
    await mongoDb.initialize();

    // Step 2: Health check
    console.log("\n🏥 Running health checks...");
    const health = await mongoDb.healthCheck();
    console.log("Trading System Health:", health);

    // Step 3: Create sandboxes for trading services
    console.log("\n🔗 Connecting trading services to Vercel Sandboxes...");
    const tradingServices = [
      "market-analysis",
      "risk-management",
      "portfolio-optimizer",
      "sentiment-analysis",
      "execution-engine",
    ] as const;

    const serviceSandboxes = await sandboxIntegration.connectTradingServices(
      [...tradingServices]
    );
    console.log(`✅ Connected ${serviceSandboxes.size} trading services to sandboxes`);

    // Step 4: Test market analysis
    console.log("\n⚙️  Testing market analysis sandbox...");
    const marketAnalysisSandbox = serviceSandboxes.get("market-analysis");

    if (marketAnalysisSandbox) {
      const sandboxId = Array.from(
        (sandboxIntegration as any).sandboxes.entries()
      ).find(([_, s]: any) => s === marketAnalysisSandbox)?.[0];

      if (sandboxId) {
        const result = await sandboxIntegration.executeTradeAnalysis(
          sandboxId,
          "echo",
          ["Market analysis complete!"]
        );

        console.log("Analysis Output:", result.stdout);
        console.log("Duration:", result.duration, "ms");
      }
    }

    // Step 5: Store market data
    console.log("\n💾 Storing market data snapshot...");
    const marketDataCollection = mongoDb.getPriceHistoryCollection();

    const marketSnapshot = {
      symbol: "AAPL",
      price: 175.50,
      volume: 5000000,
      timestamp: new Date(),
      open: 173.25,
      high: 176.50,
      low: 172.75,
      close: 175.50,
    };

    await marketDataCollection.insertOne(marketSnapshot);
    console.log("✅ Market snapshot stored");

    // Step 6: Store trade signal
    console.log("\n📊 Storing trade signal...");
    const tradeSignalsCollection = mongoDb.getTradeSignalsCollection();

    const signal = {
      symbol: "AAPL",
      signalTime: new Date(),
      strategy: "moving-average-crossover",
      strength: 0.85,
      action: "BUY",
      price: 175.50,
      confidence: 0.92,
    };

    await tradeSignalsCollection.insertOne(signal);
    console.log("✅ Trade signal stored");

    // Step 7: Store risk profile
    console.log("\n⚠️  Storing risk profile...");
    const riskProfiles = mongoDb.getRiskProfilesCollection();

    const riskProfile = {
      portfolioId: "portfolio-001",
      timestamp: new Date(),
      var95: 0.025,
      maxDrawdown: 0.15,
      sharpeRatio: 1.85,
      riskLevel: "moderate",
      exposures: {
        equities: 0.6,
        bonds: 0.3,
        cash: 0.1,
      },
    };

    await riskProfiles.insertOne(riskProfile);
    console.log("✅ Risk profile stored");

    // Step 8: Upload trading data to Blob
    console.log("\n📤 Uploading trading data to Vercel Blob...");

    // Market data
    await blobManager.uploadMarketData(
      "AAPL",
      JSON.stringify({ prices: [175.50, 174.25, 176.50] }, null, 2)
    );
    console.log("  ✅ Market data uploaded");

    // Trade log
    await blobManager.uploadTradeLog(
      "trade-001",
      JSON.stringify({ symbol: "AAPL", quantity: 100, price: 175.50 }, null, 2)
    );
    console.log("  ✅ Trade log uploaded");

    // Risk report
    await blobManager.uploadRiskReport(
      "daily",
      JSON.stringify({ var95: 0.025, date: new Date().toISOString() }, null, 2)
    );
    console.log("  ✅ Risk report uploaded");

    // Strategy config
    await blobManager.uploadStrategyConfig(
      "moving-average-crossover",
      "1.0.0",
      JSON.stringify({
        strategy: "moving-average-crossover",
        shortPeriod: 20,
        longPeriod: 50,
      }, null, 2)
    );
    console.log("  ✅ Strategy config uploaded");

    // Step 9: Get storage statistics
    console.log("\n📈 Trading Storage Statistics:");
    const stats = await blobManager.getTradingStorageStats();
    for (const [dir, stat] of Object.entries(stats)) {
      console.log(
        `  ${dir}: ${stat.count} files, ${(stat.totalSize / 1024).toFixed(2)} KB`
      );
    }

    // Step 10: Get metrics dashboard
    console.log("\n📊 Trading Metrics Dashboard:");
    const metrics = sandboxIntegration.getTradingMetricsDashboard();
    console.log(JSON.stringify(metrics, null, 2));

    console.log("\n✨ PRIV Platform setup complete! Ready for trading operations.\n");

    // Cleanup
    console.log("🧹 Cleaning up...");
    for (const [service, sandbox] of serviceSandboxes.entries()) {
      const sandboxId = Array.from(
        (sandboxIntegration as any).sandboxes.entries()
      ).find(([_, s]: any) => s === sandbox)?.[0];

      if (sandboxId) {
        await sandboxIntegration.stopTradingSandbox(sandboxId);
      }
    }

    await mongoDb.close();
    console.log("✅ Cleanup complete");
  } catch (error) {
    console.error("❌ Setup failed:", error);
    process.exit(1);
  }
}

// Run the setup
setupPrivTradingIntegration();
