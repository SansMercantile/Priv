# backend/multi_agent/priv_ethical_arbiter_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import AgentMessage, MessageType, TradeProposal, ArbitrationVote, AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivEthicalArbiterAgent(PrivAgent):
    """
    A specialized governance agent that acts as an arbiter for ethical considerations.
    It provides an independent vote on proposals based on the project's ethical framework.
    """

    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any], zk_verifier: Any):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ETHICAL_ARBITER, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.zk_verifier = zk_verifier
        # Optional: store ethical rules or framework reference
        self.ethical_rules: Dict[str, Any] = {}
        logger.info(f"Priv Ethical Arbiter Agent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        await self.broker.subscribe_to_topic(
            "trade_proposals",
            self._handle_proposal,
            f"{self.agent_id}-proposals-sub"
        )
        logger.info(f"PrivEthicalArbiterAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivEthicalArbiterAgent '{self.agent_id}' stopped.")

    async def _handle_proposal(self, message_payload: Dict[str, Any]):
        """Receives a trade proposal and casts an ethical vote."""
        proposal = TradeProposal(**message_payload.get('payload', {}))

        vote = True
        reason = "Proposal aligns with the established ethical framework."

        # Example: veto trades in controversial industries
        controversial_symbols = ["BIG_OIL_CORP", "WEAPONS_INC"]
        if proposal.symbol in controversial_symbols:
            vote = False
            reason = (
                f"Vetoing trade in {proposal.symbol} due to ethical concerns "
                "regarding the industry."
            )
            logger.warning(f"Ethical Arbiter: Vetoing proposal for {proposal.symbol}.")

        vote_msg = ArbitrationVote(
            proposal_id=f"{proposal.agent_id}-{proposal.symbol}",  # Simplified ID
            voter_id=self.agent_id,
            vote=vote,
            weight=1.0,  # Arbiter votes carry maximum weight
            reason=reason
        )

        final_msg = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ARBITRATION_VOTE,
            payload=vote_msg.model_dump()
        )
        await self.broker.publish_message("arbitration_votes", final_msg.model_dump())
