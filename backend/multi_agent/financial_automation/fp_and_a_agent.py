# backend/multi_agent/financial_automation/fp_and_a_agent.py

import logging
from datetime import datetime
from typing import Dict, Any
from ..priv_agent import PrivAgent
from ..message_broker_interface import MessageBrokerInterface
from ..priv_agent_protocol import AgentMessage, MessageType

logger = logging.getLogger(__name__)

class FPandAAgent(PrivAgent):
    """
    Specialized agent for Financial Planning & Analysis. It listens to
    financial events and generates forecasts or budget variance reports.
    """
    def __init__(self, agent_id: str, broker: MessageBrokerInterface, persona: Dict[str, Any]):
        super().__init__(agent_id, broker, persona)

    async def start(self):
        if self.is_running: return
        self.is_running = True
        # This agent listens to a wide range of financial data
        await self.broker.subscribe_to_topic("payment_status", self._handle_financial_event, f"{self.agent_id}-fpa-sub")
        await self.broker.subscribe_to_topic("expense_report_status", self._handle_financial_event, f"{self.agent_id}-fpa-sub2")
        logger.info(f"FPandAAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"FPandAAgent '{self.agent_id}' stopped.")

    async def _handle_financial_event(self, message_payload: Dict[str, Any]):
        """On any major financial event, run a new forecast."""
        logger.info(f"FP&A Agent: Detected financial event: {message_payload}. Triggering forecast update.")
        
        # In a real system, this would pull data from an accounting system
        # and run a forecasting model.
        forecast = {
            "forecast_id": f"forecast_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            "quarter": "Q3 2025",
            "projected_revenue": 1250000.00,
            "projected_expenses": 800000.00,
            "notes": "Forecast updated due to recent expense approvals and payments."
        }
        
        forecast_msg = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            payload=forecast
        )
        await self.broker.publish_message("financial_forecasts", forecast_msg.model_dump())
