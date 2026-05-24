"""
Base Agent Class with Pub/Sub Integration
All PRIV agents inherit from this class to enable seamless communication
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from backend.communication.pubsub_broker import (
    get_broker,
    publish_to_topic,
    subscribe_to_topic,
    send_request
)

logger = logging.getLogger(__name__)


class Agent(ABC):
    """
    Base class for all PRIV agents
    Provides Pub/Sub communication, lifecycle management, and message handling
    """
    
    def __init__(self, agent_id: str, agent_type: str, topics: Optional[List[str]] = None):
        """
        Initialize agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (e.g., 'strategist', 'risk', 'execution')
            topics: List of topics this agent subscribes to
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.subscribe_topics = topics or [f"agent.{agent_type}"]
        self.status = "initializing"
        self.created_at = datetime.utcnow().isoformat()
        self.broker = get_broker()
        self._tasks: List[asyncio.Task] = []
        self._message_handlers: Dict[str, Any] = {}
        logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")
    
    async def start(self) -> None:
        """Start the agent and connect to Pub/Sub"""
        try:
            # Ensure broker is connected
            if not self.broker.is_connected:
                await self.broker.connect()
            
            # Subscribe to topics
            for topic in self.subscribe_topics:
                await subscribe_to_topic(
                    topic,
                    self._handle_message,
                    f"{self.agent_id}-{topic}"
                )
            
            # Run agent-specific initialization
            await self._initialize()
            
            self.status = "running"
            logger.info(f"Agent {self.agent_id} started and subscribed to {self.subscribe_topics}")
        
        except Exception as e:
            logger.error(f"Error starting agent {self.agent_id}: {e}", exc_info=True)
            self.status = "error"
            raise
    
    async def stop(self) -> None:
        """Stop the agent"""
        try:
            # Cancel all tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to finish
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            
            # Run agent-specific cleanup
            await self._cleanup()
            
            self.status = "stopped"
            logger.info(f"Agent {self.agent_id} stopped")
        
        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}", exc_info=True)
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Agent-specific initialization - override in subclasses"""
        pass
    
    @abstractmethod
    async def _cleanup(self) -> None:
        """Agent-specific cleanup - override in subclasses"""
        pass
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message from Pub/Sub
        Override in subclasses to implement agent-specific logic
        
        Args:
            message: Message payload
            
        Returns:
            Response data if this is a request, None otherwise
        """
        pass
    
    async def _handle_message(self, full_message: Dict[str, Any]) -> None:
        """
        Internal message handler that wraps process_message
        Handles request/response patterns and error handling
        """
        try:
            # Check if this is a request that needs a response
            request_id = full_message.get("payload", {}).get("_request_id")
            response_topic = full_message.get("payload", {}).get("_response_topic")
            
            # Process the message
            response = await self.process_message(full_message.get("payload", {}))
            
            # Send response if requested
            if request_id and response_topic and response is not None:
                await publish_to_topic(
                    response_topic,
                    response,
                    sender_id=self.agent_id
                )
        
        except Exception as e:
            logger.error(f"Error handling message in {self.agent_id}: {e}", exc_info=True)
    
    async def publish_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish a message to a topic"""
        await publish_to_topic(topic, message, sender_id=self.agent_id)
    
    async def send_request(
        self,
        topic: str,
        request: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request to another agent and wait for response
        
        Args:
            topic: Topic to send request to
            request: Request payload
            timeout: How long to wait for response
            
        Returns:
            Response data or None if timeout
        """
        return await send_request(topic, request, self.agent_id, timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at,
            "subscribed_topics": self.subscribe_topics,
            "num_active_tasks": sum(1 for t in self._tasks if not t.done())
        }
    
    async def log_activity(self, activity: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log agent activity to a central topic"""
        await publish_to_topic(
            "agent.log",
            {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "activity": activity,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            },
            sender_id=self.agent_id
        )
