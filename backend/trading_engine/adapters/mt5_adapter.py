# backend/trading_engine/adapters/mt5_adapter.py

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import pandas as pd

# NOTE: The 'MetaTrader5' import has been removed from the top level of the file.
# It will be imported "lazily" inside the connect() method to prevent blocking.

from backend.trading_engine.broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

# Environment variables are still loaded here, as this is a non-blocking operation.
MT5_ACCOUNT: int = int(os.getenv("MT5_ACCOUNT", "0"))
MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "YOUR_MT5_PASSWORD")
MT5_SERVER: str = os.getenv("MT5_SERVER", "YourBroker-Server")

class MetaTrader5Adapter(BaseTradeAPIAdapter):
    def __init__(self):
        self.name = "MetaTrader5Adapter"
        self.is_connected = False
        self.mt5 = None  # MODIFIED: Will hold the imported mt5 library object after connection.
        self.account_info_cache: Dict[str, Any] = {}
        self._cache_duration_seconds = 5
        self._last_account_info_update: Optional[datetime] = None
        self.login_attempts = 0
        self.max_login_attempts = 3
        logger.info(f"Priv MetaTrader5Adapter initialized. Account: {MT5_ACCOUNT}, Server: {MT5_SERVER}")

    async def connect(self) -> bool:
        if self.is_connected:
            return True
        if self.login_attempts >= self.max_login_attempts:
            logger.warning("MT5: Max login attempts reached. Will not try to connect.")
            return False

        # --- MODIFIED: The import happens here, only when needed. ---
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5 # Store the imported library as an instance attribute
        except ImportError:
            logger.error("MetaTrader5 library not found. Please install it: pip install MetaTrader5")
            return False

        if not self.mt5.initialize():
            logger.error(f"Priv MT5: initialize() failed: {self.mt5.last_error()}")
            self.login_attempts += 1
            return False
        
        if not self.mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER):
            logger.error(f"Priv MT5: Login failed: {self.mt5.last_error()}")
            self.mt5.shutdown()
            self.login_attempts += 1
            return False
        
        self.is_connected = True
        self.login_attempts = 0
        logger.info("Priv MT5: Connected and logged in successfully.")
        await self._refresh_account_info_cache()
        return True

    async def disconnect(self) -> None:
        # MODIFIED: Check for self.mt5 before using it.
        if self.is_connected and self.mt5:
            self.mt5.shutdown()
        self.is_connected = False
        self.mt5 = None # Clear the library object on disconnect
        logger.info("Priv MT5: Disconnected.")

    async def _refresh_account_info_cache(self):
        # MODIFIED: Check for self.mt5
        if not self.is_connected or not self.mt5:
            return
        
        account_info = self.mt5.account_info()
        if account_info:
            self.account_info_cache = {
                "balance": account_info.balance, "equity": account_info.equity,
                "free_margin": account_info.margin_free, "currency": account_info.currency
            }
            self._last_account_info_update = datetime.now()
        else:
            logger.warning(f"Priv MT5: Could not fetch account info: {self.mt5.last_error()}")

    async def get_account_info(self) -> Dict[str, Any]:
        if not self.is_connected:
            await self.connect()
        if not self.is_connected: # Check again after trying to connect
            return {}
        
        if self._last_account_info_update is None or \
           (datetime.now() - self._last_account_info_update).total_seconds() > self._cache_duration_seconds:
            await self._refresh_account_info_cache()
        return self.account_info_cache

    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        # MODIFIED: Check for self.mt5
        if not self.is_connected or not self.mt5:
            logger.error("MT5 not connected. Cannot fetch historical data.")
            return None
        
        try:
            timeframe_map = {
                "M1": self.mt5.TIMEFRAME_M1, "M5": self.mt5.TIMEFRAME_M5, "M15": self.mt5.TIMEFRAME_M15,
                "M30": self.mt5.TIMEFRAME_M30, "H1": self.mt5.TIMEFRAME_H1, "H4": self.mt5.TIMEFRAME_H4,
                "D1": self.mt5.TIMEFRAME_D1, "DAILY": self.mt5.TIMEFRAME_D1,
                "W1": self.mt5.TIMEFRAME_W1, "MN1": self.mt5.TIMEFRAME_MN1
            }
            mt5_timeframe = timeframe_map.get(timeframe.upper())
            if mt5_timeframe is None:
                logger.error(f"Unsupported timeframe for MT5: {timeframe}")
                return None

            rates = self.mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, limit)
            if rates is None or len(rates) == 0:
                logger.warning(f"No historical data from MT5 for {symbol}. Error: {self.mt5.last_error()}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={'tick_volume': 'volume'}, inplace=True)
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error fetching MT5 historical data for {symbol}: {e}", exc_info=True)
            return None

    # --- Stubs for other required methods ---
    async def get_open_positions(self) -> List[Dict[str, Any]]: return []
    async def get_pending_orders(self) -> List[Dict[str, Any]]: return []
    async def send_order(self, *args, **kwargs) -> Optional[Union[int, str]]: return None
    async def close_position(self, *args, **kwargs) -> bool: return False
    async def modify_position(self, *args, **kwargs) -> bool: return False
    async def delete_pending_order(self, *args, **kwargs) -> bool: return False