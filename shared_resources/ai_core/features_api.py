# backend/ai_core/features_api.py

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import numpy as np

from .feature_store import FeatureStore

logger = logging.getLogger(__name__)
router = APIRouter()
feature_store = FeatureStore()

@router.get("/features/{symbol}", response_model=List[Dict[str, Any]])
async def get_features_for_symbol(
    symbol: str, 
    timeframe: str = Query("D1", description="The timeframe for the data (e.g., M1, H1, D1).")
):
    """
    Retrieves the pre-calculated, feature-enriched dataset for a given symbol and timeframe
    from the Feature Store.
    """
    try:
        features_df = feature_store.load_features(symbol, timeframe)
        
        if features_df is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No feature data found for symbol '{symbol}' and timeframe '{timeframe}'."
            )
            
        # Convert DataFrame to a JSON-serializable format
        features_df.reset_index(inplace=True)
        result = features_df.replace({np.nan: None}).to_dict('records')
        
        return result

    except Exception as e:
        logger.error(f"Error serving features for {symbol}/{timeframe}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving feature data.")
