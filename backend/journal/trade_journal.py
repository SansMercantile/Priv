import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Import Firebase/Firestore modules (these will be passed in from main.py)
# For local testing, you might need to set up a dummy db or mock these,
# but in the deployed environment, main.py will provide them.
_db = None # Placeholder for Firestore client instance
_auth = None # Placeholder for Firebase Auth instance
_app_id = None # Placeholder for Canvas app ID

logger = logging.getLogger(__name__)

# --- Pydantic Model for a Trade Journal Entry ---
class TradeJournalEntry(BaseModel):
    """
    Represents a single entry in the trade journal.
    Includes metadata and user-defined details about a trade.
    """
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the journal entry.")
    trade_details: Dict[str, Any] = Field(..., description="Details of the trade logged.")
    user_id: Optional[str] = Field(None, description="ID of the user associated with the trade.")

# --- Firestore Collection Name ---
TRADE_JOURNAL_COLLECTION = "trade_journal_entries"

def initialize_firestore_trade_journal(db_instance, auth_instance, app_id_instance):
    """Initializes the Firestore client for the trade journal module."""
    global _db, _auth, _app_id
    _db = db_instance
    _auth = auth_instance
    _app_id = app_id_instance
    logger.info("TradeJournal: Firestore client initialized.")

async def log_trade(entry_data: Dict[str, Any]) -> bool:
    """
    Logs a single trade entry to Firestore.
    Each entry is automatically timestamped.
    """
    if not _db or not _auth:
        logger.error("TradeJournal: Firestore not initialized. Cannot log trade.")
        return False

    try:
        # Get current user ID (or generate a random one if anonymous)
        user_id = _auth.currentUser.uid if _auth.currentUser else "anonymous-" + os.urandom(16).hex()
        
        # Create a Pydantic model instance
        journal_entry = TradeJournalEntry(trade_details=entry_data, user_id=user_id)
        
        # Convert Pydantic model to dictionary for Firestore (model_dump handles datetime)
        entry_dict = journal_entry.model_dump()
        
        # Determine collection path based on public/private data rules
        # For trade journals, it's typically private to the user
        collection_path = f"artifacts/{_app_id}/users/{user_id}/{TRADE_JOURNAL_COLLECTION}"
        
        # Add the document to the specified collection
        doc_ref = await _db.collection(collection_path).add(entry_dict)
        logger.info(f"TradeJournal: Logged trade entry to Firestore. Document ID: {doc_ref.id}")
        return True
    except Exception as e:
        logger.error(f"TradeJournal: Failed to log trade entry to Firestore: {e}", exc_info=True)
        return False

async def load_journal() -> List[TradeJournalEntry]:
    """
    Loads all trade journal entries from Firestore for the current user.
    """
    if not _db or not _auth:
        logger.error("TradeJournal: Firestore not initialized. Cannot load journal.")
        return []

    try:
        user_id = _auth.currentUser.uid if _auth.currentUser else "anonymous-" + os.urandom(16).hex()
        collection_path = f"artifacts/{_app_id}/users/{user_id}/{TRADE_JOURNAL_COLLECTION}"
        
        # Get all documents in the collection
        docs = await _db.collection(collection_path).get()
        
        journal_entries: List[TradeJournalEntry] = []
        for doc in docs:
            try:
                # Convert Firestore document data back to Pydantic model
                entry_data = doc.to_dict()
                # Ensure timestamp is a datetime object if coming from Firestore as a timestamp object
                if 'timestamp' in entry_data and hasattr(entry_data['timestamp'], 'toDate'):
                    entry_data['timestamp'] = entry_data['timestamp'].toDate()
                journal_entries.append(TradeJournalEntry(**entry_data))
            except Exception as e:
                logger.warning(f"TradeJournal: Skipping malformed Firestore document {doc.id}: {e}")
        
        logger.info(f"TradeJournal: Loaded {len(journal_entries)} trade journal entries from Firestore for user {user_id}.")
        return journal_entries
    except Exception as e:
        logger.error(f"TradeJournal: Failed to load journal entries from Firestore: {e}", exc_info=True)
        return []

# Note: The old file-based functions (log_trade_file, load_journal_file) are removed.
# The JOURNAL_FILE_PATH constant is also removed as it's no longer used.


class TradeJournal:
    """Trade Journal class for compatibility with existing code"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def log_trade(self, entry_data: Dict[str, Any]) -> bool:
        """Log a trade entry"""
        return await log_trade(entry_data)
        
    async def load_journal(self) -> List[TradeJournalEntry]:
        """Load all journal entries"""
        return await load_journal()
