/**
 * PRIV Platform - Next.js API Routes for Trading Integration
 */

// pages/api/trading/sandbox/create.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrivSandboxDatadogIntegration } from "@/lib/sandbox-datadog-integration";
import { PrivMongoDBCompartmentalization } from "@/lib/mongodb-compartmentalization";

const sandboxIntegration = new PrivSandboxDatadogIntegration();
let mongoDb: PrivMongoDBCompartmentalization;

async function initializeMongo() {
  if (!mongoDb) {
    mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });
    await mongoDb.initialize();
  }
  return mongoDb;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { service, environment } = req.body;

    const db = await initializeMongo();

    const sandbox = await sandboxIntegration.createTradingSandbox({
      name: `${service}-sandbox`,
      service,
      environment: environment || "production",
    });

    res.status(200).json({
      success: true,
      service,
      message: "Trading sandbox created successfully",
    });
  } catch (error) {
    console.error("Error creating sandbox:", error);
    res.status(500).json({
      error: error instanceof Error ? error.message : "Failed to create sandbox",
    });
  }
}

// pages/api/trading/market-data.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrivMongoDBCompartmentalization } from "@/lib/mongodb-compartmentalization";

let mongoDb: PrivMongoDBCompartmentalization;

async function initializeMongo() {
  if (!mongoDb) {
    mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });
    await mongoDb.initialize();
  }
  return mongoDb;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "GET") {
    try {
      const db = await initializeMongo();
      const priceHistory = mongoDb.getPriceHistoryCollection();

      const data = await priceHistory
        .find({})
        .sort({ timestamp: -1 })
        .limit(100)
        .toArray();

      res.status(200).json({
        success: true,
        data,
      });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to fetch market data",
      });
    }
  } else if (req.method === "POST") {
    try {
      const db = await initializeMongo();
      const priceHistory = mongoDb.getPriceHistoryCollection();

      const { symbol, price, volume } = req.body;

      const result = await priceHistory.insertOne({
        symbol,
        price,
        volume,
        timestamp: new Date(),
      });

      res.status(201).json({
        success: true,
        id: result.insertedId,
      });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to store market data",
      });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}

// pages/api/trading/trades.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrivMongoDBCompartmentalization } from "@/lib/mongodb-compartmentalization";

let mongoDb: PrivMongoDBCompartmentalization;

async function initializeMongo() {
  if (!mongoDb) {
    mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });
    await mongoDb.initialize();
  }
  return mongoDb;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "GET") {
    try {
      const db = await initializeMongo();
      const trades = mongoDb.getExecutedTradesCollection();

      const data = await trades
        .find({})
        .sort({ executionTime: -1 })
        .limit(50)
        .toArray();

      res.status(200).json({ success: true, data });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to fetch trades",
      });
    }
  } else if (req.method === "POST") {
    try {
      const db = await initializeMongo();
      const trades = mongoDb.getExecutedTradesCollection();

      const { symbol, quantity, price, action } = req.body;

      const result = await trades.insertOne({
        symbol,
        quantity,
        price,
        action,
        executionTime: new Date(),
        status: "executed",
      });

      res.status(201).json({ success: true, id: result.insertedId });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to execute trade",
      });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}

// pages/api/trading/risk.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrivMongoDBCompartmentalization } from "@/lib/mongodb-compartmentalization";

let mongoDb: PrivMongoDBCompartmentalization;

async function initializeMongo() {
  if (!mongoDb) {
    mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });
    await mongoDb.initialize();
  }
  return mongoDb;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "GET") {
    try {
      const db = await initializeMongo();
      const riskProfiles = mongoDb.getRiskProfilesCollection();

      const data = await riskProfiles.find({}).toArray();

      res.status(200).json({ success: true, data });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to fetch risk data",
      });
    }
  } else if (req.method === "POST") {
    try {
      const db = await initializeMongo();
      const riskProfiles = mongoDb.getRiskProfilesCollection();

      const { portfolioId, var95, maxDrawdown, sharpeRatio } = req.body;

      const result = await riskProfiles.insertOne({
        portfolioId,
        var95,
        maxDrawdown,
        sharpeRatio,
        timestamp: new Date(),
      });

      res.status(201).json({ success: true, id: result.insertedId });
    } catch (error) {
      res.status(500).json({
        error: error instanceof Error ? error.message : "Failed to store risk profile",
      });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}

// pages/api/trading/health.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrivMongoDBCompartmentalization } from "@/lib/mongodb-compartmentalization";

let mongoDb: PrivMongoDBCompartmentalization;

async function initializeMongo() {
  if (!mongoDb) {
    mongoDb = new PrivMongoDBCompartmentalization({
      uri: process.env.MONGODB_URI!,
    });
    await mongoDb.initialize();
  }
  return mongoDb;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const db = await initializeMongo();
    const health = await mongoDb.healthCheck();

    res.status(200).json({
      success: true,
      health,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : "Health check failed",
    });
  }
}
