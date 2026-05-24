#!/usr/bin/env python3
"""
Interactive Brokers Adapter Example Script

This script demonstrates how to use the InteractiveBrokersAdapter for:
- Connecting to IB TWS/Gateway
- Fetching account information
- Placing various order types
- Managing positions and orders
- Retrieving market data

Prerequisites:
1. TWS or IB Gateway must be running
2. API access must be enabled in TWS settings
3. Port 7497 (paper) or 7496 (live) must be configured

Usage:
    python ib_adapter_example.py
"""

import asyncio
import logging
from datetime import datetime
from backend.trading_engine.adapters import InteractiveBrokersAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_connection():
    """Example: Connect to Interactive Brokers"""
    logger.info("=== Connection Example ===")
    
    # Initialize adapter (paper trading)
    adapter = InteractiveBrokersAdapter(
        host="127.0.0.1",
        port=7497,  # Paper trading port
        client_id=1,
        readonly=False
    )
    
    # Connect
    if await adapter.connect():
        logger.info("✓ Successfully connected to IB")
        
        # Get account info
        account_info = await adapter.get_account_info()
        logger.info(f"Account Equity: ${account_info.get('equity', 0):.2f}")
        logger.info(f"Buying Power: ${account_info.get('buying_power', 0):.2f}")
        logger.info(f"Unrealized P&L: ${account_info.get('unrealized_pnl', 0):.2f}")
        
        # Disconnect
        await adapter.disconnect()
        return adapter
    else:
        logger.error("✗ Failed to connect to IB")
        return None


async def example_market_data(adapter: InteractiveBrokersAdapter):
    """Example: Fetch market data"""
    logger.info("\n=== Market Data Example ===")
    
    await adapter.connect()
    
    # Get current price
    symbol = "AAPL"
    price = await adapter.get_current_price(symbol, sec_type="STK")
    if price:
        logger.info(f"{symbol} current price: ${price:.2f}")
    
    # Get historical data
    logger.info(f"Fetching historical data for {symbol}...")
    df = await adapter.get_historical_data(
        symbol=symbol,
        timeframe="D1",
        limit=10,
        sec_type="STK"
    )
    
    if df is not None and not df.empty:
        logger.info(f"Retrieved {len(df)} bars")
        logger.info(f"Latest close: ${df.iloc[-1]['close']:.2f}")
        logger.info(f"Date range: {df.iloc[0]['time']} to {df.iloc[-1]['time']}")
    
    await adapter.disconnect()


async def example_stock_trading(adapter: InteractiveBrokersAdapter):
    """Example: Stock trading operations"""
    logger.info("\n=== Stock Trading Example ===")
    
    await adapter.connect()
    
    symbol = "AAPL"
    
    # Example 1: Market order
    logger.info(f"Placing market order to buy 10 shares of {symbol}...")
    order_id = await adapter.send_order(
        order_type="MARKET",
        symbol=symbol,
        volume=10,
        sec_type="STK",
        comment="Example market order"
    )
    
    if order_id:
        logger.info(f"✓ Market order placed: Order ID {order_id}")
    else:
        logger.error("✗ Market order failed")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Example 2: Limit order
    current_price = await adapter.get_current_price(symbol, sec_type="STK")
    if current_price:
        limit_price = current_price * 0.98  # 2% below current price
        
        logger.info(f"Placing limit order to buy 5 shares at ${limit_price:.2f}...")
        order_id = await adapter.send_order(
            order_type="LIMIT",
            symbol=symbol,
            volume=5,
            price=limit_price,
            sec_type="STK",
            comment="Example limit order"
        )
        
        if order_id:
            logger.info(f"✓ Limit order placed: Order ID {order_id}")
            
            # Cancel the order after a moment
            await asyncio.sleep(2)
            logger.info(f"Cancelling order {order_id}...")
            if await adapter.cancel_order(order_id):
                logger.info("✓ Order cancelled successfully")
    
    # Example 3: Bracket order with stop-loss and take-profit
    if current_price:
        stop_loss = current_price * 0.95  # 5% stop loss
        take_profit = current_price * 1.10  # 10% take profit
        
        logger.info(f"Placing bracket order with SL=${stop_loss:.2f}, TP=${take_profit:.2f}...")
        order_id = await adapter.send_order(
            order_type="MARKET",
            symbol=symbol,
            volume=10,
            stop_loss=stop_loss,
            take_profit=take_profit,
            sec_type="STK",
            comment="Example bracket order"
        )
        
        if order_id:
            logger.info(f"✓ Bracket order placed: Order ID {order_id}")
    
    await adapter.disconnect()


async def example_forex_trading(adapter: InteractiveBrokersAdapter):
    """Example: Forex trading"""
    logger.info("\n=== Forex Trading Example ===")
    
    await adapter.connect()
    
    # Trade EUR/USD
    symbol = "EURUSD"
    
    logger.info(f"Placing forex order for {symbol}...")
    order_id = await adapter.send_order(
        order_type="MARKET",
        symbol=symbol,
        volume=10000,  # 10,000 units
        sec_type="CASH",
        exchange="IDEALPRO",
        currency="USD",
        comment="Example forex order"
    )
    
    if order_id:
        logger.info(f"✓ Forex order placed: Order ID {order_id}")
    
    await adapter.disconnect()


async def example_position_management(adapter: InteractiveBrokersAdapter):
    """Example: Position and order management"""
    logger.info("\n=== Position Management Example ===")
    
    await adapter.connect()
    
    # Get open positions
    positions = await adapter.get_open_positions()
    logger.info(f"Open positions: {len(positions)}")
    
    for pos in positions:
        logger.info(f"  {pos['symbol']}: {pos['volume']} shares @ ${pos['avg_price']:.2f}")
        logger.info(f"    Current: ${pos['current_price']:.2f}, P&L: ${pos['unrealized_pnl']:.2f}")
    
    # Get pending orders
    orders = await adapter.get_pending_orders()
    logger.info(f"\nPending orders: {len(orders)}")
    
    for order in orders:
        logger.info(f"  Order {order['order_id']}: {order['action']} {order['volume']} {order['symbol']}")
        logger.info(f"    Type: {order['type']}, Status: {order['status']}")
    
    await adapter.disconnect()


async def main():
    """Main example runner"""
    logger.info("Interactive Brokers Adapter Examples")
    logger.info("=" * 50)
    logger.info("Make sure TWS or IB Gateway is running!")
    logger.info("=" * 50)
    
    # Example 1: Connection
    adapter = await example_connection()
    
    if adapter is None:
        logger.error("Cannot proceed without connection. Exiting.")
        return
    
    # Example 2: Market data
    await example_market_data(adapter)
    
    # Example 3: Stock trading (commented out to avoid accidental trades)
    # Uncomment to test trading functionality
    # await example_stock_trading(adapter)
    
    # Example 4: Forex trading (commented out)
    # await example_forex_trading(adapter)
    
    # Example 5: Position management
    await example_position_management(adapter)
    
    logger.info("\n" + "=" * 50)
    logger.info("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())

