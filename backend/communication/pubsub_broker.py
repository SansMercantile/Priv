"""
In-process Pub/Sub Broker for Agent Communication
Handles publish-subscribe messaging between all agents using Python's asyncio
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PubSubMessage:
    """Standard message format for agent communication"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    sender_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PubSubMessage":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            topic=data.get("topic", ""),
            sender_id=data.get("sender_id", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {})
        )


class PubSubBroker:
    """
    In-process Pub/Sub Broker for agent communication
    Supports topic-based pub/sub with async message delivery
    """
    
    def __init__(self):
        self._topics: Dict[str, List[asyncio.Queue]] = {}
        self._subscribers: Dict[str, Set[str]] = {}  # subscription_id -> set of topics
        self._callbacks: Dict[str, Callable] = {}  # subscription_id -> callback
        self._lock = asyncio.Lock()
        self.is_connected = True
        logger.info("PubSubBroker initialized")
    
    async def connect(self) -> bool:
        """Connect to broker (no-op for in-process broker)"""
        self.is_connected = True
        logger.info("PubSubBroker connected")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from broker"""
        self.is_connected = False
        logger.info("PubSubBroker disconnected")
    
    async def publish_message(
        self, 
        topic: str, 
        message: Dict[str, Any], 
        sender_id: str = "system",
        target_recipient_id: Optional[str] = None
    ) -> None:
        """
        Publish a message to a topic
        
        Args:
            topic: Topic name to publish to
            message: Message payload
            sender_id: ID of the sending agent
            target_recipient_id: Optional specific recipient
        """
        if not self.is_connected:
            logger.warning("Broker not connected, cannot publish")
            return
        
        # Create standardized message
        pubsub_msg = PubSubMessage(
            topic=topic,
            sender_id=sender_id,
            payload=message,
            metadata={"target": target_recipient_id} if target_recipient_id else {}
        )
        
        async with self._lock:
            # Create topic if it doesn't exist
            if topic not in self._topics:
                self._topics[topic] = []
                logger.info(f"Created new topic: {topic}")
            
            # Deliver to all subscribers
            for queue in self._topics[topic]:
                try:
                    await queue.put(pubsub_msg)
                except Exception as e:
                    logger.error(f"Error delivering message to queue: {e}")
        
        logger.debug(f"Published to topic '{topic}': {pubsub_msg.id}")
    
    async def subscribe_to_topic(
        self, 
        topic: str, 
        callback: Callable[[Dict[str, Any]], Any],
        subscription_id: str
    ) -> None:
        """
        Subscribe to a topic with a callback
        
        Args:
            topic: Topic name to subscribe to
            callback: Async callback function to handle messages
            subscription_id: Unique subscription identifier
        """
        if not self.is_connected:
            logger.warning("Broker not connected, cannot subscribe")
            return
        
        async with self._lock:
            # Create topic if it doesn't exist
            if topic not in self._topics:
                self._topics[topic] = []
            
            # Track subscription
            if subscription_id not in self._subscribers:
                self._subscribers[subscription_id] = set()
            self._subscribers[subscription_id].add(topic)
            
            # Store callback
            self._callbacks[subscription_id] = callback
        
        logger.info(f"Subscribed {subscription_id} to topic '{topic}'")
        
        # Create message queue for this subscription
        message_queue: asyncio.Queue = asyncio.Queue()
        
        async with self._lock:
            self._topics[topic].append(message_queue)
        
        # Start listening for messages
        asyncio.create_task(self._listen_for_messages(subscription_id, message_queue, callback))
    
    async def _listen_for_messages(
        self,
        subscription_id: str,
        message_queue: asyncio.Queue,
        callback: Callable
    ) -> None:
        """Listen for messages on a queue and invoke callback"""
        try:
            while self.is_connected:
                try:
                    # Wait for message with timeout
                    msg: PubSubMessage = await asyncio.wait_for(
                        message_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Invoke callback
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            result = await callback(msg.to_dict())
                        else:
                            result = callback(msg.to_dict())
                        logger.debug(f"Callback executed for {subscription_id}: {msg.id}")
                    except Exception as e:
                        logger.error(f"Error in callback for {subscription_id}: {e}", exc_info=True)
                
                except asyncio.TimeoutError:
                    # No message received, continue waiting
                    continue
                
        except asyncio.CancelledError:
            logger.info(f"Listener for {subscription_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message listener {subscription_id}: {e}", exc_info=True)
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe a subscription"""
        async with self._lock:
            if subscription_id in self._subscribers:
                del self._subscribers[subscription_id]
            if subscription_id in self._callbacks:
                del self._callbacks[subscription_id]
        logger.info(f"Unsubscribed {subscription_id}")
    
    def get_topics(self) -> List[str]:
        """Get list of all topics"""
        return list(self._topics.keys())
    
    def get_subscribers_for_topic(self, topic: str) -> int:
        """Get number of subscribers for a topic"""
        if topic not in self._topics:
            return 0
        return len(self._topics[topic])
    
    async def publish_request(
        self,
        topic: str,
        request_data: Dict[str, Any],
        sender_id: str,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Publish a request and wait for a response
        This is a simple RPC-style pattern for agent communication
        
        Args:
            topic: Topic to publish request to
            request_data: Request payload
            sender_id: ID of the agent making the request
            timeout: How long to wait for response
            
        Returns:
            Response data or None if timeout
        """
        request_id = str(uuid.uuid4())
        response_queue = asyncio.Queue()
        response_topic = f"response.{request_id}"
        
        # Create response subscription
        async def response_callback(msg: Dict[str, Any]) -> None:
            await response_queue.put(msg)
        
        await self.subscribe_to_topic(
            response_topic,
            response_callback,
            f"response-{request_id}"
        )
        
        # Send request
        request_data["_request_id"] = request_id
        request_data["_response_topic"] = response_topic
        
        await self.publish_message(
            topic,
            request_data,
            sender_id=sender_id
        )
        
        # Wait for response
        try:
            response = await asyncio.wait_for(response_queue.get(), timeout=timeout)
            return response.get("payload", {})
        except asyncio.TimeoutError:
            logger.warning(f"No response received for request {request_id} on topic {topic}")
            return None
        finally:
            # Clean up response subscription
            await self.unsubscribe(f"response-{request_id}")


# Global broker instance
_broker_instance: Optional[PubSubBroker] = None


def get_broker() -> PubSubBroker:
    """Get or create the global broker instance"""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = PubSubBroker()
    return _broker_instance


# Convenience functions
async def publish_to_topic(
    topic: str,
    message: Dict[str, Any],
    sender_id: str = "system"
) -> None:
    """Publish a message to a topic"""
    broker = get_broker()
    await broker.publish_message(topic, message, sender_id=sender_id)


async def subscribe_to_topic(
    topic: str,
    callback: Callable,
    subscription_id: str
) -> None:
    """Subscribe to a topic"""
    broker = get_broker()
    await broker.subscribe_to_topic(topic, callback, subscription_id)


async def send_request(
    topic: str,
    request: Dict[str, Any],
    sender_id: str,
    timeout: float = 30.0
) -> Optional[Dict[str, Any]]:
    """Send a request and wait for response"""
    broker = get_broker()
    return await broker.publish_request(topic, request, sender_id, timeout)
