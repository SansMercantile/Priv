# backend/multi_agent/priv_notification_agent.py

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .priv_agent import PrivAgent
from .priv_agent_protocol import AgentType, MessageType

logger = logging.getLogger(__name__)

class PRIVNotificationAgent(PrivAgent):
    """
    Notification Agent for PRIV system.
    Handles system notifications, alerts, and communication routing.
    """
    
    def __init__(self, agent_id: str, message_broker, broker, persona: Dict[str, Any]):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.NOTIFICATION,
            message_broker=message_broker,
            broker=broker,
            persona=persona
        )
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{agent_id}")
        self.logger.info(f"PRIVNotificationAgent initialized: {agent_id}")
    
    async def process_notification(self, notification_type: str, payload: Dict[str, Any]) -> bool:
        """
        Process different types of notifications.
        
        Args:
            notification_type: Type of notification (alert, update, warning, etc.)
            payload: Notification data
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Processing {notification_type} notification: {payload}")
            
            # Route notification based on type
            if notification_type == "system_alert":
                await self._handle_system_alert(payload)
            elif notification_type == "trade_notification":
                await self._handle_trade_notification(payload)
            elif notification_type == "security_alert":
                await self._handle_security_alert(payload)
            else:
                await self._handle_generic_notification(notification_type, payload)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing notification: {e}", exc_info=True)
            return False
    
    async def _handle_system_alert(self, payload: Dict[str, Any]):
        """Handle system-level alerts"""
        self.logger.warning(f"System Alert: {payload.get('message', 'Unknown alert')}")
        
        # Publish to message broker
        agent_message = {
            "sender_id": self.agent_id,
            "message_type": MessageType.SYSTEM_ALERT,
            "payload": {
                "alert_type": "system",
                "message": payload.get("message", "System alert"),
                "timestamp": datetime.now().isoformat(),
                "severity": payload.get("severity", "medium")
            }
        }
        
        await self.message_broker.publish_message("system_alerts", agent_message)
    
    async def _handle_trade_notification(self, payload: Dict[str, Any]):
        """Handle trade-related notifications"""
        self.logger.info(f"Trade Notification: {payload.get('symbol', 'Unknown')}")
        
        agent_message = {
            "sender_id": self.agent_id,
            "message_type": MessageType.STATUS_UPDATE,
            "payload": {
                "notification_type": "trade",
                "symbol": payload.get("symbol"),
                "action": payload.get("action"),
                "price": payload.get("price"),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.message_broker.publish_message("trade_notifications", agent_message)
    
    async def _handle_security_alert(self, payload: Dict[str, Any]):
        """Handle security-related alerts"""
        self.logger.warning(f"Security Alert: {payload.get('threat_type', 'Unknown threat')}")
        
        agent_message = {
            "sender_id": self.agent_id,
            "message_type": MessageType.SYSTEM_ALERT,
            "payload": {
                "alert_type": "security",
                "threat_type": payload.get("threat_type"),
                "severity": payload.get("severity", "high"),
                "description": payload.get("description", "Security alert triggered"),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.message_broker.publish_message("security_alerts", agent_message)
    
    async def _handle_generic_notification(self, notification_type: str, payload: Dict[str, Any]):
        """Handle generic notifications"""
        self.logger.info(f"Generic Notification ({notification_type}): {payload}")
        
        agent_message = {
            "sender_id": self.agent_id,
            "message_type": MessageType.STATUS_UPDATE,
            "payload": {
                "notification_type": notification_type,
                "data": payload,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.message_broker.publish_message("general_notifications", agent_message)
    
    async def broadcast_message(self, message: str, priority: str = "normal"):
        """Broadcast a message to all relevant channels"""
        self.logger.info(f"Broadcasting message (priority: {priority}): {message}")
        
        broadcast_message = {
            "sender_id": self.agent_id,
            "message_type": MessageType.BROADCAST,
            "payload": {
                "message": message,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Broadcast to multiple channels based on priority
        channels = ["broadcasts"]
        if priority == "high":
            channels.extend(["urgent_alerts", "system_alerts"])
        elif priority == "critical":
            channels.extend(["urgent_alerts", "system_alerts", "emergency"])
        
        for channel in channels:
            await self.message_broker.publish_message(channel, broadcast_message)
    
    async def handle_message(self, message: Dict[str, Any]) -> bool:
        """Handle incoming messages"""
        try:
            message_type = message.get("message_type")
            payload = message.get("payload", {})
            
            if message_type == MessageType.TASK:
                # Handle task requests
                task_type = payload.get("task_type")
                if task_type == "send_notification":
                    return await self.process_notification(
                        payload.get("notification_type", "generic"),
                        payload.get("notification_data", {})
                    )
                elif task_type == "broadcast_message":
                    await self.broadcast_message(
                        payload.get("message", ""),
                        payload.get("priority", "normal")
                    )
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}", exc_info=True)
            return False