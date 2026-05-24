# backend/trading_engine/state_monitor.py

from pydantic import BaseModel # Ensure BaseModel is imported
import random

# --- Pydantic Model for Account State ---
class AccountState(BaseModel):
    """
    Represents the current mock state of a user's trading account.
    """
    equity: float
    free_margin: float
    drawdown: float
    profit_today: float
    is_trading_active: bool = True # Default to active

# --- Mock Account State Data ---
# This function generates a dynamic mock account state for demonstration purposes.
def get_mock_account_state() -> AccountState:
    """
    Generates a mock representation of a user's current account state.
    """
    # Simulate some dynamic changes
    current_equity = round(random.uniform(5000, 10000), 2)
    profit_loss = round(random.uniform(-500, 1000), 2)
    current_free_margin = round(random.uniform(500, current_equity * 0.5), 2)
    current_drawdown = round(random.uniform(0.01, 0.30), 4)

    return AccountState(
        equity=current_equity,
        free_margin=current_free_margin,
        drawdown=current_drawdown,
        profit_today=profit_loss,
        is_trading_active=random.choice([True, False]) # Simulate active/inactive trading
    )