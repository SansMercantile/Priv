# Interactive Brokers Adapter Documentation

## Overview

The Interactive Brokers (IB) adapter provides comprehensive integration with Interactive Brokers' Trader Workstation (TWS) and IB Gateway APIs. This adapter supports multiple asset classes, advanced order types, real-time market data, and portfolio management.

## Features

### Supported Asset Classes
- **Stocks (STK)**: US and international equities
- **Forex (CASH)**: Currency pairs
- **Futures (FUT)**: Commodity and financial futures
- **Options (OPT)**: Equity and index options
- **CFDs (CFD)**: Contracts for difference
- **Bonds (BOND)**: Government and corporate bonds
- **Commodities (CMDTY)**: Physical commodities
- **Indices (IND)**: Market indices

### Order Types
- **Market Orders**: Execute at current market price
- **Limit Orders**: Execute at specified price or better
- **Stop Orders**: Trigger market order when stop price is reached
- **Stop-Limit Orders**: Trigger limit order when stop price is reached
- **Trailing Stop Orders**: Dynamic stop that trails the market price
- **Bracket Orders**: Parent order with attached stop-loss and take-profit orders

### Data Services
- Real-time market data (Level 1)
- Market depth (Level 2 / DOM)
- Historical data (multiple timeframes)
- Option chains
- Account information and portfolio tracking

## Installation

### Prerequisites

1. **Interactive Brokers Account**: You need an active IB account (paper or live)
2. **TWS or IB Gateway**: Download and install from [Interactive Brokers](https://www.interactivebrokers.com/en/trading/tws.php)
3. **Python Package**: Already included in `requirements.txt`

```bash
pip install ib-async==1.0.2
```

### TWS/Gateway Configuration

1. **Enable API Access**:
   - Open TWS or IB Gateway
   - Go to File → Global Configuration → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set "Socket port" to 7497 (paper) or 7496 (live)
   - Add "127.0.0.1" to "Trusted IP Addresses"
   - Uncheck "Read-Only API" if you want to place orders

2. **Configure Permissions**:
   - Enable "Download open orders on connection"
   - Enable "Allow connections from localhost only" (for security)
   - Set "Master API client ID" if needed

## Usage

### Basic Connection

```python
from backend.trading_engine.adapters import InteractiveBrokersAdapter

# Paper trading (port 7497)
ib_adapter = InteractiveBrokersAdapter(
    host="127.0.0.1",
    port=7497,
    client_id=1,
    readonly=False
)

# Connect to IB
await ib_adapter.connect()

# Get account info
account_info = await ib_adapter.get_account_info()
print(f"Equity: ${account_info['equity']:.2f}")
print(f"Buying Power: ${account_info['buying_power']:.2f}")
```

### Trading Stocks

```python
# Market order - Buy 100 shares of AAPL
order_id = await ib_adapter.send_order(
    order_type="MARKET",
    symbol="AAPL",
    volume=100,  # Positive for buy
    sec_type="STK",
    exchange="SMART",
    currency="USD"
)

# Limit order - Sell 50 shares at $150
order_id = await ib_adapter.send_order(
    order_type="LIMIT",
    symbol="AAPL",
    volume=-50,  # Negative for sell
    price=150.00,
    sec_type="STK"
)

# Bracket order with stop-loss and take-profit
order_id = await ib_adapter.send_order(
    order_type="MARKET",
    symbol="AAPL",
    volume=100,
    stop_loss=145.00,  # Exit if price drops to $145
    take_profit=160.00,  # Exit if price rises to $160
    sec_type="STK"
)
```

### Trading Forex

```python
# Buy EUR/USD (10,000 units)
order_id = await ib_adapter.send_order(
    order_type="MARKET",
    symbol="EURUSD",
    volume=10000,
    sec_type="CASH",
    exchange="IDEALPRO",
    currency="USD"
)
```

### Trading Futures

```python
# Buy 1 ES futures contract
order_id = await ib_adapter.send_order(
    order_type="LIMIT",
    symbol="ES",
    volume=1,
    price=4500.00,
    sec_type="FUT",
    exchange="CME",
    currency="USD"
)
```

### Advanced Orders

```python
# Trailing stop order (trail by 2%)
order_id = await ib_adapter.send_order(
    order_type="TRAILING_STOP",
    symbol="AAPL",
    volume=-100,
    trail_percent=2.0,
    sec_type="STK"
)

# Stop-limit order
order_id = await ib_adapter.send_order(
    order_type="STOP_LIMIT",
    symbol="AAPL",
    volume=100,
    price=150.00,  # Limit price
    stop_loss=148.00,  # Stop trigger price
    sec_type="STK"
)
```

### Portfolio Management

```python
# Get all open positions
positions = await ib_adapter.get_open_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['volume']} @ ${pos['avg_price']:.2f}")
    print(f"  Unrealized P&L: ${pos['unrealized_pnl']:.2f}")

# Get pending orders
orders = await ib_adapter.get_pending_orders()
for order in orders:
    print(f"Order {order['order_id']}: {order['action']} {order['volume']} {order['symbol']}")
    print(f"  Status: {order['status']}, Filled: {order['filled']}")

# Close a position
await ib_adapter.close_position(
    order_id="AAPL",  # Symbol to close
    volume=50,  # Quantity to close
    price=0  # Market order
)
```

### Market Data

```python
# Get current price
price = await ib_adapter.get_current_price("AAPL", sec_type="STK")
print(f"AAPL current price: ${price:.2f}")

# Get historical data
df = await ib_adapter.get_historical_data(
    symbol="AAPL",
    timeframe="D1",  # Daily bars
    limit=100,  # Last 100 days
    sec_type="STK"
)
print(df.head())

# Get market depth (Level 2)
depth = await ib_adapter.get_market_depth("AAPL", sec_type="STK")
print("Bids:", depth['bids'][:5])  # Top 5 bid levels
print("Asks:", depth['asks'][:5])  # Top 5 ask levels

# Get option chain
options = await ib_adapter.get_option_chain("AAPL")
for opt in options[:10]:
    print(f"Strike: {opt['strike']}, Expiration: {opt['expiration']}")
```

### Order Management

```python
# Cancel an order
success = await ib_adapter.cancel_order(order_id=12345)

# Modify an order
success = await ib_adapter.modify_order(
    order_id=12345,
    new_price=155.00,
    new_volume=150
)
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Interactive Brokers Configuration
IB_HOST=127.0.0.1
IB_PORT=7497  # 7497 for paper, 7496 for live
IB_CLIENT_ID=1
IB_ACCOUNT=  # Optional: specific account number
IB_READONLY=false  # Set to true for read-only mode
```

### Multiple Connections

You can create multiple adapter instances with different client IDs:

```python
# Paper trading connection
paper_adapter = InteractiveBrokersAdapter(port=7497, client_id=1)

# Live trading connection (different client ID)
live_adapter = InteractiveBrokersAdapter(port=7496, client_id=2)

# Read-only connection for monitoring
monitor_adapter = InteractiveBrokersAdapter(port=7497, client_id=3, readonly=True)
```

## Timeframes

Supported timeframes for historical data:

| Code | Description |
|------|-------------|
| M1   | 1 minute    |
| M5   | 5 minutes   |
| M15  | 15 minutes  |
| M30  | 30 minutes  |
| H1   | 1 hour      |
| H4   | 4 hours     |
| D1   | 1 day       |
| W1   | 1 week      |
| MN   | 1 month     |

## Error Handling

The adapter includes comprehensive error handling:

```python
try:
    order_id = await ib_adapter.send_order(
        order_type="MARKET",
        symbol="AAPL",
        volume=100,
        sec_type="STK"
    )
    if order_id:
        print(f"Order placed successfully: {order_id}")
    else:
        print("Order failed")
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

### 1. Connection Management
- Always check connection status before trading
- Use `await adapter.connect()` at startup
- Implement reconnection logic for production systems

### 2. Order Validation
- Validate symbol and contract details before placing orders
- Check account balance and buying power
- Use limit orders in volatile markets

### 3. Risk Management
- Always use stop-loss orders for risk protection
- Monitor position sizes relative to account equity
- Implement maximum daily loss limits

### 4. Market Data
- Subscribe to market data only when needed
- Cancel subscriptions when done to avoid data fees
- Use historical data for backtesting

### 5. Testing
- Always test with paper trading first (port 7497)
- Verify all order types work as expected
- Test error handling and edge cases

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to TWS/Gateway
- **Solution**: Ensure TWS/Gateway is running and API is enabled
- Check that the port number is correct (7497 for paper, 7496 for live)
- Verify "127.0.0.1" is in trusted IP addresses

**Problem**: "Already connected" error
- **Solution**: Use a different client_id for each connection
- Disconnect existing connections before reconnecting

### Order Issues

**Problem**: Orders not executing
- **Solution**: Check if readonly mode is enabled
- Verify account has sufficient buying power
- Ensure market is open for the security

**Problem**: "Invalid contract" error
- **Solution**: Verify symbol, exchange, and currency are correct
- Use `SMART` exchange for stocks (IB will route optimally)
- Check that the security type matches the symbol

### Data Issues

**Problem**: No historical data returned
- **Solution**: Check market data subscriptions in your IB account
- Verify the symbol and timeframe are valid
- Ensure you're requesting data for a valid date range

## API Reference

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| host | str | "127.0.0.1" | TWS/Gateway host address |
| port | int | 7497 | TWS/Gateway port (7497=paper, 7496=live) |
| client_id | int | 1 | Unique client identifier |
| account | str | None | Specific account (uses default if None) |
| readonly | bool | False | Read-only mode (no trading) |

### Methods

#### Connection Methods
- `connect() -> bool`: Connect to IB TWS/Gateway
- `disconnect() -> None`: Disconnect from IB

#### Account Methods
- `get_account_info() -> Dict`: Get account balance and equity
- `get_open_positions() -> List[Dict]`: Get all open positions
- `get_pending_orders() -> List[Dict]`: Get all pending orders

#### Trading Methods
- `send_order(...) -> Optional[int]`: Place a new order
- `close_position(...) -> bool`: Close an existing position
- `cancel_order(order_id) -> bool`: Cancel a pending order
- `modify_order(...) -> bool`: Modify an existing order

#### Market Data Methods
- `get_current_price(symbol, ...) -> Optional[float]`: Get current market price
- `get_historical_data(...) -> Optional[pd.DataFrame]`: Get historical bars
- `get_market_depth(...) -> Dict`: Get Level 2 market depth
- `get_option_chain(symbol, ...) -> List[Dict]`: Get option chain

## Integration with PRIV Trading Engine

The IB adapter integrates seamlessly with the PRIV trading engine:

```python
from backend.trading_engine.adapters import InteractiveBrokersAdapter
from backend.trading_engine.broker_interface import BrokerRouter

# Initialize adapter
ib_adapter = InteractiveBrokersAdapter(port=7497, client_id=1)

# Add to broker router
broker_router = BrokerRouter()
broker_router.register_adapter("ib", ib_adapter)

# Use through router
await broker_router.execute_trade(
    broker="ib",
    symbol="AAPL",
    action="BUY",
    quantity=100,
    order_type="MARKET"
)
```

## Support and Resources

- **IB API Documentation**: https://www.interactivebrokers.com/en/trading/ib-api.php
- **ib-async Documentation**: https://github.com/ib-api-reloaded/ib_async
- **TWS API Guide**: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/
- **IB Campus**: https://www.interactivebrokers.com/campus/

## License

This adapter is part of the PRIV trading system and follows the same license terms.


