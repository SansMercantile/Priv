# backend/multi_agent/priv_research_agent.py

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
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sourcing.tradingview_retriever import TradingViewRetriever
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from backend.data_sourcing.financial_automation_sourcing import FinancialAutomationSourcingClient
from backend.fundamental_analysis.economic_calendar.manager import EconomicCalendarManager
from backend.data_sourcing.data_loader import get_market_data # For historical OHLCV data

# Import LLM for research synthesis
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer # Reusing for general LLM capabilities

# Import settings for API keys and configurable thresholds
from backend.config import settings

logger = logging.getLogger(__name__)

class PrivResearchAgent(PrivAgent):
    """
    A specialized Priv Agent focused on conducting in-depth research on financial assets,
    market trends, economic indicators, and emerging technologies. It generates
    comprehensive research reports and insights for other agents.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.RESEARCH, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.research_queue: asyncio.Queue = asyncio.Queue() # Queue for research requests
        self.active_research_tasks: Dict[str, asyncio.Task] = {} # Track ongoing research

        # Initialize real data sourcing clients
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.tradingview_retriever = TradingViewRetriever()
        self.global_news_ingestor = GlobalNewsIngestor()
        self.fundamental_data_ingestor = FundamentalDataIngestor() # This handles SimFin and EODHD
        self.financial_automation_sourcing_client = FinancialAutomationSourcingClient(
            api_key=settings.POLYGON_API_KEY 
        )
        self.economic_calendar_manager = EconomicCalendarManager(
            calendar_url=settings.ECONOMIC_CALENDAR_URL
        )
        self.llm_client = NewsSentimentAnalyzer( # Reusing NewsSentimentAnalyzer's LLM client
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini" # Using a more capable model for research synthesis
        )

        # Internal cache for fetched data to avoid redundant API calls during a research task
        self._data_cache: Dict[str, Any] = {}
        logger.info(f"Priv Research Agent '{self.agent_id}' initialized with real data clients.")

    async def start(self):
        """Starts the research agent, subscribing to research requests and market data."""
        if self.is_running:
            logger.warning(f"Research Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to general market data (for context) and explicit research requests
        await self.broker.subscribe_to_topic(
            "real_time_market_data", self._handle_market_data_for_context, f"{self.agent_id}-market-sub"
        )
        await self.broker.subscribe_to_topic(
            "research_requests", self._handle_research_request, f"{self.agent_id}-requests-sub"
        )

        self.is_running = True
        # Start a background task to process the research queue
        self._research_processor_task = asyncio.create_task(self._process_research_queue())
        logger.info(f"Priv Research Agent '{self.agent_id}' started and research processor initiated.")

    async def stop(self):
        """Stops the research agent and cancels ongoing research tasks."""
        if not self.is_running:
            logger.warning(f"Research Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._research_processor_task:
            self._research_processor_task.cancel()
            try:
                await self._research_processor_task
            except asyncio.CancelledError:
                logger.info("Research Agent: Research queue processor cancelled.")

        for task in self.active_research_tasks.values():
            task.cancel()
        # Wait for all active research tasks to finish or be cancelled
        if self.active_research_tasks:
            await asyncio.gather(*self.active_research_tasks.values(), return_exceptions=True)

        logger.info(f"Priv Research Agent '{self.agent_id}' stopped.")

    async def _handle_market_data_for_context(self, message_payload: Dict[str, Any]):
        """
        Processes incoming market data, primarily for contextual awareness
        during research, not for direct trading signals.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload
            symbol = market_data_item.get("symbol")
            price = market_data_item.get("last_trade_price")
            
            if symbol and price is not None:
                # Store latest market data in a simple cache for quick lookup during research
                self._data_cache[f"latest_price_{symbol}"] = {"price": price, "timestamp": datetime.now().isoformat()}
                logger.debug(f"Research Agent: Received market data for {symbol}: {price} (for context).")
        except Exception as e:
            logger.error(f"Research Agent '{self.agent_id}': Error handling market data for context: {e}", exc_info=True)

    async def _handle_research_request(self, message_payload: Dict[str, Any]):
        """
        Receives and queues requests for research from other agents.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            request_details = agent_message.payload
            request_id = request_details.get("request_id", f"req_{datetime.now().timestamp()}")
            request_details["_sender_id"] = agent_message.sender_id # Store sender for reply

            logger.info(f"Research Agent: Received research request '{request_id}' from {agent_message.sender_id} for topic: {request_details.get('topic')}.")
            await self.research_queue.put((request_id, request_details))

        except Exception as e:
            logger.error(f"Research Agent '{self.agent_id}': Error handling research request: {e}", exc_info=True)

    async def _process_research_queue(self):
        """Background task to continuously process research requests from the queue."""
        while self.is_running:
            try:
                request_id, request_details = await self.research_queue.get()
                logger.info(f"Research Agent: Starting research for request '{request_id}' on topic: {request_details.get('topic')}.")
                
                # Create a task for each research request to allow parallel processing
                research_task = asyncio.create_task(self._conduct_research(request_id, request_details))
                self.active_research_tasks[request_id] = research_task
                
                # Mark the task as done in the queue
                self.research_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Research Agent: Research queue processor cancelled.")
                break
            except Exception as e:
                logger.error(f"Research Agent '{self.agent_id}': Error processing research queue: {e}", exc_info=True)
            await asyncio.sleep(0.1) # Prevent busy-waiting

    async def _conduct_research(self, request_id: str, request_details: Dict[str, Any]):
        """
        Performs the actual research based on the request details, leveraging real data sources.
        """
        topic = request_details.get("topic", "general market trends")
        depth = request_details.get("depth", "medium")
        target_symbols = request_details.get("symbols", [])
        
        logger.info(f"Research Agent: Conducting {depth} research on '{topic}' for symbols: {target_symbols}.")

        # --- Data Collection Phase ---
        collected_data = {}
        
        # 1. Fetch News Articles relevant to the topic/symbols
        try:
            news_articles = self.news_api_client.fetch_news(query=topic, symbols=target_symbols, limit=settings.RESEARCH_NEWS_LIMIT)
            collected_data['news_articles'] = news_articles
            logger.info(f"Research Agent: Fetched {len(news_articles)} news articles.")
        except Exception as e:
            logger.warning(f"Research Agent: Failed to fetch news articles: {e}")

        # 2. Fetch TradingView Ideas
        tradingview_ideas = []
        for symbol in target_symbols:
            try:
                ideas = self.tradingview_retriever.fetch_ideas(symbol, limit=settings.RESEARCH_TRADINGVIEW_LIMIT)
                tradingview_ideas.extend(ideas)
            except Exception as e:
                logger.warning(f"Research Agent: Failed to fetch TradingView ideas for {symbol}: {e}")
        collected_data['tradingview_ideas'] = tradingview_ideas
        logger.info(f"Research Agent: Fetched {len(tradingview_ideas)} TradingView ideas.")

        # 3. Fetch Economic Events
        try:
            # Fetch events for a relevant period (e.g., last 30 days and next 7 days)
            econ_events = self.economic_calendar_manager.get_events(
                start_time=datetime.now() - timedelta(days=30),
                end_time=datetime.now() + timedelta(days=7),
                refresh_if_stale=True # Ensure fresh data
            )
            collected_data['economic_events'] = [e.model_dump() for e in econ_events]
            logger.info(f"Research Agent: Fetched {len(econ_events)} economic events.")
        except Exception as e:
            logger.warning(f"Research Agent: Failed to fetch economic events: {e}")

        # 4. Fetch Fundamental Data (for target companies/symbols)
        fundamental_data = []
        for symbol in target_symbols:
            try:
                # Use FundamentalDataIngestor's clients directly or via a wrapper
                # For simplicity, directly call get_fundamentals or similar
                # Assuming FundamentalDataIngestor has a method to get data for a single ticker
                # This might need a refactor in FundamentalDataIngestor to expose single-ticker fetch
                # For now, simulate direct call to EODHD or SimFin via ingestor's clients
                if self.fundamental_data_ingestor.eodhd_client:
                    data = await self.fundamental_data_ingestor.eodhd_client.get_fundamentals(symbol)
                    if data:
                        fundamental_data.append({"symbol": symbol, "source": "EODHD", "data": data})
                elif self.fundamental_data_ingestor.simfin_client:
                    data = await self.fundamental_data_ingestor.simfin_client.get_company_info(symbol)
                    if data:
                        fundamental_data.append({"symbol": symbol, "source": "SimFin", "data": data})
            except Exception as e:
                logger.warning(f"Research Agent: Failed to fetch fundamental data for {symbol}: {e}")
        collected_data['fundamental_data'] = fundamental_data
        logger.info(f"Research Agent: Fetched {len(fundamental_data)} fundamental data sets.")

        # 5. Fetch Historical Market Data (for deeper analysis if needed)
        historical_ohlcv = {}
        for symbol in target_symbols:
            try:
                # Fetch daily data for a longer period
                df = await get_market_data(symbol=symbol, timeframe="daily", num_bars=settings.RESEARCH_OHLCV_BARS)
                if df is not None and not df.empty:
                    historical_ohlcv[symbol] = df.to_dict('records') # Convert DataFrame to list of dicts
            except Exception as e:
                logger.warning(f"Research Agent: Failed to fetch historical OHLCV for {symbol}: {e}")
        collected_data['historical_ohlcv'] = historical_ohlcv
        logger.info(f"Research Agent: Fetched historical OHLCV for {len(historical_ohlcv)} symbols.")


        # --- Synthesis Phase using LLM ---
        # Combine all collected data into a coherent prompt for the LLM
        prompt_parts = [
            f"Conduct comprehensive financial research on the following topic: '{topic}'.",
            f"Focus on the following symbols/entities: {', '.join(target_symbols) if target_symbols else 'general market'}.",
            "\n--- Collected Data ---"
        ]
        if collected_data.get('news_articles'):
            prompt_parts.append("\nNews Articles (Headlines & Snippets):")
            for article in collected_data['news_articles'][:settings.RESEARCH_LLM_NEWS_LIMIT]:
                prompt_parts.append(f"- {article.get('title', 'N/A')}: {article.get('content', '')[:100]}...")
        if collected_data.get('tradingview_ideas'):
            prompt_parts.append("\nTradingView Ideas (Titles & Summaries):")
            for idea in collected_data['tradingview_ideas'][:settings.RESEARCH_LLM_TRADINGVIEW_LIMIT]:
                prompt_parts.append(f"- {idea.get('title', 'N/A')}: {idea.get('summary', '')[:100]}...")
        if collected_data.get('economic_events'):
            prompt_parts.append("\nRecent Economic Events (High/Medium Impact):")
            for event in collected_data['economic_events']:
                prompt_parts.append(f"- [{event.get('timestamp')[:10]}] {event.get('currency')} {event.get('event_name')} (Actual: {event.get('actual')}, Forecast: {event.get('forecast')}, Impact: {event.get('impact')})")
        if collected_data.get('fundamental_data'):
            prompt_parts.append("\nFundamental Data (Company Info/Financials Snippets):")
            for fd in collected_data['fundamental_data']:
                prompt_parts.append(f"- {fd.get('symbol')}: Source: {fd.get('source')}, Info: {str(fd.get('data', {}))[:150]}...")
        if collected_data.get('historical_ohlcv'):
            prompt_parts.append("\nHistorical OHLCV Data (Latest Bars):")
            for sym, ohlcv_data in collected_data['historical_ohlcv'].items():
                if ohlcv_data:
                    latest_bar = ohlcv_data[-1]
                    prompt_parts.append(f"- {sym} Latest Close: {latest_bar.get('close')}, Volume: {latest_bar.get('volume')}")


        prompt_parts.append("\nBased on the above data, provide a concise summary of key insights and actionable recommendations. Include potential trade actions (BUY/SELL/HOLD) if applicable, with a confidence score [0-1].")
        
        full_prompt = "\n".join(prompt_parts)
        
        research_output = {}
        try:
            # Use the LLM to synthesize findings and recommendations
            llm_response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are an expert financial researcher. Synthesize provided data into key insights and actionable recommendations, including potential trade actions and confidence scores."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=settings.RESEARCH_LLM_MAX_TOKENS,
                temperature=0.7
            )
            llm_text_response = llm_response.choices[0].message.content
            
            # Attempt to parse structured output from LLM if possible, or just use text
            # For a real system, you might guide the LLM to output JSON for easier parsing
            research_output = self._parse_llm_research_output(llm_text_response)
            
            logger.info(f"Research Agent: LLM synthesized research for '{topic}'.")

        except Exception as e:
            logger.error(f"Research Agent: Error during LLM synthesis: {e}", exc_info=True)
            research_output = {
                "summary": f"Failed to synthesize research due to LLM error: {e}",
                "key_insights": [],
                "recommendations": [],
                "trade_recommendation": None,
                "confidence": 0.0
            }

        # --- Final Research Report Construction ---
        research_findings = {
            "request_id": request_id,
            "topic": topic,
            "symbols": target_symbols,
            "summary": research_output.get("summary", "No summary generated."),
            "key_insights": research_output.get("key_insights", []),
            "recommendations": research_output.get("recommendations", []),
            "trade_recommendation": research_output.get("trade_recommendation"),
            "confidence": research_output.get("confidence", 0.0),
            "timestamp": datetime.now().isoformat(),
            "raw_collected_data_summary": {k: len(v) if isinstance(v, list) else "present" for k,v in collected_data.items()} # Summary of what was collected
        }

        logger.info(f"Research Agent: Research for '{request_id}' completed. Publishing findings.")
        await self._publish_research_findings(request_details["_sender_id"], research_findings)

        # Remove task from active list
        self.active_research_tasks.pop(request_id, None)

    def _parse_llm_research_output(self, llm_text: str) -> Dict[str, Any]:
        """
        Attempts to parse structured data from LLM's free-form text response.
        This is a heuristic and might need to be replaced with a JSON-constrained LLM output
        or more robust NLP parsing.
        """
        parsed = {
            "summary": llm_text[:500] + "..." if len(llm_text) > 500 else llm_text,
            "key_insights": [],
            "recommendations": [],
            "trade_recommendation": None,
            "confidence": 0.0
        }

        # Simple regex/keyword parsing for recommendations and confidence
        if "recommendation:" in llm_text.lower():
            rec_start = llm_text.lower().find("recommendation:") + len("recommendation:")
            recommendation_text = llm_text[rec_start:].split('\n')[0].strip()
            parsed["recommendations"].append(recommendation_text)

        if "trade action:" in llm_text.lower():
            trade_action_match = re.search(r"Trade Action:\s*(BUY|SELL|HOLD)", llm_text, re.IGNORECASE)
            confidence_match = re.search(r"Confidence:\s*([\d.]+)", llm_text)
            symbol_match = re.search(r"Symbol:\s*([A-Z0-9/]+)", llm_text)

            if trade_action_match and symbol_match:
                action = TradeAction[trade_action_match.group(1).upper()]
                confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                symbol = symbol_match.group(1).upper()
                
                parsed["trade_recommendation"] = {
                    "action": action.value,
                    "symbol": symbol,
                    "confidence": confidence
                }
                parsed["confidence"] = confidence # Overall confidence for the report

        if "key insights:" in llm_text.lower():
            insights_start = llm_text.lower().find("key insights:") + len("key insights:")
            insights_section = llm_text[insights_start:].split("Recommendations:")[0].strip()
            parsed["key_insights"] = [line.strip() for line in insights_section.split('\n') if line.strip()]

        return parsed


    async def _publish_research_findings(self, recipient_id: str, findings: Dict[str, Any]):
        """Publishes the completed research findings."""
        research_message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=recipient_id, # Direct reply to the requester
            message_type=MessageType.STATUS_UPDATE, # Or a new type like MessageType.RESEARCH_REPORT
            payload=findings
        )
        await self.broker.publish_message("research_reports", research_message.model_dump())
        logger.info(f"Research Agent: Published research report for request '{findings.get('request_id')}' to {recipient_id}.")

        # If the research generated a trade recommendation, publish it as a TradeProposal
        trade_rec = findings.get("trade_recommendation")
        if trade_rec and trade_rec.get("action") in [TradeAction.BUY.value, TradeAction.SELL.value]:
            # Fetch latest price for the symbol to include in the proposal
            latest_price_info = self._data_cache.get(f"latest_price_{trade_rec['symbol']}")
            entry_price = latest_price_info.get("price") if latest_price_info else None

            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=trade_rec["symbol"],
                action=TradeAction[trade_rec["action"]],
                volume=settings.RESEARCH_TRADE_PROPOSAL_VOLUME, # Configurable default volume
                entry_price=entry_price,
                reasoning=f"Research-driven recommendation: {findings.get('summary')[:100]}...",
                confidence=trade_rec.get("confidence", 0.5),
                risk_assessment={"research_driven": True, "llm_confidence": trade_rec.get("confidence")}
            )
            await self.broker.publish_message("trade_proposals", proposal.model_dump())
            logger.info(f"Research Agent: Published trade proposal based on research: {proposal.action} {proposal.symbol}.")


# Example Usage (for testing PrivResearchAgent in isolation)
async def main_research_agent_test():
    logging.basicConfig(level=logging.INFO)
    import re # Import regex for test
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
        settings.POLYGON_API_KEY = "dummy_polygon_key"
    if not hasattr(settings, 'ECONOMIC_CALENDAR_URL'):
        settings.ECONOMIC_CALENDAR_URL = "https://www.dailyfx.com/economic-calendar" # Placeholder
    if not hasattr(settings, 'RESEARCH_NEWS_LIMIT'):
        settings.RESEARCH_NEWS_LIMIT = 5
    if not hasattr(settings, 'RESEARCH_TRADINGVIEW_LIMIT'):
        settings.RESEARCH_TRADINGVIEW_LIMIT = 3
    if not hasattr(settings, 'RESEARCH_OHLCV_BARS'):
        settings.RESEARCH_OHLCV_BARS = 10
    if not hasattr(settings, 'RESEARCH_LLM_NEWS_LIMIT'):
        settings.RESEARCH_LLM_NEWS_LIMIT = 3
    if not hasattr(settings, 'RESEARCH_LLM_TRADINGVIEW_LIMIT'):
        settings.RESEARCH_LLM_TRADINGVIEW_LIMIT = 2
    if not hasattr(settings, 'RESEARCH_LLM_MAX_TOKENS'):
        settings.RESEARCH_LLM_MAX_TOKENS = 500
    if not hasattr(settings, 'RESEARCH_TRADE_PROPOSAL_VOLUME'):
        settings.RESEARCH_TRADE_PROPOSAL_VOLUME = 0.05


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    research_agent = PrivResearchAgent(
        agent_id="Priv-Researcher",
        broker=broker,
        persona={"name": "Market Research Analyst", "focus": "Deep Dive Analysis"}
    )

    await broker.connect()
    await research_agent.start()

    logger.info("\n--- Simulating research requests for Research Agent to consume ---")

    # Simulate a research request from a Strategist Agent
    mock_research_request_1 = AgentMessage(
        sender_id="Priv-Strategist",
        message_type=MessageType.ARBITRATION_REQUEST, # Reusing for conceptual request
        payload={
            "request_id": "res_001",
            "topic": "Impact of global supply chain disruptions on tech sector.",
            "depth": "deep",
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("research_requests", mock_research_request_1.model_dump())
    await asyncio.sleep(0.5)

    # Simulate another research request from an Economic Agent
    mock_research_request_2 = AgentMessage(
        sender_id="Priv-Economic",
        message_type=MessageType.ARBITRATION_REQUEST,
        payload={
            "request_id": "res_002",
            "topic": "Future of central bank digital currencies (CBDCs).",
            "depth": "medium",
            "symbols": [], # No specific symbols
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("research_requests", mock_research_request_2.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a research request that might lead to a trade recommendation
    mock_research_request_3 = AgentMessage(
        sender_id="Priv-PortfolioManager",
        message_type=MessageType.ARBITRATION_REQUEST,
        payload={
            "request_id": "res_003",
            "topic": "Impact of inflation on USD strength.",
            "depth": "deep",
            "symbols": ["USD"], # Conceptual symbol for currency strength
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("research_requests", mock_research_request_3.model_dump())
    await asyncio.sleep(0.5)


    await asyncio.sleep(20) # Give ample time for research to complete (includes API calls and LLM)

    await research_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivResearchAgent test finished.")

if __name__ == '__main__':
    import re # Ensure re is imported for the test block
    asyncio.run(main_research_agent_test())
