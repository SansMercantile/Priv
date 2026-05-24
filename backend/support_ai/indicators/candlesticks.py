# backend/support_ai/indicators/candlesticks.py

# Make TA-Lib optional with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("TA-Lib not available in candlesticks. Pattern detection will use simplified logic.")
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# A mapping of TA-Lib function names to human-readable pattern names.
# This list is compiled from all the candlestick pattern files you provided.
TA_LIB_PATTERNS = {
    "CDL2CROWS": "Two Crows",
    "CDL3BLACKCROWS": "Three Black Crows",
    "CDL3INSIDE": "Three Inside Up/Down",
    "CDL3LINESTRIKE": "Three-Line Strike",
    "CDL3OUTSIDE": "Three Outside Up/Down",
    "CDL3STARSINSOUTH": "Three Stars In The South",
    "CDL3WHITESOLDIERS": "Three White Soldiers",
    "CDLABANDONEDBABY": "Abandoned Baby",
    "CDLADVANCEBLOCK": "Advance Block",
    "CDLBELTHOLD": "Belt-hold",
    "CDLCLOSINGMARUBOZU": "Closing Marubozu",
    "CDLDARKCLOUDCOVER": "Dark Cloud Cover",
    "CDLDOJI": "Doji",
    "CDLDOJISTAR": "Doji Star",
    "CDLDRAGONFLYDOJI": "Dragonfly Doji",
    "CDLENGULFING": "Engulfing Pattern",
    "CDLEVENINGDOJISTAR": "Evening Doji Star",
    "CDLEVENINGSTAR": "Evening Star",
    "CDLGRAVESTONEDOJI": "Gravestone Doji",
    "CDLHAMMER": "Hammer",
    "CDLHANGINGMAN": "Hanging Man",
    "CDLHARAMI": "Harami Pattern",
    "CDLHARAMICROSS": "Harami Cross Pattern",
    "CDLHIGHWAVE": "High-Wave Candle",
    "CDLINVERTEDHAMMER": "Inverted Hammer",
    "CDLMARUBOZU": "Marubozu",
    "CDLMATCHINGLOW": "Matching Low",
    "CDLMORNINGDOJISTAR": "Morning Doji Star",
    "CDLMORNINGSTAR": "Morning Star",
    "CDLPIERCING": "Piercing Pattern",
    "CDLSHOOTINGSTAR": "Shooting Star",
    "CDLSPINNINGTOP": "Spinning Top",
    "CDLSTALLEDPATTERN": "Stalled Pattern",
    "CDLTASUKIGAP": "Tasuki Gap",
    "CDLTHRUSTING": "Thrusting Pattern",
    "CDLTRISTAR": "Tristar Pattern",
    "CDLUNIQUE3RIVER": "Unique 3 River",
    "CDLXSIDEGAP3METHODS": "Upside/Downside Gap Three Methods"
}

def find_all_candlestick_patterns(
    open_prices: np.ndarray, 
    high_prices: np.ndarray, 
    low_prices: np.ndarray, 
    close_prices: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Scans the price data for all supported TA-Lib candlestick patterns and
    returns the most recent occurrences.

    Args:
        open_prices (np.ndarray): Array of opening prices.
        high_prices (np.ndarray): Array of high prices.
        low_prices (np.ndarray): Array of low prices.
        close_prices (np.ndarray): Array of closing prices.

    Returns:
        List[Dict[str, Any]]: A list of detected patterns on the last bar.
    """
    detected_patterns = []
    
    for func_name, pattern_name in TA_LIB_PATTERNS.items():
        try:
            # Get the corresponding TA-Lib function
            pattern_function = getattr(talib, func_name)
            
            # Run the pattern recognition function
            results = pattern_function(open_prices, high_prices, low_prices, close_prices)
            
            # Get the result for the last bar. TA-Lib returns 0 for no pattern,
            # 100 for bullish, and -100 for bearish.
            last_result = int(results[-1])
            
            if last_result != 0:
                direction = "Bullish" if last_result > 0 else "Bearish"
                detected_patterns.append({
                    "pattern_name": pattern_name,
                    "direction": direction,
                    "score": last_result
                })

        except AttributeError:
            logger.warning(f"TA-Lib function {func_name} not found. Skipping.")
        except Exception as e:
            logger.error(f"Error processing candlestick pattern {pattern_name}: {e}")

    return detected_patterns
