import numpy as np
import pandas as pd

# Make TA-Lib optional with fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("TA-Lib not available. Using fallback indicators. Install TA-Lib for full functionality.")
from typing import Dict, Any, List, Tuple
import logging

# Import all specific indicator and pattern detection modules
from backend.support_ai.indicators.standard_indicators import calculate_all_standard_indicators
from backend.support_ai.indicators.harmonics import find_harmonic_patterns
from backend.support_ai.indicators.candlesticks import find_all_candlestick_patterns
from backend.support_ai.indicators.outsidebar import find_outside_bars
from backend.support_ai.indicators.zigzag import get_swing_points 
from backend.support_ai.indicators.fourier import fourier_extrapolation
from backend.support_ai.indicators.wso_wro_trend_lines import detect_wso_wro_trend_lines 
from backend.support_ai.indicators.atr_3lwma_indicator import calculate_atr_3lwma 
from backend.support_ai.indicators.pattern_recognition import detect_flag_and_pennant 
from backend.support_ai.indicators.cup_scan import detect_cup_and_handle
from backend.support_ai.indicators.tradingview_analyzer import TradingViewAnalyzer
from backend.strategy_engine.stochastic_wpr_strategy import generate_stochastic_wpr_signals # NEW: TheMasterMind strategy signals


logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self):
        logger.info("AnalyticsEngine initialized.")

    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Performs a comprehensive technical analysis on the provided OHLCV data.
        This includes standard indicators, various chart patterns, and Fourier extrapolation.

        Args:
            df (pd.DataFrame): A pandas DataFrame containing OHLCV data.
                               Expected columns: 'open', 'high', 'low', 'close', 'volume'.
                               Index should preferably be datetime.

        Returns:
            Dict[str, Any]: A dictionary containing various analysis results.
                            Keys include 'standard_indicators', 'candlestick_patterns',
                            'harmonic_patterns', 'outside_bars', 'fourier_forecast',
                            'wso_wro_levels', 'atr_3lwma', 'flag_pennant_patterns',
                            'stoch_wpr_signal'.
        """
        analysis_results = {}

        if df.empty:
            logger.warning("Input DataFrame is empty for analytics engine.")
            return analysis_results

        # Ensure necessary columns are present
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns in DataFrame: {', '.join(set(required_columns) - set(df.columns))}")
            return analysis_results

        high_np = df['high'].to_numpy()
        low_np = df['low'].to_numpy()
        close_np = df['close'].to_numpy()
        open_np = df['open'].to_numpy()
        volume_np = df['volume'].to_numpy()
        times_np = df.index.to_numpy() # Use index for times

        # --- 1. Standard Indicators (from standard_indicators.py) ---
        try:
            standard_indicators = calculate_all_standard_indicators(df)
            analysis_results['standard_indicators'] = standard_indicators
        except Exception as e:
            logger.error(f"Error calculating standard indicators: {e}")
            analysis_results['standard_indicators'] = {}

        # --- 2. Pattern Recognition ---
        
        # 2.1 Candlestick Patterns (from candlesticks.py)
        try:
            candlestick_patterns = find_all_candlestick_patterns(open_np, high_np, low_np, close_np)
            analysis_results['candlestick_patterns'] = candlestick_patterns
        except Exception as e:
            logger.error(f"Error detecting candlestick patterns: {e}")
            analysis_results['candlestick_patterns'] = []

        # 2.2 Outside Bar Patterns (from outsidebar.py)
        try:
            outside_bars = find_outside_bars(open_np, high_np, low_np, close_np)
            analysis_results['outside_bars'] = outside_bars
        except Exception as e:
            logger.error(f"Error detecting outside bars: {e}")
            analysis_results['outside_bars'] = []

        # 2.3 ZigZag Swing Points (dependency for Harmonic Patterns)
        # Assuming a default deviation that makes sense for the timeframe
        zigzag_deviation = 0.01 # Example deviation for zigzag, might need to be dynamic
        try:
            # get_swing_points expects high, low, close as separate numpy arrays
            zigzag_raw_points = get_swing_points(high_np, low_np, close_np, deviation=zigzag_deviation)
            # Convert to list of tuples (index, price, type) for find_harmonic_patterns
            # Ensure indices are integers and prices are floats
            zigzag_swing_points = [(int(p[0]), float(p[1]), p[2]) for p in zigzag_raw_points] if zigzag_raw_points else []
            analysis_results['zigzag_swing_points'] = zigzag_swing_points
        except Exception as e:
            logger.error(f"Error calculating zigzag swing points: {e}")
            analysis_results['zigzag_swing_points'] = []
            zigzag_swing_points = [] # Ensure it's empty if calculation fails

        # 2.4 Harmonic Patterns (from harmonics.py)
        try:
            # find_harmonic_patterns needs close prices array and structured swing points
            harmonic_patterns = find_harmonic_patterns(close_np, zigzag_swing_points)
            analysis_results['harmonic_patterns'] = harmonic_patterns
        except Exception as e:
            logger.error(f"Error detecting harmonic patterns: {e}")
            analysis_results['harmonic_patterns'] = []

        # 2.5 Flag and Pennant Patterns (from pattern_recognition.py) - NEW
        try:
            # Pass point_size from symbol_info if available, using a default for now
            # This would ideally be passed from data_loader or a global symbol_info mapping
            point_size_for_patterns = 0.0001 # Placeholder, e.g. for 5-digit forex pairs
            if 'point' in standard_indicators and standard_indicators['point'] is not None:
                 point_size_for_patterns = standard_indicators['point'][-1]
            
            flag_pennant_patterns = detect_flag_and_pennant(
                high_np, low_np, close_np, times_np, point_size=point_size_for_patterns
            )
            analysis_results['flag_pennant_patterns'] = flag_pennant_patterns
        except Exception as e:
            logger.error(f"Error detecting Flag and Pennant patterns: {e}")
            analysis_results['flag_pennant_patterns'] = []

        # 2.6 WSO/WRO Trend Lines (from wso_wro_trend_lines.py) - NEW
        try:
            wso_wro_levels = detect_wso_wro_trend_lines(high_np, low_np, close_np, times_np)
            analysis_results['wso_wro_levels'] = wso_wro_levels
        except Exception as e:
            logger.error(f"Error detecting WSO/WRO trend lines: {e}")
            analysis_results['wso_wro_levels'] = {}
            
        # --- 3. Predictive Analysis ---
        
        # 3.1 Fourier Extrapolation (from fourier.py)
        try:
            fourier_forecast = fourier_extrapolation(close_np)
            analysis_results['fourier_forecast'] = fourier_forecast
        except Exception as e:
            logger.error(f"Error performing Fourier extrapolation: {e}")
            analysis_results['fourier_forecast'] = np.array([]) # Ensure it's an array

        # --- 4. Advanced Indicators ---

        # 4.1 ATR 3LWMA (from atr_3lwma_indicator.py) - NEW
        try:
            atr_3lwma_results = calculate_atr_3lwma(high_np, low_np, close_np)
            analysis_results['atr_3lwma'] = atr_3lwma_results
        except Exception as e:
            logger.error(f"Error calculating ATR 3LWMA: {e}")
            analysis_results['atr_3lwma'] = {}

        # --- 5. Strategy-Specific Signals ---
        # 5.1 Stochastic/Williams %R Signal (from stochastic_wpr_strategy.py) - NEW
        # Ensure stoch_d and williams_r are available from standard_indicators
        stoch_d_series = standard_indicators.get('stoch_d')
        williams_r_series = standard_indicators.get('williams_r')
        
        if stoch_d_series is not None and williams_r_series is not None:
            try:
                stoch_wpr_signal = generate_stochastic_wpr_signals(stoch_d_series, williams_r_series)
                analysis_results['stoch_wpr_signal'] = stoch_wpr_signal
            except Exception as e:
                logger.error(f"Error generating Stochastic/WPR signals: {e}")
                analysis_results['stoch_wpr_signal'] = {"signal": "NONE", "confidence": 0.0, "reason": "Error during calculation."}
        else:
            analysis_results['stoch_wpr_signal'] = {"signal": "NONE", "confidence": 0.0, "reason": "Missing Stochastic or WPR data from standard indicators."}

        logger.info(f"Comprehensive analysis completed for {df.index.name or 'symbol'}.")
        return analysis_results
                
# Example Usage (for testing the AnalyticsEngine in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Create mock OHLCV data for demonstration
    data_length = 200 # Need enough data for various indicators
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    
    # Simulate a trending market with some swings
    mock_closes = np.sin(np.linspace(0, 30, data_length)) * 20 + 100 # Sine wave for swings
    mock_opens = mock_closes + np.random.uniform(-1, 1, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 2, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 2, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)

    # Ensure valid OHLC structure
    mock_highs = np.maximum(mock_highs, mock_lows)
    mock_highs = np.maximum(mock_highs, np.maximum(mock_opens, mock_closes))
    mock_lows = np.minimum(mock_lows, mock_highs)
    mock_lows = np.minimum(mock_lows, np.minimum(mock_opens, mock_closes))


    mock_df = pd.DataFrame({
        'open': mock_opens,
        'high': mock_highs,
        'low': mock_lows,
        'close': mock_closes,
        'volume': mock_volumes
    }, index=dates)
    mock_df.index.name = 'timestamp' # Name the index for clarity

    engine = AnalyticsEngine()
    print("\n--- Running comprehensive analysis ---")
    results = engine.calculate_indicators(mock_df)

    # Print some key results to verify
    print("\n--- Summary of Analysis Results ---")
    
    # Standard Indicators
    if 'standard_indicators' in results:
        print(f"Standard Indicators (last RSI): {results['standard_indicators'].get('rsi', np.array([np.nan]))[-1]:.2f}")
        print(f"Standard Indicators (last MACD): {results['standard_indicators'].get('macd', np.array([np.nan]))[-1]:.2f}")
    else:
        print("Standard indicators not found in results.")

    # Candlestick Patterns
    print(f"Candlestick Patterns Detected: {len(results.get('candlestick_patterns', []))}")
    if results.get('candlestick_patterns'):
        print(f"  Last Candlestick: {results['candlestick_patterns'][-1].get('name')}")

    # Harmonic Patterns
    print(f"Harmonic Patterns Detected: {len(results.get('harmonic_patterns', []))}")
    if results.get('harmonic_patterns'):
        print(f"  Last Harmonic: {results['harmonic_patterns'][-1].get('name')}")
    
    # Flag and Pennant Patterns
    print(f"Flag & Pennant Patterns Detected: {len(results.get('flag_pennant_patterns', []))}")
    if results.get('flag_pennant_patterns'):
        print(f"  Last Flag/Pennant: {results['flag_pennant_patterns'][-1].get('name')}")

    # WSO/WRO Levels
    print(f"WSO Support Levels Detected: {len(results.get('wso_wro_levels', {}).get('wso_support_levels', []))}")
    print(f"WRO Resistance Levels Detected: {len(results.get('wso_wro_levels', {}).get('wro_resistance_levels', []))}")

    # Stochastic/WPR Signal
    print(f"Stochastic/WPR Signal: {results.get('stoch_wpr_signal', {}).get('signal')}")

    # ATR 3LWMA
    if 'atr_3lwma' in results and results['atr_3lwma']:
        print(f"ATR 3LWMA (last Slow): {results['atr_3lwma'].get('slow_atr_lwma', np.array([np.nan]))[-1]:.5f}")

    # Fourier Forecast
    if 'fourier_forecast' in results and len(results['fourier_forecast']) > 0:
        print(f"Fourier Forecast (last point): {results['fourier_forecast'][-1]:.2f}")
    else:
        print("Fourier forecast not found or empty.")

    print("\nFull analysis results structure:")
    # You might want to pretty-print the structure or check specific keys
    # for key, value in results.items():
    #     if isinstance(value, np.ndarray):
    #         print(f"{key}: np.ndarray (shape: {value.shape})")
    #     elif isinstance(value, list):
    #         print(f"{key}: list (len: {len(value)})")
    #     elif isinstance(value, dict):
    #         print(f"{key}: dict (keys: {list(value.keys())})")
    #     else:
    #         print(f"{key}: {type(value)}")

            # Consolidate all results into a single dictionary
            # (Removed incomplete all_results dictionary assignment)
