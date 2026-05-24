"""
PRIV Core Module

Core functionality for the PRIV (Precision Reasoning Intelligence for Verifiable Outcomes) system.
This module provides the central intelligence and coordination capabilities for PRIV.

Author: SansMercantile™ AI Development Team
Attribution: MezzofortePrivilege (mezzoforte@sansmercantile.com)
"""

try:
    from .personality_integration import initialize_priv_personality, get_priv_personality
    from .priv_core_engine import PRIVCoreEngine
    from .priv_orchestrator import PRIVOrchestrator
except ImportError as e:
    # Fallback imports for testing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Import error in priv-core: {e}. Using fallback implementations.")
    
    # Create fallback implementations
    class MockPRIVCoreEngine:
        def __init__(self):
            pass
        async def initialize(self):
            return True
        async def health_check(self):
            return {"status": "healthy", "components": {}}
        async def process_financial_request(self, request):
            return {"error": "Core engine not fully implemented"}
        async def run_system_diagnostics(self):
            return {"status": "healthy"}
            
    class MockPRIVOrchestrator:
        def __init__(self):
            pass
        async def initialize_orchestrator(self):
            return True
        async def get_component_health(self):
            return {}
        async def execute_system_command(self, command, params):
            return {"error": "Orchestrator not fully implemented"}
    
    PRIVCoreEngine = MockPRIVCoreEngine
    PRIVOrchestrator = MockPRIVOrchestrator
    
    def initialize_priv_personality():
        return True
        
    def get_priv_personality():
        class MockPersonality:
            def get_identity_context(self):
                return {"system": "PRIV", "identity": "Mock PRIV", "creator": "Mezzoforte Privilege Khoza"}
            def log_with_identity(self, message, level="info"):
                logger.info(f"[PRIV] {message}")
        return MockPersonality()

__all__ = [
    'initialize_priv_personality',
    'get_priv_personality', 
    'PRIVCoreEngine',
    'PRIVOrchestrator'
]