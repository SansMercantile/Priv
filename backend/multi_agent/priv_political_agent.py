# backend/multi_agent/priv_political_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivPoliticalAgent(PrivAgent):
    """
    A specialized Priv Agent focused on analyzing geopolitical events,
    policy changes, and their potential impact on financial markets.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.POLITICAL, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.geopolitical_outlook: Dict[str, Any] = {"stability": "neutral", "impact_risk": "low", "last_update": None}
        # NEW: Store latest market data for symbols this agent is interested in
        self.latest_market_data: Dict[str, Dict[str, Any]] = {} 
        logger.info(f"Priv Political Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the political agent, subscribing to news insights for political events and market data."""
        if self.is_running:
            logger.warning(f"Political Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to news insights, potentially filtering for political categories
        await self.message_broker.subscribe_to_topic("news_insights", self._handle_news_insight_for_political_analysis, f"{self.agent_id}-news-insights-sub")
        # NEW: Subscribe to real-time market data
        await self.message_broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")

        self.is_running = True
        logger.info(f"Political Agent '{self.agent_id}' started and subscribed to 'news_insights' and 'real_time_market_data'.")

    async def stop(self):
        """Stops the political agent."""
        if not self.is_running:
            logger.warning(f"Political Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Political Agent '{self.agent_id}' stopped.")

    async def _handle_news_insight_for_political_analysis(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming news insight messages for political analysis.
        Updates the agent's internal geopolitical outlook.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            category = news_insight.get('category', 'general')
            headline = news_insight.get('headline', 'No headline')
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact = news_insight.get('market_impact_assessment', 'unknown')

            if category == "political" or "geopolitical" in market_impact:
                logger.info(f"Political Agent '{self.agent_id}' received political news insight: {headline} (Sentiment: {sentiment})")

                # --- Conceptual Political Analysis Logic ---
                if sentiment == "negative" or sentiment == "highly_negative":
                    self.geopolitical_outlook["stability"] = "unstable"
                    self.geopolitical_outlook["impact_risk"] = "high"
                elif sentiment == "positive" or sentiment == "highly_positive":
                    self.geopolitical_outlook["stability"] = "stable"
                    self.geopolitical_outlook["impact_risk"] = "low"
                else:
                    self.geopolitical_outlook["stability"] = "neutral"
                    self.geopolitical_outlook["impact_risk"] = "medium"
                
                self.geopolitical_outlook["last_update"] = datetime.now().isoformat()
                self.geopolitical_outlook["last_headline"] = headline
                logger.info(f"Political Agent '{self.agent_id}' updated geopolitical outlook: Stability={self.geopolitical_outlook['stability']}, Risk={self.geopolitical_outlook['impact_risk']}.")

        except Exception as e:
            logger.error(f"Political Agent '{self.agent_id}': Error processing political news insight: {e}", exc_info=True)

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
                logger.warning(f"Political Agent: Received market data without a symbol: {market_data_item}")
                return

            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Political Agent '{self.agent_id}' updated live data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Political Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)


    # MODIFIED: Takes symbol as argument, uses internal state for current_price
    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on the current geopolitical outlook and live market price.
        """
        logger.info(f"Political Agent '{self.agent_id}' is generating a trade proposal based on geopolitical outlook for {symbol}...")

        live_data = self.latest_market_data.get(symbol)
        if not live_data or live_data.get("last_trade_price") is None:
            logger.warning(f"Political Agent: No live market data (price) available for {symbol}. Cannot generate proposal.")
            return None
        current_price = live_data["last_trade_price"]


        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = "Geopolitical outlook is neutral."
        
        stability = self.geopolitical_outlook.get("stability", "neutral")
        impact_risk = self.geopolitical_outlook.get("impact_risk", "low")
        last_headline = self.geopolitical_outlook.get("last_headline", "no recent political news")

        if stability == "unstable" and impact_risk == "high":
            action = TradeAction.SELL
            confidence = 0.8
            reasoning = f"High geopolitical instability detected: {last_headline}. Recommending SELL."
        elif stability == "stable" and impact_risk == "low":
            action = TradeAction.BUY
            confidence = 0.7
            reasoning = f"Stable geopolitical outlook: {last_headline}. Recommending BUY."

        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol, # Use the symbol passed in
            action=action,
            volume=0.1,
            entry_price=current_price, # Use live current price
            reasoning=reasoning,
            confidence=confidence,
            risk_assessment={"geopolitical_risk": impact_risk, "policy_impact": "high"}
        )
        logger.info(f"Political Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        return prop

# Example Usage (for testing PrivPoliticalAgent in isolation)
async def main_political_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType # Import AgentMessage, MessageType

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    political_agent = PrivPoliticalAgent(
        agent_id="Priv-Political",
        broker=broker,
        persona={"name": "Political Analyst", "focus": "Geopolitical Events", "role": "political_analyst"}
    )

    await broker.connect()
    await political_agent.start()

    # Simulate news insights arriving (these would normally come from NewsAnalysisAgent)
    mock_news_insight_positive_political = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={"source": "Gov News", "headline": "Major trade deal signed, easing global tensions.", "category": "political", "sentiment": "positive", "timestamp_processed": datetime.now().isoformat(), "market_impact_assessment": "broad_market_positive", "confidence_score": 0.8}
    )
    mock_news_insight_negative_political = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={"source": "Crisis Monitor", "headline": "Regional conflict escalates, threatening supply chains.", "category": "political", "sentiment": "highly_negative", "timestamp_processed": datetime.now().isoformat(), "market_impact_assessment": "high_volatility_commodities", "confidence_score": 0.9}
    )
    mock_news_insight_non_political = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={"source": "Business Wire", "headline": "Company X reports strong Q1 earnings.", "category": "business", "sentiment": "positive", "timestamp_processed": datetime.now().isoformat(), "market_impact_assessment": "stock_specific_positive", "confidence_score": 0.7}
    )

    # Simulate real-time market data for USDJPY
    mock_live_data_usdjpy = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "USDJPY", "bid_price": 150.00, "ask_price": 150.05, "last_trade_price": 150.02,
            "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )

    logger.info("\n--- Simulating news insights and real-time market data for Political Agent to process ---")
    await broker.publish_message("news_insights", mock_news_insight_positive_political.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_usdjpy.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("news_insights", mock_news_insight_negative_political.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("news_insights", mock_news_insight_non_political.model_dump()) # This should be ignored by political agent
    await asyncio.sleep(1) # Give agent time to process insights and market data

    # Generate a proposal after political outlook updates
    trade_proposal = await political_agent.generate_trade_proposal("USDJPY") # Pass the symbol
    if trade_proposal:
        logger.info(f"Political Agent Proposal: {trade_proposal.action} {trade_proposal.symbol} (Confidence: {trade_proposal.confidence:.2f})")
    else:
        logger.info("Political Agent: No proposal generated.")

    await asyncio.sleep(5)
    await political_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivPoliticalAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_political_agent_test())