# backend/trading_engine/adapters/binance_adapter.py

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import pandas as pd

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceRequestException
except ImportError:
    logging.error("Binance library not found. Please install it: pip install python-binance")
    Client = None
    BinanceAPIException = BinanceRequestException = Exception

from backend.trading_engine.broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

class BinanceAdapter(BaseTradeAPIAdapter):
    """
    Adapter for the Binance API, refactored for dependency injection, robust error handling,
    and support for advanced order types and historical data.
    """
    def __init__(self, api_key: str, secret_key: str):
        if Client is None:
            raise ImportError("python-binance library is not installed.")
        self.name = "BinanceAdapter"
        self.client = Client(api_key=api_key, api_secret=secret_key)
        self.is_connected = False
        logger.info("Priv BinanceAdapter initialized.")

    async def connect(self) -> bool:
        if self.is_connected: return True
        try:
            await asyncio.to_thread(self.client.get_account_status)
            self.is_connected = True
            logger.info("Priv BinanceAdapter connected and authenticated successfully.")
            return True
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Priv BinanceAdapter API error during connection: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Priv BinanceAdapter unexpected error during connection: {e}", exc_info=True)
        self.is_connected = False
        return False

    async def disconnect(self) -> None:
        self.is_connected = False
        logger.info("Priv BinanceAdapter state set to disconnected (stateless API).")

    async def get_account_info(self) -> Dict[str, Any]:
        if not self.is_connected: return {}
        try:
            account_info = await asyncio.to_thread(self.client.get_account)
            balances = {b['asset']: {'free': float(b['free']), 'locked': float(b['locked'])} for b in account_info['balances']}
            return {
                "balances": balances,
                "can_trade": account_info.get("canTrade"),
                "currency": "USD"
            }
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Priv Binance: Error fetching account info: {e}", exc_info=True)
            self.is_connected = False
        return {}

    async def send_order(self, order_type: str, symbol: str, volume: float, price: Optional[float] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None, **kwargs) -> Optional[str]:
        if not self.is_connected: return None
        
        try:
            symbol_formatted = symbol.upper().replace('/', '')
            side = Client.SIDE_BUY if "BUY" in order_type.upper() else Client.SIDE_SELL
            
            # OCO (One-Cancels-the-Other) is the way to set SL and TP simultaneously on Binance
            if stop_loss and take_profit:
                if side == Client.SIDE_BUY:
                    # For a BUY, the TP is a high-price SELL LIMIT, and SL is a low-price SELL STOP_LOSS_LIMIT
                    # This is complex. The primary use case is protecting a position you already hold.
                    # Let's assume this is for placing a protective order on an existing long position.
                    oco_params = {
                        "symbol": symbol_formatted,
                        "side": Client.SIDE_SELL, # OCO is a SELL order to close a long position
                        "quantity": volume,
                        "price": take_profit, # The TP price is the LIMIT price
                        "stopPrice": stop_loss,
                        "stopLimitPrice": stop_loss, # Required, usually same as stopPrice
                        "stopLimitTimeInForce": Client.TIME_IN_FORCE_GTC
                    }
                    order = await asyncio.to_thread(self.client.create_oco_order, **oco_params)
                    return str(order["orderReports"][0]["orderId"]) if order else None
                else: # side == SELL
                     # For a SELL, the TP is a low-price BUY LIMIT, and SL is a high-price BUY STOP_LOSS_LIMIT
                    logger.warning("OCO BUY orders (to close short positions) are not implemented in this simplified adapter.")
                    return None

            # Simple Order Types
            params = {"symbol": symbol_formatted, "side": side, "quantity": volume}
            order_type_upper = order_type.upper()

            if "LIMIT" in order_type_upper:
                if not price: raise ValueError("Limit orders require a price.")
                params.update({"type": Client.ORDER_TYPE_LIMIT, "price": price, "timeInForce": Client.TIME_IN_FORCE_GTC})
            elif "MARKET" in order_type_upper:
                params["type"] = Client.ORDER_TYPE_MARKET
            else:
                raise ValueError(f"Unsupported simple order type for Binance: {order_type}")

            order = await asyncio.to_thread(self.client.create_order, **params)
            return str(order["orderId"]) if order else None

        except (BinanceAPIException, BinanceRequestException, ValueError) as e:
            logger.error(f"Priv Binance: Error sending order for {symbol}: {e}", exc_info=True)
            return None

    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        if not self.is_connected: return None
        try:
            timeframe_map = {
                "M1": Client.KLINE_INTERVAL_1MINUTE, "D1": Client.KLINE_INTERVAL_1DAY, "DAILY": Client.KLINE_INTERVAL_1DAY
            }
            binance_tf = timeframe_map.get(timeframe.upper())
            if not binance_tf:
                raise ValueError(f"Unsupported timeframe for Binance: {timeframe}")

            klines = await asyncio.to_thread(
                self.client.get_historical_klines,
                symbol.upper().replace('/', ''),
                binance_tf,
                f"{limit + 5} days ago UTC" # Request a bit more to be safe
            )
            
            df = pd.DataFrame(klines, columns=[
                'time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume', 'ignore'
            ]).iloc[-limit:] # Take the most recent 'limit' bars

            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df.set_index('time', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            return df
        except (BinanceAPIException, ValueError) as e:
            logger.error(f"Error fetching historical data for {symbol} from Binance: {e}", exc_info=True)
            return None

    # Other methods...
    async def get_open_positions(self) -> List[Dict[str, Any]]: return []
    async def get_pending_orders(self) -> List[Dict[str, Any]]: return []
    async def close_position(self, order_id: str, **kwargs) -> bool: return False
    async def modify_position(self, order_id: str, **kwargs) -> bool: return False
    async def delete_pending_order(self, order_id: str) -> bool: return False
