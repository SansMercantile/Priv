# priv/backend/utils/matlab_engine_wrapper.py

import logging
from typing import Optional, Any, Dict, List
import numpy as np
import matlab.engine as matlab

logger = logging.getLogger(__name__)

class MATLABEngineWrapper:
    """
    Wrapper for MATLAB Engine to perform advanced quantitative analysis.
    Provides signal processing, statistical analysis, and technical indicators.
    """
    
    def __init__(self):
        self.engine: Optional[Any] = None
        self.matlab_available = False
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize MATLAB engine connection."""
        try:
            import matlab.engine
            logger.info("Starting MATLAB engine (this may take 10-30 seconds)...")
            self.engine = matlab.engine.start_matlab()
            self.matlab_available = True
            logger.info("✅ MATLAB engine started successfully!")
            
            # Test basic functionality
            result = self.engine.eval('1+1')
            logger.info(f"MATLAB engine test: 1+1 = {result}")
            
        except ImportError:
            logger.warning("matlabengine package not installed. Install with: pip install matlabengine")
            self.matlab_available = False
        except Exception as e:
            logger.error(f"Failed to start MATLAB engine: {e}")
            logger.warning("MATLAB integration will not be available")
            self.matlab_available = False
    
    def is_available(self) -> bool:
        """Check if MATLAB engine is available."""
        return self.matlab_available
    
    def calculate_technical_indicators(
        self, 
        prices: List[float], 
        volumes: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators using MATLAB's Financial Toolbox.
        
        Args:
            prices: List of price data
            volumes: Optional list of volume data
            
        Returns:
            Dictionary containing technical indicators
        """
        if not self.matlab_available or not prices:
            return {"error": "MATLAB not available or no price data"}
        
        try:
            # Convert Python list to MATLAB array
            matlab_prices = matlab.double(prices)
            
            # Calculate Simple Moving Average (SMA)
            sma_20 = self.engine.movmean(matlab_prices, 20)
            sma_50 = self.engine.movmean(matlab_prices, 50)
            
            # Calculate Exponential Moving Average (EMA)
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)
            
            # Calculate RSI (Relative Strength Index)
            rsi = self._calculate_rsi(prices, 14)
            
            # Calculate MACD
            macd = np.array(ema_12) - np.array(ema_26)
            signal_line = self._calculate_ema(macd.tolist(), 9)
            
            # Calculate Bollinger Bands
            bb_middle = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
            bb_std = np.std(prices[-20:]) if len(prices) >= 20 else np.std(prices)
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            
            return {
                "sma_20": list(sma_20)[-1] if sma_20 else None,
                "sma_50": list(sma_50)[-1] if sma_50 else None,
                "ema_12": ema_12[-1] if ema_12 else None,
                "ema_26": ema_26[-1] if ema_26 else None,
                "rsi": rsi[-1] if rsi else None,
                "macd": macd[-1] if len(macd) > 0 else None,
                "macd_signal": signal_line[-1] if signal_line else None,
                "bollinger_upper": bb_upper,
                "bollinger_middle": bb_middle,
                "bollinger_lower": bb_lower,
                "current_price": prices[-1] if prices else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators with MATLAB: {e}")
            return {"error": str(e)}
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        if not data or period <= 0:
            return []
        
        ema = [sum(data[:period]) / period]  # Start with SMA
        multiplier = 2 / (period + 1)
        
        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return []
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi_values = []
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def perform_signal_processing(
        self, 
        time_series: List[float],
        filter_type: str = "lowpass",
        cutoff_frequency: float = 0.1
    ) -> Dict[str, Any]:
        """
        Perform signal processing on time series data using MATLAB.
        
        Args:
            time_series: Time series data to process
            filter_type: Type of filter ("lowpass", "highpass", "bandpass")
            cutoff_frequency: Normalized cutoff frequency (0 to 1)
            
        Returns:
            Filtered signal and analysis
        """
        if not self.matlab_available or not time_series:
            return {"error": "MATLAB not available or no data"}
        
        try:
            matlab_data = matlab.double(time_series)
            
            # Apply digital filter
            if filter_type == "lowpass":
                # Design a low-pass filter
                filtered = self.engine.lowpass(matlab_data, cutoff_frequency)
            else:
                # For other filter types, use basic smoothing
                window_size = max(3, int(1 / cutoff_frequency))
                filtered = self.engine.movmean(matlab_data, window_size)
            
            # Calculate frequency spectrum
            fft_result = self.engine.fft(matlab_data)
            
            return {
                "filtered_signal": list(filtered),
                "original_signal": time_series,
                "noise_reduction": float(np.std(time_series) - np.std(list(filtered))),
                "fft_available": True
            }
            
        except Exception as e:
            logger.error(f"Error in signal processing with MATLAB: {e}")
            return {"error": str(e)}
    
    def statistical_analysis(self, data: List[float]) -> Dict[str, Any]:
        """
        Perform statistical analysis using MATLAB's Statistics Toolbox.
        
        Args:
            data: Numerical data for analysis
            
        Returns:
            Statistical metrics
        """
        if not self.matlab_available or not data:
            return {"error": "MATLAB not available or no data"}
        
        try:
            matlab_data = matlab.double(data)
            
            mean_val = float(self.engine.mean(matlab_data))
            median_val = float(self.engine.median(matlab_data))
            std_val = float(self.engine.std(matlab_data))
            var_val = float(self.engine.var(matlab_data))
            
            # Calculate skewness and kurtosis
            skewness = float(self.engine.skewness(matlab_data))
            kurtosis = float(self.engine.kurtosis(matlab_data))
            
            return {
                "mean": mean_val,
                "median": median_val,
                "std": std_val,
                "variance": var_val,
                "skewness": skewness,
                "kurtosis": kurtosis,
                "min": min(data),
                "max": max(data),
                "range": max(data) - min(data)
            }
            
        except Exception as e:
            logger.error(f"Error in statistical analysis with MATLAB: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close MATLAB engine connection."""
        if self.engine and self.matlab_available:
            try:
                self.engine.quit()
                logger.info("MATLAB engine closed successfully")
            except Exception as e:
                logger.error(f"Error closing MATLAB engine: {e}")

# Global singleton instance
_matlab_wrapper: Optional[MATLABEngineWrapper] = None

def get_matlab_wrapper() -> MATLABEngineWrapper:
    """Get or create the global MATLAB wrapper instance."""
    global _matlab_wrapper
    if _matlab_wrapper is None:
        _matlab_wrapper = MATLABEngineWrapper()
    return _matlab_wrapper
