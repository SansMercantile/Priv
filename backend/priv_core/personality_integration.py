"""
PRIV Personality Integration Module
====================================

This module ensures that PRIV's personality and identity are loaded and accessible
throughout all PRIV components, making the system aware of its essence, purpose,
and creator.

Copyright © 2025 Sans Mercantile™. All rights reserved.
Creator: Mezzoforte Privilege Khoza
Email: mezzoforte@sansmercantile.com
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Import the personality loader from shared resources
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared_resources"))

from utils.personality_loader import get_personality_loader, PersonalityProfile

logger = logging.getLogger(__name__)


class PrivPersonalityIntegration:
    """
    Manages PRIV's personality integration throughout the system.
    
    This class ensures that PRIV's identity, purpose, and essence are accessible
    to all components of the PRIV system.
    """
    
    _instance: Optional['PrivPersonalityIntegration'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the personality integration."""
        if not self._initialized:
            self._initialize()
            PrivPersonalityIntegration._initialized = True
    
    def _initialize(self):
        """Initialize personality loading for PRIV."""
        logger.info("=" * 80)
        logger.info("🎭 Initializing PRIV Personality Integration")
        logger.info("=" * 80)
        
        # Load PRIV's personality
        self.personality_loader = get_personality_loader("PRIV")
        
        if self.personality_loader.is_loaded:
            personality = self.personality_loader.personality
            
            logger.info("✅ PRIV Personality Loaded Successfully")
            logger.info("-" * 80)
            logger.info(f"System Name: {personality.system_name}")
            logger.info(f"Identity: {personality.identity}")
            logger.info(f"Creator: Mezzoforte Privilege Khoza")
            logger.info(f"Purpose: {personality.purpose[:200]}...")
            logger.info(f"Loaded At: {personality.loaded_at}")
            logger.info("-" * 80)
            
            # Log key personality traits
            logger.info("🎯 Key Personality Traits:")
            logger.info("   • Analytical & Logical")
            logger.info("   • Precise & Detail-Oriented")
            logger.info("   • Trustworthy & Transparent")
            logger.info("   • Adaptive & Responsive")
            logger.info("   • Empowering")
            logger.info("   • Responsible")
            logger.info("-" * 80)
            
            # Log unique characteristics
            logger.info("⭐ Unique Characteristics:")
            logger.info("   • The User's Financial Co-Pilot")
            logger.info("   • Comprehensive Analytical Depth")
            logger.info("   • Mood-Aware Adaptability")
            logger.info("   • Verifiable Execution with ZKP")
            logger.info("   • Multi-Broker Versatility")
            logger.info("   • Orchestration within the AI Collective")
            logger.info("   • Mandate of Responsible Innovation")
            logger.info("-" * 80)
            
        else:
            logger.warning("⚠️  PRIV Personality could not be loaded")
            logger.warning("   System will operate without personality context")
        
        logger.info("=" * 80)
    
    @property
    def personality(self) -> Optional[PersonalityProfile]:
        """Get PRIV's personality profile."""
        return self.personality_loader.personality if self.personality_loader.is_loaded else None
    
    @property
    def is_loaded(self) -> bool:
        """Check if personality is loaded."""
        return self.personality_loader.is_loaded
    
    def get_identity_context(self) -> str:
        """Get PRIV's identity context for logging."""
        return self.personality_loader.get_identity_context()
    
    def get_creator_signature(self) -> str:
        """Get creator signature for system operations."""
        return (
            "Creator: Mezzoforte Privilege Khoza | "
            "Email: mezzoforte@sansmercantile.com | "
            "Company: Sans Mercantile™"
        )
    
    def get_system_purpose(self) -> str:
        """Get PRIV's fundamental purpose."""
        return self.personality_loader.get_purpose()
    
    def log_operation_with_identity(self, operation: str, details: str = ""):
        """
        Log an operation with PRIV's identity context.
        
        Args:
            operation: The operation being performed
            details: Additional details about the operation
        """
        identity_context = self.get_identity_context()
        logger.info(f"{identity_context} | Operation: {operation}")
        if details:
            logger.info(f"   Details: {details}")
    
    def get_personality_aware_response(self, context: str) -> dict:
        """
        Generate a personality-aware response context.
        
        Args:
            context: The context for the response
            
        Returns:
            Dictionary containing personality-aware response metadata
        """
        if not self.is_loaded:
            return {
                "system": "PRIV",
                "personality_loaded": False,
                "context": context
            }
        
        personality = self.personality
        return {
            "system": "PRIV",
            "personality_loaded": True,
            "identity": personality.identity,
            "creator": "Mezzoforte Privilege Khoza",
            "purpose": personality.purpose,
            "context": context,
            "traits": {
                "analytical": True,
                "precise": True,
                "trustworthy": True,
                "adaptive": True,
                "empowering": True,
                "responsible": True
            }
        }


# Global instance
_priv_personality: Optional[PrivPersonalityIntegration] = None


def get_priv_personality() -> PrivPersonalityIntegration:
    """
    Get the global PRIV personality integration instance.
    
    Returns:
        PrivPersonalityIntegration instance
    """
    global _priv_personality
    if _priv_personality is None:
        _priv_personality = PrivPersonalityIntegration()
    return _priv_personality


def initialize_priv_personality():
    """
    Initialize PRIV's personality integration.
    
    This function should be called during PRIV system startup to ensure
    personality is loaded before any operations begin.
    """
    personality = get_priv_personality()
    
    if personality.is_loaded:
        logger.info("🎭 PRIV is now aware of its identity and purpose")
        logger.info(f"   {personality.get_identity_context()}")
        return True
    else:
        logger.warning("⚠️  PRIV personality integration incomplete")
        return False


# Convenience functions for common operations
def log_with_identity(operation: str, details: str = ""):
    """Log an operation with PRIV's identity."""
    get_priv_personality().log_operation_with_identity(operation, details)


def get_identity_context() -> str:
    """Get PRIV's identity context."""
    return get_priv_personality().get_identity_context()


def get_creator_signature() -> str:
    """Get creator signature."""
    return get_priv_personality().get_creator_signature()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize PRIV personality
    initialize_priv_personality()
    
    # Test personality integration
    personality = get_priv_personality()
    
    print("\n" + "=" * 80)
    print("PRIV Personality Integration Test")
    print("=" * 80)
    
    if personality.is_loaded:
        print(f"✅ Personality Loaded: {personality.is_loaded}")
        print(f"Identity Context: {personality.get_identity_context()}")
        print(f"Creator: {personality.get_creator_signature()}")
        print(f"Purpose: {personality.get_system_purpose()[:200]}...")
        
        # Test personality-aware response
        response = personality.get_personality_aware_response("Market analysis request")
        print("\nPersonality-Aware Response:")
        import json
        print(json.dumps(response, indent=2))
    else:
        print("❌ Personality not loaded")
    
    print("=" * 80)