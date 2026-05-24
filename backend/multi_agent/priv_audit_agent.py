# backend/multi_agent/priv_audit_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import settings for configurable thresholds
from backend.config import settings

# Import WhatsAppNotifier for critical alerts
from backend.communication.whatsapp_notifier import WhatsAppNotifier

# from backend.database import AuditLogDBClient # Example: if you have a dedicated client
# from google.cloud import logging as gcp_logging # Example: for Google Cloud Logging

logger = logging.getLogger(__name__)

class PrivAuditAgent(PrivAgent):
    """
    A specialized Priv Agent responsible for auditing system operations,
    transaction logs, and agent behaviors to ensure compliance, integrity,
    and detect anomalies. It acts as a governance and oversight mechanism.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.AUDIT, message_broker=message_broker, broker=broker, persona=persona)
        self.broker = broker
        self.is_running = False
        
        # In a real production system, self.audit_log would be replaced by
        # an integration with a persistent, scalable audit log storage solution
        # (e.g., a dedicated database table, a data warehouse, or a cloud logging service like BigQuery).
        # For demonstration, it remains an in-memory list, but this MUST be changed for live.
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize external logging/database clients if needed
        # self.audit_db_client = AuditLogDBClient() # Example initialization
        # self.gcp_logger = gcp_logging.Client().logger(f"priv-audit-log-{agent_id}") # Example for GCP
        
        self.whatsapp_notifier = WhatsAppNotifier() # Initialize WhatsApp Notifier

        logger.info(f"Priv Audit Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the audit agent, subscribing to relevant system events."""
        if self.is_running:
            logger.warning(f"Audit Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to arbitration decisions, trade proposals, and error notifications
        await self.message_broker.subscribe_to_topic(
            "arbitration_decisions", self._handle_arbitration_decision, f"{self.agent_id}-arbitration-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "trade_proposals", self._handle_trade_proposal, f"{self.agent_id}-proposals-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "error_notifications", self._handle_error_notification, f"{self.agent_id}-errors-sub"
        )
        await self.message_broker.subscribe_to_topic(
            "compliance_violations", self._handle_compliance_violation, f"{self.agent_id}-compliance-sub"
        )
        # Add subscription to audit_alerts if this agent needs to react to its own published alerts
        # (e.g., for internal tracking or further escalation)
        await self.message_broker.subscribe_to_topic(
            "audit_alerts", self._handle_self_published_alert, f"{self.agent_id}-self-alert-sub"
        )


        self.is_running = True
        logger.info(f"Priv Audit Agent '{self.agent_id}' started and subscribed to audit topics.")

    async def stop(self):
        """Stops the audit agent."""
        if not self.is_running:
            logger.warning(f"Audit Agent '{self.agent_id}' is not running.")
            return

        self.is_running = False
        logger.info(f"Priv Audit Agent '{self.agent_id}' stopped.")

    async def _record_audit_event(self, event_type: str, details: Dict[str, Any]):
        """
        Records an audit event to the persistent audit log.
        Implements multi-backend persistence: PostgreSQL, Firestore, and local files.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "audited_by": self.agent_id
        }
        
        # Multi-backend persistence strategy
        persistence_success = False
        
        # 1. Try PostgreSQL first (primary storage)
        try:
            if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
                import asyncpg
                conn = await asyncpg.connect(settings.DATABASE_URL)
                try:
                    await conn.execute('''
                        INSERT INTO audit_logs (timestamp, event_type, details, audited_by)
                        VALUES ($1, $2, $3, $4)
                    ''', log_entry["timestamp"], event_type, str(details), self.agent_id)
                    persistence_success = True
                    logger.debug(f"Audit Agent: Recorded to PostgreSQL: {event_type}")
                finally:
                    await conn.close()
        except Exception as e:
            logger.warning(f"Audit Agent: PostgreSQL storage failed: {e}")
        
        # 2. Try Firestore (secondary storage)
        try:
            if hasattr(settings, 'GCP_PROJECT_ID') and settings.GCP_PROJECT_ID:
                from google.cloud import firestore
                db = firestore.Client(project=settings.GCP_PROJECT_ID)
                doc_ref = db.collection('audit_logs').document()
                doc_ref.set(log_entry)
                persistence_success = True
                logger.debug(f"Audit Agent: Recorded to Firestore: {event_type}")
        except Exception as e:
            logger.warning(f"Audit Agent: Firestore storage failed: {e}")
        
        # 3. Local file storage (fallback)
        try:
            import json
            import os
            log_dir = getattr(settings, 'AUDIT_LOG_DIR', '/workspace/audit_logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            persistence_success = True
            logger.debug(f"Audit Agent: Recorded to local file: {event_type}")
        except Exception as e:
            logger.error(f"Audit Agent: Local file storage failed: {e}", exc_info=True)
        
        # 4. In-memory backup (always)
        self.audit_log.append(log_entry)
        
        if not persistence_success:
            logger.error(f"Audit Agent: All persistence backends failed for event: {event_type}")
        
        logger.debug(f"Audit Agent: Recorded audit event: {event_type}.")


    async def _handle_arbitration_decision(self, message_payload: Dict[str, Any]):
        """
        Processes arbitration decisions for audit purposes.
        Records the decision and performs real-time audit checks.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            decision = agent_message.payload

            await self._record_audit_event("arbitration_decision", decision)
            logger.info(f"Audit Agent: Logged arbitration decision for {decision.get('symbol')}.")

            # Real-time audit check: Ensure confidence is above a configurable threshold for critical actions
            # These thresholds should be loaded from configuration (e.g., settings.py)
            MIN_CONFIDENCE_FOR_TRADE = getattr(settings, 'AUDIT_MIN_TRADE_CONFIDENCE', 0.15) 
            if decision.get("action") in ["BUY", "SELL"] and decision.get("confidence", 0) < MIN_CONFIDENCE_FOR_TRADE:
                logger.warning(f"Audit Agent: Low confidence ({decision.get('confidence')}) decision for {decision.get('symbol')} detected. Threshold: {MIN_CONFIDENCE_FOR_TRADE}.")
                await self._publish_audit_alert(
                    "low_confidence_decision",
                    f"Arbitration decision for {decision.get('symbol')} made with unusually low confidence ({decision.get('confidence'):.2f}).",
                    decision,
                    severity="MEDIUM"
                )

        except Exception as e:
            logger.error(f"Audit Agent '{self.agent_id}': Error handling arbitration decision: {e}", exc_info=True)

    async def _handle_trade_proposal(self, message_payload: Dict[str, Any]):
        """
        Processes trade proposals for audit purposes.
        Records the proposal and performs real-time audit checks.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            proposal = agent_message.payload

            await self._record_audit_event("trade_proposal", proposal)
            logger.info(f"Audit Agent: Logged trade proposal from {proposal.get('agent_id')} for {proposal.get('symbol')}.")

            # Real-time audit check: Flag proposals with unusually high volume
            # This threshold should be configurable (e.g., settings.py)
            MAX_PROPOSAL_VOLUME = getattr(settings, 'AUDIT_MAX_PROPOSAL_VOLUME', 100)
            if proposal.get("volume", 0) > MAX_PROPOSAL_VOLUME:
                logger.warning(f"Audit Agent: High volume proposal ({proposal.get('volume')}) from {proposal.get('agent_id')} detected. Threshold: {MAX_PROPOSAL_VOLUME}.")
                await self._publish_audit_alert(
                    "high_volume_proposal",
                    f"Trade proposal from {proposal.get('agent_id')} for {proposal.get('symbol')} has unusually high volume ({proposal.get('volume')}).",
                    proposal,
                    severity="HIGH"
                )
            
            # Additional check: If risk_assessment is missing or incomplete
            if not proposal.get("risk_assessment"):
                logger.warning(f"Audit Agent: Trade proposal from {proposal.get('agent_id')} for {proposal.get('symbol')} missing risk assessment.")
                await self._publish_audit_alert(
                    "missing_risk_assessment",
                    f"Trade proposal from {proposal.get('agent_id')} for {proposal.get('symbol')} lacks comprehensive risk assessment.",
                    proposal,
                    severity="MEDIUM"
                )

        except Exception as e:
            logger.error(f"Audit Agent '{self.agent_id}': Error handling trade proposal: {e}", exc_info=True)

    async def _handle_error_notification(self, message_payload: Dict[str, Any]):
        """
        Processes error notifications for audit purposes.
        Records the error and potentially escalates.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            error_details = agent_message.payload

            await self._record_audit_event("error_notification", error_details)
            logger.warning(f"Audit Agent: Logged error notification from {error_details.get('source_agent_id')}: {error_details.get('message')}.")

            # Real-time audit check: Escalate critical errors
            if error_details.get("severity") == "CRITICAL":
                logger.critical(f"Audit Agent: CRITICAL error detected from {error_details.get('source_agent_id')}. Escalating.")
                await self._publish_audit_alert(
                    "critical_system_error",
                    f"Critical error reported by {error_details.get('source_agent_id')}: {error_details.get('message')}",
                    error_details,
                    severity="CRITICAL"
                )

        except Exception as e:
            logger.error(f"Audit Agent '{self.agent_id}': Error handling error notification: {e}", exc_info=True)

    async def _handle_compliance_violation(self, message_payload: Dict[str, Any]):
        """
        Processes compliance violation messages, logging them and potentially
        triggering further audit actions.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            violation_details = agent_message.payload

            await self._record_audit_event("compliance_violation", violation_details)
            logger.critical(f"Audit Agent: Logged compliance violation from {violation_details.get('agent_id')}: {violation_details.get('violation_type')}.")

            await self._publish_audit_alert(
                "compliance_violation_detected",
                f"Compliance violation of type '{violation_details.get('violation_type')}' detected for agent {violation_details.get('agent_id')}.",
                violation_details,
                severity="CRITICAL"
            )

        except Exception as e:
            logger.error(f"Audit Agent '{self.agent_id}': Error handling compliance violation: {e}", exc_info=True)

    async def _handle_self_published_alert(self, message_payload: Dict[str, Any]):
        """
        Handles alerts published by this audit agent itself.
        Used for internal tracking or to prevent infinite loops if alerts trigger new alerts.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            alert_details = agent_message.payload
            
            # Only process if this alert was NOT published by self, or if it's a specific type
            # that requires internal re-evaluation.
            if agent_message.sender_id != self.agent_id:
                logger.info(f"Audit Agent: Received external audit alert: {alert_details.get('alert_type')}.")
                # Further processing for external audit alerts could go here
            else:
                logger.debug(f"Audit Agent: Ignoring self-published alert: {alert_details.get('alert_type')}.")

        except Exception as e:
            logger.error(f"Audit Agent '{self.agent_id}': Error handling self-published alert: {e}", exc_info=True)


    async def _publish_audit_alert(self, alert_type: str, message: str, details: Dict[str, Any], severity: str = "MEDIUM"):
        """
        Publishes an audit alert message to a dedicated topic and potentially to external systems.
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
        await self.broker.publish_message("audit_alerts", alert_message.model_dump())
        logger.log(logging.getLevelName(severity), f"Audit Agent: Published audit alert: {alert_type} - {message}")

        # Integrate with real-time alerting systems based on severity
        # For critical alerts, send a WhatsApp notification
        if severity == "CRITICAL":
            critical_alert_recipient = getattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER', '+1234567890')
            try:
                whatsapp_message = f"🚨 CRITICAL AUDIT ALERT! 🚨\nType: {alert_type}\nMessage: {message}\nDetails: {details}"
                # await self.whatsapp_notifier.send_generic_alert(critical_alert_recipient, whatsapp_message)
                logger.info(f"Audit Agent: Conceptually sent critical WhatsApp alert to {critical_alert_recipient}.")
            except Exception as e:
                logger.error(f"Audit Agent: Failed to send WhatsApp alert: {e}", exc_info=True)

        # External alerting integrations
        await self._send_external_alerts(severity, alert_type, message, details)

    async def _send_external_alerts(self, severity: str, alert_type: str, message: str, details: Dict[str, Any]):
        """
        Sends alerts to external systems: PagerDuty, Slack, and Email.
        """
        # 1. PagerDuty Integration (for CRITICAL and HIGH severity)
        if severity in ["CRITICAL", "HIGH"]:
            try:
                if hasattr(settings, 'PAGERDUTY_API_KEY') and settings.PAGERDUTY_API_KEY:
                    import aiohttp
                    pagerduty_url = "https://events.pagerduty.com/v2/enqueue"
                    payload = {
                        "routing_key": settings.PAGERDUTY_ROUTING_KEY,
                        "event_action": "trigger",
                        "payload": {
                            "summary": f"[{severity}] {alert_type}: {message}",
                            "severity": severity.lower(),
                            "source": self.agent_id,
                            "custom_details": details
                        }
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(pagerduty_url, json=payload) as resp:
                            if resp.status == 202:
                                logger.info(f"Audit Agent: PagerDuty alert sent for {alert_type}")
                            else:
                                logger.warning(f"Audit Agent: PagerDuty alert failed with status {resp.status}")
            except Exception as e:
                logger.error(f"Audit Agent: PagerDuty integration failed: {e}", exc_info=True)

        # 2. Slack Integration (for all severities)
        try:
            if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
                import aiohttp
                severity_emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }
                slack_payload = {
                    "text": f"{severity_emoji.get(severity, '⚪')} *{severity} Audit Alert*",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{severity} Audit Alert: {alert_type}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Message:* {message}\n*Source:* {self.agent_id}\n*Time:* {datetime.now().isoformat()}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Details:*\n```{str(details)[:500]}```"
                            }
                        }
                    ]
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(settings.SLACK_WEBHOOK_URL, json=slack_payload) as resp:
                        if resp.status == 200:
                            logger.info(f"Audit Agent: Slack notification sent for {alert_type}")
                        else:
                            logger.warning(f"Audit Agent: Slack notification failed with status {resp.status}")
        except Exception as e:
            logger.error(f"Audit Agent: Slack integration failed: {e}", exc_info=True)

        # 3. Email Integration (for CRITICAL and HIGH severity)
        if severity in ["CRITICAL", "HIGH"]:
            try:
                if hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST:
                    import aiosmtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = f"[{severity}] Audit Alert: {alert_type}"
                    msg['From'] = getattr(settings, 'SMTP_FROM_EMAIL', 'audit@sansmercantile.com')
                    msg['To'] = getattr(settings, 'AUDIT_ALERT_EMAIL', 'alerts@sansmercantile.com')
                    
                    html_body = f"""
                    <html>
                      <body>
                        <h2 style="color: {'red' if severity == 'CRITICAL' else 'orange'};">{severity} Audit Alert</h2>
                        <p><strong>Type:</strong> {alert_type}</p>
                        <p><strong>Message:</strong> {message}</p>
                        <p><strong>Source:</strong> {self.agent_id}</p>
                        <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
                        <hr>
                        <h3>Details:</h3>
                        <pre>{str(details)}</pre>
                      </body>
                    </html>
                    """
                    msg.attach(MIMEText(html_body, 'html'))
                    
                    await aiosmtplib.send(
                        msg,
                        hostname=settings.SMTP_HOST,
                        port=getattr(settings, 'SMTP_PORT', 587),
                        username=getattr(settings, 'SMTP_USERNAME', None),
                        password=getattr(settings, 'SMTP_PASSWORD', None),
                        use_tls=getattr(settings, 'SMTP_USE_TLS', True)
                    )
                    logger.info(f"Audit Agent: Email alert sent for {alert_type}")
            except Exception as e:
                logger.error(f"Audit Agent: Email integration failed: {e}", exc_info=True)


# Example Usage (for testing PrivAuditAgent in isolation)
async def main_audit_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'AUDIT_MIN_TRADE_CONFIDENCE'):
        settings.AUDIT_MIN_TRADE_CONFIDENCE = 0.15
    if not hasattr(settings, 'AUDIT_MAX_PROPOSAL_VOLUME'):
        settings.AUDIT_MAX_PROPOSAL_VOLUME = 100
    if not hasattr(settings, 'CRITICAL_ALERT_WHATSAPP_NUMBER'):
        settings.CRITICAL_ALERT_WHATSAPP_NUMBER = "+1234567890" # Dummy number

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    audit_agent = PrivAuditAgent(
        agent_id="Priv-Auditor",
        broker=broker,
        persona={"name": "System Auditor", "focus": "Compliance and Integrity"}
    )

    await broker.connect()
    await audit_agent.start()

    logger.info("\n--- Simulating messages for Audit Agent to consume ---")

    # Simulate an arbitration decision
    mock_arbitration_decision = AgentMessage(
        sender_id="ArbitrationEngine",
        message_type=MessageType.DECISION_CONFIRMATION,
        payload={
            "symbol": "EURUSD",
            "action": "BUY",
            "volume": 0.5,
            "confidence": 0.8,
            "arbitration_outcome": "CONSENSUS_REACHED"
        }
    )
    await broker.publish_message("arbitration_decisions", mock_arbitration_decision.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a low-confidence arbitration decision
    mock_low_confidence_decision = AgentMessage(
        sender_id="ArbitrationEngine",
        message_type=MessageType.DECISION_CONFIRMATION,
        payload={
            "symbol": "GBPUSD",
            "action": "SELL",
            "volume": 0.2,
            "confidence": 0.05, # Low confidence
            "arbitration_outcome": "CONSENSUS_REACHED"
        }
    )
    await broker.publish_message("arbitration_decisions", mock_low_confidence_decision.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a trade proposal with high volume
    mock_trade_proposal_high_volume = AgentMessage(
        sender_id="Priv-Strategist",
        message_type=MessageType.TRADE_PROPOSAL,
        payload={
            "agent_id": "Priv-Strategist",
            "symbol": "USDCAD",
            "action": "BUY",
            "volume": 120, # High volume
            "confidence": 0.9,
            "reasoning": "Strong trend"
        }
    )
    await broker.publish_message("trade_proposals", mock_trade_proposal_high_volume.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a critical error notification
    mock_critical_error = AgentMessage(
        sender_id="Priv-Execution",
        message_type=MessageType.ERROR_NOTIFICATION,
        payload={
            "source_agent_id": "Priv-Execution",
            "message": "Failed to execute trade due to API timeout.",
            "severity": "CRITICAL",
            "error_code": "EX001"
        }
    )
    await broker.publish_message("error_notifications", mock_critical_error.model_dump())
    await asyncio.sleep(0.5)

    # Simulate a compliance violation
    mock_compliance_violation = AgentMessage(
        sender_id="Priv-Compliance",
        message_type=MessageType.STATUS_UPDATE, # Using STATUS_UPDATE for now, could be new type
        payload={
            "agent_id": "Priv-Strategist",
            "violation_type": "regulatory_breach",
            "description": "Attempted trade in restricted asset.",
            "timestamp": datetime.now().isoformat()
        }
    )
    await broker.publish_message("compliance_violations", mock_compliance_violation.model_dump())
    await asyncio.sleep(0.5)


    await asyncio.sleep(5) # Give time for the audit agent to process messages

    await audit_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivAuditAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_audit_agent_test())
