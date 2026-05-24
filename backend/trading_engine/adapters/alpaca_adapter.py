# backend/trading_engine/adapters/alpaca_adapter.py

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import pandas as pd

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest, LimitOrderRequest, StopOrderRequest, TrailingStopOrderRequest,
        ClosePositionRequest, TakeProfitRequest, StopLossRequest, GetOrdersRequest
    )
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, OrderStatus, AssetClass
    from alpaca.data.historical.stock import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.common.exceptions import APIError as AlpacaAPIError
except ImportError:
    logging.error("Alpaca-py library not found. Please install it: pip install alpaca-py")
    # Define dummy classes to prevent application crash on import
    TradingClient = None
    AlpacaAPIError = Exception

from backend.trading_engine.broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

class AlpacaAPIAdapter(BaseTradeAPIAdapter):
    """
    Adapter for the Alpaca API, refactored for dependency injection, robust error handling,
    and support for advanced order types and historical data fetching.
    """
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        if TradingClient is None:
            raise ImportError("alpaca-py library is not installed.")
        
        self.name = f"AlpacaAPIAdapter-{'Paper' if paper else 'Live'}"
        self.trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        self.is_connected = False
        logger.info(f"Priv {self.name} initialized.")

    async def connect(self) -> bool:
        if self.is_connected: return True
        try:
            account = await asyncio.to_thread(self.trading_client.get_account)
            if account and account.status == "ACTIVE":
                self.is_connected = True
                logger.info(f"Priv {self.name} connected successfully. Account ID: {account.id}")
                return True
            else:
                logger.error(f"{self.name} authentication failed. Account status: {account.status if account else 'N/A'}.")
                return False
        except AlpacaAPIError as e:
            logger.error(f"Priv {self.name} API error during connection: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Priv {self.name} unexpected error during connection: {e}", exc_info=True)
        self.is_connected = False
        return False

    async def disconnect(self) -> None:
        self.is_connected = False
        logger.info(f"Priv {self.name} state set to disconnected (stateless API).")

    async def get_account_info(self) -> Dict[str, Any]:
        if not await self.connect(): return {}
        try:
            account = await asyncio.to_thread(self.trading_client.get_account)
            return {
                "balance": float(account.cash),
                "equity": float(account.equity),
                "free_margin": float(account.buying_power),
                "currency": account.currency
            }
        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca account info: {e}", exc_info=True)
            self.is_connected = False
        return {}

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        if not self.is_connected: return []
        try:
            positions = await asyncio.to_thread(self.trading_client.get_all_positions)
            return [{
                "id": p.asset_id,
                "symbol": p.symbol,
                "type": "BUY" if p.side.value == "long" else "SELL",
                "volume": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "market_value": float(p.market_value),
            } for p in positions]
        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca open positions: {e}", exc_info=True)
            return []

    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        if not self.is_connected: return []
        try:
            request = GetOrdersRequest(status='open')
            orders = await asyncio.to_thread(self.trading_client.get_orders, filter=request)
            return [{
                "id": o.id,
                "symbol": o.symbol,
                "type": f"{o.side.value.upper()}_{o.order_type.value.upper()}",
                "volume": float(o.qty),
                "price": float(o.limit_price or o.stop_price or 0),
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            } for o in orders]
        except AlpacaAPIError as e:
            logger.error(f"Error fetching Alpaca pending orders: {e}", exc_info=True)
            return []

    async def send_order(self, order_type: str, symbol: str, volume: float, price: Optional[float] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None, trail_percent: Optional[float] = None, **kwargs) -> Optional[str]:
        if not self.is_connected: return None
        try:
            side = OrderSide.BUY if "BUY" in order_type.upper() else OrderSide.SELL
            
            stop_loss_req = StopLossRequest(stop_price=stop_loss) if stop_loss else None
            take_profit_req = TakeProfitRequest(limit_price=take_profit) if take_profit else None

            order_class = None
            if stop_loss and take_profit: order_class = OrderClass.BRACKET
            elif stop_loss or take_profit: order_class = OrderClass.OTO

            order_type_upper = order_type.upper()
            order_data = None

            if "MARKET" in order_type_upper:
                order_data = MarketOrderRequest(symbol=symbol, qty=volume, side=side, time_in_force=TimeInForce.GTC, order_class=order_class, take_profit=take_profit_req, stop_loss=stop_loss_req)
            elif "LIMIT" in order_type_upper:
                if not price: raise ValueError("Limit orders require a price.")
                order_data = LimitOrderRequest(symbol=symbol, qty=volume, side=side, limit_price=price, time_in_force=TimeInForce.GTC, order_class=order_class, take_profit=take_profit_req, stop_loss=stop_loss_req)
            elif "STOP" in order_type_upper:
                if not price: raise ValueError("Stop orders require a stop_price.")
                order_data = StopOrderRequest(symbol=symbol, qty=volume, side=side, stop_price=price, time_in_force=TimeInForce.GTC, order_class=order_class, take_profit=take_profit_req)
            elif "TRAILING" in order_type_upper:
                if not trail_percent: raise ValueError("Trailing stop orders require a trail_percent.")
                order_data = TrailingStopOrderRequest(symbol=symbol, qty=volume, side=side, trail_percent=trail_percent, time_in_force=TimeInForce.GTC)
            else:
                raise ValueError(f"Unsupported order type for Alpaca: {order_type}")

            order = await asyncio.to_thread(self.trading_client.submit_order, order_data=order_data)
            return order.id if order else None
        except (AlpacaAPIError, ValueError) as e:
            logger.error(f"Error sending order to Alpaca for {symbol}: {e}", exc_info=True)
            return None

    async def close_position(self, symbol: str, volume: Optional[float] = None) -> bool:
        if not self.is_connected: return False
        try:
            close_options = ClosePositionRequest(qty=str(volume)) if volume else ClosePositionRequest(percentage='100')
            await asyncio.to_thread(self.trading_client.close_position, symbol_or_asset_id=symbol, close_options=close_options)
            return True
        except AlpacaAPIError as e:
            logger.error(f"Error closing Alpaca position {symbol}: {e}", exc_info=True)
            return False
            
    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        if not self.is_connected: return None
        try:
            timeframe_map = {
                "M1": TimeFrame.Minute, "D1": TimeFrame.Day, "DAILY": TimeFrame.Day
            }
            alpaca_tf = timeframe_map.get(timeframe.upper())
            if not alpaca_tf:
                raise ValueError(f"Unsupported timeframe for Alpaca: {timeframe}")

            end_date = datetime.utcnow()
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol.upper()],
                timeframe=alpaca_tf,
                start=end_date - pd.Timedelta(days=limit * 1.5), # Request more to ensure we get enough bars
                end=end_date,
                limit=limit
            )
            bars = await asyncio.to_thread(self.data_client.get_stock_bars, request_params)
            df = bars.df
            if df.empty: return None
            df = df.reset_index().rename(columns={'timestamp': 'time'}).set_index('time')
            return df[['open', 'high', 'low', 'close', 'volume']]
        except (AlpacaAPIError, ValueError) as e:
            logger.error(f"Error fetching historical data for {symbol} from Alpaca: {e}", exc_info=True)
            return None
