# backend/data_sourcing/demo_mode_integration.py

"""
Demo Mode Integration
Integrates demo mode data sources with existing PRIV data ingestors.
Provides seamless switching between production APIs and free demo sources.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.data_sourcing.demo_mode_sources import (
    DemoModeDataAdapter,
    YahooFinanceClient,
    FreeNewsAggregator
)
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class DemoModeMarketDataProvider:
    """
    Wrapper for market data that switches between production and demo mode.
    Compatible with existing MarketDataIngestor interface.
    """
    
    def __init__(self):
        self.demo_mode = settings.DEMO_MODE
        self.demo_adapter = None
        
        if self.demo_mode:
            self.demo_adapter = DemoModeDataAdapter()
            logger.info("DemoModeMarketDataProvider initialized in DEMO MODE")
        else:
            logger.info("DemoModeMarketDataProvider initialized in PRODUCTION MODE")
    
    async def close(self):
        """Close demo adapter if active"""
        if self.demo_adapter:
            await self.demo_adapter.close()
    
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time quote for a symbol.
        In demo mode, uses Yahoo Finance. In production, uses configured APIs.
        
        Args:
            symbol: Stock/forex symbol
        
        Returns:
            Quote data dictionary
        """
        if not self.demo_mode:
            # In production mode, this would call the actual API
            logger.warning("Production mode quote fetch not implemented - use existing MarketDataIngestor")
            return None
        
        # Demo mode - use Yahoo Finance
        return await self.demo_adapter.get_market_data(symbol)
    
    async def fetch_historical(self, symbol: str, period: str = '1mo', interval: str = '1d') -> List[Dict[str, Any]]:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Stock/forex symbol
            period: Time period
            interval: Data interval
        
        Returns:
            List of historical data points
        """
        if not self.demo_mode:
            logger.warning("Production mode historical fetch not implemented - use existing MarketDataIngestor")
            return []
        
        # Demo mode - use Yahoo Finance
        return await self.demo_adapter.get_historical_data(symbol, period, interval)
    
    async def fetch_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch quotes for multiple symbols.
        
        Args:
            symbols: List of symbols
        
        Returns:
            Dictionary mapping symbols to quote data
        """
        if not self.demo_mode:
            logger.warning("Production mode batch quotes not implemented - use existing MarketDataIngestor")
            return {}
        
        # Demo mode - use Yahoo Finance
        return await self.demo_adapter.get_batch_quotes(symbols)


class DemoModeNewsProvider:
    """
    Wrapper for news data that switches between production and demo mode.
    Compatible with existing NewsAPIClient and GlobalNewsIngestor interfaces.
    """
    
    def __init__(self):
        self.demo_mode = settings.DEMO_MODE
        self.demo_adapter = None
        
        if self.demo_mode:
            self.demo_adapter = DemoModeDataAdapter()
            logger.info("DemoModeNewsProvider initialized in DEMO MODE")
        else:
            logger.info("DemoModeNewsProvider initialized in PRODUCTION MODE")
    
    async def close(self):
        """Close demo adapter if active"""
        if self.demo_adapter:
            await self.demo_adapter.close()
    
    async def fetch_news(self, 
                        query: Optional[str] = None,
                        symbols: Optional[List[str]] = None,
                        from_date: Optional[datetime] = None,
                        to_date: Optional[datetime] = None,
                        limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch news articles.
        In demo mode, uses free RSS feeds. In production, uses NewsAPI.
        
        Args:
            query: Search query
            symbols: List of relevant symbols
            from_date: Start date (not used in demo mode)
            to_date: End date (not used in demo mode)
            limit: Maximum number of articles
        
        Returns:
            List of news articles
        """
        if not self.demo_mode:
            logger.warning("Production mode news fetch not implemented - use existing NewsAPIClient")
            return []
        
        # Demo mode - use free RSS feeds
        # If symbols provided, fetch news for first symbol
        symbol = symbols[0] if symbols else None
        
        return await self.demo_adapter.get_news(query=query, symbol=symbol, limit=limit)
    
    async def fetch_all_feeds(self, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch from all configured news feeds.
        
        Args:
            limit_per_feed: Maximum articles per feed
        
        Returns:
            Combined list of articles
        """
        if not self.demo_mode:
            logger.warning("Production mode feed fetch not implemented - use existing GlobalNewsIngestor")
            return []
        
        # Demo mode - use free RSS aggregator
        if not self.demo_adapter:
            self.demo_adapter = DemoModeDataAdapter()
        
        return await self.demo_adapter.news_aggregator.fetch_all_feeds(limit_per_feed)
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            limit: Maximum number of articles
        
        Returns:
            List of matching articles
        """
        if not self.demo_mode:
            logger.warning("Production mode news search not implemented - use existing NewsAPIClient")
            return []
        
        # Demo mode - use Google News search
        if not self.demo_adapter:
            self.demo_adapter = DemoModeDataAdapter()
        
        return await self.demo_adapter.news_aggregator.search_news(query, limit)


class DemoModeDataFactory:
    """
    Factory for creating demo mode or production mode data providers.
    Provides a unified interface for the entire application.
    """
    
    @staticmethod
    def create_market_data_provider() -> DemoModeMarketDataProvider:
        """Create a market data provider (demo or production)"""
        return DemoModeMarketDataProvider()
    
    @staticmethod
    def create_news_provider() -> DemoModeNewsProvider:
        """Create a news provider (demo or production)"""
        return DemoModeNewsProvider()
    
    @staticmethod
    def is_demo_mode() -> bool:
        """Check if demo mode is enabled"""
        return settings.DEMO_MODE
    
    @staticmethod
    def get_mode_description() -> str:
        """Get a description of the current mode"""
        if settings.DEMO_MODE:
            return "DEMO MODE - Using free public data sources (Yahoo Finance, Google News, Reuters, etc.)"
        else:
            return "PRODUCTION MODE - Using paid API services"


# Convenience functions for easy integration
async def get_market_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get market quote for a symbol (demo or production mode).
    
    Args:
        symbol: Stock/forex symbol
    
    Returns:
        Quote data
    """
    provider = DemoModeDataFactory.create_market_data_provider()
    try:
        return await provider.fetch_quote(symbol)
    finally:
        await provider.close()


async def get_market_quotes(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get market quotes for multiple symbols (demo or production mode).
    
    Args:
        symbols: List of symbols
    
    Returns:
        Dictionary of quotes
    """
    provider = DemoModeDataFactory.create_market_data_provider()
    try:
        return await provider.fetch_batch_quotes(symbols)
    finally:
        await provider.close()


async def get_news(query: Optional[str] = None, 
                  symbol: Optional[str] = None,
                  limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get news articles (demo or production mode).
    
    Args:
        query: Search query
        symbol: Stock symbol
        limit: Maximum articles
    
    Returns:
        List of articles
    """
    provider = DemoModeDataFactory.create_news_provider()
    try:
        symbols = [symbol] if symbol else None
        return await provider.fetch_news(query=query, symbols=symbols, limit=limit)
    finally:
        await provider.close()


async def search_news(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for news articles (demo or production mode).
    
    Args:
        query: Search query
        limit: Maximum articles
    
    Returns:
        List of articles
    """
    provider = DemoModeDataFactory.create_news_provider()
    try:
        return await provider.search_news(query, limit)
    finally:
        await provider.close()


# Example usage
async def demo_integration_test():
    """Test demo mode integration"""
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    print(f"\n{DemoModeDataFactory.get_mode_description()}\n")
    
    # Test market data
    print("=== Testing Market Data ===")
    quote = await get_market_quote('AAPL')
    if quote:
        print(f"AAPL: ${quote['price']:.2f} ({quote['change_percent']:.2f}%)")
    
    # Test batch quotes
    print("\n=== Testing Batch Quotes ===")
    quotes = await get_market_quotes(['AAPL', 'MSFT', 'GOOGL'])
    for symbol, data in quotes.items():
        print(f"{symbol}: ${data['price']:.2f}")
    
    # Test news
    print("\n=== Testing News ===")
    news = await get_news(symbol='AAPL', limit=5)
    print(f"Found {len(news)} articles about AAPL:")
    for article in news[:3]:
        print(f"  - {article['headline'][:70]}...")
    
    # Test news search
    print("\n=== Testing News Search ===")
    search_results = await search_news('Federal Reserve', limit=5)
    print(f"Found {len(search_results)} articles about Federal Reserve:")
    for article in search_results[:3]:
        print(f"  - {article['headline'][:70]}...")


if __name__ == '__main__':
    import asyncio
    asyncio.run(demo_integration_test())