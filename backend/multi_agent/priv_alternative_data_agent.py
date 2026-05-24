# backend/multi_agent/priv_alternative_data_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import re

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeProposal, TradeAction, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual data sourcing clients
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer # Reusing for LLM capabilities
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.data_sourcing.iot_sensory_ingestor import SensoryDataIngestor # For direct IoT data simulation/ingestion
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor # For general market data context

# Import settings for configurable thresholds and API keys
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivAlternativeDataAgent(PrivAgent):
    """
    A specialized Priv Agent focused on sourcing, processing, and analyzing
    alternative data sets (e.g., satellite imagery, social media trends,
    web traffic, supply chain data, IoT sensor data) to generate unique market insights.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ALTERNATIVE_DATA, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.alternative_data_insights: Dict[str, Dict[str, Any]] = {} # Stores insights by data type/symbol

        # Initialize real data sourcing and analysis clients
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.llm_client = NewsSentimentAnalyzer( # Reusing NewsSentimentAnalyzer's LLM client for general analysis
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini" # Using a more capable model for complex alternative data analysis
        )
        self.global_news_ingestor = GlobalNewsIngestor()
        self.market_data_ingestor = MarketDataIngestor(self.broker)
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for raw data items to avoid re-processing
        self._processed_raw_data_ids = set()
        logger.info(f"Priv Alternative Data Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the alternative data agent, subscribing to raw alternative data feeds."""
        if self.is_running:
            logger.warning(f"Alternative Data Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to various raw alternative data feeds
        # These topics would be published by dedicated ingestors (e.g., your IoT Sensory Ingestor)
        await self.broker.subscribe_to_topic(
            "raw_satellite_imagery_data", self._handle_satellite_imagery, f"{self.agent_id}-satellite-sub"
        )
        await self.broker.subscribe_to_topic(
            "raw_web_traffic_data", self._handle_web_traffic_data, f"{self.agent_id}-web-traffic-sub"
        )
        await self.broker.subscribe_to_topic(
            "raw_supply_chain_data", self._handle_supply_chain_data, f"{self.agent_id}-supply-chain-sub"
        )
        await self.broker.subscribe_to_topic(
            "iot_sensory_data", self._handle_iot_sensory_data, f"{self.agent_id}-iot-sub"
        )
        await self.broker.subscribe_to_topic(
            "alternative_data_requests", self._handle_alternative_data_request, f"{self.agent_id}-requests-sub"
        )

        self.is_running = True
        # Start periodic tasks to fetch certain alternative data directly if this agent is also a source
        self._periodic_alt_data_fetch_task = asyncio.create_task(self._periodic_alt_data_fetch())
        logger.info(f"Priv Alternative Data Agent '{self.agent_id}' started and subscribed to alternative data feeds.")

    async def stop(self):
        """Stops the alternative data agent."""
        if not self.is_running:
            logger.warning(f"Alternative Data Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_alt_data_fetch_task:
            self._periodic_alt_data_fetch_task.cancel()
            try:
                await self._periodic_alt_data_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv Alternative Data Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv Alternative Data Agent '{self.agent_id}' stopped.")

    async def _periodic_alt_data_fetch(self):
        """
        Periodically fetches certain types of alternative data directly (e.g., from web scraping, specific APIs)
        that are not covered by other ingestors, and processes them.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Alternative Data Agent '{self.agent_id}': Initiating periodic alternative data fetch.")
                
                # Example: Fetching general web traffic trends for major e-commerce sites
                # This would require a dedicated web traffic API client (e.g., SimilarWeb, Alexa)
                # For now, simulate this by fetching news about e-commerce or specific companies
                ecom_news = self.news_api_client.fetch_news(query="e-commerce OR online retail", limit=settings.ALT_DATA_NEWS_LIMIT)
                for news_item in ecom_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_raw_data_ids:
                        continue
                    # Simulate converting news into a "web_traffic_data" format
                    mock_web_traffic_data = {
                        "website": "conceptual_ecom_site",
                        "metric": "news_sentiment_proxy",
                        "value": 1 if news_item.get('sentiment') == 'positive' else (-1 if news_item.get('sentiment') == 'negative' else 0),
                        "target_company": news_item.get('symbols', ['GENERAL_ECOM'])[0],
                        "timestamp": news_item.get('published_at', datetime.now().isoformat()),
                        "source_news_headline": news_item.get('headline')
                    }
                    await self._handle_web_traffic_data(AgentMessage(sender_id=self.agent_id, message_type=MessageType.STATUS_UPDATE, payload=mock_web_traffic_data).model_dump())
                    self._processed_raw_data_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv Alternative Data Agent '{self.agent_id}': Error during periodic alt data fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.ALT_DATA_FETCH_INTERVAL_SECONDS) # Configurable interval


    async def _handle_satellite_imagery(self, message_payload: Dict[str, Any]):
        """
        Processes raw satellite imagery data (e.g., parking lot counts, crop health)
        to derive insights for specific companies or commodities.
        This data would be published by an external ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            imagery_data = agent_message.payload

            location = imagery_data.get("location")
            metric = imagery_data.get("metric") # e.g., "parking_lot_occupancy", "crop_health_index"
            value = imagery_data.get("value")
            target_entity = imagery_data.get("target_entity") # e.g., "Walmart", "Corn Futures"
            original_timestamp = imagery_data.get("timestamp")

            if target_entity and metric and value is not None:
                insight_id = f"satellite_{target_entity}_{metric}_{original_timestamp}"
                if insight_id in self._processed_raw_data_ids:
                    logger.debug(f"Alt Data Agent: Skipping already processed satellite data: {insight_id}")
                    return

                # Use LLM to analyze the imagery data for deeper insights
                llm_prompt = (
                    f"Analyze the following satellite imagery data point: "
                    f"Target Entity: {target_entity}, Metric: {metric}, Value: {value}. "
                    f"Provide a concise market insight and a potential trade action (BUY/SELL/HOLD) with a confidence score [0-1]. "
                    "Example: 'High parking lot occupancy suggests strong sales, BUY AAPL, Confidence: 0.8'."
                )
                llm_analysis = await self._synthesize_llm_insight(llm_prompt)

                insight_data = {
                    "data_type": "satellite_imagery",
                    "target_entity": target_entity,
                    "metric": metric,
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "source_data": imagery_data,
                    "llm_summary": llm_analysis.get("summary"),
                    "llm_trade_recommendation": llm_analysis.get("trade_recommendation"),
                    "llm_confidence": llm_analysis.get("confidence")
                }
                self.alternative_data_insights[insight_id] = insight_data
                logger.debug(f"Alt Data Agent: Processed satellite imagery for {target_entity}: {metric}={value}.")

                await self._generate_and_publish_insight(insight_id, insight_data)
                self._processed_raw_data_ids.add(insight_id)

        except Exception as e:
            logger.error(f"Alt Data Agent '{self.agent_id}': Error handling satellite imagery data: {e}", exc_info=True)

    async def _handle_web_traffic_data(self, message_payload: Dict[str, Any]):
        """
        Processes raw web traffic data (e.g., website visits, app downloads)
        to infer consumer interest or company performance.
        This data would be published by an external ingestor or this agent's periodic fetch.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            web_traffic_data = agent_message.payload

            website = web_traffic_data.get("website")
            traffic_metric = web_traffic_data.get("metric") # e.g., "unique_visitors", "page_views"
            value = web_traffic_data.get("value")
            target_company = web_traffic_data.get("target_company") # e.g., "Amazon", "Netflix"
            original_timestamp = web_traffic_data.get("timestamp")

            if target_company and traffic_metric and value is not None:
                insight_id = f"web_traffic_{target_company}_{traffic_metric}_{original_timestamp}"
                if insight_id in self._processed_raw_data_ids:
                    logger.debug(f"Alt Data Agent: Skipping already processed web traffic data: {insight_id}")
                    return

                llm_prompt = (
                    f"Analyze the following web traffic data point: "
                    f"Target Company: {target_company}, Metric: {traffic_metric}, Value: {value}. "
                    f"Provide a concise market insight and a potential trade action (BUY/SELL/HOLD) with a confidence score [0-1]. "
                    "Example: 'Increased unique visitors suggest growing consumer interest, BUY NFLX, Confidence: 0.85'."
                )
                llm_analysis = await self._synthesize_llm_insight(llm_prompt)

                insight_data = {
                    "data_type": "web_traffic",
                    "target_company": target_company,
                    "metric": traffic_metric,
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "source_data": web_traffic_data,
                    "llm_summary": llm_analysis.get("summary"),
                    "llm_trade_recommendation": llm_analysis.get("trade_recommendation"),
                    "llm_confidence": llm_analysis.get("confidence")
                }
                self.alternative_data_insights[insight_id] = insight_data
                logger.debug(f"Alt Data Agent: Processed web traffic for {target_company}: {traffic_metric}={value}.")

                await self._generate_and_publish_insight(insight_id, insight_data)
                self._processed_raw_data_ids.add(insight_id)

        except Exception as e:
            logger.error(f"Alt Data Agent '{self.agent_id}': Error handling web traffic data: {e}", exc_info=True)

    async def _handle_supply_chain_data(self, message_payload: Dict[str, Any]):
        """
        Processes raw supply chain data (e.g., shipping manifests, factory output)
        to predict revenue or production issues for companies.
        This data would be published by an external ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            supply_chain_data = agent_message.payload

            company = supply_chain_data.get("company")
            supply_metric = supply_chain_data.get("metric") # e.g., "shipment_volume", "factory_utilization"
            value = supply_chain_data.get("value")
            original_timestamp = supply_chain_data.get("timestamp")

            if company and supply_metric and value is not None:
                insight_id = f"supply_chain_{company}_{supply_metric}_{original_timestamp}"
                if insight_id in self._processed_raw_data_ids:
                    logger.debug(f"Alt Data Agent: Skipping already processed supply chain data: {insight_id}")
                    return

                llm_prompt = (
                    f"Analyze the following supply chain data point: "
                    f"Target Company: {company}, Metric: {supply_metric}, Value: {value}. "
                    f"Provide a concise market insight and a potential trade action (BUY/SELL/HOLD) with a confidence score [0-1]. "
                    "Example: 'Significant drop in shipment volume suggests production issues, SELL TSLA, Confidence: 0.7'."
                )
                llm_analysis = await self._synthesize_llm_insight(llm_prompt)

                insight_data = {
                    "data_type": "supply_chain",
                    "target_company": company,
                    "metric": supply_metric,
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "source_data": supply_chain_data,
                    "llm_summary": llm_analysis.get("summary"),
                    "llm_trade_recommendation": llm_analysis.get("trade_recommendation"),
                    "llm_confidence": llm_analysis.get("confidence")
                }
                self.alternative_data_insights[insight_id] = insight_data
                logger.debug(f"Alt Data Agent: Processed supply chain data for {company}: {supply_metric}={value}.")

                await self._generate_and_publish_insight(insight_id, insight_data)
                self._processed_raw_data_ids.add(insight_id)

        except Exception as e:
            logger.error(f"Alt Data Agent '{self.agent_id}': Error handling supply chain data: {e}", exc_info=True)

    async def _handle_iot_sensory_data(self, message_payload: Dict[str, Any]):
        """
        Processes incoming IoT sensory data (e.g., from `iot_sensory_ingestor.py`)
        to derive insights relevant to specific industries or companies (e.g., retail foot traffic).
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            sensory_data = agent_message.payload

            room_id = sensory_data.get("room_id")
            readings = sensory_data.get("readings", {})
            original_timestamp = sensory_data.get("timestamp_utc")

            # This part needs to map generic sensor data to financial insights.
            # Example: If 'room_id' corresponds to a retail store location,
            # and 'light_lux' or 'sound_decibel' can proxy for foot traffic.
            
            # For demonstration, let's assume 'main_office' can be linked to general economic activity.
            if readings.get("sound_decibel") is not None and room_id == "main_office":
                insight_id = f"iot_sound_{room_id}_{original_timestamp}"
                if insight_id in self._processed_raw_data_ids:
                    logger.debug(f"Alt Data Agent: Skipping already processed IoT data: {insight_id}")
                    return

                sound_level = readings["sound_decibel"]
                llm_prompt = (
                    f"Analyze the office sound level: {sound_level} decibels. "
                    f"Higher sound might indicate increased activity. "
                    f"Provide a concise market insight and a potential trade action (BUY/SELL/HOLD) with a confidence score [0-1]. "
                    "Example: 'High office sound levels suggest strong business activity, BUY SPY, Confidence: 0.6'."
                )
                llm_analysis = await self._synthesize_llm_insight(llm_prompt)

                insight_data = {
                    "data_type": "iot_sensory",
                    "target_area": room_id,
                    "metric": "sound_decibel",
                    "value": sound_level,
                    "timestamp": datetime.now().isoformat(),
                    "source_data": sensory_data,
                    "llm_summary": llm_analysis.get("summary"),
                    "llm_trade_recommendation": llm_analysis.get("trade_recommendation"),
                    "llm_confidence": llm_analysis.get("confidence")
                }
                self.alternative_data_insights[insight_id] = insight_data
                logger.debug(f"Alt Data Agent: Processed IoT sensory data for {room_id}: sound={sound_level}.")

                await self._generate_and_publish_insight(insight_id, insight_data)
                self._processed_raw_data_ids.add(insight_id)

        except Exception as e:
            logger.error(f"Alt Data Agent '{self.agent_id}': Error handling IoT sensory data: {e}", exc_info=True)


    async def _handle_alternative_data_request(self, message_payload: Dict[str, Any]):
        """
        Handles explicit requests from other agents for alternative data insights.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            request_details = agent_message.payload
            sender_id = agent_message.sender_id

            request_type = request_details.get("request_type") # e.g., "latest_web_traffic", "parking_lot_trend"
            target = request_details.get("target") # e.g., "Walmart", "TSLA"
            request_id = request_details.get("request_id", f"req_{datetime.now().timestamp()}")

            logger.info(f"Alt Data Agent: Received request from {sender_id} for {request_type} on {target}.")

            # Perform conceptual retrieval and synthesis of requested insight
            requested_insight = await self._get_conceptual_insight(request_type, target, request_id)

            response_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=sender_id,
                message_type=MessageType.STATUS_UPDATE, # Or new type like MessageType.ALT_DATA_INSIGHT_RESPONSE
                payload={"request_id": request_id, "insight": requested_insight}
            )
            await self.broker.publish_message("alternative_data_insights_responses", response_message.model_dump())
            logger.info(f"Alt Data Agent: Published requested insight for {target} to {sender_id}.")

        except Exception as e:
            logger.error(f"Alt Data Agent '{self.agent_id}': Error handling alternative data request: {e}", exc_info=True)

    async def _synthesize_llm_insight(self, prompt: str) -> Dict[str, Any]:
        """
        Uses the LLM to synthesize an insight and extract a trade recommendation and confidence.
        """
        try:
            llm_response = await asyncio.to_thread(self.llm_client.client.chat.completions.create,
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are an expert alternative data analyst. Provide concise market insights and actionable trade recommendations (BUY/SELL/HOLD) with a confidence score [0-1]."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.ALT_DATA_LLM_MAX_TOKENS,
                temperature=0.7
            )
            llm_text_response = llm_response.choices[0].message.content
            
            # Attempt to parse structured output from LLM
            trade_action_match = re.search(r"Trade Action:\s*(BUY|SELL|HOLD)", llm_text_response, re.IGNORECASE)
            confidence_match = re.search(r"Confidence:\s*([\d.]+)", llm_text_response)
            symbol_match = re.search(r"Symbol:\s*([A-Z0-9/]+)", llm_text_response)

            trade_rec = None
            confidence = 0.0
            if trade_action_match and symbol_match:
                action = TradeAction[trade_action_match.group(1).upper()]
                confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                symbol = symbol_match.group(1).upper()
                trade_rec = {
                    "action": action.value,
                    "symbol": symbol,
                    "confidence": confidence
                }

            return {
                "summary": llm_text_response,
                "trade_recommendation": trade_rec,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Alt Data Agent: LLM synthesis failed: {e}", exc_info=True)
            return {
                "summary": f"LLM analysis failed: {e}",
                "trade_recommendation": None,
                "confidence": 0.0
            }


    async def _generate_and_publish_insight(self, insight_id: str, insight_data: Dict[str, Any]):
        """
        Processes raw alternative data into actionable insights and publishes them.
        This now uses the LLM-generated summary and recommendation.
        """
        data_type = insight_data.get("data_type")
        target = insight_data.get("target_entity") or insight_data.get("target_company") or insight_data.get("target_area")
        metric = insight_data.get("metric")
        value = insight_data.get("value")
        
        llm_summary = insight_data.get("llm_summary", f"Alternative data insight ({data_type}) for {target}: {metric} is {value}.")
        llm_trade_rec = insight_data.get("llm_trade_recommendation")
        llm_confidence = insight_data.get("llm_confidence", 0.0)

        summary = llm_summary
        recommendation_text = "No immediate trade recommendation."
        
        if llm_trade_rec:
            recommendation_text = f"LLM recommends {llm_trade_rec['action']} {llm_trade_rec['symbol']} with confidence {llm_trade_rec['confidence']:.2f}."

        insight_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE, # Or new type like MessageType.ALT_DATA_INSIGHT
            payload={
                "insight_id": insight_id,
                "summary": summary,
                "recommendation_text": recommendation_text,
                "confidence": llm_confidence,
                "timestamp": datetime.now().isoformat(),
                "original_data_summary": {
                    "data_type": data_type,
                    "target": target,
                    "metric": metric,
                    "value": value
                },
                "llm_generated_trade_rec": llm_trade_rec # Include the structured trade rec
            }
        )
        await self.broker.publish_message("alternative_data_insights", insight_message.model_dump())
        logger.info(f"Alt Data Agent: Published insight '{insight_id}'.")

        # If the LLM generated a trade recommendation, publish it as a TradeProposal
        if llm_trade_rec and llm_trade_rec.get("action") in [TradeAction.BUY.value, TradeAction.SELL.value]:
            # Fetch latest price for the symbol to include in the proposal
            latest_price_info = await self.market_data_ingestor.get_latest_market_data(llm_trade_rec['symbol'])
            entry_price = latest_price_info.get("last_trade_price") if latest_price_info else None

            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=llm_trade_rec["symbol"],
                action=TradeAction[llm_trade_rec["action"]],
                volume=settings.ALT_DATA_TRADE_PROPOSAL_VOLUME, # Configurable default volume
                entry_price=entry_price,
                reasoning=f"Alternative data-driven recommendation: {llm_summary[:100]}...",
                confidence=llm_trade_rec.get("confidence", 0.5),
                risk_assessment={"data_source": "alternative", "data_type": data_type, "llm_confidence": llm_trade_rec.get("confidence")}
            )
            await self._publish_trade_proposal(proposal)

    async def _get_conceptual_insight(self, request_type: str, target: str, request_id: str) -> Dict[str, Any]:
        """
        Conceptual function to retrieve a specific insight from cache or generate on demand.
        For a real system, this would involve querying a feature store or re-running analysis.
        """
        # Try to find a matching insight in the internal cache
        for insight_id, insight in self.alternative_data_insights.items():
            if target in (insight.get("target_entity", "") or insight.get("target_company", "") or insight.get("target_area", "")) and \
               request_type in insight.get("data_type", ""):
                logger.info(f"Alt Data Agent: Found cached insight for request '{request_id}'.")
                return insight
        
        # If not found in cache, generate a new one conceptually (or trigger a new data fetch/analysis)
        logger.info(f"Alt Data Agent: No cached insight found for request '{request_id}'. Generating new conceptual insight.")
        
        # Simulate fetching some raw data based on request_type and target
        mock_raw_data = {"type": request_type, "target": target, "value": random.uniform(0.1, 0.9)}
        llm_prompt = (
            f"Generate a market insight for '{target}' based on conceptual '{request_type}' data with value {mock_raw_data['value']}. "
            "Provide a concise summary and a potential trade action (BUY/SELL/HOLD) with a confidence score [0-1]."
        )
        llm_analysis = await self._synthesize_llm_insight(llm_prompt)

        return {
            "insight_id": f"conceptual_{request_type}_{target}_{datetime.now().timestamp()}",
            "summary": llm_analysis.get("summary", f"No specific recent alternative data insight found for '{target}' regarding '{request_type}'."),
            "recommendation_text": f"LLM recommends: {llm_analysis.get('trade_recommendation', {}).get('action', 'HOLD')}" if llm_analysis.get('trade_recommendation') else "No specific trade recommendation.",
            "confidence": llm_analysis.get("confidence", 0.3),
            "timestamp": datetime.now().isoformat(),
            "llm_generated_trade_rec": llm_analysis.get("trade_recommendation")
        }


    async def _publish_trade_proposal(self, proposal: TradeProposal):
        """Helper to publish a trade proposal generated by the alternative data agent."""
        proposal_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.TRADE_PROPOSAL,
            payload=proposal.model_dump()
        )
        await self.broker.publish_message("trade_proposals", proposal_message.model_dump())
        logger.info(f"Alt Data Agent: Published trade proposal: {proposal.action} {proposal.symbol} (Confidence: {proposal.confidence:.2f}).")


# Example Usage (for testing PrivAlternativeDataAgent in isolation)
async def main_alternative_data_agent_test():
    logging.basicConfig(level=logging.INFO)
    import re # Ensure re is imported for the test block
    import random # For simulating data
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

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
    if not hasattr(settings, 'POLYGON_API_KEY'):
        settings.POLYGON_API_KEY = "dummy_polygon_key" # Needed for FinancialAutomationSourcingClient init
    if not hasattr(settings, 'ALT_DATA_NEWS_LIMIT'):
        settings.ALT_DATA_NEWS_LIMIT = 5
    if not hasattr(settings, 'ALT_DATA_FETCH_INTERVAL_SECONDS'):
        settings.ALT_DATA_FETCH_INTERVAL_SECONDS = 10
    if not hasattr(settings, 'ALT_DATA_LLM_MAX_TOKENS'):
        settings.ALT_DATA_LLM_MAX_TOKENS = 300
    if not hasattr(settings, 'ALT_DATA_TRADE_PROPOSAL_VOLUME'):
        settings.ALT_DATA_TRADE_PROPOSAL_VOLUME = 0.01 # Small volume for alt data
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    alt_data_agent = PrivAlternativeDataAgent(
        agent_id="Priv-AltDataAnalyst",
        broker=broker,
        persona={"name": "Alternative Data Specialist", "focus": "Unconventional Market Signals"}
    )
    # Instantiate a simulated IoT ingestor to publish data for the AltDataAgent to consume
    simulated_iot_ingestor = SensoryDataIngestor(broker=broker, room_id="retail_store_A")


    await broker.connect()
    await alt_data_agent.start()
    simulated_iot_ingestor.start(interval_seconds=5) # Start IoT ingestor


    logger.info("\n--- Simulating raw alternative data feeds for Alt Data Agent to consume ---")

    # Simulate satellite imagery data (parking lot occupancy for Walmart)
    mock_satellite_data = AgentMessage(
        sender_id="SatelliteDataFeed",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "location": "Bentonville, AR",
            "metric": "parking_lot_occupancy",
            "value": 0.95, # High occupancy
            "target_entity": "WMT", # Walmart stock symbol
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("raw_satellite_imagery_data", mock_satellite_data.model_dump())
    await asyncio.sleep(1)

    # Simulate web traffic data (unique visitors for Netflix)
    mock_web_traffic_data = AgentMessage(
        sender_id="WebAnalyticsFeed",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "website": "netflix.com",
            "metric": "unique_visitors",
            "value": 1500000, # High visitors
            "target_company": "NFLX", # Netflix stock symbol
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("raw_web_traffic_data", mock_web_traffic_data.model_dump())
    await asyncio.sleep(1)

    # Simulate supply chain data (shipment volume for Tesla)
    mock_supply_chain_data = AgentMessage(
        sender_id="LogisticsDataFeed",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "company": "TSLA",
            "metric": "shipment_volume",
            "value": 0.4, # Significant drop (e.g., 40% of normal)
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("raw_supply_chain_data", mock_supply_chain_data.model_dump())
    await asyncio.sleep(1)

    # IoT sensory data is published by simulated_iot_ingestor.start()

    # Simulate a request for alternative data insight
    mock_alt_data_request = AgentMessage(
        sender_id="Priv-Strategist",
        message_type=MessageType.ARBITRATION_REQUEST,
        payload={
            "request_id": "alt_data_req_001",
            "request_type": "web_traffic",
            "target": "NFLX",
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("alternative_data_requests", mock_alt_data_request.model_dump())
    await asyncio.sleep(1)


    await asyncio.sleep(20) # Give time for agents to process messages and for periodic fetches

    await alt_data_agent.stop()
    simulated_iot_ingestor.stop()
    await broker.disconnect()
    logger.info("\nPrivAlternativeDataAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_alternative_data_agent_test())
