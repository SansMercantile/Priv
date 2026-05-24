# backend/support_ai/indicators/elliott_wave/zigzags.py

import numpy as np
from typing import List, Any, Optional
import logging

# Import the core get_swing_points function from the parent indicators directory
from backend.support_ai.indicators.zigzag import get_swing_points as fast_zigzag_get_swing_points

logger = logging.getLogger(__name__)

# This is a Python translation of the MQL 'Points' struct
class Points:
    """
    A data class to store the values, indices, and fixed status of zigzag points.
    Corresponds to the 'Points' struct in the original MQL Elliott Wave code.
    """
    def __init__(self):
        self.value: List[float] = []
        self.index: List[int] = []
        self.fixed: List[int] = [] # 1 for fixed, 0 for unfixed, -1 for not used
        self.num_zigzag: int = 0 # Number of zigzags (points - 1)

    def append(self, value: float, index: int, fixed_status: int = 0):
        self.value.append(value)
        self.index.append(index)
        self.fixed.append(fixed_status)

    def at(self, position: int) -> float:
        """Helper to get value at a specific position, handling out-of-bounds."""
        if 0 <= position < len(self.value):
            return self.value[position]
        return 0.0 # MQL often defaults to 0 for uninitialized doubles

    def clear(self):
        self.value.clear()
        self.index.clear()
        self.fixed.clear()
        self.num_zigzag = 0


# This is a Python translation of the MQL 'Zigzag' class (single zigzag instance)
class Zigzag:
    """
    Represents a single Zigzag line, storing its swing points.
    Corresponds to the 'Zigzag' class in zigzags.mqh.
    """
    def __init__(self, param: int, index1: int, index2: int, type_val: Any, high_prices: np.ndarray, low_prices: np.ndarray):
        self.index: List[int] = []
        self.value: List[float] = []
        
        # The 'param' in MQL often controls deviation or lookback.
        # Here we map it to the deviation for get_swing_points.
        # Assuming 'param' is a deviation value in points, convert to percentage if needed.
        # For simplicity, let's assume 'param' directly relates to the deviation percentage.
        deviation_pct = float(param) / 10.0 # Example: if param=5, deviation=0.5%

        # Use the Numba-optimized get_swing_points to get raw swings
        # Filter these swings to the index1, index2 range
        all_swings = fast_zigzag_get_swing_points(high_prices, low_prices, deviation=deviation_pct)
        
        # Filter swings within the specified index range
        filtered_swings = [
            s for s in all_swings
            if index1 <= s['index'] <= index2
        ]

        # Populate self.index and self.value from filtered swings
        for swing in filtered_swings:
            self.index.append(int(swing['index']))
            self.value.append(float(swing['price']))

        # The 'type_val' parameter in MQL's Zigzag constructor (TYPE1, TYPE2, etc.)
        # influenced how the last point was added. This logic needs to be fully
        # translated if specific end-point handling is required.
        # For now, we rely on fast_zigzag_get_swing_points to define the swings.

    def get_total(self) -> int:
        return len(self.index)

    def get_index(self) -> List[int]:
        return self.index

    def get_value(self) -> List[float]:
        return self.value

    def find_index(self, key: int, less: bool) -> int:
        """
        Binary search to find the index of a swing point.
        Translated from MQL's find_index.
        """
        left = 0
        right = len(self.index) - 1
        result_idx = -1

        while left <= right:
            middle = (left + right) // 2
            if key < self.index[middle]:
                right = middle - 1
            elif key > self.index[middle]:
                left = middle + 1
            else:
                return middle # Exact match found

        if less:
            return right # Return index of largest element less than key
        else:
            return left # Return index of smallest element greater than or equal to key


# This is a Python translation of the MQL 'Zigzags' class (collection of Zigzag instances)
class Zigzags: # Inherits from CArrayObj in MQL, here we use a list
    """
    A collection of Zigzag lines, representing different deviation parameters.
    Corresponds to the 'Zigzags' class in zigzags.mqh.
    """
    def __init__(self):
        self.zigzags_collection: List[Zigzag] = []
        self.high_prices: Optional[np.ndarray] = None
        self.low_prices: Optional[np.ndarray] = None

    def create(self, high_prices: np.ndarray, low_prices: np.ndarray, analysis_type: Any):
        """
        Creates multiple Zigzag instances with varying parameters.
        Corresponds to the 'create' method in zigzags.mqh.
        """
        self.remove() # Clear any existing zigzags
        self.high_prices = high_prices
        self.low_prices = low_prices

        # The MQL code iterates 'param++' to create multiple zigzags.
        # This typically means different deviation settings.
        # Let's create a few zigzags with different deviation parameters.
        # The original MQL had 'param = 1' and incremented it.
        # We'll use a range of deviations (e.g., 1.0% to 5.0%).
        
        # Example deviation parameters (these should ideally be configurable)
        deviation_params = [1.0, 2.0, 3.0, 4.0, 5.0] # Corresponds to MQL 'param'
        
        for param in deviation_params:
            # The Zigzag constructor in MQL took index1, index2, type.
            # Here, index1=0, index2=len(prices)-1 to cover the full range.
            zigzag_instance = Zigzag(
                param=param,
                index1=0,
                index2=len(high_prices) - 1,
                type_val=analysis_type, # Pass analysis_type if needed by Zigzag constructor
                high_prices=high_prices,
                low_prices=low_prices
            )
            if zigzag_instance.get_total() >= 2: # Must have at least two points for a zigzag
                self.zigzags_collection.append(zigzag_instance)
            else:
                logger.debug(f"Skipping zigzag with param {param} due to insufficient points.")
        
        logger.info(f"Created {len(self.zigzags_collection)} zigzag instances.")


    def remove(self):
        """Clears all stored Zigzag instances."""
        self.zigzags_collection.clear()
        self.high_prices = None
        self.low_prices = None

    def total(self) -> int:
        """Returns the number of Zigzag instances in the collection."""
        return len(self.zigzags_collection)

    def at(self, index: int) -> Optional[Zigzag]:
        """Returns a Zigzag instance at the given index."""
        if 0 <= index < len(self.zigzags_collection):
            return self.zigzags_collection[index]
        return None

    def get_points(self, num_points: int, index1: int, index2: int, value1: float, value2: float, points_obj: Points, num_zigzag_total: int) -> bool:
        """
        Extracts a sequence of `num_points` swing points from one of the stored Zigzag instances
        within a specified range and populates a `Points` object.

        This is a Python translation of the complex combinatorial logic from zigzags.mqh's get_points.
        It iterates through different zigzag instances and combinations of points to find a valid sequence.
        """
        points_obj.clear() # Clear previous points

        # Iterate through the collection of zigzags (from different 'param' settings)
        # The MQL code iterates from num_zigzag_total down to 0.
        for i in range(num_zigzag_total - 1, -1, -1):
            zigzag_instance = self.at(i)
            if zigzag_instance is None:
                continue

            zigzag_indices = zigzag_instance.get_index()
            zigzag_values = zigzag_instance.get_value()

            # Find the start and end points within this specific zigzag instance
            # using its find_index method.
            temp_index1_pos = zigzag_instance.find_index(index1, False) # Find first index >= index1
            temp_index2_pos = zigzag_instance.find_index(index2, True)  # Find first index <= index2

            # Ensure valid range and enough points
            if temp_index1_pos == -1 or temp_index2_pos == -1 or temp_index1_pos > temp_index2_pos:
                continue # Invalid range or no points found in this zigzag

            n = temp_index2_pos - temp_index1_pos + 1 # Number of points in this segment of the zigzag

            if n >= num_points:
                # Check if the start/end values match the required value1/value2 (if provided)
                # This is a crucial part of the MQL logic to fix specific points.
                value_check_failed = False
                if value1 > 0 and (abs(zigzag_values[temp_index1_pos] - value1) > 1e-6 or zigzag_indices[temp_index1_pos] != index1):
                    value_check_failed = True
                if value2 > 0 and (abs(zigzag_values[temp_index2_pos] - value2) > 1e-6 or zigzag_indices[temp_index2_pos] != index2):
                    value_check_failed = True
                
                if value_check_failed:
                    continue # This zigzag instance doesn't match the fixed points

                # If checks pass, populate the points_obj
                points_obj.num_zigzag = i # Store which zigzag instance was used
                for j in range(temp_index1_pos, temp_index2_pos + 1):
                    if len(points_obj.value) < num_points: # Only add up to num_points
                        points_obj.append(zigzag_values[j], zigzag_indices[j], 1) # Assume fixed for now

                if len(points_obj.value) == num_points:
                    return True # Found a valid sequence

        return False # No valid sequence found across all zigzags

