# backend/multi_agent/priv_futures_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeProposal, TradeAction, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual data sourcing clients
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor # For general market data
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor

# Import settings for API keys and configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivFuturesAgent(PrivAgent):
    """
    A specialized Priv Agent focused on trading futures contracts across various asset classes
    (commodities, indices, currencies). It analyzes market trends, volatility, and
    carry costs to identify opportunities and manage futures positions.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.FUTURES, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.futures_market_data: Dict[str, Dict[str, Any]] = {} # Stores latest futures data by symbol
        self.open_futures_positions: Dict[str, Dict[str, Any]] = {} # Tracks conceptual open positions

        # Initialize real data sourcing and analysis clients
        self.market_data_ingestor = MarketDataIngestor(self.broker)
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.news_sentiment_analyzer = NewsSentimentAnalyzer(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-3.5-turbo" # Or a more capable model for financial analysis
        )
        self.global_news_ingestor = GlobalNewsIngestor()
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv Futures Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the futures agent, subscribing to futures market data."""
        if self.is_running:
            logger.warning(f"Futures Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to futures market data (e.g., price, expiry, open interest)
        await self.broker.subscribe_to_topic(
            "futures_market_data", self._handle_futures_market_data, f"{self.agent_id}-futures-sub"
        )
        # Also subscribe to news insights for macro trends affecting futures
        await self.broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )

        self.is_running = True
        # Start a periodic task to fetch news directly relevant to futures markets
        self._periodic_futures_news_fetch_task = asyncio.create_task(self._periodic_futures_news_fetch())
        logger.info(f"Priv Futures Agent '{self.agent_id}' started and subscribed to futures topics.")

    async def stop(self):
        """Stops the futures agent."""
        if not self.is_running:
            logger.warning(f"Futures Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_futures_news_fetch_task:
            self._periodic_futures_news_fetch_task.cancel()
            try:
                await self._periodic_futures_news_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv Futures Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv Futures Agent '{self.agent_id}' stopped.")

    async def _periodic_futures_news_fetch(self):
        """
        Periodically fetches news specifically relevant to futures markets,
        then processes them internally.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Futures Agent '{self.agent_id}': Initiating periodic futures news fetch.")
                
                # Fetch news from NewsAPI.ai/org focusing on futures-relevant keywords
                futures_keywords = "futures OR commodity OR index OR oil OR gold OR agriculture OR interest rate futures OR bond futures OR currency futures"
                news_from_api = self.news_api_client.fetch_news(
                    query=futures_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=settings.FUTURES_NEWS_FETCH_LIMIT
                )

                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=settings.FUTURES_NEWS_RSS_LIMIT)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv Futures Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially futures-relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"Futures Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    await self._process_and_publish_futures_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv Futures Agent '{self.agent_id}': Error during periodic futures news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.FUTURES_NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _process_and_publish_futures_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for futures relevance and publishes the insight.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"Futures Agent: Skipping empty news item during direct fetch.")
            return

        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        # Assess futures market impact based on LLM analysis
        futures_impact_assessment = self._assess_futures_impact(news_item, analysis_results)
        
        if futures_impact_assessment.get("impact_level") != "NONE":
            logger.info(f"Futures Agent: News impacts futures market. Headline: {headline}. Impact: {futures_impact_assessment.get('impact_level')}")
            await self._publish_futures_alert("futures_market_news_impact", futures_impact_assessment)
            # Potentially trigger re-evaluation of specific futures contracts
            for symbol in futures_impact_assessment.get("symbols_impacted", []):
                await self._analyze_futures_opportunity(symbol)


    async def _handle_futures_market_data(self, message_payload: Dict[str, Any]):
        """
        Processes incoming futures market data.
        This data would typically come from the MarketDataIngestor or a specialized futures data ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            futures_data = agent_message.payload

            symbol = futures_data.get("symbol") # e.g., "ES=F" for S&P 500 E-mini futures
            last_price = futures_data.get("last_trade_price")
            expiry_date = futures_data.get("expiry_date") # YYYY-MM-DD
            open_interest = futures_data.get("open_interest")
            bid_price = futures_data.get("bid_price")
            ask_price = futures_data.get("ask_price")


            if all([symbol, last_price is not None, expiry_date, bid_price is not None, ask_price is not None]):
                self.futures_market_data[symbol] = {
                    "last_price": last_price,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "expiry_date": expiry_date,
                    "open_interest": open_interest,
                    "timestamp": datetime.now().isoformat()
                }
                logger.debug(f"Futures Agent: Updated data for {symbol}: Last={last_price}, Bid={bid_price}, Ask={ask_price}, Expiry={expiry_date}.")

                # Trigger analysis for potential trade opportunities
                await self._analyze_futures_opportunity(symbol)

        except Exception as e:
            logger.error(f"Futures Agent '{self.agent_id}': Error handling futures market data: {e}", exc_info=True)

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes news insights (from NewsAnalysisAgent) for macro trends relevant to futures markets.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            category = news_insight.get('category', 'general')
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact_assessment = news_insight.get('market_impact_assessment', 'unknown')


            logger.info(f"Futures Agent: Received news insight from {agent_message.sender_id}: '{headline}' (Category: {category}, Sentiment: {sentiment}, Impact: {market_impact_assessment})")

            # Assess futures market impact based on the already processed news insight
            futures_impact_assessment = self._assess_futures_impact(news_insight, news_insight) # Pass news_insight as both raw and analyzed
            
            if futures_impact_assessment.get("impact_level") != "NONE":
                logger.info(f"Futures Agent: News insight suggests potential impact on futures markets. Impact: {futures_impact_assessment.get('impact_level')}.")
                await self._publish_futures_alert("futures_market_news_impact", futures_impact_assessment)
                # Potentially trigger re-evaluation of specific futures contracts
                for symbol in futures_impact_assessment.get("symbols_impacted", []):
                    await self._analyze_futures_opportunity(symbol)

        except Exception as e:
            logger.error(f"Futures Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    def _assess_futures_impact(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses the potential impact of a news item on futures markets.
        This function should be refined with more sophisticated NLP and market knowledge.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        symbols_mentioned = llm_analysis_results.get("symbols", [])
        
        impact_level = "NONE"
        symbols_impacted = []
        reasoning = "No direct futures market impact detected."

        text_to_analyze = (headline + " " + content).lower()

        # Keywords for high impact on futures
        high_impact_keywords = ["opec", "fed rate", "inflation", "gdp", "supply disruption", "demand surge", "geopolitical crisis", "crop failure", "inventory report", "interest rate hike"]
        # Keywords for medium impact
        medium_impact_keywords = ["trade deal", "manufacturing pmi", "unemployment", "consumer spending"]

        if any(keyword in text_to_analyze for keyword in high_impact_keywords):
            impact_level = "HIGH"
            reasoning = "News contains high-impact keywords for futures markets."
        elif any(keyword in text_to_analyze for keyword in medium_impact_keywords):
            impact_level = "MEDIUM"
            reasoning = "News contains medium-impact keywords for futures markets."
        
        # Identify specific symbols/commodities impacted
        if "oil" in text_to_analyze or "crude" in text_to_analyze or "brent" in text_to_analyze:
            symbols_impacted.append("CL=F") # Crude Oil futures
            symbols_impacted.append("BRENT")
        if "gold" in text_to_analyze or "precious metals" in text_to_analyze:
            symbols_impacted.append("GC=F") # Gold futures
        if "s&p" in text_to_analyze or "spx" in text_to_analyze or "dow" in text_to_analyze or "nasdaq" in text_to_analyze:
            symbols_impacted.append("ES=F") # S&P 500 E-mini futures
            symbols_impacted.append("NQ=F") # Nasdaq 100 E-mini futures
        if "treasury" in text_to_analyze or "bond" in text_to_analyze or "interest rate" in text_to_analyze:
            symbols_impacted.append("ZB=F") # US Treasury Bond futures

        # If LLM mentioned symbols, add them
        symbols_impacted.extend(symbols_mentioned)
        symbols_impacted = list(set(symbols_impacted)) # Deduplicate

        # Adjust impact based on sentiment
        if sentiment == "positive" and impact_level != "NONE":
            reasoning += " (Positive sentiment implies bullish impact)."
        elif sentiment == "negative" and impact_level != "NONE":
            reasoning += " (Negative sentiment implies bearish impact)."

        return {
            "headline": headline,
            "sentiment": sentiment,
            "impact_level": impact_level,
            "symbols_impacted": symbols_impacted,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }


    async def _analyze_futures_opportunity(self, symbol: str):
        """
        Analyzes a futures contract for trade opportunities.
        Considers current price, time to expiry, open interest, and conceptual volatility/trend.
        """
        data = self.futures_market_data.get(symbol)
        if not data or data.get("last_price") is None or data.get("expiry_date") is None:
            logger.warning(f"Futures Agent: Insufficient data for futures {symbol} analysis.")
            return

        current_price = data["last_price"]
        bid_price = data["bid_price"]
        ask_price = data["ask_price"]
        expiry_date_str = data["expiry_date"]
        open_interest = data.get("open_interest")

        try:
            expiry_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d")
            days_to_expiry = (expiry_dt - datetime.now()).days
        except ValueError:
            logger.warning(f"Futures Agent: Invalid expiry date format for {symbol}: {expiry_date_str}. Skipping analysis.")
            return

        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = f"Monitoring {symbol}. Price: {current_price}, Days to Expiry: {days_to_expiry}."

        # Conceptual trend and volatility signals (in a real system, these would come from AnalyticsEngine)
        conceptual_trend = "neutral"
        if current_price > (self.futures_market_data.get(symbol, {}).get("last_price", current_price) * 1.005):
            conceptual_trend = "up"
        elif current_price < (self.futures_market_data.get(symbol, {}).get("last_price", current_price) * 0.995):
            conceptual_trend = "down"

        # Logic for futures trading
        MIN_DAYS_TO_EXPIRY_FOR_NEW_TRADE = getattr(settings, 'FUTURES_MIN_DAYS_TO_EXPIRY_FOR_NEW_TRADE', 30)
        FUTURES_TREND_CONFIDENCE_THRESHOLD = getattr(settings, 'FUTURES_TREND_CONFIDENCE_THRESHOLD', 0.75)
        FUTURES_NEAR_EXPIRY_DAYS = getattr(settings, 'FUTURES_NEAR_EXPIRY_DAYS', 7)

        if days_to_expiry > MIN_DAYS_TO_EXPIRY_FOR_NEW_TRADE:
            if conceptual_trend == "up" and current_price > settings.FUTURES_BULLISH_PRICE_THRESHOLD: # Example threshold
                action = TradeAction.BUY
                confidence = FUTURES_TREND_CONFIDENCE_THRESHOLD
                reasoning = f"Bullish trend detected for {symbol}. Sufficient time to expiry ({days_to_expiry} days). Price: {current_price}."
            elif conceptual_trend == "down" and current_price < settings.FUTURES_BEARISH_PRICE_THRESHOLD: # Example threshold
                action = TradeAction.SELL
                confidence = FUTURES_TREND_CONFIDENCE_THRESHOLD
                reasoning = f"Bearish trend detected for {symbol}. Sufficient time to expiry ({days_to_expiry} days). Price: {current_price}."
        elif days_to_expiry <= FUTURES_NEAR_EXPIRY_DAYS: # Near expiry, consider closing or rolling
            if symbol in self.open_futures_positions:
                action = TradeAction.CLOSE # Or roll over to next contract
                confidence = 0.8
                reasoning = f"{symbol} futures nearing expiry. Closing existing position."
            else:
                action = TradeAction.HOLD # Avoid opening new positions near expiry
                confidence = 0.3
                reasoning = f"{symbol} futures nearing expiry. Not initiating new trades."

        if action != TradeAction.HOLD:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=action,
                volume=settings.FUTURES_TRADE_PROPOSAL_VOLUME, # Configurable contract volume
                entry_price=current_price, # Use last traded price as entry
                reasoning=reasoning,
                confidence=confidence,
                risk_assessment={"futures_leverage": "high", "expiry_risk_days": days_to_expiry, "open_interest": open_interest}
            )
            await self._publish_futures_proposal(proposal)

            if action in [TradeAction.BUY, TradeAction.SELL]:
                self.open_futures_positions[symbol] = {
                    "action": action.value,
                    "entry_price": current_price,
                    "volume": settings.FUTURES_TRADE_PROPOSAL_VOLUME,
                    "timestamp": datetime.now().isoformat()
                }
            elif action == TradeAction.CLOSE and symbol in self.open_futures_positions:
                del self.open_futures_positions[symbol]

    async def _publish_futures_alert(self, alert_type: str, details: Dict[str, Any]):
        """Helper to publish futures-related alerts."""
        alert_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ERROR_NOTIFICATION, # Reusing ERROR_NOTIFICATION for alerts
            payload={
                "source_agent_id": self.agent_id,
                "message": f"Futures Alert: {alert_type}",
                "severity": details.get("impact_level", "MEDIUM"), # Use impact level as severity
                "alert_type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("futures_alerts", alert_message.model_dump())
        logger.log(logging.getLevelName(details.get("impact_level", "MEDIUM")), f"Futures Agent: Published futures alert: {alert_type}.")

        # Send WhatsApp alert for critical futures market news
        if details.get("impact_level") == "HIGH":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            whatsapp_message = (
                f"🚨 FUTURES MARKET ALERT! 🚨\n"
                f"Headline: {details.get('headline')}\n"
                f"Impact: {details.get('impact_level')}\n"
                f"Symbols: {', '.join(details.get('symbols_impacted', []))}\n"
                f"Reason: {details.get('reasoning')}"
            )
            try:
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"Futures Agent: Conceptually sent critical WhatsApp alert for futures market to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"Futures Agent: Failed to send WhatsApp alert for futures: {e}", exc_info=True)


    async def _publish_futures_proposal(self, proposal: TradeProposal):
        """Helper to publish a trade proposal generated by the futures agent."""
        proposal_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.TRADE_PROPOSAL,
            payload=proposal.model_dump()
        )
        await self.broker.publish_message("trade_proposals", proposal_message.model_dump())
        logger.info(f"Futures Agent: Published trade proposal: {proposal.action} {proposal.symbol} (Confidence: {proposal.confidence:.2f}).")


# Example Usage (for testing PrivFuturesAgent in isolation)
async def main_futures_agent_test():
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
    if not hasattr(settings, 'FUTURES_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.FUTURES_NEWS_FETCH_INTERVAL_SECONDS = 10
    if not hasattr(settings, 'FUTURES_NEWS_FETCH_LIMIT'):
        settings.FUTURES_NEWS_FETCH_LIMIT = 5
    if not hasattr(settings, 'FUTURES_NEWS_RSS_LIMIT'):
        settings.FUTURES_NEWS_RSS_LIMIT = 3
    if not hasattr(settings, 'FUTURES_MIN_DAYS_TO_EXPIRY_FOR_NEW_TRADE'):
        settings.FUTURES_MIN_DAYS_TO_EXPIRY_FOR_NEW_TRADE = 30
    if not hasattr(settings, 'FUTURES_TREND_CONFIDENCE_THRESHOLD'):
        settings.FUTURES_TREND_CONFIDENCE_THRESHOLD = 0.75
    if not hasattr(settings, 'FUTURES_NEAR_EXPIRY_DAYS'):
        settings.FUTURES_NEAR_EXPIRY_DAYS = 7
    if not hasattr(settings, 'FUTURES_TRADE_PROPOSAL_VOLUME'):
        settings.FUTURES_TRADE_PROPOSAL_VOLUME = 1 # Conceptual volume
    if not hasattr(settings, 'FUTURES_BULLISH_PRICE_THRESHOLD'):
        settings.FUTURES_BULLISH_PRICE_THRESHOLD = 4000 # Example for ES=F
    if not hasattr(settings, 'FUTURES_BEARISH_PRICE_THRESHOLD'):
        settings.FUTURES_BEARISH_PRICE_THRESHOLD = 3000 # Example for ES=F
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    futures_agent = PrivFuturesAgent(
        agent_id="Priv-FuturesTrader",
        broker=broker,
        persona={"name": "Futures Trader", "focus": "Derivatives & Hedging"}
    )
    news_agent = PrivNewsAnalysisAgent( # For simulating news insights
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await futures_agent.start()
    await news_agent.start()

    logger.info("\n--- Simulating messages for Futures Agent to consume ---")

    # Simulate futures market data for S&P 500 E-mini (ES=F)
    mock_es_futures_data_1 = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "ES=F",
            "last_trade_price": 4500.25,
            "bid_price": 4500.00,
            "ask_price": 4500.50,
            "expiry_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "open_interest": 150000,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("futures_market_data", mock_es_futures_data_1.model_dump())
    await asyncio.sleep(1)

    # Simulate futures market data for Crude Oil (CL=F)
    mock_cl_futures_data_1 = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "CL=F",
            "last_trade_price": 78.50,
            "bid_price": 78.45,
            "ask_price": 78.55,
            "expiry_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "open_interest": 800000,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("futures_market_data", mock_cl_futures_data_1.model_dump())
    await asyncio.sleep(1)

    # Simulate news affecting commodity futures (from NewsAnalysisAgent)
    mock_commodity_news_insight = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "original_news_id": "news_futures_1",
            "source": "Bloomberg",
            "headline": "OPEC+ signals deeper production cuts, boosting oil prices.",
            "content": "OPEC and its allies have indicated further production cuts are likely, leading to a significant rally in crude oil futures.",
            "category": "commodity",
            "sentiment": "positive",
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "crude_oil_price_hike",
            "confidence_score": 0.85,
            "symbols_mentioned": ["CL=F", "BRENT"]
        }
    )
    await broker.publish_message("news_insights", mock_commodity_news_insight.model_dump())
    await asyncio.sleep(1)

    # Simulate a futures contract nearing expiry (to trigger a CLOSE or HOLD)
    mock_es_futures_data_near_expiry = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "ES=F",
            "last_trade_price": 4510.00,
            "bid_price": 4509.75,
            "ask_price": 4510.25,
            "expiry_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), # Near expiry
            "open_interest": 140000,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("futures_market_data", mock_es_futures_data_near_expiry.model_dump())
    await asyncio.sleep(1)


    await asyncio.sleep(15) # Give time for agents to process messages and for periodic fetches

    await futures_agent.stop()
    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivFuturesAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_futures_agent_test())
