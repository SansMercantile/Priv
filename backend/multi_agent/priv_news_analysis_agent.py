# backend/multi_agent/priv_news_analysis_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, AgentType
from pydantic import ValidationError
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual news sourcing and sentiment analysis clients
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor # For RSS and GDELT

# Import settings for API keys
from backend.config import settings

logger = logging.getLogger(__name__)

class PrivNewsAnalysisAgent(PrivAgent): 
    """
    A specialized agent responsible for consuming raw news data,
    performing analysis using real news APIs and LLM-based sentiment analysis,
    and publishing structured news insights.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.NEWS_ANALYSIS, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False

        # Initialize real news clients and sentiment analyzer
        # Use mock news client when running in DEMO_MODE or when API keys are not configured
        use_mock = bool(getattr(settings, 'DEMO_MODE', False)) or not (settings.NEWS_API_KEY_AI or settings.NEWS_API_KEY_ORG)
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI, # Assuming NEWS_API_KEY_AI is defined in settings
            api_key_org=settings.NEWS_API_KEY_ORG, # Assuming NEWS_API_KEY_ORG is defined in settings
            use_mock=use_mock
        )
        self.news_sentiment_analyzer = NewsSentimentAnalyzer(
            openai_api_key=settings.OPENAI_API_KEY, # Assuming OPENAI_API_KEY is defined in settings
            model="gpt-3.5-turbo" # Or your preferred OpenAI model
        )
        self.global_news_ingestor = GlobalNewsIngestor() # For RSS and GDELT feeds

        # Internal cache for news items to avoid re-processing
        self._processed_news_ids = set() 
        logger.info(f"Priv NewsAnalysisAgent '{self.agent_id}' initialized with real news clients.")

    async def start(self):
        """Starts the news analysis agent, subscribing to raw news events and initiating periodic fetches."""
        if self.is_running:
            logger.warning(f"NewsAnalysisAgent '{self.agent_id}' is already running.")
            return

        # Subscribe to the raw_news_events topic (e.g., from external ingestors)
        await self.broker.subscribe_to_topic(
            "raw_news_events", self._handle_raw_news_message, f"{self.agent_id}-raw-news-sub"
        )
        
        self.is_running = True
        logger.info(f"NewsAnalysisAgent '{self.agent_id}' started and subscribed to 'raw_news_events'.")

        # Start a periodic task to fetch news directly (if this agent is also a primary news source)
        # This will fetch news and then process it, mimicking the raw_news_events flow.
        self._periodic_news_fetch_task = asyncio.create_task(self._periodic_news_fetch())
        logger.info(f"NewsAnalysisAgent '{self.agent_id}' started periodic news fetching.")


    async def stop(self):
        """Stops the news analysis agent."""
        if not self.is_running:
            logger.warning(f"NewsAnalysisAgent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        if self._periodic_news_fetch_task:
            self._periodic_news_fetch_task.cancel()
            try:
                await self._periodic_news_fetch_task # Await cancellation
            except asyncio.CancelledError:
                logger.info(f"NewsAnalysisAgent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"NewsAnalysisAgent '{self.agent_id}' stopped.")

    async def _periodic_news_fetch(self):
        """
        Periodically fetches news from configured APIs and RSS feeds, then
        publishes them as raw news events for internal processing.
        """
        while self.is_running:
            try:
                logger.info(f"NewsAnalysisAgent '{self.agent_id}': Initiating periodic news fetch.")
                
                # Fetch from NewsAPI.ai/org
                # Fetch news for the last hour, general query
                news_from_api = self.news_api_client.fetch_news(
                    query="finance OR market OR economy",
                    from_date=datetime.now() - timedelta(hours=1),
                    limit=20
                )

                # Fetch from RSS feeds
                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=10)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"NewsAnalysisAgent '{self.agent_id}': Fetched {len(all_fetched_news)} new articles from external sources.")

                for news_item in all_fetched_news:
                    # Create a unique ID for the news item to prevent reprocessing
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"NewsAnalysisAgent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    # Publish as a raw news event for _handle_raw_news_message to process
                    raw_news_message = AgentMessage(
                        sender_id=self.agent_id, # This agent is now the source of raw news
                        sender_type=AgentType.NEWS_ANALYSIS.value,
                        recipient_id="news-insights-topic",
                        message_type=MessageType.STATUS_UPDATE, # Or define a new MessageType.RAW_NEWS
                        payload=news_item
                    )
                    await self.broker.publish_message("raw_news_events", raw_news_message.model_dump())
                    self._processed_news_ids.add(news_id) # Mark as processed
                    await asyncio.sleep(0.1) # Small delay to not flood broker

            except Exception as e:
                logger.error(f"NewsAnalysisAgent '{self.agent_id}': Error during periodic news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _handle_raw_news_message(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming raw news messages.
        Performs real news analysis using LLM-based sentiment analysis and publishes an insight.
        """
        try:
            try:
                agent_message = AgentMessage.model_validate(message_payload)
            except ValidationError:
                # Incoming message payload may be a raw dict without the full AgentMessage wrapper.
                # Normalize and fill missing required fields so downstream processing succeeds.
                sender_id = message_payload.get('sender_id', self.agent_id) if isinstance(message_payload, dict) else self.agent_id
                sender_type = message_payload.get('sender_type', AgentType.NEWS_ANALYSIS.value) if isinstance(message_payload, dict) else AgentType.NEWS_ANALYSIS.value
                recipient_id = message_payload.get('recipient_id', self.agent_id) if isinstance(message_payload, dict) else self.agent_id
                message_type = message_payload.get('message_type', MessageType.STATUS_UPDATE) if isinstance(message_payload, dict) else MessageType.STATUS_UPDATE
                payload = message_payload.get('payload', message_payload) if isinstance(message_payload, dict) else message_payload

                agent_message = AgentMessage(
                    sender_id=sender_id,
                    sender_type=sender_type,
                    recipient_id=recipient_id,
                    message_type=message_type,
                    payload=payload
                )

            raw_news_item = agent_message.payload # Assuming payload is the raw news dict

            headline = raw_news_item.get('headline', 'N/A')
            content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')

            if not headline and not content:
                logger.warning(f"NewsAnalysisAgent '{self.agent_id}': Received empty news item. Skipping analysis.")
                return

            logger.info(f"NewsAnalysisAgent '{self.agent_id}' received raw news for analysis: {headline}")

            # --- Real News Analysis using NewsSentimentAnalyzer (LLM-based) ---
            analysis_results = self.news_sentiment_analyzer.analyze_article({
                "title": headline,
                "content": content
            })

            # Extract structured insights from LLM analysis
            sentiment = analysis_results.get("sentiment", "neutral")
            market_impact = analysis_results.get("market_impact", "none")
            symbols_mentioned = analysis_results.get("symbols", [])
            reasoning = analysis_results.get("reasoning", "LLM analysis.")

            news_insight = {
                "original_news_id": raw_news_item.get("url") or raw_news_item.get("headline"), # Use URL or headline as ID
                "source": raw_news_item.get("source"),
                "headline": headline,
                "content_snippet": content[:200] + "..." if len(content) > 200 else content,
                "category": raw_news_item.get('category', 'general'), # Preserve original category if available
                "sentiment": sentiment,
                "timestamp_processed": datetime.now().isoformat(),
                "market_impact_assessment": market_impact,
                "symbols_mentioned": symbols_mentioned,
                "llm_reasoning": reasoning,
                "confidence_score": 0.9 # LLM confidence, or a derived confidence
            }

            # Publish the structured news insight to a new topic
            insight_message = AgentMessage(
                sender_id=self.agent_id,
                sender_type=AgentType.NEWS_ANALYSIS.value,
                recipient_id="news-insights-consumers",
                message_type=MessageType.STATUS_UPDATE, # Or define a new MessageType.NEWS_INSIGHT
                payload=news_insight
            )
            await self.broker.publish_message("news_insights", insight_message.model_dump())
            logger.info(f"NewsAnalysisAgent '{self.agent_id}' published insight for '{headline}'. Sentiment: {sentiment}, Impact: {market_impact}.")

        except Exception as e:
            logger.error(f"NewsAnalysisAgent '{self.agent_id}': Error processing raw news message: {e}", exc_info=True)

# Example Usage (for testing NewsAnalysisAgent in isolation)
async def main_news_analysis_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

    # Ensure GCP_PROJECT_ID, OPENAI_API_KEY, NEWS_API_KEY_AI/ORG are set in your .env
    project_id = settings.GCP_PROJECT_ID
    openai_key = settings.OPENAI_API_KEY
    news_api_ai_key = settings.NEWS_API_KEY_AI
    news_api_org_key = settings.NEWS_API_KEY_ORG

    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return
    if not openai_key or "YOUR_OPENAI_API_KEY" in openai_key:
        logger.error("OPENAI_API_KEY not set or is default. LLM analysis will fail.")
        return
    if not news_api_ai_key and not news_api_org_key:
        logger.warning("Neither NEWS_API_KEY_AI nor NEWS_API_KEY_ORG are set. External news fetching will be limited.")

    # Temporarily set a mock interval for testing
    settings.NEWS_FETCH_INTERVAL_SECONDS = 5 # Fetch every 5 seconds for test

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    news_agent = PrivNewsAnalysisAgent( # Changed to PrivNewsAnalysisAgent
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await news_agent.start()

    logger.info("\n--- NewsAnalysisAgent running. It will periodically fetch news and analyze it. ---")
    logger.info("--- Check logs for 'Published insight' messages. ---")

    await asyncio.sleep(20) # Let it run for a while to fetch and process news

    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nNewsAnalysisAgent test finished.")

if __name__ == '__main__':
    # Add a dummy setting for testing if not already present
    if not hasattr(settings, 'NEWS_FETCH_INTERVAL_SECONDS'):
        settings.NEWS_FETCH_INTERVAL_SECONDS = 300 # Default to 5 minutes for non-test runs

    asyncio.run(main_news_analysis_agent_test())
