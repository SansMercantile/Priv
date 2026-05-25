# PRIV Platform - 10-Minute Deployment Guide

## Setup (2 min)
```bash
cd priv
cp .env.trading.example .env.local
```

Edit `.env.local`:
```
DATADOG_APP_ID=your_id
DATADOG_CLIENT_TOKEN=your_token
MONGODB_URI=mongodb+srv://user:pass@cluster...
VERCEL_TOKEN=vercel_token
VERCEL_BLOB_READ_WRITE_TOKEN=blob_token
ENVIRONMENT=production
```

## Install (2 min)
```bash
npm install
```

## Verify (2 min)
```bash
npm run verify:env       # Check environment
npm run health-check     # Check system
npm run db:verify        # Check databases
npm run blob:stats       # Check storage
```

## Deploy (2 min)
```bash
npm run setup            # Initialize
npm run dev              # Start server
```

## Verify Production (2 min)
```bash
# Test endpoints
curl http://localhost:3000/api/trading/health
curl http://localhost:3000/api/trading/market-data
curl http://localhost:3000/api/trading/trades

# View Datadog
open https://app.datadoghq.com
```

## Production Deploy

### Vercel
```bash
vercel --prod
```

### Docker
```bash
docker build -t priv-trading .
docker run -e MONGODB_URI="..." -e DATADOG_APP_ID="..." priv-trading
```

### Docker Compose
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s-deployment.yaml
```

---

**Deployed** ✅
