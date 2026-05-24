"""
priv/backend/agents/base_agent.py
Base class for all Pub/Sub subscriber agents
"""

import os
import json
import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

from google.cloud import pubsub_v1
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all Pub/Sub-based agents.
    Each agent:
    1. Subscribes to one or more Pub/Sub topics
    2. Processes messages asynchronously
    3. Publishes results to output topics
    4. Maintains state in Firestore
    """

    def __init__(
        self,
        agent_name: str,
        project_id: str = None,
        subscription_ids: list = None,
        output_topic: str = None
    ):
        """
        Initialize agent with Pub/Sub and Firestore connections.

        Args:
            agent_name: Unique name for this agent
            project_id: GCP project ID (auto-detected if not provided)
            subscription_ids: List of Pub/Sub subscriptions to listen to
            output_topic: Topic to publish results to
        """
        self.agent_name = agent_name
        self.project_id = project_id or os.getenv("PUBSUB_PROJECT", "priv-dev")
        self.subscription_ids = subscription_ids or []
        self.output_topic = output_topic

        # Initialize Firestore
        self.db = firestore.client()

        # Initialize Pub/Sub
        self.publisher_client = pubsub_v1.PublisherClient()
        self.subscriber_client = pubsub_v1.SubscriberClient()

        # State tracking
        self.is_running = False
        self.futures = []

        logger.info(f"Agent {agent_name} initialized for project {self.project_id}")

    @abstractmethod
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming message. Must be implemented by subclass.

        Args:
            message_data: Parsed message data from Pub/Sub

        Returns:
            Result dict to publish or store
        """
        pass

    async def handle_message_callback(self, message):
        """
        Callback function for Pub/Sub messages.
        Automatically acknowledges after processing.
        """
        try:
            # Parse message
            message_data = json.loads(message.data.decode("utf-8"))
            logger.info(f"[{self.agent_name}] Processing message: {message_data}")

            # Process message
            result = await self.process_message(message_data)

            # Publish result if output topic specified
            if self.output_topic and result:
                await self.publish_message(self.output_topic, result)

            # Update agent state in Firestore
            await self.update_state({
                'last_processed_at': datetime.utcnow().isoformat(),
                'last_message': message_data,
                'last_result': result
            })

            # Acknowledge message
            message.ack()
            logger.debug(f"[{self.agent_name}] Message acknowledged")

        except Exception as e:
            logger.error(f"[{self.agent_name}] Error processing message: {str(e)}")
            message.drop()  # Drop on error, will retry

    async def publish_message(self, topic_name: str, message_data: Dict[str, Any]):
        """
        Publish message to Pub/Sub topic.

        Args:
            topic_name: Topic to publish to
            message_data: Data to publish
        """
        try:
            topic_path = self.publisher_client.topic_path(self.project_id, topic_name)
            message_json = json.dumps(message_data)
            future = self.publisher_client.publish(
                topic_path,
                message_json.encode("utf-8")
            )
            message_id = future.result()
            logger.info(f"[{self.agent_name}] Published message {message_id} to {topic_name}")
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to publish message: {str(e)}")

    async def subscribe_to_topics(self):
        """
        Subscribe to all configured topics.
        """
        for subscription_id in self.subscription_ids:
            try:
                subscription_path = self.subscriber_client.subscription_path(
                    self.project_id, subscription_id
                )

                # Create subscriber with custom flow control
                flow_control = pubsub_v1.types.FlowControl(
                    max_messages=100,
                    max_bytes=1000 * 1024 * 1024  # 1GB
                )

                future = self.subscriber_client.subscribe(
                    subscription_path,
                    callback=self.handle_message_callback,
                    flow_control=flow_control
                )
                self.futures.append(future)

                logger.info(f"[{self.agent_name}] Subscribed to {subscription_id}")

                # Set up exception handler
                future.add_done_callback(self._on_subscription_done)

            except Exception as e:
                logger.error(f"[{self.agent_name}] Failed to subscribe to {subscription_id}: {str(e)}")

    @staticmethod
    def _on_subscription_done(future):
        """Handle subscription completion or error."""
        try:
            future.result()
        except Exception as e:
            logger.error(f"Subscription ended with error: {str(e)}")

    async def update_state(self, state_dict: Dict[str, Any]):
        """
        Update agent state in Firestore.

        Args:
            state_dict: State data to update
        """
        try:
            agent_ref = self.db.collection('agents').document(self.agent_name)
            agent_ref.update({
                'current_state': state_dict,
                'updated_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to update Firestore state: {str(e)}")

    async def get_state(self) -> Dict[str, Any]:
        """Get current agent state from Firestore."""
        try:
            agent_ref = self.db.collection('agents').document(self.agent_name)
            doc = agent_ref.get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception as e:
            logger.error(f"Failed to get Firestore state: {str(e)}")
            return {}

    async def run(self):
        """
        Start agent and listen for messages.
        """
        self.is_running = True
        logger.info(f"[{self.agent_name}] Starting agent...")

        try:
            await self.subscribe_to_topics()

            # Keep agent alive
            while self.is_running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info(f"[{self.agent_name}] Shutting down...")
            self.is_running = False
        except Exception as e:
            logger.error(f"[{self.agent_name}] Fatal error: {str(e)}")
            self.is_running = False

    def stop(self):
        """Stop the agent gracefully."""
        self.is_running = False
        for future in self.futures:
            future.cancel()
        logger.info(f"[{self.agent_name}] Agent stopped")
