import numpy as np

# Make numba optional for performance optimization
try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Fallback: njit becomes a no-op decorator
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Numba not available. ZigZag calculations will be slower but functional.")
from typing import Tuple

@njit
def _fast_zigzag(
    high: np.ndarray, 
    low: np.ndarray, 
    deviation: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    A performant Numba-compiled ZigZag indicator to identify swing points.
    
    Args:
        high (np.ndarray): Array of high prices.
        low (np.ndarray): Array of low prices.
        deviation (float): The minimum price deviation (in percentage) to form a new swing.

    Returns:
        A tuple containing:
        - p (np.ndarray): Indices of the pivot points.
        - v (np.ndarray): Values (prices) at the pivot points.
        - t (np.ndarray): Type of pivot (1 for high, -1 for low).
        - h (np.ndarray): The high of the bar at the pivot point.
    """
    p = np.full(high.shape[0], np.nan)
    v = np.full(high.shape[0], np.nan)
    t = np.full(high.shape[0], np.nan)
    h = np.full(high.shape[0], np.nan)

    last_pivot_val = high[0]
    last_pivot_idx = 0
    trend = 1

    p[0] = 0
    v[0] = last_pivot_val
    t[0] = trend
    h[0] = high[0]
    p_idx = 1

    for i in range(1, high.shape[0]):
        if trend == 1:
            if high[i] > last_pivot_val:
                last_pivot_val = high[i]
                last_pivot_idx = i
            elif low[i] < last_pivot_val * (1 - deviation / 100):
                p[p_idx] = last_pivot_idx
                v[p_idx] = last_pivot_val
                t[p_idx] = trend
                h[p_idx] = high[last_pivot_idx]
                p_idx += 1
                
                trend = -1
                last_pivot_val = low[i]
                last_pivot_idx = i
        else: # trend == -1
            if low[i] < last_pivot_val:
                last_pivot_val = low[i]
                last_pivot_idx = i
            elif high[i] > last_pivot_val * (1 + deviation / 100):
                p[p_idx] = last_pivot_idx
                v[p_idx] = last_pivot_val
                t[p_idx] = trend
                h[p_idx] = high[last_pivot_idx]
                p_idx += 1

                trend = 1
                last_pivot_val = high[i]
                last_pivot_idx = i

    return p[:p_idx], v[:p_idx], t[:p_idx], h[:p_idx]

def get_swing_points(
    high_prices: np.ndarray, 
    low_prices: np.ndarray, 
    deviation: float = 5.0
) -> np.ndarray:
    """
    Calculates and returns a structured array of swing points.

    Args:
        high_prices (np.ndarray): Numpy array of high prices.
        low_prices (np.ndarray): Numpy array of low prices.
        deviation (float): The percentage deviation for swing detection.

    Returns:
        np.ndarray: A structured numpy array with fields: 'index', 'price', 'type'.
                    Returns an empty array if calculation fails.
    """
    if len(high_prices) != len(low_prices) or len(high_prices) == 0:
        return np.array([])
        
    indices, prices, types, _ = _fast_zigzag(high_prices, low_prices, deviation)
    
    # Remove NaN values that may result from the calculation
    valid_mask = ~np.isnan(indices)
    indices = indices[valid_mask].astype(int)
    prices = prices[valid_mask]
    types = types[valid_mask].astype(int)
    
    # Create a structured array for easier use
    swing_points = np.zeros(
        len(indices), 
        dtype=[('index', 'i4'), ('price', 'f8'), ('type', 'i4')]
    )
    swing_points['index'] = indices
    swing_points['price'] = prices
    swing_points['type'] = types
    
    return swing_points