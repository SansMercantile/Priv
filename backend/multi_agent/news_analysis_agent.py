import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.multi_agent.priv_agent import PrivAgent # For conceptual agent identity

logger = logging.getLogger(__name__)

class NewsAnalysisAgent(PrivAgent): # Inherit from PrivAgent for consistency
    """
    A specialized agent responsible for consuming raw news data,
    performing analysis, and publishing structured news insights.
    """
    def __init__(self, agent_id: str, message_broker: MessageBrokerInterface, persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.NEWS_ANALYSIS,persona=persona)
        self.broker = message_broker
        self.is_running = False
        logger.info(f"Priv NewsAnalysisAgent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the news analysis agent, subscribing to raw news events."""
        if self.is_running:
            logger.warning(f"NewsAnalysisAgent '{self.agent_id}' is already running.")
            return

        # MODIFIED: Subscribe to the raw_news_events topic using the dedicated agent subscription
        await self.broker.subscribe_to_topic("raw_news_events", self._handle_raw_news_message, subscription_suffix="-agent-sub")
        self.is_running = True
        logger.info(f"NewsAnalysisAgent '{self.agent_id}' started and subscribed to 'raw_news_events' via 'raw_news_events-agent-sub'.")

    async def stop(self):
        """Stops the news analysis agent."""
        if not self.is_running:
            logger.warning(f"NewsAnalysisAgent '{self.agent_id}' is not running.")
            return
        
        # In a real scenario, you might need to explicitly unsubscribe or wait for pending tasks.
        self.is_running = False
        logger.info(f"NewsAnalysisAgent '{self.agent_id}' stopped.")

    async def _handle_raw_news_message(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming raw news messages.
        Performs a conceptual news analysis and publishes an insight.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            raw_news_item = agent_message.payload # Assuming payload is the raw news dict

            logger.info(f"NewsAnalysisAgent '{self.agent_id}' received raw news: {raw_news_item.get('headline', 'N/A')}")

            # --- Conceptual News Analysis ---
            # In a real system, this would involve:
            # 1. Calling an NLP model (e.g., from Vertex AI) for sentiment analysis, entity extraction.
            # 2. Cross-referencing with financial data.
            # 3. Determining market impact.

            # For now, let's simulate a simple analysis based on category/keywords
            sentiment = raw_news_item.get('sentiment', 'neutral')
            category = raw_news_item.get('category', 'general')
            headline = raw_news_item.get('headline', 'No headline')

            market_impact = "unknown"
            if "interest rate" in headline.lower() or "central bank" in headline.lower():
                market_impact = "high_volatility_forex"
            elif "earnings" in headline.lower() or "tech giant" in headline.lower():
                market_impact = "stock_specific_positive"
            elif "pandemic" in headline.lower() or "markets react" in headline.lower():
                market_impact = "broad_market_negative"
            elif "geopolitical" in headline.lower() or "gold prices" in headline.lower():
                market_impact = "commodity_impact"

            news_insight = {
                "original_news_id": raw_news_item.get("id"), # Assuming a unique ID in raw news
                "source": raw_news_item.get("source"),
                "headline": headline,
                "category": category,
                "sentiment": sentiment,
                "timestamp_processed": datetime.now().isoformat(),
                "market_impact_assessment": market_impact,
                "confidence_score": 0.8 # Conceptual confidence
            }

            # Publish the structured news insight to a new topic
            insight_message = AgentMessage(
                sender_id=self.agent_id,
                message_type=MessageType.STATUS_UPDATE, # Or define a new MessageType.NEWS_INSIGHT
                payload=news_insight
            )
            await self.broker.publish_message("news_insights", insight_message.model_dump())
            logger.info(f"NewsAnalysisAgent '{self.agent_id}' published insight for '{headline}'.")

        except Exception as e:
            logger.error(f"NewsAnalysisAgent '{self.agent_id}': Error processing raw news message: {e}", exc_info=True)

# Example Usage (for testing NewsAnalysisAgent in isolation)
async def main_news_analysis_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker # Use real broker for test
    from backend.config import settings # Needed for project_id

    # IMPORTANT: Ensure GCP_PROJECT_ID is set in your .env
    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    news_agent = NewsAnalysisAgent(
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await news_agent.start()

    # Simulate raw news being published (similar to how orchestrator does it)
    news_items_to_publish = [
        {"source": "Test News", "headline": "Simulated: Global economy shows signs of recovery.", "category": "economic", "sentiment": "positive", "timestamp": datetime.now().isoformat()},
        {"source": "Test News", "headline": "Simulated: Major tech company faces antitrust lawsuit.", "category": "business", "sentiment": "negative", "timestamp": datetime.now().isoformat()},
    ]
    
    logger.info("\n--- Simulating external source publishing raw news for NewsAnalysisAgent to consume ---")
    for item in news_items_to_publish:
        raw_news_message = AgentMessage(
            sender_id="ExternalNewsSource",
            message_type=MessageType.STATUS_UPDATE,
            payload=item
        )
        await broker.publish_message("raw_news_events", raw_news_message.model_dump())
        await asyncio.sleep(1) # Simulate some delay

    await asyncio.sleep(10) # Give time for the news agent to process messages

    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nNewsAnalysisAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_news_analysis_agent_test())
