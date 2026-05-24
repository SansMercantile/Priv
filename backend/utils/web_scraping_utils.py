# backend/utils/web_scraping_utils.py

import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any, Tuple
import logging

# Make selenium optional
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    ChromeOptions = None
    ChromeService = None
    logger = logging.getLogger(__name__)
    logger.warning("Selenium not available. Web scraping features will be disabled.")

logger = logging.getLogger(__name__)

def get_chrome_driver_options():
    """
    Configures and returns ChromeOptions for Selenium WebDriver in headless mode.
    Returns None if Selenium is not available.
    """
    if not SELENIUM_AVAILABLE or ChromeOptions is None:
        logger.warning("Selenium not available. Cannot create Chrome driver options.")
        return None
    
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return options


def clean_scraped_dataframe(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Standardizes and cleans scraped DataFrames.
    """
    df.columns = [col.lower().replace('<', '').replace('>', '').replace('*', '').replace('.', '').replace(' ', '_') for col in df.columns]

    df.rename(columns={
        'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 
        'close': 'Close', 'vol': 'Volume', 'volume': 'Volume'
    }, inplace=True)
    
    if 'Adj Close' in df.columns:
        df.drop(columns=['Adj Close'], inplace=True)

    date_col_candidates = ['Date']
    actual_date_col = next((col for col in date_col_candidates if col in df.columns), None)
    
    if not actual_date_col:
        raise ValueError("DataFrame must contain a 'Date' column.")

    df[actual_date_col] = pd.to_datetime(df[actual_date_col], errors='coerce')
    df.dropna(subset=[actual_date_col], inplace=True)
    df.set_index(actual_date_col, inplace=True)
    df.index.name = 'Date'
    df.sort_index(inplace=True)

    def _clean_numeric_value(value: Any) -> Union[float, Any]:
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            if value in ['-', '', 'n/a']:
                return np.nan 
        try:
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    STANDARD_OHLCV_COLS = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in STANDARD_OHLCV_COLS:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(_clean_numeric_value)
        else: 
            df[col] = np.nan

    df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)
    
    if df.empty:
        logger.warning(f"Cleaned DataFrame for {symbol} ({timeframe}) is empty.")
    
    return df