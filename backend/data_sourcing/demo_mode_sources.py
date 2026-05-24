# backend/data_sourcing/demo_mode_sources.py

"""
Demo Mode Data Sources
Provides free, publicly available data sources for demo and testing purposes.
Uses Yahoo Finance, Google News, Reuters, MSN, MarketWatch, CNBC, and other free sources.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import feedparser
import json
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """
    Yahoo Finance client for free market data and news.
    No API key required - uses public endpoints.
    """
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance"
        self.news_url = "https://finance.yahoo.com/rss"
        self.session = None
        logger.info("YahooFinanceClient initialized (no API key required)")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'EURUSD=X')
        
        Returns:
            Dictionary with quote data or None if failed
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/quote"
            params = {
                'symbols': symbol,
                'fields': 'regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketTime,regularMarketVolume,bid,ask,bidSize,askSize'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('quoteResponse', {}).get('result'):
                        quote = data['quoteResponse']['result'][0]
                        return {
                            'symbol': quote.get('symbol'),
                            'price': quote.get('regularMarketPrice'),
                            'change': quote.get('regularMarketChange'),
                            'change_percent': quote.get('regularMarketChangePercent'),
                            'volume': quote.get('regularMarketVolume'),
                            'bid': quote.get('bid'),
                            'ask': quote.get('ask'),
                            'bid_size': quote.get('bidSize'),
                            'ask_size': quote.get('askSize'),
                            'timestamp': datetime.fromtimestamp(quote.get('regularMarketTime', 0)),
                            'source': 'yahoo_finance'
                        }
                logger.warning(f"Yahoo Finance: No data for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Yahoo Finance quote error for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = '1mo', interval: str = '1d') -> List[Dict[str, Any]]:
        """
        Get historical price data.
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            List of historical data points
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/chart/{symbol}"
            params = {
                'period1': int((datetime.now() - timedelta(days=30)).timestamp()),
                'period2': int(datetime.now().timestamp()),
                'interval': interval
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    chart = data.get('chart', {}).get('result', [{}])[0]
                    timestamps = chart.get('timestamp', [])
                    quotes = chart.get('indicators', {}).get('quote', [{}])[0]
                    
                    historical_data = []
                    for i, ts in enumerate(timestamps):
                        historical_data.append({
                            'timestamp': datetime.fromtimestamp(ts),
                            'open': quotes.get('open', [])[i] if i < len(quotes.get('open', [])) else None,
                            'high': quotes.get('high', [])[i] if i < len(quotes.get('high', [])) else None,
                            'low': quotes.get('low', [])[i] if i < len(quotes.get('low', [])) else None,
                            'close': quotes.get('close', [])[i] if i < len(quotes.get('close', [])) else None,
                            'volume': quotes.get('volume', [])[i] if i < len(quotes.get('volume', [])) else None,
                            'symbol': symbol,
                            'source': 'yahoo_finance'
                        })
                    
                    logger.info(f"Yahoo Finance: Fetched {len(historical_data)} historical data points for {symbol}")
                    return historical_data
                
                logger.warning(f"Yahoo Finance: No historical data for {symbol}")
                return []
        except Exception as e:
            logger.error(f"Yahoo Finance historical data error for {symbol}: {e}")
            return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get financial news from Yahoo Finance RSS feeds.
        
        Args:
            symbol: Optional stock symbol for symbol-specific news
            limit: Maximum number of articles to return
        
        Returns:
            List of news articles
        """
        try:
            if symbol:
                rss_url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
            else:
                rss_url = "https://finance.yahoo.com/news/rssindex"
            
            feed = await asyncio.to_thread(feedparser.parse, rss_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                articles.append({
                    'headline': entry.get('title', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', ''),
                    'source': 'Yahoo Finance',
                    'symbols': [symbol] if symbol else [],
                    'category': 'financial'
                })
            
            logger.info(f"Yahoo Finance: Fetched {len(articles)} news articles")
            return articles
        except Exception as e:
            logger.error(f"Yahoo Finance news error: {e}")
            return []


class FreeNewsAggregator:
    """
    Aggregates news from multiple free RSS sources:
    - Google News
    - Reuters
    - MSN News/Finance
    - MarketWatch
    - CNBC
    - Bloomberg (RSS)
    - Financial Times (RSS)
    """
    
    def __init__(self):
        self.rss_feeds = {
            # Google News - Financial
            'google_finance': 'https://news.google.com/rss/search?q=finance+OR+stock+market+OR+economy&hl=en-US&gl=US&ceid=US:en',
            'google_business': 'https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en',
            
            # Reuters
            'reuters_business': 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best',
            'reuters_markets': 'http://feeds.reuters.com/reuters/businessNews',
            
            # MSN
            'msn_money': 'https://www.msn.com/en-us/money/rss',
            
            # MarketWatch
            'marketwatch_topstories': 'http://feeds.marketwatch.com/marketwatch/topstories',
            'marketwatch_realtimeheadlines': 'http://feeds.marketwatch.com/marketwatch/realtimeheadlines',
            
            # CNBC
            'cnbc_topnews': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
            'cnbc_markets': 'https://www.cnbc.com/id/20910258/device/rss/rss.html',
            
            # Bloomberg (limited RSS)
            'bloomberg_markets': 'https://feeds.bloomberg.com/markets/news.rss',
            
            # Financial Times
            'ft_companies': 'https://www.ft.com/companies?format=rss',
            'ft_markets': 'https://www.ft.com/markets?format=rss',
            
            # Seeking Alpha
            'seekingalpha_market': 'https://seekingalpha.com/market_currents.xml',
            
            # Barron's
            'barrons': 'https://www.barrons.com/feed/rss/',
            
            # Investor's Business Daily
            'ibd': 'https://www.investors.com/feed/',
        }
        logger.info(f"FreeNewsAggregator initialized with {len(self.rss_feeds)} RSS feeds")
    
    async def fetch_feed(self, feed_name: str, feed_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS feed.
        
        Args:
            feed_name: Name of the feed
            feed_url: URL of the RSS feed
            limit: Maximum number of articles to return
        
        Returns:
            List of articles
        """
        try:
            feed = await asyncio.to_thread(feedparser.parse, feed_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                # Extract published date
                published_at = entry.get('published', entry.get('updated', ''))
                
                # Extract content
                content = entry.get('summary', entry.get('description', ''))
                if hasattr(entry, 'content'):
                    content = entry.content[0].value if entry.content else content
                
                articles.append({
                    'headline': entry.get('title', ''),
                    'content': content,
                    'url': entry.get('link', ''),
                    'published_at': published_at,
                    'source': feed_name,
                    'category': self._categorize_feed(feed_name),
                    'symbols': []  # Would need NLP to extract
                })
            
            logger.debug(f"Fetched {len(articles)} articles from {feed_name}")
            return articles
        except Exception as e:
            logger.error(f"Error fetching {feed_name}: {e}")
            return []
    
    def _categorize_feed(self, feed_name: str) -> str:
        """Categorize feed based on name"""
        if 'market' in feed_name.lower():
            return 'markets'
        elif 'business' in feed_name.lower():
            return 'business'
        elif 'finance' in feed_name.lower() or 'money' in feed_name.lower():
            return 'financial'
        else:
            return 'general'
    
    async def fetch_all_feeds(self, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from all configured RSS feeds concurrently.
        
        Args:
            limit_per_feed: Maximum articles per feed
        
        Returns:
            Combined list of all articles
        """
        logger.info(f"Fetching all {len(self.rss_feeds)} RSS feeds...")
        
        tasks = [
            self.fetch_feed(name, url, limit_per_feed)
            for name, url in self.rss_feeds.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Feed fetch failed: {result}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"Fetched {len(unique_articles)} unique articles from all feeds")
        return unique_articles
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for news articles matching a query using Google News RSS.
        
        Args:
            query: Search query
            limit: Maximum number of articles
        
        Returns:
            List of matching articles
        """
        try:
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            search_url = f'https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en'
            
            feed = await asyncio.to_thread(feedparser.parse, search_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                articles.append({
                    'headline': entry.get('title', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', ''),
                    'source': 'Google News Search',
                    'category': 'search_result',
                    'query': query,
                    'symbols': []
                })
            
            logger.info(f"Google News search for '{query}': {len(articles)} articles")
            return articles
        except Exception as e:
            logger.error(f"Google News search error: {e}")
            return []


class DemoModeDataAdapter:
    """
    Unified adapter for demo mode data sources.
    Provides a consistent interface for all free data sources with intelligent fallbacks.
    """
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
        self.news_aggregator = FreeNewsAggregator()
        self.cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
        logger.info("DemoModeDataAdapter initialized")
    
    async def close(self):
        """Close all connections"""
        await self.yahoo_client.close()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time, _ = self.cache[cache_key]
        return (datetime.now() - cached_time).total_seconds() < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            _, data = self.cache[cache_key]
            return data
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set data in cache"""
        self.cache[cache_key] = (datetime.now(), data)
    
    async def get_market_data(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get real-time market data for a symbol.
        
        Args:
            symbol: Stock/forex symbol
            use_cache: Whether to use cached data
        
        Returns:
            Market data dictionary or None
        """
        cache_key = f"market_{symbol}"
        
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.debug(f"Returning cached market data for {symbol}")
                return cached_data
        
        # Try Yahoo Finance
        data = await self.yahoo_client.get_quote(symbol)
        
        if data:
            self._set_cache(cache_key, data)
            return data
        
        logger.warning(f"No market data available for {symbol}")
        return None
    
    async def get_historical_data(self, symbol: str, period: str = '1mo', interval: str = '1d') -> List[Dict[str, Any]]:
        """
        Get historical market data.
        
        Args:
            symbol: Stock/forex symbol
            period: Time period
            interval: Data interval
        
        Returns:
            List of historical data points
        """
        cache_key = f"historical_{symbol}_{period}_{interval}"
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Returning cached historical data for {symbol}")
            return cached_data
        
        # Try Yahoo Finance
        data = await self.yahoo_client.get_historical_data(symbol, period, interval)
        
        if data:
            self._set_cache(cache_key, data)
            return data
        
        logger.warning(f"No historical data available for {symbol}")
        return []
    
    async def get_news(self, query: Optional[str] = None, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get financial news from multiple sources.
        
        Args:
            query: Optional search query
            symbol: Optional stock symbol
            limit: Maximum number of articles
        
        Returns:
            List of news articles
        """
        all_articles = []
        
        # If symbol provided, get Yahoo Finance symbol-specific news
        if symbol:
            yahoo_news = await self.yahoo_client.get_news(symbol, limit=limit // 2)
            all_articles.extend(yahoo_news)
        
        # If query provided, search Google News
        if query:
            search_results = await self.news_aggregator.search_news(query, limit=limit // 2)
            all_articles.extend(search_results)
        
        # If no specific query/symbol, get general financial news
        if not query and not symbol:
            general_news = await self.news_aggregator.fetch_all_feeds(limit_per_feed=2)
            all_articles.extend(general_news[:limit])
        
        # Sort by published date (most recent first)
        all_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        logger.info(f"Retrieved {len(all_articles)} news articles")
        return all_articles[:limit]
    
    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols concurrently.
        
        Args:
            symbols: List of symbols
        
        Returns:
            Dictionary mapping symbols to their quote data
        """
        tasks = [self.get_market_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                quotes[symbol] = result
            elif isinstance(result, Exception):
                logger.error(f"Error fetching {symbol}: {result}")
        
        logger.info(f"Fetched quotes for {len(quotes)}/{len(symbols)} symbols")
        return quotes


# Example usage and testing
async def demo_test():
    """Test demo mode data sources"""
    logging.basicConfig(level=logging.INFO)
    
    adapter = DemoModeDataAdapter()
    
    try:
        print("\n=== Testing Market Data ===")
        # Test stock quote
        aapl = await adapter.get_market_data('AAPL')
        if aapl:
            print(f"AAPL: ${aapl['price']:.2f} ({aapl['change_percent']:.2f}%)")
        
        # Test forex quote
        eurusd = await adapter.get_market_data('EURUSD=X')
        if eurusd:
            print(f"EURUSD: {eurusd['price']:.4f}")
        
        print("\n=== Testing Batch Quotes ===")
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        quotes = await adapter.get_batch_quotes(symbols)
        for symbol, data in quotes.items():
            print(f"{symbol}: ${data['price']:.2f}")
        
        print("\n=== Testing Historical Data ===")
        historical = await adapter.get_historical_data('AAPL', period='5d', interval='1d')
        print(f"Retrieved {len(historical)} historical data points for AAPL")
        if historical:
            latest = historical[-1]
            print(f"Latest: {latest['timestamp']} - Close: ${latest['close']:.2f}")
        
        print("\n=== Testing News ===")
        # Symbol-specific news
        aapl_news = await adapter.get_news(symbol='AAPL', limit=5)
        print(f"\nAAPL News ({len(aapl_news)} articles):")
        for article in aapl_news[:3]:
            print(f"  - {article['headline'][:80]}...")
        
        # Search news
        search_news = await adapter.get_news(query='Federal Reserve interest rates', limit=5)
        print(f"\nFed News ({len(search_news)} articles):")
        for article in search_news[:3]:
            print(f"  - {article['headline'][:80]}...")
        
        # General financial news
        general_news = await adapter.get_news(limit=10)
        print(f"\nGeneral Financial News ({len(general_news)} articles):")
        for article in general_news[:5]:
            print(f"  - [{article['source']}] {article['headline'][:60]}...")
        
    finally:
        await adapter.close()


if __name__ == '__main__':
    asyncio.run(demo_test())