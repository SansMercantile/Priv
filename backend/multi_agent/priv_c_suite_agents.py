# backend/multi_agent/priv_c_suite_agents.py

import logging
import json
import httpx
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import AgentMessage, MessageType
from shared_resources.backend import dependencies
from backend.config import settings

logger = logging.getLogger(__name__)

class PrivCSuiteAgent(PrivAgent):
    """
    Base class for C-Suite agents in the PRIV Family Framework.
    These agents handle high-level governance, strategy, and cross-departmental logic.
    They are designed to receive strategic directives and delegate tasks to Tier II agents.
    """
    def __init__(self, agent_id: str, role: str, **kwargs):
        super().__init__(agent_id=agent_id, **kwargs)
        self.role = role
        # Directly access singleton instances from the dependencies module
        self.broker = dependencies.message_broker_instance
        self.compliance_engine = dependencies.compliance_engine_instance
        self.ethical_scaffolding = dependencies.ethical_scaffolding_manager_instance
        self.policy_compiler = dependencies.policy_compiler_instance
        self.licensing_manager = dependencies.licensing_manager_instance
        self.threat_detector = dependencies.dynamic_threat_detector_instance
        self.funding_protocol = dependencies.funding_protocol_instance
        self.llm_client = dependencies.llm_client_instance # For advanced reasoning
        
        logger.info(f"Initialized C-Suite Agent: {self.agent_id} ({self.role}) with access to core modules.")

    async def process_message(self, message: AgentMessage):
        """Processes high-level messages and directives by routing to the handler."""
        logger.info(f"[{self.agent_id}] received message of type '{message.message_type}' from {message.sender_id}")
        await self.handle_directive(message)

    async def handle_directive(self, message: AgentMessage):
        """Placeholder for handling specific directives for each C-Suite role."""
        logger.debug(f"[{self.agent_id}] default directive handler for payload: {message.payload}")
        pass

class SolvaAgent(PrivCSuiteAgent):
    """
    CFO Persona (ENTJ-A): Handles institutional finance, treasury, forecasting, and macro compliance.
    """
    def __init__(self, **kwargs):
        super().__init__(agent_id="SOLVA-CFO", role="Chief Financial Officer", **kwargs)

    async def handle_directive(self, message: AgentMessage):
        if message.message_type == MessageType.DATA_INSIGHT and "macro_economic_report" in message.payload:
            logger.info("[SOLVA-CFO] Analyzing new macroeconomic report to adjust capital allocation strategy.")
            # Functional Logic: Generate a new capital allocation directive
            new_directive_payload = {
                "directive": "ADJUST_CAPITAL_ALLOCATION",
                "risk_appetite": "CONSERVATIVE",
                "source_report": message.payload["macro_economic_report"]["id"]
            }
            await self.broker.publish_message(
                "capital_directives",
                AgentMessage(sender_id=self.agent_id, message_type=MessageType.DIRECTIVE, payload=new_directive_payload)
            )

class BrigitAgent(PrivCSuiteAgent):
    """
    COO Persona (ISTJ-T): Manages operations, HR policy logic, and regulatory interfacing.
    """
    def __init__(self, **kwargs):
        super().__init__(agent_id="BRIGIT-COO", role="Chief Operating Officer", **kwargs)

    async def handle_directive(self, message: AgentMessage):
        if message.message_type == MessageType.SYSTEM_ALERT and "performance_degradation" in message.payload:
            agent_id = message.payload["performance_degradation"]["agent_id"]
            logger.info(f"[BRIGIT-COO] Investigating operational performance degradation for agent: {agent_id}.")
            # Functional Logic: Request a diagnostic report from the target agent
            diagnostic_request = {
                "request": "PERFORMANCE_DIAGNOSTIC",
                "target_agent": agent_id
            }
            await self.broker.publish_message(
                "operational_tasks",
                AgentMessage(sender_id=self.agent_id, message_type=MessageType.TASK, payload=diagnostic_request)
            )

class AvaAgent(PrivCSuiteAgent):
    """
    CPO Persona (INFP-A): Manages human-AI interface, ethical scaffolding, and cultural intuition.
    """
    def __init__(self, **kwargs):
        super().__init__(agent_id="AVA-CPO", role="Chief Product Officer", **kwargs)

    async def handle_directive(self, message: AgentMessage):
        if message.message_type == MessageType.USER_FEEDBACK:
            await self._process_user_feedback(message.payload)
        elif message.message_type == MessageType.DATA_INSIGHT and "news_article" in message.payload:
            await self._process_news_for_expressive_action(message.payload)

    async def _process_user_feedback(self, payload: dict):
        feedback_content = payload.get("content", "")
        sentiment = payload.get("sentiment", 0.0)
        logger.info("[AVA-CPO] Analyzing user feedback to improve human-AI interaction protocols.")
        
        # Functional Logic: Evaluate feedback against the ethical framework
        is_aligned = self.ethical_scaffolding.evaluate_action(
            action_description=f"Reviewing user feedback: '{feedback_content}'",
            principle="USER_WELLBEING"
        )
        if not is_aligned:
            logger.warning(f"[AVA-CPO] User feedback indicates potential ethical misalignment. Escalating.")
            escalation_payload = {"feedback": payload, "concern": "Ethical Misalignment"}
            await self.broker.publish_message(
                "governance_review",
                 AgentMessage(sender_id=self.agent_id, message_type=MessageType.SYSTEM_ALERT, payload=escalation_payload)
            )
        
        # NEW: Context-Aware "Looney Tunes" Action based on positive sentiment
        if sentiment > 0.8: # If sentiment is very positive
            logger.info("[AVA-CPO] Positive sentiment detected. Triggering celebratory animation.")
            action_payload = {
                "action_type": "SPAWN_OBJECT",
                "payload": {"object_type": "confetti"} # Spawn confetti for celebration
            }
            # Make a direct API call to the Looney Tunes endpoint
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"http://localhost:8000/api/v1/looney-tunes/trigger-action", json=action_payload, timeout=5.0)
            except Exception as e:
                logger.error(f"[AVA-CPO] Failed to trigger Looney Tunes action: {e}")


    async def _process_news_for_expressive_action(self, payload: dict):
        """Analyzes news and triggers a context-aware 'Looney Tunes' action."""
        article = payload.get("news_article", {})
        headline = article.get("title", "")
        logger.info(f"[AVA-CPO] Analyzing news headline for expressive action: '{headline}'")

        if not self.llm_client or not await self.llm_client.is_initialized():
            logger.warning("[AVA-CPO] LLM client not available for expressive analysis.")
            return

        prompt = f"Analyze the following headline and determine if it relates to a simple, visual concept like 'rain', 'sun', or 'celebration'. If it does, respond with a single JSON object with two keys: 'action_type' set to 'SPAWN_OBJECT' and 'object_type' set to an appropriate object (e.g., 'umbrella', 'sun', 'confetti'). If not, respond with an empty JSON object. Headline: '{headline}'"
        
        try:
            llm_response = await self.llm_client.generate_content(prompt, temperature=0.1)
            clean_response = llm_response.strip().replace("```json", "").replace("```", "")
            action_data = json.loads(clean_response)

            if action_data and action_data.get("action_type") == "SPAWN_OBJECT":
                logger.info(f"[AVA-CPO] Triggering Looney Tunes action based on news: {action_data}")
                async with httpx.AsyncClient() as client:
                    await client.post(f"http://localhost:8000/api/v1/looney-tunes/trigger-action", json=action_data, timeout=5.0)
        except Exception as e:
            logger.error(f"[AVA-CPO] Failed to process news for expressive action: {e}", exc_info=True)


class PhiAgent(PrivCSuiteAgent):
    """
    CTO Persona (INTJ-T): Oversees systems engineering, AI orchestration, and threat modeling.
    """
    def __init__(self, **kwargs):
        super().__init__(agent_id="PHI-CTO", role="Chief Technology Officer", **kwargs)

    async def handle_directive(self, message: AgentMessage):
        if message.message_type == MessageType.SYSTEM_ALERT and "security_threat_detected" in message.payload:
            threat_details = message.payload["security_threat_detected"]
            logger.info(f"[PHI-CTO] Coordinating response to a detected security threat: {threat_details.get('type')}")
            self.policy_compiler.activate_policy("LOCKDOWN_EXTERNAL_APIS")
            logger.info("[PHI-CTO] Activated LOCKDOWN_EXTERNAL_APIS policy.")
            mpeti_task = {
                "type": "github_issue_opened",
                "priority": "critical",
                "description": f"Urgent security patch required for vulnerability: {threat_details.get('vulnerability_id')}",
                "details": threat_details
            }
            await self.broker.publish_message(
                "mpeti_tasks",
                 AgentMessage(sender_id=self.agent_id, message_type=MessageType.TASK, payload=mpeti_task)
            )

class TarkAgent(PrivCSuiteAgent):
    """
    CLO Persona (ESTJ-A): Manages regulatory law, IP protection, and multi-jurisdictional alignment.
    """
    def __init__(self, **kwargs):
        super().__init__(agent_id="TARK-CLO", role="Chief Legal Officer", **kwargs)

    async def handle_directive(self, message: AgentMessage):
        if message.message_type == MessageType.DATA_INSIGHT and "new_legal_document" in message.payload:
            document = message.payload["new_legal_document"]
            doc_text = document.get("full_text", "")
            jurisdiction = document.get("jurisdiction", "GLOBAL")
            logger.info(f"[TARK-CLO] Analyzing new legal document for {jurisdiction} to generate compliance rule.")
            
            if not self.llm_client or not await self.llm_client.is_initialized():
                logger.error("[TARK-CLO] LLM client not available for legal analysis.")
                return

            prompt = f"""
            Analyze the following legal document text from the {jurisdiction} jurisdiction.
            Extract the core compliance requirement and formulate it as a machine-readable rule in JSON format.
            The JSON output must contain: 'rule_id', 'description', and 'conditions' as a Python-like string.
            Example condition: "trade_volume <= 1000000 and asset_class != 'crypto'"
            Document Text: --- {doc_text} ---
            """
            
            try:
                llm_response = await self.llm_client.generate_content(prompt, temperature=0.2)
                clean_response = llm_response.strip().replace("```json", "").replace("```", "")
                rule_json = json.loads(clean_response)

                if not all(k in rule_json for k in ['rule_id', 'description', 'conditions']):
                    raise ValueError("LLM response missing required rule keys.")

                new_rule = {
                    "rule_id": f"REG_{jurisdiction}_{rule_json['rule_id']}",
                    "jurisdiction": jurisdiction,
                    "description": rule_json['description'],
                    "conditions": rule_json['conditions']
                }
                
                self.compliance_engine.load_rules([new_rule], append=True)
                logger.info(f"[TARK-CLO] New compliance rule {new_rule['rule_id']} has been successfully generated and loaded into the ComplianceEngine.")

            except json.JSONDecodeError:
                logger.error(f"[TARK-CLO] Failed to decode JSON from LLM response. Response: {llm_response}")
            except Exception as e:
                logger.error(f"[TARK-CLO] Error during AI-driven legal analysis: {e}", exc_info=True)
