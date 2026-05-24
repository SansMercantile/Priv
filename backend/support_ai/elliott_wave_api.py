# backend/support_ai/elliott_wave_api.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from backend.support_ai.core_ai_handler import get_latest_ai_analysis

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/counts/{symbol}", response_model=List[Dict[str, Any]], summary="Get Elliott Wave Counts")
async def get_elliott_wave_counts(symbol: str):
    """
    Provides the latest Elliott Wave analysis results for a given symbol.

    This endpoint runs the full analysis pipeline and extracts the
    highest-scoring wave counts, which can be used to draw patterns on a chart.
    """
    logger.info(f"Received API request for Elliott Wave counts for symbol: {symbol}")
    try:
        # Run the core analysis handler to get all results
        analysis_results = get_latest_ai_analysis(symbol)

        if "error" in analysis_results:
            raise HTTPException(status_code=404, detail=analysis_results["error"])

        # Extract just the Elliott Wave counts to return
        elliott_wave_counts = analysis_results.get('elliott_wave_counts', [])
        
        if not elliott_wave_counts:
            logger.info(f"No Elliott Wave counts were found for {symbol} during this analysis run.")
            # It's not an error if no waves are found, just return an empty list.
        
        return elliott_wave_counts

    except Exception as e:
        logger.error(f"API Error fetching Elliott Wave counts for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing Elliott Wave analysis.")

