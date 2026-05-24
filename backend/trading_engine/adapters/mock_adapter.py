# backend/trading_engine/adapters/mock_adapter.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from backend.trading_engine.broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

class MockTradeAPIAdapter(BaseTradeAPIAdapter):
    """
    A simple in-memory mock implementation of the BaseTradeAPIAdapter for local testing.
    """
    def __init__(self, name: str = "MockAdapter"):
        self.name = name
        self._open_positions: Dict[int, Dict[str, Any]] = {}
        self._next_order_id = 1000
        self._mock_account_balance = 50000.0
        self._mock_account_equity = 50000.0
        self.is_connected = False
        logger.info(f"Priv MockTradeAPIAdapter '{self.name}' initialized.")

    async def connect(self) -> bool:
        logger.info(f"Priv MockTradeAPIAdapter '{self.name}' connected (simulated).")
        self.is_connected = True
        return True

    async def disconnect(self) -> None:
        logger.info(f"Priv MockTradeAPIAdapter '{self.name}' disconnected (simulated).")
        self.is_connected = False

    async def get_account_info(self) -> Dict[str, Any]:
        return {"balance": self._mock_account_balance, "equity": self._mock_account_equity, "currency": "USD"}
    
    async def get_open_positions(self) -> List[Dict[str, Any]]:
        return list(self._open_positions.values())

    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        return []

    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Generates mock historical data for testing."""
        logger.info(f"MockAdapter: Generating {limit} mock bars for {symbol} ({timeframe}).")
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=limit, freq="D")
        
        price_start = 100.0
        returns = np.random.normal(loc=0.0001, scale=0.01, size=limit)
        prices = price_start * (1 + returns).cumprod()
        
        data = {
            'open': prices - np.random.uniform(0, 1, size=limit),
            'high': prices + np.random.uniform(0, 1, size=limit),
            'low': prices - np.random.uniform(0, 1, size=limit),
            'close': prices,
            'volume': np.random.randint(1000, 10000, size=limit)
        }
        df = pd.DataFrame(data, index=dates)
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        df.index.name = "timestamp"
        return df

    async def send_order(self, order_type: str, symbol: str, volume: float, price: Optional[float] = None,
                   slippage: int = 0, stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None, comment: str = "",
                   magic_number: int = 0) -> Optional[Union[int, str]]:
        order_id = self._next_order_id
        self._next_order_id += 1
        return order_id

    async def close_position(self, order_id: Union[int, str], volume: float, price: float, slippage: int = 0) -> bool:
        return True

    async def modify_position(self, order_id: Union[int, str], new_sl: Optional[float] = None, new_tp: Optional[float] = None) -> bool:
        return True

    async def delete_pending_order(self, order_id: Union[int, str]) -> bool:
        return True