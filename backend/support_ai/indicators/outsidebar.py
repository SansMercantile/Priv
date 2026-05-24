# backend/support_ai/indicators/outsidebar.py

import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def find_outside_bars(
    high_prices: np.ndarray, 
    low_prices: np.ndarray, 
    close_prices: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Identifies bullish and bearish outside bars in a price series.

    An outside bar is a bar whose high is higher than the previous bar's high,
    and whose low is lower than the previous bar's low.
    - It's considered bullish if it closes in the top 30% of its range.
    - It's considered bearish if it closes in the bottom 30% of its range.

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of close prices.

    Returns:
        List[Dict[str, Any]]: A list of found outside bar patterns, each including
                              its index, direction, and closing price.
    """
    found_patterns = []
    if len(high_prices) < 2:
        return found_patterns

    try:
        # Vectorized check for outside bars
        is_outside_bar = (high_prices[1:] > high_prices[:-1]) & (low_prices[1:] < low_prices[:-1])
        
        # Get the indices where an outside bar occurs
        outside_bar_indices = np.where(is_outside_bar)[0] + 1 # Add 1 to align with main array

        for i in outside_bar_indices:
            bar_range = high_prices[i] - low_prices[i]
            if bar_range > 0:  # Avoid division by zero for doji-like bars
                
                # A bar is bullish if it closes in the upper 30% of its own range
                is_bullish_close = close_prices[i] >= high_prices[i] - (bar_range * 0.3)
                
                # A bar is bearish if it closes in the lower 30% of its own range
                is_bearish_close = close_prices[i] <= low_prices[i] + (bar_range * 0.3)

                direction = None
                # Determine direction, ensuring it's not ambiguous (e.g., closing in the middle)
                if is_bullish_close and not is_bearish_close:
                    direction = "Bullish"
                elif is_bearish_close and not is_bullish_close:
                    direction = "Bearish"
                
                if direction:
                    found_patterns.append({
                        "index": int(i),
                        "direction": direction,
                        "price": float(close_prices[i]),
                        "pattern_name": "Outside Bar"
                    })
    except Exception as e:
        logger.error(f"Error finding outside bars: {e}", exc_info=True)

    return found_patterns

