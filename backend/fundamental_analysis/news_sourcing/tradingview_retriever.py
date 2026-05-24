# backend/fundamental_analysis/news_sourcing/tradingview_retriever.py

import logging
from typing import List, Dict, Optional
import asyncio

# Try Playwright first (recommended)
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = None

# Fallback to Selenium if Playwright not available
if not PLAYWRIGHT_AVAILABLE:
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, WebDriverException
        SELENIUM_AVAILABLE = True
    except ImportError:
        SELENIUM_AVAILABLE = False
        webdriver = None
        class WebDriverException(Exception):
            pass
        class TimeoutException(Exception):
            pass
else:
    SELENIUM_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None

if not PLAYWRIGHT_AVAILABLE and SELENIUM_AVAILABLE:
    try:
        from backend.utils.web_scraping_utils import get_chrome_driver_options
    except ImportError:
        def get_chrome_driver_options():
            return None

logger = logging.getLogger(__name__)


class TradingViewRetriever:
    """
    Retrieves market analysis and ideas from TradingView's "Ideas" section
    using Playwright (recommended) with fallback to Selenium.
    """
    def __init__(self):
        self.base_url = "https://www.tradingview.com/symbols"
        self.browser = None
        self.context = None
        self.use_playwright = PLAYWRIGHT_AVAILABLE
        self.driver = None  # For Selenium fallback

    async def _initialize_playwright_browser(self):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            # Use Chromium for best TradingView compatibility
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            logger.info("Playwright browser initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.use_playwright = False
            return False

    def _initialize_selenium_driver(self):
        """Fallback: Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available. Cannot initialize fallback driver.")
            return False
        try:
            options = get_chrome_driver_options()
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized as fallback.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {e}")
            return False

    async def _close_playwright_browser(self):
        """Close Playwright browser"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Playwright browser closed.")
        except Exception as e:
            logger.warning(f"Error closing Playwright browser: {e}")

    def _close_selenium_driver(self):
        """Close Selenium driver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.info("Selenium driver closed.")
        except Exception as e:
            logger.warning(f"Error closing Selenium driver: {e}")

    async def fetch_ideas_with_playwright(self, symbol: str, limit: int = 10) -> List[Dict[str, str]]:
        """Fetch ideas using Playwright (modern, reliable method)"""
        if not self.browser:
            if not await self._initialize_playwright_browser():
                return []

        target_url = f"{self.base_url}/{symbol}/ideas/"
        logger.info(f"Fetching TradingView ideas (Playwright) from: {target_url}")
        
        scraped_ideas = []
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                page = await self.context.new_page()
                
                try:
                    # Navigate with timeout and wait for network to settle
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Wait for idea cards to appear with explicit selector
                    try:
                        await page.wait_for_selector("div.tv-feed__item", timeout=15000)
                        logger.debug(f"Idea cards found on attempt {attempt}")
                    except PlaywrightTimeoutError:
                        logger.warning(f"Attempt {attempt}/{max_attempts}: Timeout waiting for idea cards")
                        if attempt == max_attempts:
                            logger.error(f"Failed to load TradingView ideas for {symbol} after {max_attempts} attempts")
                            return []
                        await asyncio.sleep(2 * attempt)
                        continue

                    # Get page content
                    content = await page.content()
                    
                    # Parse with BeautifulSoup
                    if not BS4_AVAILABLE:
                        logger.error("BeautifulSoup not available for parsing")
                        return []
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    idea_cards = soup.find_all('div', class_='tv-feed__item', limit=limit)
                    
                    for card in idea_cards:
                        try:
                            title_tag = card.find('a', class_='tv-widget-idea__title')
                            author_tag = card.find('span', class_='tv-card-user-info__name')
                            summary_tag = card.find('p', class_='tv-widget-idea__description-row')
                            
                            if title_tag and author_tag:
                                title = title_tag.text.strip()
                                author = author_tag.text.strip()
                                summary = summary_tag.text.strip() if summary_tag else "No summary available."
                                idea_url = "https://www.tradingview.com" + title_tag.get('href', '')
                                
                                scraped_ideas.append({
                                    "title": title,
                                    "author": author,
                                    "summary": summary,
                                    "url": idea_url,
                                    "source": "TradingView"
                                })
                        except Exception as parse_error:
                            logger.debug(f"Error parsing individual idea card: {parse_error}")
                            continue
                    
                    if scraped_ideas:
                        logger.info(f"Successfully scraped {len(scraped_ideas)} ideas from TradingView")
                        break
                    else:
                        logger.warning(f"Attempt {attempt}/{max_attempts}: No ideas found, retrying...")
                        if attempt < max_attempts:
                            await asyncio.sleep(2 * attempt)
                            
                finally:
                    await page.close()
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_attempts} error: {e}")
                if attempt == max_attempts:
                    logger.error(f"Failed to fetch TradingView ideas after {max_attempts} attempts: {e}")
                else:
                    await asyncio.sleep(2 * attempt)
        
        return scraped_ideas

    def _fetch_ideas_with_selenium(self, symbol: str, limit: int = 10) -> List[Dict[str, str]]:
        """Fallback: Fetch ideas using Selenium (slower but compatible)"""
        if not self.driver:
            if not self._initialize_selenium_driver():
                return []
        
        target_url = f"{self.base_url}/{symbol}/ideas/"
        logger.info(f"Fetching TradingView ideas (Selenium fallback) from: {target_url}")
        
        scraped_ideas = []
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.driver.get(target_url)
                wait = WebDriverWait(self.driver, 20)
                
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tv-feed__item")))
                    logger.debug(f"Idea cards found on attempt {attempt}")
                except TimeoutException:
                    logger.warning(f"Attempt {attempt}/{max_attempts}: Timeout waiting for idea cards")
                    if attempt == max_attempts:
                        logger.error(f"Failed to load TradingView ideas for {symbol} after {max_attempts} attempts")
                        return []
                    import time
                    time.sleep(2 * attempt)
                    continue
                
                # Wait for lazy-loaded content
                import time
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                idea_cards = soup.find_all('div', class_='tv-feed__item', limit=limit)
                
                for card in idea_cards:
                    try:
                        title_tag = card.find('a', class_='tv-widget-idea__title')
                        author_tag = card.find('span', class_='tv-card-user-info__name')
                        summary_tag = card.find('p', class_='tv-widget-idea__description-row')
                        
                        if title_tag and author_tag:
                            title = title_tag.text.strip()
                            author = author_tag.text.strip()
                            summary = summary_tag.text.strip() if summary_tag else "No summary available."
                            idea_url = "https://www.tradingview.com" + title_tag.get('href', '')
                            
                            scraped_ideas.append({
                                "title": title,
                                "author": author,
                                "summary": summary,
                                "url": idea_url,
                                "source": "TradingView"
                            })
                    except Exception as parse_error:
                        logger.debug(f"Error parsing individual idea card: {parse_error}")
                        continue
                
                if scraped_ideas:
                    logger.info(f"Successfully scraped {len(scraped_ideas)} ideas from TradingView")
                    break
                else:
                    logger.warning(f"Attempt {attempt}/{max_attempts}: No ideas found, retrying...")
                    if attempt < max_attempts:
                        import time
                        time.sleep(2 * attempt)
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_attempts} error: {e}")
                if attempt == max_attempts:
                    logger.error(f"Failed to fetch TradingView ideas after {max_attempts} attempts: {e}")
                else:
                    import time
                    time.sleep(2 * attempt)
        
        return scraped_ideas

    async def fetch_ideas(self, symbol: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch trading ideas for a given symbol using Playwright or Selenium.
        
        Args:
            symbol (str): Symbol to fetch ideas for (e.g., 'EURUSD', 'AAPL')
            limit (int): Maximum number of ideas to retrieve
            
        Returns:
            List[Dict[str, str]]: List of idea dictionaries with title, author, summary, url
        """
        if self.use_playwright:
            return await self.fetch_ideas_with_playwright(symbol, limit)
        else:
            # Run Selenium in thread since it's not async
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._fetch_ideas_with_selenium,
                symbol,
                limit
            )

    async def close(self):
        """Clean up resources"""
        if self.use_playwright:
            await self._close_playwright_browser()
        else:
            self._close_selenium_driver()

    def __del__(self):
        """Ensure cleanup on deletion"""
        if not self.use_playwright and self.driver:
            try:
                self.driver.quit()
            except:
                pass


# Example usage for standalone testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        logging.basicConfig(level=logging.INFO)
        retriever = TradingViewRetriever()
        
        try:
            eurusd_ideas = await retriever.fetch_ideas("EURUSD", limit=5)
            
            if eurusd_ideas:
                print("\n--- Scraped TradingView Ideas for EURUSD ---")
                for i, idea in enumerate(eurusd_ideas):
                    print(f"{i+1}. Title: {idea['title']}")
                    print(f"   Author: {idea['author']}")
                    print(f"   Summary: {idea['summary']}")
                    print(f"   URL: {idea['url']}")
                    print("-" * 20)
            else:
                print("Could not scrape any ideas for EURUSD.")
        finally:
            await retriever.close()
    
    asyncio.run(main())