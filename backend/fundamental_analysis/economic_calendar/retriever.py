# backend/fundamental_analysis/economic_calendar/retriever.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Make selenium optional
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    logger = logging.getLogger(__name__)
    logger.warning("Selenium not available. Economic calendar scraping will be disabled.")

# Import our utility functions and data models
from backend.utils.web_scraping_utils import get_chrome_driver_options, clean_scraped_dataframe
from backend.fundamental_analysis.economic_calendar.defines import EconomicEvent, ImpactLevel, EventType

logger = logging.getLogger(__name__)

class EconomicCalendarRetriever:
    """
    Retrieves economic calendar data from a specified web source using Selenium.
    This class is designed to be adaptable to different calendar website structures.
    """
    def __init__(self, calendar_url: str):
        """
        Initializes the retriever with the URL of the economic calendar.

        Args:
            calendar_url (str): The URL of the economic calendar website to scrape.
        """
        self.calendar_url = calendar_url
        self.driver: Optional[webdriver.Chrome] = None

    def _initialize_driver(self):
        """
        Initializes the Selenium WebDriver in headless mode.
        """
        try:
            options = get_chrome_driver_options()
            # Assuming chromedriver is in PATH or specify service_binary_location
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized successfully in headless mode.")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}. Make sure chromedriver is installed and in your PATH.")
            self.driver = None
            raise

    def _close_driver(self):
        """
        Closes the Selenium WebDriver if it's active.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Selenium WebDriver closed.")

    def fetch_calendar_data(self, days_to_fetch: int = 7) -> List[EconomicEvent]:
        """
        Fetches economic calendar data for a specified number of days.

        Args:
            days_to_fetch (int): The number of days into the future/past to attempt to fetch data for.
                                 (Note: Actual coverage depends on the website's available data).

        Returns:
            List[EconomicEvent]: A list of parsed EconomicEvent objects.
        """
        if not self.driver:
            try:
                self._initialize_driver()
            except WebDriverException:
                return [] # Return empty list if driver fails to initialize

        if not self.driver: # Double check if driver initialization failed
            return []

        all_events: List[EconomicEvent] = []
        try:
            logger.info(f"Navigating to {self.calendar_url} to fetch economic calendar data.")
            self.driver.get(self.calendar_url)

            # Wait for the main calendar table/elements to be present
            # You will need to adjust this XPath/CSS selector based on the actual website.
            # This is a generic placeholder.
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'economic-calendar-table')]"))
            )
            logger.info("Economic calendar table element found.")

            # --- Simulate fetching data for multiple days/pages if necessary ---
            # For a real implementation, you might need to click "next day/week" buttons
            # or adjust URL parameters to get data for the desired range.
            # This example assumes all relevant data is on the initial page or can be scrolled.

            # Example: Find all rows in the table. Adjust selector as needed.
            # This selector assumes a table with rows that contain event data.
            rows = self.driver.find_elements(By.XPATH, "//table[contains(@class, 'economic-calendar-table')]/tbody/tr")
            if not rows:
                logger.warning("No rows found in the economic calendar table. Check XPath/CSS selector.")
                return []

            raw_data = []
            for row in rows:
                # Extract cell data. Adjust cell selectors based on actual website structure.
                # Common columns: Time, Currency, Event, Actual, Forecast, Previous, Importance
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 7: # Assuming at least 7 columns for basic event data
                    try:
                        time_str = cells[0].text.strip()
                        currency = cells[1].text.strip()
                        event_name = cells[2].text.strip()
                        impact_str = cells[3].find_element(By.TAG_NAME, "span").get_attribute("title").strip() # Example for impact
                        actual_str = cells[4].text.strip()
                        forecast_str = cells[5].text.strip()
                        previous_str = cells[6].text.strip()

                        # For demonstration, assume current date for events without a date column
                        # In a real scenario, date would be extracted from a header or a dedicated cell
                        event_date = datetime.now().date() # Placeholder: Assume current date for simplicity
                        
                        # Combine date and time
                        try:
                            # This is a very basic time parsing. Real calendars might have different formats.
                            event_datetime = datetime.combine(event_date, datetime.strptime(time_str, "%H:%M").time())
                        except ValueError:
                            logger.warning(f"Could not parse time '{time_str}'. Skipping row.")
                            continue

                        raw_data.append({
                            "Date": event_datetime.strftime("%Y-%m-%d %H:%M:%S"), # Formatted for clean_scraped_dataframe
                            "Time": time_str,
                            "Currency": currency,
                            "Event": event_name,
                            "Impact": impact_str,
                            "Actual": actual_str,
                            "Forecast": forecast_str,
                            "Previous": previous_str
                            # Add other fields as needed
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing row: {row.text}. Error: {e}")
                        continue

            if not raw_data:
                logger.warning("No raw data extracted from the calendar table.")
                return []

            # Convert to DataFrame and clean using our utility
            df = pd.DataFrame(raw_data)
            # clean_scraped_dataframe expects 'Date' as index, so we need to ensure it's handled.
            # For economic calendar, 'Date' column is better than index for event uniqueness.
            # We'll manually parse to EconomicEvent instead of relying solely on clean_scraped_dataframe for this specific use case.

            for _, row in df.iterrows():
                try:
                    # Map scraped strings to EconomicEvent fields
                    timestamp_dt = datetime.strptime(row["Date"], "%Y-%m-%d %H:%M:%S")

                    impact_level = ImpactLevel.UNKNOWN
                    if "high" in row["Impact"].lower():
                        impact_level = ImpactLevel.HIGH
                    elif "medium" in row["Impact"].lower():
                        impact_level = ImpactLevel.MEDIUM
                    elif "low" in row["Impact"].lower():
                        impact_level = ImpactLevel.LOW

                    # Basic event type classification (can be improved with regex/keywords)
                    event_type = EventType.OTHER
                    if "cpi" in row["Event"].lower() or "inflation" in row["Event"].lower():
                        event_type = EventType.INFLATION
                    elif "employment" in row["Event"].lower() or "payrolls" in row["Event"].lower():
                        event_type = EventType.EMPLOYMENT
                    elif "gdp" in row["Event"].lower():
                        event_type = EventType.GDP
                    elif "interest rate" in row["Event"].lower() or "fomc" in row["Event"].lower():
                        event_type = EventType.INTEREST_RATES

                    event_id = f"{timestamp_dt.isoformat()}-{row['Currency']}-{row['Event']}"

                    event = EconomicEvent(
                        id=event_id,
                        timestamp=timestamp_dt,
                        currency=row["Currency"],
                        event_name=row["Event"],
                        impact=impact_level,
                        actual=pd.to_numeric(row["Actual"], errors='coerce'),
                        forecast=pd.to_numeric(row["Forecast"], errors='coerce'),
                        previous=pd.to_numeric(row["Previous"], errors='coerce'),
                        event_type=event_type,
                        # country=... (if extracted)
                        # unit=... (if extracted)
                    )
                    all_events.append(event)
                except Exception as e:
                    logger.error(f"Failed to parse event row {row.to_dict()}: {e}")
                    continue

        except TimeoutException:
            logger.error(f"Timeout while waiting for elements on {self.calendar_url}. Page structure might have changed or network is slow.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during calendar data fetching: {e}", exc_info=True)
        finally:
            self._close_driver() # Ensure driver is closed even if errors occur

        logger.info(f"Successfully fetched {len(all_events)} economic events.")
        return all_events

# Example Usage (for testing purposes, not part of the main application flow)
if __name__ == "__main__":
    # IMPORTANT: Replace with a real economic calendar URL for actual testing.
    # This URL is a placeholder and might not work or might have a different structure.
    # A common source is Investing.com or DailyFX.
    # For example: "https://www.investing.com/economic-calendar/"
    # or "https://www.dailyfx.com/economic-calendar"
    
    # Using a placeholder URL for now.
    # For DailyFX, you might need to handle dynamic loading more carefully.
    # A simpler approach for initial testing might be a static HTML file if available.
    MOCK_CALENDAR_URL = "https://www.dailyfx.com/economic-calendar" # This URL might require more advanced scraping techniques

    retriever = EconomicCalendarRetriever(calendar_url=MOCK_CALENDAR_URL)
    try:
        events = retriever.fetch_calendar_data(days_to_fetch=1)
        if events:
            print(f"\n--- Fetched {len(events)} Economic Events ---")
            for event in events[:5]: # Print first 5 events
                print(f"ID: {event.id}")
                print(f"  Time: {event.timestamp.isoformat()}")
                print(f"  Currency: {event.currency}")
                print(f"  Event: {event.event_name}")
                print(f"  Impact: {event.impact.value}")
                print(f"  Actual: {event.actual}")
                print(f"  Forecast: {event.forecast}")
                print(f"  Previous: {event.previous}")
                print("-" * 20)
        else:
            print("No economic events fetched.")
    except Exception as e:
        print(f"An error occurred during fetching: {e}")

