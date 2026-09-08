#!/usr/bin/env ts-node
/**
 * PRIV Platform - Trading Database Verification
 */

import { PrivMongoDBCompartmentalization, TRADING_COMPARTMENTS } from "../lib/mongodb-compartmentalization";

async function verifyTradingDatabases() {
  console.log("📦 PRIV Platform - Trading Database Compartments Verification\n");

  const mongoDb = new PrivMongoDBCompartmentalization({
    uri: process.env.MONGODB_URI!,
  });

  try {
    console.log("🔄 Initializing MongoDB trading connections...");
    await mongoDb.initialize();

    console.log("\n✅ Connected to all trading compartments\n");

    // Verify each compartment
    for (const [key, config] of Object.entries(TRADING_COMPARTMENTS)) {
      console.log(`📋 ${config.name}`);
      console.log(`   Purpose: ${config.purpose}`);
      console.log(`   Collections: ${config.collections.length}`);

      const db = mongoDb.getDatabase(key);

      for (const collection of config.collections) {
        const col = db.collection(collection);
        const count = await col.countDocuments();
        const indexes = await col.listIndexes().toArray();

        console.log(
          `     • ${collection}: ${count} documents, ${indexes.length} indexes`
        );
      }

      console.log();
    }

    // Health check
    console.log("🏥 Trading System Health Status:");
    const health = await mongoDb.healthCheck();

    for (const [compartment, isHealthy] of Object.entries(health)) {
      console.log(`  ${isHealthy ? "✅" : "❌"} ${compartment}`);
    }

    console.log("\n✨ PRIV trading database verification complete!");

    await mongoDb.close();
  } catch (error) {
    console.error("❌ Verification failed:", error);
    process.exit(1);
  }
}

verifyTradingDatabases();
