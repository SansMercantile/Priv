# backend/quantum/__init__.py
"""
Quantum Computing Module

Enables quantum computing simulations on standard hardware (CPU/GPU).
"""

import logging

logger = logging.getLogger(__name__)

__all__ = []

try:
    from .standard_hardware_quantum_adapter import (
        StandardHardwareQuantumAdapter,
        BasicQuantumSimulator
    )
    __all__.extend(["StandardHardwareQuantumAdapter", "BasicQuantumSimulator"])
except Exception as e:
    logger.warning(f"Quantum adapter not available: {e}")
    StandardHardwareQuantumAdapter = None
    BasicQuantumSimulator = None

