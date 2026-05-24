# backend/support_ai/insight_api.py

from fastapi import APIRouter, HTTPException # Ensure HTTPException is imported
from typing import Dict, Any, Optional # Ensure typing is imported

# Import the core insight generation function
from backend.support_ai.insight_synthesizer import synthesize_recent_insights

# --- Initialize the API Router ---
# This router will contain insight-related endpoints.
# The main FastAPI app (in main.py) will include this router.
router = APIRouter()


# --- API Endpoints ---

# This endpoint handles GET requests for the insight summary.
# It explicitly sets the response_model and includes error handling.
@router.get("/", response_model=Dict[str, str]) # Changed from POST to GET and path from "/insight" to "/"
def get_insight_summary() -> Dict[str, str]:
    """
    Retrieves a synthesized summary of recent insights.

    Returns:
        Dict[str, str]: A dictionary containing the 'summary' string.
    Raises:
        HTTPException: If there's an error during insight synthesis (e.g., from reading logs).
    """
    try:
        summary = synthesize_recent_insights()
        return {"summary": summary}
    except Exception as e:
        print(f"[ERROR] Error synthesizing insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to synthesize insights due to an internal error: {e}"
        )


# --- Critical: Removed all duplicated code ---
# The following elements were duplicated across multiple API files and have been removed:
# - app = FastAPI() (should ONLY be in backend/main.py)
# - app.add_middleware(...) (should ONLY be configured on the main app in backend/main.py)
# - `router = APIRouter()` was initialized, but then another @router.post("/") was defined.
#   Only one router definition per file for clarity.
# - `advisor = StrategicAdvisor()` (instance management should be centralized or handled by dependency injection).
# - `@router.post("/") async def handle_support(...)` (this duplicate endpoint for support messages
#   has been removed and should reside ONLY in backend/support_ai/support_api.py).
# - Duplicate imports like FastAPI, APIRouter, Request, StrategicAdvisor etc.