# backend/utils/watchdog.py

import asyncio
import logging
import psutil # For system resource monitoring
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text # For raw SQL execution (PostgreSQL health check)

# Import settings for thresholds and escalation policies
from backend.config import settings

# Import for database session check (PostgreSQL)
from backend.database import get_db

# Import for Firestore client access (for Firestore latency check)
try:
    from firebase_admin import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    firestore = None
    FIRESTORE_AVAILABLE = False

# NEW: Import the message broker for real alerts
from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker

logger = logging.getLogger(__name__)

# Log warning about Firebase after logger is defined
if not FIRESTORE_AVAILABLE:
    logger.warning("Firebase Admin SDK not available. Firestore health checks disabled.")

class Watchdog:
    """
    A sophisticated failsafe watchdog mechanism for Priv.
    Monitors critical system metrics and service health,
    and triggers escalation actions based on predefined policies.
    """
    def __init__(self, db_instance: "firestore.Client", message_broker: GoogleCloudPubSubBroker):
        self.interval = settings.WATCHDOG_DB_CHECK_INTERVAL_SECONDS
        self.escalation_level = settings.WATCHDOG_ESCALATION_LEVEL
        self.alert_email_recipients = settings.WATCHDOG_ALERT_EMAIL_RECIPIENTS
        self.alert_pubsub_topic = settings.WATCHDOG_ALERT_PUBSUB_TOPIC
        self.human_override_timeout = settings.WATCHDOG_HUMAN_OVERRIDE_TIMEOUT_MINUTES
        
        self.db_latency_threshold_ms = settings.WATCHDOG_DB_LATENCY_THRESHOLD_MS
        self.firestore_latency_threshold_ms = settings.WATCHDOG_FIRESTORE_LATENCY_THRESHOLD_MS
        self.external_api_error_rate_threshold = settings.WATCHDOG_EXTERNAL_API_ERROR_RATE_THRESHOLD
        self.memory_usage_threshold_percent = settings.WATCHDOG_MEMORY_USAGE_THRESHOLD_PERCENT
        self.cpu_usage_threshold_percent = settings.WATCHDOG_CPU_USAGE_THRESHOLD_PERCENT

        self._db = db_instance # Firestore client for its own health check
        self._broker = message_broker # NEW: Message broker for sending alerts
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_active = False
        self._last_alert_time: Optional[datetime] = None
        self._critical_state_active = False # Flag to indicate if a critical issue is ongoing

        logger.info(f"Watchdog initialized with interval {self.interval}s and escalation level '{self.escalation_level}'.")

    async def _perform_checks(self):
        """Performs all defined health and performance checks."""
        issues: List[str] = []

        # 1. Check Kill Switch
        if settings.KILL_SWITCH_AI_TRADING:
            issues.append("KILL_SWITCH_ACTIVE: AI trading is globally disabled.")
            logger.critical("WATCHDOG: Global AI trading kill switch is active.")
            self._critical_state_active = True # This is a critical, intentional state

        # 2. Database Connection Health (PostgreSQL)
        db_healthy, db_latency = await self._check_db_connection()
        if not db_healthy:
            issues.append(f"DB_UNHEALTHY: PostgreSQL connection failed or high latency ({db_latency:.2f}ms).")
            logger.error(f"WATCHDOG: PostgreSQL connection issues detected. Latency: {db_latency:.2f}ms.")
        elif db_latency > self.db_latency_threshold_ms:
            issues.append(f"DB_LATENCY_HIGH: PostgreSQL query latency ({db_latency:.2f}ms) exceeds threshold ({self.db_latency_threshold_ms}ms).")
            logger.warning(f"WATCHDOG: High PostgreSQL query latency: {db_latency:.2f}ms.")

        # 3. Firestore Connection Health
        firestore_healthy, firestore_latency = await self._check_firestore_connection()
        if not firestore_healthy:
            issues.append(f"FIRESTORE_UNHEALTHY: Firestore connection failed or high latency ({firestore_latency:.2f}ms).")
            logger.error(f"WATCHDOG: Firestore connection issues detected. Latency: {firestore_latency:.2f}ms.")
        elif firestore_latency > self.firestore_latency_threshold_ms:
            issues.append(f"FIRESTORE_LATENCY_HIGH: Firestore operation latency ({firestore_latency:.2f}ms) exceeds threshold ({self.firestore_latency_threshold_ms}ms).")
            logger.warning(f"WATCHDOG: High Firestore operation latency: {firestore_latency:.2f}ms.")

        # 4. System Resource Usage (CPU & Memory)
        cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking
        memory_percent = psutil.virtual_memory().percent
        if cpu_percent > self.cpu_usage_threshold_percent:
            issues.append(f"HIGH_CPU_USAGE: CPU usage ({cpu_percent:.2f}%) exceeds threshold ({self.cpu_usage_threshold_percent}%).")
            logger.warning(f"WATCHDOG: High CPU usage detected: {cpu_percent:.2f}%.")
        if memory_percent > self.memory_usage_threshold_percent:
            issues.append(f"HIGH_MEMORY_USAGE: Memory usage ({memory_percent:.2f}%) exceeds threshold ({self.memory_usage_threshold_percent}%).")
            logger.warning(f"WATCHDOG: High Memory usage detected: {memory_percent:.2f}%.")
        
        # 5. External API Error Rates (Conceptual - requires metrics collection)
        # This would require a global error tracking system (e.g., Prometheus/Grafana, or simple counters)
        # For now, this is a placeholder.
        # current_external_api_error_rate = get_external_api_error_rate() # Assume this function exists
        # if current_external_api_error_rate > self.external_api_error_rate_threshold:
        #     issues.append(f"HIGH_API_ERROR_RATE: External API error rate ({current_external_api_error_rate:.2%}) exceeds threshold ({self.external_api_error_rate_threshold:.2%}).")
        #     logger.error(f"WATCHDOG: High external API error rate detected: {current_external_api_error_rate:.2%}.")

        # Determine overall critical state
        was_critical = self._critical_state_active
        is_now_critical = bool(issues) and not settings.KILL_SWITCH_AI_TRADING
        self._critical_state_active = is_now_critical or settings.KILL_SWITCH_AI_TRADING

        # Trigger escalation if issues found
        if issues:
            await self._escalate(issues)
        elif was_critical and not self._critical_state_active: # If issues were present but now resolved
            logger.info("WATCHDOG: All critical issues resolved. System operating normally.")
            await self._send_alert("WATCHDOG: RESOLVED - All systems normal.", is_resolution=True)
            self._last_alert_time = None # Reset alert time

    async def _check_db_connection(self) -> tuple[bool, float]:
        """Checks PostgreSQL database connection health and latency."""
        start_time = datetime.now()
        db_session = None
        try:
            db_session = next(get_db())
            # Perform a lightweight query to test connection and latency
            await asyncio.to_thread(db_session.execute, text("SELECT 1"))
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            return True, latency_ms
        except Exception as e:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Watchdog: PostgreSQL health check failed: {e}", exc_info=True)
            return False, latency_ms
        finally:
            if db_session:
                db_session.close() # Ensure session is closed

    async def _check_firestore_connection(self) -> tuple[bool, float]:
        """Checks Firestore connection health and latency."""
        if not self._db:
            return False, 0.0 # Firestore not initialized
        start_time = datetime.now()
        try:
            # Perform a lightweight Firestore operation (e.g., get a dummy document)
            await self._db.collection("watchdog_health_check").document("test_doc").get()
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            return True, latency_ms
        except Exception as e:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Watchdog: Firestore health check failed: {e}", exc_info=True)
            return False, latency_ms

    async def _escalate(self, issues: List[str]):
        """Triggers escalation actions based on the configured level."""
        alert_message = f"WATCHDOG ALERT! Critical issues detected:\n- " + "\n- ".join(issues)
        logger.error(alert_message) # Always log the alert

        if self._last_alert_time and (datetime.now() - self._last_alert_time).total_seconds() < (self.interval * 4):
            logger.info("WATCHDOG: Skipping repeated alert within short interval to avoid spam.")
            return

        self._last_alert_time = datetime.now()

        if self.escalation_level == "LOG_ONLY":
            logger.warning("WATCHDOG: Escalation level is LOG_ONLY. No further action taken.")
        elif self.escalation_level == "CRITICAL_ALERT":
            await self._send_alert(alert_message)
            logger.critical("WATCHDOG: Critical alert sent to human operators.")
        elif self.escalation_level == "SHUTDOWN_AI_TRADING":
            settings.KILL_SWITCH_AI_TRADING = True # Activate the global kill switch
            await self._send_alert(alert_message + "\n\nACTION: Automated AI trading has been shut down.")
            logger.critical("WATCHDOG: Automated AI trading shut down due to critical issues.")
        elif self.escalation_level == "FULL_SHUTDOWN":
            await self._send_alert(alert_message + "\n\nACTION: Initiating full application shutdown!")
            logger.critical("WATCHDOG: Initiating full application shutdown due to critical issues.")
            asyncio.create_task(self._initiate_graceful_shutdown())
        else:
            logger.warning(f"WATCHDOG: Unknown escalation level '{self.escalation_level}'. Defaulting to LOG_ONLY.")

    async def _send_alert(self, message: str, is_resolution: bool = False):
        """Sends alerts via email and/or Pub/Sub."""
        subject = f"Priv Watchdog Alert: { 'SYSTEMS CRITICAL' if not is_resolution else 'SYSTEMS RESOLVED' }"
        
        # Pub/Sub Alerting
        if self.alert_pubsub_topic and self._broker and self._broker.is_connected:
            logger.info(f"WATCHDOG: Publishing Pub/Sub alert to topic {self.alert_pubsub_topic}")
            pubsub_message = {
                "source": "PrivWatchdog",
                "is_resolution": is_resolution,
                "timestamp": datetime.utcnow().isoformat(),
                "escalation_level": self.escalation_level,
                "message": message,
            }
            try:
                await self._broker.publish_message(self.alert_pubsub_topic, pubsub_message)
            except Exception as e:
                logger.error(f"WATCHDOG: Failed to publish alert to Pub/Sub topic '{self.alert_pubsub_topic}': {e}", exc_info=True)
        
        # Email Alerting
        if self.alert_email_recipients:
            logger.info(f"WATCHDOG: Sending email alert to {self.alert_email_recipients}")
            # This is where you would integrate with a real email service (e.g., SendGrid, Mailgun).
            # For this implementation, we will log the intent and publish a message
            # that a dedicated email-sending microservice could subscribe to.
            email_task = {
                "recipients": self.alert_email_recipients,
                "subject": subject,
                "body": message
            }
            logger.info(f"Email task generated: {email_task}")
            # Optional: Publish to a dedicated 'send-email' Pub/Sub topic
            if self._broker and self._broker.is_connected:
                 await self._broker.publish_message("system_email_tasks", email_task)

    async def _initiate_graceful_shutdown(self):
        """Conceptual: Initiates a graceful shutdown of the FastAPI application."""
        logger.critical("WATCHDOG: Attempting graceful shutdown of FastAPI application in 5 seconds...")
        await asyncio.sleep(5)
        # This will cause the Uvicorn server to exit. In Kubernetes, this will
        # lead to the pod being restarted according to its restart policy.
        raise SystemExit("Watchdog triggered full application shutdown.")

    async def start_monitoring(self):
        """Starts the watchdog's periodic monitoring loop in the background."""
        if self._is_active:
            logger.warning("Watchdog is already active.")
            return
        logger.info("Watchdog: Starting periodic monitoring.")
        self._is_active = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """The actual monitoring loop that runs periodically."""
        while self._is_active:
            try:
                await self._perform_checks()
            except Exception as e:
                logger.error(f"Watchdog: Unhandled error in monitoring cycle: {e}", exc_info=True)
            await asyncio.sleep(self.interval)

    def stop_monitoring(self):
        """Stops the watchdog's periodic monitoring loop."""
        if not self._is_active:
            logger.warning("Watchdog is not active.")
            return
        logger.info("Watchdog: Stopping periodic monitoring.")
        self._is_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None

    def is_critical_state_active(self) -> bool:
        """Returns True if the watchdog has detected a critical issue."""
        return self._critical_state_active
