import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Constants from Ind-WSOdWROaTrend_Line.mq4
DEFAULT_PERIOD: int = 9 # nPeriod in MQL, used for Lowest/Highest lookback
DEFAULT_LIMIT: int = 350 # Limit in MQL, maximum bars to process back.

def detect_wso_wro_trend_lines(
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    bar_times: np.ndarray,
    period: int = DEFAULT_PERIOD,
    limit: int = DEFAULT_LIMIT
) -> Dict[str, Any]:
    """
    Detects Widners Oscillator Support (WSO) and Widners Oscillator Resistance (WRO)
    trend lines based on Ind-WSOdWROaTrend_Line.mq4 logic.

    This indicator finds significant swing highs and lows over a `period`
    and considers them as potential support and resistance levels.

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of closing prices.
        bar_times (np.ndarray): Array of bar timestamps.
        period (int): The period used for finding Highest/Lowest points (nPeriod in MQL).
        limit (int): The maximum number of bars to process (Limit in MQL).

    Returns:
        Dict[str, Any]: A dictionary containing lists of detected WSO (support) and
                        WRO (resistance) levels, each with price and time.
    """
    detected_levels = {
        "wso_support_levels": [],  # Widners Oscillator Support (Low points)
        "wro_resistance_levels": [] # Widners Oscillator Resistance (High points)
    }

    rates_total = len(high_prices)
    if rates_total < period + 1:
        logger.warning(f"Insufficient data for WSO/WRO detection. Need at least {period+1} bars, got {rates_total}.")
        return detected_levels

    # Ensure limit does not exceed available data
    actual_limit = min(limit, rates_total)

    # In MQL, `Lowest` and `Highest` are used. These functions find the index of the lowest/highest
    # value within a specified number of bars (shift, count, index).
    # For Python, we can use rolling window functions or explicit iteration.

    # The MQL code iterates from `Limit` down to 0, which means from an older bar
    # towards the current bar. We will iterate from oldest relevant bar to current.
    # The `nCurBar + (nPeriod-1)/2` in MQL implies looking at the middle of the period
    # and comparing it to the extreme within that period.

    # Let's collect a few recent significant highs and lows as per the MQL logic
    # The MQL indicator stores up to 6 `r`/`s` values (highs/lows).

    temp_highs = [] # Stores (price, bar_index) for WRO
    temp_lows = []  # Stores (price, bar_index) for WSO

    # Process from `rates_total - actual_limit` up to `rates_total - 1`
    # We need a lookback period for `Highest` and `Lowest`
    for i in range(rates_total - actual_limit, rates_total):
        # Ensure we have enough data for the lookback period centered around `i`
        # The MQL uses `nCurBar + (nPeriod-1)/2` as the center of the period for the extreme.
        # This implies a range that extends before and after `i`.
        
        # To replicate `Lowest(NULL,0,MODE_LOW,nPeriod,nCurBar)`:
        # It means finding the lowest low over `nPeriod` bars, ending at `nCurBar`.
        # So for bar `i`, we look back `period` bars.
        lookback_start = max(0, i - period)
        current_period_lows = low_prices[lookback_start : i + 1]
        current_period_highs = high_prices[lookback_start : i + 1]

        if len(current_period_lows) < period or len(current_period_highs) < period:
            continue # Not enough data for the current period

        # Check for potential WSO (Support) point
        # A bar `low_prices[i]` is a potential WSO if it's the lowest in its `period` window.
        # MQL: `Low[nCurBar + (nPeriod-1)/2] == Low[Lowest(NULL,0,MODE_LOW,nPeriod,nCurBar)]`
        # This means the current low at the center of the period is the actual lowest in that window.
        # This is typically interpreted as a fractal low or a swing low.
        
        # Let's simplify: A low is significant if it's the lowest in its lookback window.
        if i >= period - 1: # Ensure enough bars for the lookback window
            current_window_lows = low_prices[i - (period - 1) : i + 1]
            if low_prices[i] == np.min(current_window_lows):
                # We need to refine this to only capture significant pivots, not every lowest low.
                # The MQL code stores up to 6 `s` points (support).
                # To avoid too many points, we can add a condition that the point is
                # sufficiently far from the previous detected point, or that price
                # has reversed significantly after it.
                
                # For now, let's just collect these local minima
                if not any(np.isclose(low_prices[i], val['price'], atol=1e-5) for val in temp_lows): # Avoid near-duplicates
                    temp_lows.append({"price": float(low_prices[i]), "time": bar_times[i].isoformat(), "index": i})
                    # Keep only the latest `x` significant points, similar to how MQL updates s1, s2, etc.
                    if len(temp_lows) > 6: # Keep track of last 6 or so
                        temp_lows.pop(0) # Remove oldest

            # Check for potential WRO (Resistance) point
            if high_prices[i] == np.max(current_window_highs):
                if not any(np.isclose(high_prices[i], val['price'], atol=1e-5) for val in temp_highs): # Avoid near-duplicates
                    temp_highs.append({"price": float(high_prices[i]), "time": bar_times[i].isoformat(), "index": i})
                    if len(temp_highs) > 6: # Keep track of last 6 or so
                        temp_highs.pop(0) # Remove oldest
    
    # Sort detected points by time (most recent last)
    detected_levels["wso_support_levels"] = sorted(temp_lows, key=lambda x: x['time'])
    detected_levels["wro_resistance_levels"] = sorted(temp_highs, key=lambda x: x['time'])

    # The MQL also draws Trend Lines based on WSO/WRO points (`Trend DN-`, `Trend UP-`).
    # This implies identifying a sequence of at least two such points to form a line.
    # For now, we return the points. Trend line drawing based on these points would be a separate step
    # or a visualization task for the frontend.

    return detected_levels

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Generate some mock price data with clear swings
    data_len = 150
    dates = pd.date_range(start='2023-01-01', periods=data_len, freq='D')
    
    # Simulate an uptrend with pullbacks (for support) and then a downtrend with rallies (for resistance)
    closes = np.linspace(100, 110, data_len) + np.sin(np.linspace(0, 20, data_len)) * 2
    highs = closes + np.random.rand(data_len) * 0.5 + 0.1 # Add some noise
    lows = closes - np.random.rand(data_len) * 0.5 - 0.1 # Add some noise

    # Add a distinct low swing for WSO
    lows[50:55] = np.array([98.0, 97.5, 97.0, 97.5, 98.0])
    closes[52] = 97.0

    # Add a distinct high swing for WRO
    highs[100:105] = np.array([112.0, 113.5, 114.0, 113.5, 112.0])
    closes[102] = 114.0

    # Ensure high >= close >= low
    highs = np.maximum(highs, closes)
    lows = np.minimum(lows, closes)


    print("\n--- Detecting WSO/WRO Trend Lines ---")
    detected_s_r = detect_wso_wro_trend_lines(highs, lows, closes, dates.to_numpy(), period=DEFAULT_PERIOD, limit=DEFAULT_LIMIT)

    print("WSO Support Levels Detected:")
    for level in detected_s_r["wso_support_levels"]:
        print(f"  Price: {level['price']:.5f}, Time: {level['time']}, Index: {level['index']}")

    print("\nWRO Resistance Levels Detected:")
    for level in detected_s_r["wro_resistance_levels"]:
        print(f"  Price: {level['price']:.5f}, Time: {level['time']}, Index: {level['index']}")

    if not detected_s_r["wso_support_levels"] and not detected_s_r["wro_resistance_levels"]:
        print("No significant WSO/WRO levels detected in sample data.")