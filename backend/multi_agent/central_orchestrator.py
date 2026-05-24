# priv/backend/multi_agent/central_orchestrator.py

import asyncio
import logging
from typing import Dict, Any, Optional
import json

from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker, MessageBrokerInterface
from backend.multi_agent.trade_agent_orchestrator import TradeAgentOrchestrator
# Lazy import to avoid circular dependency
DepartmentalOrchestrator = None

def get_departmental_orchestrator():
    """Lazy import of DepartmentalOrchestrator to avoid circular imports."""
    global DepartmentalOrchestrator
    if DepartmentalOrchestrator is None:
        from backend.multi_agent.departmental_orchestrator import DepartmentalOrchestrator as DO
        DepartmentalOrchestrator = DO
    return DepartmentalOrchestrator
from backend.utils.watchdog import Watchdog
from backend.multi_agent.dynamic_threat_detector import DynamicThreatDetector, ThreatEvent
from backend.governance.ethical_framework import EthicalScaffoldingManager
from backend.governance.regulatory_compliance import ComplianceEngine
from backend.governance.tokenization.zk_verifier import ZKVerifier
from backend.config import settings

logger = logging.getLogger(__name__)

class CentralOrchestrator:
    """
    The top-level orchestrator for the entire multi-agent system.
    Manages global services, coordinates between specialized orchestrators
    (TradeAgentOrchestrator, DepartmentalOrchestrator), and handles system-wide events.
    """
    # UPDATED the __init__ method signature
    def __init__(self, db_instance: Optional[Any], message_broker: MessageBrokerInterface, zk_verifier: ZKVerifier):
        """
        Initializes the CentralOrchestrator.

        Args:
            db_instance: The Firestore database instance for the Watchdog.
            message_broker: The message broker instance for the Watchdog and other components.
            zk_verifier: The ZK-Proof verifier instance.
        """
        self.message_broker_interface = message_broker
        self.zk_verifier = zk_verifier # <-- STORE the zk_verifier
        
        # Initialize cross-cutting services
        self.watchdog = Watchdog(db_instance=db_instance, message_broker=self.message_broker_interface)
        self.dynamic_threat_detector = DynamicThreatDetector(self.message_broker_interface)
        self.ethical_scaffolding_manager = EthicalScaffoldingManager()
        self.compliance_engine = ComplianceEngine()

        # Initialize specialized orchestrators
        # UPDATED to pass the zk_verifier to the TradeAgentOrchestrator
        self.trade_orchestrator = TradeAgentOrchestrator(self.message_broker_interface, self.zk_verifier)
        self.departmental_orchestrator = get_departmental_orchestrator()(self.message_broker_interface, self.zk_verifier)

        # State management
        self.is_running = False
        self.processing_task = None
        logger.info("Central Orchestrator initialized.")

    async def start(self):
        """Starts the central orchestrator and all its managed components."""
        if self.is_running:
            logger.warning("Central Orchestrator is already running.")
            return

        self.is_running = True
        logger.info("Starting Central Orchestrator...")

        # Message broker is now connected in main.py lifespan, so we don't connect here.
        # await self.message_broker_interface.connect()
        # logger.info("Central Orchestrator connected global message broker.")

        # Start cross-cutting services
        await self.watchdog.start_monitoring()
        await self.dynamic_threat_detector.start_monitoring()
        logger.info("Central Orchestrator started watchdog and threat detector.")

        # Start specialized orchestrators
        await self.trade_orchestrator.start()
        await self.departmental_orchestrator.start()
        logger.info("Central Orchestrator started specialized orchestrators.")

        # Start listening for system-wide messages
        self.processing_task = asyncio.create_task(self._listen_for_system_messages())
        logger.info("Central Orchestrator fully operational.")

    async def stop(self):
        """Stops the central orchestrator and all its managed components."""
        if not self.is_running:
            logger.warning("Central Orchestrator is not running.")
            return

        self.is_running = False
        logger.info("Stopping Central Orchestrator...")

        # Stop specialized orchestrators
        await self.trade_orchestrator.stop()
        await self.departmental_orchestrator.stop()
        logger.info("Central Orchestrator stopped specialized orchestrators.")

        # Stop cross-cutting services
        await self.watchdog.stop_monitoring()
        await self.dynamic_threat_detector.stop_monitoring()
        logger.info("Central Orchestrator stopped watchdog and threat detector.")

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                logger.info("Central Orchestrator processing task cancelled.")

        # Disconnect is handled in main.py lifespan
        # await self.message_broker_interface.disconnect()
        # logger.info("Central Orchestrator disconnected global message broker.")
        logger.info("Central Orchestrator stopped.")

    async def _listen_for_system_messages(self):
        """
        Listens for system-wide messages (e.g., system status, threat events)
        that require central coordination or logging.
        """
        system_status_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/system_status_updates-sub"
        threat_events_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/threat_events-sub"
        critical_logs_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/mpeti-critical-logs-sub"

        async def system_status_callback(message):
            try:
                status_update = json.loads(message.data.decode('utf-8'))
                logger.info(f"Central Orchestrator received system status update: {status_update.get('component')} - {status_update.get('status')}")
                # Central Orchestrator can decide on system-wide reactions or simply log
                await message.ack()
            except Exception as e:
                logger.error(f"Error handling central system status update: {e}", exc_info=True)
                await message.nack()

        async def threat_event_callback(message):
            try:
                threat_event = ThreatEvent.parse_raw(message.data)
                logger.warning(f"Central Orchestrator received threat event: {threat_event.threat_type.value} - {threat_event.threat_level.value}")
                # Central Orchestrator can coordinate high-level threat responses
                # or delegate to specialized security agents via DepartmentalOrchestrator
                await message.ack()
            except Exception as e:
                logger.error(f"Error handling central threat event: {e}", exc_info=True)
                await message.nack()

        async def critical_logs_callback(message):
            try:
                log_entry = json.loads(message.data.decode('utf-8'))
                logger.error(f"Central Orchestrator received critical log: {log_entry.get('component')} - {log_entry.get('details')}")
                # Central Orchestrator can decide on further escalation or notification
                await message.ack()
            except Exception as e:
                logger.error(f"Error handling central critical log: {e}", exc_info=True)
                await message.nack()

        await self.message_broker_interface.subscribe(system_status_sub, system_status_callback)
        await self.message_broker_interface.subscribe(threat_events_sub, threat_event_callback)
        await self.message_broker_interface.subscribe(critical_logs_sub, critical_logs_callback)

        while self.is_running:
            await asyncio.sleep(1)


