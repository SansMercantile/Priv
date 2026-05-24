# backend/utils/swift_bridge.py

import ctypes
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SwiftBridge:
    """
    A bridge to call high-performance functions from a compiled Swift library.
    This class uses ctypes to load the shared library (.so file) and define the
    function signatures, enabling seamless integration between Python and Swift.
    """
    def __init__(self, library_path: str = "./lib/libswiftmodule.so"):
        self.swift_lib = None
        try:
            # Check if the library file exists before attempting to load
            if not os.path.exists(library_path):
                raise FileNotFoundError(f"Swift shared library not found at path: {library_path}")

            # Load the compiled Swift shared library
            self.swift_lib = ctypes.CDLL(library_path)
            
            # Define the function signature for the Swift function
            # Corresponds to: @_cdecl("perform_high_performance_calculation")
            self.perform_high_performance_calculation = self.swift_lib.perform_high_performance_calculation
            self.perform_high_performance_calculation.argtypes = [ctypes.c_int, ctypes.c_int]
            self.perform_high_performance_calculation.restype = ctypes.c_int
            
            logger.info(f"Successfully loaded Swift library from {library_path} and bridged functions.")

        except FileNotFoundError as e:
            logger.warning(f"Swift bridge disabled: {e}")
        except Exception as e:
            logger.error(f"Failed to load Swift library or bridge functions: {e}", exc_info=True)
            self.swift_lib = None

    def is_available(self) -> bool:
        """Check if the Swift library was loaded successfully."""
        return self.swift_lib is not None

    def high_performance_task(self, a: int, b: int) -> Optional[int]:
        """
        Executes a high-performance calculation by calling the Swift function.

        Returns:
            The result of the calculation, or None if the bridge is not available.
        """
        if not self.is_available():
            logger.error("Cannot execute high-performance task: Swift bridge is not available.")
            return None
        
        logger.info(f"Calling Swift module to perform calculation with inputs: {a}, {b}")
        result = self.perform_high_performance_calculation(a, b)
        logger.info(f"Received result from Swift module: {result}")
        return result

# --- Singleton Instance ---
# This allows the rest of the application to use a single, configured bridge.
swift_bridge_instance = SwiftBridge()
