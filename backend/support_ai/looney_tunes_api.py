# backend/support_ai/looney_tunes_api.py

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# This new API provides an endpoint to trigger "Looney Tunes" style actions
# for the AI personas on the frontend.

logger = logging.getLogger(__name__)
router = APIRouter()

# In a real application, this would be a more sophisticated connection manager.
# For now, we'll use a simple list to keep track of active WebSocket connections.
from ..main import vision_websockets

class ActionRequest(BaseModel):
    action_type: str  # e.g., "SPAWN_OBJECT"
    payload: Dict[str, Any] # e.g., {"object_type": "chair", "position": [x, y, z]}

@router.post("/trigger-action")
async def trigger_looney_tunes_action(action: ActionRequest):
    """
    Receives a request to trigger a dynamic action and broadcasts it
    to all connected frontend clients via WebSocket.
    """
    if not vision_websockets:
        logger.warning("No active vision clients to send action to.")
        return {"status": "success", "message": "Action received, but no clients connected."}

    logger.info(f"Broadcasting Looney Tunes action: {action.action_type} with payload: {action.payload}")
    
    # Create the message payload to send over the WebSocket
    message = {
        "type": "looney_tunes_action",
        "action": action.dict()
    }
    
    # Broadcast the message to all connected clients
    # Using a list comprehension to handle potential disconnections during iteration
    for ws in list(vision_websockets):
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send action to a WebSocket client: {e}")
            vision_websockets.remove(ws)
            
    return {"status": "success", "message": f"Action '{action.action_type}' broadcast to {len(vision_websockets)} clients."}
