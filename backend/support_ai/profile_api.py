# backend/support_ai/profile_api.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import os
from typing import Dict, Any, Optional, List # ADD THIS IMPORT FOR 'List'
from pydantic import BaseModel, Field

# Import the shared StrategicAdvisor instance (or create a local one if needed)
# It's better to manage instances centrally in main.py and pass/inject them
# For now, we'll keep the local instance creation for this file's refactor.
from backend.support_ai.strategic_advisor import StrategicAdvisor # Assuming StrategicAdvisor handles profile loading internally

# --- Configuration Constants ---
PROFILE_FILE = "logs/user_profile.json"

# --- Pydantic Model for User Profile ---
# Define the structure of the user profile, matching frontend expectations.
# This ensures validation of incoming data and clarity of output.
class AITradingBotControl(BaseModel):
    enabled: bool = False
    kill_switch_triggered: bool = False

class UserProfile(BaseModel):
    preferred_assets: List[str] = Field(default_factory=list)
    risk_tolerance: str = "not set"
    trading_style: str = "unknown"
    emotional_tendencies: List[str] = Field(default_factory=list)
    primary_goals: List[str] = Field(default_factory=list)
    tone_preference: str = "neutral"
    ai_trading_bot_control: AITradingBotControl = Field(default_factory=AITradingBotControl)

# Initialize the router for profile-related endpoints
# The main FastAPI app will include this router later.
router = APIRouter()

# Instantiate StrategicAdvisor if it manages profile loading itself, or inject it
# We keep it here for now as in original code, but central management is better.
# advisor = StrategicAdvisor() # Removed, as get_profile will load directly or it should be injected.


# --- Helper Function for Profile Loading ---
def _load_profile_data() -> UserProfile:
    """
    Loads user profile data from the JSON file, or returns a default profile.
    Handles file not found and JSON decoding errors.
    """
    if not os.path.exists(PROFILE_FILE):
        return UserProfile() # Return default empty profile if file doesn't exist
    
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            raw_profile = json.load(f)
        # Validate and return the profile using the Pydantic model
        return UserProfile(**raw_profile)
    except json.JSONDecodeError as e:
        print(f"Error decoding user profile JSON from {PROFILE_FILE}: {e}")
        # Consider logging the corrupted file or moving it for recovery
        raise HTTPException(
            status_code=500,
            detail="User profile file is corrupted. Please contact support."
        )
    except Exception as e:
        print(f"An unexpected error occurred while loading profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load user profile due to an internal error."
        )


# --- API Endpoints ---

@router.get("/", response_model=UserProfile)
def get_user_profile() -> UserProfile:
    """
    Retrieves the current user's profile.
    Returns a default empty profile if no saved profile exists.
    """
    return _load_profile_data()


@router.post("/", response_model=Dict[str, str]) # Use a simple dict response for status
async def update_user_profile(
    updated_profile: UserProfile # FastAPI will automatically validate the incoming JSON against this model
) -> Dict[str, str]:
    """
    Updates the user's profile with new data.
    The incoming data is validated against the UserProfile Pydantic model.
    """
    # Ensure the logs directory exists before writing
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
    
    try:
        # Convert Pydantic model back to a dictionary for JSON dumping
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_profile.model_dump(), f, indent=2) # Use .model_dump() for dictionary output
        return {"status": "success", "message": "Profile updated successfully."}
    except IOError as e:
        print(f"Error writing user profile to {PROFILE_FILE}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save user profile due to file system error."
        )
    except Exception as e:
        print(f"An unexpected error occurred while updating profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile due to an internal error."
        )


# --- Critical: Removed the duplicated handle_support endpoint ---
# The handle_support endpoint was defined identically in multiple API files.
# It should ONLY be defined once, preferably in support_api.py (which we will refactor next).
# @router.post("/")
# async def handle_support(request: Request):
#     payload = await request.json()
#     return advisor.respond(payload.get("message", ""))