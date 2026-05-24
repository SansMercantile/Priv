# backend/multi_agent/priv_strategist_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from datetime import timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivStrategistAgent(PrivAgent):
    """
    A specialized Priv Agent focused on strategic trade proposal generation,
    now incorporating news insights and real-time market data.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.STRATEGIST, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.current_market_sentiment: Dict[str, Any] = {"overall": "neutral", "last_update": None}
        # NEW: Store latest market data for symbols this agent is interested in
        self.latest_market_data: Dict[str, Dict[str, Any]] = {} # e.g., {"SPX500": {"price": 5200.0, "timestamp": "...", "source": "..."}}
        logger.info(f"Priv Strategist Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the strategist agent, subscribing to news insights and market data."""
        if self.is_running:
            logger.warning(f"Strategist Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to the news_insights topic
        await self.message_broker.subscribe_to_topic("news_insights", self._handle_news_insight_message, f"{self.agent_id}-news-insights-sub")
        # NEW: Subscribe to real-time market data
        await self.message_broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")

        self.is_running = True
        logger.info(f"Strategist Agent '{self.agent_id}' started and subscribed to 'news_insights' and 'real_time_market_data'.")

    async def stop(self):
        """Stops the strategist agent."""
        if not self.is_running:
            logger.warning(f"Strategist Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Strategist Agent '{self.agent_id}' stopped.")

    async def _handle_news_insight_message(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming news insight messages.
        Updates the agent's internal market sentiment based on news.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload # Assuming payload is the news insight dict

            logger.info(f"Strategist Agent '{self.agent_id}' received news insight: {news_insight.get('headline', 'N/A')} (Sentiment: {news_insight.get('sentiment')})")

            # --- Conceptual Logic: Update internal market sentiment ---
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact = news_insight.get('market_impact_assessment', 'unknown')
            
            self.current_market_sentiment = {
                "overall": sentiment,
                "last_update": news_insight.get("timestamp_processed"),
                "impact": market_impact,
                "headline": news_insight.get("headline")
            }
            logger.info(f"Strategist Agent '{self.agent_id}' updated internal market sentiment to: {self.current_market_sentiment['overall']}.")

        except Exception as e:
            logger.error(f"Strategist Agent '{self.agent_id}': Error processing news insight message: {e}", exc_info=True)

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
                logger.warning(f"Strategist Agent: Received market data without a symbol: {market_data_item}")
                return

            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Strategist Agent '{self.agent_id}' updated live data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Strategist Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)

    # Conceptual method for generating a trade proposal based on market conditions and news
    # MODIFIED: Takes symbol as argument, uses internal state for current_price
    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on current market data and internal sentiment.
        """
        logger.info(f"Strategist Agent '{self.agent_id}' is generating a trade proposal for {symbol}...")

        live_data = self.latest_market_data.get(symbol)
        if not live_data or live_data.get("last_trade_price") is None:
            logger.warning(f"Strategist Agent: No live market data (price) available for {symbol}. Cannot generate proposal.")
            return None
        current_price = live_data["last_trade_price"]

        # Example: Adjust confidence and action based on news sentiment
        base_confidence = 0.7
        reason_suffix = ""
        action = TradeAction.HOLD # Default action

        if self.current_market_sentiment['overall'] == 'positive':
            base_confidence += 0.1
            action = TradeAction.BUY
            reason_suffix = f" (influenced by positive news: {self.current_market_sentiment.get('headline', 'N/A')})"
        elif self.current_market_sentiment['overall'] == 'negative':
            base_confidence -= 0.1
            action = TradeAction.SELL
            reason_suffix = f" (influenced by negative news: {self.current_market_sentiment.get('headline', 'N/A')})"
        elif self.current_market_sentiment['overall'] == 'highly_negative':
            base_confidence -= 0.2
            action = TradeAction.SELL
            reason_suffix = f" (strongly influenced by highly negative news: {self.current_market_sentiment.get('headline', 'N/A')})"
        
        # Clamp confidence
        adjusted_confidence = max(0.1, min(1.0, base_confidence))

        # Simulate a trade proposal
        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            volume=0.1,
            entry_price=current_price, # Using live current price
            reasoning=f"Market analysis indicates {action.value} opportunity{reason_suffix}.",
            confidence=adjusted_confidence,
            risk_assessment={"per_trade_risk_pct": 0.5, "rr_ratio": 2.0}
        )
        logger.info(f"Strategist Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        return prop

# Example Usage (for testing PrivStrategistAgent in isolation)
async def main_strategist_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType # Import AgentMessage, MessageType

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    strategist_agent = PrivStrategistAgent(
        agent_id="Priv-Strategist",
        broker=broker,
        persona={"name": "Market Strategist", "focus": "Global Macro"}
    )

    await broker.connect()
    await strategist_agent.start()

    # Simulate a news insight arriving (positive)
    mock_news_insight_positive = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "source": "Mock News",
            "headline": "Global GDP growth exceeds expectations, boosting investor confidence.",
            "category": "economic",
            "sentiment": "positive",
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "broad_market_positive",
            "confidence_score": 0.9
        }
    )
    # Simulate a news insight arriving (negative)
    mock_news_insight_negative = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "source": "Mock News",
            "headline": "Unexpected rate hike fears rattle markets.",
            "category": "economic",
            "sentiment": "negative",
            "timestamp_processed": (datetime.now() + timedelta(seconds=1)).isoformat(),
            "market_impact_assessment": "broad_market_negative",
            "confidence_score": 0.8
        }
    )

    # Simulate real-time market data for SPX500
    mock_live_data_spx500 = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "SPX500", "bid_price": 5200.00, "ask_price": 5201.00, "last_trade_price": 5200.50,
            "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )

    logger.info("\n--- Simulating news insights and real-time market data arrival for Strategist Agent ---")
    await broker.publish_message("news_insights", mock_news_insight_positive.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_spx500.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("news_insights", mock_news_insight_negative.model_dump())
    await asyncio.sleep(1) # Give agent time to process

    logger.info("\n--- Strategist Agent generating proposals using internal data ---")
    prop1 = await strategist_agent.generate_trade_proposal("SPX500")
    if prop1:
        logger.info(f"Strategist Proposal 1 (SPX500): {prop1.action} {prop1.symbol} (Confidence: {prop1.confidence:.2f})")

    prop_no_data = await strategist_agent.generate_trade_proposal("NONEXISTENT_SYMBOL")
    if prop_no_data:
        logger.info("Unexpected proposal for NONEXISTENT_SYMBOL.")
    else:
        logger.info("Correctly did not generate proposal for NONEXISTENT_SYMBOL (no live data).")

    await asyncio.sleep(2)
    await strategist_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivStrategistAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_strategist_agent_test())