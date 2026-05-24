# backend/support_ai/support_api.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional # Import Optional for subject

from backend.dependencies import get_strategic_advisor
from backend.support_ai.strategic_advisor import StrategicAdvisor
from backend.support_ai.emotion_patterns import is_in_greed_cooldown

logger = logging.getLogger(__name__)
router = APIRouter()

# UPDATED: To match the Postman payload
class MessagePayload(BaseModel):
    subject: Optional[str] = None # Make subject optional or required based on your needs
    message: str

@router.post("/")
async def post_support_message(
    payload: MessagePayload,
    advisor: StrategicAdvisor = Depends(get_strategic_advisor)
) -> Dict[str, Any]:
    """
    Handles incoming user messages for the AI assistant.
    """
    # --- ADDED THIS LINE FOR DEBUGGING ---
    logger.info(f"Received POST request to /api/v1/support/ with message: {payload.message[:50]}...")
    # --- END DEBUG LINE ---

    try:
        user_message = payload.message

        if is_in_greed_cooldown():
            logger.info("Greed cooldown active, returning specific message.")
            return {
                "message": "You're in a cooldown period. Take a breath and review your plan.",
                "emotion": "cooldown_active",
                "state_snapshot": None
            }

        logger.info(f"Calling StrategicAdvisor.respond with message: {user_message[:50]}...")
        response_data = await advisor.respond(user_message) 
        logger.info(f"StrategicAdvisor.respond returned response.")
        
        return {
            "message": response_data.get("message", "No message from AI."),
            "emotion": response_data.get("emotion"),
            "state_snapshot": response_data.get("state_snapshot")
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred in /support endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

