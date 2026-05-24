import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# Import Firebase/Firestore modules (these will be passed in from main.py)
_db = None # Placeholder for Firestore client instance
_auth = None # Placeholder for Firebase Auth instance
_app_id = None # Placeholder for Canvas app ID

logger = logging.getLogger(__name__)

# --- Pydantic Model for a Card Token ---
class CardToken(BaseModel):
    """Represents a stored payment credential."""
    token: str = Field(..., description="Obfuscated/encrypted token from the payment processor.")
    last_four_digits: str = Field(..., description="The last four digits of the card for identification.")
    currency: str = Field("USD", description="The currency associated with the card.")
    user_id: Optional[str] = Field(None, description="ID of the user who owns this token.")

# --- Firestore Collection Name ---
CARD_TOKENS_COLLECTION = "card_tokens"

def initialize_firestore_wallet_vault(db_instance, auth_instance, app_id_instance):
    """Initializes the Firestore client for the wallet vault module."""
    global _db, _auth, _app_id
    _db = db_instance
    _auth = auth_instance
    _app_id = app_id_instance
    logger.info("WalletVault: Firestore client initialized.")

class WalletVault:
    """
    Conceptual module representing secure custody and wallet infrastructure.
    It manages access to stored payment credentials (tokens) for automated funding.
    """
    def __init__(self): # Removed vault_file_path from init
        self.card_tokens: Dict[str, CardToken] = {} # Now stores CardToken objects
        # No longer loading from mock file in __init__; data will be fetched from Firestore on demand
        logger.info("Priv's WalletVault initialized (conceptual, now Firestore-backed).")

    async def _get_user_collection_path(self) -> Optional[str]:
        """Helper to get the user-specific Firestore collection path."""
        if not _db or not _auth:
            logger.error("WalletVault: Firestore not initialized. Cannot get collection path.")
            return None
        user_id = _auth.currentUser.uid if _auth.currentUser else "anonymous-" + os.urandom(16).hex()
        return f"artifacts/{_app_id}/users/{user_id}/{CARD_TOKENS_COLLECTION}"

    async def store_card_token(self, card_id: str, token: str, last_four_digits: str, currency: str) -> bool:
        """
        Stores a new card token in Firestore.
        """
        collection_path = await self._get_user_collection_path()
        if not collection_path:
            return False
        
        user_id = _auth.currentUser.uid if _auth.currentUser else "anonymous-" + os.urandom(16).hex()
        new_card = CardToken(token=token, last_four_digits=last_four_digits, currency=currency, user_id=user_id)
        
        try:
            # Use set() with a specific document ID (card_id) for easy retrieval
            doc_ref = _db.collection(collection_path).document(card_id)
            await doc_ref.set(new_card.model_dump())
            logger.info(f"WalletVault: Stored conceptual token for card_id: {card_id} in Firestore.")
            return True
        except Exception as e:
            logger.error(f"WalletVault: Failed to store card token to Firestore: {e}", exc_info=True)
            return False

    async def retrieve_card_token(self, card_id: str) -> Optional[CardToken]:
        """
        Retrieves a conceptual card token object from Firestore.
        """
        collection_path = await self._get_user_collection_path()
        if not collection_path:
            return None

        try:
            doc_ref = _db.collection(collection_path).document(card_id)
            doc = await doc_ref.get()
            
            if doc.exists:
                token_data = doc.to_dict()
                token_obj = CardToken(**token_data)
                logger.info(f"WalletVault: Retrieved conceptual token for card_id: {card_id} from Firestore.")
                return token_obj
            else:
                logger.warning(f"WalletVault: Card token for '{card_id}' not found in Firestore.")
                return None
        except Exception as e:
            logger.error(f"WalletVault: Failed to retrieve card token from Firestore: {e}", exc_info=True)
            return None

    async def initiate_deposit(self, card_id: str, amount: float) -> bool:
        """
        Conceptually initiates a deposit process using a stored card token from Firestore.
        """
        token_obj = await self.retrieve_card_token(card_id)
        if token_obj:
            logger.info(f"WalletVault: Conceptual deposit initiated: {amount:.2f} {token_obj.currency} using card ending in '{token_obj.last_four_digits}'.")
            # In a real system, this would interact with a payment gateway.
            return True
        return False

    async def initiate_withdrawal(self, card_id: str, amount: float) -> bool:
        """
        Conceptually initiates a withdrawal process to a stored card from Firestore.
        """
        token_obj = await self.retrieve_card_token(card_id)
        if token_obj:
            logger.info(f"WalletVault: Conceptual withdrawal initiated: {amount:.2f} to card ending in '{token_obj.last_four_digits}'.")
            # In a real system, this would interact with a payment gateway.
            return True
        return False

    # Note: The old file-based functions (_load_mock_vault, _save_mock_vault) are removed.
    # The VAULT_MOCK_FILE constant is also removed as it's no longer used.
