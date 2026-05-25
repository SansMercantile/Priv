#!/usr/bin/env ts-node
/**
 * PRIV Platform - Trading Blob Storage Stats
 */

import { PrivBlobManager } from "../lib/vercel-blob-management";

async function getTradingStats() {
  console.log("📊 PRIV Platform - Trading Blob Storage Statistics\n");

  const blobManager = new PrivBlobManager();

  try {
    const stats = await blobManager.getTradingStorageStats();

    const headers = ["Directory", "Files", "Size (KB)", "Size (MB)"];
    console.log(
      headers.map((h) => h.padEnd(20)).join(" | ")
    );
    console.log("-".repeat(80));

    let totalFiles = 0;
    let totalSize = 0;

    for (const [dir, stat] of Object.entries(stats)) {
      const sizeKB = stat.totalSize / 1024;
      const sizeMB = sizeKB / 1024;

      console.log(
        [
          dir.padEnd(20),
          String(stat.count).padEnd(20),
          sizeKB.toFixed(2).padEnd(20),
          sizeMB.toFixed(2).padEnd(20),
        ].join(" | ")
      );

      totalFiles += stat.count;
      totalSize += stat.totalSize;
    }

    console.log("-".repeat(80));
    console.log(
      [
        "TOTAL".padEnd(20),
        String(totalFiles).padEnd(20),
        (totalSize / 1024).toFixed(2).padEnd(20),
        (totalSize / 1024 / 1024).toFixed(2).padEnd(20),
      ].join(" | ")
    );

    console.log("\n💾 Trading Storage Analysis:");
    console.log(`  • Total Trading Files: ${totalFiles}`);
    console.log(`  • Total Storage Used: ${(totalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  • Average File Size: ${(totalSize / totalFiles / 1024).toFixed(2)} KB`);
  } catch (error) {
    console.error("❌ Failed to get blob statistics:", error);
    process.exit(1);
  }
}

getTradingStats();
