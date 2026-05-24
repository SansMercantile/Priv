# backend/ventures/adapters.py

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx

# This file provides functional adapters for expanding the PRIV AI into new industries.
# It includes Pydantic models for industry-specific data (FHIR for healthcare)
# and clients for interacting with external APIs.

logger = logging.getLogger(__name__)

# --- Healthcare (FHIR) Models ---
class Patient(BaseModel):
    resourceType: str = "Patient"
    id: str
    name: List[Dict[str, Any]]
    gender: str
    birthDate: str

class Observation(BaseModel):
    resourceType: str = "Observation"
    id: str
    status: str
    code: Dict[str, Any]
    subject: Dict[str, str]
    valueQuantity: Optional[Dict[str, Any]] = None

# --- Legal Models ---
class LegalDocument(BaseModel):
    id: str
    title: str
    document_type: str = Field(..., description="e.g., 'Contract', 'Pleading', 'Statute'")
    jurisdiction: str
    full_text: str
    summary: Optional[str] = None

# --- Adapter Clients ---
class HealthcareAdapter:
    """
    Client for interacting with a healthcare system's FHIR-compliant API.
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)
        logger.info(f"HealthcareAdapter initialized for endpoint: {self.base_url}")

    async def get_patient_data(self, patient_id: str) -> Optional[Patient]:
        try:
            response = await self.client.get(f"/Patient/{patient_id}")
            response.raise_for_status()
            return Patient(**response.json())
        except Exception as e:
            logger.error(f"Failed to retrieve patient data for ID {patient_id}: {e}", exc_info=True)
            return None

class LegalAdapter:
    """
    Client for interacting with a legal research database API.
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)
        logger.info(f"LegalAdapter initialized for endpoint: {self.base_url}")

    async def search_legal_documents(self, query: str, jurisdiction: str) -> List[LegalDocument]:
        try:
            params = {"q": query, "jurisdiction": jurisdiction}
            response = await self.client.get("/search", params=params)
            response.raise_for_status()
            docs_data = response.json().get("documents", [])
            return [LegalDocument(**doc) for doc in docs_data]
        except Exception as e:
            logger.error(f"Failed to search legal documents for query '{query}': {e}", exc_info=True)
            return []
