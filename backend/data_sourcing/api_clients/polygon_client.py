# backend/data_sourcing/api_clients/polygon_client.py

import os
import requests
from typing import Dict, Any, Optional

class PolygonClient:
    """
    A client for interacting with the Polygon.io REST API.
    Handles authentication, request construction, and error handling for fetching
    various types of market data.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the PolygonClient.
        
        Args:
            api_key (Optional[str]): The Polygon.io API key. If not provided,
                                     it will be read from the 'POLYGON_API_KEY'
                                     environment variable.
        """
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon API key not provided or found in environment variables.")
        self.base_url = "https://api.polygon.io"
        print("PolygonClient initialized.")

    def get_aggregate_bars(self, ticker: str, multiplier: int, timespan: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Fetches aggregate bars (candles) for a ticker over a given date range.
        
        Args:
            ticker (str): The ticker symbol (e.g., 'AAPL').
            multiplier (int): The size of the timespan multiplier.
            timespan (str): The size of the time window (e.g., 'day', 'hour').
            from_date (str): The start of the aggregate time window (YYYY-MM-DD).
            to_date (str): The end of the aggregate time window (YYYY-MM-DD).
            
        Returns:
            Dict[str, Any]: The JSON response from the API.
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            "apiKey": self.api_key,
            "sort": "asc",
            "limit": 50000  # Max limit
        }
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        return {}

# Example Usage:
if __name__ == '__main__':
    # Make sure to set your API key as an environment variable before running
    # export POLYGON_API_KEY="YOUR_API_KEY"
    
    if not os.getenv('POLYGON_API_KEY'):
        print("Please set the POLYGON_API_KEY environment variable to run this example.")
    else:
        polygon_client = PolygonClient()
        
        print("\nFetching daily bars for AAPL...")
        aapl_daily_data = polygon_client.get_aggregate_bars(
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_date="2023-01-01",
            to_date="2023-01-31"
        )
        
        if aapl_daily_data.get('results'):
            print(f"Successfully fetched {aapl_daily_data['resultsCount']} daily bars for AAPL.")
            print("First bar:", aapl_daily_data['results'][0])
        else:
            print("Failed to fetch data for AAPL.")
