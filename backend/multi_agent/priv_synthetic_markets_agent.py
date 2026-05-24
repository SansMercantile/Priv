# backend/multi_agent/priv_synthetic_markets_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import TradeProposal, TradeAction, AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivSyntheticMarketsAgent(PrivAgent):
    """
    A specialized agent that focuses on analyzing and trading synthetic indices
    like Volatility Indices (VIX, V100), Boom/Crash, and Step Indices.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.SYNTHETIC_MARKETS, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        logger.info(f"Priv Synthetic Markets Agent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        await self.broker.subscribe_to_topic(
            "synthetic_market_data",
            self._handle_data,
            f"{self.agent_id}-synth-sub"
        )
        logger.info(f"PrivSyntheticMarketsAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivSyntheticMarketsAgent '{self.agent_id}' stopped.")

    async def _handle_data(self, message_payload: Dict[str, Any]):
        """Analyzes incoming data for synthetic markets."""
        data = message_payload.get('payload', {})
        symbol = data.get('symbol')
        price = data.get('price')

        if not symbol or not price:
            return

        proposal = None
        if "Boom" in symbol and data.get('momentum_score', 0) > 0.8:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=TradeAction.BUY,
                volume=0.1,
                reasoning=f"Strong upward momentum detected in {symbol}.",
                confidence=0.75,
                risk_assessment={"strategy": "synthetic_momentum"}
            )
        elif "Crash" in symbol and data.get('momentum_score', 0) < -0.8:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=TradeAction.SELL,
                volume=0.1,
                reasoning=f"Strong downward momentum detected in {symbol}.",
                confidence=0.75,
                risk_assessment={"strategy": "synthetic_momentum"}
            )

        if proposal:
            # Publish the proposal to the message broker
            from .priv_agent_protocol import AgentMessage, MessageType
            proposal_message = AgentMessage(
                sender_id=self.agent_id,
                message_type=MessageType.TRADE_PROPOSAL,
                payload=proposal.model_dump()
            )
            await self.message_broker.publish_message("trade_proposals", proposal_message.model_dump())
            logger.info(f"Synthetic Agent published proposal for {symbol} to message broker")