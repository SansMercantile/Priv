# backend/emotion_feedback/relay_api.py

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import logging
from typing import Dict, Any, Optional, Union

# Import Firestore modules (these will be passed in via dependencies)
try:
    from firebase_admin import firestore
    FIRESTORE_AVAILABLE = True
    FirestoreClient = firestore.Client
except ImportError:
    FIRESTORE_AVAILABLE = False
    firestore = None
    FirestoreClient = Any  # Use Any when firestore is not available
    logging.getLogger(__name__).warning("Firebase Admin SDK not available. Using local storage fallback.")

# Attempt to import the shared constant from emotion_driver (no longer needed for file path, but for conceptual consistency)
try:
    # This constant is for the *topic* if emotion driver publishes to Pub/Sub, not a file path.
    # If emotion_driver.py exists and uses this, keep it. Otherwise, it can be removed.
    from backend.emotion_feedback.emotion_driver import LATEST_EMOTION_LOG_FILE # This was a file path, now conceptual
except ImportError:
    LATEST_EMOTION_LOG_FILE = "logs/latest_emotion.json" # Fallback, though we're moving to Firestore

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Firestore Collection Name for Emotion Data ---
EMOTION_COLLECTION = "current_emotion_signals"
EMOTION_DOCUMENT_ID = "latest_signal" # We'll use a single document to store the latest state

# --- Firestore Dependency for FastAPI ---
# This function will be provided by main.py's lifespan or a global instance
_db_instance = None
_app_id_instance = None

def initialize_firestore_relay_api(db_instance, app_id_instance):
    """Initializes the Firestore client for the relay_api module."""
    global _db_instance, _app_id_instance
    _db_instance = db_instance
    _app_id_instance = app_id_instance
    logger.info("RelayAPI: Firestore client initialized.")

def get_firestore_db():
    """Dependency injector for Firestore database client."""
    if _db_instance is None:
        raise HTTPException(status_code=500, detail="Firestore database not initialized.")
    return _db_instance

def get_app_id():
    """Dependency injector for app ID."""
    if _app_id_instance is None:
        raise HTTPException(status_code=500, detail="App ID not initialized.")
    return _app_id_instance

app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/emotion", response_model=Dict[str, Optional[str]])
async def get_emotion(
    db: FirestoreClient = Depends(get_firestore_db),
    app_id: str = Depends(get_app_id)
) -> Dict[str, Optional[str]]:
    """
    Retrieves the latest emotion signal and its associated asset from Firestore.

    Returns:
        Dict[str, Optional[str]]: A dictionary containing the 'emotion' type and 'asset' filename.
                                  Returns {"emotion": None, "asset": None} if no data is found.
    Raises:
        HTTPException: If there's an error retrieving data from Firestore.
    """
    try:
        # Construct the document path based on Firestore rules
        # For a single, latest emotion, we can store it in a public collection
        doc_path = f"artifacts/{app_id}/public/data/{EMOTION_COLLECTION}/{EMOTION_DOCUMENT_ID}"
        doc_ref = db.document(doc_path)
        
        doc = await doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            emotion_type = data.get("emotion")
            asset_filename = data.get("asset")
            logger.info(f"RelayAPI: Retrieved emotion from Firestore: {emotion_type}, {asset_filename}")
            return {"emotion": emotion_type, "asset": asset_filename}
        else:
            logger.warning("RelayAPI: Latest emotion signal document not found in Firestore.")
            return {"emotion": None, "asset": None}

    except Exception as e:
        logger.error(f"RelayAPI: Failed to retrieve emotion signal from Firestore: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve emotion signal: {e}"
        )
