# priv/backend/utils/go_status_client.py
import httpx # Using httpx for async operations
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GoStatusClient:
    """
    Client to interact with the Go Status Microservice.
    It communicates via HTTP/REST.
    """
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        logger.info(f"Initialized GoStatusClient with base URL: {self.base_url}")

    async def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the status from the Go microservice.

        Returns:
            Optional[Dict[str, Any]]: The status dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/status"
        try:
            logger.info(f"Requesting status from Go service at {endpoint}")
            response = await self.client.get(endpoint, timeout=5.0) # Add a timeout
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            status_data = response.json()
            logger.info(f"Received status from Go service: {status_data}")
            return status_data
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r} from Go service: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error response {exc.response.status_code} from Go service while requesting {exc.request.url!r}: {exc.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Go service call: {e}", exc_info=True)
            return None

