# backend/multi_agent/priv_portfolio_manager_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List # Added List for type hinting
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivPortfolioManagerAgent(PrivAgent):
    """
    A specialized Priv Agent focused on overall portfolio management,
    including asset allocation, rebalancing, and strategic adjustments,
    now incorporating real-time market data and broker account data.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.PORTFOLIO_MANAGER, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.portfolio_composition: Dict[str, float] = {"stocks": 0.6, "bonds": 0.3, "commodities": 0.1} # Conceptual target allocation
        
        # Store actual live portfolio data from broker monitoring
        self.live_account_summaries: List[Dict[str, Any]] = [] # List of account summaries from different brokers
        self.live_open_positions: List[Dict[str, Any]] = []   # List of open positions from different brokers
        
        # Store latest market data for symbols it tracks (needed for accurate valuation)
        self.latest_market_data: Dict[str, Dict[str, Any]] = {} 

        # Derived values from live data
        self.current_total_equity: float = 0.0
        self.current_asset_holdings: Dict[str, float] = {} # Aggregated current holdings by symbol
        self.last_portfolio_update_time: Optional[datetime] = None

        logger.info(f"Priv Portfolio Manager Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the portfolio manager agent, subscribing to arbitration decisions, portfolio updates, and market data."""
        if self.is_running:
            logger.warning(f"Portfolio Manager Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to arbitration decisions (to track executed trades and their impact)
        await self.message_broker.subscribe_to_topic("arbitration_decisions", self._handle_arbitration_decision_for_portfolio, f"{self.agent_id}-arbitration-decisions-sub")
        # Subscribe to real-time portfolio updates from the BrokerAccountMonitor
        await self.message_broker.subscribe_to_topic("portfolio_updates", self._handle_portfolio_updates, f"{self.agent_id}-portfolio-updates-sub")
        # NEW: Subscribe to real-time market data to get current prices for valuation
        await self.message_broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")
        
        self.is_running = True
        logger.info(f"Portfolio Manager Agent '{self.agent_id}' started and subscribed to 'arbitration_decisions', 'portfolio_updates', and 'real_time_market_data'.")

    async def stop(self):
        """Stops the portfolio manager agent."""
        if not self.is_running:
            logger.warning(f"Portfolio Manager Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Portfolio Manager Agent '{self.agent_id}' stopped.")

    async def _handle_arbitration_decision_for_portfolio(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming arbitration decisions.
        In a real system, this would update internal models of executed trades.
        For now, we just log and acknowledge. Actual portfolio state comes from `_handle_portfolio_updates`.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            decision = agent_message.payload

            action = decision.get("action")
            symbol = decision.get("symbol")
            volume = decision.get("volume", 0.0)
            executed_price = decision.get("executed_price", decision.get("entry_price"))

            if decision.get("arbitration_outcome") == "APPROVED":
                logger.info(f"Portfolio Manager Agent: Noted APPROVED decision for {action} {volume} of {symbol} at {executed_price}.")
                # In a real system, you'd update an internal model of your positions here,
                # but the `portfolio_updates` from the broker monitoring will be the source of truth.
            else:
                logger.info(f"Portfolio Manager Agent: Noted REJECTED decision for {action} {symbol}.")

        except Exception as e:
            logger.error(f"Portfolio Manager Agent '{self.agent_id}': Error processing arbitration decision: {e}", exc_info=True)

    async def _handle_portfolio_updates(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time portfolio updates (account info, open positions).
        This is the primary source for the agent's current portfolio state.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            portfolio_data = agent_message.payload

            self.live_account_summaries = portfolio_data.get("account_summaries", [])
            self.live_open_positions = portfolio_data.get("open_positions", [])
            self.last_portfolio_update_time = datetime.fromisoformat(portfolio_data.get("timestamp"))

            # Aggregate total equity across all accounts
            self.current_total_equity = sum(acc.get('equity', acc.get('balance', 0.0)) for acc in self.live_account_summaries)
            
            # Aggregate current holdings by symbol
            self.current_asset_holdings.clear() # Clear previous holdings
            for pos in self.live_open_positions:
                symbol = pos.get('symbol')
                volume = pos.get('volume', 0.0)
                if symbol:
                    self.current_asset_holdings[symbol] = self.current_asset_holdings.get(symbol, 0.0) + volume
            
            logger.info(f"Portfolio Manager Agent '{self.agent_id}' updated with live portfolio data. Total Equity: ${self.current_total_equity:.2f}. Holdings: {self.current_asset_holdings}.")

            # OPTIONAL: Trigger rebalancing check immediately after portfolio update
            # This is a common pattern for portfolio managers.
            # await self.generate_trade_proposal()

        except Exception as e:
            logger.error(f"Portfolio Manager Agent '{self.agent_id}': Error processing portfolio update message: {e}", exc_info=True)

    async def _handle_real_time_market_data(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time market data messages.
        Updates the agent's internal state with the latest prices for relevant symbols,
        especially those in its portfolio.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload # Assuming payload is the market data dict

            symbol = market_data_item.get("symbol")
            if not symbol:
                logger.warning(f"Portfolio Manager Agent: Received market data without a symbol: {market_data_item}")
                return

            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Portfolio Manager Agent '{self.agent_id}' updated live market data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Portfolio Manager Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)


    async def generate_trade_proposal(self) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on real-time portfolio state and rebalancing needs.
        This method should be called periodically (e.g., by orchestrator) or on significant portfolio changes.
        """
        logger.info(f"Portfolio Manager Agent '{self.agent_id}' is checking portfolio for rebalancing needs...")

        if not self.live_account_summaries or not self.current_asset_holdings:
            logger.warning("Portfolio Manager: No live account or position data available. Cannot generate rebalancing proposal.")
            return None
        
        if self.current_total_equity <= 0:
            logger.warning("Portfolio Manager: Total equity is zero or negative. Cannot rebalance.")
            return None

        # --- Conceptual Rebalancing Logic using Live Data ---
        # This is a simplified example. A real rebalancer would:
        # 1. Map individual positions to asset classes (stocks, bonds, crypto, etc.).
        # 2. Calculate current allocation percentages based on `current_total_equity`.
        # 3. Compare with `self.portfolio_composition` (target allocations).
        # 4. Determine trades needed to bring allocations back in line.

        # For demonstration, let's assume 'SPY' represents our 'stocks' allocation.
        spy_holding_volume = self.current_asset_holdings.get("SPY", 0.0)
        
        # Get latest SPY price from internal market data cache
        spy_live_data = self.latest_market_data.get("SPY")
        spy_current_price = spy_live_data.get("last_trade_price") if spy_live_data else None

        if spy_current_price is None or spy_current_price <= 0:
            logger.warning("Portfolio Manager: No live price for SPY available in cache. Cannot perform rebalancing calculation for SPY.")
            # If SPY price is missing, try other symbols or simply return None if SPY is critical for rebalance.
            return None

        current_stocks_value = spy_holding_volume * spy_current_price
        
        # Calculate current allocation (avoid division by zero)
        current_stock_allocation = (current_stocks_value / self.current_total_equity) if self.current_total_equity > 0 else 0.0

        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = "Portfolio is balanced or insufficient data."
        volume_to_trade = 0.0
        symbol_to_trade = "SPY" # Default to SPY for rebalancing example

        target_stock_allocation = self.portfolio_composition.get("stocks", 0.6)
        rebalance_threshold = 0.05 # 5% deviation from target

        if current_stock_allocation < target_stock_allocation - rebalance_threshold:
            action = TradeAction.BUY
            confidence = 0.75
            reasoning = f"Portfolio rebalancing: Stocks ({current_stock_allocation:.2%}) are underweight, increasing allocation towards target {target_stock_allocation:.0%}. Current total equity: ${self.current_total_equity:.2f}."
            needed_value = (target_stock_allocation * self.current_total_equity) - current_stocks_value
            if spy_current_price > 0:
                volume_to_trade = needed_value / spy_current_price
            volume_to_trade = round(volume_to_trade, 2)
            
        elif current_stock_allocation > target_stock_allocation + rebalance_threshold:
            action = TradeAction.SELL
            confidence = 0.75
            reasoning = f"Portfolio rebalancing: Stocks ({current_stock_allocation:.2%}) are overweight, decreasing allocation towards target {target_stock_allocation:.0%}. Current total equity: ${self.current_total_equity:.2f}."
            excess_value = current_stocks_value - (target_stock_allocation * self.current_total_equity)
            if spy_current_price > 0:
                volume_to_trade = excess_value / spy_current_price
            volume_to_trade = round(volume_to_trade, 2)

        if action != TradeAction.HOLD and volume_to_trade > 0:
            prop = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol_to_trade,
                action=action,
                volume=volume_to_trade,
                entry_price=spy_current_price,
                reasoning=reasoning,
                confidence=confidence,
                risk_assessment={"portfolio_rebalancing": True, "long_term_strategy": True}
            )
            logger.info(f"Portfolio Manager Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} (Volume: {prop.volume:.2f}) with confidence {prop.confidence:.2f}.")
            return prop
        
        logger.info("Portfolio Manager: No rebalance proposal generated (current allocation is within threshold or no trade needed).")
        return None

# Example Usage (for testing PrivPortfolioManagerAgent in isolation)
async def main_portfolio_manager_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    portfolio_agent = PrivPortfolioManagerAgent(
        agent_id="Priv-PortfolioManager",
        broker=broker,
        persona={"name": "Portfolio Manager", "focus": "Asset Allocation", "role": "portfolio_manager"}
    )

    await broker.connect()
    await portfolio_agent.start()

    # Simulate initial portfolio holdings and account info (these would come from BrokerAccountMonitor)
    initial_portfolio_update = AgentMessage(
        sender_id="BrokerAccountMonitor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "timestamp": datetime.now().isoformat(),
            "account_summaries": [
                {"adapter_name": "MockBroker", "balance": 100000.0, "equity": 100000.0, "currency": "USD"}
            ],
            "open_positions": [
                {"adapter_name": "MockBroker", "symbol": "SPY", "volume": 100.0, "current_price": 500.0}, # 100 shares of SPY at $500
                {"adapter_name": "MockBroker", "symbol": "TLT", "volume": 50.0, "current_price": 100.0}  # 50 shares of TLT at $100
            ]
        }
    )
    logger.info("\n--- Simulating initial portfolio update for Portfolio Manager ---")
    await broker.publish_message("portfolio_updates", initial_portfolio_update.model_dump())
    await asyncio.sleep(1) # Give agent time to process

    logger.info(f"Portfolio Value after initial update: ${portfolio_agent.current_total_equity:.2f}")
    logger.info(f"Portfolio Holdings: {portfolio_agent.current_asset_holdings}")

    # Simulate market data for SPY (essential for rebalancing calculation)
    mock_live_data_spy = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "SPY", "bid_price": 480.00, "ask_price": 480.10, "last_trade_price": 480.05,
            "timestamp": (datetime.now() + timedelta(seconds=1)).timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"
        }
    )
    logger.info("\n--- Simulating SPY price drop (to trigger rebalance buy) ---")
    await broker.publish_message("real_time_market_data", mock_live_data_spy.model_dump())
    await asyncio.sleep(1) # Give agent time to process

    # Trigger rebalancing check
    logger.info("\n--- Portfolio Manager checking for rebalancing (expecting BUY proposal) ---")
    rebalance_proposal = await portfolio_agent.generate_trade_proposal()
    if rebalance_proposal:
        logger.info(f"Portfolio Manager Rebalance Proposal: {rebalance_proposal.action} {rebalance_proposal.symbol} (Volume: {rebalance_proposal.volume:.2f}, Confidence: {rebalance_proposal.confidence:.2f})")
    else:
        logger.info("Portfolio Manager: No rebalance proposal generated.")

    await asyncio.sleep(5)
    await portfolio_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivPortfolioManagerAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_portfolio_manager_agent_test())