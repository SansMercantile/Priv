# backend/multi_agent/priv_social_media_agent.py

import logging
from typing import Dict, Any, Optional
from .priv_agent import PrivAgent
from .priv_agent_protocol import TradeProposal, TradeAction, AgentType
from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivSocialMediaAgent(PrivAgent):
    """
    A specialized agent that monitors social media platforms (e.g., Twitter, Reddit)
    for shifts in public sentiment and emerging trends related to financial assets.
    """

    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.SOCIAL_MEDIA, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        # Optional: track aggregated sentiment like PrivSentimentAgent
        self.aggregated_sentiment: Dict[str, Any] = {
            "overall": "neutral",
            "score": 0.0,
            "last_update": None
        }
        # Optional: store latest market data for symbols of interest
        self.latest_market_data: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Priv SocialMediaAgent '{self.agent_id}' initialized.")

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        # Subscribe to a data stream from a social media aggregator
        await self.message_broker.subscribe_to_topic(
            "social_media_trends",
            self._handle_trend,
            f"{self.agent_id}-social-sub"
        )
        logger.info(f"PrivSocialMediaAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivSocialMediaAgent '{self.agent_id}' stopped.")

    async def _handle_trend(self, message_payload: Dict[str, Any]):
        """Analyzes a social media trend and may generate a proposal."""
        trend = message_payload.get('payload', {})
        symbol = trend.get('symbol')
        mention_velocity = trend.get('mention_velocity')  # e.g., mentions per hour change
        sentiment_score = trend.get('sentiment_score')    # e.g., -1 to 1

        if not all([symbol, mention_velocity, sentiment_score]):
            return

        logger.info(
            f"Social Media Agent: Detected trend for {symbol}. "
            f"Velocity: {mention_velocity:.2f}%, Sentiment: {sentiment_score:.2f}"
        )

        # If a stock is trending rapidly with positive sentiment, propose a speculative buy
        if mention_velocity > 50 and sentiment_score > 0.7:
            proposal = TradeProposal(
                agent_id=self.agent_id,
                symbol=symbol,
                action=TradeAction.BUY,
                volume=0.05,  # Small volume for speculative trades
                reasoning=(
                    f"High positive social media momentum detected. "
                    f"Mention velocity: {mention_velocity:.2f}%, "
                    f"Sentiment: {sentiment_score:.2f}"
                ),
                confidence=0.65,
                risk_assessment={
                    "strategy": "social_momentum",
                    "source": "alternative_data"
                }
            )
            # Publish the proposal
            await self.broker.publish_message("trade_proposals", proposal.model_dump())