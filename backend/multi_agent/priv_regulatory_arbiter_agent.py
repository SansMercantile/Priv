# backend/multi_agent/priv_regulatory_arbiter_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import AgentMessage, MessageType, TradeProposal, ArbitrationVote,  AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivRegulatoryArbiterAgent(PrivAgent):
    """
    A specialized governance agent that provides an independent vote on proposals
    based on a loaded set of regulatory rules (e.g., leverage limits, jurisdictional rules).
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any], zk_verifier: Any):
        super().__init__(agent_id=agent_id, agent_type=AgentType.REGULATORY_ARBITER, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.zk_verifier = zk_verifier
        self.regulatory_rules: Dict[str, Any] = {}
        logger.info(f"Priv Regulatory Arbiter Agent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        await self.message_broker.subscribe_to_topic(
            "trade_proposals",
            self._handle_proposal,
            f"{self.agent_id}-proposals-sub"
        )
        logger.info(f"PrivRegulatoryArbiterAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivRegulatoryArbiterAgent '{self.agent_id}' stopped.")

    async def _handle_proposal(self, message_payload: Dict[str, Any]):
        """Receives a trade proposal and casts a regulatory vote."""
        proposal = TradeProposal(**message_payload.get('payload', {}))

        vote = True
        reason = "Proposal is compliant with known regulations."

        # Example compliance check: leverage limits for CFDs
        if "CFD" in proposal.symbol and proposal.risk_assessment.get('leverage', 1) > 30:
            vote = False
            reason = (
                f"Vetoing trade in {proposal.symbol} due to excessive leverage "
                f"({proposal.risk_assessment.get('leverage')}x) which violates retail investor protection rules."
            )
            logger.warning(f"Regulatory Arbiter: Vetoing proposal for {proposal.symbol}.")

        vote_msg = ArbitrationVote(
            proposal_id=f"{proposal.agent_id}-{proposal.symbol}",  # Simplified ID
            voter_id=self.agent_id,
            vote=vote,
            weight=1.0,  # Regulatory votes are non-negotiable
            reason=reason
        )

        final_msg = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ARBITRATION_VOTE,
            payload=vote_msg.model_dump()
        )
        await self.broker.publish_message("arbitration_votes", final_msg.model_dump())