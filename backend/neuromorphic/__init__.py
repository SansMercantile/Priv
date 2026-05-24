# backend/neuromorphic/__init__.py
"""
Neuromorphic Computing Module

Enables neuromorphic computing using standard cameras instead of specialized hardware.
"""

import logging

logger = logging.getLogger(__name__)

__all__ = []

try:
    from .camera_neuromorphic_adapter import CameraNeuromorphicAdapter
    __all__.append("CameraNeuromorphicAdapter")
except Exception as e:
    logger.warning(f"Camera neuromorphic adapter not available: {e}")
    CameraNeuromorphicAdapter = None

try:
    from .spiking_neural_network import SpikingNeuralNetwork, LeakyIntegrateFireNeuron
    __all__.extend(["SpikingNeuralNetwork", "LeakyIntegrateFireNeuron"])
except Exception as e:
    logger.warning(f"Spiking neural network not available: {e}")
    SpikingNeuralNetwork = None
    LeakyIntegrateFireNeuron = None

