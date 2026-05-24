# backend/trading_engine/broker_api.py
"""
Comprehensive Broker Management API

This module provides a unified API for managing multiple broker connections,
executing trades, and monitoring positions across different brokers.

Supported Brokers:
- Interactive Brokers (IB)
- Alpaca
- Binance
- Deriv
- MetaTrader 5 (MT5)
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

# Import adapters with error handling for optional dependencies
try:
    from .adapters.ib_adapter import InteractiveBrokersAdapter
except ImportError as e:
    logging.warning(f"IB adapter not available: {e}")
    InteractiveBrokersAdapter = None

try:
    from .adapters.alpaca_adapter import AlpacaAPIAdapter
except Exception as e:
    logging.warning(f"Alpaca adapter not available: {e}")
    AlpacaAPIAdapter = None

try:
    from .adapters.binance_adapter import BinanceAdapter
except ImportError as e:
    logging.warning(f"Binance adapter not available: {e}")
    BinanceAdapter = None

try:
    from .adapters.deriv_adapter import DerivAPIAdapter
except ImportError as e:
    logging.warning(f"Deriv adapter not available: {e}")
    DerivAPIAdapter = None

try:
    from .adapters.mt5_adapter import MetaTrader5Adapter
except ImportError as e:
    logging.warning(f"MT5 adapter not available: {e}")
    MetaTrader5Adapter = None

logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    """Supported broker types"""
    INTERACTIVE_BROKERS = "ib"
    ALPACA = "alpaca"
    BINANCE = "binance"
    DERIV = "deriv"
    MT5 = "mt5"
    XM = "xm"


class BrokerManager:
    """
    Centralized broker management system.
    
    Features:
    - Multiple broker connections
    - Unified trading interface
    - Portfolio aggregation across brokers
    - Risk management and position tracking
    """
    
    def __init__(self):
        self.adapters: Dict[str, Any] = {}
        self.active_connections: Dict[str, bool] = {}
        logger.info("PRIV BrokerManager initialized")
    
    async def register_broker(
        self,
        broker_id: str,
        broker_type: BrokerType,
        config: Dict[str, Any]
    ) -> bool:
        """
        Register a new broker connection.
        
        Args:
            broker_id: Unique identifier for this broker connection
            broker_type: Type of broker (IB, Alpaca, etc.)
            config: Broker-specific configuration
        
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if broker_id in self.adapters:
                logger.warning(f"Broker {broker_id} already registered")
                return False
            
            # Create adapter based on broker type
            if broker_type == BrokerType.INTERACTIVE_BROKERS:
                if InteractiveBrokersAdapter is None:
                    raise ImportError("Interactive Brokers adapter not available")
                adapter = InteractiveBrokersAdapter(
                    host=config.get("host", "127.0.0.1"),
                    port=config.get("port", 7497),
                    client_id=config.get("client_id", 1),
                    account=config.get("account"),
                    readonly=config.get("readonly", False)
                )

            elif broker_type == BrokerType.ALPACA:
                if AlpacaAPIAdapter is None:
                    raise ImportError("Alpaca adapter not available")
                adapter = AlpacaAPIAdapter(
                    api_key=config.get("api_key"),
                    secret_key=config.get("secret_key"),
                    paper=config.get("paper", True)
                )

            elif broker_type == BrokerType.BINANCE:
                if BinanceAdapter is None:
                    raise ImportError("Binance adapter not available")
                adapter = BinanceAdapter(
                    api_key=config.get("api_key"),
                    secret_key=config.get("secret_key"),
                    testnet=config.get("testnet", True)
                )

            elif broker_type == BrokerType.DERIV:
                if DerivAPIAdapter is None:
                    raise ImportError("Deriv adapter not available")
                adapter = DerivAPIAdapter(
                    app_id=config.get("app_id"),
                    api_token=config.get("api_token")
                )

            elif broker_type == BrokerType.MT5:
                if MetaTrader5Adapter is None:
                    raise ImportError("MT5 adapter not available")
                adapter = MetaTrader5Adapter(
                    login=config.get("login"),
                    password=config.get("password"),
                    server=config.get("server")
                )

            elif broker_type == BrokerType.XM:
                from .adapters.xm_adapter import XmAdapter
                adapter = XmAdapter(
                    api_key=config.get("api_key") or config.get("account_id") or config.get("login") or config.get("email") or "XMGlobal-5824901",
                    api_secret=config.get("api_secret") or config.get("password") or "default_secret",
                    account_id=config.get("account_id"),
                    password=config.get("password"),
                    server=config.get("server") or "XMGlobal-MT5-Demo",
                    leverage=config.get("leverage") or "1:500"
                )

            else:
                logger.error(f"Unsupported broker type: {broker_type}")
                return False
            
            # Store adapter
            self.adapters[broker_id] = adapter
            self.active_connections[broker_id] = False
            
            logger.info(f"PRIV Broker {broker_id} ({broker_type}) registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering broker {broker_id}: {e}", exc_info=True)
            return False
    
    async def connect_broker(self, broker_id: str) -> bool:
        """Connect to a registered broker."""
        if broker_id not in self.adapters:
            logger.error(f"Broker {broker_id} not registered")
            return False
        
        try:
            adapter = self.adapters[broker_id]
            success = await adapter.connect()
            self.active_connections[broker_id] = success
            
            if success:
                logger.info(f"PRIV Connected to broker {broker_id}")
            else:
                logger.error(f"Failed to connect to broker {broker_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error connecting to broker {broker_id}: {e}", exc_info=True)
            return False
    
    async def disconnect_broker(self, broker_id: str) -> bool:
        """Disconnect from a broker."""
        if broker_id not in self.adapters:
            logger.error(f"Broker {broker_id} not registered")
            return False
        
        try:
            adapter = self.adapters[broker_id]
            await adapter.disconnect()
            self.active_connections[broker_id] = False

            logger.info(f"PRIV Disconnected from broker {broker_id}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting from broker {broker_id}: {e}", exc_info=True)
            return False

    async def get_broker_status(self, broker_id: str) -> Dict[str, Any]:
        """Get status of a specific broker."""
        if broker_id not in self.adapters:
            return {"error": f"Broker {broker_id} not registered"}

        adapter = self.adapters[broker_id]
        return {
            "broker_id": broker_id,
            "connected": self.active_connections.get(broker_id, False),
            "adapter_name": adapter.name if hasattr(adapter, 'name') else "Unknown"
        }

    async def get_all_brokers_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered brokers."""
        statuses = []
        for broker_id in self.adapters.keys():
            status = await self.get_broker_status(broker_id)
            statuses.append(status)
        return statuses

    async def get_account_info(self, broker_id: str) -> Dict[str, Any]:
        """Get account information from a specific broker."""
        if broker_id not in self.adapters:
            return {"error": f"Broker {broker_id} not registered"}

        if not self.active_connections.get(broker_id, False):
            if not await self.connect_broker(broker_id):
                return {"error": f"Failed to connect to broker {broker_id}"}

        try:
            adapter = self.adapters[broker_id]
            account_info = await adapter.get_account_info()
            account_info["broker_id"] = broker_id
            return account_info

        except Exception as e:
            logger.error(f"Error getting account info from {broker_id}: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_aggregated_portfolio(self) -> Dict[str, Any]:
        """Get aggregated portfolio across all connected brokers."""
        total_equity = 0.0
        total_balance = 0.0
        total_unrealized_pnl = 0.0
        broker_accounts = []

        for broker_id in self.adapters.keys():
            if self.active_connections.get(broker_id, False):
                account_info = await self.get_account_info(broker_id)

                if "error" not in account_info:
                    total_equity += account_info.get("equity", 0.0)
                    total_balance += account_info.get("balance", 0.0)
                    total_unrealized_pnl += account_info.get("unrealized_pnl", 0.0)
                    broker_accounts.append(account_info)

        return {
            "total_equity": total_equity,
            "total_balance": total_balance,
            "total_unrealized_pnl": total_unrealized_pnl,
            "broker_count": len(broker_accounts),
            "broker_accounts": broker_accounts,
            "timestamp": datetime.now().isoformat()
        }

    async def get_all_positions(self, broker_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Args:
            broker_id: Specific broker ID, or None for all brokers
        """
        all_positions = []

        if broker_id:
            # Get positions from specific broker
            if broker_id not in self.adapters:
                return []

            if not self.active_connections.get(broker_id, False):
                await self.connect_broker(broker_id)

            try:
                adapter = self.adapters[broker_id]
                positions = await adapter.get_open_positions()

                # Add broker_id to each position
                for pos in positions:
                    pos["broker_id"] = broker_id
                    all_positions.append(pos)

            except Exception as e:
                logger.error(f"Error getting positions from {broker_id}: {e}", exc_info=True)

        else:
            # Get positions from all connected brokers
            for bid in self.adapters.keys():
                if self.active_connections.get(bid, False):
                    try:
                        adapter = self.adapters[bid]
                        positions = await adapter.get_open_positions()

                        for pos in positions:
                            pos["broker_id"] = bid
                            all_positions.append(pos)

                    except Exception as e:
                        logger.error(f"Error getting positions from {bid}: {e}", exc_info=True)

        return all_positions

    async def get_all_orders(self, broker_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all pending orders.

        Args:
            broker_id: Specific broker ID, or None for all brokers
        """
        all_orders = []

        if broker_id:
            # Get orders from specific broker
            if broker_id not in self.adapters:
                return []

            if not self.active_connections.get(broker_id, False):
                await self.connect_broker(broker_id)

            try:
                adapter = self.adapters[broker_id]
                orders = await adapter.get_pending_orders()

                for order in orders:
                    order["broker_id"] = broker_id
                    all_orders.append(order)

            except Exception as e:
                logger.error(f"Error getting orders from {broker_id}: {e}", exc_info=True)

        else:
            # Get orders from all connected brokers
            for bid in self.adapters.keys():
                if self.active_connections.get(bid, False):
                    try:
                        adapter = self.adapters[bid]
                        orders = await adapter.get_pending_orders()

                        for order in orders:
                            order["broker_id"] = bid
                            all_orders.append(order)

                    except Exception as e:
                        logger.error(f"Error getting orders from {bid}: {e}", exc_info=True)

        return all_orders

    async def execute_trade(
        self,
        broker_id: str,
        order_type: str,
        symbol: str,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a trade on a specific broker.

        Args:
            broker_id: Broker to execute on
            order_type: Type of order (MARKET, LIMIT, STOP, etc.)
            symbol: Trading symbol
            volume: Order volume (positive for buy, negative for sell)
            price: Limit price (if applicable)
            stop_loss: Stop loss price
            take_profit: Take profit price
            **kwargs: Additional broker-specific parameters

        Returns:
            Dict with order_id and status
        """
        if broker_id not in self.adapters:
            return {"error": f"Broker {broker_id} not registered", "success": False}

        if not self.active_connections.get(broker_id, False):
            if not await self.connect_broker(broker_id):
                return {"error": f"Failed to connect to broker {broker_id}", "success": False}

        try:
            adapter = self.adapters[broker_id]

            order_id = await adapter.send_order(
                order_type=order_type,
                symbol=symbol,
                volume=volume,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                **kwargs
            )

            if order_id:
                logger.info(f"PRIV Trade executed on {broker_id}: {order_type} {volume} {symbol}")
                return {
                    "success": True,
                    "order_id": order_id,
                    "broker_id": broker_id,
                    "symbol": symbol,
                    "volume": volume,
                    "order_type": order_type,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": "Order execution failed", "success": False}

        except Exception as e:
            logger.error(f"Error executing trade on {broker_id}: {e}", exc_info=True)
            return {"error": str(e), "success": False}

    async def close_position(
        self,
        broker_id: str,
        symbol: str,
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Close a position on a specific broker.

        Args:
            broker_id: Broker ID
            symbol: Symbol to close
            volume: Volume to close (None for full position)
        """
        if broker_id not in self.adapters:
            return {"error": f"Broker {broker_id} not registered", "success": False}

        if not self.active_connections.get(broker_id, False):
            if not await self.connect_broker(broker_id):
                return {"error": f"Failed to connect to broker {broker_id}", "success": False}

        try:
            adapter = self.adapters[broker_id]

            # Get current position to determine volume if not specified
            if volume is None:
                positions = await adapter.get_open_positions()
                target_pos = next((p for p in positions if p['symbol'] == symbol), None)

                if not target_pos:
                    return {"error": f"No position found for {symbol}", "success": False}

                volume = abs(target_pos['volume'])

            # Close the position
            success = await adapter.close_position(
                order_id=symbol,
                volume=volume,
                price=0  # Market order
            )

            if success:
                logger.info(f"PRIV Position closed on {broker_id}: {symbol}")
                return {
                    "success": True,
                    "broker_id": broker_id,
                    "symbol": symbol,
                    "volume": volume,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": "Failed to close position", "success": False}

        except Exception as e:
            logger.error(f"Error closing position on {broker_id}: {e}", exc_info=True)
            return {"error": str(e), "success": False}

    async def cancel_order(self, broker_id: str, order_id: Union[int, str]) -> Dict[str, Any]:
        """Cancel a pending order."""
        if broker_id not in self.adapters:
            return {"error": f"Broker {broker_id} not registered", "success": False}

        if not self.active_connections.get(broker_id, False):
            if not await self.connect_broker(broker_id):
                return {"error": f"Failed to connect to broker {broker_id}", "success": False}

        try:
            adapter = self.adapters[broker_id]

            # Try cancel_order method if available
            if hasattr(adapter, 'cancel_order'):
                success = await adapter.cancel_order(order_id)
            # Fallback to delete_pending_order
            elif hasattr(adapter, 'delete_pending_order'):
                success = await adapter.delete_pending_order(order_id)
            else:
                return {"error": "Cancel order not supported by this broker", "success": False}

            if success:
                logger.info(f"PRIV Order cancelled on {broker_id}: {order_id}")
                return {
                    "success": True,
                    "broker_id": broker_id,
                    "order_id": order_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": "Failed to cancel order", "success": False}

        except Exception as e:
            logger.error(f"Error cancelling order on {broker_id}: {e}", exc_info=True)
            return {"error": str(e), "success": False}

    async def get_historical_data(
        self,
        broker_id: str,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> Optional[Any]:
        """Get historical market data from a broker."""
        if broker_id not in self.adapters:
            logger.error(f"Broker {broker_id} not registered")
            return None

        if not self.active_connections.get(broker_id, False):
            if not await self.connect_broker(broker_id):
                return None

        try:
            adapter = self.adapters[broker_id]
            return await adapter.get_historical_data(symbol, timeframe, limit)

        except Exception as e:
            logger.error(f"Error getting historical data from {broker_id}: {e}", exc_info=True)
            return None

    def get_registered_brokers(self) -> List[str]:
        """Get list of all registered broker IDs."""
        return list(self.adapters.keys())

    def get_connected_brokers(self) -> List[str]:
        """Get list of all connected broker IDs."""
        return [bid for bid, connected in self.active_connections.items() if connected]

    async def disconnect_all(self) -> None:
        """Disconnect from all brokers."""
        for broker_id in self.adapters.keys():
            if self.active_connections.get(broker_id, False):
                await self.disconnect_broker(broker_id)

        logger.info("PRIV Disconnected from all brokers")


# Global broker manager instance
broker_manager = BrokerManager()

