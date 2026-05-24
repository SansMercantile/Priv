# backend/data_sourcing/global_news_ingestor.py

import logging
import asyncio
from typing import List, Dict, Any, Optional

# Make gdeltdoc optional
try:
    from gdeltdoc import GdeltDoc, Filters
    GDELT_AVAILABLE = True
except ImportError:
    GDELT_AVAILABLE = False
    GdeltDoc = None
    Filters = None
    logger = logging.getLogger(__name__)
    logger.warning("gdeltdoc not available. GDELT news analysis will be disabled. Using RSS feeds only.")

from backend.data_sourcing.rss_retriever import RSSRetriever

logger = logging.getLogger(__name__)

# --- Expanded and Categorized List of High-Quality RSS Feeds ---
RSS_FEED_CONFIG = {
    # Major Global News
    "Reuters_World": "http://feeds.reuters.com/Reuters/worldNews",
    "Reuters_Business": "http://feeds.reuters.com/reuters/businessNews",
    "AP_News_World": "https://apnews.com/hub/world-news/rss",
    "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC_Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "AlJazeera_English": "https://www.aljazeera.com/xml/rss/all.xml",
    "NYT_World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "NYT_Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "TheGuardian_World": "https://www.theguardian.com/world/rss",
    "TheGuardian_Business": "https://www.theguardian.com/business/rss",

    # Financial News
    "FT_World": "https://www.ft.com/world?format=rss",
    "FT_Markets": "https://www.ft.com/markets?format=rss",
    "WSJ_World": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "WSJ_Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Bloomberg_Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "TheEconomist_Finance": "https://www.economist.com/finance-and-economics/rss.xml",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "CNBC_World": "https://www.cnbc.com/id/100727362/device/rss/rss.html",

    # Regional News
    "DerSpiegel_International": "https://www.spiegel.de/international/index.rss", # Germany
    "LeMonde": "https://www.lemonde.fr/rss/en_continu.xml", # France
    "TimesOfIndia_World": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", # India
    "Globo": "https://g1.globo.com/rss/g1/", # Brazil (in Portuguese)

    # Supranational Organizations
    "UN_News": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    "WorldBank_News": "https://www.worldbank.org/en/news/all.rss", # World Bank
    "ECB_Press": "https://www.ecb.europa.eu/rss/press.html", # European Central Bank
}


class GlobalNewsIngestor:
    """
    Ingests global news data from various sources, including GDELT and a curated list of RSS feeds.
    """
    def __init__(self):
        self.gdelt_client = GdeltDoc() if GDELT_AVAILABLE else None
        self.rss_retriever = RSSRetriever()
        logger.info("GlobalNewsIngestor initialized with GDELTClient and RSSRetriever.")

    async def fetch_gdelt_articles(self, query: str, timespan: str = "24h", num_results: int = 100) -> List[Dict[str, Any]]:
        """ Fetches articles from GDELT. """
        logger.info(f"Fetching GDELT articles with query: '{query}', timespan: {timespan}...")
        if not GDELT_AVAILABLE or not self.gdelt_client:
            logger.warning("GDELT client not available. Returning empty list.")
            return []
        try:
            filters = Filters(
                keyword=query,
                timespan=timespan,
                num_records=num_results
            )
            articles_df = await asyncio.to_thread(self.gdelt_client.article_search, filters)
            if articles_df is None or articles_df.empty:
                return []
            
            # Convert DataFrame to list of dicts
            return articles_df.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching articles from GDELT: {e}", exc_info=True)
            return []

    async def fetch_all_rss_feeds(self, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches articles from all configured RSS feeds concurrently.
        """
        logger.info(f"Fetching all {len(RSS_FEED_CONFIG)} configured RSS feeds...")
        tasks = [self.rss_retriever.fetch_feed(url, limit=limit_per_feed) for url in RSS_FEED_CONFIG.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for res in results:
            if isinstance(res, list):
                all_articles.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"An error occurred while fetching an RSS feed: {res}")
        
        logger.info(f"Fetched a total of {len(all_articles)} articles from all RSS feeds.")
        return all_articles

    async def fetch_all_rss_articles(self, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        """
        Alias for fetch_all_rss_feeds to keep compatibility with news_api endpoints.
        """
        return await self.fetch_all_rss_feeds(limit_per_feed)

# Example Usage
async def main():
    logging.basicConfig(level=logging.INFO)
    ingestor = GlobalNewsIngestor()

    print("\n--- Fetching All RSS Feeds ---")
    all_news = await ingestor.fetch_all_rss_feeds(limit_per_feed=2)
    
    if all_news:
        # Print a sample of the fetched articles
        for i, article in enumerate(all_news[:5]):
            print(f"{i+1}. [{article.get('source', 'Unknown Source').split('/')[2]}] {article.get('headline')}")
    else:
        print("No news fetched from RSS feeds.")

if __name__ == '__main__':
    asyncio.run(main())
