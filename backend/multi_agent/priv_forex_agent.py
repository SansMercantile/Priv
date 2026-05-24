# backend/multi_agent/priv_forex_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import TradeProposal, TradeAction, AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivForexAgent(PrivAgent):
    """
    A specialized agent with deep expertise in Forex markets. It analyzes
    interest rate differentials, central bank policies, and carry trade opportunities.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.FOREX, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        # Optional: store latest central bank stance and FX rates
        self.latest_central_bank_data: Dict[str, Any] = {}
        self.latest_fx_rates: Dict[str, float] = {}
        logger.info(f"Priv Forex Agent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        # Subscribe to central bank announcements and interest rate data
        await self.message_broker.subscribe_to_topic(
            "central_bank_news",
            self._handle_central_bank_news,
            f"{self.agent_id}-cbank-sub"
        )
        logger.info(f"PrivForexAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivForexAgent '{self.agent_id}' stopped.")

    async def _handle_central_bank_news(self, message_payload: Dict[str, Any]):
        """Analyzes central bank news to generate proposals."""
        news = message_payload.get('payload', {})
        central_bank = news.get('central_bank')  # e.g., "FED", "ECB"
        stance = news.get('stance')              # "hawkish" or "dovish"
        currency = news.get('currency')          # "USD", "EUR"

        if not all([central_bank, stance, currency]):
            return

        logger.info(f"Forex Agent: Detected {stance} stance from {central_bank} for {currency}.")

        # Store latest stance
        self.latest_central_bank_data[currency] = {
            "central_bank": central_bank,
            "stance": stance,
            "timestamp": news.get("timestamp")
        }

        # Simple logic: Hawkish is bullish for the currency, Dovish is bearish.
        action = TradeAction.BUY if stance == "hawkish" else TradeAction.SELL

        proposal = TradeProposal(
            agent_id=self.agent_id,
            symbol=f"{currency}USD" if currency != "USD" else f"EUR{currency}",  # Conceptual pair
            action=action,
            volume=0.5,
            reasoning=f"Fundamental analysis of {central_bank}'s {stance} stance.",
            confidence=0.8,
            risk_assessment={"strategy": "central_bank_policy"}
        )

        # Publish the proposal
        await self.broker.publish_message("trade_proposals", proposal.model_dump())
