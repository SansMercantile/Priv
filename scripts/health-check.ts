#!/usr/bin/env ts-node
/**
 * PRIV Platform - Health Check Script
 */

import { PrivMongoDBCompartmentalization } from "../lib/mongodb-compartmentalization";
import { PrivBlobManager } from "../lib/vercel-blob-management";

async function healthCheck() {
  console.log("🔍 PRIV Platform - Comprehensive Health Check\n");

  // MongoDB Health
  console.log("📦 Checking MongoDB trading compartments...");
  try {
    const mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });

    await mongoDb.initialize();
    const health = await mongoDb.healthCheck();

    let allHealthy = true;
    for (const [compartment, isHealthy] of Object.entries(health)) {
      console.log(`  ${isHealthy ? "✅" : "❌"} ${compartment}`);
      if (!isHealthy) allHealthy = false;
    }

    if (!allHealthy) {
      console.error("\n❌ Some MongoDB compartments are unhealthy");
    }

    await mongoDb.close();
  } catch (error) {
    console.error("❌ MongoDB health check failed:", error);
  }

  // Blob Storage Health
  console.log("\n📤 Checking Vercel Blob storage...");
  try {
    const blobManager = new PrivBlobManager();
    const stats = await blobManager.getTradingStorageStats();

    let totalSize = 0;
    let totalFiles = 0;

    for (const [dir, stat] of Object.entries(stats)) {
      console.log(
        `  ✅ ${dir}: ${stat.count} files, ${(stat.totalSize / 1024).toFixed(2)} KB`
      );
      totalSize += stat.totalSize;
      totalFiles += stat.count;
    }

    console.log(
      `\n  📊 Total: ${totalFiles} files, ${(totalSize / 1024 / 1024).toFixed(2)} MB`
    );
  } catch (error) {
    console.error("❌ Blob storage health check failed:", error);
  }

  // Environment Variables
  console.log("\n🔐 Checking environment variables...");
  const requiredEnvs = [
    "MONGODB_URI",
    "VERCEL_TOKEN",
    "VERCEL_BLOB_READ_WRITE_TOKEN",
    "DATADOG_APP_ID",
    "DATADOG_CLIENT_TOKEN",
  ];

  for (const env of requiredEnvs) {
    const isSet = !!process.env[env];
    console.log(`  ${isSet ? "✅" : "❌"} ${env}`);
  }

  console.log("\n✨ PRIV Platform health check complete!");
}

healthCheck().catch((error) => {
  console.error("Health check failed:", error);
  process.exit(1);
});
