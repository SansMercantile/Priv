# priv/backend/multi_agent/financial_automation/financial_cpp_client.py
import httpx # Using httpx for async operations, as mpeti_core uses asyncio
import logging

logger = logging.getLogger(__name__)

class FinancialCppClient:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def calculate_compound_interest(self, principal: float, rate: float, years: int) -> float:
        """
        Calls the C++ financial calculator service to calculate compound interest.
        """
        endpoint = f"{self.base_url}/calculate"
        payload = {
            "principal": principal,
            "rate": rate,
            "years": years
        }
        try:
            logger.info(f"Sending calculation request to C++ service: {payload}")
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            result_data = response.json()
            calculated_value = result_data.get("result")
            logger.info(f"Received result from C++ service: {calculated_value}")
            return calculated_value
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during C++ service call: {e}")
            raise

# Usage in MPETI Core (or a financial automation agent)
# from .financial_cpp_client import FinancialCppClient
# financial_cpp_client = FinancialCppClient()
# result = await financial_cpp_client.calculate_compound_interest(1000, 0.05, 10)
