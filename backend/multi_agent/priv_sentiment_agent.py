# backend/multi_agent/priv_sentiment_agent.py

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

class PrivSentimentAgent(PrivAgent):
    """
    A specialized Priv Agent focused on analyzing market sentiment from various sources.
    This agent will generate trade proposals or sentiment reports based on its analysis.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.SENTIMENT, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.aggregated_sentiment: Dict[str, Any] = {"overall": "neutral", "score": 0.0, "last_update": None}
        self.latest_market_data: Dict[str, Dict[str, Any]] = {} 
        logger.info(f"Priv Sentiment Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the sentiment agent, subscribing to news insights (as a source of sentiment) and market data."""
        if self.is_running:
            logger.warning(f"Sentiment Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to news insights as a primary source for sentiment
        await self.broker.subscribe_to_topic("news_insights", self._handle_news_insight_for_sentiment, f"{self.agent_id}-news-insights-sub")
        # Subscribe to real-time market data
        await self.broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")

        self.is_running = True
        logger.info(f"Sentiment Agent '{self.agent_id}' started and subscribed to 'news_insights' and 'real_time_market_data'.")

    async def stop(self):
        """Stops the sentiment agent."""
        if not self.is_running:
            logger.warning(f"Sentiment Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Sentiment Agent '{self.agent_id}' stopped.")

    async def _handle_news_insight_for_sentiment(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming news insight messages and update aggregated sentiment.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            logger.info(f"Sentiment Agent '{self.agent_id}' received news insight for sentiment: {news_insight.get('headline', 'N/A')}")

            # --- Conceptual Sentiment Aggregation Logic ---
            sentiment_text = news_insight.get('sentiment', 'neutral')
            confidence_score = news_insight.get('confidence_score', 0.5)

            sentiment_map = {"highly_negative": -1.0, "negative": -0.5, "neutral": 0.0, "positive": 0.5, "highly_positive": 1.0}
            numerical_sentiment = sentiment_map.get(sentiment_text, 0.0)

            self.aggregated_sentiment = {
                "overall": sentiment_text,
                "score": numerical_sentiment * confidence_score, # Weighted by confidence
                "last_update": datetime.now().isoformat(),
                "source_headline": news_insight.get('headline')
            }
            logger.info(f"Sentiment Agent '{self.agent_id}' updated aggregated sentiment to: {self.aggregated_sentiment['overall']} (Score: {self.aggregated_sentiment['score']:.2f}).")

            sentiment_report_message = AgentMessage(
                sender_id=self.agent_id,
                message_type=MessageType.STATUS_UPDATE,
                payload=self.aggregated_sentiment
            )
            await self.broker.publish_message("market_sentiment_reports", sentiment_report_message.model_dump())
            logger.info(f"Sentiment Agent '{self.agent_id}' published market sentiment report.")

        except Exception as e:
            logger.error(f"Sentiment Agent '{self.agent_id}': Error processing news insight for sentiment: {e}", exc_info=True)

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
                logger.warning(f"Sentiment Agent: Received market data without a symbol: {market_data_item}")
                return

            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Sentiment Agent '{self.agent_id}' updated live data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Sentiment Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)


    # MODIFIED: Takes symbol as argument, uses internal state for current_price
    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on the current aggregated market sentiment and live market price.
        """
        logger.info(f"Sentiment Agent '{self.agent_id}' is generating a trade proposal based on sentiment for {symbol}...")

        live_data = self.latest_market_data.get(symbol)
        if not live_data or live_data.get("last_trade_price") is None:
            logger.warning(f"Sentiment Agent: No live market data (price) available for {symbol}. Cannot generate proposal.")
            return None
        current_price = live_data["last_trade_price"]


        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = "Sentiment analysis indicates no strong directional bias."
        
        sentiment_score = self.aggregated_sentiment.get("score", 0.0)

        if sentiment_score > 0.3: # Positive sentiment threshold
            action = TradeAction.BUY
            confidence = min(0.9, 0.5 + sentiment_score * 0.4) # Scale confidence
            reasoning = f"Overall market sentiment is positive: {self.aggregated_sentiment.get('source_headline', 'N/A')}."
        elif sentiment_score < -0.3: # Negative sentiment threshold
            action = TradeAction.SELL
            confidence = min(0.9, 0.5 + abs(sentiment_score) * 0.4) # Scale confidence
            reasoning = f"Overall market sentiment is negative: {self.aggregated_sentiment.get('source_headline', 'N/A')}."

        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol, # Use the symbol passed in
            action=action,
            volume=0.01, # Small volume for sentiment-based signals
            entry_price=current_price, # Use live current price
            reasoning=reasoning,
            confidence=confidence,
            risk_assessment={"sentiment_driven": True, "market_breadth": "broad"}
        )
        logger.info(f"Sentiment Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        return prop

# Example Usage (for testing PrivSentimentAgent in isolation)
async def main_sentiment_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType # Import AgentMessage, MessageType

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    sentiment_agent = PrivSentimentAgent(
        agent_id="Priv-Sentiment",
        broker=broker,
        persona={"name": "Market Sentiment Analyst", "focus": "Social & News Mood", "role": "sentiment_analyst"}
    )

    await broker.connect()
    await sentiment_agent.start()

    # Simulate news insights arriving (these would normally come from NewsAnalysisAgent)
    mock_news_insight_1 = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={"source": "News", "headline": "Strong Q4 earnings across the board.", "category": "business", "sentiment": "positive", "timestamp_processed": datetime.now().isoformat(), "confidence_score": 0.9}
    )
    mock_news_insight_2 = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={"source": "News", "headline": "Geopolitical tensions escalate in key region.", "category": "political", "sentiment": "highly_negative", "timestamp_processed": datetime.now().isoformat(), "confidence_score": 0.8}
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

    logger.info("\n--- Simulating news insights and real-time market data for Sentiment Agent to process ---")
    await broker.publish_message("news_insights", mock_news_insight_1.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_spx500.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("news_insights", mock_news_insight_2.model_dump())
    await asyncio.sleep(1) # Give agent time to process insights and market data

    # Generate a proposal after sentiment updates
    trade_proposal = await sentiment_agent.generate_trade_proposal("SPX500") # Pass the symbol
    if trade_proposal:
        logger.info(f"Sentiment Agent Proposal: {trade_proposal.action} {trade_proposal.symbol} (Confidence: {trade_proposal.confidence:.2f})")
    else:
        logger.info("Sentiment Agent: No proposal generated.")

    await asyncio.sleep(5)
    await sentiment_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivSentimentAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_sentiment_agent_test())