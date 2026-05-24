# backend/data_sourcing/iot_sensory_ingestor.py

import asyncio
import json
import logging
import random
import time
from typing import Any, Dict, Optional

# NEW: Import paho-mqtt for real sensor integration.
# This library needs to be added to your requirements.txt or environment.yml
import paho.mqtt.client as mqtt

from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.config.settings import Settings

# Create settings instance
_settings = Settings()

logger = logging.getLogger(__name__)

class SimulatedIoTSensor:
    """Simulates an IoT sensor generating environmental data."""

    async def read_data(self) -> Dict[str, Any]:
        """Generates a simulated sensor reading."""
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate network latency
        return {
            "timestamp": time.time(),
            "temperature_celsius": round(random.uniform(18.0, 25.0), 2),
            "humidity_percent": round(random.uniform(40.0, 60.0), 2),
            "light_lux": round(random.uniform(300.0, 1500.0), 2),
            "sound_db": round(random.uniform(30.0, 55.0), 2),
            "source": "simulated"
        }

class RealIoTSensor:
    """
    Connects to a real IoT sensor network via an MQTT broker.
    This class is a concrete implementation for live environmental data.
    """
    def __init__(self, broker_url: str, port: int, topic: str, username: Optional[str] = None, password: Optional[str] = None):
        self.broker_url = broker_url
        self.port = port
        self.topic = topic
        self.latest_data: Optional[Dict[str, Any]] = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        if username and password:
            self.client.username_pw_set(username, password)
        self._is_connected = False
        self.connection_lock = asyncio.Lock()

    def _on_connect(self, client, userdata, flags, rc, properties):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logger.info(f"Successfully connected to MQTT Broker at {self.broker_url}")
            client.subscribe(self.topic)
            logger.info(f"Subscribed to MQTT topic: {self.topic}")
            self._is_connected = True
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code {rc}")
            self._is_connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            # Add metadata to the received data
            data['source'] = 'real_iot_mqtt'
            data['received_at'] = time.time()
            self.latest_data = data
            logger.debug(f"Received real IoT data: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from MQTT message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    async def connect(self):
        """Connects to the MQTT broker asynchronously."""
        async with self.connection_lock:
            if not self._is_connected:
                try:
                    logger.info(f"Attempting to connect to MQTT broker: {self.broker_url}:{self.port}")
                    self.client.connect(self.broker_url, self.port, 60)
                    self.client.loop_start()
                    # Wait a moment to establish connection
                    await asyncio.sleep(2)
                    if not self._is_connected:
                       logger.error("MQTT connection attempt timed out or failed in callback.")
                except Exception as e:
                    logger.error(f"Exception while connecting to MQTT broker: {e}", exc_info=True)
                    self._is_connected = False
        return self._is_connected

    async def disconnect(self):
        """Disconnects from the MQTT broker."""
        if self._is_connected:
            self.client.loop_stop()
            self.client.disconnect()
            self._is_connected = False
            logger.info("Disconnected from MQTT Broker.")

    async def read_data(self) -> Optional[Dict[str, Any]]:
        """
        Returns the latest data received from the MQTT topic.
        This is not a blocking call; it returns the last known value.
        """
        if not self._is_connected:
            logger.warning("Cannot read data, MQTT client is not connected.")
            return None
        return self.latest_data


class SensoryDataIngestor:
    """
    Orchestrates the ingestion of sensory data from either simulated or real sources
    and publishes it to the message broker.
    """
    def __init__(self, broker: MessageBrokerInterface):
        self.broker = broker
        if _settings.ENABLE_REAL_IOT_SENSORS:
            logger.info("Initializing RealIoTSensor for live environmental data.")
            self.sensor = RealIoTSensor(
                broker_url=_settings.MQTT_BROKER_URL,
                port=_settings.MQTT_BROKER_PORT,
                topic=_settings.MQTT_TOPIC_ENVIRONMENTAL,
                username=_settings.MQTT_USERNAME,
                password=_settings.MQTT_PASSWORD
            )
        else:
            logger.info("Initializing SimulatedIoTSensor for mock environmental data.")
            self.sensor = SimulatedIoTSensor()

    async def initialize(self):
        """Initializes the sensor connection if it's a real sensor."""
        if isinstance(self.sensor, RealIoTSensor):
            await self.sensor.connect()

    async def run_ingestion_cycle(self):
        """
        Reads data from the configured sensor and publishes it.
        For real sensors, it publishes the latest received data.
        For simulated sensors, it actively fetches a new reading.
        """
        try:
            sensory_data = await self.sensor.read_data()
            if sensory_data:
                await self.broker.publish_message("sensory_data", sensory_data)
                logger.info(f"Published sensory data to broker: {sensory_data}")
            else:
                logger.debug("No new sensory data to publish in this cycle.")
        except Exception as e:
            logger.error(f"Error during sensory data ingestion cycle: {e}", exc_info=True)

    async def shutdown(self):
        """Shuts down the sensor connection if applicable."""
        if isinstance(self.sensor, RealIoTSensor):
            await self.sensor.disconnect()
