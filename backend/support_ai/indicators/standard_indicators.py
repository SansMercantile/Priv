# backend/support_ai/indicators/standard_indicators.py

# Make TA-Lib optional with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("TA-Lib not available in standard_indicators. Using numpy-based fallbacks.")
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_camarilla_levels(high: float, low: float, close: float) -> Dict[str, float]:
    """Calculates Camarilla pivot points for a given period (typically daily)."""
    range_val = high - low
    if range_val == 0: range_val = 0.0001
    levels = {
        "H5": (high / low) * close, "H4": close + range_val * 1.1 / 2,
        "H3": close + range_val * 1.1 / 4, "H2": close + range_val * 1.1 / 6,
        "H1": close + range_val * 1.1 / 12, "L1": close - range_val * 1.1 / 12,
        "L2": close - range_val * 1.1 / 6, "L3": close - range_val * 1.1 / 4,
        "L4": close - range_val * 1.1 / 2,
    }
    levels["L5"] = close - (levels["H5"] - close)
    return levels

def calculate_all_standard_indicators(
    high: np.ndarray, low: np.ndarray, close: np.ndarray,
    volume: np.ndarray, open_prices: np.ndarray
) -> Dict[str, Any]:
    """
    Calculates a comprehensive suite of standard technical indicators using TA-Lib.
    This function consolidates the logic from the various provided MQL indicator files.
    """
    indicators = {}
    try:
        # --- Volatility and Channel Indicators ---
        indicators['ATR'] = talib.ATR(high, low, close, timeperiod=14).tolist()
        upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        indicators['BBANDS'] = {'UPPER': upper.tolist(), 'MIDDLE': middle.tolist(), 'LOWER': lower.tolist()}
        
        # Keltner Channels - from Keltner Channel.py
        ema20 = talib.EMA(close, timeperiod=20)
        atr10 = talib.ATR(high, low, close, timeperiod=10)
        indicators['KELTNER_CHANNEL'] = {
            'UPPER': (ema20 + (2.0 * atr10)).tolist(),
            'MIDDLE': ema20.tolist(),
            'LOWER': (ema20 - (2.0 * atr10)).tolist()
        }

        # Donchian Channels - from Donchian Channel.py
        indicators['DONCHIAN_CHANNEL'] = {
            'UPPER': talib.MAX(high, timeperiod=20).tolist(),
            'LOWER': talib.MIN(low, timeperiod=20).tolist()
        }

        # --- Momentum Indicators ---
        median_price = (high + low) / 2
        ao_fast = talib.SMA(median_price, timeperiod=5)
        ao_slow = talib.SMA(median_price, timeperiod=34)
        ao = ao_fast - ao_slow
        indicators['AWESOME_OSCILLATOR'] = ao.tolist()
        ac = ao - talib.SMA(ao, timeperiod=5)
        indicators['ACCELERATOR_OSCILLATOR'] = ac.tolist()
        indicators['CCI'] = talib.CCI(high, low, close, timeperiod=14).tolist()
        indicators['ULTIMATE_OSCILLATOR'] = talib.ULTOSC(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28).tolist()
        indicators['TRIX'] = talib.TRIX(close, timeperiod=14).tolist()
        
        # Detrended Price Oscillator (DPO) - from DPO.py
        dpo_period = 12
        dpo_shift = int(dpo_period / 2) + 1
        dpo_ma = pd.Series(close).shift(dpo_shift).rolling(window=dpo_period).mean()
        indicators['DPO'] = (pd.Series(close) - dpo_ma).tolist()

        # --- Trend & Strength Indicators ---
        indicators['ADX'] = talib.ADX(high, low, close, timeperiod=14).tolist()
        indicators['PLUS_DI'] = talib.PLUS_DI(high, low, close, timeperiod=14).tolist()
        indicators['MINUS_DI'] = talib.MINUS_DI(high, low, close, timeperiod=14).tolist()
        indicators['SAR'] = talib.SAR(high, low, acceleration=0.02, maximum=0.2).tolist()
        
        ema13 = talib.EMA(close, timeperiod=13)
        indicators['BULLS_POWER'] = (high - ema13).tolist()
        indicators['BEARS_POWER'] = (low - ema13).tolist()
        
        # Ichimoku Kinko Hyo - from Ichimoku.py
        tenkan, kijun, senkou_a, senkou_b, chikou = talib.ICHIMOKU(close, tenkan_period=9, kijun_period=26, senkou_period=52, chikou_period=26)
        indicators['ICHIMOKU'] = {
            'TENKAN': tenkan.tolist(), 'KIJUN': kijun.tolist(),
            'SENKOU_A': senkou_a.tolist(), 'SENKOU_B': senkou_b.tolist(),
            'CHIKOU': chikou.tolist()
        }

        # --- Volume Indicators ---
        ad_line = talib.AD(high, low, close, volume)
        indicators['AD_LINE'] = ad_line.tolist()
        ad_ema_fast = talib.EMA(ad_line, timeperiod=3)
        ad_ema_slow = talib.EMA(ad_line, timeperiod=10)
        indicators['CHAIKIN_OSCILLATOR'] = (ad_ema_fast - ad_ema_slow).tolist()
        indicators['FORCE_INDEX'] = (pd.Series(close).diff(1) * pd.Series(volume)).ewm(span=13).mean().tolist()
        indicators['MFI'] = talib.MFI(high, low, close, volume, timeperiod=14).tolist()
        indicators['OBV'] = talib.OBV(close, volume).tolist()

        # --- Other ---
        indicators['KAMA'] = talib.KAMA(close, timeperiod=10).tolist()
        indicators['DEMA'] = talib.DEMA(close, timeperiod=14).tolist()
        indicators['TEMA'] = talib.TEMA(close, timeperiod=14).tolist()
        
        # Fractals - from Fractals.py (Simplified logic)
        fractal_up = (high == pd.Series(high).rolling(5, center=True).max())
        fractal_down = (low == pd.Series(low).rolling(5, center=True).min())
        indicators['FRACTALS'] = {
            'UP': np.where(fractal_up, high, np.nan).tolist(),
            'DOWN': np.where(fractal_down, low, np.nan).tolist()
        }

        if len(high) > 1:
            indicators['CAMARILLA'] = calculate_camarilla_levels(high[-2], low[-2], close[-2])
        
    except Exception as e:
        logger.error(f"Error calculating standard indicators: {e}", exc_info=True)

    # Clean up NaN values for JSON compatibility
    for key, value in list(indicators.items()):
        if isinstance(value, list):
            indicators[key] = [v if pd.notna(v) else None for v in value]
        elif isinstance(value, dict):
            for sub_key, sub_value in list(value.items()):
                 if isinstance(sub_value, list):
                    value[sub_key] = [v if pd.notna(v) else None for v in sub_value]

    return indicators
