# PRIV Platform - Trading Integration Quick Reference

## 🎯 One-Command Setup

```bash
npm install && npm run verify:env && npm run setup && npm run dev
```

## 🏦 Trading Databases at a Glance

| DB | Collections | Example |
|----|-------------|---------|
| **market-data** | price_history, indicators, market_snapshots | 1M+ prices |
| **portfolio** | positions, holdings, allocations | Long positions |
| **trades** | executed_trades, pending_orders, signals | BUY 100 AAPL |
| **risk** | risk_profiles, var_analysis, stress_tests | VAR 2.5% |
| **analytics** | performance_metrics, backtest_results, sentiment | Sharpe 1.85 |
| **operations** | api_keys, webhooks, audit_logs | System logs |

## 🔗 API Endpoints

```bash
# Market Data
GET    /api/trading/market-data       # Get prices
POST   /api/trading/market-data       # Store price

# Trades
GET    /api/trading/trades            # Get trade history
POST   /api/trading/trades            # Execute trade

# Risk
GET    /api/trading/risk              # Get risk profiles
POST   /api/trading/risk              # Store risk analysis

# Health
GET    /api/trading/health            # System health
```

## 💾 MongoDB Usage Examples

### Market Data
```typescript
const prices = mongoDb.getPriceHistoryCollection();
await prices.insertOne({
  symbol: "AAPL",
  price: 175.50,
  volume: 5000000,
  timestamp: new Date()
});
```

### Trades
```typescript
const trades = mongoDb.getExecutedTradesCollection();
await trades.insertOne({
  symbol: "AAPL",
  quantity: 100,
  price: 175.50,
  action: "BUY",
  executionTime: new Date()
});
```

### Risk
```typescript
const risk = mongoDb.getRiskProfilesCollection();
await risk.insertOne({
  portfolioId: "portfolio-001",
  var95: 0.025,
  maxDrawdown: 0.15,
  sharpeRatio: 1.85
});
```

## 📤 Vercel Blob Examples

### Market Data
```typescript
await blobManager.uploadMarketData(
  "AAPL",
  JSON.stringify(priceData)
);
```

### Trade Log
```typescript
await blobManager.uploadTradeLog(
  "trade-001",
  JSON.stringify(tradeDetails)
);
```

### Risk Report
```typescript
await blobManager.uploadRiskReport(
  "daily",
  JSON.stringify(riskMetrics)
);
```

### Strategy Config
```typescript
await blobManager.uploadStrategyConfig(
  "moving-average-crossover",
  "1.0.0",
  JSON.stringify(config)
);
```

## 🧪 Verification Commands

```bash
npm run verify:env        # ✅ Environment
npm run health-check      # ✅ System health
npm run db:verify         # ✅ Trading databases
npm run blob:stats        # ✅ Storage stats
```

## 🏪 Trading Services

```typescript
const services = [
  "market-analysis",
  "risk-management",
  "portfolio-optimizer",
  "sentiment-analysis",
  "execution-engine"
];

const sandboxes = await sandboxIntegration
  .connectTradingServices(services);
```

## 📊 Get Metrics

```typescript
const metrics = sandboxIntegration.getTradingMetricsDashboard();
// Returns: CPU, memory, trades processed, analysis time
```

## 🔐 Environment Variables

```bash
DATADOG_APP_ID=your_app_id
DATADOG_CLIENT_TOKEN=your_token
MONGODB_URI=mongodb+srv://...
VERCEL_TOKEN=vercel_...
VERCEL_BLOB_READ_WRITE_TOKEN=...
ENVIRONMENT=production
```

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Sandbox fails | Check VERCEL_TOKEN |
| MongoDB error | Verify MONGODB_URI |
| Datadog missing | Check DATADOG tokens |
| Trade not stored | Verify collection |
| Blob upload fails | Check VERCEL_BLOB token |

## 📈 Monitoring Workflow

```
Execute Trade
  ↓
Datadog Tracks
  ↓
MongoDB Stores
  ↓
Blob Archives
  ↓
View Dashboard
  ↓
Analyze Results
```

## 🎯 Next Steps

1. Set environment variables
2. Run `npm run verify:env`
3. Run `npm run setup`
4. Deploy trading service
5. Monitor in Datadog

---

**Ready to trade** 🚀
