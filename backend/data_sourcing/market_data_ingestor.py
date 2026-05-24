# backend/data_sourcing/market_data_ingestor.py

import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.data_sourcing.data_ingestion_framework import BaseDataIngestor, DataIngestionConfig, DataSourceType
from backend.data_sourcing.api_clients.polygon_client import PolygonClient
from backend.data_sourcing.api_clients.finnhub_client import FinnhubClient
from backend.data_sourcing.api_clients.twelvedata_client import TwelveDataClient
from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.utils.async_utils import async_retry_api_call # Corrected import path

# Import demo mode integration
try:
    from backend.data_sourcing.demo_mode_integration import DemoModeMarketDataProvider
    DEMO_MODE_AVAILABLE = True
except ImportError:
    DEMO_MODE_AVAILABLE = False
    DemoModeMarketDataProvider = None

logger = logging.getLogger(__name__)

class EnhancedMarketDataIngestor(BaseDataIngestor):
    """Enhanced market data ingestor with multiple provider support and failover"""
    
    def __init__(self, broker):
        # Initialize with primary provider configuration
        config = DataIngestionConfig(
            source_id="market_data_multi",
            source_type=DataSourceType.MARKET_DATA,
            api_endpoint="multi_provider",
            rate_limit_per_minute=120,
            retry_attempts=3,
            timeout_seconds=30
        )
        
        super().__init__(config, broker)
        
        # Check if demo mode is enabled
        self.demo_mode = getattr(_settings, 'DEMO_MODE', False)
        self.demo_provider = None
        
        if self.demo_mode and DEMO_MODE_AVAILABLE:
            logger.info("Market Data Ingestor running in DEMO MODE - using free public sources")
            self.demo_provider = DemoModeMarketDataProvider()
            self.providers = []  # No paid providers in demo mode
        else:
            # Initialize multiple data providers (production mode)
            self.providers = self._initialize_providers()
        
        self.current_provider_index = 0
        self.symbols_to_track = self._get_symbols_to_track()
        
        # WebSocket connections for real-time data
        self.websocket_connections = {}
        self.real_time_enabled = getattr(_settings, 'REAL_TIME_MARKET_DATA_ENABLED', False) and not self.demo_mode
    
    def _initialize_providers(self) -> List[tuple]:
        """Initialize all available market data providers"""
        providers = []
        
        # Finnhub (Primary - generous free tier)
        if _settings.FINNHUB_API_KEY and _settings.FINNHUB_API_KEY != "YOUR_FINNHUB_API_KEY":
            finnhub_client = FinnhubClient(_settings.FINNHUB_API_KEY)
            providers.append((finnhub_client, "Finnhub", 60))  # 60 calls per minute
        
        # Polygon (Secondary)
        if _settings.POLYGON_API_KEY and _settings.POLYGON_API_KEY != "YOUR_POLYGON_API_KEY":
            polygon_client = PolygonClient(_settings.POLYGON_API_KEY)
            providers.append((polygon_client, "Polygon", 5))  # 5 calls per minute on free tier
        
        # TwelveData (Tertiary)
        if _settings.TWELVEDATA_API_KEY and _settings.TWELVEDATA_API_KEY != "YOUR_TWELVEDATA_API_KEY":
            # Corrected: TwelveDataClient only takes api_key as an argument.
            twelvedata_client = TwelveDataClient(_settings.TWELVEDATA_API_KEY)
            providers.append((twelvedata_client, "TwelveData", 8))  # 8 calls per minute on free tier
        
        if not providers:
            logger.critical("No market data providers configured with valid API keys")
        else:
            logger.info(f"Initialized {len(providers)} market data providers: {[p[1] for p in providers]}")
        
        return providers
    
    def _get_symbols_to_track(self) -> List[str]:
        """Get list of symbols to track"""
        default_symbols = [
            # Major Forex
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
            # Major Indices
            "SPY", "QQQ", "IWM", "DIA", "VTI", "EFA", "EEM",
            # Major Stocks
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            # Commodities
            "XAUUSD", "XAGUSD", "CRUDE_OIL", "NATURAL_GAS",
            # Crypto (if supported)
            "BTCUSD", "ETHUSD", "ADAUSD"
        ]
        
        # Get from settings or use defaults
        return getattr(_settings, 'MARKET_DATA_SYMBOLS', default_symbols)
    
    async def _fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch market data from available providers with failover"""
        
        # Demo mode - use free public sources
        if self.demo_mode and self.demo_provider:
            return await self._fetch_data_demo_mode()
        
        # Production mode - use paid APIs
        all_data = []
        
        for provider_client, provider_name, rate_limit in self.providers:
            try:
                # Adjust symbols per provider rate limit
                symbols_batch = self.symbols_to_track[:min(len(self.symbols_to_track), rate_limit // 2)]
                
                provider_data = await self._fetch_from_provider(
                    provider_client, provider_name, symbols_batch
                )
                
                if provider_data:
                    all_data.extend(provider_data)
                    logger.debug(f"Fetched {len(provider_data)} items from {provider_name}")
                
                # Rate limiting between providers
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to fetch from {provider_name}: {e}")
                continue
        
        return all_data if all_data else None
    
    async def _fetch_data_demo_mode(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch market data in demo mode using free public sources"""
        try:
            logger.info(f"Fetching market data in DEMO MODE for {len(self.symbols_to_track)} symbols")
            
            # Fetch quotes for all tracked symbols
            quotes = await self.demo_provider.fetch_batch_quotes(self.symbols_to_track)
            
            if not quotes:
                logger.warning("No data fetched in demo mode")
                return None
            
            # Convert to standard format
            all_data = []
            for symbol, quote_data in quotes.items():
                if quote_data:
                    # Standardize format to match production data
                    standardized_data = {
                        'symbol': symbol,
                        'price': quote_data.get('price'),
                        'bid': quote_data.get('bid'),
                        'ask': quote_data.get('ask'),
                        'volume': quote_data.get('volume'),
                        'change': quote_data.get('change'),
                        'change_percent': quote_data.get('change_percent'),
                        'timestamp': quote_data.get('timestamp', datetime.now()),
                        'source': 'demo_mode_yahoo_finance',
                        'provider': 'Yahoo Finance (Demo)'
                    }
                    all_data.append(standardized_data)
            
            logger.info(f"Demo mode: Successfully fetched {len(all_data)} quotes")
            return all_data if all_data else None
            
        except Exception as e:
            logger.error(f"Error fetching data in demo mode: {e}", exc_info=True)
            return None
    
    async def _fetch_from_provider(
        self, 
        client, 
        provider_name: str, 
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch data from a specific provider"""
        provider_data = []
        
        for symbol in symbols:
            try:
                # Normalize symbol for provider
                normalized_symbol = self._normalize_symbol_for_provider(symbol, provider_name)
                
                # Fetch quote data
                quote_data = await client.get_latest_quote(normalized_symbol)
                
                if quote_data:
                    # Add metadata
                    quote_data.update({
                        'original_symbol': symbol,
                        'normalized_symbol': normalized_symbol,
                        'provider': provider_name,
                        'fetch_timestamp': datetime.utcnow().isoformat()
                    })
                    provider_data.append(quote_data)
                
                # Small delay between symbol requests
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"Failed to fetch {symbol} from {provider_name}: {e}")
                continue
        
        return provider_data
    
    def _normalize_symbol_for_provider(self, symbol: str, provider: str) -> str:
        """Normalize symbol format for specific providers"""
        symbol_mappings = {
            "TwelveData": {
                "EURUSD": "EUR/USD",
                "GBPUSD": "GBP/USD", 
                "USDJPY": "USD/JPY",
                "XAUUSD": "XAU/USD",
                "XAGUSD": "XAG/USD",
                "BTCUSD": "BTC/USD",
                "ETHUSD": "ETH/USD"
            },
            "Polygon": {
                "EURUSD": "C:EURUSD",
                "GBPUSD": "C:GBPUSD",
                "USDJPY": "C:USDJPY",
                "XAUUSD": "C:XAUUSD",
                "BTCUSD": "X:BTCUSD"
            },
            "Finnhub": {
                # Finnhub uses standard symbols mostly
                "XAUUSD": "OANDA:XAU_USD",
                "XAGUSD": "OANDA:XAG_USD"
            }
        }
        
        provider_mapping = symbol_mappings.get(provider, {})
        return provider_mapping.get(symbol, symbol)
    
    async def start_real_time_streams(self):
        """Start real-time WebSocket streams for market data"""
        if not self.real_time_enabled:
            logger.info("Real-time market data streams disabled")
            return
        
        for provider_client, provider_name, _ in self.providers:
            if hasattr(provider_client, 'start_websocket'):
                try:
                    websocket_task = asyncio.create_task(
                        self._manage_websocket_connection(provider_client, provider_name)
                    )
                    self.websocket_connections[provider_name] = websocket_task
                    logger.info(f"Started WebSocket connection for {provider_name}")
                except Exception as e:
                    logger.error(f"Failed to start WebSocket for {provider_name}: {e}")
    
    async def _manage_websocket_connection(self, client, provider_name: str):
        """Manage WebSocket connection with reconnection logic"""
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        
        while self.is_running and reconnect_attempts < max_reconnect_attempts:
            try:
                await client.start_websocket(
                    symbols=self.symbols_to_track[:10],  # Limit symbols for WebSocket
                    callback=self._handle_websocket_data
                )
                reconnect_attempts = 0  # Reset on successful connection
                
            except Exception as e:
                reconnect_attempts += 1
                logger.error(f"WebSocket error for {provider_name}: {e}")
                
                if reconnect_attempts < max_reconnect_attempts:
                    wait_time = min(2 ** reconnect_attempts, 60)  # Exponential backoff
                    logger.info(f"Reconnecting to {provider_name} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max reconnection attempts reached for {provider_name}")
                    break
    
    async def _handle_websocket_data(self, data: Dict[str, Any]):
        """Handle incoming WebSocket data"""
        try:
            # Validate and normalize WebSocket data
            is_valid, quality, issues = self._validate_data(data)
            
            if is_valid:
                normalized_data = self._normalize_data(data)
                normalized_data['data_source'] = 'websocket'
                normalized_data['real_time'] = True
                
                # Publish to real-time topic
                await self.broker.publish_message("real_time_market_data", normalized_data)
                
                logger.debug(f"Published real-time data for {data.get('symbol', 'unknown')}")
            else:
                logger.warning(f"Invalid WebSocket data: {issues}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket data: {e}")
    
    async def stop_ingestion(self):
        """Stop ingestion and close WebSocket connections"""
        await super().stop_ingestion()
        
        # Close WebSocket connections
        for provider_name, websocket_task in self.websocket_connections.items():
            websocket_task.cancel()
            try:
                await websocket_task
            except asyncio.CancelledError:
                pass
            logger.info(f"Closed WebSocket connection for {provider_name}")
        
        self.websocket_connections.clear()
    
    def get_provider_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        provider_health = {}
        
        for provider_client, provider_name, rate_limit in self.providers:
            # Basic health check
            try:
                health_status = {
                    "name": provider_name,
                    "rate_limit": rate_limit,
                    "websocket_active": provider_name in self.websocket_connections,
                    "last_check": datetime.utcnow().isoformat()
                }
                provider_health[provider_name] = health_status
            except Exception as e:
                provider_health[provider_name] = {
                    "name": provider_name,
                    "error": str(e),
                    "status": "unhealthy"
                }
        
        return provider_health

# Legacy compatibility
class MarketDataIngestor(EnhancedMarketDataIngestor):
    """Legacy compatibility class"""
    
    def __init__(self, broker):
        # The broker instance is now passed in from dependencies.py
        super().__init__(broker)
    
    async def get_latest_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Legacy method for getting latest market data"""
        try:
            data = await self._fetch_from_provider(
                self.providers[0][0], self.providers[0][1], [symbol]
            )
            return data[0] if data else None
        except Exception as e:
            logger.error(f"Error fetching latest data for {symbol}: {e}")
            return None
    
    async def poll_market_data(self, symbols: List[str]):
        """Legacy method for polling market data"""
        self.symbols_to_track = symbols
        data = await self._fetch_data()
        
        if data:
            # This block was incomplete in the original file.
            # A reasonable action is to log the result.
            logger.info(f"Polled {len(data)} data points successfully.")

async def main_market_data_ingestor_test():
    """A functional test for the EnhancedMarketDataIngestor."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # A mock broker is used to initialize the ingestor without real dependencies.
    class MockBroker:
        async def publish_message(self, topic: str, message: Dict[str, Any]):
            logger.info(f"MOCK BROKER: Published to topic '{topic}': {message.get('original_symbol')}")
        
        def _validate_data(self, data): return True, 1.0, [] # Mock validation
        def _normalize_data(self, data): return data # Mock normalization

    logger.info("Initializing EnhancedMarketDataIngestor for a test run...")
    # The ingestor requires a broker instance upon initialization.
    ingestor = EnhancedMarketDataIngestor(broker=MockBroker())
    
    if not ingestor.providers:
        logger.error("No data providers configured in _settings. Aborting test.")
        return

    logger.info("Attempting to fetch data from configured providers...")
    fetched_data = await ingestor._fetch_data()

    if fetched_data:
        logger.info(f"Successfully fetched {len(fetched_data)} data points.")
        logger.info(f"Example data point: {fetched_data[0]}")
    else:
        logger.warning("No data was fetched. Check API keys and provider status.")
    
    logger.info("Test finished.")

# This block runs only when the script is executed directly.
if __name__ == "__main__":
    asyncio.run(main_market_data_ingestor_test())

