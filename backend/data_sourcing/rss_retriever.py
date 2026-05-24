# backend/data_sourcing/rss_retriever.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import feedparser
import asyncio
import requests
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

class RSSRetriever:
    """
    Retrieves news and updates from RSS feeds with robust error handling.
    Gracefully handles malformed XML, encoding issues, and unavailable feeds.
    """
    
    # List of feeds known to have issues
    PROBLEMATIC_FEEDS = {
        "https://www.who.int/rss-feeds/news-en.xml": "Known XML encoding issues",
        "http://www.asahi.com/ajw/rss2.xml": "Malformed feed structure",
        "https://feeds.bloomberg.com/": "Rate limiting",
    }
    
    def __init__(self):
        logger.info("RSSRetriever initialized with robust error handling.")
        self.timeout = 10
        self.headers = {
            'User-Agent': 'SansMercantile/1.0 (+https://github.com/sans-mercantile)',
            'Accept': 'application/rss+xml, application/atom+xml, */*'
        }
        self.failed_feeds = {}  # Track feeds that consistently fail

    def _is_xml_well_formed(self, content: str) -> bool:
        """Quick check if XML is well-formed"""
        try:
            ET.fromstring(content[:5000])  # Check first 5KB
            return True
        except ET.ParseError:
            return False

    def _extract_encoding(self, raw_bytes: bytes) -> str:
        """Extract encoding from XML declaration"""
        try:
            header = raw_bytes[:200].decode('latin1', errors='ignore')
            if 'encoding=' in header:
                start = header.find('encoding=') + 9
                end = header.find('"', start)
                if end > start:
                    return header[start:end]
        except:
            pass
        return 'utf-8'

    async def fetch_feed(self, rss_url: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches and parses a single RSS feed with comprehensive error handling.
        
        Args:
            rss_url (str): The URL of the RSS feed
            limit (int): Maximum number of entries to return
            
        Returns:
            List[Dict[str, Any]]: List of parsed articles, empty if all parsing fails
        """
        logger.info(f"Fetching RSS feed from: {rss_url} (limit: {limit})")
        
        # Check if feed is known to be problematic
        if rss_url in self.PROBLEMATIC_FEEDS:
            logger.warning(f"Feed {rss_url} is known to have issues: {self.PROBLEMATIC_FEEDS[rss_url]}")
        
        # If feed failed too many times, skip it
        if rss_url in self.failed_feeds and self.failed_feeds[rss_url] >= 3:
            logger.warning(f"Feed {rss_url} has failed 3+ times. Skipping...")
            return []
        
        articles = []
        
        try:
            # Try 1: Direct parse with feedparser
            try:
                logger.debug(f"Attempt 1: Direct feedparser parse for {rss_url}")
                feed = await asyncio.to_thread(feedparser.parse, rss_url, timeout=self.timeout)
                
                if feed.bozo and isinstance(feed.bozo_exception, feedparser.CharacterEncodingOverride):
                    # This is usually harmless, continue
                    logger.debug(f"Encoding override for {rss_url}, continuing...")
                elif feed.bozo:
                    logger.warning(f"Feed parsing warning for {rss_url}: {feed.bozo_exception}")
                
                articles = self._parse_feed_entries(feed, rss_url, limit)
                if articles:
                    logger.info(f"Fetched {len(articles)} articles from {rss_url}")
                    return articles
                    
            except Exception as e:
                logger.debug(f"Direct feedparser parse failed: {e}")
            
            # Try 2: Fetch raw content and handle encoding issues
            try:
                logger.debug(f"Attempt 2: Raw fetch with encoding handling for {rss_url}")
                response = await asyncio.to_thread(
                    requests.get,
                    rss_url,
                    timeout=self.timeout,
                    headers=self.headers
                )
                response.raise_for_status()
                
                # Detect encoding from XML declaration
                detected_encoding = self._extract_encoding(response.content)
                
                # Decode with detected encoding and fallbacks
                for encoding in [detected_encoding, 'utf-8', 'iso-8859-1', 'windows-1252']:
                    try:
                        raw_text = response.content.decode(encoding, errors='replace')
                        
                        # Quick well-formed check
                        if not self._is_xml_well_formed(raw_text):
                            logger.debug(f"XML malformed with {encoding}, trying next...")
                            continue
                        
                        # Try to parse
                        feed = await asyncio.to_thread(feedparser.parse, raw_text)
                        
                        articles = self._parse_feed_entries(feed, rss_url, limit)
                        if articles:
                            logger.info(f"Fetched {len(articles)} articles from {rss_url} using {encoding}")
                            return articles
                            
                    except Exception as enc_e:
                        logger.debug(f"Encoding {encoding} failed: {enc_e}")
                        continue
                        
            except requests.RequestException as req_e:
                logger.warning(f"Request failed for {rss_url}: {req_e}")
                self.failed_feeds[rss_url] = self.failed_feeds.get(rss_url, 0) + 1
            except Exception as e:
                logger.warning(f"Raw fetch fallback failed for {rss_url}: {e}")
                self.failed_feeds[rss_url] = self.failed_feeds.get(rss_url, 0) + 1
            
            # Try 3: Use feedparser's built-in error recovery
            try:
                logger.debug(f"Attempt 3: Feedparser error recovery for {rss_url}")
                feed = await asyncio.to_thread(feedparser.parse, rss_url)
                # Force entry parsing even if bozo
                articles = self._parse_feed_entries(feed, rss_url, limit, force=True)
                if articles:
                    logger.info(f"Fetched {len(articles)} articles from {rss_url} (with error recovery)")
                    return articles
            except Exception as e:
                logger.debug(f"Error recovery failed: {e}")
            
            # All attempts failed
            logger.error(f"All parsing methods failed for {rss_url}")
            self.failed_feeds[rss_url] = self.failed_feeds.get(rss_url, 0) + 1
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error fetching RSS feed {rss_url}: {e}", exc_info=True)
            return []

    def _parse_feed_entries(self, feed, rss_url: str, limit: int, force: bool = False) -> List[Dict[str, Any]]:
        """
        Parse feed entries with robust error handling.
        
        Args:
            feed: feedparser feed object
            rss_url: Source URL for logging
            limit: Max entries to parse
            force: If True, parse even if feed.bozo is True
            
        Returns:
            List of parsed articles
        """
        articles = []
        
        # Check if feed has entries
        if not hasattr(feed, 'entries') or not feed.entries:
            logger.warning(f"No entries found in feed {rss_url}")
            return []
        
        for i, entry in enumerate(feed.entries[:limit]):
            try:
                # Safely extract fields
                title = self._safe_get(entry, ['title', 'summary', 'name'], 'No Title')
                
                # Extract published date
                published_date = self._extract_date(entry)
                
                # Extract content
                content = self._extract_content(entry)
                
                # Extract URL
                url = self._safe_get(entry, ['link', 'id', 'url'], rss_url)
                
                articles.append({
                    "source": url,
                    "headline": title,
                    "content": content,
                    "full_content_url": url,
                    "category": self._safe_get(entry, ['category', 'tags'], 'rss_general'),
                    "sentiment": "neutral",
                    "timestamp": published_date,
                    "language": self._safe_get(entry, ['language', 'lang'], 'en'),
                })
                
            except Exception as entry_error:
                logger.debug(f"Error parsing entry {i} from {rss_url}: {entry_error}")
                # Continue with next entry instead of failing
                continue
        
        if articles:
            logger.debug(f"Successfully parsed {len(articles)} entries from {rss_url}")
        else:
            logger.warning(f"No articles successfully parsed from {rss_url}")
        
        return articles

    def _safe_get(self, obj, keys, default=None):
        """Safely extract field from object using multiple possible keys"""
        if isinstance(keys, str):
            keys = [keys]
        
        for key in keys:
            try:
                if hasattr(obj, key):
                    value = getattr(obj, key)
                    if value:
                        return str(value).strip()
                elif isinstance(obj, dict) and key in obj:
                    value = obj[key]
                    if value:
                        return str(value).strip()
            except:
                continue
        
        return default

    def _extract_date(self, entry) -> Optional[str]:
        """Extract and parse publication date"""
        try:
            # Try multiple date fields
            for date_field in ['published', 'updated', 'pubDate', 'date']:
                if hasattr(entry, date_field):
                    date_val = getattr(entry, date_field)
                    if date_val:
                        return str(date_val)
                        
                # Try parsed versions
                parsed_field = f"{date_field}_parsed"
                if hasattr(entry, parsed_field):
                    parsed = getattr(entry, parsed_field)
                    if parsed:
                        try:
                            dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                            return dt.isoformat()
                        except:
                            pass
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting date: {e}")
            return None

    def _extract_content(self, entry) -> str:
        """Extract content from entry"""
        try:
            # Try structured content field
            if hasattr(entry, 'content') and entry.content:
                if isinstance(entry.content, list):
                    return str(entry.content[0].get('value', ''))
                return str(entry.content)
            
            # Try summary
            if hasattr(entry, 'summary') and entry.summary:
                return str(entry.summary)
            
            # Try description
            if hasattr(entry, 'description') and entry.description:
                return str(entry.description)
            
            return ''
        except Exception as e:
            logger.debug(f"Error extracting content: {e}")
            return ''


# Example Usage (for testing RSSRetriever in isolation)
async def main_rss_retriever_test():
    logging.basicConfig(level=logging.INFO)
    retriever = RSSRetriever()

    who_news_feed = "https://www.who.int/rss-feeds/news-en.xml"
    imf_news_feed = "https://www.imf.org/rss/external.xml"
    
    print("\n--- Testing WHO News RSS Feed ---")
    who_articles = await retriever.fetch_feed(who_news_feed, limit=3)
    if who_articles:
        for article in who_articles:
            print(f"WHO Article: {article['headline']}\n  Source: {article['source']}\n  Published: {article['timestamp']}")
            print("-" * 20)
    else:
        print("No articles fetched from WHO RSS.")

    print("\n--- Testing IMF News RSS Feed ---")
    imf_articles = await retriever.fetch_feed(imf_news_feed, limit=3)
    if imf_articles:
        for article in imf_articles:
            print(f"IMF Article: {article['headline']}\n  Source: {article['source']}\n  Published: {article['timestamp']}")
            print("-" * 20)
    else:
        print("No articles fetched from IMF RSS.")

if __name__ == '__main__':
    asyncio.run(main_rss_retriever_test())