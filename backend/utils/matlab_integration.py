"""
MATLAB Engine Integration for PRIV Trading System.

Provides advanced quantitative analysis using MATLAB's computational capabilities.
"""

import logging
import numpy as np
import os
from typing import Optional, Dict, Any, List
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class MATLABEngine:
    """Wrapper for MATLAB Engine integration with graceful fallback."""
    
    def __init__(self):
        self.engine: Optional[Any] = None
        self.available = False
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize MATLAB engine with error handling."""
        # Check if MATLAB is explicitly disabled
        if os.getenv("DISABLE_MATLAB", "false").lower() == "true":
            logger.info("💤 MATLAB disabled via DISABLE_MATLAB=true (using NumPy/SciPy fallback)")
            return
            
        try:
            import matlab.engine
            logger.info("Starting MATLAB engine (this may take 10-30 seconds)...")
            self.engine = matlab.engine.start_matlab()
            self.available = True
            logger.info("✅ MATLAB Engine successfully initialized and ready")
        except ImportError:
            logger.warning("⚠️ MATLAB Engine not available: matlabengine package not installed (using NumPy/SciPy fallback)")
        except Exception as e:
            logger.warning(f"⚠️ MATLAB Engine initialization failed: {e} (using NumPy/SciPy fallback)")
    
    def is_available(self) -> bool:
        """Check if MATLAB engine is available."""
        return self.available
    
    async def compute_advanced_statistics(self, prices: np.ndarray) -> Dict[str, float]:
        """
        Compute advanced statistical measures using MATLAB.
        
        Args:
            prices: Array of historical prices
            
        Returns:
            Dictionary with statistical measures
        """
        if not self.available or self.engine is None:
            logger.debug("MATLAB not available, using NumPy fallback")
            return self._numpy_fallback_stats(prices)
        
        try:
            # Convert to MATLAB array
            prices_matlab = self.engine.double(prices.tolist())
            
            # Run MATLAB computations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._matlab_statistics, 
                prices_matlab
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"MATLAB computation failed: {e}, using NumPy fallback")
            return self._numpy_fallback_stats(prices)
    
    def _matlab_statistics(self, prices_matlab) -> Dict[str, float]:
        """Execute MATLAB statistical computations."""
        # MATLAB provides more accurate statistical functions
        mean_val = float(self.engine.mean(prices_matlab))
        std_val = float(self.engine.std(prices_matlab))
        skewness = float(self.engine.skewness(prices_matlab))
        kurtosis = float(self.engine.kurtosis(prices_matlab))
        
        # Compute returns
        returns = self.engine.diff(prices_matlab)
        volatility = float(self.engine.std(returns)) * np.sqrt(252)  # Annualized
        
        return {
            'mean': mean_val,
            'std': std_val,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'annualized_volatility': volatility
        }
    
    def _numpy_fallback_stats(self, prices: np.ndarray) -> Dict[str, float]:
        """Fallback statistical computations using NumPy."""
        from scipy import stats
        
        returns = np.diff(prices) / prices[:-1]
        
        return {
            'mean': float(np.mean(prices)),
            'std': float(np.std(prices)),
            'skewness': float(stats.skew(prices)),
            'kurtosis': float(stats.kurtosis(prices)),
            'annualized_volatility': float(np.std(returns) * np.sqrt(252))
        }
    
    async def perform_signal_processing(
        self, 
        signal: np.ndarray, 
        filter_type: str = 'moving_average',
        window: int = 20
    ) -> np.ndarray:
        """
        Perform signal processing on time series data.
        
        Args:
            signal: Input signal (price series)
            filter_type: Type of filter ('moving_average', 'exponential', 'savitzky_golay')
            window: Window size for filtering
            
        Returns:
            Filtered signal
        """
        if not self.available or self.engine is None:
            logger.debug("MATLAB not available, using SciPy fallback")
            return self._scipy_signal_processing(signal, filter_type, window)
        
        try:
            signal_matlab = self.engine.double(signal.tolist())
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._matlab_filter,
                signal_matlab,
                filter_type,
                window
            )
            
            return np.array(result).flatten()
            
        except Exception as e:
            logger.warning(f"MATLAB signal processing failed: {e}, using SciPy fallback")
            return self._scipy_signal_processing(signal, filter_type, window)
    
    def _matlab_filter(self, signal_matlab, filter_type: str, window: int):
        """Execute MATLAB filtering operations."""
        if filter_type == 'moving_average':
            # Use MATLAB's movmean for better performance
            filtered = self.engine.movmean(signal_matlab, float(window))
        elif filter_type == 'exponential':
            # Exponential smoothing
            alpha = 2.0 / (window + 1)
            filtered = self.engine.filter(
                [alpha], 
                [1, -(1-alpha)], 
                signal_matlab
            )
        else:  # savitzky_golay
            # Use MATLAB's sgolayfilt
            filtered = self.engine.sgolayfilt(signal_matlab, 3, window)
        
        return filtered
    
    def _scipy_signal_processing(
        self, 
        signal: np.ndarray, 
        filter_type: str, 
        window: int
    ) -> np.ndarray:
        """Fallback signal processing using SciPy."""
        from scipy.signal import savgol_filter
        from pandas import Series
        
        if filter_type == 'moving_average':
            return Series(signal).rolling(window=window, center=True).mean().fillna(signal).values
        elif filter_type == 'exponential':
            return Series(signal).ewm(span=window, adjust=False).mean().values
        else:  # savitzky_golay
            return savgol_filter(signal, window if window % 2 == 1 else window + 1, 3)
    
    async def compute_correlation_matrix(
        self, 
        price_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Compute correlation matrix for multiple assets.
        
        Args:
            price_matrix: Matrix where each column is a price series
            
        Returns:
            Correlation matrix
        """
        if not self.available or self.engine is None:
            return np.corrcoef(price_matrix.T)
        
        try:
            # Convert to MATLAB format
            matrix_matlab = self.engine.double(price_matrix.tolist())
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.engine.corrcoef,
                matrix_matlab
            )
            
            return np.array(result)
            
        except Exception as e:
            logger.warning(f"MATLAB correlation failed: {e}, using NumPy fallback")
            return np.corrcoef(price_matrix.T)
    
    async def optimize_portfolio(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Any]:
        """
        Perform portfolio optimization using MATLAB's optimization toolbox.
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of returns
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            
        Returns:
            Optimal weights and portfolio metrics
        """
        if not self.available or self.engine is None:
            logger.debug("MATLAB not available, using scipy.optimize fallback")
            return self._scipy_portfolio_optimization(
                expected_returns, 
                covariance_matrix, 
                risk_free_rate
            )
        
        try:
            # This would use MATLAB's optimization toolbox
            # For now, fall back to scipy
            return self._scipy_portfolio_optimization(
                expected_returns,
                covariance_matrix,
                risk_free_rate
            )
            
        except Exception as e:
            logger.warning(f"MATLAB portfolio optimization failed: {e}")
            return self._scipy_portfolio_optimization(
                expected_returns,
                covariance_matrix,
                risk_free_rate
            )
    
    def _scipy_portfolio_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_free_rate: float
    ) -> Dict[str, Any]:
        """Fallback portfolio optimization using scipy."""
        from scipy.optimize import minimize
        
        n_assets = len(expected_returns)
        
        def sharpe_ratio(weights):
            portfolio_return = np.sum(expected_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            return -(portfolio_return - risk_free_rate) / portfolio_volatility
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_guess = np.array([1.0 / n_assets] * n_assets)
        
        result = minimize(
            sharpe_ratio,
            initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        portfolio_return = np.sum(expected_returns * optimal_weights)
        portfolio_volatility = np.sqrt(
            np.dot(optimal_weights.T, np.dot(covariance_matrix, optimal_weights))
        )
        
        return {
            'weights': optimal_weights.tolist(),
            'expected_return': float(portfolio_return),
            'volatility': float(portfolio_volatility),
            'sharpe_ratio': float((portfolio_return - risk_free_rate) / portfolio_volatility)
        }
    
    def shutdown(self):
        """Gracefully shutdown MATLAB engine."""
        if self.available and self.engine is not None:
            try:
                self.engine.quit()
                logger.info("MATLAB Engine shut down successfully")
            except Exception as e:
                logger.warning(f"Error shutting down MATLAB Engine: {e}")


# Singleton instance
_matlab_engine_instance: Optional[MATLABEngine] = None


@lru_cache(maxsize=1)
def get_matlab_engine() -> MATLABEngine:
    """Get or create singleton MATLAB engine instance."""
    global _matlab_engine_instance
    if _matlab_engine_instance is None:
        _matlab_engine_instance = MATLABEngine()
    return _matlab_engine_instance
