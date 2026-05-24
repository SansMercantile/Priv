# backend/data_sourcing/api_clients/finnhub_client.py

import os
import requests
from typing import Dict, Any, Optional, List

class FinnhubClient:
    """
    A client for interacting with the Finnhub.io REST API.
    Provides methods to fetch real-time quotes, company news, and other financial data.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the FinnhubClient.
        
        Args:
            api_key (Optional[str]): The Finnhub API key. If not provided,
                                     it will be read from the 'FINNHUB_API_KEY'
                                     environment variable.
        """
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("Finnhub API key not provided or found in environment variables.")
        self.base_url = "https://finnhub.io/api/v1"
        self.params = {"token": self.api_key}
        print("FinnhubClient initialized.")

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote data for a US stock.
        
        Args:
            symbol (str): The stock symbol (e.g., 'MSFT').
            
        Returns:
            Dict[str, Any]: A dictionary containing the quote data.
        """
        endpoint = "/quote"
        params = {**self.params, "symbol": symbol}
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        return {}

    def get_company_news(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        List company news for a given stock.
        
        Args:
            symbol (str): The stock symbol.
            from_date (str): From date in YYYY-MM-DD format.
            to_date (str): To date in YYYY-MM-DD format.
            
        Returns:
            List[Dict[str, Any]]: A list of news articles.
        """
        endpoint = "/company-news"
        params = {**self.params, "symbol": symbol, "from": from_date, "to": to_date}
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        return []

# Example Usage:
if __name__ == '__main__':
    # Make sure to set your API key as an environment variable before running
    # export FINNHUB_API_KEY="YOUR_API_KEY"
    
    if not os.getenv('FINNHUB_API_KEY'):
        print("Please set the FINNHUB_API_KEY environment variable to run this example.")
    else:
        finnhub_client = FinnhubClient()
        
        print("\nFetching real-time quote for MSFT...")
        msft_quote = finnhub_client.get_quote("MSFT")
        if msft_quote:
            print(f"MSFT Current Price: {msft_quote.get('c')}, High: {msft_quote.get('h')}, Low: {msft_quote.get('l')}")
        else:
            print("Failed to fetch quote for MSFT.")
            
        print("\nFetching company news for TSLA...")
        tsla_news = finnhub_client.get_company_news("TSLA", "2023-08-01", "2023-08-10")
        if tsla_news:
            print(f"Found {len(tsla_news)} news articles for TSLA.")
            print("First article headline:", tsla_news[0]['headline'])
        else:
            print("Failed to fetch news for TSLA.")
