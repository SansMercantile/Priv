# backend/governance/fraud_detection_service.py
# New standalone service for automated fraud detection.
# Fulfills the "Automated Fraud Detection" roadmap item.

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
from backend.config.settings import Settings

# Create settings instance
_settings = Settings()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FraudDetectionEngine:
    """
    Analyzes transactions and activities for fraudulent patterns.
    This is a conceptual engine. A real-world system would use more sophisticated
    machine learning models and rule engines (e.g., running on Vertex AI).
    """
    def __init__(self):
        # In a real system, these would be configurable and more complex.
        self.high_velocity_threshold = 5  # e.g., 5 transactions
        self.high_velocity_window_seconds = 60 # within 1 minute
        self.unusual_amount_threshold = 100000  # e.g., $100,000
        
        # This is a simple in-memory store for demonstration.
        # A production system MUST use a distributed cache like Redis for this.
        self.activity_log: Dict[str, list[datetime]] = {}
        logger.info("FraudDetectionEngine initialized.")

    async def analyze_transaction(self, transaction_data: Dict[str, Any], broker: GoogleCloudPubSubBroker):
        """
        Analyzes a single transaction for potential fraud.
        """
        user_id = transaction_data.get("user_id", "unknown_user")
        amount = transaction_data.get("amount", 0.0)
        action = transaction_data.get("action", "unknown")
        
        logger.info(f"Analyzing transaction for user '{user_id}': {action} of {amount}")

        # Rule 1: Check for unusually large amounts
        if amount > self.unusual_amount_threshold:
            await self.trigger_alert(
                user_id,
                "UNUSUAL_AMOUNT",
                f"Transaction amount {amount} exceeds threshold {self.unusual_amount_threshold}",
                broker
            )
            
        # Rule 2: Check for high velocity of transactions
        now = datetime.utcnow()
        if user_id not in self.activity_log:
            self.activity_log[user_id] = []
        
        # Add current transaction time and filter out old ones
        self.activity_log[user_id].append(now)
        time_window_start = now - timedelta(seconds=self.high_velocity_window_seconds)
        recent_transactions = [t for t in self.activity_log[user_id] if t > time_window_start]
        self.activity_log[user_id] = recent_transactions
        
        if len(recent_transactions) > self.high_velocity_threshold:
            await self.trigger_alert(
                user_id,
                "HIGH_VELOCITY",
                f"User had {len(recent_transactions)} transactions in the last {self.high_velocity_window_seconds} seconds.",
                broker
            )

    async def trigger_alert(self, user_id: str, fraud_type: str, details: str, broker: GoogleCloudPubSubBroker):
        """
        Triggers a fraud alert by publishing it to a dedicated Pub/Sub topic.
        """
        alert_message = {
            "alert_type": "FRAUD_DETECTION",
            "user_id": user_id,
            "fraud_type": fraud_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.critical(f"FRAUD ALERT: {alert_message}")
        
        # Publish to a high-priority alert topic
        alert_topic = "fraud-alerts"
        await broker.publish_message(alert_topic, alert_message)
        logger.info(f"Published fraud alert to topic '{alert_topic}'.")


class FraudDetectionService:
    """
    The main service that subscribes to topics and uses the engine to detect fraud.
    """
    def __init__(self):
        self.engine = FraudDetectionEngine()
        self.broker = GoogleCloudPubSubBroker(broker_config={"project_id": _settings.GCP_PROJECT_ID})
        # This service would subscribe to topics where financial actions are posted.
        self.transaction_topic = "financial_transactions"

    async def on_transaction(self, message: Dict[str, Any]):
        """Callback for processing messages from the transaction topic."""
        logger.debug(f"Received transaction message: {message}")
        await self.engine.analyze_transaction(message, self.broker)

    async def start(self):
        """Connects to the broker and subscribes to topics."""
        await self.broker.connect()
        await self.broker.subscribe_to_topic(self.transaction_topic, self.on_transaction, "-fraud-sub")
        logger.info(f"FraudDetectionService started, monitoring topic '{self.transaction_topic}'.")

    async def stop(self):
        """Disconnects from the message broker."""
        await self.broker.disconnect()
        logger.info("FraudDetectionService stopped.")


async def main():
    """Main function to run the service."""
    service = FraudDetectionService()
    await service.start()
    try:
        # Keep the service running indefinitely
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("FraudDetectionService shutting down.")
    finally:
        await service.stop()

if __name__ == "__main__":
    # This service would be run in its own container.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("FraudDetectionService stopped by user.")
