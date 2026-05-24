# backend/trading_engine/oauth_api.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlencode

from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Deriv OAuth 2.0 Configuration ---
DERIV_APP_ID = settings.DERIV_APP_ID
DERIV_AUTHORIZE_URL = "https://oauth.deriv.com/oauth2/authorize"
DERIV_TOKEN_URL = "https://oauth.deriv.com/oauth2/token"

# IMPORTANT: This must match the "OAuth redirect URL" in your Deriv app settings
# In production, this would be your actual frontend URL.
# For local development, it will redirect back to the frontend.
FRONTEND_REDIRECT_URL = "http://localhost:3000/dashboard" 

@router.get("/deriv/login")
async def deriv_login():
    """
    Redirects the user to the Deriv authorization page.
    """
    params = {
        "app_id": DERIV_APP_ID,
        "response_type": "code",
        "scope": "read trade trading_information payments", # from your screenshot
    }
    redirect_url = f"{DERIV_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)

@router.get("/deriv/callback")
async def deriv_callback(code: str = Query(...)):
    """
    Handles the callback from Deriv after user grants permission.
    Exchanges the authorization code for an access token.
    """
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": DERIV_APP_ID,
        # In a real app, a client_secret might be required and stored securely
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(DERIV_TOKEN_URL, data=token_data)
            response.raise_for_status()
            token_info = response.json()

            # In a real app, you would securely save this token_info (especially the
            # access_token and refresh_token) to the user's profile in your database.
            logger.info(f"Successfully received Deriv access token for user.")

            # Redirect the user back to the frontend dashboard with the token info
            # In a real app, you'd likely use a more secure method like setting a cookie.
            # For now, we'll redirect to a success page (or the main dashboard).
            return RedirectResponse(url=f"{FRONTEND_REDIRECT_URL}?deriv_connected=true")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to exchange Deriv auth code for token: {e.response.text}")
            raise HTTPException(status_code=400, detail="Could not verify authorization with Deriv.")