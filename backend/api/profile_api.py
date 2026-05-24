from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'demo_profiles.json')
# Normalize path
DATA_FILE: str = os.path.abspath(DATA_FILE_PATH)

# Ensure directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Basic in-file persistence for demo profiles
def _load_profiles() -> Dict[str, Any]:
    try:
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading profiles: {e}")
        return {}


def _save_profiles(profiles: Dict[str, Any]):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving profiles: {e}")


class ProfileUpdate(BaseModel):
    id: str = "demo_user"
    display_name: str = "Demo User"
    preferred_agents: list[str] = []
    tax_residency: Optional[str] = None
    demo_mode: bool = True
    metadata: dict[str, Any] = {}


@router.get("/")
async def get_profile(user_id: str = 'demo_user') -> Dict[str, Any]:
    profiles = _load_profiles()
    profile: Dict[str, Any] | None = profiles.get(user_id)
    if not profile:
        # Provide a default demo profile
        profile = {
            "id": "demo_user",
            "display_name": "Demo User",
            "preferred_agents": [],
            "tax_residency": None,
            "demo_mode": True,
            "metadata": {}
        }
    return {"success": True, "data": profile}


@router.put("/")
@router.post("/")
async def update_profile(profile: ProfileUpdate) -> Dict[str, Any]:
    try:
        profiles = _load_profiles()
        profiles[profile.id] = profile.model_dump()
        _save_profiles(profiles)
        return {"success": True, "data": profiles[profile.id]}
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/onboarding")
async def onboarding_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        user_id = payload.get('id', 'demo_user')
        profiles = _load_profiles()
        profile: Dict[str, Any] = profiles.get(user_id, {"id": user_id, "display_name": "Demo User", "preferred_agents": [], "tax_residency": None, "demo_mode": True, "metadata": {}})
        # Update known fields
        if 'preferred_agents' in payload:
            profile['preferred_agents'] = payload['preferred_agents']
        if 'tax_residency' in payload:
            profile['tax_residency'] = payload['tax_residency']
        profile['demo_mode'] = payload.get('demo_mode', profile.get('demo_mode', True))
        profiles[user_id] = profile
        _save_profiles(profiles)
        return {"success": True, "data": profile}
    except Exception as e:
        logger.error(f"Error in onboarding update: {e}")
        raise HTTPException(status_code=500, detail=str(e))
