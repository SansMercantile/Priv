# backend/fundamental_analysis/economic_calendar/manager.py

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import json
import os

# Import our data models and retriever
from backend.fundamental_analysis.economic_calendar.defines import EconomicEvent, ImpactLevel, EventType
from backend.fundamental_analysis.economic_calendar.retriever import EconomicCalendarRetriever

logger = logging.getLogger(__name__)

# --- Configuration Constants for Manager ---
# These can be externalized to a config file if needed
CALENDAR_CACHE_FILE = "logs/economic_calendar_cache.json"
CACHE_EXPIRATION_HOURS = 24 # How often to refresh the cache by re-fetching data

class EconomicCalendarManager:
    """
    Manages fetching, caching, filtering, and providing access to economic calendar events.
    Leverages a retriever for data acquisition and an in-memory cache for performance.
    """
    def __init__(self, calendar_url: str):
        """
        Initializes the EconomicCalendarManager.

        Args:
            calendar_url (str): The URL for the EconomicCalendarRetriever.
        """
        self.retriever = EconomicCalendarRetriever(calendar_url=calendar_url)
        self.events_cache: Set[EconomicEvent] = set() # Using a set for automatic deduplication
        self.last_cache_update: Optional[datetime] = None
        self._load_cache_from_file() # Attempt to load cache on startup

    async def initialize(self) -> bool:
        """Initialize the economic calendar manager (asynchronous compatibility wrapper)."""
        logger.info("Initializing EconomicCalendarManager...")
        return True

    async def get_relevant_events(self, symbol: str) -> List[Any]:
        """
        Retrieves relevant economic events for a given symbol (asynchronous compatibility wrapper).
        """
        currency = "USD"
        symbol_upper = symbol.upper()
        if "EUR" in symbol_upper:
            currency = "EUR"
        elif "GBP" in symbol_upper:
            currency = "GBP"
        elif "JPY" in symbol_upper:
            currency = "JPY"
            
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=7)
        
        try:
            events = self.get_events(start_time=start, end_time=end, currencies=[currency], refresh_if_stale=False)
            return events
        except Exception as e:
            logger.warning(f"Failed to get events for {symbol}: {e}")
            return []

    def _load_cache_from_file(self):
        """
        Loads cached economic events from a JSON file.
        """
        if os.path.exists(CALENDAR_CACHE_FILE):
            try:
                with open(CALENDAR_CACHE_FILE, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    for item in raw_data:
                        try:
                            # Reconstruct datetime objects
                            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                            # Reconstruct Enum types
                            item['impact'] = ImpactLevel(item['impact'])
                            item['event_type'] = EventType(item['event_type'])
                            self.events_cache.add(EconomicEvent(**item))
                        except Exception as e:
                            logger.warning(f"Skipping malformed event in cache file: {item}. Error: {e}")
                logger.info(f"Loaded {len(self.events_cache)} events from cache file.")
                # Assume the file's modification time or a stored timestamp for last update
                self.last_cache_update = datetime.fromtimestamp(os.path.getmtime(CALENDAR_CACHE_FILE))
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading economic calendar cache from {CALENDAR_CACHE_FILE}: {e}")
                self.events_cache.clear() # Clear potentially corrupted cache
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading cache: {e}", exc_info=True)
        else:
            logger.info("No existing economic calendar cache file found.")

    def _save_cache_to_file(self):
        """
        Saves the current in-memory cache of economic events to a JSON file.
        """
        os.makedirs(os.path.dirname(CALENDAR_CACHE_FILE), exist_ok=True)
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_events = [event.model_dump_json() for event in self.events_cache]
            # model_dump_json returns a JSON string, so we need to load it back to dict
            # or use model_dump() and handle datetime/enum serialization manually.
            # Let's use model_dump() and custom serialization for better control.
            
            list_of_dicts = []
            for event in self.events_cache:
                event_dict = event.model_dump()
                event_dict['timestamp'] = event_dict['timestamp'].isoformat()
                event_dict['impact'] = event_dict['impact'].value # Convert Enum to string
                event_dict['event_type'] = event_dict['event_type'].value # Convert Enum to string
                list_of_dicts.append(event_dict)

            with open(CALENDAR_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(list_of_dicts, f, indent=2)
            self.last_cache_update = datetime.now()
            logger.info(f"Saved {len(self.events_cache)} events to cache file.")
        except IOError as e:
            logger.error(f"Error saving economic calendar cache to {CALENDAR_CACHE_FILE}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving cache: {e}", exc_info=True)

    def _should_refresh_cache(self) -> bool:
        """
        Checks if the cache needs to be refreshed based on expiration time.
        """
        if not self.events_cache or self.last_cache_update is None:
            return True # Cache is empty or never updated
        
        time_since_last_update = datetime.now() - self.last_cache_update
        return time_since_last_update > timedelta(hours=CACHE_EXPIRATION_HOURS)

    def refresh_cache(self, force: bool = False, days_to_fetch: int = 7):
        """
        Refreshes the economic calendar cache by fetching new data.

        Args:
            force (bool): If True, forces a refresh even if cache is not expired.
            days_to_fetch (int): Number of days to fetch from the retriever.
        """
        if not force and not self._should_refresh_cache():
            logger.info("Cache is still fresh, skipping refresh.")
            return

        logger.info("Refreshing economic calendar cache...")
        new_events = self.retriever.fetch_calendar_data(days_to_fetch=days_to_fetch)
        
        if new_events:
            # Add new events to the cache, leveraging set's deduplication
            initial_count = len(self.events_cache)
            for event in new_events:
                self.events_cache.add(event)
            logger.info(f"Added {len(self.events_cache) - initial_count} new events to cache. Total: {len(self.events_cache)}")
            self._save_cache_to_file()
        else:
            logger.warning("No new events fetched during cache refresh.")

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        impact_levels: Optional[List[ImpactLevel]] = None,
        currencies: Optional[List[str]] = None,
        event_types: Optional[List[EventType]] = None,
        refresh_if_stale: bool = True
    ) -> List[EconomicEvent]:
        """
        Retrieves economic events from the cache, applying filters.
        Refreshes the cache if it's stale and refresh_if_stale is True.

        Args:
            start_time (Optional[datetime]): Only return events after this time.
            end_time (Optional[datetime]): Only return events before this time.
            impact_levels (Optional[List[ImpactLevel]]): Filter by impact level.
            currencies (Optional[List[str]]): Filter by currency.
            event_types (Optional[List[EventType]]): Filter by event type.
            refresh_if_stale (bool): If True, refresh cache if it's expired.

        Returns:
            List[EconomicEvent]: A list of filtered economic events, sorted by timestamp.
        """
        if refresh_if_stale:
            self.refresh_cache() # Refresh if stale, or if empty

        filtered_events: List[EconomicEvent] = []
        for event in self.events_cache:
            # Apply time filters
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            # Apply impact level filter
            if impact_levels and event.impact not in impact_levels:
                continue

            # Apply currency filter (case-insensitive comparison)
            if currencies and event.currency.upper() not in [c.upper() for c in currencies]:
                continue

            # Apply event type filter
            if event_types and event.event_type not in event_types:
                continue

            filtered_events.append(event)

        # Sort events by timestamp
        return sorted(filtered_events, key=lambda e: e.timestamp)

# Example Usage (for testing purposes, not part of the main application flow)
if __name__ == "__main__":
    # IMPORTANT: Use a real URL for actual data fetching.
    # For testing, you might want to mock the retriever or use a known working URL.
    TEST_CALENDAR_URL = "https://www.dailyfx.com/economic-calendar" # Placeholder

    manager = EconomicCalendarManager(calendar_url=TEST_CALENDAR_URL)

    print("\n--- Initial Load & Refresh ---")
    # This will trigger a refresh if the cache is empty or stale
    high_impact_events_today = manager.get_events(
        start_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        end_time=datetime.now() + timedelta(days=1),
        impact_levels=[ImpactLevel.HIGH, ImpactLevel.MEDIUM],
        currencies=["USD", "EUR"]
    )

    if high_impact_events_today:
        print(f"\n--- Fetched and Filtered {len(high_impact_events_today)} High/Medium Impact Events (USD/EUR) ---")
        for event in high_impact_events_today[:5]: # Print first 5
            print(f"  [{event.timestamp.strftime('%Y-%m-%d %H:%M')}] {event.currency} - {event.event_name} ({event.impact.value})")
            print(f"    Actual: {event.actual}, Forecast: {event.forecast}, Previous: {event.previous}")
        print("-" * 30)
    else:
        print("\nNo high/medium impact USD/EUR events found for today/tomorrow after refresh.")

    print("\n--- Fetching again (should use cache if not forced refresh) ---")
    # This call should be faster as it uses the cache unless forced
    all_events_cached = manager.get_events(refresh_if_stale=False)
    print(f"Total events in cache: {len(all_events_cached)}")

    # Simulate a forced refresh
    print("\n--- Forcing a cache refresh ---")
    manager.refresh_cache(force=True, days_to_fetch=1)
    
    print("\n--- Retrieving all events after forced refresh ---")
    all_events_after_force = manager.get_events(refresh_if_stale=False)
    print(f"Total events in cache after forced refresh: {len(all_events_after_force)}")

