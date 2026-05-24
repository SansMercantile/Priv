# backend/trading_engine/priv_trading_engine.py

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from backend.trading_engine.broker_interface import BrokerInterface
from backend.trading_engine.trade_executor_class import TradeExecutor
from backend.trading_engine.broker_router import BrokerRouter

logger = logging.getLogger(__name__)

class PRIVTradingEngine:
    """
    PRIV Trading Engine - Main trading engine for the PRIV system.
    Coordinates between broker interfaces, trade execution, and order management.
    """
    
    def __init__(self):
        self.broker_router = BrokerRouter()
        self.trade_executor = TradeExecutor()
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.info("PRIVTradingEngine initialized")
    
    async def initialize(self) -> bool:
        """Initialize the trading engine"""
        try:
            self.logger.info("Initializing PRIV Trading Engine")
            # Initialize components
            await self.broker_router.initialize()
            await self.trade_executor.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize trading engine: {e}", exc_info=True)
            return False
    
    async def execute_trade(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade request through the trading engine.
        
        Args:
            trade_request: Trade request containing symbol, action, quantity, etc.
            
        Returns:
            Trade execution result
        """
        try:
            self.logger.info(f"Processing trade request: {trade_request}")
            
            # Validate trade request
            if not self._validate_trade_request(trade_request):
                return {"status": "failed", "error": "Invalid trade request"}
            
            # Route to appropriate broker
            broker = self.broker_router.select_broker(trade_request)
            if not broker:
                return {"status": "failed", "error": "No suitable broker found"}
            
            # Execute trade
            result = await self.trade_executor.execute_trade(trade_request, broker)
            
            self.logger.info(f"Trade executed successfully: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    def _validate_trade_request(self, trade_request: Dict[str, Any]) -> bool:
        """Validate trade request format and content"""
        required_fields = ["symbol", "action", "quantity"]
        for field in required_fields:
            if field not in trade_request:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate action type
        valid_actions = ["buy", "sell", "hold", "close"]
        if trade_request["action"].lower() not in valid_actions:
            self.logger.error(f"Invalid action: {trade_request['action']}")
            return False
        
        # Validate quantity
        quantity = trade_request.get("quantity", 0)
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            self.logger.error(f"Invalid quantity: {quantity}")
            return False
        
        return True
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a symbol"""
        try:
            self.logger.info(f"Getting market data for: {symbol}")
            
            # Get data from broker router
            market_data = await self.broker_router.get_market_data(symbol)
            
            if market_data:
                self.logger.info(f"Market data retrieved for {symbol}")
                return market_data
            else:
                self.logger.warning(f"No market data available for {symbol}")
                return {"status": "no_data", "symbol": symbol}
                
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}", exc_info=True)
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status"""
        try:
            self.logger.info("Getting portfolio status")
            
            # Get status from all connected brokers
            portfolio_data = {}
            for broker_name, broker in self.broker_router.get_connected_brokers().items():
                try:
                    status = await broker.get_portfolio_status()
                    portfolio_data[broker_name] = status
                except Exception as e:
                    self.logger.error(f"Error getting status from {broker_name}: {e}")
                    portfolio_data[broker_name] = {"status": "error", "error": str(e)}
            
            return {
                "status": "success",
                "portfolio_data": portfolio_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def handle_risk_event(self, risk_event: Dict[str, Any]) -> bool:
        """Handle risk events and take appropriate action"""
        try:
            self.logger.warning(f"Handling risk event: {risk_event}")
            
            # Evaluate risk level
            risk_level = risk_event.get("risk_level", "medium")
            
            if risk_level == "high":
                # Immediate action required
                self.logger.critical("High risk event detected - taking protective action")
                
                # Close risky positions
                await self._close_risky_positions(risk_event)
                
                # Notify all relevant parties
                await self._broadcast_risk_alert(risk_event)
                
            elif risk_level == "medium":
                # Monitor and reduce exposure
                self.logger.warning("Medium risk event detected - reducing exposure")
                await self._reduce_exposure(risk_event)
                
            else:
                # Log and monitor
                self.logger.info(f"Low risk event: {risk_event}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling risk event: {e}", exc_info=True)
            return False
    
    async def _close_risky_positions(self, risk_event: Dict[str, Any]):
        """Close positions deemed risky"""
        try:
            self.logger.info("Closing risky positions")
            
            # Get current positions
            portfolio_status = await self.get_portfolio_status()
            if portfolio_status["status"] == "success":
                # Analyze positions and close risky ones
                for broker_name, broker_data in portfolio_status["portfolio_data"].items():
                    if broker_data.get("status") == "success":
                        positions = broker_data.get("positions", [])
                        for position in positions:
                            if self._is_position_risky(position, risk_event):
                                # Close the position
                                close_request = {
                                    "symbol": position["symbol"],
                                    "action": "close",
                                    "quantity": position["quantity"]
                                }
                                await self.execute_trade(close_request)
            
        except Exception as e:
            self.logger.error(f"Error closing risky positions: {e}", exc_info=True)
    
    async def _reduce_exposure(self, risk_event: Dict[str, Any]):
        """Reduce exposure to risky assets"""
        try:
            self.logger.info("Reducing exposure to risky assets")
            
            # Implement exposure reduction logic
            # This could involve partial position closures, hedging, etc.
            
        except Exception as e:
            self.logger.error(f"Error reducing exposure: {e}", exc_info=True)
    
    async def _broadcast_risk_alert(self, risk_event: Dict[str, Any]):
        """Broadcast risk alert to all relevant parties"""
        try:
            self.logger.critical("Broadcasting risk alert")
            
            alert_message = {
                "type": "risk_alert",
                "risk_level": risk_event.get("risk_level", "unknown"),
                "description": risk_event.get("description", "Risk event occurred"),
                "timestamp": datetime.now().isoformat(),
                "recommended_action": "Review and adjust positions"
            }
            
            # This would typically send notifications, emails, etc.
            self.logger.critical(f"RISK ALERT: {alert_message}")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting risk alert: {e}", exc_info=True)
    
    def _is_position_risky(self, position: Dict[str, Any], risk_event: Dict[str, Any]) -> bool:
        """Determine if a position is risky based on the risk event"""
        try:
            # Simple risk assessment - can be enhanced with more sophisticated logic
            symbol = position.get("symbol", "")
            risk_symbols = risk_event.get("affected_symbols", [])
            
            if symbol in risk_symbols:
                return True
            
            # Add more risk assessment logic here
            return False
            
        except Exception as e:
            self.logger.error(f"Error assessing position risk: {e}", exc_info=True)
            return False