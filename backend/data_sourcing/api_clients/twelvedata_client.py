# backend/data_sourcing/api_clients/twelvedata_client.py

import os
import requests
from typing import Dict, Any, Optional

class TwelveDataClient:
    """
    A client for interacting with the Twelve Data API.
    Specializes in fetching time series data for a wide range of assets.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the TwelveDataClient.
        
        Args:
            api_key (Optional[str]): The Twelve Data API key. If not provided,
                                     it will be read from the 'TWELVEDATA_API_KEY'
                                     environment variable.
        """
        self.api_key = api_key or os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("Twelve Data API key not provided or found in environment variables.")
        self.base_url = "https://api.twelvedata.com"
        print("TwelveDataClient initialized.")

    def get_time_series(self, symbol: str, interval: str, outputsize: int = 30) -> Dict[str, Any]:
        """
        Fetches time series data for a given symbol.
        
        Args:
            symbol (str): The instrument ticker (e.g., 'EUR/USD', 'GOOGL').
            interval (str): The interval between data points 
                            (e.g., '1min', '5min', '1h', '4h', '1day').
            outputsize (int): The number of data points to retrieve.
            
        Returns:
            Dict[str, Any]: The JSON response from the API.
        """
        endpoint = "/time_series"
        params = {
            "apikey": self.api_key,
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        return {}

# Example Usage:
if __name__ == '__main__':
    # Make sure to set your API key as an environment variable before running
    # export TWELVEDATA_API_KEY="YOUR_API_KEY"

    if not os.getenv('TWELVEDATA_API_KEY'):
        print("Please set the TWELVEDATA_API_KEY environment variable to run this example.")
    else:
        twelve_data_client = TwelveDataClient()
        
        print("\nFetching 1-hour time series for EUR/USD...")
        eurusd_data = twelve_data_client.get_time_series(
            symbol="EUR/USD",
            interval="1h",
            outputsize=10
        )
        
        if eurusd_data.get('values'):
            print(f"Successfully fetched {len(eurusd_data['values'])} data points for EUR/USD.")
            print("Latest data point:", eurusd_data['values'][0])
        else:
            print(f"Failed to fetch data for EUR/USD. Response: {eurusd_data}")
