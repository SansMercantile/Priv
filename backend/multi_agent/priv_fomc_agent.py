# backend/multi_agent/priv_fomc_agent.py

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

# Import actual data sourcing and analysis clients
from backend.fundamental_analysis.economic_calendar.manager import EconomicCalendarManager
from backend.fundamental_analysis.economic_calendar.defines import EconomicEvent, ImpactLevel, EventType
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer # Reusing for LLM
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor # For current prices for proposals

# Import settings for configurable thresholds and API keys
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivFOMCAgent(PrivAgent):
    """
    A specialized Priv Agent focused on monitoring, analyzing, and reacting to
    Federal Open Market Committee (FOMC) meetings, statements, and press conferences.
    It interprets the hawkish/dovish tone and its implications for interest rates,
    currency markets (especially USD), and bond markets.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.FOMC, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.fomc_events_tracked: Dict[str, Dict[str, Any]] = {} # Cache for FOMC events and their outcomes
        self.last_fomc_stance: Dict[str, Any] = {"stance": "neutral", "timestamp": None}

        # Initialize real data sourcing and analysis clients
        self.economic_calendar_manager = EconomicCalendarManager(
            calendar_url=settings.ECONOMIC_CALENDAR_URL
        )
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.news_sentiment_analyzer = NewsSentimentAnalyzer(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini" # Using a more capable model for nuanced policy analysis
        )
        self.global_news_ingestor = GlobalNewsIngestor()
        self.market_data_ingestor = MarketDataIngestor(self.broker)
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv FOMC Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the FOMC agent, subscribing to relevant data feeds and scheduling tasks."""
        if self.is_running:
            logger.warning(f"FOMC Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to economic reports (specifically FOMC-related ones)
        await self.broker.subscribe_to_topic(
            "economic_reports", self._handle_economic_report, f"{self.agent_id}-econ-sub"
        )
        # Subscribe to news insights (for general market sentiment around central banks)
        await self.broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )

        self.is_running = True
        # Schedule periodic tasks
        self._periodic_fomc_calendar_check_task = asyncio.create_task(self._periodic_fomc_calendar_check())
        self._periodic_fomc_news_fetch_task = asyncio.create_task(self._periodic_fomc_news_fetch())
        logger.info(f"Priv FOMC Agent '{self.agent_id}' started and scheduled tasks.")

    async def stop(self):
        """Stops the FOMC agent and cancels periodic tasks."""
        if not self.is_running:
            logger.warning(f"FOMC Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_fomc_calendar_check_task:
            self._periodic_fomc_calendar_check_task.cancel()
            try: await self._periodic_fomc_calendar_check_task
            except asyncio.CancelledError: logger.info(f"FOMC Agent calendar check task cancelled.")
        if self._periodic_fomc_news_fetch_task:
            self._periodic_fomc_news_fetch_task.cancel()
            try: await self._periodic_fomc_news_fetch_task
            except asyncio.CancelledError: logger.info(f"FOMC Agent news fetch task cancelled.")

        logger.info(f"Priv FOMC Agent '{self.agent_id}' stopped.")

    async def _periodic_fomc_calendar_check(self):
        """
        Periodically checks the economic calendar for upcoming or recent FOMC events.
        """
        while self.is_running:
            try:
                logger.info(f"Priv FOMC Agent '{self.agent_id}': Checking economic calendar for FOMC events.")
                
                # Fetch economic events for today and next few days
                fomc_events = self.economic_calendar_manager.get_events(
                    start_time=datetime.now() - timedelta(hours=24), # Look back 24 hours
                    end_time=datetime.now() + timedelta(days=settings.FOMC_CALENDAR_LOOKAHEAD_DAYS),
                    event_types=[EventType.INTEREST_RATES, EventType.SPEECH],
                    currencies=["USD"],
                    impact_levels=[ImpactLevel.HIGH],
                    refresh_if_stale=True
                )

                for event in fomc_events:
                    if "fomc" in event.event_name.lower() or "federal reserve" in event.event_name.lower():
                        event_id = event.id
                        if event_id not in self.fomc_events_tracked:
                            self.fomc_events_tracked[event_id] = event.model_dump()
                            logger.info(f"FOMC Agent: Detected new FOMC event: {event.event_name} on {event.timestamp}.")
                            
                            # If event is in the past (i.e., just released), trigger immediate news analysis
                            if event.timestamp < datetime.now() and event.actual is not None:
                                logger.info(f"FOMC Agent: FOMC event {event.event_name} just released. Triggering immediate analysis.")
                                await self._analyze_fomc_outcome(event)
                            else:
                                logger.info(f"FOMC Agent: Upcoming FOMC event: {event.event_name}. Will monitor for release.")
                                await self._publish_fomc_alert(
                                    "upcoming_fomc_event",
                                    f"Upcoming FOMC event: {event.event_name} on {event.timestamp.isoformat()}.",
                                    event.model_dump(),
                                    severity="HIGH"
                                )
            except Exception as e:
                logger.error(f"Priv FOMC Agent '{self.agent_id}': Error during periodic calendar check: {e}", exc_info=True)
            
            await asyncio.sleep(settings.FOMC_CALENDAR_CHECK_INTERVAL_SECONDS)

    async def _periodic_fomc_news_fetch(self):
        """
        Periodically fetches news specifically relevant to FOMC and Federal Reserve.
        """
        while self.is_running:
            try:
                logger.info(f"Priv FOMC Agent '{self.agent_id}': Initiating periodic FOMC news fetch.")
                
                fomc_keywords = "FOMC OR Federal Reserve OR Fed OR Jerome Powell OR interest rates OR monetary policy OR quantitative easing OR quantitative tightening"
                news_from_api = self.news_api_client.fetch_news(
                    query=fomc_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=settings.FOMC_NEWS_FETCH_LIMIT
                )

                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=settings.FOMC_NEWS_RSS_LIMIT)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv FOMC Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially FOMC-relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"FOMC Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    await self._process_and_publish_fomc_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv FOMC Agent '{self.agent_id}': Error during periodic FOMC news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.FOMC_NEWS_FETCH_INTERVAL_SECONDS)

    async def _process_and_publish_fomc_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for FOMC relevance and publishes the insight.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"FOMC Agent: Skipping empty news item during direct fetch.")
            return

        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        fomc_impact_assessment = await self._assess_fomc_impact(news_item, analysis_results)
        
        if fomc_impact_assessment.get("stance") != "neutral":
            logger.info(f"FOMC Agent: News impacts FOMC stance. Headline: {headline}. Stance: {fomc_impact_assessment.get('stance')}")
            await self._publish_fomc_alert("fomc_news_impact", fomc_impact_assessment)
            
            # Update last known FOMC stance
            self.last_fomc_stance = {
                "stance": fomc_impact_assessment["stance"],
                "timestamp": datetime.now().isoformat(),
                "reasoning": fomc_impact_assessment["reasoning"]
            }
            # Potentially trigger trade proposals based on new stance
            await self._generate_trade_proposal_from_fomc_stance(fomc_impact_assessment)

    async def _handle_economic_report(self, message_payload: Dict[str, Any]):
        """
        Processes incoming economic reports, specifically looking for FOMC-related releases.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            report_data = agent_message.payload

            report_type = report_data.get("report_type")
            currency = report_data.get("currency")
            
            if currency == "USD" and ("fomc" in report_type.lower() or "federal reserve" in report_type.lower() or "interest rate decision" in report_type.lower()):
                logger.info(f"FOMC Agent: Received FOMC-related economic report: {report_type}.")
                # Convert to EconomicEvent object for consistent processing
                # This assumes report_data has enough fields to construct an EconomicEvent
                event_timestamp = datetime.fromisoformat(report_data["timestamp"]) if "timestamp" in report_data else datetime.now()
                event_id = f"{event_timestamp.isoformat()}-{report_type}-{currency}"

                # Attempt to get impact level from report_data, default to HIGH for FOMC
                impact_level = ImpactLevel.HIGH
                if "impact" in report_data and report_data["impact"] in [e.value for e in ImpactLevel]:
                    impact_level = ImpactLevel(report_data["impact"])

                fomc_event = EconomicEvent(
                    id=event_id,
                    timestamp=event_timestamp,
                    currency=currency,
                    event_name=report_type,
                    impact=impact_level,
                    actual=report_data.get("actual"),
                    forecast=report_data.get("forecast"),
                    previous=report_data.get("previous"),
                    unit=report_data.get("unit"),
                    event_type=EventType.INTEREST_RATES if "interest rate" in report_type.lower() else EventType.SPEECH,
                    description=report_data.get("impact_summary")
                )
                
                # Check if this event has already been processed by calendar check
                if fomc_event.id not in self.fomc_events_tracked:
                    self.fomc_events_tracked[fomc_event.id] = fomc_event.model_dump()
                    logger.info(f"FOMC Agent: New FOMC event {fomc_event.event_name} processed from economic reports.")
                    await self._analyze_fomc_outcome(fomc_event)
                else:
                    logger.debug(f"FOMC Agent: Event {fomc_event.id} already tracked.")

        except Exception as e:
            logger.error(f"Priv FOMC Agent '{self.agent_id}': Error handling economic report: {e}", exc_info=True)

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes news insights (from NewsAnalysisAgent) for general central bank sentiment.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            
            # Check if headline or content contains FOMC-relevant keywords
            fomc_keywords = ["fomc", "federal reserve", "fed", "jerome powell", "monetary policy"]
            if any(keyword in headline.lower() for keyword in fomc_keywords) or \
               any(keyword in news_insight.get('content', '').lower() for keyword in fomc_keywords):
                
                logger.info(f"FOMC Agent: Received FOMC-relevant news insight: '{headline}'.")
                fomc_impact_assessment = await self._assess_fomc_impact(news_insight, news_insight) # Reuse insight for analysis
                
                if fomc_impact_assessment.get("stance") != "neutral":
                    logger.info(f"FOMC Agent: News insight impacts FOMC stance. Stance: {fomc_impact_assessment.get('stance')}")
                    await self._publish_fomc_alert("fomc_news_insight_impact", fomc_impact_assessment)
                    
                    self.last_fomc_stance = {
                        "stance": fomc_impact_assessment["stance"],
                        "timestamp": datetime.now().isoformat(),
                        "reasoning": fomc_impact_assessment["reasoning"]
                    }
                    await self._generate_trade_proposal_from_fomc_stance(fomc_impact_assessment)

        except Exception as e:
            logger.error(f"Priv FOMC Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    async def _analyze_fomc_outcome(self, fomc_event: EconomicEvent):
        """
        Analyzes the outcome of an FOMC event (e.g., rate decision, statement) using LLM.
        """
        logger.info(f"FOMC Agent: Analyzing FOMC event outcome: {fomc_event.event_name} (Actual: {fomc_event.actual}, Forecast: {fomc_event.forecast}).")
        
        # Construct prompt for LLM based on economic event details and recent news
        prompt = (
            f"Analyze the outcome of the FOMC event: '{fomc_event.event_name}' on {fomc_event.timestamp.isoformat()}. "
            f"Actual value: {fomc_event.actual}, Forecast: {fomc_event.forecast}, Previous: {fomc_event.previous}. "
            f"Description: {fomc_event.description}. "
            "Determine the overall stance of the Federal Reserve (hawkish, dovish, neutral). "
            "Provide a concise summary of the implications for the USD and US bond markets. "
            "Suggest potential trade directions for USD (e.g., BUY USD, SELL USD, HOLD USD) and US bonds (e.g., BUY bonds, SELL bonds). "
            "Assign a confidence score [0-1] for your assessment. "
            "Respond in JSON format with keys: 'stance', 'summary', 'usd_implication', 'bonds_implication', 'trade_recommendation', 'confidence'."
        )

        try:
            llm_response = await asyncio.to_thread(self.news_sentiment_analyzer.client.chat.completions.create,
                model=self.news_sentiment_analyzer.model,
                messages=[
                    {"role": "system", "content": "You are an expert central bank policy analyst. Provide a concise analysis of FOMC outcomes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.FOMC_LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
                temperature=0.5
            )
            llm_analysis = json.loads(llm_response.choices[0].message.content)

            fomc_analysis_result = {
                "event_id": fomc_event.id,
                "event_name": fomc_event.event_name,
                "timestamp": fomc_event.timestamp.isoformat(),
                "stance": llm_analysis.get("stance", "neutral").lower(),
                "summary": llm_analysis.get("summary", "Analysis not available."),
                "usd_implication": llm_analysis.get("usd_implication"),
                "bonds_implication": llm_analysis.get("bonds_implication"),
                "trade_recommendation": llm_analysis.get("trade_recommendation"),
                "confidence": llm_analysis.get("confidence", 0.0),
                "raw_event_data": fomc_event.model_dump()
            }
            self.fomc_events_tracked[fomc_event.id] = fomc_analysis_result
            self.last_fomc_stance = {
                "stance": fomc_analysis_result["stance"],
                "timestamp": datetime.now().isoformat(),
                "reasoning": fomc_analysis_result["summary"]
            }

            logger.info(f"FOMC Agent: Analyzed FOMC outcome. Stance: {fomc_analysis_result['stance']}. Confidence: {fomc_analysis_result['confidence']:.2f}.")
            await self._publish_fomc_alert("fomc_outcome_analysis", fomc_analysis_result, severity="CRITICAL")
            await self._generate_trade_proposal_from_fomc_stance(fomc_analysis_result)

        except Exception as e:
            logger.error(f"FOMC Agent: LLM analysis of FOMC outcome failed: {e}", exc_info=True)
            # Fallback to simple logic if LLM fails
            stance = "neutral"
            if fomc_event.actual > fomc_event.forecast: stance = "hawkish" # Higher than expected rate hike
            elif fomc_event.actual < fomc_event.forecast: stance = "dovish" # Lower than expected rate hike
            
            fomc_analysis_result = {
                "event_id": fomc_event.id,
                "event_name": fomc_event.event_name,
                "timestamp": fomc_event.timestamp.isoformat(),
                "stance": stance,
                "summary": f"Simple analysis: Actual {fomc_event.actual} vs Forecast {fomc_event.forecast}.",
                "usd_implication": None, "bonds_implication": None, "trade_recommendation": None, "confidence": 0.5,
                "raw_event_data": fomc_event.model_dump()
            }
            self.last_fomc_stance = {
                "stance": stance,
                "timestamp": datetime.now().isoformat(),
                "reasoning": fomc_analysis_result["summary"]
            }
            await self._publish_fomc_alert("fomc_outcome_simple_analysis", fomc_analysis_result, severity="HIGH")
            await self._generate_trade_proposal_from_fomc_stance(fomc_analysis_result)


    async def _assess_fomc_impact(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses the potential FOMC stance implied by a news item, leveraging LLM analysis.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        
        stance = "neutral"
        reasoning = "No clear FOMC stance implied by news."

        text_to_analyze = (headline + " " + content).lower()

        # Keywords for hawkish stance
        hawkish_keywords = ["rate hike", "tapering", "tightening", "inflation concerns", "strong economy", "hawkish"]
        # Keywords for dovish stance
        dovish_keywords = ["rate cut", "easing", "stimulus", "recession fears", "weak economy", "dovish"]

        if any(keyword in text_to_analyze for keyword in hawkish_keywords):
            stance = "hawkish"
            reasoning = "News suggests a hawkish FOMC stance."
        elif any(keyword in text_to_analyze for keyword in dovish_keywords):
            stance = "dovish"
            reasoning = "News suggests a dovish FOMC stance."
        
        # Refine based on LLM sentiment
        if stance == "neutral": # If no strong keywords, rely more on general sentiment
            if sentiment == "positive": stance = "slightly_hawkish"
            elif sentiment == "negative": stance = "slightly_dovish"

        return {
            "headline": headline,
            "sentiment": sentiment,
            "stance": stance,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }

    async def _generate_trade_proposal_from_fomc_stance(self, fomc_analysis: Dict[str, Any]):
        """
        Generates a trade proposal based on the determined FOMC stance.
        Targets USD currency pairs and potentially US bond futures.
        """
        stance = fomc_analysis.get("stance")
        confidence = fomc_analysis.get("confidence", 0.5)
        reasoning_base = fomc_analysis.get("summary", "FOMC analysis indicates a specific stance.")

        trade_action_usd = TradeAction.HOLD
        trade_action_bonds = TradeAction.HOLD
        
        # Get current USDJPY price for proposal
        usdjpy_data = await self.market_data_ingestor.get_latest_market_data("USDJPY")
        usdjpy_price = usdjpy_data.get("last_trade_price") if usdjpy_data else None

        if stance == "hawkish":
            trade_action_usd = TradeAction.BUY
            trade_action_bonds = TradeAction.SELL # Higher rates -> lower bond prices
            reasoning = f"Hawkish FOMC stance: implies higher interest rates, bullish for USD, bearish for bonds. {reasoning_base}"
            confidence = min(1.0, confidence + settings.FOMC_STANCE_CONFIDENCE_BOOST)
        elif stance == "dovish":
            trade_action_usd = TradeAction.SELL
            trade_action_bonds = TradeAction.BUY # Lower rates -> higher bond prices
            reasoning = f"Dovish FOMC stance: implies lower interest rates, bearish for USD, bullish for bonds. {reasoning_base}"
            confidence = min(1.0, confidence + settings.FOMC_STANCE_CONFIDENCE_BOOST)
        else: # Neutral or slightly_hawkish/dovish
            reasoning = f"Neutral FOMC stance: limited immediate impact. {reasoning_base}"
            confidence = max(0.0, confidence - settings.FOMC_STANCE_CONFIDENCE_DECAY)

        if trade_action_usd != TradeAction.HOLD and usdjpy_price:
            usd_proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol="USDJPY", # Example USD pair
                action=trade_action_usd,
                volume=settings.FOMC_TRADE_PROPOSAL_VOLUME_FX, # Configurable volume
                entry_price=usdjpy_price,
                reasoning=reasoning,
                confidence=confidence,
                risk_assessment={"fomc_impact": stance, "asset_class": "FX"}
            )
            await self.broker.publish_message("trade_proposals", usd_proposal.model_dump())
            logger.info(f"FOMC Agent: Published USD trade proposal: {usd_proposal.action} {usd_proposal.symbol} (Conf: {usd_proposal.confidence:.2f}).")

        if trade_action_bonds != TradeAction.HOLD:
            # For bonds, use a generic bond futures symbol, e.g., ZB=F (US Treasury Bond Futures)
            zb_futures_data = await self.market_data_ingestor.get_latest_market_data("ZB=F")
            zb_futures_price = zb_futures_data.get("last_trade_price") if zb_futures_data else None

            if zb_futures_price:
                bond_proposal = TradeProposal(
                    agent_id=self.agent_id,
                    symbol="ZB=F", # US Treasury Bond Futures
                    action=trade_action_bonds,
                    volume=settings.FOMC_TRADE_PROPOSAL_VOLUME_BONDS, # Configurable volume
                    entry_price=zb_futures_price,
                    reasoning=reasoning,
                    confidence=confidence,
                    risk_assessment={"fomc_impact": stance, "asset_class": "Bonds"}
                )
                await self.broker.publish_message("trade_proposals", bond_proposal.model_dump())
                logger.info(f"FOMC Agent: Published Bond trade proposal: {bond_proposal.action} {bond_proposal.symbol} (Conf: {bond_proposal.confidence:.2f}).")

    async def _publish_fomc_alert(self, alert_type: str, details: Dict[str, Any], severity: str = "MEDIUM"):
        """Helper to publish FOMC-related alerts."""
        alert_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ERROR_NOTIFICATION, # Reusing ERROR_NOTIFICATION for alerts
            payload={
                "source_agent_id": self.agent_id,
                "message": f"FOMC Alert: {alert_type}",
                "severity": severity, # CRITICAL, HIGH, MEDIUM, LOW
                "alert_type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("fomc_alerts", alert_message.model_dump())
        logger.log(logging.getLevelName(severity), f"FOMC Agent: Published FOMC alert: {alert_type}.")

        # Send WhatsApp alert for critical FOMC events
        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            whatsapp_message = (
                f"🚨 CRITICAL FOMC ALERT! 🚨\n"
                f"Type: {alert_type}\n"
                f"Stance: {details.get('stance', 'N/A')}\n"
                f"Summary: {details.get('summary', 'N/A')}\n"
                f"USD Implication: {details.get('usd_implication', 'N/A')}"
            )
            try:
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"FOMC Agent: Conceptually sent critical WhatsApp alert for FOMC to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"FOMC Agent: Failed to send WhatsApp alert for FOMC: {e}", exc_info=True)


# Example Usage (for testing PrivFomcAgent in isolation)
async def main_fomc_agent_test():
    logging.basicConfig(level=logging.INFO)
    import json # For LLM response parsing in test
    import re # For regex in LLM parsing
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_news_analysis_agent import PrivNewsAnalysisAgent # To simulate news insights
    from unittest.mock import patch, MagicMock # Needed for test patching

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
    if not hasattr(settings, 'ECONOMIC_CALENDAR_URL'):
        settings.ECONOMIC_CALENDAR_URL = "https://www.dailyfx.com/economic-calendar"
    if not hasattr(settings, 'FOMC_CALENDAR_LOOKAHEAD_DAYS'):
        settings.FOMC_CALENDAR_LOOKAHEAD_DAYS = 7
    if not hasattr(settings, 'FOMC_CALENDAR_CHECK_INTERVAL_SECONDS'):
        settings.FOMC_CALENDAR_CHECK_INTERVAL_SECONDS = 5 # Frequent for test
    if not hasattr(settings, 'FOMC_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.FOMC_NEWS_FETCH_INTERVAL_SECONDS = 10
    if not hasattr(settings, 'FOMC_NEWS_FETCH_LIMIT'):
        settings.FOMC_NEWS_FETCH_LIMIT = 5
    if not hasattr(settings, 'FOMC_NEWS_RSS_LIMIT'):
        settings.FOMC_NEWS_RSS_LIMIT = 3
    if not hasattr(settings, 'FOMC_LLM_MAX_TOKENS'):
        settings.FOMC_LLM_MAX_TOKENS = 500
    if not hasattr(settings, 'FOMC_STANCE_CONFIDENCE_BOOST'):
        settings.FOMC_STANCE_CONFIDENCE_BOOST = 0.1
    if not hasattr(settings, 'FOMC_STANCE_CONFIDENCE_DECAY'):
        settings.FOMC_STANCE_CONFIDENCE_DECAY = 0.05
    if not hasattr(settings, 'FOMC_TRADE_PROPOSAL_VOLUME_FX'):
        settings.FOMC_TRADE_PROPOSAL_VOLUME_FX = 0.1
    if not hasattr(settings, 'FOMC_TRADE_PROPOSAL_VOLUME_BONDS'):
        settings.FOMC_TRADE_PROPOSAL_VOLUME_BONDS = 1
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    fomc_agent = PrivFOMCAgent(
        agent_id="Priv-FOMCWatcher",
        broker=broker,
        persona={"name": "FOMC Policy Analyst", "focus": "Monetary Policy & Central Banks"}
    )
    news_agent = PrivNewsAnalysisAgent( # To simulate news insights
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await fomc_agent.start()
    await news_agent.start()

    logger.info("\n--- Simulating messages for FOMC Agent to consume ---")

    # Mock MarketDataIngestor's get_latest_market_data for USDJPY and ZB=F
    with patch('backend.data_sourcing.market_data_ingestor.MarketDataIngestor.get_latest_market_data') as mock_get_market_data:
        mock_get_market_data.side_effect = [
            {"last_trade_price": 150.20, "timestamp": datetime.now().timestamp() * 1e9, "source": "Mock"}, # For USDJPY
            {"last_trade_price": 110.50, "timestamp": datetime.now().timestamp() * 1e9, "source": "Mock"}, # For ZB=F
            {"last_trade_price": 150.25, "timestamp": datetime.now().timestamp() * 1e9, "source": "Mock"}, # For subsequent USDJPY
            {"last_trade_price": 110.40, "timestamp": datetime.now().timestamp() * 1e9, "source": "Mock"}, # For subsequent ZB=F
        ]
        
        # Simulate an economic report for an FOMC interest rate decision
        mock_fomc_decision_report = AgentMessage(
            sender_id="Priv-Economist",
            message_type=MessageType.STATUS_UPDATE,
            payload={
                "report_type": "FOMC Interest Rate Decision",
                "impact_summary": "Federal Reserve raises interest rates by 25 basis points, hawkish tone.",
                "timestamp": datetime.now().isoformat(),
                "currency": "USD",
                "actual": 0.0550, # 5.50%
                "forecast": 0.0525, # 5.25%
                "previous": 0.0525,
                "impact": ImpactLevel.HIGH.value,
                "event_name": "FOMC Statement and Federal Funds Rate"
            }
        )
        # Patch the LLM response for FOMC outcome analysis
        with patch('backend.fundamental_analysis.news_sentiment_analyzer.OpenAI.chat.completions.create') as mock_llm_create:
            mock_llm_create.return_value = MagicMock()
            mock_llm_create.return_value.choices[0].message.content = json.dumps({
                "stance": "hawkish",
                "summary": "The Federal Reserve's decision to raise rates by 25bps, exceeding forecasts, signals a strong commitment to combating inflation, with a hawkish outlook for future tightening.",
                "usd_implication": "Bullish for USD due to higher yield attractiveness.",
                "bonds_implication": "Bearish for US bonds as yields rise.",
                "trade_recommendation": {"action": "BUY", "symbol": "USDJPY", "confidence": 0.9},
                "confidence": 0.9
            })
            await broker.publish_message("economic_reports", mock_fomc_decision_report.model_dump())
        await asyncio.sleep(1)

        # Simulate a news insight about a dovish comment from a Fed official
        mock_dovish_news_insight = AgentMessage(
            sender_id="Priv-NewsAnalyzer",
            message_type=MessageType.STATUS_UPDATE,
            payload={
                "original_news_id": "news_fomc_2",
                "source": "Bloomberg",
                "headline": "Fed Governor hints at slower pace of rate hikes.",
                "content": "A prominent Federal Reserve Governor suggested that the central bank might adopt a more cautious approach to future interest rate increases, citing global economic headwinds.",
                "category": "economic",
                "sentiment": "positive", # Positive for markets, dovish for Fed
                "timestamp_processed": datetime.now().isoformat(),
                "market_impact_assessment": "high_monetary_policy_impact",
                "confidence_score": 0.8,
                "symbols_mentioned": ["USD", "USDBONDS"]
            }
        )
        # Patch the LLM response for FOMC news impact analysis
        with patch('backend.fundamental_analysis.news_sentiment_analyzer.OpenAI.chat.completions.create') as mock_llm_create:
            mock_llm_create.return_value = MagicMock()
            mock_llm_create.return_value.choices[0].message.content = json.dumps({
                "stance": "dovish",
                "summary": "Comments from a Fed Governor suggest a potential slowdown in rate hikes, indicating a dovish shift in monetary policy outlook.",
                "usd_implication": "Bearish for USD as rate hike expectations soften.",
                "bonds_implication": "Bullish for US bonds as yields may stabilize or fall.",
                "trade_recommendation": {"action": "SELL", "symbol": "USDJPY", "confidence": 0.85},
                "confidence": 0.85
            })
            await broker.publish_message("news_insights", mock_dovish_news_insight.model_dump())
        await asyncio.sleep(1)

        # Allow time for periodic checks and processing
        await asyncio.sleep(15)

    await fomc_agent.stop()
    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivFomcAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_fomc_agent_test())
