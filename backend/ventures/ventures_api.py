# backend/ventures/ventures_api.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional

from .healthcare_adapter import HealthcareAdapter
from .legal_adapter import LegalAdapter
from backend.dependencies import get_healthcare_adapter, get_legal_adapter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/healthcare/patient/{patient_id}", response_model=Optional[Dict[str, Any]])
async def get_patient_record(
    patient_id: str,
    adapter: HealthcareAdapter = Depends(get_healthcare_adapter)
):
    """
    Retrieves a patient's electronic health record (EHR).
    """
    if not adapter.client:
        raise HTTPException(status_code=503, detail="Healthcare adapter is not configured or available.")
    record = await adapter.get_patient_record(patient_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Patient record for ID {patient_id} not found.")
    return record

@router.post("/legal/search/cases", response_model=Optional[List[Dict[str, Any]]])
async def search_case_law(
    payload: Dict[str, Any],
    adapter: LegalAdapter = Depends(get_legal_adapter)
):
    """
    Searches for relevant case law based on a query and jurisdiction.
    """
    if not adapter.client:
        raise HTTPException(status_code=503, detail="Legal adapter is not configured or available.")
    
    query = payload.get("query")
    jurisdiction = payload.get("jurisdiction")
    if not query or not jurisdiction:
        raise HTTPException(status_code=400, detail="Both 'query' and 'jurisdiction' are required.")
        
    results = await adapter.search_case_law(query, jurisdiction)
    if results is None:
        raise HTTPException(status_code=500, detail="An error occurred while searching case law.")
    return results
