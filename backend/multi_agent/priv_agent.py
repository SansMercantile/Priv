
# priv/backend/multi_agent/priv_agent.py
import asyncio
import logging
from typing import Optional, Dict, Any, List
import json
import os
try:
    from backend.utils.llm_client_loader import LLMClient
except ImportError:
    class LLMClient:
        def __init__(self, *args, **kwargs):
            pass
        def explain(self, input_text: str) -> str:
            return f"[Mock LLMClient] {input_text}"


try:
    from backend.config import settings
    _ = settings.INTER_AGENT_COMMUNICATION_TOPIC
except (ImportError, AttributeError):
    from backend.config import settings
from backend.multi_agent.priv_agent_protocol import AgentType, AgentState, AgentMessage, TradeProposal, ArbitrationVote
from backend.trading_engine.broker_interface import BrokerInterface
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
# LLMClient is loaded above with a mock fallback for tests/demos

logger = logging.getLogger(__name__)

class PrivAgent:
    """
    Base class for all specialized Priv agents.
    Includes foundational methods for communication, state management,
    adaptive learning, resiliency skills, and transparency.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface] = None, persona: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.persona = persona or {}
        self.state = AgentState.IDLE
        self.is_running = False
        self.message_broker = message_broker
        self.broker = broker
        self.task_queue = asyncio.Queue()
        self.processing_task = None
        self.inherited_healing_protocols: List[str] = [] # To store inherited protocols
        self.inherited_governance_rules: List[str] = [] # To store inherited rules
        # Robust sandbox/test fallback for GCP_PROJECT_ID
        import os
        _is_test = os.getenv('DEMO_MODE', 'false').lower() == 'true' or os.getenv('SANDBOX_MODE', 'false').lower() == 'true' or 'pytest' in __import__('sys').argv[0]
        gcp_project_id = getattr(settings, 'GCP_PROJECT_ID', None)
        if gcp_project_id is None and _is_test:
            gcp_project_id = 'sandbox-project'
        self.llm_client = LLMClient(project_id=gcp_project_id)
        logger.info(f"PrivAgent {self.agent_id} ({self.agent_type.value}) initialized.")

    async def start(self):
        """Starts the agent's operation."""
        if self.is_running:
            logger.warning(f"Agent {self.agent_id} is already running.")
            return

        self.is_running = True
        self.state = AgentState.ACTIVE
        self.processing_task = asyncio.create_task(self._process_messages())
        logger.info(f"Agent {self.agent_id} started.")

    async def stop(self):
        """Stops the agent's operation."""
        if not self.is_running:
            logger.warning(f"Agent {self.agent_id} is not running.")
            return

        self.is_running = False
        self.state = AgentState.SHUTTING_DOWN
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                logger.info(f"Agent {self.agent_id} processing task cancelled.")
        self.state = AgentState.IDLE
        logger.info(f"Agent {self.agent_id} stopped.")

    async def send_message(self, recipient_id: str, message_type: str, payload: Dict[str, Any]):
        """Sends a message to another agent or topic via the message broker."""
        msg = AgentMessage(
            sender_id=self.agent_id,
            sender_type=self.agent_type,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload
        )
        topic = getattr(settings, 'INTER_AGENT_COMMUNICATION_TOPIC', 'priv-inter-agent-comm')
        await self.message_broker.publish_message(msg.json(), topic)
        logger.debug(f"Agent {self.agent_id} sent message type '{message_type}' to '{recipient_id}'.")

    async def publish_message(self, message_type, payload: Dict[str, Any], topic: str | None = None, recipient_id: str = ""):
        """Convenience wrapper for publishing structured messages.
        - message_type: MessageType or string
        - payload: Dict payload
        - topic: optional explicit topic to publish to
        - recipient_id: optional recipient id for directed messages
        """
        # Lazy import to avoid circular import at module load
        try:
            from backend.multi_agent.priv_agent_protocol import MessageType
        except Exception:
            MessageType = None

        # If an enum MessageType is provided, use its value for a sensible default topic
        if hasattr(message_type, 'value'):
            default_topic = message_type.value.lower()
        else:
            default_topic = str(message_type).lower()

        publish_topic = topic or default_topic or getattr(settings, 'INTER_AGENT_COMMUNICATION_TOPIC', 'priv-inter-agent-comm')

        # Construct AgentMessage in canonical form
        msg = AgentMessage(
            sender_id=self.agent_id,
            sender_type=getattr(self.agent_type, 'value', str(self.agent_type)),
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload
        )

        # MessageBrokerInterface expects (topic, message)
        await self.message_broker.publish_message(publish_topic, msg.model_dump())
        logger.debug(f"Agent {self.agent_id} published message to topic '{publish_topic}': {message_type}")

    async def _process_messages(self):
        """Internal loop to process messages from its queue."""
        logger.info(f"Agent {self.agent_id} message processing loop started.")
        while self.is_running:
            try:
                message = await self.task_queue.get()
                await self.handle_message(message)
                self.task_queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"Agent {self.agent_id} message processing loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Agent {self.agent_id} error processing message: {e}", exc_info=True)
                await asyncio.sleep(1) # Prevent tight loop on errors

    async def handle_message(self, message: AgentMessage):
        """
        Abstract method to be implemented by subclasses for specific message handling logic.
        """
        logger.info(f"Agent {self.agent_id} received message: {message.message_type}")
        pass

    async def _adapt_learning_method(self, feedback: Dict[str, Any]):
        """
        Integrates domain-agnostic adaptive learning methods.
        Contains logic for adjusting the agent's learning strategy or model parameters
        based on performance feedback across tasks.
        """
        logger.info(f"Agent {self.agent_id}: Adapting learning method based on feedback: {feedback}")
        # Example: if performance is low, trigger a re-evaluation of feature sets
        if feedback.get("performance", 1.0) < 0.7:
            logger.warning(f"Agent {self.agent_id}: Low performance detected. Triggering adaptive adjustment.")
            # self.model.adjust_hyperparameters(learning_rate_multiplier=0.9)
            # self.re_evaluate_feature_set()
        else:
            logger.info(f"Agent {self.agent_id}: Performance is satisfactory. Maintaining current learning strategy.")

    async def receive_feedback(self, feedback: Dict[str, Any]):
        """
        Allows other parts of the system or external monitors to provide feedback
        for adaptive learning.
        """
        logger.info(f"Agent {self.agent_id} received feedback: {feedback}")
        await self._adapt_learning_method(feedback)

    async def apply_healing_protocol(self, protocol_name: str, params: Dict[str, Any]):
        """
        Applies a self-healing protocol inherited from MPETI.
        Contains logic to address internal issues, e.g., resetting a faulty module,
        re-initializing a connection.
        """
        logger.info(f"Agent {self.agent_id}: Applying healing protocol '{protocol_name}' with params: {params}")
        if protocol_name in self.inherited_healing_protocols:
            if protocol_name == "reset_connection":
                logger.info(f"Resetting network connection for {self.agent_id}.")
                if self.broker:
                    await self.broker.connect() # Reconnect broker if applicable
            elif protocol_name == "restart_module":
                logger.info(f"Restarting internal module for {self.agent_id}.")
                # Example: Re-initialize a sub-component of the agent
                # self.some_internal_module.reinitialize()
            else:
                logger.warning(f"Unknown healing protocol: {protocol_name}")
        else:
            logger.warning(f"Agent {self.agent_id}: Healing protocol '{protocol_name}' not inherited or recognized.")

    async def evaluate_action_against_governance(self, action_data: Dict[str, Any]) -> bool:
        """
        Evaluates a proposed action against inherited ethical/governance rules.
        """
        logger.info(f"Agent {self.agent_id}: Evaluating action against governance rules: {action_data}")
        # This would typically involve calling the EthicalFramework or ComplianceEngine
        # based on the inherited_governance_rules.
        if "forbidden_symbols" in self.inherited_governance_rules and action_data.get("symbol") in ["XYZ", "ABC"]:
            logger.warning(f"Action for {action_data.get('symbol')} violates inherited governance rule: Forbidden Symbol.")
            return False
        if "max_trade_volume" in self.inherited_governance_rules and action_data.get("volume", 0) > 1000:
            logger.warning(f"Action for {action_data.get('symbol')} violates inherited governance rule: Max Trade Volume.")
            return False
        logger.info(f"Action for {action_data.get('symbol')} passes inherited governance checks.")
        return True

    async def resolve_internal_conflict(self, conflict_details: Dict[str, Any]):
        """
        Initiates an internal conflict resolution process using inherited skills.
        """
        logger.info(f"Agent {self.agent_id}: Initiating internal conflict resolution: {conflict_details}")
        # This might involve:
        # - Adjusting internal priorities
        # - Re-evaluating conflicting data
        # - Requesting arbitration from a higher-level orchestrator/arbiter agent
        logger.info(f"Agent {self.agent_id}: Conflict resolution initiated.")

    async def generate_reasoning_explanation(self, decision_context: Dict[str, Any], decision_outcome: Dict[str, Any]) -> str:
        """
        Generates a human-readable explanation for an agent's decision.
        Uses LLMClient for sophisticated explanation generation.
        """
        logger.info(f"Agent {self.agent_id}: Generating explanation for decision.")
        
        prompt = (
            f"As a {self.agent_type.value} agent, explain the following decision in a concise, human-readable manner.\n"
            f"Decision Context: {json.dumps(decision_context, indent=2)}\n"
            f"Decision Outcome: {json.dumps(decision_outcome, indent=2)}\n"
            f"Focus on the key factors that led to this decision and its expected impact. Avoid technical jargon where possible."
        )
        
        try:
            # Assuming LLMClient.generate_content returns a string
            explanation = await self.llm_client.generate_content(prompt)
            logger.info(f"Generated explanation for {self.agent_id}.")
            return explanation
        except Exception as e:
            logger.error(f"Failed to generate explanation for {self.agent_id}: {e}", exc_info=True)
            return f"Error generating explanation: {e}"

