import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from pydantic import BaseModel, Field, conlist # conlist for fixed-size lists in Pydantic
import random
from collections import Counter
import numpy as np
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# --- Pydantic Models for Synthetic Account Profile ---
class MoneyManagementMode(str, Enum):
    FIXED = "fixed"           # Fixed lot size
    RISK_BASED = "risk_based" # Lot size based on risk appetite and margin
    DYNAMIC = "dynamic"       # Uses behavioral factors and randomness

class BehaviorProfile(BaseModel):
    """Defines the behavioral characteristics of a synthetic account."""
    risk_appetite: float = Field(0.5, ge=0.0, le=1.0, description="Risk appetite score [0, 1].")
    time_horizon: str = Field("medium", description="Investment time horizon (short, medium, long).")
    volatility_response: str = Field("neutral", description="How account reacts to volatility (aggressive, neutral, defensive).")
    # New: For multi-agent inheritance / hybrid behaviors
    parent_personas: List[str] = Field(default_factory=list, description="IDs of parent personas for hybrid behavior simulation.")

class SyntheticAccount(BaseModel):
    """
    Represents a single non-fiat pseudo account for simulation purposes.
    Can be used for multi-agent inheritance simulation.
    """
    account_id: str = Field(..., description="Unique ID for the synthetic account.")
    initial_equity: float = Field(..., gt=0, description="Starting equity.")
    current_equity: float = Field(..., gt=0, description="Current floating equity.")
    balance: float = Field(..., gt=0, description="Current balance (equity excluding PnL).")
    free_margin: float = Field(..., ge=0, description="Available margin for new trades.")
    unrealized_pnl: float = Field(0.0, description="Unrealized profit/loss from open positions.")
    behavior_profile: BehaviorProfile = Field(default_factory=BehaviorProfile)
    # Track historical performance during simulation (simplified)
    simulated_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Log of simulated trades.")
    
    # Context for behavior adjustment in simulation
    current_market_stress_level: float = Field(0.0, ge=0.0, le=1.0, description="Simulated market stress [0,1].")

    def apply_simulated_pnl(self, pnl: float):
        """Simulates applying profit/loss to the account."""
        self.current_equity += pnl
        self.unrealized_pnl += pnl # For simplicity, PnL impacts equity and unrealized
        self.free_margin = self.current_equity - self.unrealized_pnl # Simplified free margin
        logger.debug(f"Synthetic Account '{self.account_id}': PnL {pnl:.2f}, new equity: {self.current_equity:.2f}")

    def record_simulated_trade(self, trade_details: Dict[str, Any]):
        """Records a simulated trade within this account's history."""
        self.simulated_trades.append({"timestamp": datetime.now().isoformat(), "details": trade_details})
        logger.debug(f"Synthetic Account '{self.account_id}': Recorded simulated trade: {trade_details.get('symbol')}, {trade_details.get('action')}")

class SyntheticAccountGenerator:
    """
    Generates and manages synthetic trading accounts for simulation.
    Supports instantiating accounts with various behavior profiles,
    including those derived from "multi-agent inheritance".
    """
    def __init__(self):
        self.accounts: Dict[str, SyntheticAccount] = {}
        self.next_account_id = 1
        logger.info("Priv's SyntheticAccountGenerator initialized.")

    def create_account(
        self,
        initial_equity: float = 10000.0,
        risk_appetite: float = 0.5,
        time_horizon: str = "medium",
        volatility_response: str = "neutral",
        parent_personas: Optional[List[str]] = None,
        account_id: Optional[str] = None
    ) -> SyntheticAccount:
        """
        Creates a new synthetic trading account with a defined behavior profile.

        Args:
            initial_equity (float): Starting equity for the account.
            risk_appetite (float): Risk appetite score [0, 1].
            time_horizon (str): Investment time horizon.
            volatility_response (str): How account reacts to volatility.
            parent_personas (Optional[List[str]]): For multi-agent inheritance simulation.
            account_id (Optional[str]): Specific ID for the account, or auto-generated.

        Returns:
            SyntheticAccount: The newly created synthetic account.
        """
        if account_id is None:
            account_id = f"SYNTH_ACC_{self.next_account_id:04d}"
            self.next_account_id += 1
        
        behavior_profile = BehaviorProfile(
            risk_appetite=risk_appetite,
            time_horizon=time_horizon,
            volatility_response=volatility_response,
            parent_personas=parent_personas if parent_personas else []
        )

        new_account = SyntheticAccount(
            account_id=account_id,
            initial_equity=initial_equity,
            current_equity=initial_equity,
            balance=initial_equity,
            free_margin=initial_equity,
            unrealized_pnl=0.0,
            behavior_profile=behavior_profile
        )
        self.accounts[account_id] = new_account
        logger.info(f"Priv: Synthetic account '{account_id}' created with equity {initial_equity:.2f} and profile: {behavior_profile.model_dump_json()}.")
        return new_account

    def get_account(self, account_id: str) -> Optional[SyntheticAccount]:
        """Retrieves a synthetic account by its ID."""
        return self.accounts.get(account_id)

    def simulate_hybrid_behavior(self, parent_personas: List[Dict[str, Any]]) -> BehaviorProfile:
        """
        Simulates the synthesis of a new behavior profile based on multiple parent personas.
        This is a conceptual implementation of multi-agent inheritance.

        Args:
            parent_personas (List[Dict[str, Any]]): List of parent persona dictionaries,
                                                  e.g., from different PrivAgent instances.

        Returns:
            BehaviorProfile: A synthesized behavior profile.
        """
        if not parent_personas:
            return BehaviorProfile() # Return default if no parents

        # Simple averaging for numerical attributes, majority for categorical
        avg_risk_appetite = np.mean([p.get('risk_appetite', 0.5) for p in parent_personas])
        
        # For categorical, a simple majority vote (or most common)
        time_horizons = [p.get('time_horizon', 'medium') for p in parent_personas]
        vol_responses = [p.get('volatility_response', 'neutral') for p in parent_personas]

        most_common_horizon = Counter(time_horizons).most_common(1)[0][0] if time_horizons else "medium"
        most_common_vol_response = Counter(vol_responses).most_common(1)[0][0] if vol_responses else "neutral"

        synthesized_profile = BehaviorProfile(
            risk_appetite=float(avg_risk_appetite),
            time_horizon=most_common_horizon,
            volatility_response=most_common_vol_response,
            parent_personas=[p.get('name', 'Unknown') for p in parent_personas] # Record parent names
        )
        logger.info(f"Priv: Synthesized hybrid behavior profile: {synthesized_profile.model_dump_json()}.")
        return synthesized_profile


# Example Usage (for testing SyntheticAccountGenerator in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    account_generator = SyntheticAccountGenerator()

    # --- Scenario 1: Create a basic synthetic account ---
    print("\n--- Creating a basic synthetic account ---")
    account1 = account_generator.create_account(initial_equity=50000.0, risk_appetite=0.7, time_horizon="short")
    print(f"Account 1: {account1.model_dump_json(indent=2)}")

    # --- Scenario 2: Simulate PnL and record a trade ---
    print("\n--- Simulating PnL and trade recording ---")
    account1.apply_simulated_pnl(1500.0) # Profit
    account1.record_simulated_trade({"symbol": "EURUSD", "action": "BUY", "volume": 0.5, "pnl": 1500.0})
    
    account1.apply_simulated_pnl(-500.0) # Loss
    account1.record_simulated_trade({"symbol": "EURUSD", "action": "SELL", "volume": 0.2, "pnl": -500.0})
    print(f"Account 1 after trades: Current Equity={account1.current_equity:.2f}, Unrealized PnL={account1.unrealized_pnl:.2f}")

    # --- Scenario 3: Create an account with a specific ID and different profile ---
    print("\n--- Creating another account with specific ID ---")
    account2 = account_generator.create_account(initial_equity=1000000.0, risk_appetite=0.2, volatility_response="defensive", account_id="Institutional_Client_A")
    print(f"Account 2: {account2.model_dump_json(indent=2)}")

    # --- Scenario 4: Simulate multi-agent inheritance for a new persona ---
    print("\n--- Simulating Multi-Agent Inheritance ---")
    # Mock parent personas (e.g., from different PrivAgent instances)
    parent_persona_risk = {"name": "Risk Manager Priv", "risk_appetite": 0.3, "time_horizon": "long", "volatility_response": "defensive"}
    parent_persona_growth = {"name": "Growth Priv", "risk_appetite": 0.8, "time_horizon": "short", "volatility_response": "aggressive"}
    
    hybrid_profile = account_generator.simulate_hybrid_behavior(
        parent_personas=[parent_persona_risk, parent_persona_growth]
    )
    print(f"Synthesized Hybrid Profile: {hybrid_profile.model_dump_json(indent=2)}")

    account3 = account_generator.create_account(initial_equity=250000.0, behavior_profile=hybrid_profile, account_id="Hybrid_Strategist_ACC")
    print(f"Account 3 (Hybrid): {account3.model_dump_json(indent=2)}")

def calculate_lot_size(account: SyntheticAccount, base_lot: float = 1.0) -> float:
    """
    Calculates an appropriate lot size for a synthetic account based on its behavior profile,
    financial state, recent confidence, and market conditions.

    Enhancements:
    - Uses confidence_score from recent trades to adjust aggressiveness
    - Scales based on time_horizon (short-term = higher leverage)
    - Adds randomness for behavioral realism

    Args:
        account (SyntheticAccount): The synthetic account to evaluate.
        base_lot (float): The base lot size to scale from.

    Returns:
        float: The calculated lot size.
    """
    # --- Core behavioral factors ---
    risk_factor = account.behavior_profile.risk_appetite
    margin_factor = account.free_margin / account.initial_equity
    stress_penalty = 1.0 - account.current_market_stress_level

    # --- Confidence adjustment ---
    recent_confidences = [
        trade["details"].get("confidence_score", 0.5)
        for trade in account.simulated_trades[-5:]
        if "confidence_score" in trade["details"]
    ]
    avg_confidence = np.mean(recent_confidences) if recent_confidences else 0.5

    # --- Time horizon leverage scaling ---
    horizon_multiplier = {
        "short": 1.5,
        "medium": 1.0,
        "long": 0.75
    }.get(account.behavior_profile.time_horizon.lower(), 1.0)

    # --- Randomness for realism ---
    noise = random.uniform(0.95, 1.05)

    # --- Final lot calculation ---
    lot_multiplier = risk_factor * margin_factor * stress_penalty * avg_confidence * horizon_multiplier * noise
    calculated_lot = max(0.01, round(base_lot * lot_multiplier, 2))

    logger.debug(
        f"Lot size for '{account.account_id}': {calculated_lot} | "
        f"risk={risk_factor:.2f}, margin={margin_factor:.2f}, stress={account.current_market_stress_level:.2f}, "
        f"confidence={avg_confidence:.2f}, horizon={account.behavior_profile.time_horizon}, noise={noise:.2f}"
    )
    return calculated_lot
