# backend/ai_core/feature_store.py

import logging
import os
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

class FeatureStore:
    """
    A simple file-based feature store for saving and loading feature-enriched DataFrames.
    Uses the efficient Feather format.
    """
    def __init__(self, base_path: str = "data/feature_store"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"FeatureStore initialized at base path: {self.base_path}")

    def _get_filepath(self, symbol: str, timeframe: str) -> str:
        """Constructs a standardized filepath, ensuring it is within the base directory."""
        filename = f"{symbol.replace('/', '_').upper()}_{timeframe.upper()}.feather"
        # Construct the full path and normalize it
        fullpath = os.path.normpath(os.path.join(self.base_path, filename))
        # Ensure the path is within the base directory
        base_abs = os.path.abspath(self.base_path)
        fullpath_abs = os.path.abspath(fullpath)
        if not fullpath_abs.startswith(base_abs + os.sep):
            raise ValueError("Attempted access outside of feature store directory.")
        return fullpath

    def save_features(self, symbol: str, timeframe: str, features_df: pd.DataFrame):
        """Saves a feature DataFrame to the store."""
        if features_df.empty:
            logger.warning(f"Attempted to save an empty DataFrame for {symbol}/{timeframe}. Aborting.")
            return
            
        filepath = self._get_filepath(symbol, timeframe)
        try:
            # Feather requires a default index.
            df_to_save = features_df.reset_index()
            df_to_save.to_feather(filepath)
            logger.info(f"Successfully saved features for {symbol}/{timeframe} to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save features to {filepath}: {e}", exc_info=True)

    def load_features(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Loads a feature DataFrame from the store."""
        filepath = self._get_filepath(symbol, timeframe)
        if not os.path.exists(filepath):
            return None
        
        try:
            df = pd.read_feather(filepath)
            # Restore the timestamp index
            if 'time' in df.columns:
                df.set_index('time', inplace=True)
            elif 'timestamp' in df.columns:
                 df.set_index('timestamp', inplace=True)
            logger.info(f"Successfully loaded features for {symbol}/{timeframe} from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Failed to load features from {filepath}: {e}", exc_info=True)
            return None
