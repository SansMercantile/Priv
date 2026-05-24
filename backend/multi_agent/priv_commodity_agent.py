# backend/multi_agent/priv_commodity_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

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
from backend.fundamental_analysis.economic_calendar.manager import EconomicCalendarManager # For economic reports
from backend.fundamental_analysis.economic_calendar.defines import EconomicEvent, ImpactLevel, EventType # For EconomicEvent types

# Import settings for API keys and configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts - Corrected import path
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivCommodityAgent(PrivAgent):
    """
    A specialized Priv Agent focused on analyzing and trading physical and derivative
    commodities (e.g., oil, gold, agricultural products). It considers supply/demand,
    geopolitical factors, weather, and inventory reports.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.COMMODITY, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.commodity_market_data: Dict[str, Dict[str, Any]] = {} 
        self.supply_demand_factors: Dict[str, Dict[str, Any]] = {} 

        # Initialize real data sourcing and analysis clients
        self.market_data_ingestor = MarketDataIngestor(self.broker)
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.news_sentiment_analyzer = NewsSentimentAnalyzer(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini" # Using a more capable model for financial analysis
        )
        self.global_news_ingestor = GlobalNewsIngestor()
        self.economic_calendar_manager = EconomicCalendarManager(
            calendar_url=settings.ECONOMIC_CALENDAR_URL
        )
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv Commodity Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the commodity agent, subscribing to relevant data feeds."""
        if self.is_running:
            logger.warning(f"Commodity Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to commodity market data, news insights (geopolitical, weather),
        # and economic reports
        await self.broker.subscribe_to_topic(
            "commodity_market_data", self._handle_commodity_market_data, f"{self.agent_id}-commodity-sub"
        )
        await self.broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )
        await self.broker.subscribe_to_topic(
            "economic_reports", self._handle_economic_report, f"{self.agent_id}-economic-sub"
        )

        self.is_running = True
        # Start a periodic task to fetch news directly relevant to commodities
        self._periodic_commodity_news_fetch_task = asyncio.create_task(self._periodic_commodity_news_fetch())
        logger.info(f"Priv Commodity Agent '{self.agent_id}' started and subscribed to commodity topics.")

    async def stop(self):
        """Stops the commodity agent."""
        if not self.is_running:
            logger.warning(f"Commodity Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_commodity_news_fetch_task:
            self._periodic_commodity_news_fetch_task.cancel()
            try:
                await self._periodic_commodity_news_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv Commodity Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv Commodity Agent '{self.agent_id}' stopped.")

    async def _periodic_commodity_news_fetch(self):
        """
        Periodically fetches news specifically relevant to commodities,
        then processes them internally.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Commodity Agent '{self.agent_id}': Initiating periodic commodity news fetch.")
                
                # Fetch news from NewsAPI.ai/org focusing on commodity-relevant keywords
                commodity_keywords = "oil OR crude OR gold OR silver OR copper OR wheat OR corn OR natural gas OR supply OR demand OR inventory OR OPEC OR agriculture OR weather impact"
                news_from_api = self.news_api_client.fetch_news(
                    query=commodity_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=settings.COMMODITY_NEWS_FETCH_LIMIT
                )

                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=settings.COMMODITY_NEWS_RSS_LIMIT)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv Commodity Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially commodity-relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"Commodity Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    await self._process_and_publish_commodity_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv Commodity Agent '{self.agent_id}': Error during periodic commodity news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.COMMODITY_NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _process_and_publish_commodity_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for commodity relevance and publishes the insight.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"Commodity Agent: Skipping empty news item during direct fetch.")
            return

        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        # Assess commodity market impact based on LLM analysis
        commodity_impact_assessment = self._assess_commodity_impact(news_item, analysis_results)
        
        if commodity_impact_assessment.get("impact_level") != "NONE":
            logger.info(f"Commodity Agent: News impacts commodity market. Headline: {headline}. Impact: {commodity_impact_assessment.get('impact_level')}")
            await self._publish_commodity_alert("commodity_market_news_impact", commodity_impact_assessment)
            # Potentially trigger re-evaluation of specific commodity contracts
            for symbol in commodity_impact_assessment.get("symbols_impacted", []):
                await self._analyze_commodity_opportunity(symbol)

    async def _handle_commodity_market_data(self, message_payload: Dict[str, Any]):
        """
        Processes incoming commodity market data (spot prices, futures, inventory reports).
        This data would typically come from the MarketDataIngestor or a specialized commodity data ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            commodity_data = agent_message.payload

            symbol = commodity_data.get("symbol") # e.g., "WTI", "GOLD", "CORN"
            price = commodity_data.get("price")
            data_type = commodity_data.get("type") # e.g., "spot_price", "futures_price", "inventory_report"
            value = commodity_data.get("value")

            if symbol: # Ensure symbol is present
                if symbol not in self.commodity_market_data:
                    self.commodity_market_data[symbol] = {}
                
                # Update price information if available
                if price is not None:
                    self.commodity_market_data[symbol]["spot_price"] = price # Assume 'price' is spot price
                    # If it's a futures price, it should be explicitly handled by data_type
                    if data_type == "futures_price":
                        self.commodity_market_data[symbol]["futures_price"] = price
                
                # Update other data types (e.g., inventory)
                if data_type and value is not None:
                    self.commodity_market_data[symbol][data_type] = value
                
                self.commodity_market_data[symbol]["last_updated"] = datetime.now().isoformat()
                logger.debug(f"Commodity Agent: Updated data for {symbol}: {data_type}={self.commodity_market_data[symbol].get(data_type, price)}.")

                # If it's a price update, trigger opportunity analysis
                if price is not None: # Any price update
                    await self._analyze_commodity_opportunity(symbol)
                # If it's an inventory report, update supply/demand factors
                elif data_type == "inventory_report":
                    self.supply_demand_factors[symbol] = {
                        "inventory": value,
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.info(f"Commodity Agent: Updated inventory for {symbol}: {value}.")
                    await self._analyze_commodity_opportunity(symbol) # Re-evaluate based on new factors
                else:
                    pass # No specific action needed if neither price nor inventory report

        except Exception as e:
            logger.error(f"Commodity Agent '{self.agent_id}': Error handling commodity market data: {e}", exc_info=True)

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes news insights (from NewsAnalysisAgent) for geopolitical events, weather, or other factors
        affecting commodity supply/demand.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            category = news_insight.get('category', 'general')
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact_assessment = news_insight.get('market_impact_assessment', 'unknown')

            logger.info(f"Commodity Agent: Received news insight from {agent_message.sender_id}: '{headline}' (Category: {category}, Sentiment: {sentiment}, Impact: {market_impact_assessment})")

            # Assess commodity market impact based on the already processed news insight
            commodity_impact_assessment = self._assess_commodity_impact(news_insight, news_insight) # Pass news_insight as both raw and analyzed
            
            if commodity_impact_assessment.get("impact_level") != "NONE":
                logger.info(f"Commodity Agent: News insight suggests potential impact on commodity markets. Impact: {commodity_impact_assessment.get('impact_level')}.")
                await self._publish_commodity_alert("commodity_market_news_impact", commodity_impact_assessment)
                # Potentially trigger re-evaluation of specific commodity contracts
                for symbol in commodity_impact_assessment.get("symbols_impacted", []):
                    await self._analyze_commodity_opportunity(symbol)


        except Exception as e:
            logger.error(f"Commodity Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    async def _handle_economic_report(self, message_payload: Dict[str, Any]):
        """
        Processes economic reports (e.g., CPI, GDP) that can influence commodity prices.
        This data would typically come from an EconomicAgent or a dedicated economic data ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            report_data = agent_message.payload

            report_type = report_data.get("report_type")
            impact_summary = report_data.get("impact_summary")
            currency = report_data.get("currency")
            actual = report_data.get("actual")
            forecast = report_data.get("forecast")
            previous = report_data.get("previous")
            
            logger.info(f"Commodity Agent: Received economic report: {report_type}. Summary: {impact_summary}.")

            # Sophisticated analysis of economic report data
            economic_insight_prompt = (
                f"Analyze the economic report: '{report_type}' for {currency}. "
                f"Summary: '{impact_summary}'. "
                f"Actual: {actual}, Forecast: {forecast}, Previous: {previous}. "
                "Evaluate its specific implications for commodity markets (e.g., Gold, Oil, Industrial Metals, Agricultural products). "
                "Provide a concise summary of the commodity impact, a sentiment (bullish/bearish/neutral), "
                "and a list of most impacted commodity symbols (e.g., GOLD, CRUDE_OIL). "
                "Respond in JSON format with keys: 'commodity_impact_summary', 'sentiment', 'impacted_symbols'."
            )
            
            try:
                llm_response = await asyncio.to_thread(self.news_sentiment_analyzer.client.chat.completions.create,
                    model=self.news_sentiment_analyzer.model,
                    messages=[
                        {"role": "system", "content": "You are an expert commodity market analyst. Analyze economic reports for commodity market implications."},
                        {"role": "user", "content": economic_insight_prompt}
                    ],
                    max_tokens=settings.COMMODITY_LLM_MAX_TOKENS,
                    response_format={"type": "json_object"},
                    temperature=0.5
                )
                llm_analysis = json.loads(llm_response.choices[0].message.content)

                commodity_impact_summary = llm_analysis.get("commodity_impact_summary", "No specific commodity impact identified.")
                commodity_sentiment = llm_analysis.get("sentiment", "neutral").lower()
                impacted_symbols_llm = [s.upper() for s in llm_analysis.get("impacted_symbols", []) if isinstance(s, str)]

                logger.info(f"Commodity Agent: LLM analysis of economic report: {commodity_impact_summary}. Sentiment: {commodity_sentiment}.")

                # Update supply/demand factors and trigger analysis based on LLM insight
                for symbol in impacted_symbols_llm:
                    if symbol not in self.supply_demand_factors:
                        self.supply_demand_factors[symbol] = {"supply_change": 0.0, "demand_change": 0.0, "inventory": None}
                    
                    # Adjust conceptual supply/demand based on LLM sentiment
                    if commodity_sentiment == "bullish":
                        self.supply_demand_factors[symbol]["demand_change"] += settings.COMMODITY_LLM_IMPACT_FACTOR # Positive impact
                    elif commodity_sentiment == "bearish":
                        self.supply_demand_factors[symbol]["demand_change"] -= settings.COMMODITY_LLM_IMPACT_FACTOR # Negative impact
                    
                    self.supply_demand_factors[symbol]["timestamp"] = datetime.now().isoformat()
                    await self._analyze_commodity_opportunity(symbol)

            except Exception as e:
                logger.error(f"Commodity Agent: LLM analysis of economic report failed: {e}", exc_info=True)
                # Fallback to simpler keyword-based logic if LLM fails
                if "inflation" in impact_summary.lower() and "high" in impact_summary.lower():
                    logger.info("Commodity Agent: Inflationary pressure detected. Re-evaluating gold strategy.")
                    await self._analyze_commodity_opportunity("GOLD")
                if "industrial production" in report_type.lower() and actual is not None and forecast is not None and actual > forecast:
                    logger.info("Commodity Agent: Strong industrial production. Re-evaluating base metals strategy (e.g., COPPER).")
                    await self._analyze_commodity_opportunity("COPPER")

        except Exception as e:
            logger.error(f"Commodity Agent '{self.agent_id}': Error handling economic report: {e}", exc_info=True)

    def _assess_commodity_impact(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses the potential impact of a news item on commodity markets.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        symbols_mentioned = llm_analysis_results.get("symbols", [])
        
        impact_level = "NONE"
        symbols_impacted = []
        reasoning = "No direct commodity market impact detected."

        text_to_analyze = (headline + " " + content).lower()

        # Keywords for high impact on commodities
        high_impact_keywords = ["opec", "supply disruption", "demand surge", "inventory", "crop failure", "drought", "flood", "mining strike", "geopolitical tension", "trade war"]
        # Keywords for medium impact
        medium_impact_keywords = ["manufacturing pmi", "industrial output", "consumer demand", "economic growth forecast"]

        if any(keyword in text_to_analyze for keyword in high_impact_keywords):
            impact_level = "HIGH"
            reasoning = "News contains high-impact keywords for commodity markets."
        elif any(keyword in text_to_analyze for keyword in medium_impact_keywords):
            impact_level = "MEDIUM"
            reasoning = "News contains medium-impact keywords for commodity markets."
        
        # Identify specific symbols/commodities impacted
        if "oil" in text_to_analyze or "crude" in text_to_analyze or "brent" in text_to_analyze:
            symbols_impacted.append("CRUDE_OIL") # Use generic symbol for this agent
            symbols_impacted.append("BRENT")
        if "gold" in text_to_analyze or "precious metals" in text_to_analyze:
            symbols_impacted.append("GOLD")
        if "silver" in text_to_analyze:
            symbols_impacted.append("SILVER")
        if "wheat" in text_to_analyze or "corn" in text_to_analyze or "soy" in text_to_analyze:
            symbols_impacted.append("AGRICULTURE") # Generic for agricultural commodities
        if "copper" in text_to_analyze or "industrial metals" in text_to_analyze:
            symbols_impacted.append("COPPER")

        # If LLM mentioned symbols, add them (ensure they are commodity-related)
        # This requires a mapping or a more intelligent filter
        for sym in symbols_mentioned:
            if sym.upper() in ["XAUUSD", "XAGUSD", "CL=F", "GC=F", "ZC=F", "ZS=F", "ZW=F"]: # Example futures symbols
                symbols_impacted.append(sym.upper())
            elif sym.upper() in ["GOLD", "SILVER", "CRUDE_OIL", "CORN", "WHEAT", "COPPER"]:
                symbols_impacted.append(sym.upper())

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


    async def _analyze_commodity_opportunity(self, symbol: str):
        """
        Analyzes a commodity for trade opportunities.
        Considers current price, and conceptual supply/demand factors.
        """
        price_data = self.commodity_market_data.get(symbol)
        current_price = price_data.get("spot_price") or price_data.get("futures_price") if price_data else None

        if current_price is None:
            logger.warning(f"Commodity Agent: No price data available for {symbol}. Cannot analyze opportunity.")
            return

        supply_demand = self.supply_demand_factors.get(symbol, {"supply_change": 0.0, "demand_change": 0.0, "inventory": None})
        net_supply_demand_pressure = supply_demand["demand_change"] - supply_demand["supply_change"]

        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = f"Monitoring {symbol}. Price: {current_price}. Net S/D Pressure: {net_supply_demand_pressure:.2f}."
        
        # Incorporate inventory data if available
        if supply_demand.get("inventory") is not None:
            if supply_demand["inventory"] < getattr(settings, 'COMMODITY_LOW_INVENTORY_THRESHOLD', 1000): # Example threshold
                net_supply_demand_pressure += 0.1 # Add bullish pressure
                reasoning += f" Low inventory ({supply_demand['inventory']})."
            elif supply_demand["inventory"] > getattr(settings, 'COMMODITY_HIGH_INVENTORY_THRESHOLD', 5000): # Example threshold
                net_supply_demand_pressure -= 0.1 # Add bearish pressure
                reasoning += f" High inventory ({supply_demand['inventory']})."


        # Simple conceptual logic:
        # Positive net pressure (demand > supply) -> BUY
        # Negative net pressure (supply > demand) -> SELL
        COMMODITY_BUY_THRESHOLD = getattr(settings, 'COMMODITY_BUY_THRESHOLD', 0.05)
        COMMODITY_SELL_THRESHOLD = getattr(settings, 'COMMODITY_SELL_THRESHOLD', -0.05)

        if net_supply_demand_pressure > COMMODITY_BUY_THRESHOLD: # Significant demand pressure
            action = TradeAction.BUY
            confidence = 0.7
            reasoning = f"Strong demand pressure detected for {symbol} (Net S/D: {net_supply_demand_pressure:.2f}). {reasoning}"
        elif net_supply_demand_pressure < COMMODITY_SELL_THRESHOLD: # Significant supply pressure
            action = TradeAction.SELL
            confidence = 0.7
            reasoning = f"Significant oversupply detected for {symbol} (Net S/D: {net_supply_demand_pressure:.2f}). {reasoning}"

        if action != TradeAction.HOLD:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=action,
                volume=settings.COMMODITY_TRADE_PROPOSAL_VOLUME, # Configurable unit of commodity
                entry_price=current_price,
                reasoning=reasoning,
                confidence=confidence,
                risk_assessment={"commodity_specific_risk": "high_volatility", "supply_demand_imbalance": net_supply_demand_pressure}
            )
            await self._publish_commodity_proposal(proposal)

    async def _publish_commodity_alert(self, alert_type: str, details: Dict[str, Any]):
        """Helper to publish commodity-related alerts."""
        alert_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ERROR_NOTIFICATION, # Reusing ERROR_NOTIFICATION for alerts
            payload={
                "source_agent_id": self.agent_id,
                "message": f"Commodity Alert: {alert_type}",
                "severity": details.get("impact_level", "MEDIUM"), # Use impact level as severity
                "alert_type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("commodity_alerts", alert_message.model_dump())
        logger.log(logging.getLevelName(details.get("impact_level", "MEDIUM")), f"Commodity Agent: Published commodity alert: {alert_type}.")

        # Send WhatsApp alert for critical commodity market news
        if details.get("impact_level") == "HIGH":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            whatsapp_message = (
                f"🚨 COMMODITY MARKET ALERT! 🚨\n"
                f"Headline: {details.get('headline')}\n"
                f"Impact: {details.get('impact_level')}\n"
                f"Symbols: {', '.join(details.get('symbols_impacted', []))}\n"
                f"Reason: {details.get('reasoning')}"
            )
            try:
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"Commodity Agent: Conceptually sent critical WhatsApp alert for commodity market to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"Commodity Agent: Failed to send WhatsApp alert for commodity: {e}", exc_info=True)


    async def _publish_commodity_proposal(self, proposal: TradeProposal):
        """Helper to publish a trade proposal generated by the commodity agent."""
        proposal_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.TRADE_PROPOSAL,
            payload=proposal.model_dump()
        )
        await self.broker.publish_message("trade_proposals", proposal_message.model_dump())
        logger.info(f"Commodity Agent: Published trade proposal: {proposal.action} {proposal.symbol} (Confidence: {proposal.confidence:.2f}).")


# Example Usage (for testing PrivCommodityAgent in isolation)
async def main_commodity_agent_test():
    logging.basicConfig(level=logging.INFO)
    import json # For LLM response parsing in test
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_news_analysis_agent import PrivNewsAnalysisAgent # To simulate news insights
    # Assuming PrivEconomicAgent exists and publishes economic_reports
    # from backend.multi_agent.priv_economic_agent import PrivEconomicAgent

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
    if not hasattr(settings, 'COMMODITY_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.COMMODITY_NEWS_FETCH_INTERVAL_SECONDS = 10
    if not hasattr(settings, 'COMMODITY_NEWS_FETCH_LIMIT'):
        settings.COMMODITY_NEWS_FETCH_LIMIT = 5
    if not hasattr(settings, 'COMMODITY_NEWS_RSS_LIMIT'):
        settings.COMMODITY_NEWS_RSS_LIMIT = 3
    if not hasattr(settings, 'COMMODITY_LOW_INVENTORY_THRESHOLD'):
        settings.COMMODITY_LOW_INVENTORY_THRESHOLD = 1000
    if not hasattr(settings, 'COMMODITY_HIGH_INVENTORY_THRESHOLD'):
        settings.COMMODITY_HIGH_INVENTORY_THRESHOLD = 5000
    if not hasattr(settings, 'COMMODITY_BUY_THRESHOLD'):
        settings.COMMODITY_BUY_THRESHOLD = 0.05
    if not hasattr(settings, 'COMMODITY_SELL_THRESHOLD'):
        settings.COMMODITY_SELL_THRESHOLD = -0.05
    if not hasattr(settings, 'COMMODITY_TRADE_PROPOSAL_VOLUME'):
        settings.COMMODITY_TRADE_PROPOSAL_VOLUME = 1 # Conceptual volume
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"
    if not hasattr(settings, 'COMMODITY_LLM_MAX_TOKENS'):
        settings.COMMODITY_LLM_MAX_TOKENS = 300
    if not hasattr(settings, 'COMMODITY_LLM_IMPACT_FACTOR'):
        settings.COMMODITY_LLM_IMPACT_FACTOR = 0.05 # Default impact factor from LLM analysis


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    commodity_agent = PrivCommodityAgent(
        agent_id="Priv-CommodityTrader",
        broker=broker,
        persona={"name": "Commodity Specialist", "focus": "Physical & Derivative Commodities"}
    )
    news_agent = PrivNewsAnalysisAgent( # For simulating news insights
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )
    # Mock EconomicAgent for testing purposes, assuming it publishes economic_reports
    class MockEconomicAgent:
        def __init__(self, broker): self.broker = broker
        async def start(self):
            logger.info("MockEconomicAgent started.")
            # Simulate an economic report indicating high inflation
            mock_economic_report_inflation = AgentMessage(
                sender_id="Priv-Economist",
                message_type=MessageType.STATUS_UPDATE,
                payload={
                    "report_type": "CPI_Report",
                    "impact_summary": "Consumer Price Index shows higher-than-expected inflation, potentially bullish for gold.",
                    "data": {"cpi_yoy": 0.035},
                    "timestamp": datetime.now().isoformat(),
                    "actual": 0.035, "forecast": 0.025, "currency": "USD" # Added for potential use
                }
            )
            # Patch the LLM response for economic report analysis in test
            with patch('backend.fundamental_analysis.news_sentiment_analyzer.OpenAI.chat.completions.create') as mock_llm_create:
                mock_llm_create.return_value = MagicMock()
                mock_llm_create.return_value.choices[0].message.content = json.dumps({
                    "commodity_impact_summary": "High inflation suggests bullish outlook for gold and other inflation-hedge commodities.",
                    "sentiment": "bullish",
                    "impacted_symbols": ["GOLD", "SILVER"]
                })
                await self.broker.publish_message("economic_reports", mock_economic_report_inflation.model_dump())
            logger.info("MockEconomicAgent published mock economic report.")
        async def stop(self): logger.info("MockEconomicAgent stopped.")

    economic_agent = MockEconomicAgent(broker)


    await broker.connect()
    await commodity_agent.start()
    await news_agent.start()
    await economic_agent.start() # Start mock economic agent

    logger.info("\n--- Simulating messages for Commodity Agent to consume ---")

    # Simulate commodity spot price data (Crude Oil)
    mock_crude_spot_data = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "CRUDE_OIL",
            "type": "spot_price",
            "price": 85.20,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("commodity_market_data", mock_crude_spot_data.model_dump())
    await asyncio.sleep(0.5)

    # Simulate commodity futures price data (Gold)
    mock_gold_futures_data = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "GOLD",
            "type": "futures_price",
            "price": 2350.00,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("commodity_market_data", mock_gold_futures_data.model_dump())
    await asyncio.sleep(0.5)

    # Simulate inventory report for Crude Oil
    mock_crude_inventory_data = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "CRUDE_OIL",
            "type": "inventory_report",
            "value": 800, # Low inventory
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("commodity_market_data", mock_crude_inventory_data.model_dump())
    await asyncio.sleep(0.5)


    # Simulate news impacting crude oil supply (from NewsAnalysisAgent)
    mock_news_oil_supply_insight = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "original_news_id": "news_oil_1",
            "source": "Reuters",
            "headline": "Major oil pipeline disruption in North America.",
            "content": "A key pipeline has been shut down, leading to concerns about crude oil supply shortages in the region.",
            "category": "geopolitical",
            "sentiment": "negative", # Negative for supply
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "crude_oil_supply_shock",
            "confidence_score": 0.9,
            "symbols_mentioned": ["CRUDE_OIL", "WTI"]
        }
    )
    await broker.publish_message("news_insights", mock_news_oil_supply_insight.model_dump())
    await asyncio.sleep(1)

    # Economic report is simulated by MockEconomicAgent.start()

    await asyncio.sleep(15) # Give time for agents to process messages and for periodic fetches

    await commodity_agent.stop()
    await news_agent.stop()
    await economic_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivCommodityAgent test finished.")

if __name__ == '__main__':
    from unittest.mock import patch, MagicMock # Needed for test patching
    asyncio.run(main_commodity_agent_test())
