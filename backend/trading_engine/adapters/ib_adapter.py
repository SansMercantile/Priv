# backend/trading_engine/adapters/ib_adapter.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import asyncio
import pandas as pd

try:
    from ib_async import IB, Stock, Forex, Future, Option, Index, CFD, Commodity, Bond
    from ib_async import MarketOrder, LimitOrder, StopOrder, StopLimitOrder, TrailingStopOrder
    from ib_async import Trade, Position, PortfolioItem, AccountValue
    from ib_async import util
except ImportError:
    logging.error("ib-async library not found. Please install it: pip install ib-async")
    IB = None

from ..broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)


class InteractiveBrokersAdapter(BaseTradeAPIAdapter):
    """
    Comprehensive adapter for Interactive Brokers TWS API using ib-async.
    Supports stocks, forex, futures, options, CFDs, bonds, and commodities.
    
    Features:
    - Multiple asset classes (stocks, forex, futures, options, CFDs, bonds, commodities)
    - Advanced order types (market, limit, stop, stop-limit, trailing stop, bracket, OCO)
    - Real-time market data and historical data
    - Portfolio management and position tracking
    - Account information and margin calculations
    - Paper trading and live trading support
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,  # 7497 for paper trading, 7496 for live trading
        client_id: int = 1,
        account: Optional[str] = None,
        readonly: bool = False
    ):
        """
        Initialize Interactive Brokers adapter.
        
        Args:
            host: TWS/IB Gateway host (default: 127.0.0.1)
            port: TWS/IB Gateway port (7497 for paper, 7496 for live)
            client_id: Unique client ID for this connection
            account: Specific account to use (optional, uses default if None)
            readonly: If True, only allow read operations (no trading)
        """
        if IB is None:
            raise ImportError("ib-async library is not installed.")
        
        self.name = f"InteractiveBrokersAdapter-{'Paper' if port == 7497 else 'Live'}"
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self.readonly = readonly
        self.ib = IB()
        self.is_connected = False
        
        # Cache for contracts and market data
        self._contract_cache = {}
        self._position_cache = {}
        
        logger.info(f"PRIV {self.name} initialized (host={host}, port={port}, client_id={client_id})")

    async def connect(self) -> bool:
        """Connect to Interactive Brokers TWS or IB Gateway."""
        if self.is_connected:
            return True
        
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id, readonly=self.readonly)
            
            # Verify connection
            if self.ib.isConnected():
                self.is_connected = True
                
                # Get account information
                accounts = self.ib.managedAccounts()
                if self.account and self.account not in accounts:
                    logger.error(f"Specified account {self.account} not found. Available: {accounts}")
                    await self.disconnect()
                    return False
                
                if not self.account and accounts:
                    self.account = accounts[0]
                
                logger.info(f"PRIV {self.name} connected successfully. Account: {self.account}")
                return True
            else:
                logger.error(f"{self.name} connection failed.")
                return False
                
        except Exception as e:
            logger.error(f"PRIV {self.name} error during connection: {e}", exc_info=True)
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Interactive Brokers."""
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
            self.is_connected = False
            logger.info(f"PRIV {self.name} disconnected.")
        except Exception as e:
            logger.error(f"Error disconnecting {self.name}: {e}", exc_info=True)

    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance, equity, and margin."""
        if not self.is_connected:
            if not await self.connect():
                return {}
        
        try:
            account_values = self.ib.accountValues(account=self.account)
            
            # Extract key account metrics
            info = {
                "balance": 0.0,
                "equity": 0.0,
                "free_margin": 0.0,
                "currency": "USD",
                "margin_used": 0.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "buying_power": 0.0
            }
            
            for av in account_values:
                if av.tag == "NetLiquidation":
                    info["equity"] = float(av.value)
                elif av.tag == "TotalCashValue":
                    info["balance"] = float(av.value)
                elif av.tag == "AvailableFunds":
                    info["free_margin"] = float(av.value)
                elif av.tag == "BuyingPower":
                    info["buying_power"] = float(av.value)
                elif av.tag == "UnrealizedPnL":
                    info["unrealized_pnl"] = float(av.value)
                elif av.tag == "RealizedPnL":
                    info["realized_pnl"] = float(av.value)
                elif av.tag == "Currency":
                    info["currency"] = av.value

            return info

        except Exception as e:
            logger.error(f"Error fetching IB account info: {e}", exc_info=True)
            return {}

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        if not self.is_connected:
            if not await self.connect():
                return []

        try:
            positions = self.ib.positions(account=self.account)
            position_list = []

            for pos in positions:
                position_list.append({
                    "symbol": pos.contract.symbol,
                    "type": pos.contract.secType,
                    "volume": float(pos.position),
                    "avg_price": float(pos.avgCost / pos.position) if pos.position != 0 else 0.0,
                    "current_price": float(pos.marketPrice) if pos.marketPrice else 0.0,
                    "unrealized_pnl": float(pos.unrealizedPNL) if pos.unrealizedPNL else 0.0,
                    "realized_pnl": float(pos.realizedPNL) if pos.realizedPNL else 0.0,
                    "market_value": float(pos.marketValue) if pos.marketValue else 0.0,
                    "currency": pos.contract.currency,
                    "exchange": pos.contract.exchange
                })

            return position_list

        except Exception as e:
            logger.error(f"Error fetching IB positions: {e}", exc_info=True)
            return []

    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending (open) orders."""
        if not self.is_connected:
            if not await self.connect():
                return []

        try:
            trades = self.ib.openTrades()
            order_list = []

            for trade in trades:
                order = trade.order
                contract = trade.contract

                order_list.append({
                    "order_id": order.orderId,
                    "symbol": contract.symbol,
                    "type": order.orderType,
                    "action": order.action,
                    "volume": float(order.totalQuantity),
                    "price": float(order.lmtPrice) if order.lmtPrice else None,
                    "stop_price": float(order.auxPrice) if order.auxPrice else None,
                    "status": trade.orderStatus.status,
                    "filled": float(trade.orderStatus.filled),
                    "remaining": float(trade.orderStatus.remaining),
                    "avg_fill_price": float(trade.orderStatus.avgFillPrice) if trade.orderStatus.avgFillPrice else 0.0,
                    "time": trade.log[-1].time if trade.log else None
                })

            return order_list

        except Exception as e:
            logger.error(f"Error fetching IB pending orders: {e}", exc_info=True)
            return []

    def _create_contract(self, symbol: str, sec_type: str = "STK", exchange: str = "SMART", currency: str = "USD") -> Any:
        """
        Create an IB contract object.

        Args:
            symbol: Ticker symbol
            sec_type: Security type (STK, CASH, FUT, OPT, CFD, BOND, CMDTY, IND)
            exchange: Exchange (SMART for stocks, IDEALPRO for forex)
            currency: Currency (USD, EUR, GBP, etc.)
        """
        cache_key = f"{symbol}_{sec_type}_{exchange}_{currency}"
        if cache_key in self._contract_cache:
            return self._contract_cache[cache_key]

        if sec_type == "STK":
            contract = Stock(symbol, exchange, currency)
        elif sec_type == "CASH":  # Forex
            contract = Forex(symbol, exchange=exchange)
        elif sec_type == "FUT":
            contract = Future(symbol, exchange=exchange, currency=currency)
        elif sec_type == "OPT":
            contract = Option(symbol, exchange=exchange, currency=currency)
        elif sec_type == "CFD":
            contract = CFD(symbol, exchange=exchange, currency=currency)
        elif sec_type == "BOND":
            contract = Bond(symbol, exchange=exchange, currency=currency)
        elif sec_type == "CMDTY":
            contract = Commodity(symbol, exchange=exchange, currency=currency)
        elif sec_type == "IND":
            contract = Index(symbol, exchange=exchange, currency=currency)
        else:
            logger.warning(f"Unknown security type {sec_type}, defaulting to Stock")
            contract = Stock(symbol, exchange, currency)

        self._contract_cache[cache_key] = contract
        return contract

    async def send_order(
        self,
        order_type: str,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
        slippage: int = 0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "",
        magic_number: int = 0,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD",
        trail_percent: Optional[float] = None,
        trail_amount: Optional[float] = None
    ) -> Optional[Union[int, str]]:
        """
        Send an order to Interactive Brokers.

        Supports multiple order types:
        - MARKET: Market order
        - LIMIT: Limit order
        - STOP: Stop order
        - STOP_LIMIT: Stop-limit order
        - TRAILING_STOP: Trailing stop order
        - BRACKET: Bracket order (with stop loss and take profit)

        Args:
            order_type: Type of order (MARKET, LIMIT, STOP, etc.)
            symbol: Ticker symbol
            volume: Order quantity (positive for buy, negative for sell)
            price: Limit price (for LIMIT and STOP_LIMIT orders)
            slippage: Not used for IB (kept for interface compatibility)
            stop_loss: Stop loss price (for bracket orders)
            take_profit: Take profit price (for bracket orders)
            comment: Order comment/tag
            magic_number: Order identifier
            sec_type: Security type (STK, CASH, FUT, OPT, CFD, BOND, CMDTY, IND)
            exchange: Exchange
            currency: Currency
            trail_percent: Trailing stop percentage
            trail_amount: Trailing stop amount
        """
        if not self.is_connected:
            if not await self.connect():
                return None

        if self.readonly:
            logger.warning(f"{self.name} is in readonly mode. Order not sent.")
            return None

        try:
            # Create contract
            contract = self._create_contract(symbol, sec_type, exchange, currency)

            # Qualify contract (get full contract details from IB)
            await self.ib.qualifyContractsAsync(contract)

            # Determine action (BUY or SELL)
            action = "BUY" if volume > 0 else "SELL"
            quantity = abs(volume)

            # Create order based on type
            order_type_upper = order_type.upper()

            if order_type_upper == "MARKET":
                order = MarketOrder(action, quantity)

            elif order_type_upper == "LIMIT":
                if price is None:
                    raise ValueError("LIMIT order requires a price")
                order = LimitOrder(action, quantity, price)

            elif order_type_upper == "STOP":
                if price is None:
                    raise ValueError("STOP order requires a stop price")
                order = StopOrder(action, quantity, price)

            elif order_type_upper == "STOP_LIMIT":
                if price is None or stop_loss is None:
                    raise ValueError("STOP_LIMIT order requires both limit price and stop price")
                order = StopLimitOrder(action, quantity, price, stop_loss)

            elif order_type_upper == "TRAILING_STOP":
                if trail_percent is not None:
                    order = TrailingStopOrder(action, quantity, trailingPercent=trail_percent)
                elif trail_amount is not None:
                    order = TrailingStopOrder(action, quantity, auxPrice=trail_amount)
                else:
                    raise ValueError("TRAILING_STOP order requires trail_percent or trail_amount")

            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            # Add order tag/comment
            if comment:
                order.orderRef = comment

            # Place the order
            trade = self.ib.placeOrder(contract, order)

            # Wait for order to be submitted
            await asyncio.sleep(0.5)

            # Handle bracket orders (stop loss and take profit)
            if stop_loss or take_profit:
                parent_order_id = trade.order.orderId

                # Create stop loss order
                if stop_loss:
                    sl_action = "SELL" if action == "BUY" else "BUY"
                    sl_order = StopOrder(sl_action, quantity, stop_loss)
                    sl_order.parentId = parent_order_id
                    sl_order.transmit = not take_profit  # Only transmit if no TP
                    self.ib.placeOrder(contract, sl_order)

                # Create take profit order
                if take_profit:
                    tp_action = "SELL" if action == "BUY" else "BUY"
                    tp_order = LimitOrder(tp_action, quantity, take_profit)
                    tp_order.parentId = parent_order_id
                    tp_order.transmit = True
                    self.ib.placeOrder(contract, tp_order)

            logger.info(f"PRIV IB order placed: {action} {quantity} {symbol} @ {order_type}")
            return trade.order.orderId

        except Exception as e:
            logger.error(f"Error sending IB order for {symbol}: {e}", exc_info=True)
            return None

    async def close_position(
        self,
        order_id: Union[int, str],
        volume: float,
        price: float,
        slippage: int = 0
    ) -> bool:
        """Close a position (partial or full)."""
        if not self.is_connected:
            if not await self.connect():
                return False

        if self.readonly:
            logger.warning(f"{self.name} is in readonly mode. Position not closed.")
            return False

        try:
            # Find the position by symbol (order_id is treated as symbol for IB)
            symbol = str(order_id)
            positions = self.ib.positions(account=self.account)

            target_position = None
            for pos in positions:
                if pos.contract.symbol == symbol:
                    target_position = pos
                    break

            if not target_position:
                logger.error(f"Position not found for symbol: {symbol}")
                return False

            # Determine close action (opposite of current position)
            current_volume = target_position.position
            action = "SELL" if current_volume > 0 else "BUY"
            close_volume = min(abs(volume), abs(current_volume))

            # Create market order to close
            contract = target_position.contract
            order = MarketOrder(action, close_volume)
            order.orderRef = f"Close position {symbol}"

            trade = self.ib.placeOrder(contract, order)

            # Wait for execution
            await asyncio.sleep(1)

            logger.info(f"PRIV IB position closed: {action} {close_volume} {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error closing IB position: {e}", exc_info=True)
            return False

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical market data.

        Args:
            symbol: Ticker symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN)
            limit: Number of bars to fetch
            sec_type: Security type
            exchange: Exchange
            currency: Currency
        """
        if not self.is_connected:
            if not await self.connect():
                return None

        try:
            # Create contract
            contract = self._create_contract(symbol, sec_type, exchange, currency)
            await self.ib.qualifyContractsAsync(contract)

            # Map timeframe to IB bar size
            timeframe_map = {
                "M1": "1 min", "M5": "5 mins", "M15": "15 mins", "M30": "30 mins",
                "H1": "1 hour", "H4": "4 hours", "D1": "1 day", "W1": "1 week", "MN": "1 month"
            }
            bar_size = timeframe_map.get(timeframe.upper(), "1 day")

            # Calculate duration based on timeframe and limit
            if "min" in bar_size:
                duration = f"{limit * int(bar_size.split()[0])} S"  # Seconds
            elif "hour" in bar_size:
                duration = f"{limit * int(bar_size.split()[0])} D"  # Days
            elif "day" in bar_size:
                duration = f"{limit} D"
            elif "week" in bar_size:
                duration = f"{limit} W"
            else:  # month
                duration = f"{limit} M"

            # Request historical data
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            if not bars:
                logger.warning(f"No historical data returned for {symbol}")
                return None

            # Convert to DataFrame
            df = util.df(bars)
            df = df.rename(columns={
                'date': 'time',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })

            return df

        except Exception as e:
            logger.error(f"Error fetching IB historical data for {symbol}: {e}", exc_info=True)
            return None

    async def get_current_price(
        self,
        symbol: str,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Optional[float]:
        """Get current market price for a symbol."""
        if not self.is_connected:
            if not await self.connect():
                return None

        try:
            contract = self._create_contract(symbol, sec_type, exchange, currency)
            await self.ib.qualifyContractsAsync(contract)

            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            await asyncio.sleep(1)  # Wait for data

            # Get last price or close price
            price = ticker.last if ticker.last and ticker.last > 0 else ticker.close

            # Cancel market data subscription
            self.ib.cancelMktData(contract)

            return float(price) if price else None

        except Exception as e:
            logger.error(f"Error fetching IB current price for {symbol}: {e}", exc_info=True)
            return None

    async def cancel_order(self, order_id: Union[int, str]) -> bool:
        """Cancel a pending order."""
        if not self.is_connected:
            if not await self.connect():
                return False

        if self.readonly:
            logger.warning(f"{self.name} is in readonly mode. Order not cancelled.")
            return False

        try:
            # Find the trade by order ID
            trades = self.ib.openTrades()
            target_trade = None

            for trade in trades:
                if trade.order.orderId == int(order_id):
                    target_trade = trade
                    break

            if not target_trade:
                logger.error(f"Order not found: {order_id}")
                return False

            # Cancel the order
            self.ib.cancelOrder(target_trade.order)
            await asyncio.sleep(0.5)

            logger.info(f"PRIV IB order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling IB order {order_id}: {e}", exc_info=True)
            return False

    async def modify_order(
        self,
        order_id: Union[int, str],
        new_price: Optional[float] = None,
        new_volume: Optional[float] = None,
        new_stop_loss: Optional[float] = None,
        new_take_profit: Optional[float] = None
    ) -> bool:
        """Modify an existing order."""
        if not self.is_connected:
            if not await self.connect():
                return False

        if self.readonly:
            logger.warning(f"{self.name} is in readonly mode. Order not modified.")
            return False

        try:
            # Find the trade by order ID
            trades = self.ib.openTrades()
            target_trade = None

            for trade in trades:
                if trade.order.orderId == int(order_id):
                    target_trade = trade
                    break

            if not target_trade:
                logger.error(f"Order not found: {order_id}")
                return False

            # Modify order parameters
            order = target_trade.order

            if new_price is not None:
                if hasattr(order, 'lmtPrice'):
                    order.lmtPrice = new_price

            if new_volume is not None:
                order.totalQuantity = abs(new_volume)

            # Place modified order
            self.ib.placeOrder(target_trade.contract, order)
            await asyncio.sleep(0.5)

            logger.info(f"PRIV IB order modified: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Error modifying IB order {order_id}: {e}", exc_info=True)
            return False

    async def get_market_depth(
        self,
        symbol: str,
        sec_type: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get market depth (Level 2 data) for a symbol."""
        if not self.is_connected:
            if not await self.connect():
                return {}

        try:
            contract = self._create_contract(symbol, sec_type, exchange, currency)
            await self.ib.qualifyContractsAsync(contract)

            # Request market depth
            ticker = self.ib.reqMktDepth(contract)
            await asyncio.sleep(2)  # Wait for data

            # Extract bid/ask data
            bids = [[dom.price, dom.size] for dom in ticker.domBids]
            asks = [[dom.price, dom.size] for dom in ticker.domAsks]

            # Cancel market depth subscription
            self.ib.cancelMktDepth(contract)

            return {
                "symbol": symbol,
                "bids": bids,
                "asks": asks,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error fetching IB market depth for {symbol}: {e}", exc_info=True)
            return {}

    async def get_option_chain(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> List[Dict[str, Any]]:
        """Get option chain for a symbol."""
        if not self.is_connected:
            if not await self.connect():
                return []

        try:
            # Create underlying stock contract
            stock = Stock(symbol, exchange, currency)
            await self.ib.qualifyContractsAsync(stock)

            # Request option chain
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock.symbol, '', stock.secType, stock.conId
            )

            if not chains:
                logger.warning(f"No option chain found for {symbol}")
                return []

            # Extract option details
            option_list = []
            for chain in chains:
                for expiration in chain.expirations:
                    for strike in chain.strikes:
                        option_list.append({
                            "symbol": symbol,
                            "expiration": expiration,
                            "strike": strike,
                            "exchange": chain.exchange,
                            "multiplier": chain.multiplier
                        })

            return option_list

        except Exception as e:
            logger.error(f"Error fetching IB option chain for {symbol}: {e}", exc_info=True)
            return []

    def __repr__(self) -> str:
        """String representation of the adapter."""
        status = "Connected" if self.is_connected else "Disconnected"
        return f"<InteractiveBrokersAdapter(account={self.account}, status={status}, readonly={self.readonly})>"

