#!/usr/bin/env ts-node
/**
 * PRIV Platform - Environment Verification
 */

function verifyEnvironment() {
  console.log("🔐 PRIV Platform - Verifying Environment Variables\n");

  const required = {
    "Datadog": [
      "DATADOG_APP_ID",
      "DATADOG_CLIENT_TOKEN",
    ],
    "MongoDB": [
      "MONGODB_URI",
    ],
    "Vercel": [
      "VERCEL_TOKEN",
      "VERCEL_BLOB_READ_WRITE_TOKEN",
    ],
    "General": [
      "ENVIRONMENT",
      "NODE_ENV",
    ],
  };

  let allValid = true;

  for (const [category, vars] of Object.entries(required)) {
    console.log(`📋 ${category}:`);
    for (const varName of vars) {
      const value = process.env[varName];
      if (value) {
        const masked = value.substring(0, 4) + "..." + value.substring(value.length - 4);
        console.log(`  ✅ ${varName}: ${masked}`);
      } else {
        console.log(`  ❌ ${varName}: NOT SET`);
        allValid = false;
      }
    }
    console.log();
  }

  if (allValid) {
    console.log("✨ All environment variables are properly configured for PRIV Platform!\n");
  } else {
    console.error("❌ Some environment variables are missing.\n");
    console.log("Please set the missing variables in .env.local\n");
    process.exit(1);
  }
}

verifyEnvironment();
