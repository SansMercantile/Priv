# backend/compute/hardware_integration_manager.py

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.security.pqc_encryption import PQCCipher

logger = logging.getLogger(__name__)

class ComputeBackend(str, Enum):
    """Enum for supported specialized computing backends."""
    NEUROMORPHIC = "neuromorphic"
    QUANTUM = "quantum"

class HardwareIntegrationManager:
    """
    Manages connections and task offloading to specialized computing hardware like
    neuromorphic and quantum processors. This is a production-ready implementation.
    """

    def __init__(self):
        """Initializes the manager with secure clients for each backend."""
        from backend.dependencies import get_singleton  # Moved here to avoid circular import
        pqc_enabled = getattr(_settings, 'PQC_ENCRYPTION_ENABLED', False)
        self.pqc_cipher: Optional[PQCCipher] = get_singleton("pqc_cipher") if pqc_enabled else None
        
        self.clients: Dict[ComputeBackend, Optional[httpx.AsyncClient]] = {
            ComputeBackend.NEUROMORPHIC: self._create_secure_client(
                base_url=getattr(_settings, 'NEUROMORPHIC_ENDPOINT', None),
                api_key=getattr(_settings, 'NEUROMORPHIC_API_KEY', None)
            ),
            ComputeBackend.QUANTUM: self._create_secure_client(
                base_url=getattr(_settings, 'QUANTUM_ENDPOINT', None),
                api_key=getattr(_settings, 'QUANTUM_API_KEY', None)
            )
        }

    def _create_secure_client(self, base_url: Optional[str], api_key: Optional[str]) -> Optional[httpx.AsyncClient]:
        """Creates a secure httpx client with appropriate headers and timeouts."""
        if not base_url or not api_key:
            logger.warning(f"Missing base_url or api_key for a specialized backend. Client will not be created.")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"{_settings.APP_NAME}/{_settings.APP_VERSION}"
        }
        
        # Production-grade transport with connection pooling and keep-alive
        transport = httpx.AsyncHTTPTransport(retries=2)
        
        return httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=httpx.Timeout(120.0, connect=15.0), # Generous timeout for complex computations
            http2=True,
            transport=transport
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def offload_task(self, backend: ComputeBackend, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Offloads a computational task to the specified specialized backend.
        Includes PQC encryption if enabled.

        Args:
            backend (ComputeBackend): The target hardware backend.
            task_id (str): A unique identifier for tracking the task.
            payload (Dict[str, Any]): The data and instructions for the task.

        Returns:
            Dict[str, Any]: The result from the backend.
        
        Raises:
            ValueError: If the client for the specified backend is not configured.
            httpx.HTTPStatusError: If the API returns an error status code.
        """
        client = self.clients.get(backend)
        if not client:
            logger.error(f"Cannot offload task {task_id}: No client configured for backend '{backend}'.")
            raise ValueError(f"Client for backend '{backend}' is not configured.")

        logger.info(f"Offloading task {task_id} to {backend} backend.")
        
        request_data = {"task_id": task_id, "payload": payload}
        
        if self.pqc_cipher:
            encrypted_payload_str = self.pqc_cipher.encrypt(json.dumps(payload))
            request_data = {"task_id": task_id, "encrypted_payload": encrypted_payload_str}

        try:
            response = await client.post("/compute", json=request_data)
            response.raise_for_status()
            
            result_data = response.json()

            if self.pqc_cipher and "encrypted_result" in result_data:
                decrypted_result_str = self.pqc_cipher.decrypt(result_data["encrypted_result"])
                return json.loads(decrypted_result_str)
            
            return result_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error on task {task_id} for {backend}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during task {task_id} offloading to {backend}: {e}", exc_info=True)
            raise

    async def get_backend_status(self, backend: ComputeBackend) -> Dict[str, Any]:
        """Retrieves the status and capabilities of a specialized computing backend."""
        client = self.clients.get(backend)
        if not client:
            return {"status": "unconfigured", "message": f"No client configured for backend: {backend}"}

        try:
            response = await client.get("/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get status for {backend}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
