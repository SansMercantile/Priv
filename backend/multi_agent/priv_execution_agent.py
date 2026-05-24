import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, AgentType
from backend.trading_engine.broker_router import BrokerRouter 
from backend.multi_agent.message_broker_interface import MessageBrokerInterface

logger = logging.getLogger(__name__)

class PrivExecutionAgent(PrivAgent):
    """
    A specialized Priv Agent focused on optimal trade execution.
    This agent subscribes to final arbitration decisions and simulates executing trades.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Any, persona: Dict[str, Any], broker_router: Optional[BrokerRouter] = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.EXECUTION, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.broker_router = broker_router 
        self.is_running = False
        logger.info(f"Priv Execution Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the execution agent, subscribing to arbitration decisions."""
        if self.is_running:
            logger.warning(f"Execution Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to final arbitration decisions (approved trades)
        await self.message_broker.subscribe_to_topic("arbitration_decisions", self._handle_arbitration_decision_for_execution, f"{self.agent_id}-arbitration-decisions-sub")
        self.is_running = True
        logger.info(f"Execution Agent '{self.agent_id}' started and subscribed to 'arbitration_decisions'.")

    async def stop(self):
        """Stops the execution agent."""
        if not self.is_running:
            logger.warning(f"Execution Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Execution Agent '{self.agent_id}' stopped.")

    async def _handle_arbitration_decision_for_execution(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming arbitration decisions and trigger trade execution.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            decision = agent_message.payload # Assuming payload is the arbitration result dict

            action = decision.get("action")
            symbol = decision.get("symbol")
            volume = decision.get("volume")
            entry_price = decision.get("entry_price") # Assuming these are passed in decision
            arbitration_outcome = decision.get("arbitration_outcome")

            if arbitration_outcome == "APPROVED" and action in [TradeAction.BUY.value, TradeAction.SELL.value]:
                logger.info(f"Execution Agent '{self.agent_id}' received APPROVED decision for {action} {volume} of {symbol}.")
                
                # --- Conceptual Execution Logic ---
                # In a real system, this would involve:
                # 1. Selecting the optimal broker/adapter from self.broker_router.
                # 2. Implementing smart order routing (SOR) logic.
                # 3. Sending the order to the chosen broker adapter.
                # 4. Monitoring order status and handling fills/partial fills.

                if self.broker_router:
                    logger.info(f"Execution Agent '{self.agent_id}': Attempting to send order via BrokerRouter (conceptual).")
                    # In a real scenario:
                    # order_id = await self.broker_router.send_order(action, symbol, volume, price=entry_price)
                    # if order_id:
                    #     logger.info(f"Execution Agent: Order sent to broker, ID: {order_id}")
                    #     # Publish execution confirmation
                    # else:
                    #     logger.error("Execution Agent: Failed to send order.")
                else:
                    logger.info(f"Execution Agent '{self.agent_id}': Simulating execution of {action} {volume} of {symbol} at {entry_price}.")
                
                # Publish an execution confirmation message
                execution_confirmation = {
                    "trade_id": f"exec-{symbol}-{datetime.now().timestamp()}",
                    "symbol": symbol,
                    "action": action,
                    "volume": volume,
                    "status": "SIMULATED_EXECUTED",
                    "execution_time": datetime.now().isoformat(),
                    "arbitration_decision_id": decision.get("proposal_id") # Link to original decision
                }
                await self.broker.publish_message("trade_executions", AgentMessage(sender_id=self.agent_id, message_type=MessageType.DECISION_CONFIRMATION, payload=execution_confirmation).model_dump())
                logger.info(f"Execution Agent '{self.agent_id}' published execution confirmation for {symbol}.")
            else:
                logger.info(f"Execution Agent '{self.agent_id}' received non-executable decision: {action} {symbol} (Outcome: {arbitration_outcome}).")

        except Exception as e:
            logger.error(f"Execution Agent '{self.agent_id}': Error processing arbitration decision for execution: {e}", exc_info=True)

# Example Usage (for testing PrivExecutionAgent in isolation)
async def main_execution_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    # from backend.trading_engine.broker_router import BrokerRouter # Uncomment if you have a real BrokerRouter

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    # broker_router = BrokerRouter() # Instantiate if you have a real BrokerRouter
    execution_agent = PrivExecutionAgent(
        agent_id="Priv-Execution",
        broker=broker,
        persona={"name": "Execution Specialist", "focus": "Optimal Trade Execution", "role": "execution_specialist"},
        # broker_router=broker_router # Pass the real broker router here
    )

    await broker.connect()
    await execution_agent.start()

    # Simulate an approved arbitration decision
    mock_approved_decision = AgentMessage(
        sender_id="ArbitrationEngine",
        message_type=MessageType.DECISION_CONFIRMATION,
        payload={
            "action": TradeAction.BUY.value, # Must be string for JSON
            "symbol": "TSLA",
            "volume": 0.01,
            "entry_price": 200.00,
            "arbitration_outcome": "APPROVED",
            "reasoning": "Consensus reached."
        }
    )
    mock_rejected_decision = AgentMessage(
        sender_id="ArbitrationEngine",
        message_type=MessageType.DECISION_CONFIRMATION,
        payload={
            "action": TradeAction.SELL.value,
            "symbol": "GOOG",
            "volume": 0.05,
            "arbitration_outcome": "REJECTED",
            "reasoning": "Risk limit exceeded."
        }
    )

    logger.info("\n--- Simulating arbitration decisions for Execution Agent to process ---")
    await broker.publish_message("arbitration_decisions", mock_approved_decision.model_dump())
    await asyncio.sleep(1)
    await broker.publish_message("arbitration_decisions", mock_rejected_decision.model_dump())
    await asyncio.sleep(3) # Give time for execution agent to process

    await execution_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivExecutionAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_execution_agent_test())
