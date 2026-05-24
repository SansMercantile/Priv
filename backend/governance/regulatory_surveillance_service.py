# backend/governance/regulatory_surveillance_service.py
# New standalone service for real-time regulatory surveillance.
# Fulfills the "Real-time Regulatory Surveillance" roadmap item.

import logging
import asyncio
from typing import Dict, Any

from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
from backend.config import settings
# We can reuse the existing ComplianceEngine for post-trade checks
from backend.governance.regulatory_compliance import ComplianceEngine, ComplianceStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegulatorySurveillanceService:
    """
    Monitors all trade activities in real-time to ensure ongoing compliance
    with loaded regulatory frameworks (e.g., JRPPI).
    """
    def __init__(self):
        self.compliance_engine = ComplianceEngine()
        self.broker = GoogleCloudPubSubBroker(broker_config={"project_id": settings.GCP_PROJECT_ID})
        # This service subscribes to a topic where successfully executed trades are published.
        self.trade_execution_topic = "trade_executions"
        logger.info("RegulatorySurveillanceService initialized.")

    async def on_trade_executed(self, message: Dict[str, Any]):
        """
        Callback to process and check every executed trade against compliance rules.
        This serves as a secondary, post-facto check.
        """
        logger.info(f"Performing surveillance check on executed trade: {message}")
        
        # The ComplianceEngine's check_trade_decision requires a context.
        # We can build a mock context from the trade message.
        trade_context = {
            "account_type": message.get("account_type", "pro"),
            "jurisdiction": message.get("jurisdiction", "JP"), # Default to Japan for JRPPI
            "risk_appetite": "surveillance_check", # Use a specific context identifier
        }

        # Reuse the compliance engine to check the executed trade.
        compliance_result = await self.compliance_engine.check_trade_decision(
            action=message.get("action"),
            symbol=message.get("symbol"),
            volume=message.get("volume", 0.0),
            context=trade_context
        )
        
        # If the executed trade is found to be non-compliant by the surveillance service,
        # it indicates a potential failure in the pre-trade checks or a rule update.
        if compliance_result.status != ComplianceStatus.COMPLIANT.value:
            await self.trigger_alert(message, compliance_result)

    async def trigger_alert(self, trade: Dict[str, Any], result):
        """
        Triggers a compliance alert for a potentially non-compliant executed trade.
        """
        alert_message = {
            "alert_type": "REGULATORY_SURVEILLANCE",
            "trade_details": trade,
            "compliance_result": result.model_dump(),
            "timestamp": asyncio.get_event_loop().time()
        }
        logger.critical(f"REGULATORY ALERT: An executed trade may have violated compliance rules! {alert_message}")
        
        # Publish to a high-priority compliance alert topic
        alert_topic = "compliance-alerts"
        await self.broker.publish_message(alert_topic, alert_message)
        logger.info(f"Published compliance alert to topic '{alert_topic}'.")

    async def start(self):
        """Connects to the broker and subscribes to topics."""
        await self.broker.connect()
        await self.broker.subscribe_to_topic(self.trade_execution_topic, self.on_trade_executed, "-surveillance-sub")
        logger.info(f"RegulatorySurveillanceService started, monitoring topic '{self.trade_execution_topic}'.")

    async def stop(self):
        """Disconnects from the message broker."""
        await self.broker.disconnect()
        logger.info("RegulatorySurveillanceService stopped.")


async def main():
    """Main function to run the service."""
    service = RegulatorySurveillanceService()
    await service.start()
    try:
        # Keep the service running indefinitely
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("RegulatorySurveillanceService shutting down.")
    finally:
        await service.stop()

if __name__ == "__main__":
    # This service would be run in its own container.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("RegulatorySurveillanceService stopped by user.")
