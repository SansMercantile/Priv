# backend/multi_agent/priv_yield_optimizer_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import TradeProposal, TradeAction, AgentMessage, MessageType, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual data sourcing clients
from backend.data_sourcing.financial_automation_sourcing import FinancialAutomationSourcingClient
from backend.data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer # Reusing for LLM

# Import settings for configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivYieldOptimizerAgent(PrivAgent):
    """
    A specialized agent that analyzes low-risk yield opportunities, such as
    staking, lending, or holding dividend-paying assets.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.YIELD_OPTIMIZER, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker # Ensure broker is set from super().__init__
        self.is_running = False

        # Initialize data sourcing clients
        self.financial_automation_sourcing_client = FinancialAutomationSourcingClient(
            api_key=settings.POLYGON_API_KEY 
        )
        self.fundamental_data_ingestor = FundamentalDataIngestor() # For deeper company analysis
        self.news_api_client = NewsAPIClient(
            api_key_ai=settings.NEWS_API_KEY_AI,
            api_key_org=settings.NEWS_API_KEY_ORG,
            use_mock=False
        )
        self.llm_client = NewsSentimentAnalyzer( # Reusing for general LLM capabilities
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini" # Using a more capable model for financial analysis
        )
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for processed events/symbols
        self._processed_dividend_events = set()
        logger.info(f"PrivYieldOptimizerAgent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running: return
        self.is_running = True
        
        # Subscribe to topics related to DeFi protocols or dividend announcements
        await self.broker.subscribe_to_topic(
            "dividend_announcements", self._handle_dividend_news, f"{self.agent_id}-dividends-sub"
        )
        await self.broker.subscribe_to_topic(
            "fundamental_data_updates", self._handle_fundamental_data_update, f"{self.agent_id}-fundamental-sub"
        )
        await self.broker.subscribe_to_topic(
            "defi_opportunities", self._handle_defi_opportunity, f"{self.agent_id}-defi-sub" # Hypothetical DeFi topic
        )

        # Start a periodic task to actively check for dividend announcements or other yield data
        self._periodic_yield_check_task = asyncio.create_task(self._periodic_yield_opportunity_check())
        
        logger.info(f"PrivYieldOptimizerAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        if self._periodic_yield_check_task:
            self._periodic_yield_check_task.cancel()
            try:
                await self._periodic_yield_check_task
            except asyncio.CancelledError:
                logger.info(f"PrivYieldOptimizerAgent '{self.agent_id}' periodic yield check task cancelled.")

        logger.info(f"PrivYieldOptimizerAgent '{self.agent_id}' stopped.")

    async def _periodic_yield_opportunity_check(self):
        """
        Periodically checks for new dividend announcements or other yield opportunities
        by fetching data directly.
        """
        while self.is_running:
            try:
                logger.info(f"PrivYieldOptimizerAgent '{self.agent_id}': Initiating periodic yield opportunity check.")
                
                # Example: Check top N dividend-paying stocks or a watchlist
                # This list should ideally come from a configuration or a portfolio manager agent
                symbols_to_check = settings.YIELD_OPTIMIZER_SYMBOLS_TO_CHECK

                for symbol in symbols_to_check:
                    logger.debug(f"Yield Optimizer: Fetching dividends for {symbol} via FinancialAutomationSourcingClient.")
                    dividends = await self.financial_automation_sourcing_client.get_dividends(symbol)
                    
                    if dividends:
                        for dividend in dividends:
                            # Use a unique ID for each dividend event to prevent reprocessing
                            dividend_id = f"{symbol}-{dividend.get('exDate', '')}-{dividend.get('amount', '')}"
                            if dividend_id in self._processed_dividend_events:
                                logger.debug(f"Yield Optimizer: Skipping already processed dividend: {dividend_id}")
                                continue
                            
                            # Simulate a message payload as if it came from an ingestor
                            mock_dividend_message_payload = {
                                "payload": {
                                    "symbol": symbol,
                                    "amount": dividend.get('amount'),
                                    "ex_date": dividend.get('exDate'),
                                    "pay_date": dividend.get('payDate'),
                                    "record_date": dividend.get('recordDate'),
                                    "declared_date": dividend.get('declaredDate'),
                                    "currency": dividend.get('currency'),
                                    # Calculate yield conceptually, or fetch current price to calculate
                                    "yield": dividend.get('amount', 0) / (await self._get_current_price(symbol) or 1) # Requires current price
                                }
                            }
                            await self._handle_dividend_news(mock_dividend_message_payload)
                            self._processed_dividend_events.add(dividend_id)
                    await asyncio.sleep(settings.YIELD_OPTIMIZER_SYMBOL_DELAY_SECONDS) # Small delay between symbols

            except Exception as e:
                logger.error(f"PrivYieldOptimizerAgent '{self.agent_id}': Error during periodic yield check: {e}", exc_info=True)
            
            await asyncio.sleep(settings.YIELD_OPTIMIZER_CHECK_INTERVAL_SECONDS)

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Helper to get the current price of a symbol."""
        market_data = await self.market_data_ingestor.get_latest_market_data(symbol)
        return market_data.get("last_trade_price") if market_data else None


    async def _handle_dividend_news(self, message_payload: Dict[str, Any]):
        """Analyzes a dividend announcement and may generate a proposal."""
        news = message_payload.get('payload', {})
        symbol = news.get('symbol')
        dividend_yield = news.get('yield') # e.g., 0.05 for 5%
        dividend_amount = news.get('amount')
        ex_date = news.get('ex_date')

        if not symbol or not dividend_yield:
            logger.warning(f"Yield Optimizer: Incomplete dividend news received: {news}. Skipping.")
            return

        logger.info(f"Yield Optimizer: Detected dividend announcement for {symbol} with yield {dividend_yield:.2%}.")
        
        # Fetch fundamental data for deeper analysis
        fundamental_data = None
        if self.fundamental_data_ingestor.eodhd_client:
            fundamental_data = await self.fundamental_data_ingestor.eodhd_client.get_fundamentals(symbol)
        elif self.fundamental_data_ingestor.simfin_client:
            fundamental_data = await self.fundamental_data_ingestor.simfin_client.get_company_info(symbol)

        # Use LLM for a more sophisticated analysis of the dividend's attractiveness
        llm_prompt = (
            f"Analyze the dividend announcement for {symbol}: Yield {dividend_yield:.2%}, Amount {dividend_amount}, Ex-Date {ex_date}. "
            f"Consider recent company fundamentals (if available: {fundamental_data}). "
            "Is this an attractive yield opportunity for a long-term investor? "
            "Provide a concise assessment and a recommendation (BUY/HOLD/AVOID) with a confidence score [0-1]. "
            "Respond in JSON format with keys: 'assessment_summary', 'recommendation', 'confidence'."
        )

        llm_analysis_results = {}
        try:
            llm_response = await asyncio.to_thread(self.llm_client.client.chat.completions.create,
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are an expert yield optimizer. Analyze dividend opportunities."},
                    {"role": "user", "content": llm_prompt}
                ],
                max_tokens=settings.YIELD_OPTIMIZER_LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
                temperature=0.5
            )
            llm_analysis_results = json.loads(llm_response.choices[0].message.content)
            logger.info(f"Yield Optimizer: LLM analysis for {symbol} dividend: {llm_analysis_results.get('assessment_summary')}")
        except Exception as e:
            logger.error(f"Yield Optimizer: LLM analysis for {symbol} dividend failed: {e}", exc_info=True)
            llm_analysis_results = {"recommendation": "HOLD", "confidence": 0.5, "assessment_summary": "LLM analysis failed, relying on simple threshold."}


        # If the yield is attractive (based on LLM or simple threshold), generate a proposal to buy the asset
        llm_recommendation = llm_analysis_results.get("recommendation", "HOLD").upper()
        llm_confidence = llm_analysis_results.get("confidence", 0.5)

        if llm_recommendation == "BUY" and llm_confidence >= settings.YIELD_OPTIMIZER_LLM_CONFIDENCE_THRESHOLD:
            current_price = await self._get_current_price(symbol)
            if current_price is None:
                logger.warning(f"Yield Optimizer: Cannot generate proposal for {symbol}, no current price.")
                return

            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=TradeAction.BUY,
                volume=settings.YIELD_OPTIMIZER_TRADE_VOLUME, # Configurable volume
                entry_price=current_price,
                reasoning=f"High dividend yield of {dividend_yield:.2%} announced. LLM assessment: {llm_analysis_results.get('assessment_summary')}.",
                confidence=llm_confidence,
                risk_assessment={"strategy": "dividend_capture", "fundamental_health_checked": bool(fundamental_data)}
            )
            await self.broker.publish_message("trade_proposals", proposal.model_dump())
            logger.info(f"Yield Optimizer: Published BUY proposal for {symbol} based on dividend. Confidence: {llm_confidence:.2f}.")
            
            # Send WhatsApp alert for high-confidence opportunities
            if llm_confidence >= settings.YIELD_OPTIMIZER_ALERT_CONFIDENCE_THRESHOLD:
                await self._send_yield_opportunity_alert(symbol, dividend_yield, llm_analysis_results)

        elif dividend_yield > settings.YIELD_OPTIMIZER_SIMPLE_THRESHOLD and llm_recommendation == "HOLD": # Fallback if LLM is neutral but yield is high
             current_price = await self._get_current_price(symbol)
             if current_price:
                proposal = TradeProposal(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    action=TradeAction.BUY,
                    volume=settings.YIELD_OPTIMIZER_TRADE_VOLUME,
                    entry_price=current_price,
                    reasoning=f"High dividend yield of {dividend_yield:.2%} announced (simple threshold).",
                    confidence=0.7, # Lower confidence for simple threshold
                    risk_assessment={"strategy": "dividend_capture_simple"}
                )
                await self.broker.publish_message("trade_proposals", proposal.model_dump())
                logger.info(f"Yield Optimizer: Published BUY proposal for {symbol} based on simple dividend threshold. Confidence: 0.70.")


    async def _handle_fundamental_data_update(self, message_payload: Dict[str, Any]):
        """
        Processes incoming fundamental data updates to re-evaluate existing holdings
        or identify new yield opportunities.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            fundamental_data = agent_message.payload
            
            symbol = fundamental_data.get("symbol")
            company_info = fundamental_data.get("company_info")
            income_statement = fundamental_data.get("income_statement")
            balance_sheet = fundamental_data.get("balance_sheet")

            if symbol and (company_info or income_statement or balance_sheet):
                logger.info(f"Yield Optimizer: Received fundamental data update for {symbol}. Re-assessing yield potential.")
                
                # Re-fetch dividends to ensure latest yield calculation
                dividends = await self.financial_automation_sourcing_client.get_dividends(symbol)
                if dividends:
                    latest_dividend = dividends[0] if dividends else None
                    if latest_dividend:
                        current_price = await self._get_current_price(symbol)
                        if current_price:
                            calculated_yield = latest_dividend.get('amount', 0) / current_price
                            # Trigger dividend analysis with the new fundamental context
                            await self._handle_dividend_news({
                                "payload": {
                                    "symbol": symbol,
                                    "amount": latest_dividend.get('amount'),
                                    "ex_date": latest_dividend.get('exDate'),
                                    "yield": calculated_yield,
                                    "fundamental_context": fundamental_data # Pass full fundamental data
                                }
                            })

        except Exception as e:
            logger.error(f"Yield Optimizer: Error handling fundamental data update: {e}", exc_info=True)

    async def _handle_defi_opportunity(self, message_payload: Dict[str, Any]):
        """
        Processes incoming DeFi opportunity messages (e.g., high staking APY, new lending pools).
        This assumes another agent or ingestor publishes these.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            defi_opportunity = agent_message.payload

            platform = defi_opportunity.get("platform")
            asset = defi_opportunity.get("asset")
            apy = defi_opportunity.get("apy") # Annual Percentage Yield
            risk_level = defi_opportunity.get("risk_level", "medium")

            if asset and apy is not None:
                logger.info(f"Yield Optimizer: Detected DeFi opportunity on {platform} for {asset} with APY: {apy:.2%}.")
                
                # Use LLM to evaluate the DeFi opportunity
                llm_prompt = (
                    f"Evaluate the DeFi opportunity: Asset {asset}, Platform {platform}, APY {apy:.2%}, Risk Level {risk_level}. "
                    "Is this a good yield opportunity? Consider the risk. "
                    "Provide a concise assessment and a recommendation (INVEST/AVOID) with a confidence score [0-1]. "
                    "Respond in JSON format with keys: 'assessment_summary', 'recommendation', 'confidence'."
                )
                llm_analysis_results = {}
                try:
                    llm_response = await asyncio.to_thread(self.llm_client.client.chat.completions.create,
                        model=self.llm_client.model,
                        messages=[
                            {"role": "system", "content": "You are an expert DeFi yield optimizer. Analyze DeFi opportunities."},
                            {"role": "user", "content": llm_prompt}
                        ],
                        max_tokens=settings.YIELD_OPTIMIZER_LLM_MAX_TOKENS,
                        response_format={"type": "json_object"},
                        temperature=0.5
                    )
                    llm_analysis_results = json.loads(llm_response.choices[0].message.content)
                    logger.info(f"Yield Optimizer: LLM analysis for DeFi opportunity: {llm_analysis_results.get('assessment_summary')}")
                except Exception as e:
                    logger.error(f"Yield Optimizer: LLM analysis for DeFi opportunity failed: {e}", exc_info=True)
                    llm_analysis_results = {"recommendation": "HOLD", "confidence": 0.5, "assessment_summary": "LLM analysis failed."}

                llm_recommendation = llm_analysis_results.get("recommendation", "HOLD").upper()
                llm_confidence = llm_analysis_results.get("confidence", 0.5)

                if llm_recommendation == "INVEST" and llm_confidence >= settings.YIELD_OPTIMIZER_LLM_CONFIDENCE_THRESHOLD:
                    # Generate a conceptual "trade" proposal for DeFi investment (e.g., allocate capital)
                    proposal = TradeProposal(
                        agent_id=self.agent_id,
                        symbol=asset, # Asset to invest in (e.g., USDC, ETH)
                        action=TradeAction.BUY, # Conceptual "BUY" for investment
                        volume=settings.YIELD_OPTIMIZER_DEFI_VOLUME, # Configurable volume for DeFi
                        reasoning=f"High APY ({apy:.2%}) DeFi opportunity on {platform}. LLM assessment: {llm_analysis_results.get('assessment_summary')}.",
                        confidence=llm_confidence,
                        risk_assessment={"strategy": "defi_staking_lending", "platform_risk": risk_level}
                    )
                    await self.broker.publish_message("trade_proposals", proposal.model_dump())
                    logger.info(f"Yield Optimizer: Published INVEST proposal for DeFi asset {asset}. Confidence: {llm_confidence:.2f}.")

                    if llm_confidence >= settings.YIELD_OPTIMIZER_ALERT_CONFIDENCE_THRESHOLD:
                        await self._send_yield_opportunity_alert(asset, apy, llm_analysis_results, is_defi=True)

        except Exception as e:
            logger.error(f"Yield Optimizer: Error handling DeFi opportunity: {e}", exc_info=True)

    async def _send_yield_opportunity_alert(self, symbol: str, yield_pct: float, llm_analysis: Dict[str, Any], is_defi: bool = False):
        """Sends a WhatsApp alert for high-yield opportunities."""
        alert_type = "DeFi Yield Opportunity" if is_defi else "Dividend Opportunity"
        whatsapp_message = (
            f"💰 *NEW {alert_type.upper()}!* 💰\n"
            f"Asset: *{symbol.upper()}*\n"
            f"Yield: `{yield_pct:.2%}`\n"
            f"LLM Assessment: {llm_analysis.get('assessment_summary', 'N/A')}\n"
            f"Recommendation: *{llm_analysis.get('recommendation', 'N/A').upper()}* (Confidence: {llm_analysis.get('confidence', 0.0):.2f})\n"
            "Review for potential investment."
        )
        critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
        try:
            # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
            logger.info(f"Yield Optimizer: Conceptually sent WhatsApp alert for {alert_type} to {critical_alert_recipient}.")
        except Exception as e:
            logger.error(f"Yield Optimizer: Failed to send WhatsApp alert for yield opportunity: {e}", exc_info=True)


# Example Usage (for testing PrivYieldOptimizerAgent in isolation)
async def main_yield_optimizer_agent_test():
    logging.basicConfig(level=logging.INFO)
    import json # For LLM response parsing in test
    from unittest.mock import patch, MagicMock # Needed for test patching
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'POLYGON_API_KEY'):
        settings.POLYGON_API_KEY = "dummy_polygon_key"
    if not hasattr(settings, 'NEWS_API_KEY_AI'):
        settings.NEWS_API_KEY_AI = "dummy_news_ai_key"
    if not hasattr(settings, 'NEWS_API_KEY_ORG'):
        settings.NEWS_API_KEY_ORG = "dummy_news_org_key"
    if not hasattr(settings, 'OPENAI_API_KEY') or "YOUR_OPENAI_API_KEY" in settings.OPENAI_API_KEY:
        settings.OPENAI_API_KEY = "dummy_openai_key"
    if not hasattr(settings, 'YIELD_OPTIMIZER_SYMBOLS_TO_CHECK'):
        settings.YIELD_OPTIMIZER_SYMBOLS_TO_CHECK = ["AAPL", "MSFT", "GOOGL"]
    if not hasattr(settings, 'YIELD_OPTIMIZER_SYMBOL_DELAY_SECONDS'):
        settings.YIELD_OPTIMIZER_SYMBOL_DELAY_SECONDS = 0.5
    if not hasattr(settings, 'YIELD_OPTIMIZER_CHECK_INTERVAL_SECONDS'):
        settings.YIELD_OPTIMIZER_CHECK_INTERVAL_SECONDS = 10 # Frequent for test
    if not hasattr(settings, 'YIELD_OPTIMIZER_TRADE_VOLUME'):
        settings.YIELD_OPTIMIZER_TRADE_VOLUME = 10 # Shares
    if not hasattr(settings, 'YIELD_OPTIMIZER_DEFI_VOLUME'):
        settings.YIELD_OPTIMIZER_DEFI_VOLUME = 100 # Units of crypto
    if not hasattr(settings, 'YIELD_OPTIMIZER_SIMPLE_THRESHOLD'):
        settings.YIELD_OPTIMIZER_SIMPLE_THRESHOLD = 0.04 # 4%
    if not hasattr(settings, 'YIELD_OPTIMIZER_LLM_MAX_TOKENS'):
        settings.YIELD_OPTIMIZER_LLM_MAX_TOKENS = 300
    if not hasattr(settings, 'YIELD_OPTIMIZER_LLM_CONFIDENCE_THRESHOLD'):
        settings.YIELD_OPTIMIZER_LLM_CONFIDENCE_THRESHOLD = 0.7
    if not hasattr(settings, 'YIELD_OPTIMIZER_ALERT_CONFIDENCE_THRESHOLD'):
        settings.YIELD_OPTIMIZER_ALERT_CONFIDENCE_THRESHOLD = 0.8
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    yield_agent = PrivYieldOptimizerAgent(
        agent_id="Priv-YieldOptimizer",
        broker=broker,
        persona={"name": "Yield Optimiser", "focus": "Low-Risk Income Generation"}
    )

    await broker.connect()
    await yield_agent.start()

    logger.info("\n--- Simulating messages for Yield Optimizer Agent to consume ---")

    # Mock FinancialAutomationSourcingClient.get_dividends
    with patch('backend.data_sourcing.financial_automation_sourcing.FinancialAutomationSourcingClient.get_dividends') as mock_get_dividends:
        mock_get_dividends.side_effect = lambda symbol: {
            "AAPL": [{"amount": 0.24, "exDate": "2024-05-10", "currency": "USD"}],
            "MSFT": [{"amount": 0.75, "exDate": "2024-05-15", "currency": "USD"}],
            "GOOGL": [] # No dividends for Google
        }.get(symbol, [])
        
        # Mock MarketDataIngestor.get_latest_market_data for price lookups
        with patch('backend.data_sourcing.market_data_ingestor.MarketDataIngestor.get_latest_market_data') as mock_get_market_data:
            mock_get_market_data.side_effect = lambda symbol: {
                "AAPL": {"last_trade_price": 170.00},
                "MSFT": {"last_trade_price": 400.00},
                "ETH": {"last_trade_price": 3000.00} # For DeFi test
            }.get(symbol)

            # Mock LLM calls for dividend analysis
            with patch('backend.fundamental_analysis.news_sentiment_analyzer.OpenAI.chat.completions.create') as mock_llm_create:
                mock_llm_create.side_effect = [
                    MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({
                        "assessment_summary": "AAPL dividend is consistent, good for long-term yield.",
                        "recommendation": "BUY",
                        "confidence": 0.85
                    })))]) # For AAPL dividend
                    ,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({
                        "assessment_summary": "MSFT dividend is fair, but growth potential is higher.",
                        "recommendation": "HOLD",
                        "confidence": 0.6
                    })))]) # For MSFT dividend
                    ,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps({
                        "assessment_summary": "High APY on ETH staking, but consider smart contract risk.",
                        "recommendation": "INVEST",
                        "confidence": 0.75
                    })))]) # For DeFi opportunity
                ]

                # Simulate a fundamental data update for AAPL (will trigger re-evaluation)
                mock_fundamental_data_aapl = AgentMessage(
                    sender_id="FundamentalDataIngestor",
                    message_type=MessageType.STATUS_UPDATE,
                    payload={
                        "symbol": "AAPL",
                        "company_info": {"name": "Apple Inc.", "sector": "Technology"},
                        "income_statement": [{"netIncome": 100e9}],
                        "balance_sheet": [{"totalDebt": 0, "totalEquity": 200e9}],
                        "timestamp": datetime.now().isoformat()
                    }
                )
                await broker.publish_message("fundamental_data_updates", mock_fundamental_data_aapl.model_dump())
                await asyncio.sleep(1)

                # Simulate a DeFi opportunity
                mock_defi_opportunity = AgentMessage(
                    sender_id="DeFiMonitor",
                    message_type=MessageType.STATUS_UPDATE,
                    payload={
                        "platform": "Lido",
                        "asset": "ETH",
                        "apy": 0.05, # 5% APY
                        "risk_level": "low",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                await broker.publish_message("defi_opportunities", mock_defi_opportunity.model_dump())
                await asyncio.sleep(1)


                await asyncio.sleep(15) # Give time for periodic checks and processing

    await yield_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivYieldOptimizerAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_yield_optimizer_agent_test())
