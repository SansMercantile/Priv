import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import hashlib
import re
from dataclasses import dataclass

from backend.data_sourcing.data_ingestion_framework import BaseDataIngestor, DataIngestionConfig, DataSourceType
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient
from backend.data_sourcing.global_news_ingestor import GlobalNewsIngestor
from backend.fundamental_analysis.news_sourcing.tradingview_retriever import TradingViewRetriever
from backend.config.settings import Settings

# Create settings instance
_settings = Settings()

# Import demo mode integration
try:
    from backend.data_sourcing.demo_mode_integration import DemoModeNewsProvider
    DEMO_MODE_AVAILABLE = True
except ImportError:
    DEMO_MODE_AVAILABLE = False
    DemoModeNewsProvider = None

# Import DataQuality if defined elsewhere, or define a minimal version here
try:
    from backend.data_sourcing.data_ingestion_framework import DataQuality
except ImportError:
    from enum import Enum
    class DataQuality(Enum):
        CORRUPTED = "corrupted"
        VALID = "valid"
        # Add other statuses as needed

logger = logging.getLogger(__name__)

@dataclass
class NewsSource:
    name: str
    url: str
    source_type: str  # 'rss', 'api', 'scraper'
    update_frequency: int  # minutes
    priority: int  # 1-5, higher is more important
    categories: List[str]
    enabled: bool = True

class SentimentAnalyzer:
    """Advanced sentiment analysis for news content"""
    
    def __init__(self):
        self.positive_keywords = {
            'financial': ['profit', 'growth', 'gain', 'rise', 'surge', 'boom', 'bullish', 'optimistic'],
            'general': ['good', 'great', 'excellent', 'positive', 'success', 'achievement', 'breakthrough']
        }
        
        self.negative_keywords = {
            'financial': ['loss', 'decline', 'fall', 'crash', 'bearish', 'recession', 'crisis', 'risk'],
            'general': ['bad', 'terrible', 'negative', 'failure', 'problem', 'concern', 'worry']
        }
        
        self.intensity_modifiers = {
            'very': 1.3, 'extremely': 1.5, 'significantly': 1.4, 'dramatically': 1.5,
            'slightly': 0.7, 'somewhat': 0.8, 'moderately': 0.9
        }
    
    def analyze_sentiment(self, text: str, headline: str = "") -> Dict[str, Any]:
        """Analyze sentiment of news text"""
        combined_text = f"{headline} {text}".lower()
        
        # Count positive and negative keywords
        positive_score = 0
        negative_score = 0
        
        for category, keywords in self.positive_keywords.items():
            for keyword in keywords:
                matches = len(re.findall(r'\b' + keyword + r'\b', combined_text))
                positive_score += matches
        
        for category, keywords in self.negative_keywords.items():
            for keyword in keywords:
                matches = len(re.findall(r'\b' + keyword + r'\b', combined_text))
                negative_score += matches
        
        # Apply intensity modifiers
        for modifier, multiplier in self.intensity_modifiers.items():
            if modifier in combined_text:
                positive_score *= multiplier
                negative_score *= multiplier
        
        # Calculate sentiment
        total_score = positive_score + negative_score
        if total_score == 0:
            sentiment = "neutral"
            confidence = 0.5
        else:
            sentiment_ratio = positive_score / total_score
            if sentiment_ratio > 0.6:
                sentiment = "positive"
                confidence = min(sentiment_ratio, 0.9)
            elif sentiment_ratio < 0.4:
                sentiment = "negative"
                confidence = min(1 - sentiment_ratio, 0.9)
            else:
                sentiment = "neutral"
                confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "keywords_found": {
                "positive": positive_score,
                "negative": negative_score
            }
        }

class SymbolExtractor:
    """Extract financial symbols and entities from news content"""
    
    def __init__(self):
        # Common stock symbols pattern
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        # Forex pairs pattern
        self.forex_pattern = re.compile(r'\b[A-Z]{3}[/\-]?[A-Z]{3}\b')
        
        # Company name mappings
        self.company_mappings = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
            'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META', 'facebook': 'META',
            'netflix': 'NFLX', 'nvidia': 'NVDA', 'intel': 'INTC', 'amd': 'AMD'
        }
        
        # Currency mappings
        self.currency_mappings = {
            'dollar': 'USD', 'euro': 'EUR', 'pound': 'GBP', 'yen': 'JPY',
            'swiss franc': 'CHF', 'canadian dollar': 'CAD', 'australian dollar': 'AUD'
        }
    
    def extract_symbols(self, text: str, headline: str = "") -> List[str]:
        """Extract financial symbols from text"""
        combined_text = f"{headline} {text}".lower()
        symbols = set()
        
        # Extract direct stock symbols
        stock_matches = self.stock_pattern.findall(text.upper())
        for match in stock_matches:
            if len(match) <= 5 and match.isalpha():
                symbols.add(match)
        
        # Extract forex pairs
        forex_matches = self.forex_pattern.findall(text.upper())
        for match in forex_matches:
            clean_match = match.replace('/', '').replace('-', '')
            if len(clean_match) == 6:
                symbols.add(clean_match)
        
        # Extract from company names
        for company, symbol in self.company_mappings.items():
            if company in combined_text:
                symbols.add(symbol)
        
        # Extract currency pairs from text
        mentioned_currencies = []
        for currency_name, currency_code in self.currency_mappings.items():
            if currency_name in combined_text:
                mentioned_currencies.append(currency_code)
        
        # Create forex pairs from mentioned currencies
        if len(mentioned_currencies) >= 2:
            for i in range(len(mentioned_currencies)):
                for j in range(i + 1, len(mentioned_currencies)):
                    pair = mentioned_currencies[i] + mentioned_currencies[j]
                    symbols.add(pair)
        
        return list(symbols)

class EnhancedNewsIngestor(BaseDataIngestor):
    """Enhanced news ingestion system with multiple sources and advanced processing"""
    
    def __init__(self, broker):
        config = DataIngestionConfig(
            source_id="enhanced_news",
            source_type=DataSourceType.NEWS,
            api_endpoint="multi_source",
            rate_limit_per_minute=100,
            retry_attempts=3,
            timeout_seconds=45
        )
        
        super().__init__(config, broker)
        
        # Check if demo mode is enabled
        self.demo_mode = getattr(_settings, 'DEMO_MODE', False)
        self.demo_provider = None
        
        if self.demo_mode and DEMO_MODE_AVAILABLE:
            logger.info("Enhanced News Ingestor running in DEMO MODE - using free public RSS feeds")
            self.demo_provider = DemoModeNewsProvider()
        
        # Initialize components
        self.sentiment_analyzer = SentimentAnalyzer()
        self.symbol_extractor = SymbolExtractor()
        self.processed_articles: Set[str] = set()
        
        # Initialize news sources (skip in demo mode)
        if not self.demo_mode:
            self.news_sources = self._initialize_news_sources()
            self.news_clients = self._initialize_news_clients()
        else:
            self.news_sources = []
            self.news_clients = []
        
        # Deduplication settings
        self.dedup_window_hours = 24
        self.similarity_threshold = 0.8
    
    def _initialize_news_sources(self) -> List[NewsSource]:
        """Initialize comprehensive news sources"""
        sources = [
            # Financial News APIs
            NewsSource("NewsAPI", "newsapi", "api", 15, 5, ["finance", "business"]),
            NewsSource("Alpha Vantage News", "alphavantage", "api", 30, 4, ["finance"]),
            
            # RSS Feeds
            NewsSource("Reuters Business", "https://feeds.reuters.com/reuters/businessNews", "rss", 10, 5, ["business"]),
            NewsSource("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss", "rss", 10, 5, ["finance"]),
            NewsSource("Financial Times", "https://www.ft.com/rss/home", "rss", 15, 4, ["finance"]),
            NewsSource("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "rss", 10, 4, ["finance"]),
            NewsSource("Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline", "rss", 10, 4, ["finance"]),
            NewsSource("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "rss", 10, 5, ["finance"]),
            
            # Economic News
            NewsSource("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "rss", 60, 5, ["monetary_policy"]),
            NewsSource("ECB Press", "https://www.ecb.europa.eu/rss/press.xml", "rss", 60, 4, ["monetary_policy"]),
            
            # Crypto News
            NewsSource("CoinDesk", "https://feeds.coindesk.com/coindesk/rss", "rss", 15, 3, ["crypto"]),
            NewsSource("CoinTelegraph", "https://cointelegraph.com/rss", "rss", 15, 3, ["crypto"]),
            
            # Scrapers
            NewsSource("TradingView Ideas", "tradingview", "scraper", 30, 3, ["analysis", "ideas"]),
            NewsSource("Seeking Alpha", "seekingalpha", "scraper", 60, 4, ["analysis"]),
        ]
        
        # Filter enabled sources
        return [source for source in sources if source.enabled]
    
    def _initialize_news_clients(self) -> Dict[str, Any]:
        """Initialize news API clients"""
        clients = {}
        
        # NewsAPI client
        if _settings.NEWS_API_KEY_AI and _settings.NEWS_API_KEY_AI != "YOUR_NEWS_API_KEY":
            clients['newsapi'] = NewsAPIClient(
                api_key_ai=_settings.NEWS_API_KEY_AI,
                api_key_org=getattr(settings, 'NEWS_API_KEY_ORG', ''),
                use_mock=False
            )
        
        # Global news ingestor for RSS feeds
        clients['global_news'] = GlobalNewsIngestor()
        
        # TradingView retriever
        clients['tradingview'] = TradingViewRetriever()
        
        return clients
    
    async def _fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch news from all configured sources"""
        
        # Demo mode - use free public RSS feeds
        if self.demo_mode and self.demo_provider:
            return await self._fetch_data_demo_mode()
        
        # Production mode - use paid APIs
        all_articles = []
        
        # Fetch from different source types
        api_articles = await self._fetch_from_apis()
        rss_articles = await self._fetch_from_rss()
        scraper_articles = await self._fetch_from_scrapers()
        
        all_articles.extend(api_articles)
        all_articles.extend(rss_articles)
        all_articles.extend(scraper_articles)
        
        # Deduplicate articles
        deduplicated_articles = self._deduplicate_articles(all_articles)
        
        logger.info(f"Fetched {len(all_articles)} articles, {len(deduplicated_articles)} after deduplication")
        
        return deduplicated_articles if deduplicated_articles else None
    
    async def _fetch_data_demo_mode(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch news in demo mode using free public RSS feeds"""
        try:
            logger.info("Fetching news in DEMO MODE from free public RSS feeds")
            
            # Fetch from all free RSS feeds
            articles = await self.demo_provider.fetch_all_feeds(limit_per_feed=5)
            
            if not articles:
                logger.warning("No articles fetched in demo mode")
                return None
            
            # Process articles through sentiment analyzer and symbol extractor
            processed_articles = []
            for article in articles:
                # Skip if already processed
                article_id = self._generate_article_id(article)
                if article_id in self.processed_articles:
                    continue
                
                # Analyze sentiment
                sentiment_score = self.sentiment_analyzer.analyze(article.get('content', ''))
                
                # Extract symbols
                symbols = self.symbol_extractor.extract(
                    article.get('headline', '') + ' ' + article.get('content', '')
                )
                
                # Add processed data
                processed_article = {
                    **article,
                    'sentiment_score': sentiment_score,
                    'symbols': symbols,
                    'processed_at': datetime.now().isoformat(),
                    'demo_mode': True
                }
                
                processed_articles.append(processed_article)
                self.processed_articles.add(article_id)
            
            logger.info(f"Demo mode: Processed {len(processed_articles)} articles")
            return processed_articles if processed_articles else None
            
        except Exception as e:
            logger.error(f"Error fetching news in demo mode: {e}", exc_info=True)
            return None
    
    async def _fetch_from_apis(self) -> List[Dict[str, Any]]:
        """Fetch news from API sources"""
        articles = []
        
        if 'newsapi' in self.news_clients:
            try:
                # Fetch financial news
                financial_queries = ["stocks", "forex", "cryptocurrency", "federal reserve", "inflation"]
                
                for query in financial_queries:
                    api_articles = await self.news_clients['newsapi'].fetch_news(
                        query=query,
                        language="en",
                        sort_by="publishedAt",
                        page_size=20
                    )
                    
                    if api_articles:
                        for article in api_articles:
                            article['source_type'] = 'api'
                            article['source_name'] = 'NewsAPI'
                            article['query'] = query
                        articles.extend(api_articles)
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
            except Exception as e:
                logger.error(f"Error fetching from NewsAPI: {e}")
        
        return articles
    
    async def _fetch_from_rss(self) -> List[Dict[str, Any]]:
        """Fetch news from RSS sources"""
        articles = []
        
        if 'global_news' in self.news_clients:
            try:
                # Fetch from all RSS feeds
                rss_articles = await self.news_clients['global_news'].fetch_all_rss_feeds(
                    limit_per_feed=50
                )
                
                for article in rss_articles:
                    article['source_type'] = 'rss'
                    if 'source' not in article:
                        article['source'] = 'RSS Feed'
                
                articles.extend(rss_articles)
                
            except Exception as e:
                logger.error(f"Error fetching from RSS feeds: {e}")
        
        return articles
    
    async def _fetch_from_scrapers(self) -> List[Dict[str, Any]]:
        """Fetch news from scraper sources"""
        articles = []
        
        # TradingView ideas
        if 'tradingview' in self.news_clients:
            try:
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "SPY", "QQQ", "AAPL", "TSLA"]
                
                for symbol in symbols:
                    ideas = await asyncio.to_thread(
                        self.news_clients['tradingview'].fetch_ideas,
                        symbol,
                        limit=10
                    )
                    
                    if ideas:
                        for idea in ideas:
                            article = {
                                'headline': idea.get('title', ''),
                                'content': idea.get('description', ''),
                                'url': idea.get('url', ''),
                                'published_at': idea.get('published_at', datetime.utcnow().isoformat()),
                                'source': 'TradingView',
                                'source_type': 'scraper',
                                'symbols': [symbol],
                                'category': 'analysis'
                            }
                            articles.append(article)
                    
                    await asyncio.sleep(2)  # Rate limiting for scraping
                    
            except Exception as e:
                logger.error(f"Error fetching from TradingView: {e}")
        
        return articles
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on content similarity"""
        unique_articles = []
        seen_hashes = set()
        
        for article in articles:
            # Create content hash
            content_for_hash = f"{article.get('headline', '')}{article.get('url', '')}"
            content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            if content_hash not in seen_hashes and content_hash not in self.processed_articles:
                # Check for similar content
                is_duplicate = False
                for existing_article in unique_articles:
                    if self._calculate_similarity(article, existing_article) > self.similarity_threshold:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_articles.append(article)
                    seen_hashes.add(content_hash)
                    self.processed_articles.add(content_hash)
        
        # Clean old processed articles
        if len(self.processed_articles) > 10000:
            # Keep only recent hashes (simple cleanup)
            self.processed_articles = set(list(self.processed_articles)[-5000:])
        
        return unique_articles
    
    def _calculate_similarity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate similarity between two articles"""
        headline1 = article1.get('headline', '').lower()
        headline2 = article2.get('headline', '').lower()
        
        if not headline1 or not headline2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(headline1.split())
        words2 = set(headline2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def _process_and_publish_data(self, raw_data: List[Dict[str, Any]]) -> int:
        """Enhanced processing with sentiment analysis and symbol extraction"""
        processed_count = 0
        
        for article in raw_data:
            try:
                # Basic validation
                is_valid, quality, issues = self._validate_data(article)
                
                if not is_valid and quality == DataQuality.CORRUPTED:
                    continue
                
                # Normalize article
                normalized_article = self._normalize_data(article)
                
                # Add sentiment analysis
                sentiment_data = self.sentiment_analyzer.analyze_sentiment(
                    normalized_article.get('content', ''),
                    normalized_article.get('headline', '')
                )
                normalized_article['sentiment_analysis'] = sentiment_data
                
                # Extract financial symbols
                symbols = self.symbol_extractor.extract_symbols(
                    normalized_article.get('content', ''),
                    normalized_article.get('headline', '')
                )
                
                if symbols:
                    normalized_article['extracted_symbols'] = symbols
                
                # Add processing metadata
                normalized_article.update({
                    'processing_timestamp': datetime.utcnow().isoformat(),
                    'data_quality': quality.value,
                    'validation_issues': issues,
                    'enhanced_processing': True
                })
                
                # Publish to appropriate topics
                await self.broker.publish_message("global_news", normalized_article)
                
                # Publish to symbol-specific topics if symbols found
                if symbols:
                    for symbol in symbols[:5]:  # Limit to top 5 symbols
                        symbol_article = normalized_article.copy()
                        symbol_article['target_symbol'] = symbol
                        await self.broker.publish_message(f"news_{symbol}", symbol_article)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
        
        return processed_count
    
    def get_source_health(self) -> Dict[str, Any]:
        """Get health status of all news sources"""
        source_health = {}
        
        for source in self.news_sources:
            health_data = {
                "name": source.name,
                "type": source.source_type,
                "priority": source.priority,
                "enabled": source.enabled,
                "update_frequency": source.update_frequency,
                "categories": source.categories
            }
            
            # Add client-specific health info
            if source.source_type == "api" and source.name.lower() in self.news_clients:
                health_data["client_available"] = True
            elif source.source_type == "rss":
                health_data["client_available"] = 'global_news' in self.news_clients
            elif source.source_type == "scraper":
                health_data["client_available"] = source.name.lower() in self.news_clients
            else:
                health_data["client_available"] = False
            
            source_health[source.name] = health_data
        
        return source_health