# backend/multi_agent/sensory_protocol.py

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

class VisionAnalysis(BaseModel):
    """Represents the analysis of a single visual frame."""
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    detected_emotion: str = Field(..., description="e.g., focused, stressed, confused")
    confidence: float = Field(..., ge=0.0, le=1.0)

class AudioAnalysis(BaseModel):
    """Represents the analysis of an audio snippet."""
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    transcribed_text: Optional[str] = Field(None, description="Text from speech-to-text.")
    detected_tone: str = Field(..., description="e.g., calm, agitated, inquisitive")

class EnvironmentalState(BaseModel):
    """Represents the state of the physical environment from IoT sensors."""
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    room_id: str
    readings: Dict[str, float] # e.g., {"temperature_celsius": 22.5, "humidity_percent": 45.1}

class FusedSensoryState(BaseModel):
    """
    A holistic representation of the AI's current sensory awareness.
    This is the output of the Sensory Agent.
    """
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    overall_mood: str = Field(..., description="The synthesized mood (e.g., Calm, Tense, Collaborative).")
    environmental_context: EnvironmentalState
    human_context: Optional[Dict[str, Any]] = Field(None, description="Context from vision and audio.")
