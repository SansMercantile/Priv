# backend/multi_agent/priv_credit_agent.py

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
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from backend.data_sourcing.financial_automation_sourcing import FinancialAutomationSourcingClient

# Import settings for API keys and configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivCreditAgent(PrivAgent):
    """
    A specialized Priv Agent focused on credit analysis, debt markets,
    and assessing the creditworthiness of entities (corporations, governments).
    It identifies opportunities in bonds, credit default swaps, and provides
    credit risk assessments.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.CREDIT, message_broker=message_broker, broker=broker, persona=persona)
        self.is_running = False
        self.credit_ratings_cache: Dict[str, Dict[str, Any]] = {} # Cache for entity credit ratings
        self.bond_market_data: Dict[str, Dict[str, Any]] = {} # Cache for bond prices/yields

        # Initialize real data sourcing and analysis clients
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
        self.fundamental_data_ingestor = FundamentalDataIngestor()
        
        # Initialize FinancialAutomationSourcingClient with optional API key
        polygon_key = getattr(settings, 'POLYGON_API_KEY', None)
        self.financial_automation_sourcing_client = FinancialAutomationSourcingClient(
            api_key=polygon_key
        )
        self.whatsapp_notifier = WhatsAppNotifier()

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv Credit Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the credit agent, subscribing to relevant data feeds."""
        if self.is_running:
            logger.warning(f"Credit Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to news insights (corporate news, economic reports),
        # and specific credit market data feeds (bond prices, CDS spreads)
        await self.broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )
        await self.broker.subscribe_to_topic(
            "credit_market_data", self._handle_credit_market_data, f"{self.agent_id}-credit-sub"
        )
        await self.broker.subscribe_to_topic(
            "credit_analysis_requests", self._handle_credit_analysis_request, f"{self.agent_id}-requests-sub"
        )
        await self.broker.subscribe_to_topic(
            "fundamental_data_updates", self._handle_fundamental_data_update, f"{self.agent_id}-fundamental-sub"
        )

        self.is_running = True
        # Start a periodic task to fetch news directly relevant to credit
        self._periodic_credit_news_fetch_task = asyncio.create_task(self._periodic_credit_news_fetch())
        logger.info(f"Priv Credit Agent '{self.agent_id}' started and subscribed to credit topics.")

    async def stop(self):
        """Stops the credit agent."""
        if not self.is_running:
            logger.warning(f"Credit Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_credit_news_fetch_task:
            self._periodic_credit_news_fetch_task.cancel()
            try:
                await self._periodic_credit_news_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv Credit Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv Credit Agent '{self.agent_id}' stopped.")

    async def _periodic_credit_news_fetch(self):
        """
        Periodically fetches news specifically relevant to credit and corporate finance,
        then processes them internally.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Credit Agent '{self.agent_id}': Initiating periodic credit news fetch.")
                
                # Fetch news from NewsAPI.ai/org focusing on credit-relevant keywords
                credit_keywords = "debt OR bond OR credit rating OR default OR bankruptcy OR earnings OR M&A OR corporate finance OR dividend OR split"
                news_from_api = self.news_api_client.fetch_news(
                    query=credit_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=settings.CREDIT_NEWS_FETCH_LIMIT
                )

                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=settings.CREDIT_NEWS_RSS_LIMIT)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv Credit Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially credit-relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"Credit Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    await self._process_and_publish_credit_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv Credit Agent '{self.agent_id}': Error during periodic credit news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.CREDIT_NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _process_and_publish_credit_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for credit relevance and publishes the insight.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"Credit Agent: Skipping empty news item during direct fetch.")
            return

        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        entity_impact = self._assess_entity_credit_impact(news_item, analysis_results)
        
        if entity_impact:
            logger.info(f"Credit Agent: News impacts credit for {entity_impact.get('entity')}. New rating: {entity_impact.get('new_rating')}")
            self.credit_ratings_cache[entity_impact["entity"]] = entity_impact
            await self._publish_credit_update("entity_credit_update", entity_impact)

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes incoming news insights (from NewsAnalysisAgent) for credit implications.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            category = news_insight.get('category', 'general')
            sentiment = news_insight.get('sentiment', 'neutral')

            logger.info(f"Credit Agent: Received news insight from {agent_message.sender_id}: '{headline}' (Category: {category}, Sentiment: {sentiment})")

            # Assess credit impact based on the already processed news insight
            entity_impact = self._assess_entity_credit_impact(news_insight, news_insight) # Pass news_insight as both raw and analyzed
            
            if entity_impact:
                logger.info(f"Credit Agent: News insight impacts credit for {entity_impact.get('entity')}. New rating: {entity_impact.get('new_rating')}")
                self.credit_ratings_cache[entity_impact["entity"]] = entity_impact
                await self._publish_credit_update("entity_credit_update", entity_impact)

        except Exception as e:
            logger.error(f"Credit Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    async def _handle_credit_market_data(self, message_payload: Dict[str, Any]):
        """
        Processes incoming credit market data (e.g., bond prices, yields, CDS spreads).
        This data would typically come from the MarketDataIngestor or a specialized credit data ingestor.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            credit_data = agent_message.payload

            instrument = credit_data.get("instrument") # e.g., "US10YT", "AAPL_BOND_2030"
            data_type = credit_data.get("type") # e.g., "bond_price", "yield", "cds_spread"
            value = credit_data.get("value")

            if instrument and data_type and value is not None:
                if instrument not in self.bond_market_data:
                    self.bond_market_data[instrument] = {}
                self.bond_market_data[instrument][data_type] = value
                self.bond_market_data[instrument]["timestamp"] = datetime.now().isoformat()
                logger.debug(f"Credit Agent: Updated credit market data for {instrument}: {data_type}={value}.")

                # Trigger analysis if significant changes detected
                await self._analyze_bond_opportunity(instrument)

        except Exception as e:
            logger.error(f"Credit Agent '{self.agent_id}': Error handling credit market data: {e}", exc_info=True)

    async def _handle_fundamental_data_update(self, message_payload: Dict[str, Any]):
        """
        Processes incoming fundamental data updates (from FundamentalDataIngestor)
        to update internal credit assessment.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            fundamental_data = agent_message.payload
            
            symbol = fundamental_data.get("symbol")
            company_info = fundamental_data.get("company_info")
            income_statement = fundamental_data.get("income_statement")
            balance_sheet = fundamental_data.get("balance_sheet")

            if symbol and (company_info or income_statement or balance_sheet):
                logger.info(f"Credit Agent: Received fundamental data update for {symbol}. Re-assessing credit.")
                
                # Perform a more in-depth credit analysis based on financials
                credit_assessment_from_fundamentals = self._analyze_credit_from_fundamentals(
                    symbol, company_info, income_statement, balance_sheet
                )
                
                if credit_assessment_from_fundamentals:
                    self.credit_ratings_cache[symbol] = credit_assessment_from_fundamentals
                    await self._publish_credit_update("fundamental_credit_update", credit_assessment_from_fundamentals)
                    # Also re-evaluate any bonds related to this entity
                    for bond_symbol in self.bond_market_data.keys():
                        if symbol in bond_symbol: # Simple heuristic to link bond to company
                            await self._analyze_bond_opportunity(bond_symbol)

        except Exception as e:
            logger.error(f"Credit Agent '{self.agent_id}': Error handling fundamental data update: {e}", exc_info=True)


    async def _handle_credit_analysis_request(self, message_payload: Dict[str, Any]):
        """
        Handles explicit requests for credit analysis on a specific entity or bond.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            request_details = agent_message.payload
            sender_id = agent_message.sender_id
            entity = request_details.get("entity")
            instrument = request_details.get("instrument")

            logger.info(f"Credit Agent: Received credit analysis request from {sender_id} for entity: {entity} or instrument: {instrument}.")

            analysis_result = await self._perform_detailed_credit_analysis(entity, instrument)

            response_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=sender_id,
                message_type=MessageType.STATUS_UPDATE, # Or new type like MessageType.CREDIT_ANALYSIS_REPORT
                payload={"request_id": request_details.get("request_id"), "analysis_result": analysis_result}
            )
            await self.broker.publish_message("credit_analysis_reports", response_message.model_dump())
            logger.info(f"Credit Agent: Published credit analysis report for request from {sender_id}.")

        except Exception as e:
            logger.error(f"Credit Agent '{self.agent_id}': Error handling credit analysis request: {e}", exc_info=True)

    def _assess_entity_credit_impact(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Assesses credit impact on an entity from news, leveraging LLM analysis.
        This function should be refined with more sophisticated entity extraction and credit modeling.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        symbols_mentioned = llm_analysis_results.get("symbols", [])
        
        # Simple entity extraction for demo based on symbols mentioned by LLM or keywords
        entity = None
        if symbols_mentioned:
            entity = symbols_mentioned[0] # Take the first symbol as the primary entity
        elif "google" in headline.lower() or "alphabet" in headline.lower(): entity = "GOOGL"
        elif "tesla" in headline.lower(): entity = "TSLA"
        elif "us treasury" in headline.lower() or "us government" in headline.lower(): entity = "US_GOVT"

        if not entity: return None

        current_rating = self.credit_ratings_cache.get(entity, {}).get("new_rating", "BBB") # Default to BBB if unknown
        new_rating = current_rating
        reason_for_change = f"News impact: {headline}"

        # Logic for rating changes based on sentiment and keywords
        if sentiment == "negative":
            if "default" in content.lower() or "bankruptcy" in content.lower():
                new_rating = "D"
                reason_for_change = "Bankruptcy/Default announced."
            elif "downgrade" in content.lower() or "negative outlook" in content.lower():
                # Simple downgrade logic (e.g., AAA -> AA+, AA+ -> AA, etc.)
                if current_rating == "AAA": new_rating = "AA+"
                elif current_rating == "AA+": new_rating = "AA"
                elif current_rating == "AA": new_rating = "AA-"
                elif current_rating == "BBB": new_rating = "BB+" # Junk status
                reason_for_change = "Credit rating downgrade implied by news."
            elif "debt increase" in content.lower() or "profit warning" in content.lower():
                # Slight negative adjustment
                if current_rating.startswith("A"): new_rating = current_rating[:-1] + "-" # A+ -> A, A -> A-
                elif current_rating.startswith("B"): new_rating = current_rating[:-1] + "-"
                reason_for_change = "Negative financial news impacting credit profile."

        elif sentiment == "positive":
            if "upgrade" in content.lower() or "positive outlook" in content.lower():
                # Simple upgrade logic
                if current_rating == "AA-": new_rating = "AA"
                elif current_rating == "AA": new_rating = "AA+"
                elif current_rating == "BB+": new_rating = "BBB" # Investment grade
                reason_for_change = "Credit rating upgrade implied by news."
            elif "strong earnings" in content.lower() or "debt reduction" in content.lower():
                # Slight positive adjustment
                if current_rating.endswith("+"): new_rating = current_rating # Already highest in tier
                elif current_rating.endswith("-"): new_rating = current_rating[:-1] # A- -> A
                elif current_rating.isalpha(): new_rating = current_rating + "+" # A -> A+
                reason_for_change = "Positive financial news improving credit profile."

        return {
            "entity": entity,
            "original_rating": current_rating,
            "new_rating": new_rating,
            "reason": reason_for_change,
            "timestamp": datetime.now().isoformat(),
            "llm_analysis": llm_analysis_results
        }

    def _analyze_credit_from_fundamentals(self, symbol: str, company_info: Optional[Dict[str, Any]],
                                          income_statement: Optional[List[Dict[str, Any]]],
                                          balance_sheet: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """
        Analyzes creditworthiness based on fundamental financial statements.
        This is a conceptual implementation and needs detailed financial ratio analysis.
        """
        if not (company_info or income_statement or balance_sheet):
            logger.warning(f"No fundamental data to analyze credit for {symbol}.")
            return None

        # Conceptual credit score based on available data
        credit_score = 0.5 # Default neutral
        current_rating = self.credit_ratings_cache.get(symbol, {}).get("new_rating", "BBB")
        new_rating = current_rating
        reason = "Fundamental analysis."

        if income_statement and balance_sheet:
            # Example: Simple check for debt-to-equity ratio and profitability
            latest_income = income_statement[0] if income_statement else {}
            latest_balance = balance_sheet[0] if balance_sheet else {}

            total_debt = latest_balance.get('totalDebt', 0) or latest_balance.get('longTermDebt', 0) + latest_balance.get('shortTermDebt', 0)
            total_equity = latest_balance.get('totalEquity', 0)
            net_income = latest_income.get('netIncome', 0)

            if total_equity > 0 and total_debt is not None:
                debt_to_equity = total_debt / total_equity
                if debt_to_equity > settings.CREDIT_HIGH_DEBT_THRESHOLD: # e.g., 2.0
                    credit_score -= 0.2
                    reason += " High debt-to-equity ratio."
                    if new_rating == "AAA": new_rating = "AA+" # Example downgrade
                elif debt_to_equity < settings.CREDIT_LOW_DEBT_THRESHOLD: # e.g., 0.5
                    credit_score += 0.1
                    reason += " Low debt-to-equity ratio."
                    if new_rating == "AA+": new_rating = "AAA" # Example upgrade

            if net_income < 0:
                credit_score -= 0.1
                reason += " Negative net income."
                if new_rating.startswith("A"): new_rating = "BBB" # Significant downgrade for unprofitability

        # Map conceptual score to a rating or adjust existing rating
        # This is a highly simplified mapping. Real credit models are complex.
        if credit_score > 0.7: new_rating = "AAA"
        elif credit_score > 0.4: new_rating = "BBB"
        elif credit_score < 0.2: new_rating = "BB"

        return {
            "entity": symbol,
            "original_rating": current_rating,
            "new_rating": new_rating,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "fundamental_data_summary": {
                "company_info_present": bool(company_info),
                "income_statement_present": bool(income_statement),
                "balance_sheet_present": bool(balance_sheet)
            }
        }


    async def _analyze_bond_opportunity(self, instrument: str):
        """
        Analyzes a bond for potential trade opportunities
        based on its yield and the entity's credit rating.
        """
        data = self.bond_market_data.get(instrument)
        if not data or "yield" not in data or data.get("bond_price") is None:
            logger.warning(f"Credit Agent: Insufficient data for bond {instrument} analysis.")
            return

        bond_yield = data["yield"]
        bond_price = data["bond_price"]
        
        # Assume instrument name contains entity, e.g., "AAPL_BOND_2030" -> "AAPL"
        entity_id = instrument.split('_')[0] if '_' in instrument else instrument

        entity_rating_info = self.credit_ratings_cache.get(entity_id, {})
        current_rating = entity_rating_info.get("new_rating", "BBB") # Default to BBB if no specific rating

        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = f"Monitoring {instrument}. Price: {bond_price}, Yield: {bond_yield:.2%}, Rating: {current_rating}."

        # Simple logic: if yield is high for a good rating, it's a BUY. If yield is low for bad rating, it's a SELL.
        # Thresholds from settings for configurability
        INVESTMENT_GRADE_YIELD_BUY_THRESHOLD = getattr(settings, 'CREDIT_INVESTMENT_GRADE_YIELD_BUY_THRESHOLD', 0.04)
        JUNK_BOND_YIELD_SELL_THRESHOLD = getattr(settings, 'CREDIT_JUNK_BOND_YIELD_SELL_THRESHOLD', 0.02)
        
        if current_rating in ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"] and \
           bond_yield > INVESTMENT_GRADE_YIELD_BUY_THRESHOLD:
            action = TradeAction.BUY
            confidence = 0.8
            reasoning = f"Attractive yield ({bond_yield:.2%}) for investment-grade bond ({instrument}, Rating: {current_rating})."
        elif current_rating in ["BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"] and \
             bond_yield < JUNK_BOND_YIELD_SELL_THRESHOLD:
            action = TradeAction.SELL
            confidence = 0.7
            reasoning = f"Poor yield ({bond_yield:.2%}) for speculative-grade bond ({instrument}, Rating: {current_rating})."

        if action != TradeAction.HOLD:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=instrument,
                action=action,
                volume=settings.CREDIT_TRADE_PROPOSAL_VOLUME, # Configurable volume for bonds
                entry_price=bond_price,
                reasoning=reasoning,
                confidence=confidence,
                risk_assessment={"credit_risk_rating": current_rating, "bond_yield": bond_yield}
            )
            await self._publish_credit_proposal(proposal)

    async def _perform_detailed_credit_analysis(self, entity: Optional[str], instrument: Optional[str]) -> Dict[str, Any]:
        """
        Performs a detailed credit analysis based on a request, fetching data as needed
        and using LLM for synthesis.
        """
        analysis_summary = "No specific analysis performed."
        rating = "N/A"
        collected_analysis_data = {}

        if entity:
            logger.info(f"Credit Agent: Performing detailed analysis for entity: {entity}.")
            # Fetch fundamental data for the entity
            if self.fundamental_data_ingestor.eodhd_client:
                fundamentals = await self.fundamental_data_ingestor.eodhd_client.get_fundamentals(entity)
                if fundamentals: collected_analysis_data['fundamentals'] = fundamentals
            elif self.fundamental_data_ingestor.simfin_client:
                info = await self.fundamental_data_ingestor.simfin_client.get_company_info(entity)
                statements = await self.fundamental_data_ingestor.simfin_client.get_company_statements(entity, "income")
                if info: collected_analysis_data['company_info'] = info
                if statements: collected_analysis_data['income_statement'] = statements

            # Fetch news related to the entity
            entity_news = self.news_api_client.fetch_news(query=entity, limit=settings.CREDIT_LLM_NEWS_LIMIT)
            if entity_news: collected_analysis_data['entity_news'] = entity_news

            # Use LLM to synthesize a credit report
            prompt = f"Analyze the creditworthiness of {entity} based on the following data:\n"
            if 'fundamentals' in collected_analysis_data:
                prompt += f"Fundamental Data: {collected_analysis_data['fundamentals']}\n"
            if 'company_info' in collected_analysis_data:
                prompt += f"Company Info: {collected_analysis_data['company_info']}\n"
            if 'income_statement' in collected_analysis_data:
                prompt += f"Income Statement (latest): {collected_analysis_data['income_statement'][0] if collected_analysis_data['income_statement'] else 'N/A'}\n"
            if 'entity_news' in collected_analysis_data:
                prompt += f"Recent News: {[n['title'] for n in collected_analysis_data['entity_news']]}\n"
            
            prompt += "Provide a credit rating (e.g., AAA, BBB, junk), a summary of key factors, and a recommendation (e.g., 'Invest', 'Avoid')."

            try:
                llm_response = self.news_sentiment_analyzer.client.chat.completions.create(
                    model=self.news_sentiment_analyzer.model,
                    messages=[
                        {"role": "system", "content": "You are an expert credit analyst. Provide a concise credit report."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=settings.CREDIT_LLM_MAX_TOKENS,
                    temperature=0.5
                )
                llm_text_response = llm_response.choices[0].message.content
                analysis_summary = llm_text_response
                # Attempt to extract rating from LLM response
                rating_match = re.search(r"(AAA|AA\+|AA|AA-|A\+|A|A-|BBB\+|BBB|BBB-|BB\+|BB|BB-|B\+|B|B-|CCC\+|CCC|CCC-|CC|C|D)", llm_text_response, re.IGNORECASE)
                if rating_match:
                    rating = rating_match.group(0).upper()
            except Exception as e:
                logger.error(f"Credit Agent: LLM analysis failed for entity {entity}: {e}", exc_info=True)
                analysis_summary = f"LLM analysis failed: {e}"

        elif instrument:
            logger.info(f"Credit Agent: Performing detailed analysis for instrument: {instrument}.")
            bond_data = self.bond_market_data.get(instrument, {"yield": 0.03, "bond_price": 100})
            analysis_summary = f"Analysis for bond {instrument}: Current yield is {bond_data['yield']:.2%}. Price: {bond_data['bond_price']}."
            # Retrieve cached rating for the associated entity if available
            entity_id = instrument.split('_')[0] if '_' in instrument else instrument
            rating = self.credit_ratings_cache.get(entity_id, {}).get("new_rating", "N/A")

        return {
            "subject_entity": entity,
            "subject_instrument": instrument,
            "analysis_summary": analysis_summary,
            "conceptual_rating": rating,
            "timestamp": datetime.now().isoformat(),
            "collected_data_summary": {k: len(v) if isinstance(v, list) else "present" for k,v in collected_analysis_data.items()}
        }

    async def _publish_credit_update(self, update_type: str, details: Dict[str, Any]):
        """Helper to publish credit-related updates."""
        update_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE, # Or new type like MessageType.CREDIT_UPDATE
            payload={
                "update_type": update_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("credit_updates", update_message.model_dump())
        logger.info(f"Credit Agent: Published credit update: {update_type} for {details.get('entity', details.get('instrument'))}.")

        # Send WhatsApp alert for significant rating changes
        if update_type == "entity_credit_update" and details.get("original_rating") != details.get("new_rating"):
            if details.get("new_rating") in ["D", "CCC", "CC", "C", "BB+", "BB", "BB-"]: # Significant downgrade or junk status
                critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
                whatsapp_message = (
                    f"🚨 CREDIT RATING ALERT! 🚨\n"
                    f"Entity: {details.get('entity')}\n"
                    f"Old Rating: {details.get('original_rating')}\n"
                    f"New Rating: {details.get('new_rating')}\n"
                    f"Reason: {details.get('reason')}\n"
                    f"Urgent review required."
                )
                try:
                    # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                    logger.info(f"Credit Agent: Conceptually sent critical WhatsApp alert for credit downgrade to {critical_alert_recipient}.")
                except Exception as e:
                    logger.error(f"Credit Agent: Failed to send WhatsApp alert for credit: {e}", exc_info=True)


    async def _publish_credit_proposal(self, proposal: TradeProposal):
        """Helper to publish a trade proposal generated by the credit agent."""
        proposal_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.TRADE_PROPOSAL,
            payload=proposal.model_dump()
        )
        await self.broker.publish_message("trade_proposals", proposal_message.model_dump())
        logger.info(f"Credit Agent: Published trade proposal: {proposal.action} {proposal.symbol} (Confidence: {proposal.confidence:.2f}).")


# Example Usage (for testing PrivCreditAgent in isolation)
async def main_credit_agent_test():
    logging.basicConfig(level=logging.INFO)
    import re # Import regex for test
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
    if not hasattr(settings, 'POLYGON_API_KEY'):
        settings.POLYGON_API_KEY = "dummy_polygon_key"
    if not hasattr(settings, 'CREDIT_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.CREDIT_NEWS_FETCH_INTERVAL_SECONDS = 10
    if not hasattr(settings, 'CREDIT_NEWS_FETCH_LIMIT'):
        settings.CREDIT_NEWS_FETCH_LIMIT = 5
    if not hasattr(settings, 'CREDIT_NEWS_RSS_LIMIT'):
        settings.CREDIT_NEWS_RSS_LIMIT = 3
    if not hasattr(settings, 'CREDIT_LLM_NEWS_LIMIT'):
        settings.CREDIT_LLM_NEWS_LIMIT = 3
    if not hasattr(settings, 'CREDIT_LLM_MAX_TOKENS'):
        settings.CREDIT_LLM_MAX_TOKENS = 500
    if not hasattr(settings, 'CREDIT_TRADE_PROPOSAL_VOLUME'):
        settings.CREDIT_TRADE_PROPOSAL_VOLUME = 1 # Conceptual volume for bonds
    if not hasattr(settings, 'CREDIT_HIGH_DEBT_THRESHOLD'):
        settings.CREDIT_HIGH_DEBT_THRESHOLD = 2.0
    if not hasattr(settings, 'CREDIT_LOW_DEBT_THRESHOLD'):
        settings.CREDIT_LOW_DEBT_THRESHOLD = 0.5
    if not hasattr(settings, 'CREDIT_INVESTMENT_GRADE_YIELD_BUY_THRESHOLD'):
        settings.CREDIT_INVESTMENT_GRADE_YIELD_BUY_THRESHOLD = 0.04
    if not hasattr(settings, 'CREDIT_JUNK_BOND_YIELD_SELL_THRESHOLD'):
        settings.CREDIT_JUNK_BOND_YIELD_SELL_THRESHOLD = 0.02
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    credit_agent = PrivCreditAgent(
        agent_id="Priv-CreditAnalyst",
        broker=broker,
        persona={"name": "Credit Analyst", "focus": "Debt Markets & Credit Risk"}
    )
    news_agent = PrivNewsAnalysisAgent( # For simulating news insights
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await credit_agent.start()
    await news_agent.start()

    logger.info("\n--- Simulating messages for Credit Agent to consume ---")

    # Simulate news impacting a company's credit (from NewsAnalysisAgent)
    mock_news_credit_downgrade = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "original_news_id": "news_789",
            "source": "Reuters",
            "headline": "Tesla's debt outlook downgraded by Moody's.",
            "content": "Moody's has revised its outlook on Tesla's debt from stable to negative, citing concerns over increasing competition and capital expenditure.",
            "category": "corporate_finance",
            "sentiment": "negative",
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "corporate_bond_impact",
            "confidence_score": 0.9,
            "symbols_mentioned": ["TSLA"]
        }
    )
    await broker.publish_message("news_insights", mock_news_credit_downgrade.model_dump())
    await asyncio.sleep(1)

    # Simulate fundamental data update (from FundamentalDataIngestor)
    mock_fundamental_data_aapl = AgentMessage(
        sender_id="FundamentalDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "AAPL",
            "source": "EODHD",
            "company_info": {"name": "Apple Inc.", "sector": "Technology"},
            "income_statement": [{"netIncome": 100e9, "revenue": 400e9}],
            "balance_sheet": [{"totalDebt": 100e9, "totalEquity": 200e9}],
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("fundamental_data_updates", mock_fundamental_data_aapl.model_dump())
    await asyncio.sleep(1)

    # Simulate credit market data for a bond
    mock_bond_data_aapl = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "instrument": "AAPL_BOND_2030",
            "type": "bond_price",
            "value": 102.50,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("credit_market_data", mock_bond_data_aapl.model_dump())
    await asyncio.sleep(0.5)

    mock_bond_data_aapl_yield = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "instrument": "AAPL_BOND_2030",
            "type": "yield",
            "value": 0.045, # High yield for a good company
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("credit_market_data", mock_bond_data_aapl_yield.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a credit analysis request
    mock_credit_analysis_request = AgentMessage(
        sender_id="Priv-PortfolioManager",
        message_type=MessageType.ARBITRATION_REQUEST,
        payload={
            "request_id": "credit_req_001",
            "entity": "Alphabet Inc.",
            "instrument": None,
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("credit_analysis_requests", mock_credit_analysis_request.model_dump())
    await asyncio.sleep(1)


    await asyncio.sleep(15) # Give time for agents to process messages and for periodic fetches

    await credit_agent.stop()
    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivCreditAgent test finished.")

if __name__ == '__main__':
    import re # Ensure re is imported for the test block
    asyncio.run(main_credit_agent_test())
