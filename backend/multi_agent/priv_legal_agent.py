# backend/multi_agent/priv_legal_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual news sourcing and sentiment analysis clients
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor

# Import settings for API keys and configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

from backend.governance.regulatory_compliance import ComplianceEngine

logger = logging.getLogger(__name__)

class PrivLegalAgent(PrivAgent):
    """
    A specialized Priv Agent focused on monitoring legal and regulatory changes,
    assessing their impact on operations, and providing legal guidance or alerts.
    It interacts closely with the Compliance Agent and Regulatory Arbiter.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.LEGAL, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.legal_updates: List[Dict[str, Any]] = [] # Stores parsed legal updates

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
        self.global_news_ingestor = GlobalNewsIngestor() # For RSS and GDELT feeds
        self.whatsapp_notifier = WhatsAppNotifier() # Initialize WhatsApp Notifier

        # Initialize ComplianceEngine if needed for direct rule lookup (conceptual)
        # self.compliance_engine = ComplianceEngine(rules_definitions_path=settings.COMPLIANCE_RULES_PATH)

        # Internal cache for news items to avoid re-processing if this agent also fetches
        self._processed_news_ids = set()
        logger.info(f"Priv Legal Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the legal agent, subscribing to relevant information feeds."""
        if self.is_running:
            logger.warning(f"Legal Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to news insights (especially regulatory/geopolitical),
        # compliance violation reports, and requests for legal review
        await self.message_broker.subscribe_to_topic(
            "news_insights", self._handle_news_insight, f"{self.agent_id}-news-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "compliance_violations", self._handle_compliance_violation, f"{self.agent_id}-compliance-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "legal_review_requests", self._handle_legal_review_request, f"{self.agent_id}-requests-sub"
        )

        self.is_running = True
        # Start a periodic task to fetch news directly relevant to legal topics
        self._periodic_legal_news_fetch_task = asyncio.create_task(self._periodic_legal_news_fetch())
        logger.info(f"Priv Legal Agent '{self.agent_id}' started and subscribed to legal topics.")

    async def stop(self):
        """Stops the legal agent."""
        if not self.is_running:
            logger.warning(f"Legal Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._periodic_legal_news_fetch_task:
            self._periodic_legal_news_fetch_task.cancel()
            try:
                await self._periodic_legal_news_fetch_task
            except asyncio.CancelledError:
                logger.info(f"Priv Legal Agent '{self.agent_id}' periodic fetch task cancelled.")

        logger.info(f"Priv Legal Agent '{self.agent_id}' stopped.")

    async def _periodic_legal_news_fetch(self):
        """
        Periodically fetches news specifically relevant to legal and regulatory changes,
        then processes them internally.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Legal Agent '{self.agent_id}': Initiating periodic legal news fetch.")
                
                # Fetch news from NewsAPI.ai/org focusing on legal/regulatory keywords
                legal_keywords = "regulation OR compliance OR legal OR lawsuit OR sanction OR policy OR directive OR bill OR act"
                news_from_api = self.news_api_client.fetch_news(
                    query=legal_keywords,
                    from_date=datetime.now() - timedelta(hours=2), # Look back 2 hours
                    limit=15
                )

                # Fetch from RSS feeds, potentially filtering for relevant sources
                # For a real system, you'd have specific RSS feeds for legal/regulatory bodies
                news_from_rss = await self.global_news_ingestor.fetch_all_rss_feeds(limit_per_feed=5)
                
                all_fetched_news = news_from_api + news_from_rss
                
                logger.info(f"Priv Legal Agent '{self.agent_id}': Fetched {len(all_fetched_news)} new potentially legally relevant articles.")

                for news_item in all_fetched_news:
                    news_id = news_item.get('url') or news_item.get('headline') + news_item.get('published_at', '')
                    if news_id in self._processed_news_ids:
                        logger.debug(f"Legal Agent: Skipping already processed news item: {news_item.get('headline')}")
                        continue

                    # Directly process the news item for legal insights
                    await self._process_and_publish_legal_insight(news_item)
                    self._processed_news_ids.add(news_id)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priv Legal Agent '{self.agent_id}': Error during periodic legal news fetch: {e}", exc_info=True)
            
            await asyncio.sleep(settings.LEGAL_NEWS_FETCH_INTERVAL_SECONDS) # Configurable interval

    async def _process_and_publish_legal_insight(self, news_item: Dict[str, Any]):
        """
        Analyzes a single news item for legal relevance and publishes the insight.
        This is similar to _handle_raw_news_message but for direct fetches by this agent.
        """
        headline = news_item.get('headline', 'N/A')
        content = news_item.get('content', '') or news_item.get('full_content', '')

        if not headline and not content:
            logger.warning(f"Legal Agent: Skipping empty news item during direct fetch.")
            return

        # Use LLM-based sentiment analyzer to get structured analysis
        analysis_results = self.news_sentiment_analyzer.analyze_article({
            "title": headline,
            "content": content
        })

        # Assess legal impact based on LLM analysis and keywords
        legal_impact_assessment = self._assess_legal_impact(news_item, analysis_results)
        
        if legal_impact_assessment.get("severity") != "NONE": # Only publish if there's a perceived impact
            self.legal_updates.append(legal_impact_assessment)
            logger.info(f"Legal Agent: Identified potential legal relevance in news: {headline}. Severity: {legal_impact_assessment.get('severity')}")

            # Publish a legal alert or update for other agents
            await self._publish_legal_alert(
                "regulatory_change_alert",
                f"Potential legal/regulatory change detected: '{headline}'. Severity: {legal_impact_assessment.get('severity')}.",
                legal_impact_assessment,
                severity=legal_impact_assessment.get("severity", "MEDIUM")
            )

    async def _handle_news_insight(self, message_payload: Dict[str, Any]):
        """
        Processes incoming news insights (from NewsAnalysisAgent) for legal implications.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            news_insight = agent_message.payload

            headline = news_insight.get('headline', 'N/A')
            category = news_insight.get('category', 'general')
            sentiment = news_insight.get('sentiment', 'neutral')
            market_impact = news_insight.get('market_impact_assessment', 'unknown')

            logger.info(f"Legal Agent: Received news insight from {agent_message.sender_id}: '{headline}' (Category: {category}, Sentiment: {sentiment}, Impact: {market_impact})")

            # Assess legal impact based on the already processed news insight
            legal_impact_assessment = self._assess_legal_impact(news_insight, news_insight) # Pass news_insight as both raw and analyzed
            
            if legal_impact_assessment.get("severity") != "NONE":
                self.legal_updates.append(legal_impact_assessment)
                logger.info(f"Legal Agent: Identified potential legal relevance in news insight: {headline}. Severity: {legal_impact_assessment.get('severity')}")

                # Publish a legal alert or update for other agents
                await self._publish_legal_alert(
                    "regulatory_change_alert",
                    f"Potential legal/regulatory change detected: '{headline}'. Severity: {legal_impact_assessment.get('severity')}.",
                    legal_impact_assessment,
                    severity=legal_impact_assessment.get("severity", "MEDIUM")
                )

        except Exception as e:
            logger.error(f"Legal Agent '{self.agent_id}': Error handling news insight: {e}", exc_info=True)

    async def _handle_compliance_violation(self, message_payload: Dict[str, Any]):
        """
        Processes compliance violation reports, providing legal context or advice.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            violation_details = agent_message.payload

            logger.warning(f"Legal Agent: Received compliance violation report for agent {violation_details.get('agent_id')}: {violation_details.get('violation_type')}.")

            # Provide legal advice based on violation type, potentially consulting ComplianceEngine
            legal_advice = self._provide_legal_advice_for_violation(violation_details)

            await self._publish_legal_alert(
                "compliance_violation_legal_review",
                f"Legal review initiated for compliance violation: {violation_details.get('violation_type')}. Advice: {legal_advice.get('summary')}",
                {**violation_details, "legal_advice": legal_advice},
                severity="HIGH" if "regulatory_breach" in violation_details.get("violation_type", "") else "MEDIUM"
            )

        except Exception as e:
            logger.error(f"Legal Agent '{self.agent_id}': Error handling compliance violation: {e}", exc_info=True)

    async def _handle_legal_review_request(self, message_payload: Dict[str, Any]):
        """
        Handles explicit requests from other agents for legal review of a specific matter.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            request_details = agent_message.payload
            sender_id = agent_message.sender_id

            logger.info(f"Legal Agent: Received legal review request from {sender_id} for: {request_details.get('subject')}.")

            # Perform conceptual legal review using LLM or rule-based system
            review_outcome = self._perform_conceptual_legal_review(request_details)

            # Publish the review outcome back to the requesting agent or a general legal topic
            response_message = AgentMessage(
                sender_id=self.agent_id,
                sender_type="agent",
                recipient_id=sender_id, # Direct reply
                message_type=MessageType.STATUS_UPDATE, # Or a new type like MessageType.LEGAL_REVIEW_RESPONSE
                payload={"request_id": request_details.get("request_id"), "review_outcome": review_outcome}
            )
            await self.broker.publish_message("legal_review_responses", response_message.model_dump())
            logger.info(f"Legal Agent: Published legal review response for request from {sender_id}.")

        except Exception as e:
            logger.error(f"Legal Agent '{self.agent_id}': Error handling legal review request: {e}", exc_info=True)

    def _assess_legal_impact(self, raw_news_item: Dict[str, Any], llm_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses the legal impact of a news item based on its content and LLM analysis.
        This function should be refined with more sophisticated NLP and rule-based systems.
        """
        headline = raw_news_item.get('headline', '')
        content = raw_news_item.get('content', '') or raw_news_item.get('full_content', '')
        sentiment = llm_analysis_results.get("sentiment", "neutral")
        market_impact = llm_analysis_results.get("market_impact", "none")
        llm_reasoning = llm_analysis_results.get("reasoning", "")

        severity = "NONE"
        required_action = "monitor"
        summary = f"Legal assessment of: {headline}"

        # Keywords for high severity
        high_severity_keywords = ["ban", "prohibit", "fine", "sanction", "enforcement action", "indictment", "fraud", "money laundering", "regulatory crackdown"]
        # Keywords for medium severity
        medium_severity_keywords = ["new regulation", "compliance change", "proposed law", "consultation", "investigation", "audit", "tax reform"]

        text_to_analyze = (headline + " " + content).lower()

        if any(keyword in text_to_analyze for keyword in high_severity_keywords):
            severity = "CRITICAL"
            required_action = "immediate_legal_review_and_action"
            summary = f"CRITICAL legal alert: {headline}. Potential severe regulatory/legal consequences."
        elif any(keyword in text_to_analyze for keyword in medium_severity_keywords):
            severity = "HIGH"
            required_action = "review_by_compliance_and_legal_team"
            summary = f"HIGH legal alert: {headline}. Requires detailed assessment of new/changing regulations."
        elif sentiment == "negative" and market_impact == "high":
            # General negative news with high market impact might have legal undertones
            severity = "MEDIUM"
            required_action = "monitor_closely_for_legal_implications"
            summary = f"MEDIUM legal alert: General negative market event ({headline}) with potential indirect legal implications."

        # Further refinement could involve:
        # - Entity extraction to identify specific companies/jurisdictions
        # - Cross-referencing with known legal databases
        # - Using a specialized legal LLM for deeper analysis

        return {
            "source_news_id": raw_news_item.get("url") or raw_news_item.get("headline"),
            "summary": summary,
            "severity": severity,
            "required_action": required_action,
            "timestamp": datetime.now().isoformat(),
            "llm_analysis": llm_analysis_results
        }

    def _provide_legal_advice_for_violation(self, violation_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides conceptual legal advice for a compliance violation.
        This could be augmented by querying a knowledge base of legal precedents or an LLM.
        """
        violation_type = violation_details.get("violation_type", "unknown")
        agent_id = violation_details.get("agent_id", "N/A")
        description = violation_details.get("description", "")

        advice_summary = f"Review {violation_type} for agent {agent_id}. Further investigation is required."
        recommended_actions = ["investigate_root_cause", "document_incident"]

        if "regulatory_breach" in violation_type.lower():
            advice_summary = f"URGENT: Regulatory breach by {agent_id} detected. Immediate cessation of activity related to the breach and reporting to relevant authorities may be required. Consult legal counsel immediately."
            recommended_actions.extend(["cease_activity", "notify_regulator", "legal_consultation"])
        elif "ethical_violation" in violation_type.lower():
            advice_summary = f"Ethical violation by {agent_id}. Internal investigation and review of ethical guidelines recommended. Consider reputation impact."
            recommended_actions.extend(["internal_investigation", "reputation_assessment", "policy_review"])
        elif "data_privacy" in violation_type.lower():
            advice_summary = f"Data privacy violation by {agent_id}. Assess data exposure, implement containment, and prepare for potential notification requirements. Consult legal counsel on data breach laws."
            recommended_actions.extend(["data_breach_protocol", "legal_consultation_privacy"])

        # Conceptual integration with ComplianceEngine to get specific rule details
        # try:
        #     rule_info = self.compliance_engine.get_rule_details(violation_details.get("rule_id"))
        #     advice_summary += f" (Rule: {rule_info.get('name', 'N/A')})"
        # except Exception as e:
        #     logger.warning(f"Could not retrieve rule details for violation: {e}")

        return {
            "summary": advice_summary,
            "recommended_actions": recommended_actions,
            "timestamp": datetime.now().isoformat(),
            "violation_context": violation_details
        }

    def _perform_conceptual_legal_review(self, request_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a comprehensive legal review using NLP and LLM analysis.
        Includes contract parsing, risk assessment, and compliance checking.
        """
        subject = request_details.get("subject", "general matter")
        details = request_details.get("details", "")
        request_id = request_details.get("request_id", "N/A")
        contract_text = request_details.get("contract_text", "")

        # Initialize review components
        outcome_summary = f"Comprehensive legal review for '{subject}' (Request ID: {request_id}) completed."
        recommendation = "Proceed with caution, seek expert human legal advice for critical matters."
        risk_assessment = "MEDIUM"
        extracted_clauses = []
        compliance_issues = []

        # 1. Contract Parsing with NLP (if contract text provided)
        if contract_text:
            try:
                # Extract key clauses using pattern matching and NLP
                import re
                
                # Common contract clause patterns
                clause_patterns = {
                    "termination": r"(?i)(termination|cancellation|end of agreement).*?(?=\n\n|\Z)",
                    "liability": r"(?i)(liability|indemnification|damages).*?(?=\n\n|\Z)",
                    "confidentiality": r"(?i)(confidential|proprietary|non-disclosure).*?(?=\n\n|\Z)",
                    "payment": r"(?i)(payment|compensation|fees|pricing).*?(?=\n\n|\Z)",
                    "jurisdiction": r"(?i)(governing law|jurisdiction|venue).*?(?=\n\n|\Z)",
                    "dispute_resolution": r"(?i)(arbitration|mediation|dispute resolution).*?(?=\n\n|\Z)"
                }
                
                for clause_type, pattern in clause_patterns.items():
                    matches = re.findall(pattern, contract_text, re.DOTALL)
                    if matches:
                        extracted_clauses.append({
                            "type": clause_type,
                            "text": matches[0][:200] + "..." if len(matches[0]) > 200 else matches[0],
                            "risk_level": self._assess_clause_risk(clause_type, matches[0])
                        })
                
                # Use LLM for deeper analysis if available
                if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                    try:
                        llm_analysis = self.news_sentiment_analyzer.analyze_article({
                            "title": f"Legal Contract Review: {subject}",
                            "content": contract_text[:4000]  # Limit for token constraints
                        })
                        outcome_summary += f" LLM Analysis: {llm_analysis.get('reasoning', 'N/A')}"
                    except Exception as e:
                        logger.warning(f"LLM analysis failed: {e}")
                
            except Exception as e:
                logger.error(f"Contract parsing failed: {e}", exc_info=True)

        # 2. Subject-specific analysis
        if "new product launch" in subject.lower():
            outcome_summary += " Initial assessment indicates potential regulatory hurdles."
            recommendation = "Requires full regulatory impact assessment and legal counsel review before launch."
            risk_assessment = "HIGH"
            compliance_issues.append("Regulatory approval required")
            compliance_issues.append("Product liability insurance needed")
        elif "contract draft" in subject.lower() or contract_text:
            outcome_summary += " Contract clauses analyzed. Key terms identified."
            recommendation = "Review extracted clauses for risk mitigation. Recommend human legal review for high-value or unusual terms."
            risk_assessment = "MEDIUM" if not extracted_clauses else "LOW"
            if any(clause["risk_level"] == "HIGH" for clause in extracted_clauses):
                risk_assessment = "HIGH"
                compliance_issues.append("High-risk clauses detected requiring review")
        elif "international expansion" in subject.lower():
            outcome_summary += " Jurisdictional analysis initiated. Different legal frameworks apply."
            recommendation = "Conduct in-depth jurisdictional legal analysis. Engage local counsel."
            risk_assessment = "HIGH"
            compliance_issues.append("Multi-jurisdictional compliance required")
            compliance_issues.append("Local legal counsel engagement recommended")
        elif "sanction" in subject.lower() or "compliance" in subject.lower():
            outcome_summary += " Sanctions and compliance verification initiated."
            recommendation = "Cross-reference with OFAC, UN, and EU sanctions lists. Verify entity compliance status."
            risk_assessment = "CRITICAL"
            compliance_issues.append("Sanctions screening required")
            compliance_issues.append("Enhanced due diligence needed")

        # 3. Regulatory updates check
        regulatory_keywords = ["regulation", "compliance", "legal", "sanction", "policy"]
        if any(keyword in details.lower() for keyword in regulatory_keywords):
            compliance_issues.append("Regulatory landscape monitoring recommended")

        return {
            "summary": outcome_summary,
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "extracted_clauses": extracted_clauses,
            "compliance_issues": compliance_issues,
            "timestamp": datetime.now().isoformat(),
            "original_request": request_details
        }

    def _assess_clause_risk(self, clause_type: str, clause_text: str) -> str:
        """
        Assesses the risk level of a contract clause based on type and content.
        """
        high_risk_keywords = ["unlimited", "perpetual", "irrevocable", "waive", "forfeit"]
        medium_risk_keywords = ["may", "discretion", "reasonable", "material"]
        
        clause_lower = clause_text.lower()
        
        if clause_type in ["liability", "termination", "jurisdiction"]:
            if any(keyword in clause_lower for keyword in high_risk_keywords):
                return "HIGH"
            elif any(keyword in clause_lower for keyword in medium_risk_keywords):
                return "MEDIUM"
        
        return "LOW"

    async def _publish_legal_alert(self, alert_type: str, message: str, details: Dict[str, Any], severity: str = "MEDIUM"):
        """
        Publishes a legal alert message to a dedicated topic and potentially to external systems.
        """
        alert_message = AgentMessage(
            sender_id=self.agent_id,
            sender_type="agent",
            recipient_id="",
            message_type=MessageType.ERROR_NOTIFICATION, # Reusing ERROR_NOTIFICATION for alerts
            payload={
                "source_agent_id": self.agent_id,
                "message": message,
                "severity": severity, # CRITICAL, HIGH, MEDIUM, LOW
                "alert_type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("legal_alerts", alert_message.model_dump())
        # Ensure a numeric logging level is used
        level = logging._nameToLevel.get(str(severity).upper(), logging.INFO)
        logger.log(level, f"Legal Agent: Published legal alert: {alert_type} - {message}")

        # For critical alerts, send a WhatsApp notification
        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            try:
                whatsapp_message = f"🚨 CRITICAL LEGAL ALERT! 🚨\nType: {alert_type}\nMessage: {message}\nDetails: {details}"
                # You might need a generic send_alert method in WhatsAppNotifier
                # For now, we'll log its conceptual sending.
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"Legal Agent: Conceptually sent critical WhatsApp alert to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"Legal Agent: Failed to send WhatsApp alert: {e}", exc_info=True)


# Example Usage (for testing PrivLegalAgent in isolation)
async def main_legal_agent_test():
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
    if not hasattr(settings, 'LEGAL_NEWS_FETCH_INTERVAL_SECONDS'):
        settings.LEGAL_NEWS_FETCH_INTERVAL_SECONDS = 10 # Fetch every 10 seconds for test
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890" # Dummy number


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    legal_agent = PrivLegalAgent(
        agent_id="Priv-LegalCounsel",
        broker=broker,
        persona={"name": "Legal Advisor", "focus": "Regulatory Compliance & Risk"}
    )
    # The NewsAnalysisAgent is used to simulate incoming news_insights messages
    news_agent = PrivNewsAnalysisAgent(
        agent_id="Priv-NewsAnalyzer",
        broker=broker,
        persona={"name": "News Analyzer", "focus": "Market-moving events"}
    )

    await broker.connect()
    await legal_agent.start()
    await news_agent.start() # Start news agent to produce insights

    logger.info("\n--- Simulating messages for Legal Agent to consume ---")

    # Simulate a news insight about a new regulation (from NewsAnalysisAgent)
    mock_regulatory_news_insight = AgentMessage(
        sender_id="Priv-NewsAnalyzer",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "original_news_id": "news_123",
            "source": "RegulatoryWatch",
            "headline": "New EU regulation on crypto assets proposed, impacting DeFi.",
            "content": "The European Commission has put forward a new legislative package aimed at bringing clarity and oversight to decentralized finance. This could lead to new licensing requirements.",
            "category": "regulatory",
            "sentiment": "neutral", # LLM might classify as neutral, but legal agent should flag
            "timestamp_processed": datetime.now().isoformat(),
            "market_impact_assessment": "high_regulatory_impact",
            "confidence_score": 0.9,
            "symbols_mentioned": ["EU", "DEFI", "CRYPTO"]
        }
    )
    await broker.publish_message("news_insights", mock_regulatory_news_insight.model_dump())
    await asyncio.sleep(1)

    # Simulate a compliance violation report
    mock_compliance_violation = AgentMessage(
        sender_id="Priv-Compliance",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "agent_id": "Priv-Strategist",
            "violation_type": "regulatory_breach",
            "description": "Attempted trade in sanctioned entity. Rule ID: REG-005.",
            "timestamp": datetime.now().isoformat(),
            "rule_id": "REG-005"
        }
    )
    await broker.publish_message("compliance_violations", mock_compliance_violation.model_dump())
    await asyncio.sleep(1)

    # Simulate a request for legal review
    mock_legal_review_request = AgentMessage(
        sender_id="Priv-PortfolioManager",
        message_type=MessageType.ARBITRATION_REQUEST, # Reusing for conceptual request
        payload={
            "request_id": "req_001",
            "subject": "Review of new investment product legal risks.",
            "details": "Product involves novel derivatives and cross-border implications.",
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("legal_review_requests", mock_legal_review_request.model_dump())
    await asyncio.sleep(1)

    # Allow time for periodic fetches and processing
    await asyncio.sleep(15) # Give time for agents to process messages and for legal agent's periodic fetch

    await legal_agent.stop()
    await news_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivLegalAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_legal_agent_test())
