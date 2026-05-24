# backend/multi_agent/priv_pr_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface

# Import actual news sourcing and sentiment analysis clients
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor

# Import settings for API keys and configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivPRAgent(PrivAgent):
    """
    A specialized Priv Agent focused on public relations and external communications.
    It monitors public sentiment, drafts responses to events (positive or negative),
    and manages the public image of the Priv system.
    """
    def __init__(self, agent_id: str, broker: MessageBrokerInterface, persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, persona=persona)
        self.broker = broker
        self.is_running = False
        self.public_sentiment: Dict[str, Any] = {"overall": "neutral", "trends": []}

        # Initialize real news clients and sentiment analyzer for internal use
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.news_sentiment_analyzer = NewsSentimentAnalyzer(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-3.5-turbo"
        )
        self.global_news_ingestor = GlobalNewsIngestor()
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv PR Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the PR agent, subscribing to relevant internal and external feeds."""
        if self.is_running:
            logger.warning(f"PR Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to news insights, social media sentiment, and critical error/violation notifications
        await self.message_broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "social_media_sentiment", self._handle_social_media_sentiment, f"{self.agent_id}-social-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "error_notifications", self._handle_internal_alert, f"{self.agent_id}-errors-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "compliance_violations", self._handle_internal_alert, f"{self.agent_id}-compliance-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "audit_alerts", self._handle_internal_alert, f"{self.agent_id}-audit-sub"
        )

        self.is_running = True
        # Start a periodic task to fetch news directly relevant to public perception
        self._periodic_pr_news_fetch_task = asyncio.create_task(self._periodic_pr_news_fetch())
        logger.info(f"Priv PR Agent '{self.agent_id}' started and subscribed to PR topics.")

    async def stop(self):
        """Stops the PR agent."""
        if not self.is_running:
            logger.warning(f"PR Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_pr_news_fetch_task:
            self._periodic_pr_news_fetch_task.cancel()
            try:
                await self._periodic_pr_news_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv PR Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv PR Agent '{self.agent_id}' stopped.")

    async def _periodic_pr_news_fetch(self):
        """
        Periodically fetches news specifically relevant to public perception,
        then processes them internally.
        """
        while self.is_running:
            try:
                logger.info(f"Priv PR Agent '{self.agent_id}': Initiating periodic PR-relevant news fetch.")
                
                # Fetch news from NewsAPI.ai/org focusing on keywords relevant to brand image
                pr_keywords = "Priv OR Sans Mercantile OR AI trading OR financial innovation OR ethical AI OR data breach OR market manipulation"
                news_from_api = self.news_api_client.fetch_news(
                    query=pr_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=10
                )

                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=5)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv PR Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially PR-relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"PR Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    await self._process_and_publish_pr_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv PR Agent '{self.agent_id}': Error during periodic PR news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.PR_NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _process_and_publish_pr_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for PR relevance and publishes the insight.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"PR Agent: Skipping empty news item during direct fetch.")
            return

        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        pr_impact_assessment = self._assess_pr_impact_from_news(news_item, analysis_results)
        
        if pr_impact_assessment.get("action_required"):
            logger.warning(f"PR Agent: News requires PR action: {headline}. Recommended: {pr_impact_assessment.get('recommendation')}")
            await self._draft_and_publish_statement(pr_impact_assessment)

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes incoming news insights (from NewsAnalysisAgent) for PR implications.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact = news_insight.get('market_impact_assessment', 'unknown')

            logger.info(f"PR Agent: Received news insight from {agent_message.sender_id}: '{headline}' (Sentiment: {sentiment}, Impact: {market_impact})")

            pr_impact = self._assess_pr_impact_from_news(news_insight, news_insight) # Pass news_insight as both raw and analyzed
            if pr_impact.get("action_required"):
                logger.warning(f"PR Agent: News insight requires PR action: {headline}. Recommended: {pr_impact.get('recommendation')}")
                await self._draft_and_publish_statement(pr_impact)

        except Exception as e:
            logger.error(f"PR Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    async def _handle_social_media_sentiment(self, message_payload: Dict[str, Any]):
        """
        Processes incoming social media sentiment data to understand public mood.
        This relies on a separate agent (e.g., PrivSocialMediaAgent) publishing this data.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            sentiment_data = agent_message.payload

            platform = sentiment_data.get('platform', 'N/A')
            overall_sentiment = sentiment_data.get('overall_sentiment', 'neutral')
            keywords = sentiment_data.get('keywords', [])

            logger.info(f"PR Agent: Received social media sentiment from {platform}: Overall '{overall_sentiment}' for keywords {keywords}.")

            # Update internal sentiment tracking
            self.public_sentiment["overall"] = overall_sentiment
            self.public_sentiment["trends"].append({
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "sentiment": overall_sentiment,
                "keywords": keywords
            })
            # Keep trend list short for demo
            if len(self.public_sentiment["trends"]) > settings.PR_SENTIMENT_TREND_HISTORY_LIMIT:
                self.public_sentiment["trends"].pop(0)

            # Conceptual PR action based on sentiment
            # Thresholds should be configurable in settings
            if overall_sentiment == "negative" and any(k.lower() in ["priv", "sans mercantile"] for k in keywords):
                logger.warning("PR Agent: Negative social media sentiment detected for 'Priv'. Considering proactive communication.")
                await self._draft_and_publish_statement({
                    "type": "proactive_engagement",
                    "reason": "Negative social media trend",
                    "recommendation": "Address concerns, highlight positive aspects.",
                    "details": sentiment_data,
                    "severity": "MEDIUM"
                })
            elif overall_sentiment == "positive" and any(k.lower() in ["priv", "sans mercantile"] for k in keywords) and \
                 overall_sentiment == "positive" and sentiment_data.get('trend_score', 0) > settings.PR_POSITIVE_TREND_THRESHOLD:
                logger.info("PR Agent: Strong positive social media sentiment detected. Amplifying positive news.")
                await self._draft_and_publish_statement({
                    "type": "amplification",
                    "reason": "Strong positive social media trend",
                    "recommendation": "Amplify positive news through official channels.",
                    "details": sentiment_data,
                    "severity": "LOW"
                })


        except Exception as e:
            logger.error(f"PR Agent '{self.agent_id}': Error handling social media sentiment: {e}", exc_info=True)

    async def _handle_internal_alert(self, message_payload: Dict[str, Any]):
        """
        Processes internal alerts (errors, violations, audit findings) that might
        have public relations implications.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            alert_details = agent_message.payload
            alert_type = alert_details.get("alert_type", "unknown_alert")
            severity = alert_details.get("severity", "LOW")

            logger.warning(f"PR Agent: Received internal alert of type '{alert_type}' with severity '{severity}'.")

            # Conceptual PR response for high-severity internal issues
            if severity in ["CRITICAL", "HIGH"] and ("violation" in alert_type or "error" in alert_type or "outage" in alert_type):
                logger.critical(f"PR Agent: High-severity internal issue detected: {alert_type}. Preparing public response strategy.")
                await self._draft_and_publish_statement({
                    "type": "crisis_communication",
                    "reason": f"Internal alert: {alert_type}",
                    "recommendation": "Prepare transparent statement, mitigate public damage.",
                    "details": alert_details,
                    "severity": "CRITICAL"
                })

        except Exception as e:
            logger.error(f"PR Agent '{self.agent_id}': Error handling internal alert: {e}", exc_info=True)

    def _assess_pr_impact_from_news(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses PR impact from a news item based on its content and LLM analysis.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        market_impact = llm_analysis_results.get("market_impact", "none")
        symbols_mentioned = llm_analysis_results.get("symbols", [])

        action_required = False
        recommendation = "Monitor"
        pr_severity = "LOW"

        text_to_analyze = (headline + " " + content).lower()

        # Keywords for negative PR impact
        negative_pr_keywords = ["lawsuit", "scandal", "breach", "fine", "investigation", "controversy", "failure", "outage", "manipulation", "fraud"]
        # Keywords for positive PR impact
        positive_pr_keywords = ["award", "innovation", "partnership", "record profits", "expansion", "breakthrough"]

        if any(keyword in text_to_analyze for keyword in negative_pr_keywords):
            action_required = True
            recommendation = "Draft defensive statement and prepare for media inquiries."
            pr_severity = "CRITICAL"
        elif any(keyword in text_to_analyze for keyword in positive_pr_keywords):
            action_required = True
            recommendation = "Amplify positive news through official channels."
            pr_severity = "MEDIUM"
        elif sentiment == "negative" and market_impact == "high":
            action_required = True
            recommendation = "Assess potential reputational damage and prepare a proactive statement."
            pr_severity = "HIGH"
        elif sentiment == "positive" and market_impact == "high":
            action_required = True
            recommendation = "Leverage positive market sentiment for brand building."
            pr_severity = "MEDIUM"

        # Check if "Priv" or "Sans Mercantile" is explicitly mentioned in the headline/content
        if "priv" in text_to_analyze or "sans mercantile" in text_to_analyze:
            if pr_severity == "LOW": # If no other strong signals, but brand mentioned
                pr_severity = "MEDIUM" # Elevate to medium if direct mention
                action_required = True
                recommendation = "Monitor closely and consider a general positive/neutral communication."


        return {
            "source_news": raw_news_item,
            "llm_analysis": llm_analysis_results,
            "action_required": action_required,
            "recommendation": recommendation,
            "pr_severity": pr_severity,
            "timestamp": datetime.now().isoformat()
        }

    async def _draft_and_publish_statement(self, pr_strategy: Dict[str, Any]):
        """
        Conceptual function to draft and publish a public statement.
        This would involve LLM-based drafting and integration with external PR platforms.
        """
        statement_type = pr_strategy.get("type", "general")
        reason = pr_strategy.get("reason", "no specific reason")
        recommendation = pr_strategy.get("recommendation", "no specific recommendation")
        severity = pr_strategy.get("severity", "LOW")

        # In a real system, this would involve:
        # 1. Using an LLM to draft the actual statement based on context.
        # 2. Getting approval from a human or governance agent.
        # 3. Publishing to external platforms (e.g., press release service, social media APIs).

        conceptual_statement_text = (
            f"Official statement regarding {statement_type} due to '{reason}'. "
            f"Our current strategy: '{recommendation}'. "
            "We are committed to transparency and will provide updates as they become available."
        )

        statement_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE, # Or a new type like MessageType.PUBLIC_STATEMENT
            payload={
                "statement_type": statement_type,
                "text": conceptual_statement_text,
                "status": "drafted", # Could be "published" after external integration
                "timestamp": datetime.now().isoformat(),
                "context": pr_strategy
            }
        )
        await self.broker.publish_message("public_statements", statement_message.model_dump())
        logger.info(f"PR Agent: Drafted and conceptually published statement of type '{statement_type}'.")

        # Send WhatsApp alert for critical PR issues
        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            try:
                whatsapp_message = f"🚨 CRITICAL PR ALERT! 🚨\nType: {statement_type}\nReason: {reason}\nRecommendation: {recommendation}\nStatement: {conceptual_statement_text[:150]}..."
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"PR Agent: Conceptually sent critical WhatsApp alert for PR issue to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"PR Agent: Failed to send WhatsApp alert for PR issue: {e}", exc_info=True)


# Example Usage (for testing PrivPRAgent in isolation)
async def main_pr_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_news_analysis_agent import PrivNewsAnalysisAgent # To simulate news insights

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'OPENAI_API_KEY') or "YOUR_OPENAI_API_KEY" in settings.OPENAI_API_KEY:
        settings.OPENAI_API_KEY = "dummy_openai_key" # For local test, won't work with real LLM
    if not hasattr(settings, 'NEWS_API_KEY_AI'):
        settings.NEWS_API_KEY_AI = "dummy_news_ai_key"
    if not hasattr(settings, 'NEWS_API_KEY_ORG'):
        settings.NEWS_API_KEY_ORG = "dummy_news_org_key"
    if not hasattr(settings, 'PR_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.PR_NEWS_FETCH_INTERVAL_SECONDS = 10 # Fetch every 10 seconds for test
    if not hasattr(settings, 'PR_SENTIMENT_TREND_HISTORY_LIMIT'):
        settings.PR_SENTIMENT_TREND_HISTORY_LIMIT = 5
    if not hasattr(settings, 'PR_POSITIVE_TREND_THRESHOLD'):
        settings.PR_POSITIVE_TREND_THRESHOLD = 0.6
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890" # Dummy number


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    pr_agent = PrivPRAgent(
        agent_id="Priv-PRManager",
        broker=broker,
        persona={"name": "Public Relations Manager", "focus": "Brand Image & Communication"}
    )
    news_agent = PrivNewsAnalysisAgent( # For simulating news insights
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )
    # Assuming a hypothetical SocialMediaSentimentAgent exists for simulation
    # from backend.multi_agent.priv_social_media_agent import PrivSocialMediaAgent

    await broker.connect()
    await pr_agent.start()
    await news_agent.start()

    logger.info("\n--- Simulating messages for PR Agent to consume ---")

    # Simulate a negative news insight (from NewsAnalysisAgent)
    mock_negative_news_insight = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "original_news_id": "news_456",
            "source": "FinancialTimes",
            "headline": "PrivCo faces class-action lawsuit over data breach.",
            "content": "A significant data breach has led to a class-action lawsuit against PrivCo, raising concerns about customer data security.",
            "category": "legal",
            "sentiment": "negative",
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "high_reputational_damage",
            "confidence_score": 0.95,
            "symbols_mentioned": ["PRIVCO"] # Example symbol
        }
    )
    await broker.publish_message("news_insights", mock_negative_news_insight.model_dump())
    await asyncio.sleep(1)

    # Simulate positive social media sentiment (from a hypothetical PrivSocialMediaAgent)
    mock_positive_social_sentiment = AgentMessage(
        sender_id="Priv-SocialMediaMonitor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "platform": "Twitter",
            "overall_sentiment": "positive",
            "keywords": ["Priv", "innovation", "AI", "Sans Mercantile"],
            "trend_score": 0.75, # High trend score
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("social_media_sentiment", mock_positive_social_sentiment.model_dump())
    await asyncio.sleep(1)

    # Simulate a critical internal error (from PrivAuditAgent)
    mock_critical_internal_error = AgentMessage(
        sender_id="Priv-Auditor",
        message_type=MessageType.ERROR_NOTIFICATION, # From AuditAgent
        payload={
            "source_agent_id": "Priv-Auditor",
            "message": "Major system outage detected in trading engine.",
            "severity": "CRITICAL",
            "alert_type": "critical_infrastructure_failure",
            "details": {"system": "trading_engine", "duration": "unknown"},
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("error_notifications", mock_critical_internal_error.model_dump())
    await asyncio.sleep(1)


    await asyncio.sleep(15) # Give time for agents to process messages and for periodic fetches

    await pr_agent.stop()
    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivPRAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_pr_agent_test())
