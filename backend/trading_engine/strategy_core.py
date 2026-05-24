import talib
import numpy as np
import pandas as pd
from typing import List, Dict, Union, Any, Optional

# --- Configuration Constants for Indicator Parameters ---
RSI_PERIOD: int = 14
MACD_FAST_PERIOD: int = 12
MACD_SLOW_PERIOD: int = 26
MACD_SIGNAL_PERIOD: int = 9
SMA_SHORT_PERIOD: int = 50
SMA_LONG_PERIOD: int = 200

# --- Configuration Constants for Signal Thresholds ---
RSI_OVERBOUGHT_THRESHOLD: float = 70.0
RSI_OVERSOLD_THRESHOLD: float = 30.0 # Added for completeness if needed later


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates various technical indicators and adds them as new columns to the DataFrame.

    Args:
        df (pd.DataFrame): A pandas DataFrame containing at least a 'close' price column.
                          Expected columns: 'open', 'high', 'low', 'close', 'volume' (optional).

    Returns:
        pd.DataFrame: The DataFrame with new indicator columns ('rsi', 'macd', 'macd_signal',
                      'sma_50', 'sma_200'). Returns original DataFrame if input is invalid.
    Raises:
        ValueError: If the input DataFrame is empty or missing the 'close' column.
        KeyError: If a required column is not found (handled by accessing df["close"]).
    """
    if df.empty:
        raise ValueError("Input DataFrame for indicator calculation is empty.")
    if "close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'close' column for indicator calculation.")

    # Calculate Relative Strength Index (RSI)
    df["rsi"] = talib.RSI(df["close"], timeperiod=RSI_PERIOD)

    # Calculate Moving Average Convergence Divergence (MACD)
    # The third return value (macd_hist) is typically discarded if not needed directly.
    df["macd"], df["macd_signal"], _ = talib.MACD(
        df["close"],
        fastperiod=MACD_FAST_PERIOD,
        slowperiod=MACD_SLOW_PERIOD,
        signalperiod=MACD_SIGNAL_PERIOD
    )

    # Calculate Simple Moving Averages (SMA)
    df["sma_50"] = talib.SMA(df["close"], timeperiod=SMA_SHORT_PERIOD)
    df["sma_200"] = talib.SMA(df["close"], timeperiod=SMA_LONG_PERIOD)

    return df


def detect_signals(df: pd.DataFrame) -> List[str]:
    """
    Detects various trading signals based on the latest calculated indicators in the DataFrame.

    Args:
        df (pd.DataFrame): A pandas DataFrame with calculated indicator columns.

    Returns:
        List[str]: A list of detected signal names (e.g., "bullish_macd", "overbought", "golden_cross").
    Raises:
        ValueError: If the input DataFrame is empty or does not have enough rows for latest indicators.
        KeyError: If a required indicator column is missing.
    """
    if df.empty:
        raise ValueError("Input DataFrame for signal detection is empty.")
    if len(df) < 1: # Ensure there's at least one row to get latest
        raise ValueError("DataFrame must contain at least one row for signal detection.")

    latest = df.iloc[-1]
    signals: List[str] = []

    # Check for required columns before accessing, to avoid KeyError
    required_cols = ["macd", "macd_signal", "rsi", "sma_50", "sma_200"]
    if not all(col in latest.index for col in required_cols):
        raise KeyError(f"Missing one or more required indicator columns for signal detection. Required: {required_cols}")

    # MACD Bullish Crossover
    if latest["macd"] > latest["macd_signal"]:
        signals.append("bullish_macd_crossover") # Renamed for clarity

    # RSI Overbought
    if latest["rsi"] > RSI_OVERBOUGHT_THRESHOLD:
        signals.append("overbought_rsi") # Renamed for clarity

    # Golden Cross (SMA 50 crossing above SMA 200)
    # For a cross, usually you check current SMA_SHORT > SMA_LONG AND previous SMA_SHORT <= SMA_LONG
    # For simplicity, if just the current relationship indicates a cross
    if latest["sma_short"] is not np.nan and latest["sma_long"] is not np.nan: # Ensure SMAs are calculated
        if latest["sma_50"] > latest["sma_200"]:
            signals.append("golden_cross")

    return signals