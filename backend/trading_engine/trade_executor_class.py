# backend/trading_engine/trade_executor_class.py

import logging
from typing import Dict, Any, Optional, Union
import asyncio

# Import the existing functions from trade_executor.py
from .trade_executor import (
    execute_market_order,
    execute_pending_order,
    close_position_by_id,
    modify_position_sltp,
    modify_pending_order_sltp,
    delete_pending_order,
    apply_trailing_pending_orders,
    apply_trailing_stop,
    apply_move_to_breakeven
)

logger = logging.getLogger(__name__)

class TradeExecutor:
    """
    Trade Executor class that wraps the existing trade execution functions.
    Provides a unified interface for trade execution operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.info("TradeExecutor initialized")
    
    async def initialize(self) -> bool:
        """Initialize the trade executor"""
        try:
            self.logger.info("Initializing TradeExecutor")
            # No specific initialization needed for the function-based approach
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TradeExecutor: {e}", exc_info=True)
            return False
    
    async def execute_trade(self, trade_request: Dict[str, Any], broker) -> Dict[str, Any]:
        """
        Execute a trade based on the trade request.
        
        Args:
            trade_request: Dictionary containing trade details
            broker: Broker interface for execution
            
        Returns:
            Trade execution result
        """
        try:
            self.logger.info(f"Executing trade: {trade_request}")
            
            # Extract trade details
            symbol = trade_request.get("symbol")
            action = trade_request.get("action", "buy")
            order_type = trade_request.get("order_type", "market")
            quantity = trade_request.get("quantity", 1)
            price = trade_request.get("price")
            
            # Route to appropriate execution function
            if order_type.lower() == "market":
                result = await execute_market_order(
                    symbol=symbol,
                    order_type=action.upper(),
                    volume=quantity,
                    slippage=trade_request.get("slippage", 3),
                    comment=trade_request.get("comment", ""),
                    symbol_info=trade_request.get("symbol_info", {}),
                    symbol_prices=trade_request.get("symbol_prices", {})
                )
            elif order_type.lower() == "pending":
                result = await execute_pending_order(
                    symbol=symbol,
                    order_type=action.upper(),
                    volume=quantity,
                    price=price,
                    slippage=trade_request.get("slippage", 3),
                    comment=trade_request.get("comment", ""),
                    symbol_info=trade_request.get("symbol_info", {}),
                    symbol_prices=trade_request.get("symbol_prices", {})
                )
            else:
                return {"status": "failed", "error": f"Unsupported order type: {order_type}"}
            
            self.logger.info(f"Trade executed successfully: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    async def close_position(self, position_id: Union[int, str], symbol_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Close a position by ID.
        
        Args:
            position_id: Position identifier
            symbol_info: Optional symbol information
            
        Returns:
            Success status
        """
        try:
            self.logger.info(f"Closing position: {position_id}")
            result = await close_position_by_id(position_id, symbol_info or {})
            self.logger.info(f"Position closed: {position_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error closing position {position_id}: {e}", exc_info=True)
            return False
    
    async def modify_position(self, position_id: Union[int, str], sl_price: Optional[float] = None, 
                            tp_price: Optional[float] = None, symbol_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Modify position stop loss and take profit.
        
        Args:
            position_id: Position identifier
            sl_price: New stop loss price
            tp_price: New take profit price
            symbol_info: Optional symbol information
            
        Returns:
            Success status
        """
        try:
            self.logger.info(f"Modifying position {position_id}: SL={sl_price}, TP={tp_price}")
            result = await modify_position_sltp(position_id, sl_price, tp_price, symbol_info or {})
            self.logger.info(f"Position modified: {position_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error modifying position {position_id}: {e}", exc_info=True)
            return False
    
    async def delete_pending_order(self, order_id: Union[int, str]) -> bool:
        """
        Delete a pending order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Success status
        """
        try:
            self.logger.info(f"Deleting pending order: {order_id}")
            result = await delete_pending_order(order_id)
            self.logger.info(f"Pending order deleted: {order_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting pending order {order_id}: {e}", exc_info=True)
            return False
    
    async def apply_trailing_features(self, symbol: str, symbol_info: Optional[Dict[str, Any]] = None):
        """
        Apply trailing stop and other trailing features.
        
        Args:
            symbol: Symbol to apply trailing to
            symbol_info: Optional symbol information
        """
        try:
            self.logger.info(f"Applying trailing features for: {symbol}")
            
            # Apply trailing stop
            await apply_trailing_stop(symbol, symbol_info or {})
            
            # Apply trailing pending orders
            await apply_trailing_pending_orders(symbol, symbol_info or {})
            
            # Apply move to breakeven
            await apply_move_to_breakeven(symbol, symbol_info or {})
            
            self.logger.info(f"Trailing features applied for: {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error applying trailing features for {symbol}: {e}", exc_info=True)