# backend/fundamental_analysis/economic_calendar/defines.py

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- Enums for Standardization ---

class ImpactLevel(str, Enum):
    """
    Defines the potential market impact level of an economic event.
    """
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    HOLIDAY = "Holiday" # For non-trading days
    UNKNOWN = "Unknown" # Default for unclassified events

class EventType(str, Enum):
    """
    Defines common categories for economic events.
    This can be expanded as needed.
    """
    INFLATION = "Inflation"
    EMPLOYMENT = "Employment"
    GDP = "GDP"
    INTEREST_RATES = "Interest Rates"
    MANUFACTURING = "Manufacturing"
    CONSUMER_SPENDING = "Consumer Spending"
    HOUSING = "Housing"
    TRADE = "Trade"
    SENTIMENT = "Sentiment"
    SPEECH = "Speech" # Central bank speeches, etc.
    HOLIDAY = "Holiday"
    OTHER = "Other"

# --- Pydantic Model for Economic Event ---

class EconomicEvent(BaseModel):
    """
    Represents a single economic calendar event.
    """
    id: str = Field(..., description="Unique identifier for the event (e.g., combination of date, time, currency, name).")
    timestamp: datetime = Field(..., description="The precise date and time of the event release (UTC).")
    currency: str = Field(..., description="The currency affected by the event (e.g., 'USD', 'EUR', 'JPY').")
    event_name: str = Field(..., description="The name of the economic event (e.g., 'Non-Farm Payrolls', 'CPI').")
    country: Optional[str] = Field(None, description="The country associated with the event, if applicable.")
    impact: ImpactLevel = Field(..., description="The expected market impact level of the event.")
    actual: Optional[float] = Field(None, description="The actual released value, if available.")
    forecast: Optional[float] = Field(None, description="The forecasted value, if available.")
    previous: Optional[float] = Field(None, description="The previous period's value, if available.")
    revised: Optional[float] = Field(None, description="The revised previous value, if applicable.")
    unit: Optional[str] = Field(None, description="The unit of the value (e.g., '%', 'K', 'B').")
    event_type: EventType = Field(EventType.OTHER, description="Categorization of the event type.")
    description: Optional[str] = Field(None, description="A brief description or additional details about the event.")

    def __hash__(self):
        """
        Enables hashing for use in sets or as dictionary keys, primarily for deduplication.
        """
        return hash((self.timestamp, self.currency, self.event_name))

    def __eq__(self, other):
        """
        Defines equality for deduplication based on core event identifiers.
        """
        if not isinstance(other, EconomicEvent):
            return NotImplemented
        return (self.timestamp == other.timestamp and
                self.currency == other.currency and
                self.event_name == other.event_name)

