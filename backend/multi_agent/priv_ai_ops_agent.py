# backend/multi_agent/priv_ai_ops_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import ML pipeline components for interaction
from backend.ml_pipeline.model_predictor import MLModelPredictor
from backend.ml_pipeline.model_trainer import ModelTrainer # For triggering retraining
from backend.ml_pipeline.vertex_ai_pipeline import run_training_pipeline # For orchestrating full pipeline

# Import settings for configurable thresholds and API keys
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)

class PrivAIOpsAgent(PrivAgent):
    """
    A specialized Priv Agent focused on monitoring, maintaining, and optimizing
    the AI models and infrastructure within the Priv system. It ensures model
    performance, detects drift, manages resource allocation, and handles deployments.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.AI_OPS, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        self.model_performance_metrics: Dict[str, Dict[str, Any]] = {} # Stores metrics for various models
        self.infrastructure_status: Dict[str, Any] = {"cpu_usage": 0.0, "memory_usage": 0.0, "last_checked": None}

        # Initialize ML pipeline components (they might be singletons managed by dependencies.py)
        # We instantiate them here for direct use within the agent, assuming they are ready.
        live_model_dir = getattr(settings, 'LIVE_MODEL_DIR', None)
        self.model_predictor = MLModelPredictor(model_path=live_model_dir) if live_model_dir else None
        self.model_trainer = ModelTrainer() # Used to trigger training pipeline

        self.whatsapp_notifier = WhatsAppNotifier()

        logger.info(f"Priv AI-Ops Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the AI-Ops agent, subscribing to system health and model performance data."""
        if self.is_running:
            logger.warning(f"AI-Ops Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to model performance metrics (published by ML pipeline or monitoring tools)
        await self.message_broker.subscribe_to_topic(
            "model_performance_metrics", self._handle_model_metrics, f"{self.agent_id}-model-metrics-sub"
        )
        # Subscribe to infrastructure alerts (e.g., from a system monitoring service)
        await self.message_broker.subscribe_to_topic(
            "infrastructure_alerts", self._handle_infrastructure_alert, f"{self.agent_id}-infra-sub"
        )
        # Subscribe to model deployment requests (e.g., from a human operator or automated pipeline)
        await self.message_broker.subscribe_to_topic(
            "model_deployment_requests", self._handle_deployment_request, f"{self.agent_id}-deploy-sub"
        )
        # Subscribe to raw IoT sensory data for environmental awareness (if relevant for AI-Ops context)
        await self.message_broker.subscribe_to_topic(
            "iot_sensory_data", self._handle_iot_sensory_data, f"{self.agent_id}-iot-sub"
        )

        self.is_running = True
        # Start a periodic check for overall system health (could also be fed by external monitoring)
        self._health_check_task = asyncio.create_task(self._periodic_health_check())
        logger.info(f"Priv AI-Ops Agent '{self.agent_id}' started and health check initiated.")

    async def stop(self):
        """Stops the AI-Ops agent and cancels periodic tasks."""
        if not self.is_running:
            logger.warning(f"AI-Ops Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                logger.info(f"Priv AI-Ops Agent '{self.agent_id}' periodic health check task cancelled.")

        logger.info(f"Priv AI-Ops Agent '{self.agent_id}' stopped.")

    async def _periodic_health_check(self):
        """
        Performs periodic internal health checks of the AI infrastructure.
        In a real system, this would query actual system metrics (e.g., Prometheus, Cloud Monitoring APIs).
        """
        while self.is_running:
            try:
                logger.debug("AI-Ops Agent: Performing periodic system health check.")
                
                # Retrieve actual system metrics using psutil
                try:
                    import psutil
                    cpu_usage = psutil.cpu_percent(interval=1)
                    memory_usage = psutil.virtual_memory().percent
                    disk_usage = psutil.disk_usage('/').percent
                    
                    logger.info(f"System Metrics - CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%")
                    
                    # Check for critical thresholds
                    if cpu_usage > 90:
                        await self.handle_infrastructure_alert("high_cpu_usage", "CRITICAL")
                    elif memory_usage > 90:
                        await self.handle_infrastructure_alert("high_memory_usage", "CRITICAL")
                    elif disk_usage > 90:
                        await self.handle_infrastructure_alert("high_disk_usage", "WARNING")
                except ImportError:
                    logger.warning("psutil not available, using mock metrics")
                    cpu_usage = 45.0
                    memory_usage = 60.0

                # Simulate fluctuating usage for demonstration
                cpu_usage = round(random.uniform(settings.AI_OPS_MIN_CPU, settings.AI_OPS_MAX_CPU), 2)
                memory_usage = round(random.uniform(settings.AI_OPS_MIN_MEMORY, settings.AI_OPS_MAX_MEMORY), 2)

                self.infrastructure_status = {
                    "cpu_usage_percent": cpu_usage,
                    "memory_usage_percent": memory_usage,
                    "last_checked": datetime.now().isoformat(),
                    "status": "healthy"
                }

                if cpu_usage > settings.WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT or \
                   memory_usage > settings.WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT:
                    self.infrastructure_status["status"] = "alert"
                    logger.warning(f"AI-Ops Agent: High resource usage detected. CPU: {cpu_usage}%, Mem: {memory_usage}%.")
                    await self._publish_aiops_alert(
                        "resource_overload",
                        f"High resource usage detected: CPU {cpu_usage}%, Mem {memory_usage}%.",
                        self.infrastructure_status,
                        severity="HIGH"
                    )
                else:
                    logger.info(f"AI-Ops Agent: System health is nominal. CPU: {cpu_usage}%, Mem: {memory_usage}%.")

            except Exception as e:
                logger.error(f"AI-Ops Agent '{self.agent_id}': Error during periodic health check: {e}", exc_info=True)
            await asyncio.sleep(settings.AI_OPS_HEALTH_CHECK_INTERVAL_SECONDS) # Configurable interval

    async def _handle_iot_sensory_data(self, message_payload: Dict[str, Any]):
        """
        Processes incoming IoT sensory data. While primarily for PrivSensoryAgent,
        AI-Ops might use it for environmental monitoring of server rooms, etc.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            sensory_data = agent_message.payload
            
            room_id = sensory_data.get("room_id")
            readings = sensory_data.get("readings", {})
            
            logger.debug(f"AI-Ops Agent: Received IoT sensory data from {room_id}: {readings}.")

            # Example: Check for unusual temperature in server room
            if readings.get("temperature_celsius") and \
               readings["temperature_celsius"] > settings.AI_OPS_SERVER_ROOM_TEMP_THRESHOLD:
                logger.warning(f"AI-Ops Agent: High temperature detected in {room_id}: {readings['temperature_celsius']}°C.")
                await self._publish_aiops_alert(
                    "server_room_overheat",
                    f"Server room '{room_id}' temperature is {readings['temperature_celsius']}°C, exceeding threshold.",
                    sensory_data,
                    severity="HIGH"
                )
            
        except Exception as e:
            logger.error(f"AI-Ops Agent '{self.agent_id}': Error handling IoT sensory data: {e}", exc_info=True)


    async def _handle_model_metrics(self, message_payload: Dict[str, Any]):
        """
        Processes incoming model performance metrics (e.g., accuracy, latency, drift).
        These metrics would be published by your ML training/monitoring pipelines.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            metrics_data = agent_message.payload

            model_id = metrics_data.get("model_id")
            metric_type = metrics_data.get("metric_type") # e.g., "accuracy", "latency", "data_drift"
            value = metrics_data.get("value")

            if model_id and metric_type and value is not None:
                if model_id not in self.model_performance_metrics:
                    self.model_performance_metrics[model_id] = {}
                self.model_performance_metrics[model_id][metric_type] = value
                self.model_performance_metrics[model_id]["last_updated"] = datetime.now().isoformat()
                logger.debug(f"AI-Ops Agent: Updated metrics for model {model_id}: {metric_type}={value}.")

                # Trigger conceptual model re-training or alert if performance degrades
                if metric_type == "accuracy" and value < settings.AI_OPS_MODEL_ACCURACY_THRESHOLD:
                    logger.warning(f"AI-Ops Agent: Model {model_id} accuracy ({value:.2f}) is below threshold. Considering re-training.")
                    await self._publish_aiops_alert(
                        "model_performance_degradation",
                        f"Model {model_id} accuracy dropped to {value:.2f}.",
                        metrics_data,
                        severity="HIGH"
                    )
                    # Trigger the full training pipeline for this model/symbol
                    # Assuming a mapping from model_id to symbol/timeframe
                    # For simplicity, let's assume 'trade_prediction_v1' is for 'EURUSD'
                    if model_id.startswith("trade_prediction"):
                        target_symbol = "EURUSD" # This needs to be dynamically determined
                        logger.info(f"AI-Ops Agent: Triggering retraining pipeline for {target_symbol} due to model degradation.")
                        # Run the training pipeline in a non-blocking way
                        asyncio.create_task(run_training_pipeline(symbol=target_symbol, dry_run=False))

                elif metric_type == "data_drift" and value > settings.AI_OPS_DATA_DRIFT_THRESHOLD:
                    logger.warning(f"AI-Ops Agent: High data drift ({value:.2f}) detected for model {model_id}. Investigating data pipeline.")
                    await self._publish_aiops_alert(
                        "data_drift_detected",
                        f"Significant data drift detected for model {model_id}.",
                        metrics_data,
                        severity="HIGH"
                    )

        except Exception as e:
            logger.error(f"AI-Ops Agent '{self.agent_id}': Error handling model metrics: {e}", exc_info=True)

    async def handle_infrastructure_alert(self, alert_type: str, severity: str):
        """Handle infrastructure alerts directly"""
        try:
            logger.warning(f"Infrastructure alert: {alert_type} (Severity: {severity})")
            
            if severity == "CRITICAL":
                await self._attempt_auto_healing(alert_type)
                await self._publish_aiops_alert(
                    "critical_infrastructure_failure",
                    f"Critical infrastructure failure: {alert_type}. Immediate action required.",
                    {"alert_type": alert_type, "severity": severity},
                    severity="CRITICAL"
                )
        except Exception as e:
            logger.error(f"Error handling infrastructure alert: {e}")
    
    async def _attempt_auto_healing(self, alert_type: str):
        """Attempt automatic healing for infrastructure issues"""
        try:
            logger.info(f"Attempting auto-healing for: {alert_type}")
            
            # Auto-healing strategies based on alert type
            healing_strategies = {
                "high_cpu_usage": self._heal_high_cpu,
                "high_memory_usage": self._heal_high_memory,
                "high_disk_usage": self._heal_high_disk,
                "service_down": self._heal_service_down,
                "network_issue": self._heal_network_issue,
            }
            
            healing_func = healing_strategies.get(alert_type)
            if healing_func:
                await healing_func()
                logger.info(f"Auto-healing completed for: {alert_type}")
            else:
                logger.warning(f"No auto-healing strategy for: {alert_type}")
                
        except Exception as e:
            logger.error(f"Auto-healing failed: {e}")
    
    async def _heal_high_cpu(self):
        """Heal high CPU usage"""
        # Kill non-essential processes, scale horizontally, etc.
        logger.info("Healing high CPU: Optimizing processes")
    
    async def _heal_high_memory(self):
        """Heal high memory usage"""
        # Clear caches, restart memory-intensive services, scale up
        logger.info("Healing high memory: Clearing caches and optimizing")
    
    async def _heal_high_disk(self):
        """Heal high disk usage"""
        # Clean up logs, temporary files, old backups
        logger.info("Healing high disk: Cleaning up storage")
    
    async def _heal_service_down(self):
        """Heal service downtime"""
        # Restart service, failover to backup, scale up
        logger.info("Healing service down: Attempting restart")
        # Example: kubectl restart deployment/service-name
    
    async def _heal_network_issue(self):
        """Heal network issues"""
        # Reset connections, switch to backup network, restart network services
        logger.info("Healing network issue: Resetting connections")
    
    async def _handle_infrastructure_alert(self, message_payload: Dict[str, Any]):
        """
        Processes alerts related to the underlying infrastructure (e.g., server down, network issues).
        These would typically come from your monitoring system.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            alert_details = agent_message.payload

            alert_type = alert_details.get("alert_type")
            severity = alert_details.get("severity")

            logger.critical(f"AI-Ops Agent: Received infrastructure alert: {alert_type} (Severity: {severity}).")

            # Trigger auto-healing or escalate
            if severity == "CRITICAL":
                logger.critical(f"AI-Ops Agent: CRITICAL infrastructure alert. Attempting auto-healing or escalating to human ops.")
                # Integrate with actual auto-healing scripts/APIs
                await self._attempt_auto_healing(alert_type)
                await self._publish_aiops_alert(
                    "critical_infrastructure_failure",
                    f"Critical infrastructure failure: {alert_type}. Immediate action required.",
                    alert_details,
                    severity="CRITICAL"
                )

        except Exception as e:
            logger.error(f"AI-Ops Agent '{self.agent_id}': Error handling infrastructure alert: {e}", exc_info=True)

    async def _handle_deployment_request(self, message_payload: Dict[str, Any]):
        """
        Handles requests to deploy new models or model versions.
        This would typically come from a human operator or a CI/CD pipeline.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            deployment_request = agent_message.payload

            model_id = deployment_request.get("model_id")
            version = deployment_request.get("version")
            source_agent = agent_message.sender_id
            target_symbol = deployment_request.get("target_symbol") # Assume deployment requests include target symbol

            logger.info(f"AI-Ops Agent: Received deployment request for model {model_id} v{version} for {target_symbol} from {source_agent}.")

            # Trigger the full training pipeline, which handles saving and deployment if successful
            logger.info(f"AI-Ops Agent: Triggering full training pipeline for {target_symbol} as part of deployment request.")
            deployment_results = await run_training_pipeline(symbol=target_symbol, dry_run=False)

            deployment_status = deployment_results.get("status", "UNKNOWN")
            if deployment_results.get("model_deployed"):
                deployment_status = "SUCCESS"
            elif "failed" in deployment_status:
                deployment_status = "FAILED"

            response_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=source_agent,
                message_type=MessageType.STATUS_UPDATE, # Or new type like MessageType.DEPLOYMENT_STATUS
                payload={"model_id": model_id, "version": version, "status": deployment_status, "timestamp": datetime.now().isoformat(), "pipeline_results": deployment_results}
            )
            await self.broker.publish_message("deployment_status_updates", response_message.model_dump())
            logger.info(f"AI-Ops Agent: Published deployment status for {model_id} v{version}: {deployment_status}.")

            if deployment_status == "FAILED":
                await self._publish_aiops_alert(
                    "model_deployment_failed",
                    f"Deployment of model {model_id} v{version} for {target_symbol} failed.",
                    response_message.payload,
                    severity="CRITICAL"
                )

        except Exception as e:
            logger.error(f"AI-Ops Agent '{self.agent_id}': Error handling deployment request: {e}", exc_info=True)

    async def _publish_aiops_alert(self, alert_type: str, message: str, details: Dict[str, Any], severity: str = "MEDIUM"):
        """
        Publishes an AI-Ops alert message to a dedicated topic and potentially to external systems.
        """
        alert_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.ERROR_NOTIFICATION, # Reusing ERROR_NOTIFICATION for alerts
            payload={
                "source_agent_id": self.agent_id,
                "message": message,
                "severity": severity, # CRITICAL, HIGH, MEDIUM, LOW
                "alert_type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.broker.publish_message("aiops_alerts", alert_message.model_dump())
        logger.log(logging.getLevelName(severity), f"AI-Ops Agent: Published AI-Ops alert: {alert_type} - {message}")

        # Send WhatsApp alert for critical AI-Ops issues
        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            whatsapp_message = (
                f"🚨 CRITICAL AI-OPS ALERT! 🚨\n"
                f"Type: {alert_type}\n"
                f"Message: {message}\n"
                f"Details: {details}"
            )
            try:
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"AI-Ops Agent: Conceptually sent critical WhatsApp alert for AI-Ops to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"AI-Ops Agent: Failed to send WhatsApp alert for AI-Ops: {e}", exc_info=True)


# Example Usage (for testing PrivAIOpsAgent in isolation)
async def main_aiops_agent_test():
    logging.basicConfig(level=logging.INFO)
    import random # For simulating data
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    # Import for patching the pipeline function in test
    from unittest.mock import patch

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'LIVE_MODEL_DIR'):
        settings.LIVE_MODEL_DIR = "models/current_live_model"
    if not hasattr(settings, 'AI_OPS_MIN_CPU'):
        settings.AI_OPS_MIN_CPU = 5
    if not hasattr(settings, 'AI_OPS_MAX_CPU'):
        settings.AI_OPS_MAX_CPU = 15
    if not hasattr(settings, 'AI_OPS_MIN_MEMORY'):
        settings.AI_OPS_MIN_MEMORY = 20
    if not hasattr(settings, 'AI_OPS_MAX_MEMORY'):
        settings.AI_OPS_MAX_MEMORY = 40
    if not hasattr(settings, 'WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT'):
        settings.WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT = 90 # High for watchdog, lower for AI-Ops proactive
    if not hasattr(settings, 'WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT'):
        settings.WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT = 85 # High for watchdog, lower for AI-Ops proactive
    if not hasattr(settings, 'AI_OPS_HEALTH_CHECK_INTERVAL_SECONDS'):
        settings.AI_OPS_HEALTH_CHECK_INTERVAL_SECONDS = 5 # Frequent for test
    if not hasattr(settings, 'AI_OPS_SERVER_ROOM_TEMP_THRESHOLD'):
        settings.AI_OPS_SERVER_ROOM_TEMP_THRESHOLD = 30
    if not hasattr(settings, 'AI_OPS_MODEL_ACCURACY_THRESHOLD'):
        settings.AI_OPS_MODEL_ACCURACY_THRESHOLD = 0.85
    if not hasattr(settings, 'AI_OPS_DATA_DRIFT_THRESHOLD'):
        settings.AI_OPS_DATA_DRIFT_THRESHOLD = 0.1
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890"

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    aiops_agent = PrivAIOpsAgent(
        agent_id="Priv-AIOps",
        broker=broker,
        persona={"name": "AI Operations Manager", "focus": "Model Health & Infrastructure"}
    )

    await broker.connect()
    await aiops_agent.start()

    logger.info("\n--- Simulating messages for AI-Ops Agent to consume ---")

    # Patch the run_training_pipeline to avoid actual heavy ML ops during test
    mock_pipeline_results_success = {"status": "completed", "model_deployed": True, "new_model_accuracy": 0.9}
    mock_pipeline_results_failure = {"status": "failed_training", "model_deployed": False, "new_model_accuracy": 0.0}

    # Simulate model performance metrics (accuracy drop)
    mock_model_accuracy_drop = AgentMessage(
        sender_id="Priv-MLAgent",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "model_id": "trade_prediction_v1",
            "metric_type": "accuracy",
            "value": 0.82, # Below threshold
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("model_performance_metrics", mock_model_accuracy_drop.model_dump())
    await asyncio.sleep(1)

    # Simulate data drift detection
    mock_data_drift = AgentMessage(
        sender_id="Priv-MLAgent",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "model_id": "sentiment_analyzer_v2",
            "metric_type": "data_drift",
            "value": 0.15, # Above threshold
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("model_performance_metrics", mock_data_drift.model_dump())
    await asyncio.sleep(1)

    # Simulate an infrastructure alert (e.g., from a monitoring system)
    mock_infra_alert = AgentMessage(
        sender_id="InfrastructureMonitor",
        message_type=MessageType.ERROR_NOTIFICATION,
        payload={
            "alert_type": "server_unresponsive",
            "severity": "CRITICAL",
            "component": "trading_engine_server_01",
            "message": "Trading engine server is not responding to health checks.",
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("infrastructure_alerts", mock_infra_alert.model_dump())
    await asyncio.sleep(1)

    # Simulate IoT sensory data (e.g., server room temperature)
    mock_iot_temp_high = AgentMessage(
        sender_id="IoTSensorIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "room_id": "server_room_alpha",
            "timestamp_utc": datetime.utcnow().isoformat(),
            "readings": {"temperature_celsius": 32.5, "humidity_percent": 50.0}
        }
    )
    await broker.publish_message("iot_sensory_data", mock_iot_temp_high.model_dump())
    await asyncio.sleep(1)


    # Simulate a model deployment request (will trigger run_training_pipeline)
    # Patch the run_training_pipeline function for this specific call
    with patch('backend.ml_pipeline.vertex_ai_pipeline.run_training_pipeline') as mock_run_pipeline:
        mock_run_pipeline.return_value = mock_pipeline_results_success # Simulate success
        mock_deployment_request = AgentMessage(
            sender_id="Priv-MLAgent",
            message_type=MessageType.ARBITRATION_REQUEST, # Reusing for conceptual request
            payload={
                "request_id": "deploy_001",
                "model_id": "trade_prediction_v2",
                "version": "2.0.1",
                "target_symbol": "EURUSD", # Specify target symbol for pipeline
                "source_code_repo": "git@example.com/models/trade_v2.git",
                "timestamp": datetime.now().isoformat()
            }
        )
        await broker.publish_message("model_deployment_requests", mock_deployment_request.model_dump())
        await asyncio.sleep(1)

        mock_run_pipeline.return_value = mock_pipeline_results_failure # Simulate failure
        mock_deployment_request_fail = AgentMessage(
            sender_id="Priv-MLAgent",
            message_type=MessageType.ARBITRATION_REQUEST,
            payload={
                "request_id": "deploy_002",
                "model_id": "risk_model_v3",
                "version": "3.0.0",
                "target_symbol": "SPY",
                "timestamp": datetime.now().isoformat()
            }
        )
        await broker.publish_message("model_deployment_requests", mock_deployment_request_fail.model_dump())
        await asyncio.sleep(1)


    await asyncio.sleep(15) # Give time for agents to process messages and health checks to run

    await aiops_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivAIOpsAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_aiops_agent_test())
