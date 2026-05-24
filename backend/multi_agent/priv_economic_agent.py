# backend/multi_agent/priv_economic_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivEconomicAgent(PrivAgent):
    """
    A specialized Priv Agent focused on economic impulses and macroeconomic data.
    This agent will generate trade proposals based on economic analysis.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ECONOMIC, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.economic_outlook: Dict[str, Any] = {"GDP_growth": "neutral", "inflation": "stable", "last_update": None}
        # NEW: Store latest market data for symbols this agent is interested in
        self.latest_market_data: Dict[str, Dict[str, Any]] = {} # e.g., {"EURUSD": {"price": 1.0850, "timestamp": "...", "source": "..."}}
        # NEW: Store latest economic calendar data (conceptual for now, will connect to manager later)
        self.latest_economic_calendar_events: List[Dict[str, Any]] = []
        logger.info(f"Priv Economic Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the economic agent."""
        if self.is_running:
            logger.warning(f"Economic Agent '{self.agent_id}' is already running.")
            return

        # NEW: Subscribe to real-time market data
        await self.message_broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")
        # OPTIONAL: Subscribe to economic calendar events if you publish them to Pub/Sub
        # await self.message_broker.subscribe_to_topic("economic_calendar_events", self._handle_economic_calendar_event)
        
        self.is_running = True
        logger.info(f"Economic Agent '{self.agent_id}' started and subscribed to 'real_time_market_data'.")

    async def stop(self):
        """Stops the economic agent."""
        if not self.is_running:
            logger.warning(f"Economic Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Economic Agent '{self.agent_id}' stopped.")

    async def _handle_real_time_market_data(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time market data messages.
        Updates the agent's internal state with the latest prices for relevant symbols.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload # Assuming payload is the market data dict

            symbol = market_data_item.get("symbol")
            if not symbol:
                logger.warning(f"Economic Agent: Received market data without a symbol: {market_data_item}")
                return

            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Economic Agent '{self.agent_id}' updated live data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Economic Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)

    # OPTIONAL: Placeholder for handling economic calendar events
    # async def _handle_economic_calendar_event(self, message_payload: Dict[str, Any]):
    #     try:
    #         agent_message = AgentMessage.model_validate(message_payload)
    #         event = agent_message.payload # Assuming payload is the EconomicEvent dict
    #         logger.info(f"Economic Agent received economic event: {event.get('event_name')}")
    #         self.latest_economic_calendar_events.append(event)
    #         # Logic to process and update economic_outlook based on new event
    #     except Exception as e:
    #         logger.error(f"Economic Agent: Error processing economic calendar event: {e}", exc_info=True)


    # Conceptual method for generating a trade proposal based on economic analysis
    # MODIFIED: Takes symbol as argument, uses internal state for current_price
    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on conceptual economic data and live market price.
        """
        logger.info(f"Economic Agent '{self.agent_id}' is performing economic analysis and generating a proposal for {symbol}...")

        live_data = self.latest_market_data.get(symbol)
        if not live_data or live_data.get("last_trade_price") is None:
            logger.warning(f"Economic Agent: No live market data (price) available for {symbol}. Cannot generate proposal.")
            return None
        current_price = live_data["last_trade_price"]

        # --- Conceptual Economic Analysis Logic ---
        # In a real system, this would analyze actual economic data (GDP, CPI, interest rates)
        # potentially from your EconomicCalendarManager or other direct economic data feeds.
        # For now, we use a simplified conceptual model.

        # Retrieve economic outlook from internal state (updated by an upstream process or separate subscription)
        gdp_growth = self.economic_outlook.get("GDP_growth", "neutral")
        inflation_outlook = self.economic_outlook.get("inflation", "stable")
        interest_rate_expectations = self.economic_outlook.get("interest_rates", "neutral")

        action = TradeAction.HOLD
        confidence = 0.6
        reasoning = "Economic analysis indicates no strong directional bias or insufficient data."

        if gdp_growth == "strong" and inflation_outlook == "low" and interest_rate_expectations == "rising":
            action = TradeAction.BUY
            confidence = 0.85
            reasoning = "Strong GDP, low inflation, and rising rates suggest currency strength."
        elif gdp_growth == "weak" and inflation_outlook == "high" and interest_rate_expectations == "falling":
            action = TradeAction.SELL
            confidence = 0.85
            reasoning = "Weak GDP, high inflation, and falling rates suggest currency weakness."
        elif interest_rate_expectations == "hawkish":
            action = TradeAction.BUY
            confidence = 0.75
            reasoning = "Hawkish central bank stance indicates potential currency appreciation."
        elif interest_rate_expectations == "dovish":
            action = TradeAction.SELL
            confidence = 0.75
            reasoning = "Dovish central bank stance indicates potential currency depreciation."

        # Update internal outlook (this would typically be done by a dedicated handler or external input)
        # For this demo, we'll keep it as-is to show how the current_price is now taken from live data.
        # self.economic_outlook = { ... }

        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            volume=0.1,
            entry_price=current_price, # Using live current price
            reasoning=reasoning,
            confidence=confidence,
            risk_assessment={"economic_risk": "high", "policy_uncertainty": "low"}
        )
        logger.info(f"Economic Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        return prop

# Example Usage (for testing PrivEconomicAgent in isolation)
async def main_economic_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType # Import AgentMessage, MessageType

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    economic_agent = PrivEconomicAgent(
        agent_id="Priv-Economic",
        broker=broker,
        persona={"name": "Economic Analyst", "focus": "Macroeconomic Trends"}
    )

    await broker.connect()
    await economic_agent.start()

    # Simulate real-time market data arrival (for the agent to use in generate_trade_proposal)
    mock_live_data_usdjpy = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "USDJPY", "bid_price": 150.00, "ask_price": 150.05, "last_trade_price": 150.02,
            "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )
    mock_live_data_eurusd = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "EURUSD", "bid_price": 1.0800, "ask_price": 1.0805, "last_trade_price": 1.0802,
            "timestamp": (datetime.now() + timedelta(seconds=1)).timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"
        }
    )
    mock_live_data_gbpusd = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "GBPUSD", "bid_price": 1.2500, "ask_price": 1.2505, "last_trade_price": 1.2502,
            "timestamp": (datetime.now() + timedelta(seconds=2)).timestamp() * 1e9, "source": "TwelveData.com", "type": "market_data_quote"
        }
    )

    logger.info("\n--- Simulating real-time market data arrival for Economic Agent ---")
    await broker.publish_message("real_time_market_data", mock_live_data_usdjpy.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_eurusd.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_gbpusd.model_dump())
    await asyncio.sleep(1) # Give agent time to process the incoming data

    # Simulate setting conceptual economic outlook (this would come from another module/agent)
    economic_agent.economic_outlook = {
        "GDP_growth": "strong", "inflation": "low", "interest_rates": "rising", "last_update": datetime.now().isoformat()
    }

    logger.info("\n--- Economic Agent generating proposals using internal live data ---")
    prop1 = await economic_agent.generate_trade_proposal("USDJPY")
    if prop1:
        logger.info(f"Economic Agent Proposal 1 (USDJPY): {prop1.action} {prop1.symbol} (Confidence: {prop1.confidence:.2f})")

    # Change conceptual economic outlook to trigger a SELL
    economic_agent.economic_outlook = {
        "GDP_growth": "weak", "inflation": "high", "interest_rates": "falling", "last_update": datetime.now().isoformat()
    }
    prop2 = await economic_agent.generate_trade_proposal("EURUSD")
    if prop2:
        logger.info(f"Economic Agent Proposal 2 (EURUSD): {prop2.action} {prop2.symbol} (Confidence: {prop2.confidence:.2f})")

    # Change conceptual economic outlook to trigger another BUY
    economic_agent.economic_outlook = {
        "GDP_growth": "neutral", "inflation": "stable", "interest_rates": "hawkish", "last_update": datetime.now().isoformat()
    }
    prop3 = await economic_agent.generate_trade_proposal("GBPUSD")
    if prop3:
        logger.info(f"Economic Agent Proposal 3 (GBPUSD): {prop3.action} {prop3.symbol} (Confidence: {prop3.confidence:.2f})")
    
    prop_no_data = await economic_agent.generate_trade_proposal("NONEXISTENT_SYMBOL")
    if prop_no_data:
        logger.info("Unexpected proposal for NONEXISTENT_SYMBOL.")
    else:
        logger.info("Correctly did not generate proposal for NONEXISTENT_SYMBOL (no live data).")


    await asyncio.sleep(2)
    await economic_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivEconomicAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_economic_agent_test())