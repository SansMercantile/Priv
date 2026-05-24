# backend/multi_agent/priv_tax_agent.py

import logging
from typing import Dict, Any, List, Optional
from .priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentType
from .message_broker_interface import MessageBrokerInterface
from ..financial_automation.sars_tax_reporting import SarsTaxCalculator, Transaction
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivTaxAgent(PrivAgent):
    """
    A specialized agent responsible for monitoring transactions and generating
    tax reports, with a specific focus on SARS (South African Revenue Service) requirements.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.TAX, message_broker=message_broker, broker=broker, persona=persona)
        self.transactions: List[Transaction] = []

    async def start(self):
        if self.is_running: return
        self.is_running = True
        # This agent listens to confirmed trade executions to build its transaction log
        await self.broker.subscribe_to_topic("trade_executions", self._handle_executed_trade, f"{self.agent_id}-executions-sub")
        logger.info(f"PrivTaxAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivTaxAgent '{self.agent_id}' stopped.")

    async def _handle_executed_trade(self, message_payload: Dict[str, Any]):
        """Callback to log a completed trade for tax purposes."""
        try:
            trade = message_payload.get('payload', {})
            # Adapt the trade execution message to the Transaction model
            tx = Transaction(
                asset_name=trade.get('symbol'),
                transaction_type=trade.get('action', '').lower(),
                quantity=trade.get('volume'),
                price_per_unit=trade.get('executed_price'),
                transaction_date=trade.get('execution_time'),
                transaction_costs=trade.get('commission', 0.0)
            )
            self.transactions.append(tx)
            logger.info(f"Tax Agent logged transaction for {tx.asset_name}.")
        except Exception as e:
            logger.error(f"Tax Agent error handling executed trade: {e}", exc_info=True)

    def generate_tax_report(self) -> Dict[str, Any]:
        """
        Generates a SARS-compliant Capital Gains Tax report based on the logged transactions.
        """
        if not self.transactions:
            logger.warning("Tax Agent: No transactions logged, cannot generate report.")
            return {"error": "No transaction data available."}
        
        logger.info("Tax Agent: Generating SARS CGT report...")
        calculator = SarsTaxCalculator(self.transactions)
        report = calculator.generate_sars_report()
        return report
