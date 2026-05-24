from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field # Import Pydantic for data modeling

# Define a Pydantic model for a trading position.
# This ensures a consistent and validated data structure across your application.
class MockPosition(BaseModel):
    """
    Represents a mock trading position with common attributes.
    This model aligns with the 'Position' model defined in risk_engine.py.
    """
    symbol: str = Field(..., description="The trading instrument symbol (e.g., 'XAU/USD').")
    volume: float = Field(..., gt=0, description="The size of the trade.")
    entry_price: float = Field(..., gt=0, description="The price at which the position was opened.")
    current_price: float = Field(..., gt=0, description="The current market price of the instrument.")
    open_time: str = Field(..., description="The ISO format datetime string when the position was opened.")
    stop_loss: Optional[float] = Field(None, description="The stop-loss price, if set.")
    take_profit: Optional[float] = Field(None, description="The take-profit price, if set.")
    holding_reason: str = Field(..., description="A brief reason for holding the trade.")
    # Add an optional unique ID for frontend keying (e.g., 'id: str = Field(None)') if applicable

def get_mock_positions() -> List[MockPosition]:
    """
    Generates a list of mock trading positions.
    In a real trading application, this would fetch live positions from an API.

    Returns:
        List[MockPosition]: A list of Pydantic MockPosition models.
    """
    now = datetime.now()
    positions_data = [
        {
            "symbol": "XAU/USD",
            "volume": 1.2,
            "entry_price": 1924.50,
            "current_price": 1931.70,
            "open_time": (now - timedelta(hours=7)).isoformat(),
            "stop_loss": 1910.00,
            "take_profit": 1950.00,
            "holding_reason": "Gold breakout attempt"
        },
        {
            "symbol": "ETH/USD",
            "volume": 2.0,
            "entry_price": 3200.00,
            "current_price": 3120.00,
            "open_time": (now - timedelta(hours=2)).isoformat(),
            "stop_loss": None,
            "take_profit": None,
            "holding_reason": "FOMO after breakout"
        },
        {
            "symbol": "USD/JPY",
            "volume": 0.8,
            "entry_price": 148.20,
            "current_price": 148.45,
            "open_time": (now - timedelta(minutes=45)).isoformat(),
            "stop_loss": 147.90,
            "take_profit": 148.60,
            "holding_reason": "JPY weakness continuation"
        }
    ]
    
    # Validate and convert dictionary data to Pydantic models
    return [MockPosition(**data) for data in positions_data]