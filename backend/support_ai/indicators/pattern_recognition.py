import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Constants from flag_and_pennant.mq4
FLAG_PERIOD: int = 10
FLAG_MIN_PERIOD: int = 5
PENNANT_PATTERN_FACTOR: float = -10.0
FLAG_PATTERN_FACTOR: float = 5.0

def _calculate_regression(prices: np.ndarray) -> Optional[Tuple[float, float]]:
    """
    Calculates the linear regression (a, b) for a given price series.
    Ported from calc_regression in flag_and_pennant.mq4.

    Args:
        prices (np.ndarray): A numpy array of prices.

    Returns:
        Optional[Tuple[float, float]]: A tuple (a, b) representing the y-intercept and slope
                                       of the regression line, or None if calculation fails.
    """
    if len(prices) == 0:
        return None

    sum_y = 0.0
    sum_x = 0.0
    sum_xy = 0.0
    sum_x2 = 0.0
    cnt = 0

    for x_val in range(len(prices)):
        if prices[x_val] == 0: # Equivalent to MQL's continue for 0 values
            continue
        sum_x += x_val
        sum_x2 += x_val * x_val
        sum_y += prices[x_val]
        sum_xy += prices[x_val] * x_val
        cnt += 1

    if cnt < 2: # Need at least 2 points for a line
        return None

    c_val = sum_x2 * cnt - sum_x * sum_x
    if c_val == 0.0:
        # Vertical line or single point, slope undefined. Handle as flat line.
        b = 0.0
        a = sum_y / cnt
    else:
        b = (sum_xy * cnt - sum_x * sum_y) / c_val
        a = (sum_y - sum_x * b) / cnt
    return a, b

def detect_flag_and_pennant(
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    bar_times: np.ndarray, # Assuming datetime or similar for times
    min_period: int = FLAG_MIN_PERIOD,
    flag_period: int = FLAG_PERIOD,
    pennant_factor: float = PENNANT_PATTERN_FACTOR,
    flag_factor: float = FLAG_PATTERN_FACTOR,
    point_size: float = 0.0001 # Placeholder for broker's point size, adjust as needed
) -> List[Dict[str, Any]]:
    """
    Detects Flag and Pennant continuation patterns.
    Ported logic from flag_and_pennant.mq4.

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of closing prices.
        bar_times (np.ndarray): Array of bar timestamps (for pattern start/end).
        min_period (int): Minimum period for pattern detection.
        flag_period (int): Period to look back for Flag pattern.
        pennant_factor (float): Factor to distinguish Pennant.
        flag_factor (float): Factor to distinguish Flag.
        point_size (float): The broker's point size (e.g., 0.0001 for EURUSD).

    Returns:
        List[Dict[str, Any]]: A list of detected patterns, each with type, direction,
                              and key price/time points.
    """
    detected_patterns = []
    rates_total = len(high_prices)

    if rates_total <= flag_period * 2: # Need enough data for calculations
        return detected_patterns

    for i in range(flag_period, rates_total):
        # Approximate "pole" - a strong directional move before consolidation
        pole_period_lookback = flag_period * 2 # Look further back for pole
        if i < pole_period_lookback:
            continue

        # Use recent closes to determine initial trend for the "pole"
        pole_segment_closes = close_prices[i - pole_period_lookback : i - flag_period]
        if len(pole_segment_closes) < 2:
            continue
        
        pole_start_price = pole_segment_closes[0]
        pole_end_price = pole_segment_closes[-1]
        pole_move = pole_end_price - pole_start_price

        # Check for consolidation (small range relative to pole, and minimal recent slope)
        # using the current `flag_period` prices
        consolidation_highs = high_prices[i - flag_period : i]
        consolidation_lows = low_prices[i - flag_period : i]
        
        if len(consolidation_highs) == 0: # Ensure arrays are not empty
            continue

        consolidation_range = np.max(consolidation_highs) - np.min(consolidation_lows)
        
        # Calculate slope of consolidation period itself
        consolidation_closes = close_prices[i - flag_period : i]
        consolidation_reg_result = _calculate_regression(consolidation_closes)

        if consolidation_reg_result is None:
            continue

        _, consolidation_slope = consolidation_reg_result
        
        # Heuristic for "rest" / consolidation:
        # Consolidation range should be a small fraction of the pole move,
        # and the consolidation slope should be relatively flat compared to the pole.
        # These thresholds are heuristic and may need fine-tuning.
        is_consolidating = False
        if abs(pole_move) > 0.0: # Avoid division by zero
            if consolidation_range < abs(pole_move) * 0.5: # Range less than half of pole
                # Check if consolidation slope is much flatter than if there was a strong trend
                # A simple check: if the slope over the period doesn't change price much.
                if abs(consolidation_slope * flag_period * point_size) < (0.1 * consolidation_range):
                    is_consolidating = True

        if is_consolidating:
            # Analyze pattern within the consolidation range
            # Simplified regression for upper and lower boundaries of the flag/pennant itself
            # These regressions apply to the `flag_period` segment.
            upper_reg = _calculate_regression(consolidation_highs)
            lower_reg = _calculate_regression(consolidation_lows)

            if upper_reg is None or lower_reg is None:
                continue

            _, upper_slope = upper_reg
            _, lower_slope = lower_reg

            # Convert slopes to "angle" in points (simplified from MQL's /_Point)
            # This is a conceptual mapping, actual angular calculation can be complex
            up_angle = upper_slope / point_size
            dn_angle = lower_slope / point_size

            pattern_type = None
            direction = None

            # Bullish Flags/Pennants: Pole is up (positive pole_move), consolidation is down/sideways/slightly up
            if pole_move > 0: # Bullish Pole
                # Pennant: converging lines, smaller range, typically symmetrical or slightly downward sloping in bullish
                # MQL's condition for Pennant: `up_angle - dn_angle < PennantPatternFacter`
                # And for Flag: `up_angle - dn_angle >= PennantPatternFacter && up_angle - dn_angle < FlagPatternFacter`
                # These factors likely relate to the *difference* in slopes.
                
                # For bullish, slopes are typically negative or slightly positive but converging.
                # Here, we interpret `up_angle < 0 and dn_angle < 0` for both sides sloping down.
                # Original MQL: `up_angle-dn_angle<PennantPatternFacter`
                # For `PENNANT_PATTERN_FACTOR = -10.0`, `FLAG_PATTERN_FACTOR = 5.0`
                # If `up_angle - dn_angle` is e.g. -15 (converging sharply downward)
                # This suggests the numbers refer to point difference in some context, not raw angle.
                # Let's interpret the original factors as indicative of the relative 'steepness' and convergence.

                # Assuming flags/pennants are generally counter-trend consolidations.
                # Bullish: price goes up (pole), then consolidates (slopes down or sideways)
                # Bearish: price goes down (pole), then consolidates (slopes up or sideways)
                
                # Let's apply a more direct "converging" logic for pennants, and parallel/down for flags.
                # And ensure slopes are generally counter-trend for flags, or converging for pennants.
                
                # Pennant: converging slopes. Upper slope < 0 (down), Lower slope < 0 (down), but upper more steep.
                # Or for converging: `upper_slope < lower_slope` for bullish (both negative, or upper positive, lower positive, but upper less steep)
                # The MQL's `up_angle-dn_angle` check with negative/positive factors implies specific angular relationships.
                # Let's try to infer from typical pattern definitions.
                
                # Pennant: converging lines. This means upper slope is less than lower slope in context of prices,
                # so upper line is falling faster or rising slower. For bullish after uptrend, this is falling.
                if (upper_slope < 0 and lower_slope < 0 and abs(upper_slope) > abs(lower_slope)) or \
                   (upper_slope > 0 and lower_slope > 0 and upper_slope < lower_slope): # Both falling or both rising but converging
                    # Check convergence magnitude using factors derived from MQL.
                    # The absolute difference between slopes for pennants vs flags.
                    if (abs(up_angle - dn_angle) < abs(pennant_factor)): # Small diff for tight pennant
                        pattern_type = "Pennant"
                        direction = "Bullish"
                    elif (abs(up_angle - dn_angle) >= abs(pennant_factor) and abs(up_angle - dn_angle) < abs(flag_factor)):
                        pattern_type = "Flag" # Broader consolidation, might be parallel or slight slant
                        direction = "Bullish"

            # Bearish Flags/Pennants: Pole is down (negative pole_move), consolidation is up/sideways/slightly down
            elif pole_move < 0: # Bearish Pole
                # Pennant: converging lines. Upper slope > 0 (up), Lower slope > 0 (up), but upper less steep.
                # Or `upper_slope > lower_slope` for bearish (both positive, or upper negative, lower negative, but upper less steep)
                if (upper_slope > 0 and lower_slope > 0 and upper_slope < lower_slope) or \
                   (upper_slope < 0 and lower_slope < 0 and abs(upper_slope) < abs(lower_slope)): # Both rising or both falling but converging
                    if (abs(up_angle - dn_angle) < abs(pennant_factor)):
                        pattern_type = "Pennant"
                        direction = "Bearish"
                    elif (abs(up_angle - dn_angle) >= abs(pennant_factor) and abs(up_angle - dn_angle) < abs(flag_factor)):
                        pattern_type = "Flag"
                        direction = "Bearish"
            
            if pattern_type:
                start_idx = i - flag_period
                end_idx = i - 1 # Last bar before detection

                # Basic pattern details - will need refinement based on exact points from PDF
                pattern_info = {
                    "name": f"{direction} {pattern_type}",
                    "type": "Continuation",
                    "direction": direction,
                    "timeframe": "CURRENT", # Or actual timeframe if passed from data_loader
                    "start_index": start_idx,
                    "end_index": end_idx,
                    "start_time": bar_times[start_idx].isoformat() if bar_times.dtype == 'object' else str(bar_times[start_idx]),
                    "end_time": bar_times[end_idx].isoformat() if bar_times.dtype == 'object' else str(bar_times[end_idx]),
                    "key_points": {
                        "pole_start_price": float(pole_start_price),
                        "pole_end_price": float(pole_end_price),
                        "consolidation_range": float(consolidation_range),
                        "upper_line_slope": float(upper_slope),
                        "lower_line_slope": float(lower_slope)
                    },
                    "confirmation_details": { # Placeholder - add volume, RSI confirmations here
                        "price_consolidation": True,
                        "volume_behavior": "Requires specific volume logic (e.g., decreasing volume during consolidation)"
                    },
                    "strength_score": 0.0, # To be refined with more checks
                    "projected_target": "Requires calculation based on pole length/pattern height"
                }
                detected_patterns.append(pattern_info)
                logger.info(f"Detected: {pattern_info['name']} from {pattern_info['start_time']} to {pattern_info['end_time']}")

    return detected_patterns

# Example usage (mock data for demonstration)
if __name__ == '__main__':
    # Mock OHLCV data for a few bars
    sample_data = {
        'open': np.array([100, 105, 110, 108, 107, 109, 112, 110, 108, 107, 109, 110, 115, 120, 122, 125, 124, 123, 125, 128, 130]),
        'high': np.array([106, 112, 115, 110, 109, 111, 114, 113, 110, 109, 111, 112, 118, 123, 125, 128, 126, 125, 127, 130, 132]),
        'low': np.array([98, 103, 108, 106, 105, 107, 109, 107, 106, 105, 107, 108, 113, 118, 120, 123, 122, 121, 123, 126, 128]),
        'close': np.array([104, 110, 112, 109, 108, 110, 110, 108, 107, 108, 110, 111, 116, 121, 123, 126, 125, 122, 124, 128, 130]),
        'time': np.array(pd.to_datetime(pd.date_range('2023-01-01', periods=21, freq='H')))
    }
    
    # Create an upward pole followed by consolidation for bullish flag/pennant
    bullish_pole_closes = np.linspace(100, 120, 10)
    bullish_consolidation_closes = np.linspace(119, 117, 5) # Slight downward drift
    bullish_consolidation_lows = bullish_consolidation_closes - 0.5
    bullish_consolidation_highs = bullish_consolidation_closes + 0.5
    bullish_breakout_closes = np.linspace(118, 125, 6)

    # Example 1: Simulate a bullish flag
    # Pole: prices 100-120
    # Flag: prices 119-117 (downward slope, converging if we adjust highs/lows)
    
    # Let's create a more explicit bullish flag pattern.
    # Start with an upward impulse (pole)
    pole_length = 20 # bars
    pole_start_price = 100.0
    pole_end_price = 120.0
    
    # Consolidation (Flag)
    flag_length = 10 # bars
    flag_start_price = pole_end_price # 120
    flag_end_price = flag_start_price - 2 # 118, slight downtrend
    
    # Breakout
    breakout_length = 5
    
    # Generate prices for Bullish Flag
    bh = np.linspace(pole_start_price, pole_end_price, pole_length) # Pole highs
    bl = np.linspace(pole_start_price, pole_end_price, pole_length) # Pole lows (just for array size)
    bc = np.linspace(pole_start_price, pole_end_price, pole_length) # Pole closes
    
    # Simulate flag body (slight downward tilt, parallel lines)
    fh = np.linspace(flag_start_price + 0.5, flag_end_price + 0.5, flag_length)
    fl = np.linspace(flag_start_price - 0.5, flag_end_price - 0.5, flag_length)
    fc = np.linspace(flag_start_price, flag_end_price, flag_length)

    # Combine into a larger dataset
    sample_highs = np.concatenate((bh, fh))
    sample_lows = np.concatenate((bl, fl))
    sample_closes = np.concatenate((bc, fc))
    sample_times = np.array(pd.to_datetime(pd.date_range('2023-01-01', periods=len(sample_highs), freq='H')))

    print("\n--- Detecting Bullish Flag ---")
    bullish_flags = detect_flag_and_pennant(
        sample_highs, sample_lows, sample_closes, sample_times,
        flag_period=flag_length, min_period=FLAG_MIN_PERIOD,
        pennant_factor=-10.0, flag_factor=5.0, point_size=0.0001
    )
    if bullish_flags:
        for pattern in bullish_flags:
            print(f"Detected: {pattern['name']} from {pattern['start_time']} to {pattern['end_time']}")
            print(f"  Pole Move: {pattern['key_points']['pole_move']:.2f}")
            print(f"  Consolidation Range: {pattern['key_points']['consolidation_range']:.2f}")
            print(f"  Upper Slope: {pattern['key_points']['upper_line_slope']:.4f}")
            print(f"  Lower Slope: {pattern['key_points']['lower_line_slope']:.4f}")
    else:
        print("No bullish flag detected in sample data.")

    # Example 2: Simulate a bearish flag
    bearish_pole_closes = np.linspace(120, 100, 20)
    bearish_consolidation_closes = np.linspace(101, 103, 10) # Slight upward drift
    
    beh = np.linspace(120, 100, pole_length)
    bel = np.linspace(120, 100, pole_length)
    bec = np.linspace(120, 100, pole_length)
    
    # Simulate flag body (slight upward tilt, parallel lines)
    bfh = np.linspace(100 + 0.5, 102 + 0.5, flag_length)
    bfl = np.linspace(100 - 0.5, 102 - 0.5, flag_length)
    bfc = np.linspace(100, 102, flag_length) # goes slightly up, counter-trend to pole

    sample_highs_b = np.concatenate((beh, bfh))
    sample_lows_b = np.concatenate((bel, bfl))
    sample_closes_b = np.concatenate((bec, bfc))
    sample_times_b = np.array(pd.to_datetime(pd.date_range('2023-01-01', periods=len(sample_highs_b), freq='H')))

    print("\n--- Detecting Bearish Flag ---")
    bearish_flags = detect_flag_and_pennant(
        sample_highs_b, sample_lows_b, sample_closes_b, sample_times_b,
        flag_period=flag_length, min_period=FLAG_MIN_PERIOD,
        pennant_factor=-10.0, flag_factor=5.0, point_size=0.0001
    )
    if bearish_flags:
        for pattern in bearish_flags:
            print(f"Detected: {pattern['name']} from {pattern['start_time']} to {pattern['end_time']}")
            print(f"  Pole Move: {pattern['key_points']['pole_move']:.2f}")
            print(f"  Consolidation Range: {pattern['key_points']['consolidation_range']:.2f}")
            print(f"  Upper Slope: {pattern['key_points']['upper_line_slope']:.4f}")
            print(f"  Lower Slope: {pattern['key_points']['lower_line_slope']:.4f}")
    else:
        print("No bearish flag detected in sample data.")