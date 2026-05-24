# Module: shared_resources/utils/personality_loader.py
# Provides the personality loader class and profiles for the PRIV system and AGI framework.

import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class PersonalityProfile:
    system_name: str = "PRIV"
    identity: str = "PRIV Financial Co-Pilot"
    purpose: str = (
        "PRIV is designed to be the ultimate personal financial assistant and trading co-pilot, "
        "providing security, transparency, and state-of-the-art multi-broker orchestration "
        "to discover market opportunities responsibly under the mandate of innovation."
    )
    loaded_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

class PersonalityLoader:
    def __init__(self, system_name: str = "PRIV"):
        self.system_name = system_name
        self.is_loaded = True
        self.personality = PersonalityProfile(system_name=system_name)

    def get_identity_context(self) -> str:
        return f"[{self.system_name} Identity Tracker]"

    def get_purpose(self) -> str:
        return self.personality.purpose

def get_personality_loader(system_name: str = "PRIV") -> PersonalityLoader:
    return PersonalityLoader(system_name)
