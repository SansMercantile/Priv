import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

# Constants from atr_3lwma.mq4
# InpSigPeriod=14; InpFastPeriod=25; InpSlowPeriod=50;
# SigMaPeriod=(int)MathCeil(InpSigPeriod/5); etc.
DEFAULT_SIG_PERIOD: int = 14
DEFAULT_FAST_PERIOD: int = 25
DEFAULT_SLOW_PERIOD: int = 50

def _calculate_true_range(high: float, low: float, close_prev: float) -> float:
    """
    Calculates the True Range for a single bar.
    TR = max(High - Low, abs(High - Close_prev), abs(Low - Close_prev))
    """
    return max(high - low, abs(high - close_prev), abs(low - close_prev))

def _calculate_atr(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculates the Average True Range (ATR).
    This is a basic ATR calculation, often smoothed using an EMA in standard libraries.
    The MQL version's `calc_atr` seems to calculate a simple average of True Ranges
    and then feeds that into an LWMA. We'll simplify to a direct ATR for flexibility.
    """
    true_ranges = []
    if len(close_prices) < period + 1: # Need previous close for first TR
        return np.array([])

    for i in range(1, len(high_prices)):
        close_prev = close_prices[i-1]
        tr = _calculate_true_range(high_prices[i], low_prices[i], close_prev)
        true_ranges.append(tr)
    
    if len(true_ranges) < period:
        return np.array([])
        
    # Simple Moving Average of True Range for initial ATR, not EMA as in standard TA-Lib
    # MQL's `calc_atr` uses `lwma_atr` on a simple array of True Ranges.
    atr_values = np.array([np.mean(true_ranges[j:j+period]) for j in range(len(true_ranges) - period + 1)])
    
    # Pad with NaNs at the beginning to align with original price series length
    return np.pad(atr_values, (len(high_prices) - len(atr_values), 0), 'constant', constant_values=np.nan)


def _lwma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculates the Linear Weighted Moving Average (LWMA).
    Ported from lwma_atr in atr_3lwma.mq4.
    """
    if len(data) < period:
        return np.full(len(data), np.nan)

    weights = np.arange(1, period + 1)
    weighted_sum = np.sum(weights)

    lwma_values = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        current_data = data[i - period + 1 : i + 1]
        if not np.isnan(current_data).any():
            lwma_values[i] = np.sum(current_data * weights) / weighted_sum
    return lwma_values

def calculate_atr_3lwma(
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    sig_period: int = DEFAULT_SIG_PERIOD,
    fast_period: int = DEFAULT_FAST_PERIOD,
    slow_period: int = DEFAULT_SLOW_PERIOD
) -> Dict[str, np.ndarray]:
    """
    Calculates the ATR 3LWMA indicator with three lines (Signal, Fast, Slow).
    Translated from atr_3lwma.mq4.

    Args:
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of closing prices.
        sig_period (int): Period for the Signal ATR.
        fast_period (int): Period for the Fast ATR.
        slow_period (int): Period for the Slow ATR.

    Returns:
        Dict[str, np.ndarray]: Dictionary containing 'sig_atr_lwma', 'fast_atr_lwma', 'slow_atr_lwma'.
    """
    if len(high_prices) != len(low_prices) or len(high_prices) != len(close_prices):
        raise ValueError("Price arrays must have the same length.")

    # Calculate raw ATR for each period
    # Note: The MQL `calc_atr` in `atr_3lwma.mq4` implicitly computes a simple average of TRs
    # then `lwma_atr` computes LWMA of that. A standard TA-Lib ATR uses EMA smoothing.
    # We will mimic the MQL's approach of simple average TR for ATR, then LWMA of that.
    
    sig_atr_raw = _calculate_atr(high_prices, low_prices, close_prices, sig_period)
    fast_atr_raw = _calculate_atr(high_prices, low_prices, close_prices, fast_period)
    slow_atr_raw = _calculate_atr(high_prices, low_prices, close_prices, slow_period)

    # Calculate LWMA of the ATRs
    sig_atr_lwma = _lwma(sig_atr_raw, int(np.ceil(sig_period / 5))) # SigMaPeriod = (int)MathCeil(InpSigPeriod/5)
    fast_atr_lwma = _lwma(fast_atr_raw, int(np.ceil(fast_period / 5))) # FastMaPeriod = (int)MathCeil(InpFastPeriod/5)
    slow_atr_lwma = _lwma(slow_atr_raw, int(np.ceil(slow_period / 5))) # SlowMaPeriod = (int)MathCeil(InpSlowPeriod/5)

    return {
        "sig_atr_lwma": sig_atr_lwma,
        "fast_atr_lwma": fast_atr_lwma,
        "slow_atr_lwma": slow_atr_lwma
    }