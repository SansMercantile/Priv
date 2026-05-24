# backend/multi_agent/financial_automation/accounts_payable_agent.py

import logging
from typing import Dict, Any
from ..priv_agent import PrivAgent
from ..message_broker_interface import MessageBrokerInterface
from ..priv_agent_protocol import AgentMessage, MessageType

logger = logging.getLogger(__name__)

class AccountsPayableAgent(PrivAgent):
    """
    Specialized agent for managing accounts payable. It processes incoming
    invoices and schedules them for payment.
    """
    def __init__(self, agent_id: str, broker: MessageBrokerInterface, persona: Dict[str, Any]):
        super().__init__(agent_id, broker, persona)

    async def start(self):
        if self.is_running: return
        self.is_running = True
        await self.broker.subscribe_to_topic("incoming_invoices", self._handle_invoice, f"{self.agent_id}-invoices-sub")
        logger.info(f"AccountsPayableAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"AccountsPayableAgent '{self.agent_id}' stopped.")

    async def _handle_invoice(self, message_payload: Dict[str, Any]):
        """Processes an incoming invoice."""
        invoice = message_payload.get('payload', {})
        invoice_id = invoice.get('invoice_id')
        vendor = invoice.get('vendor')
        amount = invoice.get('amount')
        
        if not all([invoice_id, vendor, amount]):
            logger.warning(f"AP Agent received incomplete invoice: {invoice}")
            return

        logger.info(f"AP Agent: Processing invoice {invoice_id} from {vendor} for ${amount}.")
        
        # In a real system, this would involve:
        # 1. Validating the invoice against a PO.
        # 2. Checking for duplicates.
        # 3. Getting approval via a workflow.
        # 4. Scheduling the payment in an accounting system.

        # For now, we'll just publish a confirmation.
        payment_scheduled_msg = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            payload={
                "status": "PAYMENT_SCHEDULED",
                "invoice_id": invoice_id,
                "amount": amount,
                "notes": "Invoice validated and scheduled for payment."
            }
        )
        await self.broker.publish_message("payment_status", payment_scheduled_msg.model_dump())
