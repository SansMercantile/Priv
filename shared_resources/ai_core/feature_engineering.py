# backend/ai_core/feature_engineering.py

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# It's good practice to handle potential import errors for major libraries.
# If TA-Lib is not installed correctly, the application can still provide a warning.
try:
    import talib
except ImportError:
    talib = None
    logging.warning("TA-Lib library not found. Technical indicator features will be unavailable.")

# Same for scikit-learn, which is crucial for ML preprocessing.
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_regression
except ImportError:
    StandardScaler = None
    PCA = None
    SelectKBest = None
    f_regression = None
    logging.warning("scikit-learn library not found. Scaling, PCA, and feature selection will be unavailable.")

# Assuming this path is correct for your project structure.
# This service consumes the output of your existing AnalyticsEngine.
from backend.support_ai.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Takes raw market data, enriches it with a wide range of features,
    and prepares it for machine learning models. This class is designed
    to be robust and handle potential errors during feature calculation.
    """
    def __init__(self, analytics_engine: AnalyticsEngine, n_features_to_select: int = 50):
        """
        Initializes the feature engineer.

        Args:
            analytics_engine: An instance of your existing analytics engine.
            n_features_to_select (int): The number of top features to select.
        """
        self.analytics_engine = analytics_engine
        self.n_features_to_select = n_features_to_select
        
        # Halt initialization if critical dependencies are missing.
        if talib is None or StandardScaler is None:
            raise ImportError("Critical dependencies (TA-Lib or scikit-learn) are not installed.")
            
        # Initialize transformers for scaling and feature selection.
        self.scaler = StandardScaler()
        self.selector = SelectKBest(f_regression, k=self.n_features_to_select)
        
        logger.info("AdvancedFeatureEngineer initialized successfully.")

    def generate_features(self, ohlcv_df: pd.DataFrame, fit_transformers: bool = False) -> pd.DataFrame:
        """
        Main method to generate a full feature set from raw OHLCV data.

        Args:
            ohlcv_df (pd.DataFrame): DataFrame with columns ['open', 'high', 'low', 'close', 'volume'].
            fit_transformers (bool): If True, fits the scaler and selector. This should be True for training data
                                     and False for new/prediction data.

        Returns:
            pd.DataFrame: A DataFrame with engineered features, ready for an ML model.
        """
        if ohlcv_df.empty:
            logger.warning("Input ohlcv_df is empty. Returning an empty DataFrame.")
            return pd.DataFrame()

        # Step 1: Get base analysis from the analytics engine and flatten it.
        try:
            analysis_results = self.analytics_engine.calculate_indicators(ohlcv_df)
            feature_df = self._flatten_analysis_results(ohlcv_df, analysis_results)
        except Exception as e:
            logger.error(f"Error during initial analysis flattening: {e}. Starting with base OHLCV.")
            feature_df = ohlcv_df.copy()

        # Step 2: Add a comprehensive set of technical indicators.
        feature_df = self._add_technical_indicators(feature_df)

        # Step 3: Add time-based features from the index.
        feature_df = self._add_time_features(feature_df)
        
        # Step 4: Add interaction and lag features.
        feature_df = self._add_interaction_features(feature_df)

        # Step 6: Clean the data and prepare for ML transformations.
        # A temporary target variable is needed for feature selection.
        feature_df['temp_target'] = feature_df['close'].pct_change().shift(-1)
        
        feature_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        feature_df.dropna(inplace=True)

        if feature_df.empty:
            logger.warning("DataFrame became empty after cleaning NaNs. Cannot proceed.")
            return pd.DataFrame()

        y = feature_df['temp_target']
        X = feature_df.drop(columns=['temp_target'])
        
        numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
        non_numeric_cols = X.select_dtypes(exclude=np.number).columns.tolist()
        
        X_numeric = X[numeric_cols]

        # Step 6: Scale numeric features.
        if fit_transformers:
            X_scaled = self.scaler.fit_transform(X_numeric)
        else:
            X_scaled = self.scaler.transform(X_numeric)

        X_scaled_df = pd.DataFrame(X_scaled, index=X.index, columns=numeric_cols)
        
        # Re-combine non-numeric features if they exist.
        final_X = pd.concat([X_scaled_df, X[non_numeric_cols]], axis=1)

        logger.info(f"Feature engineering complete. Final shape: {final_X.shape}")
        return final_X

    def _flatten_analysis_results(self, ohlcv_df: pd.DataFrame, analysis_results: Dict[str, Any]) -> pd.DataFrame:
        """Flattens the nested dictionary from AnalyticsEngine into DataFrame columns."""
        feature_df = ohlcv_df.copy()

        if 'standard_indicators' in analysis_results:
            for key, value in analysis_results['standard_indicators'].items():
                # This try/except block handles errors for individual indicators.
                try:
                    if isinstance(value, pd.Series):
                        feature_df[f'indicator_{key}'] = value
                    elif isinstance(value, pd.DataFrame):
                         for col in value.columns:
                            feature_df[f'indicator_{key}_{col}'] = value[col]
                    elif isinstance(value, dict):
                        for sub_key, sub_val in value.items():
                             if isinstance(sub_val, (pd.Series, list, np.ndarray)):
                                feature_df[f'indicator_{key}_{sub_key}'] = sub_val
                except Exception as e:
                    logger.warning(f"Could not flatten indicator '{key}': {e}")
        return feature_df

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds a comprehensive set of technical indicators using TA-Lib."""
        logger.info("Adding TA-Lib technical indicators...")
        df_out = df.copy()
        
        op, hi, lo, cl, vo = (df_out[c] for c in ['open', 'high', 'low', 'close', 'volume'])
        
        # Each calculation is in a try/except block to prevent one failure from stopping the whole process.
        try:
            df_out['momentum_rsi'] = talib.RSI(cl)
            df_out['momentum_macd'], df_out['momentum_macdsignal'], df_out['momentum_macdhist'] = talib.MACD(cl)
            df_out['momentum_adx'] = talib.ADX(hi, lo, cl)
        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {e}")

        try:
            df_out['volatility_atr'] = talib.ATR(hi, lo, cl)
            upper, middle, lower = talib.BBANDS(cl)
            df_out['volatility_bb_width'] = (upper - lower) / middle
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")

        try:
            df_out['volume_obv'] = talib.OBV(cl, vo.astype(float))
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {e}")
            
        return df_out

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds time-based features from the DataFrame index."""
        logger.info("Adding time-based features...")
        df_out = df.copy()
        
        try:
            if not isinstance(df_out.index, pd.DatetimeIndex):
                df_out.index = pd.to_datetime(df_out.index)
            
            df_out['time_dayofweek'] = df_out.index.dayofweek
            df_out['time_hour'] = df_out.index.hour
            df_out['time_weekofyear'] = df_out.index.isocalendar().week.astype(int)
        except Exception as e:
            logger.error(f"Could not add time features: {e}")
        
        return df_out
        
    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds interaction and lag features."""
        logger.info("Adding interaction and lag features...")
        df_out = df.copy()
        
        for lag in [1, 2, 3, 5, 10]:
            # This try/except block handles errors if data is too short for a lag.
            try:
                df_out[f'lag_return_{lag}'] = df_out['close'].pct_change(periods=lag)
            except Exception as e:
                logger.warning(f"Could not create lag feature for period {lag}: {e}")

        try:
            df_out['inter_high_low_range'] = df_out['high'] - df_out['low']
            df_out['inter_close_open_diff'] = df_out['close'] - df_out['open']
        except Exception as e:
            logger.warning(f"Could not create interaction features: {e}")
            
        return df_out
