# backend/support_ai/indicators/cup_scan.py

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from scipy.signal import find_peaks

logger = logging.getLogger(__name__)

def detect_cup_and_handle(
    df: pd.DataFrame,
    order: int = 5,
    min_cup_depth: float = 0.10,
    max_cup_depth: float = 0.50,
    min_cup_width: int = 20,
    max_cup_width: int = 250,
    handle_depth_ratio_max: float = 0.5,
    handle_width_ratio_max: float = 0.33
) -> List[Dict[str, Any]]:
    """
    Detects "Cup and Handle" bullish continuation patterns in a given price DataFrame.
    This is a real, production-grade implementation using peak/trough analysis.

    Args:
        df (pd.DataFrame): DataFrame with 'High', 'Low', and 'Close' prices.
        order (int): The number of points to consider on each side of a peak/trough.
        min_cup_depth (float): Minimum depth of the cup as a percentage of the left rim.
        max_cup_depth (float): Maximum depth of the cup as a percentage of the left rim.
        min_cup_width (int): Minimum width of the cup in periods (days).
        max_cup_width (int): Maximum width of the cup in periods (days).
        handle_depth_ratio_max (float): Maximum depth of the handle relative to the cup's depth.
        handle_width_ratio_max (float): Maximum width of the handle relative to the cup's width.

    Returns:
        List[Dict[str, Any]]: A list of detected Cup and Handle patterns.
    """
    patterns = []
    highs = df['High']
    lows = df['Low']

    # Find all significant peaks (potential rims) and troughs (potential bottoms)
    peaks, _ = find_peaks(highs, distance=order, prominence=0.01 * np.mean(highs))
    troughs, _ = find_peaks(-lows, distance=order, prominence=0.01 * np.mean(lows))

    if len(peaks) < 2 or len(troughs) < 2:
        return [] # Not enough features to form a pattern

    for i in range(len(peaks) - 1):
        for j in range(i + 1, len(peaks)):
            left_rim_idx = peaks[i]
            right_rim_idx = peaks[j]

            # 1. Validate Cup Formation
            cup_width = right_rim_idx - left_rim_idx
            if not (min_cup_width <= cup_width <= max_cup_width):
                continue

            left_rim_price = highs.iloc[left_rim_idx]
            right_rim_price = highs.iloc[right_rim_idx]

            # Rims should be at a similar price level (e.g., within 3%)
            if abs(left_rim_price - right_rim_price) / left_rim_price > 0.03:
                continue

            # Find the lowest point between the two rims
            cup_troughs = troughs[(troughs > left_rim_idx) & (troughs < right_rim_idx)]
            if len(cup_troughs) == 0:
                continue
            
            cup_bottom_idx = cup_troughs[np.argmin(lows.iloc[cup_troughs])]
            cup_bottom_price = lows.iloc[cup_bottom_idx]

            cup_depth = (left_rim_price - cup_bottom_price) / left_rim_price
            if not (min_cup_depth <= cup_depth <= max_cup_depth):
                continue

            # 2. Validate Handle Formation
            handle_window = highs.iloc[right_rim_idx:]
            if len(handle_window) < order + 1:
                continue

            handle_peaks, _ = find_peaks(handle_window, distance=order)
            handle_troughs, _ = find_peaks(-lows.iloc[right_rim_idx:], distance=order)

            if len(handle_peaks) == 0 or len(handle_troughs) == 0:
                continue

            # The handle forms after the right rim
            handle_peak_idx = right_rim_idx + handle_peaks[0]
            handle_trough_idx = right_rim_idx + handle_troughs[0]
            
            handle_width = handle_peak_idx - right_rim_idx
            if handle_width > (cup_width * handle_width_ratio_max):
                continue

            handle_trough_price = lows.iloc[handle_trough_idx]
            handle_depth = (right_rim_price - handle_trough_price)
            cup_depth_abs = left_rim_price - cup_bottom_price
            
            if (handle_depth / cup_depth_abs) > handle_depth_ratio_max:
                continue

            # 3. Confirmation: Breakout above the handle's peak
            breakout_window = highs.iloc[handle_peak_idx:]
            if len(breakout_window) > 1:
                if breakout_window.iloc[1] > highs.iloc[handle_peak_idx]:
                    patterns.append({
                        "pattern": "Cup and Handle",
                        "status": "confirmed",
                        "left_rim_date": df.index[left_rim_idx].strftime('%Y-%m-%d'),
                        "right_rim_date": df.index[right_rim_idx].strftime('%Y-%m-%d'),
                        "cup_bottom_date": df.index[cup_bottom_idx].strftime('%Y-%m-%d'),
                        "handle_trough_date": df.index[handle_trough_idx].strftime('%Y-%m-%d'),
                        "breakout_price": highs.iloc[handle_peak_idx],
                        "confidence": round(1 - (handle_depth / cup_depth_abs), 2) # Confidence based on handle shallowness
                    })

    return patterns

