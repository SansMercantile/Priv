import logging
import hashlib # For cryptographic hashing
import json # For JSON serialization of token data
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Pydantic Model for an Action Token ---
class ActionToken(BaseModel):
    """
    Represents a cryptographically verifiable record (token) for a Priv-originated action.
    This encapsulates rationale, context, and compliance status for auditability.
    """
    action_id: str = Field(..., description="Unique ID for the action.")
    agent_id: str = Field(..., description="ID of the Priv agent originating the action.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the action.")
    action_type: str = Field(..., description="Type of action (e.g., 'trade_execution', 'proposal_submission', 'calibration_event').")
    action_details: Dict[str, Any] = Field(..., description="Detailed payload of the action (e.g., trade parameters, decision outcome).")
    context_metadata: Dict[str, Any] = Field(default_factory=dict, description="Market, account, and environmental context at time of action.")
    
    # Compliance and Ethical Status at the time of action
    compliance_status: str = Field(..., description="Regulatory compliance status ('compliant', 'non_compliant', 'flagged').")
    ethical_status: str = Field(..., description="Ethical compliance status ('compliant', 'non_compliant', 'flagged').")
    
    # Cryptographic signature to ensure immutability and authenticity
    cryptographic_signature: str = Field(..., description="SHA256 hash of the token's content, representing its integrity.")

class ActionTokenizer:
    """
    Generates and verifies cryptographically signed action tokens for Priv's operations.
    This serves as the core of Priv's Action Tokenizer.
    """
    def __init__(self, signing_key: str = "default_secure_key"): # In real system, this would be a real crypto key
        self.signing_key = signing_key # Conceptual signing key
        logger.info("Priv's ActionTokenizer initialized.")

    def _generate_content_hash(self, data: Dict[str, Any]) -> str:
        """Generates a SHA256 hash of the token's core content (excluding the final signature itself)."""
        # Ensure consistent serialization for hashing
        # Sort keys to ensure consistent JSON string for hashing
        json_string = json.dumps(data, sort_keys=True, default=str) # default=str handles datetime objects
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()

    def generate_token(
        self,
        action_id: str,
        agent_id: str,
        action_type: str,
        action_details: Dict[str, Any],
        context_metadata: Dict[str, Any],
        compliance_status: str,
        ethical_status: str
    ) -> ActionToken:
        """
        Generates a new, cryptographically signed Action Token.

        Args:
            action_id (str): Unique ID for this specific action.
            agent_id (str): ID of the Priv agent performing the action.
            action_type (str): Type of action.
            action_details (Dict[str, Any]): Detailed payload of the action.
            context_metadata (Dict[str, Any]): Context at time of action.
            compliance_status (str): Regulatory compliance status.
            ethical_status (str): Ethical compliance status.

        Returns:
            ActionToken: The newly generated and signed action token.
        """
        # Create a dict that represents the token's verifiable content
        token_content = {
            "action_id": action_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(),
            "action_type": action_type,
            "action_details": action_details,
            "context_metadata": context_metadata,
            "compliance_status": compliance_status,
            "ethical_status": ethical_status
        }

        # Generate cryptographic signature (SHA256 hash of the content)
        # For actual cryptographic signing (e.g., with RSA or ECDSA), you'd use a private key.
        # Here, it's a hash to represent immutability of recorded content.
        content_hash = self._generate_content_hash(token_content)
        
        # Add the signature to the token data
        token_data = token_content.copy() # Create a copy to add signature field
        token_data['cryptographic_signature'] = content_hash

        token = ActionToken(**token_data)
        logger.info(f"Priv: Generated ActionToken for action '{action_id}' ({action_type}).")
        return token

    def verify_token(self, token: ActionToken) -> bool:
        """
        Verifies the integrity of an Action Token by recomputing its hash.
        This ensures the token's content has not been tampered with.

        Args:
            token (ActionToken): The ActionToken object to verify.

        Returns:
            bool: True if the token's signature is valid, False otherwise.
        """
        # Reconstruct the content that was originally hashed
        reconstructed_content = {
            "action_id": token.action_id,
            "agent_id": token.agent_id,
            "timestamp": token.timestamp,
            "action_type": token.action_type,
            "action_details": token.action_details,
            "context_metadata": token.context_metadata,
            "compliance_status": token.compliance_status,
            "ethical_status": token.ethical_status
        }
        
        computed_hash = self._generate_content_hash(reconstructed_content)
        is_valid = computed_hash == token.cryptographic_signature
        
        if is_valid:
            logger.info(f"Priv: ActionToken '{token.action_id}' verification: SUCCESS.")
        else:
            logger.warning(f"Priv: ActionToken '{token.action_id}' verification: FAILED (computed hash '{computed_hash}' != stored hash '{token.cryptographic_signature}').")
        
        return is_valid

# Example Usage (for testing ActionTokenizer in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    tokenizer = ActionTokenizer(signing_key="my_secret_key_123")

    # --- Scenario 1: Generate a trade execution token ---
    print("\n--- Generating Trade Execution Token ---")
    trade_details = {
        "symbol": "EURUSD",
        "action": "BUY",
        "volume": 0.1,
        "price": 1.0850,
        "trade_id": "trade_xyz_123",
        "pnl": 50.0
    }
    context_data = {
        "market_state": "trending_up",
        "news_impact": "low",
        "sentiment_score": 0.7
    }
    
    trade_token = tokenizer.generate_token(
        action_id="trade_exec_001",
        agent_id="Priv_Main_Strategist",
        action_type="trade_execution",
        action_details=trade_details,
        context_metadata=context_data,
        compliance_status="compliant",
        ethical_status="compliant"
    )
    print(f"Generated Trade Token:\n{trade_token.model_dump_json(indent=2)}")

    print("\n--- Verifying Trade Execution Token ---")
    is_valid_token = tokenizer.verify_token(trade_token)
    print(f"Token is valid: {is_valid_token}")

    # --- Scenario 2: Simulate a tampered token ---
    print("\n--- Simulating Tampered Token ---")
    tampered_token_data = trade_token.model_dump()
    tampered_token_data['action_details']['pnl'] = -1000.0 # Change PnL to simulate tampering
    # Create a new ActionToken object from the tampered data, but keep old signature
    tampered_token_obj = ActionToken(**tampered_token_data)

    is_tampered_valid = tokenizer.verify_token(tampered_token_obj)
    print(f"Tampered token is valid: {is_tampered_valid}") # Expected: False

    # --- Scenario 3: Generate a proposal token with flagged compliance ---
    print("\n--- Generating Proposal Token (Flagged Regulatory) ---")
    proposal_details = {
        "symbol": "BTCUSD",
        "action": "SELL",
        "volume": 0.05,
        "confidence": 0.75
    }
    flagged_proposal_token = tokenizer.generate_token(
        action_id="prop_002",
        agent_id="Priv_Risk_Manager",
        action_type="proposal_submission",
        action_details=proposal_details,
        context_metadata={"market": "volatile"},
        compliance_status="flagged", # Example: flagged by regulatory check
        ethical_status="compliant"
    )
    print(f"Generated Flagged Proposal Token:\n{flagged_proposal_token.model_dump_json(indent=2)}")
    print(f"Token is valid: {tokenizer.verify_token(flagged_proposal_token)}")