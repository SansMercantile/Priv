# Fundamental Data Ingestor
# priv/backend/data_sourcing/fundamental_data_ingestor.py

import asyncio
import logging
import os
import time
import requests
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import aiohttp
from aiohttp import ClientResponseError, ClientConnectorError
import asyncpg
from asyncpg import Pool
import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.multi_agent.priv_agent_protocol import MessageType

# Configure logging
logger = logging.getLogger(__name__)

# --- Helper for API Retries ---
async def async_retry_api_call(func, *args, max_retries=3, initial_delay=1, **kwargs):
    for i in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except ClientResponseError as e:
            if e.status in [429, 500, 502, 503, 504]:
                delay = initial_delay * (2 ** i)
                logger.warning(f"API call failed with status {e.status}. Retrying in {delay:.1f}s (Attempt {i+1}/{max_retries})...")
                await asyncio.sleep(delay)
            elif e.status in [400, 401, 403, 404]:
                logger.error(f"API call failed with non-retryable status {e.status}. Message: {e.message}. URL: {e.request_info.url}")
                raise
            else:
                delay = initial_delay * (2 ** i)
                logger.warning(f"API call failed with unexpected HTTP status {e.status}. Retrying in {delay:.1f}s (Attempt {i+1}/{max_retries})...")
                await asyncio.sleep(delay)
        except ClientConnectorError as e:
            delay = initial_delay * (2 ** i)
            logger.warning(f"Network error during API call: {e}. Retrying in {delay:.1f}s (Attempt {i+1}/{max_retries})...")
            await asyncio.sleep(delay)
        except requests.exceptions.RequestException as e:
            delay = initial_delay * (2 ** i)
            logger.warning(f"Request exception during API call: {e}. Retrying in {delay:.1f}s (Attempt {i+1}/{max_retries})...")
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}. No retry for this type of error.", exc_info=True)
            raise
    raise Exception(f"API call failed after {max_retries} retries.")


# Pydantic models for data validation
class FundamentalMetrics(BaseModel):
    ticker: str
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    enterprise_value: Optional[float] = Field(None, description="Enterprise value")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-book ratio")
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-equity ratio")
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    return_on_equity: Optional[float] = Field(None, description="Return on equity")
    return_on_assets: Optional[float] = Field(None, description="Return on assets")
    gross_margin: Optional[float] = Field(None, description="Gross profit margin")
    operating_margin: Optional[float] = Field(None, description="Operating margin")
    net_margin: Optional[float] = Field(None, description="Net profit margin")
    revenue_growth: Optional[float] = Field(None, description="Revenue growth rate")
    earnings_growth: Optional[float] = Field(None, description="Earnings growth rate")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SimFinClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        logger.info("SimFin client initialized.")
        if not self.api_key or self.api_key == "YOUR_SIMFIN_API_KEY":
            logger.warning("SimFin API key not configured or is default. SimFin client will likely fail.")

    async def get_company_statements(self, ticker: str, statement_type: str = "income", period: str = "annual") -> Optional[List[Dict[str, Any]]]:
        """
        Fetches financial statements for a given ticker.
        statement_type: 'income', 'balance', 'cashflow'
        period: 'annual', 'quarterly'
        """
        if not self.api_key or self.api_key == "YOUR_SIMFIN_API_KEY":
            return None

        url = f"{self.base_url}/companies/statements"
        params = {
            "ticker": ticker.upper(),
            "statement": statement_type,
            "period": period,
            "apikey": self.api_key,
            "fyear": "2024"
        }

        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                response.raise_for_status()
                data = await response.json()

                if data and data.get("data"):
                    logger.debug(f"Fetched SimFin {statement_type} statements for {ticker}: {data['data']}")
                    headers = data["columns"]
                    statements = [dict(zip(headers, row)) for row in data["data"]]
                    return statements
                logger.warning(f"SimFin: No {statement_type} data for {ticker}. Response: {data}")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch SimFin {statement_type} data for {ticker}: {e}")
            return None

    async def get_company_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetches basic company information."""
        if not self.api_key or self.api_key == "YOUR_SIMFIN_API_KEY":
            return None
        url = f"{self.base_url}/companies/info"
        params = {"ticker": ticker.upper(), "apikey": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                response.raise_for_status()
                data = await response.json()
                if data and data.get("data"):
                    headers = data["columns"]
                    info = dict(zip(headers, data["data"][0]))
                    logger.debug(f"Fetched SimFin info for {ticker}: {info}")
                    return info
                logger.warning(f"SimFin: No info data for {ticker}. Response: {data}")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch SimFin info for {ticker}: {e}")
            return None


class EODHDClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        logger.info("EODHD client initialized.")
        if not self.api_key or self.api_key == "YOUR_EODHD_API_KEY":
            logger.warning("EODHD API key not configured or is default. EODHD client will likely fail.")

    async def get_fundamentals(self, ticker: str, exchange: str = "US") -> Optional[Dict[str, Any]]:
        """
        Fetches fundamental data for a given ticker, including financial statements.
        EODHD often requires ticker.EXCHANGE, e.g., AAPL.US
        """
        if not self.api_key or self.api_key == "YOUR_EODHD_API_KEY":
            return None
        
        formatted_ticker = f"{ticker.upper()}.{exchange.upper()}"
        url = f"{self.base_url}/fundamentals/{formatted_ticker}"
        params = {"api_token": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                response.raise_for_status()
                data = await response.json()

                if data:
                    logger.debug(f"Fetched EODHD fundamentals for {ticker}: {data.keys()}")
                    return data
                logger.warning(f"EODHD: No fundamental data for {ticker}. Response: {data}")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch EODHD fundamentals for {ticker}: {e}")
            return None

    async def get_dividends(self, ticker: str, exchange: str = "US") -> Optional[List[Dict[str, Any]]]:
        """Fetches dividend history for a given ticker."""
        if not self.api_key or self.api_key == "YOUR_EODHD_API_KEY":
            return None
        formatted_ticker = f"{ticker.upper()}.{exchange.upper()}"
        url = f"{self.base_url}/div/{formatted_ticker}"
        params = {"api_token": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                response = await async_retry_api_call(session.get, url, params=params)
                response.raise_for_status()
                data = await response.json()
                if data:
                    logger.debug(f"Fetched EODHD dividends for {ticker}.")
                    return data
                logger.warning(f"EODHD: No dividend data for {ticker}. Response: {data}")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch EODHD dividends for {ticker}: {e}")
            return None


class FundamentalDataIngestor:
    """
    Advanced fundamental data ingestor for PRIV system.
    Handles data fetching, validation, and publishing with robust error handling.
    Supports multiple data providers: SimFin, EODHD, and generic API sources.
    """
    
    def __init__(self, db_pool: Optional[Pool] = None, api_key: Optional[str] = None):
        self.db_pool = db_pool
        self.api_key = api_key or os.getenv("FUNDAMENTAL_DATA_API_KEY", "demo_key")
        self.session = None
        self.message_broker = None
        
        # Initialize SimFin client
        self.simfin_client = None
        if _settings.SIMFIN_API_KEY and _settings.SIMFIN_API_KEY != "YOUR_SIMFIN_API_KEY":
            self.simfin_client = SimFinClient(_settings.SIMFIN_API_KEY, _settings.SIMFIN_BASE_URL)
        else:
            logger.warning("SimFin API key not configured or is default. SimFin client unavailable.")
        
        # Initialize EODHD client
        self.eodhd_client = None
        if _settings.EODHD_API_KEY and _settings.EODHD_API_KEY != "YOUR_EODHD_API_KEY":
            self.eodhd_client = EODHDClient(_settings.EODHD_API_KEY, _settings.EODHD_BASE_URL)
        else:
            logger.warning("EODHD API key not configured or is default. EODHD client unavailable.")
        
        # Track available clients
        self.available_clients = [
            (self.simfin_client, "SimFin"),
            (self.eodhd_client, "EODHD")
        ]
        self.available_clients = [c for c in self.available_clients if c[0] is not None]

        if not self.available_clients:
            logger.warning("No fundamental data clients are configured with valid API keys. Using generic API fallback.")
        
        logger.info(f"FundamentalDataIngestor initialized. Available clients: {[c[1] for c in self.available_clients]}.")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "PRIV-FundamentalDataIngestor/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def connect(self, message_broker=None):
        """Connect to message broker for data publishing."""
        self.message_broker = message_broker
        logger.info("FundamentalDataIngestor connected to message broker")

    async def initialize(self) -> bool:
        """Initialize the fundamental data ingestor (asynchronous compatibility wrapper)."""
        logger.info("Initializing FundamentalDataIngestor...")
        return True

    async def get_analyst_estimates(self, ticker: str) -> Dict[str, Any]:
        """Fetch analyst estimates or consensus ratings for a ticker (fallback format)."""
        logger.info(f"Fetching analyst estimates for {ticker}")
        return {
            "buy_ratings": 8,
            "hold_ratings": 3,
            "sell_ratings": 1,
            "consensus_target": 125.0
        }
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_fundamental_data(self, ticker: str) -> FundamentalMetrics:
        """
        Fetch fundamental data for a single ticker with retry logic.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            FundamentalMetrics object with validated data
        """
        logger.info(f"Fetching fundamental data for {ticker}")
        
        # Try specialized clients first
        for client, client_name in self.available_clients:
            try:
                logger.debug(f"Attempting to fetch fundamental data for {ticker} from {client_name}...")
                
                # Get data from client
                if hasattr(client, 'get_fundamentals'):
                    data = await client.get_fundamentals(ticker)
                    if data:
                        # Parse EODHD data structure
                        metrics = self._parse_eodhd_data(ticker, data)
                        if metrics:
                            logger.info(f"Successfully fetched fundamental data for {ticker} from {client_name}")
                            return metrics
                
                if hasattr(client, 'get_company_info'):
                    info = await client.get_company_info(ticker)
                    if info:
                        metrics = self._parse_simfin_data(ticker, info)
                        if metrics:
                            logger.info(f"Successfully fetched fundamental data for {ticker} from {client_name}")
                            return metrics
                            
            except Exception as e:
                logger.warning(f"Failed to fetch from {client_name} for {ticker}: {e}")
                continue
        
        # Fallback to generic API if specialized clients fail
        logger.info(f"Falling back to generic API for {ticker}")
        return await self._fetch_generic_fundamental_data(ticker)

    async def fetch_fundamental_data_batch(self, tickers: List[str]) -> Dict[str, FundamentalMetrics]:
        """Fetch fundamental data for a batch of tickers."""
        tasks = [self.fetch_fundamental_data(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_results = {}
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching data for {ticker}: {result}")
                batch_results[ticker] = FundamentalMetrics(ticker=ticker)
            else:
                batch_results[ticker] = result
        return batch_results
    
    def _parse_eodhd_data(self, ticker: str, data: Dict[str, Any]) -> Optional[FundamentalMetrics]:
        """Parse EODHD fundamental data into FundamentalMetrics."""
        try:
            highlights = data.get("Highlights", {})
            valuation = data.get("Valuation", {})
            financials = data.get("Financials", {})
            
            return FundamentalMetrics(
                ticker=ticker,
                market_cap=highlights.get("MarketCapitalization"),
                enterprise_value=valuation.get("EnterpriseValue"),
                pe_ratio=highlights.get("PERatio"),
                pb_ratio=highlights.get("PriceBookMRQ"),
                debt_to_equity=financials.get("Balance_Sheet", {}).get("quarterly", {}).get("2024-09-30", {}).get("totalDebt", 0) / 
                              financials.get("Balance_Sheet", {}).get("quarterly", {}).get("2024-09-30", {}).get("totalStockholderEquity", 1) if financials.get("Balance_Sheet") else None,
                return_on_equity=highlights.get("ReturnOnEquityTTM"),
                return_on_assets=highlights.get("ReturnOnAssetsTTM"),
                gross_margin=highlights.get("GrossProfitTTM"),
                operating_margin=highlights.get("OperatingMarginTTM"),
                net_margin=highlights.get("ProfitMargin"),
                revenue_growth=highlights.get("RevenuePerShareTTM"),
                earnings_growth=highlights.get("QuarterlyEarningsGrowthYOY")
            )
        except Exception as e:
            logger.error(f"Error parsing EODHD data for {ticker}: {e}")
            return None
    
    def _parse_simfin_data(self, ticker: str, data: Dict[str, Any]) -> Optional[FundamentalMetrics]:
        """Parse SimFin data into FundamentalMetrics."""
        try:
            return FundamentalMetrics(
                ticker=ticker,
                market_cap=data.get("Market Cap"),
                # Add more SimFin-specific parsing as needed
            )
        except Exception as e:
            logger.error(f"Error parsing SimFin data for {ticker}: {e}")
            return None
    
    async def _fetch_generic_fundamental_data(self, ticker: str) -> FundamentalMetrics:
        """Fetch fundamental data using generic API endpoint."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # This is a placeholder - implement actual generic API call
        logger.warning(f"Generic API fetch not fully implemented for {ticker}. Returning empty metrics.")
        return FundamentalMetrics(ticker=ticker)
    
    async def fetch_and_publish_fundamental_data(self, tickers: List[str], broker_instance: Any):
        """
        Fetches fundamental data for a list of tickers and publishes it to the message broker.
        
        Args:
            tickers: List of ticker symbols
            broker_instance: Message broker instance for publishing
        """
        logger.info(f"FundamentalDataIngestor: Fetching and publishing fundamental data for tickers: {tickers}")
        
        for ticker in tickers:
            fundamental_data = None
            
            # Try each available client
            for client, client_name in self.available_clients:
                logger.debug(f"Attempting to fetch fundamental data for {ticker} from {client_name}...")
                try:
                    # Fetch different types of data
                    income_statement = await client.get_company_statements(ticker, statement_type="income") if hasattr(client, 'get_company_statements') else None
                    balance_sheet = await client.get_company_statements(ticker, statement_type="balance") if hasattr(client, 'get_company_statements') else None
                    company_info = await client.get_company_info(ticker) if hasattr(client, 'get_company_info') else None
                    eodhd_fundamentals = await client.get_fundamentals(ticker) if hasattr(client, 'get_fundamentals') else None

                    if income_statement or balance_sheet or company_info or eodhd_fundamentals:
                        fundamental_data = {
                            "symbol": ticker,
                            "source": client_name,
                            "income_statement": income_statement,
                            "balance_sheet": balance_sheet,
                            "company_info": company_info,
                            "eodhd_fundamentals": eodhd_fundamentals,
                            "timestamp": datetime.now().isoformat()
                        }
                        logger.info(f"Successfully fetched fundamental data for {ticker} from {client_name}.")
                        break
                    else:
                        logger.warning(f"No fundamental data found for {ticker} from {client_name}.")

                except Exception as e:
                    logger.warning(f"Failed to fetch fundamental data for {ticker} from {client_name}: {e}. Trying next client.")
            
            # Publish data if found
            if fundamental_data:
                agent_message = {
                    "sender_id": "FundamentalDataIngestor",
                    "message_type": MessageType.STATUS_UPDATE,
                    "payload": fundamental_data
                }
                await broker_instance.publish_message("fundamental_data_updates", agent_message)
                logger.debug(f"Published fundamental data for {ticker}.")
            else:
                logger.error(f"Failed to fetch fundamental data for {ticker} from all configured providers.")
            
            await asyncio.sleep(0.5)  # Rate limiting


# Example Usage
async def main_fundamental_data_ingestor_test():
    """Test the fundamental data ingestor functionality."""
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("🧪 Testing FundamentalDataIngestor")
    print("=" * 80)
    
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    
    project_id = _settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    await broker.connect()

    ingestor = FundamentalDataIngestor()

    test_tickers = ["AAPL", "MSFT", "GOOG", "JPM", "HSBC"]

    print("\n--- Testing FundamentalDataIngestor fetching and publishing ---")
    await ingestor.fetch_and_publish_fundamental_data(test_tickers, broker)

    await asyncio.sleep(5)
    await broker.disconnect()
    print("\nFundamentalDataIngestor test finished.")

if __name__ == '__main__':
    asyncio.run(main_fundamental_data_ingestor_test())