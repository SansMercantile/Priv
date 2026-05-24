# backend/multi_agent/priv_sensory_agent.py

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .priv_agent import PrivAgent
from .priv_agent_protocol import AgentMessage, MessageType, AgentType
from .message_broker_interface import MessageBrokerInterface
from .sensory_protocol import VisionAnalysis, AudioAnalysis, EnvironmentalState, FusedSensoryState
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivSensoryAgent(PrivAgent):
    """
    A specialized agent that processes and fuses various sensory inputs (vision,
    audio, environmental) into a holistic awareness state.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id, agent_type=AgentType.SENSORY, message_broker=message_broker, broker=broker, persona=persona)
        self.latest_vision: Optional[VisionAnalysis] = None
        self.latest_environment: Optional[EnvironmentalState] = None
        # Add other sensory states as needed (e.g., audio)

    async def start(self):
        if self.is_running: return
        self.is_running = True
        # This agent subscribes to the outputs of various sensory APIs/ingestors
        await self.broker.subscribe_to_topic("analyzed_vision_data", self._handle_vision_data, f"{self.agent_id}-vision-sub")
        await self.broker.subscribe_to_topic("iot_sensory_data", self._handle_environmental_data, f"{self.agent_id}-iot-sub")
        logger.info(f"SensoryAgent '{self.agent_id}' started and subscribed to sensory data topics.")

    async def stop(self):
        self.is_running = False
        logger.info(f"SensoryAgent '{self.agent_id}' stopped.")

    async def _handle_vision_data(self, message_payload: Dict[str, Any]):
        try:
            self.latest_vision = VisionAnalysis(**message_payload)
            logger.debug(f"SensoryAgent received new vision data: Emotion '{self.latest_vision.detected_emotion}'")
            await self.fuse_and_publish_state()
        except Exception as e:
            logger.error(f"Error handling vision data: {e}", exc_info=True)

    async def _handle_environmental_data(self, message_payload: Dict[str, Any]):
        try:
            self.latest_environment = EnvironmentalState(**message_payload)
            logger.debug(f"SensoryAgent received new environmental data: {self.latest_environment.readings}")
            await self.fuse_and_publish_state()
        except Exception as e:
            logger.error(f"Error handling environmental data: {e}", exc_info=True)

    async def fuse_and_publish_state(self):
        """
        Fuses the latest sensory data into a single state and publishes it.
        """
        if not self.latest_environment:
            return # Wait for at least environmental data

        # --- Fusion Logic ---
        # This is where the AI's "mood" is determined based on inputs.
        mood = "Calm"
        temp = self.latest_environment.readings.get("temperature_celsius", 22)
        
        human_context = {}
        if self.latest_vision:
            human_context['vision'] = self.latest_vision.model_dump()
            if self.latest_vision.detected_emotion in ["stressed", "confused", "agitated"]:
                mood = "Tense"
            elif self.latest_vision.detected_emotion == "focused":
                mood = "Collaborative"

        if temp > 28:
            mood = "Agitated" # High temperature can affect mood

        fused_state = FusedSensoryState(
            overall_mood=mood,
            environmental_context=self.latest_environment,
            human_context=human_context if human_context else None
        )

        # Publish the fused state for other agents to use
        state_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            payload=fused_state.model_dump()
        )
        await self.broker.publish_message("fused_sensory_state", state_message.model_dump())
        logger.info(f"SensoryAgent published new fused state. Overall Mood: {mood}")
