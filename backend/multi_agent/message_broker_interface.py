# backend/multi_agent/message_broker_interface.py

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Tuple, Protocol
import asyncio
import json
import os
import base64

# Import project components
from backend.config import settings
from backend.security.pqc_encryption import pqc_encryptor

logger = logging.getLogger(__name__)


# Google Cloud Pub/Sub client libraries
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
try:
    from google.cloud import pubsub_v1
    from google.api_core.exceptions import GoogleAPIError, NotFound, AlreadyExists
    _PUBSUB_CLIENTS_AVAILABLE = not DEMO_MODE
except ImportError:
    logger.warning("Google Cloud Pub/Sub library not found. Using local fallback.")
    _PUBSUB_CLIENTS_AVAILABLE = False
    # Define dummy classes to prevent import errors
    class pubsub_v1: pass
    class GoogleAPIError(Exception): pass
    class NotFound(Exception): pass
    class AlreadyExists(Exception): pass

# A shared, in-memory store for public keys. In a distributed system,
# this MUST be replaced with a proper service like a Redis cache or a database.
PQC_PUBLIC_KEY_STORE: Dict[str, bytes] = {}

class MessageBrokerInterface(Protocol):
    """A protocol defining the interface for a message broker."""
    is_connected: bool

    async def connect(self) -> bool:
        ...

    async def disconnect(self) -> None:
        ...

    async def publish_message(self, topic: str, message: Dict[str, Any], target_recipient_id: Optional[str] = None) -> None:
        ...

    async def subscribe_to_topic(self, topic: str, callback: Callable[[Dict[str, Any]], None], subscription_id: str) -> None:
        ...



# Patch: Use a mock broker for tests/demos (DEMO_MODE)
if _PUBSUB_CLIENTS_AVAILABLE:
    class GoogleCloudPubSubBroker:
        """A real implementation of the message broker using Google Cloud Pub/Sub."""
        # ...existing code (copy the real implementation here)...
        def __init__(self, broker_config: Optional[Dict[str, Any]] = None):
            self.broker_config = broker_config or {}
            self.is_connected = False
            self.project_id = self.broker_config.get("project_id", settings.GCP_PROJECT_ID)
            if not self.project_id:
                raise ValueError("GCP_PROJECT_ID is required for GoogleCloudPubSubBroker.")

            self.pqc_enabled = getattr(settings, 'PQC_ENCRYPTION_ENABLED', False) and pqc_encryptor is not None
            if self.pqc_enabled:
                self.my_pqc_public_key, self.my_pqc_secret_key = pqc_encryptor.generate_keypair()
                self.my_id = f"service_instance_{os.getpid()}"
                PQC_PUBLIC_KEY_STORE[self.my_id] = self.my_pqc_public_key
                logger.info(f"PQC Enabled for broker. Registered public key for '{self.my_id}'.")

            self.publisher_client: Optional[pubsub_v1.PublisherClient] = None
            self.subscriber_client: Optional[pubsub_v1.SubscriberClient] = None
            self._subscription_futures: Dict[str, asyncio.Future] = {}
            self._callbacks: Dict[str, Callable] = {}
            self._main_event_loop: Optional[asyncio.AbstractEventLoop] = None

        async def connect(self) -> bool:
            if not _PUBSUB_CLIENTS_AVAILABLE: return False
            try:
                self.publisher_client = pubsub_v1.PublisherClient()
                self.subscriber_client = pubsub_v1.SubscriberClient()
                self.is_connected = True
                self._main_event_loop = asyncio.get_running_loop()
                logger.info("GoogleCloudPubSubBroker connected successfully.")
                return True
            except Exception as e:
                logger.error(f"GoogleCloudPubSubBroker connection failed: {e}", exc_info=True)
                return False

        async def disconnect(self):
            for future in self._subscription_futures.values():
                future.cancel()
            self.is_connected = False
            logger.info("GoogleCloudPubSubBroker disconnected.")

        async def publish_message(self, topic: str, message: Dict[str, Any], target_recipient_id: Optional[str] = None):
            if not self.is_connected: return
            topic_path = self.publisher_client.topic_path(self.project_id, topic)
            attributes = {}
            payload_bytes = json.dumps(message, default=str).encode('utf-8')
            if self.pqc_enabled and target_recipient_id:
                recipient_public_key = PQC_PUBLIC_KEY_STORE.get(target_recipient_id)
                if recipient_public_key:
                    try:
                        kem_ciphertext, nonce, aead_ciphertext = pqc_encryptor.encrypt_payload(payload_bytes, recipient_public_key)
                        payload_bytes = aead_ciphertext
                        attributes = {
                            "pqc_encrypted": "true",
                            "pqc_kem_ciphertext": base64.b64encode(kem_ciphertext).decode('utf-8'),
                            "pqc_aead_nonce": base64.b64encode(nonce).decode('utf-8'),
                            "pqc_recipient_id": target_recipient_id,
                        }
                    except Exception as e:
                        logger.error(f"PQC encryption failed: {e}. Sending message in plaintext.", exc_info=True)
                else:
                    logger.warning(f"PQC public key for recipient '{target_recipient_id}' not found. Sending in plaintext.")
            try:
                future = self.publisher_client.publish(topic_path, payload_bytes, **attributes)
                await asyncio.to_thread(future.result)
            except NotFound:
                logger.warning(f"Topic '{topic}' not found. Attempting to create it.")
                await self._ensure_topic_exists(topic_path)
                future = self.publisher_client.publish(topic_path, payload_bytes, **attributes)
                await asyncio.to_thread(future.result)
            except Exception as e:
                logger.error(f"Error publishing to '{topic}': {e}", exc_info=True)

        def _message_handler(self, message: "pubsub_v1.subscriber.message.Message"):
            try:
                payload_bytes = message.data
                attributes = message.attributes
                is_pqc_encrypted = attributes.get("pqc_encrypted") == "true"
                recipient_id = attributes.get("pqc_recipient_id")
                if is_pqc_encrypted and self.pqc_enabled and recipient_id == self.my_id:
                    try:
                        kem_ciphertext = base64.b64decode(attributes.get("pqc_kem_ciphertext", ""))
                        nonce = base64.b64decode(attributes.get("pqc_aead_nonce", ""))
                        decrypted_bytes = pqc_encryptor.decrypt_payload(kem_ciphertext, nonce, payload_bytes, self.my_pqc_secret_key)
                        decoded_message = json.loads(decrypted_bytes.decode('utf-8'))
                    except Exception as e:
                        logger.error(f"PQC decryption failed: {e}. Nacking message.", exc_info=True)
                        message.nack()
                        return
                else:
                    decoded_message = json.loads(payload_bytes.decode('utf-8'))
                subscription_path = message.ack_id.split("\n")[0]
                if subscription_path in self._callbacks:
                    callback = self._callbacks[subscription_path]
                    self._main_event_loop.call_soon_threadsafe(lambda: asyncio.create_task(callback(decoded_message)))
                message.ack()
            except Exception as e:
                logger.error(f"Critical error in message handler: {e}", exc_info=True)
                message.nack()

        async def _ensure_topic_exists(self, topic_path: str):
            try:
                await asyncio.to_thread(self.publisher_client.create_topic, name=topic_path)
                logger.info(f"Topic '{topic_path}' created.")
            except AlreadyExists:
                logger.debug(f"Topic '{topic_path}' already exists.")
            except Exception as e:
                logger.error(f"Failed to create topic '{topic_path}': {e}", exc_info=True)

        async def _ensure_subscription_exists(self, subscription_path: str, topic_path: str):
            try:
                await asyncio.to_thread(self.subscriber_client.create_subscription, name=subscription_path, topic=topic_path)
                logger.info(f"Subscription '{subscription_path}' created for topic '{topic_path}'.")
            except AlreadyExists:
                logger.debug(f"Subscription '{subscription_path}' already exists.")
            except Exception as e:
                logger.error(f"Failed to create subscription '{subscription_path}': {e}", exc_info=True)

        async def subscribe_to_topic(self, topic: str, callback: Callable[[Dict[str, Any]], None], subscription_id: str):
            if not self.is_connected: return
            topic_path = self.publisher_client.topic_path(self.project_id, topic)
            subscription_path = self.subscriber_client.subscription_path(self.project_id, subscription_id)
            await self._ensure_topic_exists(topic_path)
            await self._ensure_subscription_exists(subscription_path, topic_path)
            self._callbacks[subscription_path] = callback
            streaming_pull_future = self.subscriber_client.subscribe(subscription_path, callback=self._message_handler)
            self._subscription_futures[subscription_id] = streaming_pull_future
            logger.info(f"Subscribed to '{topic}' via subscription '{subscription_id}'.")
else:
    class GoogleCloudPubSubBroker:
        """Mock implementation for tests/demos: does nothing, never connects to real cloud APIs."""
        def __init__(self, broker_config: Optional[Dict[str, Any]] = None):
            self.broker_config = broker_config or {}
            self.is_connected = True
            self.project_id = self.broker_config.get("project_id", "demo-project")
            self.pqc_enabled = False
        async def connect(self) -> bool:
            logger.info("[MOCK] GoogleCloudPubSubBroker.connect() called.")
            return True
        async def disconnect(self) -> None:
            logger.info("[MOCK] GoogleCloudPubSubBroker.disconnect() called.")
        async def publish_message(self, topic: str, message: Dict[str, Any], target_recipient_id: Optional[str] = None) -> None:
            logger.info(f"[MOCK] Publishing message to topic '{topic}': {message}")
        async def subscribe_to_topic(self, topic: str, callback, subscription_id: str) -> None:
            logger.info(f"[MOCK] Subscribing to topic '{topic}' with subscription_id '{subscription_id}'")

