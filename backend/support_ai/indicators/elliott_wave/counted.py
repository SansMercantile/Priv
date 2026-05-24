# backend/support_ai/indicators/elliott_wave/counted.py

from typing import List, Dict, Any, Optional
import logging

# Assuming Wave and Node are defined in the same package
from .wave import Wave
from .node import Node

logger = logging.getLogger(__name__)

class Counted:
    """
    Implements a caching mechanism for Elliott Wave analysis to avoid redundant calculations.
    This corresponds to the 'Counted' class in the original MQL Elliott Wave code.
    It stores information about already analyzed wave segments.
    """
    def __init__(self):
        # A simple dictionary to store cached results.
        # The key can be a tuple representing the wave's key characteristics (e.g., start_index, end_index, pattern_name).
        # The value could be a boolean (if counted) or a reference to the node/wave.
        self.cache: Dict[str, bool] = {}
        logger.debug("Counted cache initialized.")

    def _generate_key(self, wave: Wave, num_wave: int, node: Node, name_subwaves: str) -> str:
        """
        Generates a unique key for caching based on the wave segment's properties.
        This key should represent the unique combination of parameters that define a wave analysis state.
        """
        # For simplicity, let's use a combination of wave indices, level, and subwave names.
        # In a full translation, this key generation would precisely mirror MQL's logic.
        key_elements = [
            wave.index[0], wave.index[1], # Start and end indices of the wave
            wave.level,                   # Wave level
            num_wave,                     # Current sub-wave number being analyzed
            name_subwaves                 # Names of subwaves being considered
            # You might add more elements like wave.value[0], wave.value[1] if they define uniqueness
        ]
        return "_".join(map(str, key_elements))

    def is_counted(self, wave: Wave, num_wave: int, node: Node, name_subwaves: str) -> bool:
        """
        Checks if a specific wave analysis state has already been counted (analyzed).

        Args:
            wave (Wave): The current Wave object being analyzed.
            num_wave (int): The number of the sub-wave being considered.
            node (Node): The current Node in the analysis tree.
            name_subwaves (str): The names of subwaves being considered.

        Returns:
            bool: True if this state has already been counted, False otherwise.
        """
        key = self._generate_key(wave, num_wave, node, name_subwaves)
        if key in self.cache:
            logger.debug(f"Cache hit for key: {key}")
            return True
        
        logger.debug(f"Cache miss for key: {key}. Marking as counted.")
        self.cache[key] = True # Mark as counted
        return False

    def clear(self):
        """
        Clears the entire cache.
        """
        self.cache.clear()
        logger.debug("Counted cache cleared.")

