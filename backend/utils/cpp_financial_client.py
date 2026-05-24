# priv/backend/utils/cpp_financial_client.py

import httpx # Using httpx for async operations
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CppFinancialClient:
    """
    Client to interact with the C++ Financial Calculation Microservice.
    It communicates via HTTP/REST.
    """
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        # Use a persistent async client for better performance in a long-running application
        self.client = httpx.AsyncClient()
        logger.info(f"Initialized CppFinancialClient with base URL: {self.base_url}")

    async def check_health(self) -> bool:
        """Checks the health of the C++ microservice."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            logger.info(f"C++ Financial Microservice health check: {response.json()}")
            return response.status_code == 200
        except httpx.RequestError as exc:
            logger.error(f"C++ Financial Microservice health check failed: {exc}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during C++ health check: {e}", exc_info=True)
            return False

    async def calculate_compound_interest(self, principal: float, rate: float, years: int) -> Optional[float]:
        """
        Calls the C++ financial calculator service to calculate compound interest.

        Args:
            principal (float): The initial principal amount.
            rate (float): The annual interest rate (as a decimal, e.g., 0.05 for 5%).
            years (int): The number of years the money is invested or borrowed for.

        Returns:
            Optional[float]: The calculated future value, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/calculate_compound_interest"
        payload = {
            "principal": principal,
            "rate": rate,
            "years": years
        }
        try:
            logger.info(f"Sending calculation request to C++ service: {payload}")
            response = await self.client.post(endpoint, json=payload, timeout=10.0) # Add a timeout
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            result_data = response.json()
            calculated_value = result_data.get("result")
            logger.info(f"Received result from C++ service: {calculated_value}")
            return calculated_value
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r} from C++ service: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error response {exc.response.status_code} from C++ service while requesting {exc.request.url!r}: {exc.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during C++ service call: {e}", exc_info=True)
            return None

