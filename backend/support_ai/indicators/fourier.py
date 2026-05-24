# backend/support_ai/indicators/fourier.py

import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def fourier_extrapolation(
    price_series: np.ndarray, 
    n_predict: int = 10, 
    n_harmonics: int = 10
) -> Optional[np.ndarray]:
    """
    Extrapolates a price series using Fourier transformation.

    This method decomposes the price series into a sum of sine and cosine waves,
    filters out high-frequency noise by keeping only the most significant
    harmonics, and then projects the resulting smooth curve into the future.

    Args:
        price_series (np.ndarray): The input array of prices (e.g., close prices).
        n_predict (int): The number of future periods to extrapolate.
        n_harmonics (int): The number of harmonics to use for filtering. A lower
                           number results in a smoother, more generalized curve.

    Returns:
        Optional[np.ndarray]: An array containing the extrapolated price points,
                              or None if an error occurs.
    """
    if price_series.size < n_harmonics * 2:
        logger.warning("Not enough data for Fourier extrapolation. Need at least 2x the number of harmonics.")
        return None
        
    n = price_series.size
    t = np.arange(0, n)
    
    try:
        # Detrend the price series
        p = np.polyfit(t, price_series, 1)
        price_series_no_trend = price_series - p[0] * t
        
        # Perform Fast Fourier Transform
        freqs = np.fft.fftfreq(n)
        fft_result = np.fft.fft(price_series_no_trend)
        
        # Filter out noise by keeping only the most significant harmonics
        indices = list(range(n))
        # Sort by amplitude, but ignore the zero-frequency component (DC offset)
        indices.sort(key=lambda i: np.absolute(fft_result[i]), reverse=True)
        
        fft_filtered = np.zeros(n, dtype=complex)
        for i in indices[:1 + n_harmonics * 2]:
            fft_filtered[i] = fft_result[i]
            
        # Perform Inverse Fourier Transform to get the smoothed signal
        restored_signal = np.fft.ifft(fft_filtered)
        
        # Extrapolate the future points by extending the restored signal
        t_future = np.arange(n, n + n_predict)
        
        # The extrapolation is the trend line plus the restored periodic component
        extrapolated = np.polyval(p, t_future)
        
        # To continue the periodic component, we can use the last part of the restored signal
        # This is a simplification; more advanced methods could be used.
        # Here, we'll simply repeat the last `n_predict` points of the cycle.
        extrapolated += restored_signal[-n_predict:].real
        
        return extrapolated

    except Exception as e:
        logger.error(f"Error during Fourier extrapolation: {e}", exc_info=True)
        return None
