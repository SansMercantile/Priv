from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
import logging
from backend.financial_automation.global_tax_systems import global_tax_system, TaxResidency, TaxType

logger = logging.getLogger(__name__)
router = APIRouter()

class TaxCalculationRequest(BaseModel):
    tax_residency: str
    tax_type: str
    amount: Decimal
    tax_year: int

class TaxReportRequest(BaseModel):
    tax_residency: str
    tax_year: int
    transactions: List[Dict[str, Any]] = []


@router.get("/supported_countries")
async def supported_countries() -> Dict[str, Any]:
    try:
        countries = global_tax_system.get_supported_countries()
        return {"success": True, "data": countries}
    except Exception as e:
        logger.error(f"Error getting supported countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_tax(req: TaxCalculationRequest) -> Dict[str, Any]:
    try:
        residency = TaxResidency(req.tax_residency)
        ttype = TaxType(req.tax_type)
        calc = global_tax_system.calculate_tax(residency, ttype, req.amount, req.tax_year)
        return {"success": True, "data": calc.model_dump() if hasattr(calc, 'model_dump') else (calc.dict() if hasattr(calc, 'dict') else calc)}
    except Exception as e:
        logger.error(f"Error calculating tax: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def generate_report(req: TaxReportRequest) -> Dict[str, Any]:
    try:
        residency = TaxResidency(req.tax_residency)
        report = global_tax_system.generate_tax_report(residency, req.tax_year, req.transactions)
        # Convert pydantic models to dicts
        return {"success": True, "data": report.model_dump() if hasattr(report, 'model_dump') else (report.dict() if hasattr(report, 'dict') else report)}
    except Exception as e:
        logger.error(f"Error generating tax report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_report(report: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Expect the client to send a report in the TaxReport shape
        # For demo mode just call submit_tax_report stubs
        # Build a minimal object compatible with global_tax_system.submit_tax_report
        submission: Dict[str, Any] = {
            "status": "prepared",
            "message": "In demo mode the report is not actually submitted."
        }
        return {"success": True, "data": submission}
    except Exception as e:
        logger.error(f"Error submitting tax report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
