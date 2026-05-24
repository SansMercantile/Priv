# backend/support_ai/history_api.py

from fastapi import APIRouter, HTTPException, Depends
import json
import os
from typing import List, Dict, Any

# --- Import shared constants ---
# Assuming a central config file now holds the log path
from backend.config import settings

# --- Initialize the API Router ---
router = APIRouter()

# --- Dependency to get recent conversations ---
def get_recent_conversations_dependency() -> List[Dict[str, Any]]:
    """
    Dependency to retrieve recent conversation logs.
    """
    log_file_path = settings.CONVERSATION_LOG_PATH
    if not os.path.exists(log_file_path):
        return []
    
    logs: List[Dict[str, Any]] = []
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            # Read lines in reverse to get the most recent first
            for line in reversed(list(f)):
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    # Log this warning if needed
                    pass
        return logs
    except IOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read conversation log: {e}"
        )

# --- API Endpoints ---
@router.get("/", response_model=List[Dict[str, str]])
def get_recent_history(
    limit: int = 100,
    conversations: List[Dict[str, Any]] = Depends(get_recent_conversations_dependency)
) -> List[Dict[str, str]]:
    """
    Retrieves the most recent conversation history logs.
    """
    # The dependency already gets the logs, now we just format and limit them.
    formatted_logs = [
        {
            "user": entry.get("user", ""),
            "ai": entry.get("ai", ""),
            "emotion": entry.get("emotion"),
            "timestamp": entry.get("timestamp", "")
        }
        for entry in conversations
    ]
    return formatted_logs[:limit]