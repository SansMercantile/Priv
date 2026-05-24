# backend/data_sourcing/financial_automation_sourcing.py

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date
import aiohttp

from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.utils.async_utils import async_retry_api_call # Reuse retry helper

logger = logging.getLogger(__name__)

class FinancialAutomationSourcingClient:
    """
    A dedicated client for sourcing data relevant to financial automation agents,
    such as corporate actions, financials, and other company-specific events.
    This implementation uses Polygon.io.
    """
    def __init__(self, api_key: Optional[str] = None):
        if not api_key or "YOUR" in api_key:
            logger.warning("Polygon.io API key not configured. FinancialAutomationSourcingClient will use fallback/mock data.")
            self.api_key = None
            self.base_url = None
        else:
            self.api_key = api_key
            self.base_url = "https://api.polygon.io"
            logger.info("FinancialAutomationSourcingClient (Polygon.io) initialized.")

    async def get_dividends(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches historical dividend data for a stock ticker.
        """
        if not self.api_key or not self.base_url:
            logger.warning(f"Polygon.io API not configured. Cannot fetch dividends for {ticker}. Returning empty list.")
            return []
            
        url = f"{self.base_url}/v3/reference/dividends"
        params = {"ticker": ticker.upper(), "apiKey": self.api_key, "limit": 100} # Get last 100 dividends
        
        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                data = await response.json()
                if response.status == 200 and data.get("results"):
                    logger.info(f"Successfully fetched {len(data['results'])} dividend records for {ticker}.")
                    return data["results"]
                else:
                    logger.warning(f"Could not fetch dividends for {ticker}. Status: {response.status}, Response: {data}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching dividends for {ticker}: {e}", exc_info=True)
            return None
            
    async def get_stock_splits(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches historical stock split data for a stock ticker.
        """
        if not self.api_key or not self.base_url:
            logger.warning(f"Polygon.io API not configured. Cannot fetch stock splits for {ticker}. Returning empty list.")
            return []
            
        url = f"{self.base_url}/v3/reference/splits"
        params = {"ticker": ticker.upper(), "apiKey": self.api_key, "limit": 100}
        
        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                data = await response.json()
                if response.status == 200 and data.get("results"):
                    logger.info(f"Successfully fetched {len(data['results'])} split records for {ticker}.")
                    return data["results"]
                else:
                    logger.warning(f"Could not fetch splits for {ticker}. Status: {response.status}, Response: {data}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching splits for {ticker}: {e}", exc_info=True)
            return None

    async def get_financials(self, ticker: str, timeframe: str = "annual") -> Optional[List[Dict[str, Any]]]:
        """
        Fetches financial statements (income, balance sheet, cash flow) for a ticker.
        Note: This is a premium Polygon.io endpoint.
        """
        if not self.api_key or not self.base_url:
            logger.warning(f"Polygon.io API not configured. Cannot fetch financials for {ticker}. Returning empty list.")
            return []
            
        url = f"{self.base_url}/vX/reference/financials" # vX is a placeholder for the correct version
        params = {
            "ticker": ticker.upper(), 
            "apiKey": self.api_key, 
            "timeframe": timeframe,
            "limit": 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                data = await response.json()
                if response.status == 200 and data.get("results"):
                    logger.info(f"Successfully fetched {len(data['results'])} financial records for {ticker}.")
                    return data["results"]
                else:
                    logger.warning(f"Could not fetch financials for {ticker}. This is likely a premium endpoint. Status: {response.status}, Response: {data}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching financials for {ticker}: {e}", exc_info=True)
            return None

# Example Usage
async def main():
    logging.basicConfig(level=logging.INFO)
    if not _settings.POLYGON_API_KEY or "YOUR" in _settings.POLYGON_API_KEY:
        logger.error("POLYGON_API_KEY is not configured in your .env file. Cannot run test.")
        return
        
    client = FinancialAutomationSourcingClient(api_key=_settings.POLYGON_API_KEY)
    
    ticker = "AAPL"
    print(f"\n--- Fetching data for {ticker} ---")
    
    dividends = await client.get_dividends(ticker)
    if dividends:
        print(f"Found {len(dividends)} dividend records. Most recent: {dividends[0] if dividends else 'N/A'}")
        
    splits = await client.get_stock_splits(ticker)
    if splits:
        print(f"Found {len(splits)} split records. Most recent: {splits[0] if splits else 'N/A'}")

    # Note: This call will likely fail without a premium Polygon subscription
    financials = await client.get_financials(ticker)
    if financials:
        print(f"Found {len(financials)} financial records.")

if __name__ == "__main__":
    asyncio.run(main())
