# backend/support_ai/analytics_api.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Tuple

# --- CORRECTED: Import from the log analysis module, not the market analysis engine ---
from backend.support_ai.insight_synthesizer import get_top_emotions, get_frequent_phrases

# --- Initialize the API Router ---
router = APIRouter()

@router.get("/", response_model=Dict[str, List[Tuple[str, int]]])
def get_analytics_dashboard_data() -> Dict[str, List[Tuple[str, int]]]:
    """
    Retrieves aggregated analytics data from conversation logs, such as top
    emotions and frequent user phrases.
    """
    try:
        # --- CORRECTED: Call the right functions from the right module ---
        top_emotions = get_top_emotions()
        top_phrases = get_frequent_phrases()
        
        return {
            "top_emotions": top_emotions,
            "top_user_terms": top_phrases
        }
    except Exception as e:
        print(f"[ERROR] Error generating analytics data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics data due to an internal error: {e}"
        )