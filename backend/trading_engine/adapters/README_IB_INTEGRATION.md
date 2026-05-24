# Interactive Brokers Integration - Quick Start Guide

## 🎯 Overview

The PRIV trading system now includes comprehensive Interactive Brokers (IB) integration, enabling you to trade stocks, forex, futures, options, CFDs, bonds, and commodities through a unified API.

**Status**: ✅ Complete and Ready for Testing  
**Date**: January 5, 2026

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install TWS or IB Gateway

1. Download from: https://www.interactivebrokers.com/en/trading/tws.php
2. Install and launch the application
3. Sign up for a paper trading account if you don't have one

### Step 2: Configure TWS API Access

1. In TWS, go to: **File → Global Configuration → API → Settings**
2. Enable these options:
   - ✅ Enable ActiveX and Socket Clients
   - ✅ Download open orders on connection
   - ✅ Allow connections from localhost only
3. Set **Socket port** to `7497` (paper trading)
4. Add `127.0.0.1` to **Trusted IP Addresses**
5. **Uncheck** "Read-Only API" (to allow trading)
6. Click **OK** and restart TWS

### Step 3: Configure PRIV

Copy the example environment file:

```bash
cp priv/.env.ib.example priv/.env
```

Edit `.env` and set:

```bash
ENABLE_IB_ADAPTER=true
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1
IB_READONLY=false
```

### Step 4: Start PRIV Backend

```bash
cd priv
python backend/main.py
```

### Step 5: Test the Connection

Open your browser and go to: http://localhost:8000/docs

Try the following endpoints:

1. **Register IB Broker**:
   - POST `/api/brokers/register`
   - Body:
     ```json
     {
       "broker_id": "ib_paper_1",
       "broker_type": "ib",
       "config": {
         "host": "127.0.0.1",
         "port": 7497,
         "client_id": 1,
         "readonly": false
       }
     }
     ```

2. **Connect to IB**:
   - POST `/api/brokers/connect/ib_paper_1`

3. **Get Account Info**:
   - GET `/api/brokers/account/ib_paper_1`

4. **Execute a Test Trade** (Paper Trading Only!):
   - POST `/api/brokers/trade`
   - Body:
     ```json
     {
       "broker_id": "ib_paper_1",
       "order_type": "MARKET",
       "symbol": "AAPL",
       "volume": 10,
       "stop_loss": 145.00,
       "take_profit": 160.00
     }
     ```

---

## 📚 Documentation

### Complete Documentation
- **User Guide**: `IB_ADAPTER_DOCUMENTATION.md` - Comprehensive usage guide
- **Implementation Summary**: `INTERACTIVE_BROKERS_INTEGRATION_SUMMARY.md` - Technical details
- **Example Scripts**: `examples/ib_adapter_example.py` - Python examples

### API Reference

#### Broker Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brokers/register` | Register a new broker |
| POST | `/api/brokers/connect/{id}` | Connect to a broker |
| POST | `/api/brokers/disconnect/{id}` | Disconnect from a broker |
| GET | `/api/brokers/status` | Get all brokers status |
| GET | `/api/brokers/account/{id}` | Get account information |
| GET | `/api/brokers/portfolio` | Get aggregated portfolio |
| GET | `/api/brokers/positions` | Get all positions |
| GET | `/api/brokers/orders` | Get all orders |
| POST | `/api/brokers/trade` | Execute a trade |
| POST | `/api/brokers/close-position` | Close a position |
| POST | `/api/brokers/cancel-order` | Cancel an order |
| POST | `/api/brokers/historical-data` | Get historical data |

### Supported Features

#### Asset Classes
- ✅ Stocks (STK)
- ✅ Forex (CASH)
- ✅ Futures (FUT)
- ✅ Options (OPT)
- ✅ CFDs (CFD)
- ✅ Bonds (BOND)
- ✅ Commodities (CMDTY)
- ✅ Indices (IND)

#### Order Types
- ✅ MARKET - Execute at current market price
- ✅ LIMIT - Execute at specified price or better
- ✅ STOP - Trigger market order when stop price is reached
- ✅ STOP_LIMIT - Trigger limit order when stop price is reached
- ✅ TRAILING_STOP - Dynamic stop that trails the market price
- ✅ BRACKET - Parent order with attached stop-loss and take-profit

#### Data Services
- ✅ Real-time market data (Level 1)
- ✅ Market depth (Level 2 / DOM)
- ✅ Historical data (M1, M5, M15, M30, H1, H4, D1, W1, MN)
- ✅ Option chains
- ✅ Account information and portfolio tracking

---

## 🔧 Troubleshooting

### Connection Issues

**Problem**: Cannot connect to TWS/Gateway  
**Solution**:
- Ensure TWS/Gateway is running
- Check that API is enabled in TWS settings
- Verify port number (7497 for paper, 7496 for live)
- Confirm "127.0.0.1" is in trusted IP addresses

**Problem**: "Already connected" error  
**Solution**:
- Use a different `client_id` for each connection
- Disconnect existing connections before reconnecting

### Order Issues

**Problem**: Orders not executing  
**Solution**:
- Check if readonly mode is enabled
- Verify account has sufficient buying power
- Ensure market is open for the security

**Problem**: "Invalid contract" error  
**Solution**:
- Verify symbol, exchange, and currency are correct
- Use `SMART` exchange for stocks
- Check that the security type matches the symbol

### Data Issues

**Problem**: No historical data returned  
**Solution**:
- Check market data subscriptions in your IB account
- Verify the symbol and timeframe are valid
- Ensure you're requesting data for a valid date range

---

## 🛡️ Security Best Practices

1. **Always test with paper trading first** (port 7497)
2. **Never commit .env files** with real credentials
3. **Enable read-only mode** for monitoring: `IB_READONLY=true`
4. **Restrict API access** to localhost only in TWS settings
5. **Use strong passwords** for your IB account
6. **Enable two-factor authentication** on your IB account
7. **Monitor API activity** regularly
8. **Set risk limits** in your IB account settings

---

## 📦 Files Created

### Core Implementation
1. `adapters/ib_adapter.py` (730 lines) - IB adapter implementation
2. `broker_api.py` (527 lines) - Broker management system
3. `api/broker_endpoints.py` (313 lines) - FastAPI endpoints

### Documentation
4. `adapters/IB_ADAPTER_DOCUMENTATION.md` (429 lines) - Complete user guide
5. `INTERACTIVE_BROKERS_INTEGRATION_SUMMARY.md` - Technical summary
6. `adapters/README_IB_INTEGRATION.md` (this file) - Quick start guide

### Configuration
7. `.env.ib.example` - Environment configuration template
8. `adapters/examples/ib_adapter_example.py` (200 lines) - Python examples

### Modified Files
9. `requirements.txt` - Added ib-async==1.0.2
10. `backend/config.py` - Added IB configuration settings
11. `backend/main.py` - Registered broker endpoints
12. `adapters/__init__.py` - Exported IB adapter

**Total**: ~2,200 lines of code

---

## 🎓 Learning Resources

- **IB API Documentation**: https://www.interactivebrokers.com/en/trading/ib-api.php
- **ib-async Documentation**: https://github.com/ib-api-reloaded/ib_async
- **TWS API Guide**: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/
- **IB Campus**: https://www.interactivebrokers.com/campus/

---

## ✅ Testing Checklist

- [ ] TWS/Gateway installed and running
- [ ] API access enabled in TWS settings
- [ ] Paper trading account created
- [ ] PRIV backend started successfully
- [ ] IB broker registered via API
- [ ] Connection to IB successful
- [ ] Account information retrieved
- [ ] Test trade executed (paper trading)
- [ ] Position retrieved
- [ ] Order cancelled
- [ ] Historical data fetched

---

## 🚀 Next Steps

1. **Test thoroughly** with paper trading
2. **Integrate with frontend** - Create broker management UI
3. **Add monitoring** - Set up alerts and logging
4. **Implement risk management** - Add position limits and stop-loss rules
5. **Deploy to production** - Only after extensive testing!

---

**Need Help?**

- Check the comprehensive documentation in `IB_ADAPTER_DOCUMENTATION.md`
- Review example scripts in `examples/ib_adapter_example.py`
- Consult the implementation summary in `INTERACTIVE_BROKERS_INTEGRATION_SUMMARY.md`

**Ready to Trade!** 🎉

