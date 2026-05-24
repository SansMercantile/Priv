import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os

# Advanced NewsAPI.ai helper functions are implemented directly in this module (no separate EventRegistry provider).

logger = logging.getLogger(__name__)

class NewsAPIClient:
    """
    A client for fetching financial news articles from multiple news APIs.
    Supports NewsAPI.ai (primary) and NewsAPI.org (secondary/backup).
    Can be configured to use real APIs or fall back to mock data.
    """
    def __init__(self,
                 api_key_ai: Optional[str] = None, # API key for NewsAPI.ai
                 api_key_org: Optional[str] = None, # API key for NewsAPI.org
                 base_url_ai: str = "https://api.newsapi.ai/api/v1/article/getArticles",
                 base_url_org: str = "https://newsapi.org/v2/everything",
                 use_mock: bool = True):
        """
        Initializes the NewsAPIClient with primary and secondary API configurations.

        Args:
            api_key_ai (Optional[str]): The API key for NewsAPI.ai. Defaults to NEWS_API_KEY_AI env var.
            api_key_org (Optional[str]): The API key for NewsAPI.org. Defaults to NEWS_API_KEY_ORG env var.
            base_url_ai (str): The base URL for NewsAPI.ai.
            base_url_org (str): The base URL for NewsAPI.org.
            use_mock (bool): If True, use mock data; otherwise, attempt to use real APIs (requires valid api_keys).
        """
        self.api_key_ai = api_key_ai if api_key_ai else os.getenv("NEWS_API_KEY_AI", "MOCK_API_KEY_AI")
        self.api_key_org = api_key_org if api_key_org else os.getenv("NEWS_API_KEY_ORG", "MOCK_API_KEY_ORG")
        self.base_url_ai = base_url_ai
        self.base_url_org = base_url_org

        # Auto-detect demo/invalid keys and force mock mode
        demo_keys = ["demo-news-api-key-ai", "demo-news-api-key-org", "MOCK_API_KEY_AI", "MOCK_API_KEY_ORG", "YOUR_NEWS_API_KEY"]
        if self.api_key_ai in demo_keys or self.api_key_org in demo_keys:
            self.use_mock = True
            logger.info("NewsAPIClient: Demo/invalid API keys detected. Using mock data mode.")
        else:
            self.use_mock = use_mock

        if self.use_mock:
            logger.info("NewsAPIClient initialized (using mock data).")
        else:
            if self.api_key_ai == "MOCK_API_KEY_AI":
                logger.warning("NewsAPI.ai key not found. Primary API unavailable.")
            if self.api_key_org == "MOCK_API_KEY_ORG":
                logger.warning("NewsAPI.org key not found. Secondary API unavailable.")
            logger.info("NewsAPIClient initialized (attempting real APIs).")

    def fetch_news(self,
                   query: Optional[str] = None,
                   symbols: Optional[List[str]] = None,
                   from_date: Optional[datetime] = None,
                   to_date: Optional[datetime] = None,
                   language: str = "en", # Defaulting to 'en' for simplicity; NewsAPI.ai uses 'eng'
                   sort_by: str = "publishedAt", # Defaulting to 'publishedAt' for simplicity
                   limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches news articles from primary (NewsAPI.ai) then secondary (NewsAPI.org) API,
        or mock data.

        Args:
            query (Optional[str]): A general search query.
            symbols (Optional[List[str]]): A list of relevant stock/currency symbols.
            from_date (Optional[datetime]): The start date for news articles.
            to_date (Optional[datetime]): The end date for news articles.
            language (str): The language of the articles.
            sort_by (str): How to sort articles.
            limit (int): Maximum number of articles to return.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a news article.
        """
        if self.use_mock:
            return self._fetch_news_mock(query, symbols, from_date, to_date, limit)
        
        # Build list of providers to try in-order. This allows rotating to the next provider on rate limits (429) or other transient errors.
        providers = []
        if self.api_key_ai != "MOCK_API_KEY_AI":
            providers.append(("newsapi_ai", self._fetch_from_newsapi_ai))
        if self.api_key_org != "MOCK_API_KEY_ORG":
            providers.append(("newsapi_org", self._fetch_from_newsapi_org))


        # If no real providers configured, return mock data or empty
        if not providers:
            logger.warning("No real news providers configured. Returning mock results.")
            return self._fetch_news_mock(query, symbols, from_date, to_date, limit)

        # Try each provider in order. If rate-limited (HTTP 429) or transient error occurs, fall back to the next provider.
        last_exception = None
        for name, fetch_fn in providers:
            logger.info(f"Attempting to fetch news from provider: {name}...")
            try:
                articles = fetch_fn(query, symbols, from_date, to_date, language, sort_by, limit)
                if articles:
                    logger.info(f"Fetched {len(articles)} articles from provider: {name}")
                    return articles
                # If provider returned an empty list (no results), continue to next provider
                logger.warning(f"Provider {name} returned no articles. Trying next provider.")
            except Exception as e:
                # Inspect for rate-limit specific behavior where possible
                try:
                    import requests
                    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None and e.response.status_code == 429:
                        logger.warning(f"Provider {name} is rate-limited (429). Moving to next provider.")
                        last_exception = e
                        continue
                except Exception:
                    pass
                logger.error(f"Error from provider {name}: {e}. Trying next provider if available.")
                last_exception = e
                continue

        # No provider returned results
        logger.warning("No real news could be fetched from any configured provider. Returning empty list.")
        if last_exception:
            logger.debug(f"Last provider exception: {last_exception}")
        return []

    def fetch_news_advanced(self,
                            query: Optional[str] = None,
                            keywords: Optional[List[str]] = None,
                            operator: str = "OR",
                            category: Optional[str] = None,
                            from_date: Optional[datetime] = None,
                            to_date: Optional[datetime] = None,
                            language: str = "en",
                            sort_by: str = "publishedAt",
                            limit: int = 20) -> List[Dict[str, Any]]:
        """Advanced query helper that composes complex queries (AND/OR) and category filters,
        then executes fetch_news using existing provider rotation."""
        q = query or ""
        if keywords:
            op = f" {operator} "
            joined = op.join([f'"{k}"' if ' ' in k else k for k in keywords])
            if q:
                q = f"{q} AND ({joined})"
            else:
                q = joined
        if category:
            q = f"{q} category:{category}" if q else f"category:{category}"

        # Reuse existing provider rotation and fetch logic
        return self.fetch_news(query=q, symbols=None, from_date=from_date, to_date=to_date, language=language, sort_by=sort_by, limit=limit)

    def _fetch_from_newsapi_ai(self, query: Optional[str], symbols: Optional[List[str]],
                               from_date: Optional[datetime], to_date: Optional[datetime],
                               language: str, sort_by: str, limit: int) -> List[Dict[str, Any]]:
        """Fetches from NewsAPI.ai."""
        params = {
            'query': query if query else '',
            'lang': language if language == 'en' else 'eng', # NewsAPI.ai uses 'eng' for English
            'sortBy': 'date' if sort_by == 'publishedAt' else sort_by, # Map 'publishedAt' to 'date'
            'articlesPageSize': limit,
            'apiKey': self.api_key_ai
        }
        if from_date:
            params['dateStart'] = from_date.strftime("%Y%m%d")
        if to_date:
            params['dateEnd'] = to_date.strftime("%Y%m%d")
        
        if symbols:
            if params['query']:
                params['query'] += " AND (" + " OR ".join(symbols) + ")"
            else:
                params['query'] = " OR ".join(symbols)

        try:
            response = requests.get(self.base_url_ai, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article_data in data.get('articles', {}).get('results', []): 
                articles.append({
                    "title": article_data.get('title'),
                    "content": article_data.get('body'), # NewsAPI.ai uses 'body' for full content
                    "source": article_data.get('source', {}).get('title'),
                    "published_at": article_data.get('pubDate'),
                    "url": article_data.get('url'),
                    "symbols": [] # NewsAPI.ai doesn't provide symbols directly, might need NLP to extract
                })
            logger.info(f"Fetched {len(articles)} articles from NewsAPI.ai.")
            return articles
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for NewsAPI.ai: {e}")
            raise # Re-raise to trigger fallback
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed for NewsAPI.ai: {e}")
            raise # Re-raise to trigger fallback

    def _fetch_from_newsapi_org(self, query: Optional[str], symbols: Optional[List[str]],
                                from_date: Optional[datetime], to_date: Optional[datetime],
                                language: str, sort_by: str, limit: int) -> List[Dict[str, Any]]:
        """Fetches from NewsAPI.org."""
        params = {
            'q': query if query else '',
            'language': language,
            'sortBy': sort_by,
            'pageSize': limit,
            'apiKey': self.api_key_org
        }
        if from_date:
            params['from'] = from_date.isoformat()
        if to_date:
            params['to'] = to_date.isoformat()
        
        if symbols:
            if params['q']:
                params['q'] += " OR ".join(symbols)
            else:
                params['q'] = " OR ".join(symbols)

        try:
            response = requests.get(self.base_url_org, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article_data in data.get('articles', []):
                articles.append({
                    "title": article_data.get('title'),
                    "content": article_data.get('description'), # NewsAPI.org uses 'description' for snippet
                    "full_content": article_data.get('content'), # NewsAPI.org uses 'content' for full text
                    "source": article_data.get('source', {}).get('name'),
                    "published_at": article_data.get('publishedAt'),
                    "url": article_data.get('url'),
                    "symbols": [] # NewsAPI.org doesn't provide symbols directly, might need NLP to extract
                })
            logger.info(f"Fetched {len(articles)} articles from NewsAPI.org.")
            return articles
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for NewsAPI.org: {e}")
            raise # Re-raise to trigger fallback
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode failed for NewsAPI.org: {e}")
            raise # Re-raise to trigger fallback



    def _fetch_news_mock(self, query: Optional[str], symbols: Optional[List[str]],
                         from_date: Optional[datetime], to_date: Optional[datetime],
                         limit: int) -> List[Dict[str, Any]]:
        """Private method to generate mock news articles."""
        mock_news_articles = [
            {
                "title": "Central Bank Hints at Rate Hike Amid Inflation Concerns",
                "content": "Speculation grows as the central bank's latest statement suggests a hawkish stance to combat rising inflation, potentially impacting currency markets. This might lead to USD strength.",
                "source": "Financial Times",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "symbols": ["EURUSD", "USDJPY", "XAUUSD"]
            },
            {
                "title": "Tech Giant's Earnings Beat Expectations, Stock Jumps",
                "content": "Shares of a leading technology company surged today after reporting quarterly earnings that surpassed analyst forecasts, driven by strong cloud services growth. AAPL and GOOGL are up.",
                "source": "Bloomberg",
                "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                "symbols": ["GOOGL", "AAPL", "MSFT"]
            },
            {
                "title": "Geopolitical Tensions Escalate, Oil Prices Spike on Middle East Conflict",
                "content": "Renewed tensions in a key producing region have sent crude oil prices climbing, raising concerns about global supply chains and energy costs. Brent futures rallied.",
                "source": "Reuters",
                "published_at": (datetime.now() - timedelta(hours=10)).isoformat(),
                "symbols": ["XTIUSD", "BRENT"]
            },
            {
                "title": "Commodity Prices Steady After Recent Volatility, Gold holds support",
                "content": "Following a week of significant swings, various commodity markets, including copper and wheat, show signs of stabilization as supply concerns ease. Gold, often a safe haven, saw some buying interest.",
                "source": "Wall Street Journal",
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "symbols": ["XAUUSD", "XAGUSD"]
            },
            {
                "title": "Retail Sales Figures Show Unexpected Decline, impacting consumer confidence",
                "content": "Official data released this morning indicated a surprising drop in retail sales last month, raising questions about consumer spending and economic growth prospects in Europe.",
                "source": "MarketWatch",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "symbols": ["EURUSD", "GBPUSD"]
            },
            {
                "title": "Major Stock Market Rebound: Investors Shrug Off Inflation Fears",
                "content": "The Dow Jones Industrial Average experienced a significant rally, recovering much of its recent losses as investors appeared to downplay ongoing inflation concerns, signaling renewed optimism.",
                "source": "Yahoo Finance",
                "published_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                "symbols": ["^DJI", "^SPX"]
            },
            {
                "title": "Forex Market Update: Yen Weakens Against Dollar on Dovish Comments",
                "content": "The Japanese Yen continued its decline against the US Dollar today, following comments from the Bank of Japan indicating a cautious approach to monetary tightening, reinforcing interest rate differentials.",
                "source": "FXStreet",
                "published_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "symbols": ["USDJPY"]
            },
            {
                "title": "Cryptocurrency Volatility Spikes: Bitcoin Drops Below Key Support",
                "content": "Bitcoin and other major cryptocurrencies experienced sharp declines overnight, with Bitcoin breaking below a crucial support level, triggering further sell-offs across the digital asset market.",
                "source": "CoinDesk",
                "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                "symbols": ["BTCUSD", "ETHUSD"]
            }
        ]

        filtered_news = []
        for article in mock_news_articles:
            article_time = datetime.fromisoformat(article["published_at"])

            # Date filtering
            if from_date and article_time < from_date:
                continue
            if to_date and article_time > to_date:
                continue

            # Query filtering (combining query and symbols)
            full_query_match = False
            search_terms = []
            if query:
                search_terms.append(query.lower())
            if symbols:
                search_terms.extend([s.lower() for s in symbols])
            
            article_text = (article["title"] + " " + article.get("content", "") + " ".join(article.get("symbols", []))).lower()
            if search_terms:
                if any(term in article_text for term in search_terms):
                    full_query_match = True
            else: # If no query or symbols specified, match all mock articles
                full_query_match = True

            if not full_query_match:
                continue

            filtered_news.append(article)
            if len(filtered_news) >= limit:
                break
        
        logger.info(f"Mock news fetch completed. Found {len(filtered_news)} articles.")
        return filtered_news

# Example Usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # --- Test Mock News Client ---
    print("\n--- Testing Mock News Client ---")
    mock_news_client = NewsAPIClient(use_mock=True)

    print("\n--- Fetching recent news (mock, default limit) ---")
    recent_news = mock_news_client.fetch_news()
    for article in recent_news:
        print(f"Title: {article['title']}\n  Source: {article['source']}, Published: {article['published_at']}\n  Symbols: {article.get('symbols')}\n---")

    print("\n--- Fetching news about 'inflation' for 'EURUSD' ---")
    eurusd_inflation_news = mock_news_client.fetch_news(query="inflation", symbols=["EURUSD"])
    if eurusd_inflation_news:
        for article in eurusd_inflation_news:
            print(f"Title: {article['title']}\n  Source: {article['source']}\n---")
    else:
        print("No mock news found for 'inflation' and 'EURUSD'.")

    # --- Test Real News Client (Requires NEWS_API_KEY_AI/ORG env vars set and internet access) ---
    print("\n--- Testing Real News Client (if API Keys are configured) ---")
    # To test this, you need NewsAPI.ai and/or NewsAPI.org API keys set as environment variables.
    # NEWS_API_KEY_AI="YOUR_ACTUAL_NEWSAPI_KEY_AI"
    # NEWS_API_KEY_ORG="YOUR_ACTUAL_NEWSAPI_KEY_ORG"
    real_news_client = NewsAPIClient(use_mock=False)

    try:
        if os.getenv("NEWS_API_KEY_AI") or os.getenv("NEWS_API_KEY_ORG"):
            print("\n--- Fetching real news about 'economy' from primary/secondary API ---")
            real_economy_news = real_news_client.fetch_news(query="economy", limit=5, to_date=datetime.now()) # to_date is important for real API
            if real_economy_news:
                for article in real_economy_news:
                    print(f"Title: {article['title']}\n  Source: {article['source']}, Published: {article['published_at']}\n  URL: {article.get('url')}\n---")
            else:
                print("No real news found for 'economy' (or API limits reached/keys invalid).")
        else:
            print("Skipping real news client test: Neither NEWS_API_KEY_AI nor NEWS_API_KEY_ORG environment variables set.")
    except Exception as e:
        print(f"An error occurred during real news client test: {e}")