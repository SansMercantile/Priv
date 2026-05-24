# backend/trading_engine/broker_interface.py
from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, List, Optional, Union
import pandas as pd

# class BrokerInterface(ABC):
#    @abstractmethod
#    def execute_trade(self, trade_details: Dict[str, Any]) -> Dict[str, Any]:
#        """Executes a trade and returns execution metadata."""
#        pass
#
#    @abstractmethod
#    def get_account_status(self) -> Dict[str, Any]:
#        """Returns current account status including margin, balance, etc."""
#        pass

class BrokerInterface:
    def execute_trade(self, trade_details):
        print("Mock trade executed:", trade_details)
        return {"status": "success", "details": trade_details}

    def get_account_status(self):
        return {"balance": 100000, "margin": 50000}

class BrokerRouter:
    """
    Routes trade execution requests to the appropriate broker implementation.
    """
    def __init__(self, broker: Optional[Any] = None):
        self.broker = broker or self._get_default_broker()

    def _get_default_broker(self):
        # Return a mock or default broker for demo mode
        class MockBroker:
            def execute_trade(self, trade_details):
                print("Mock trade executed:", trade_details)
                return {"status": "success", "details": trade_details}
        return MockBroker()

    def execute(self, trade_details: Dict[str, Any]) -> Dict[str, Any]:
        return self.broker.execute_trade(trade_details)
    
class BaseTradeAPIAdapter(Protocol):
    name: str
    is_connected: bool
    
    async def connect(self) -> bool: ...
    async def disconnect(self) -> None: ...
    async def get_account_info(self) -> Dict[str, Any]: ...
    async def get_open_positions(self) -> List[Dict[str, Any]]: ...
    async def get_pending_orders(self) -> List[Dict[str, Any]]: ...
    async def get_historical_data(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]: ...
    async def send_order(
        self, order_type: str, symbol: str, volume: float, price: Optional[float] = None,
        slippage: int = 0, stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None, comment: str = "",
        magic_number: int = 0
    ) -> Optional[Union[int, str]]: ...
    async def close_position(
        self, order_id: Union[int, str], volume: float, price: float, slippage: int = 0
    ) -> bool: ...
    async def modify_position(
        self, order_id: Union[int, str], new_sl: Optional[float] = None, new_tp: Optional[float] = None
    ) -> bool: ...
    async def delete_pending_order(self, order_id: Union[int, str]) -> bool: ...