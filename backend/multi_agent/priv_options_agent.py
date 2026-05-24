# backend/multi_agent/priv_options_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import TradeProposal, TradeAction, MessageType, AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivOptionsAgent(PrivAgent):
    """
    A specialized agent for analyzing and proposing trades in the options market.
    """

    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.OPTIONS, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        # Optional: track latest volatility data or option chain snapshots
        self.latest_volatility_data: Dict[str, Any] = {}
        logger.info(f"Priv Options Agent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        # Subscribe to volatility index updates or specific stock price alerts
        await self.message_broker.subscribe_to_topic(
            "volatility_index_updates",
            self._handle_volatility_update,
            f"{self.agent_id}-vol-sub"
        )
        logger.info(f"PrivOptionsAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivOptionsAgent '{self.agent_id}' stopped.")

    async def _handle_volatility_update(self, message_payload: Dict[str, Any]):
        """Analyzes market volatility to propose option strategies."""
        volatility_data = message_payload.get('payload', {})
        vix_level = volatility_data.get('vix_price')

        if not vix_level:
            return

        logger.info(f"Options Agent: Market volatility (VIX) is at {vix_level}.")

        # If volatility is high, propose selling options (e.g., covered call)
        if vix_level > 25:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol="SPY_CALL_OTM",  # Conceptual symbol for an out-of-the-money SPY call
                action=TradeAction.SELL,
                volume=1,
                reasoning=(
                    f"High market volatility (VIX: {vix_level}) makes selling "
                    "options premium attractive."
                ),
                confidence=0.7,
                risk_assessment={"strategy": "covered_call_high_iv"}
            )
            # Publish the proposal
            await self.broker.publish_message("trade_proposals", proposal.model_dump())
