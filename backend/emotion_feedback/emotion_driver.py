# backend/emotion_feedback/emotion_driver.py

import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Import Firestore modules
try:
    from firebase_admin import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    firestore = None
    logger.warning("Firebase Admin SDK not available. Using local storage fallback.")

# --- Configuration Constants (EMOTION_MAP_FILE is still local for now) ---
ANIMATION_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../public/animations"))
EMOTION_MAP_FILE: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "emotion_map.json"))

# Firestore Collection and Document ID for Emotion Data (matching relay_api.py)
EMOTION_COLLECTION = "current_emotion_signals"
EMOTION_DOCUMENT_ID = "latest_signal"

_db_instance = None
_app_id_instance = None

def initialize_firestore_emotion_driver(db_instance, app_id_instance):
    """Initializes the Firestore client for the emotion driver module."""
    global _db_instance, _app_id_instance
    _db_instance = db_instance
    _app_id_instance = app_id_instance
    logger.info("EmotionDriver: Firestore client initialized.")

def load_emotion_map() -> Dict[str, List[str]]:
    """
    Loads the emotion-to-asset mapping from the emotion_map.json file.
    This file remains local for now as it's a configuration mapping.
    """
    if not os.path.exists(EMOTION_MAP_FILE):
        raise FileNotFoundError(f"Emotion map file not found at: {EMOTION_MAP_FILE}")
    try:
        with open(EMOTION_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error decoding emotion map JSON: {e}", e.doc, e.pos)

def get_emotion_asset(emotion_type: str) -> Optional[str]:
    """
    Selects a random asset filename for a given emotion type from the loaded map.
    """
    try:
        emotion_map = load_emotion_map()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"EmotionDriver: Failed to load emotion map: {e}")
        return None
    
    options = emotion_map.get(emotion_type)
    if options and isinstance(options, list) and len(options) > 0:
        return random.choice(options)
    else:
        logger.warning(f"EmotionDriver: No valid assets found for emotion type: {emotion_type}")
        return None

async def broadcast_emotion_to_firestore(emotion_type: str, asset: Optional[str]) -> bool:
    """
    Saves the latest detected emotion and its associated asset to Firestore.
    This replaces the file-based broadcast_emotion function.
    """
    if not _db_instance or not _app_id_instance:
        logger.error("EmotionDriver: Firestore not initialized. Cannot broadcast emotion.")
        return False

    log_data = {
        "emotion": emotion_type,
        "asset": asset,
        "timestamp": datetime.now().isoformat() # Use ISO format for string storage
    }

    try:
        # Construct the document path based on Firestore rules
        # For a single, latest emotion, we store it in a public collection
        doc_path = f"artifacts/{_app_id_instance}/public/data/{EMOTION_COLLECTION}/{EMOTION_DOCUMENT_ID}"
        doc_ref = _db_instance.document(doc_path)
        
        # Use set() to create or overwrite the document with the latest emotion
        await doc_ref.set(log_data)
        logger.info(f"EmotionDriver: Broadcasted emotion '{emotion_type}' to Firestore.")
        return True
    except Exception as e:
        logger.error(f"EmotionDriver: Failed to broadcast emotion to Firestore: {e}", exc_info=True)
        return False

async def trigger_emotion(emotion_type: str) -> Optional[str]:
    """
    Triggers an emotion, selects a random asset for it, and broadcasts it to Firestore.
    """
    asset = get_emotion_asset(emotion_type)
    success = await broadcast_emotion_to_firestore(emotion_type, asset)

    if success:
        logger.info(f"EmotionDriver: Triggered: {emotion_type} -> {asset}")
        return asset
    else:
        logger.error(f"EmotionDriver: Failed to trigger emotion: {emotion_type}")
        return None

# Note: The old file-based broadcast_emotion function is removed.
# The LATEST_EMOTION_LOG_FILE constant is also removed as it's no longer used for writing.
