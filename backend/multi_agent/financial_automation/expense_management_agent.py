# backend/multi_agent/financial_automation/expense_management_agent.py

import logging
from typing import Dict, Any
from ..priv_agent import PrivAgent
from ..message_broker_interface import MessageBrokerInterface
from ..priv_agent_protocol import AgentMessage, MessageType

logger = logging.getLogger(__name__)

class ExpenseManagementAgent(PrivAgent):
    """
    Specialized agent for managing employee expense reports.
    """
    def __init__(self, agent_id: str, broker: MessageBrokerInterface, persona: Dict[str, Any]):
        super().__init__(agent_id, broker, persona)

    async def start(self):
        if self.is_running: return
        self.is_running = True
        await self.broker.subscribe_to_topic("expense_reports_submitted", self._handle_expense_report, f"{self.agent_id}-expenses-sub")
        logger.info(f"ExpenseManagementAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"ExpenseManagementAgent '{self.agent_id}' stopped.")

    async def _handle_expense_report(self, message_payload: Dict[str, Any]):
        """Processes a submitted expense report."""
        report = message_payload.get('payload', {})
        report_id = report.get('report_id')
        employee = report.get('employee')
        amount = report.get('amount')
        
        logger.info(f"Expense Agent: Reviewing expense report {report_id} from {employee} for ${amount}.")
        
        # Apply rules (e.g., amounts > $1000 need manager approval)
        status = "APPROVED"
        notes = "Expense report is within policy and auto-approved."
        if amount > 1000:
            status = "NEEDS_MANAGER_APPROVAL"
            notes = "Amount exceeds auto-approval limit. Forwarded to manager."

        approval_msg = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            payload={"report_id": report_id, "status": status, "notes": notes}
        )
        await self.broker.publish_message("expense_report_status", approval_msg.model_dump())
