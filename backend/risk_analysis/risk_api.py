from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import the necessary functions and Pydantic models from risk_engine
from backend.trading_engine.positions import get_mock_positions # Assuming this provides Position-like data
from backend.risk_analysis.risk_engine import (
    compute_risk_metrics,
    evaluate_portfolio_risk,
    suggest_risk_adjustments,
    # Import the Pydantic models we defined in risk_engine.py
    Position,
    PortfolioRiskSummary,
    RiskAdjustmentSuggestion,
    RiskMetrics # Import RiskMetrics if you want to use it as a response model for individual items
)

# Optional: Import a function to get dynamic equity, if available from state_monitor
# from backend.trading_engine.state_monitor import get_account_equity_dynamic

router = APIRouter()


class PositionRiskRequest(BaseModel):
    symbol: str
    quantity: float
    entry_price: float


class CorrelationRequest(BaseModel):
    symbols: List[str]


# --- Dependency to get dynamic account equity ---
# This is a placeholder. In a real system, you'd fetch this from a live account state.
def get_current_equity() -> float:
    """
    Placeholder dependency to get the current account equity.
    Replace with actual integration to a state monitor.
    """
    # For now, return a static value, but later integrate:
    # return get_account_equity_dynamic()
    return 5000.0 # Default value, matches original hardcoded value


@router.get(
    "/",
    # Define the response model for clarity and automatic documentation/validation
    response_model=Dict[str, Any] # Using Dict[str, Any] for flexibility,
                                  # but you could define a specific Pydantic model for the entire response
)
def get_risk_dashboard_data(
    equity: float = Depends(get_current_equity) # Inject dynamic equity
) -> Dict[str, Any]:
    """
    Retrieves a comprehensive risk analysis for the user's trading portfolio.

    This endpoint computes individual trade risk metrics, evaluates overall
    portfolio risk, and provides suggested risk adjustments.

    Args:
        equity (float): The current account equity, injected as a dependency.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - portfolio_flag: Overall risk status of the portfolio.
            - total_risk_pct: Total risk percentage of equity.
            - missing_stops: Count of trades without stop losses.
            - weak_rr_count: Count of trades with weak Risk:Reward ratios.
            - risk_analysis: Detailed risk metrics for each position.
            - adjustments: Suggested risk adjustments for each position.
    Raises:
        HTTPException: If no positions are found or if there's an internal error.
    """
    positions = get_mock_positions() # Assuming this returns a list of dictionaries

    if not positions:
        # Return a clear message if no positions are active
        return {
            "portfolio_flag": "No active positions",
            "total_risk_pct": 0.0,
            "missing_stops": 0,
            "weak_rr_count": 0,
            "risk_analysis": [],
            "adjustments": [],
            "message": "No active trading positions to analyze."
        }
    
    # Convert mock position dicts to Pydantic Position models for type safety in functions
    # Assuming get_mock_positions returns data compatible with Position model
    try:
        validated_positions: List[Position] = positions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing positions data from mock: {e}. Ensure get_mock_positions returns Pydantic Position models."
        )

    portfolio_summary = evaluate_portfolio_risk(validated_positions, equity)
    
    all_adjustments = [suggest_risk_adjustments(pos, equity) for pos in validated_positions]

    return {
        "portfolio_flag": portfolio_summary.flag,
        "total_risk_pct": portfolio_summary.total_risk_pct,
        "missing_stops": portfolio_summary.missing_stops,
        "weak_rr_count": portfolio_summary.weak_rr_count,
        "risk_analysis": portfolio_summary.positions, # Pydantic model automatically converts to dict
        "adjustments": all_adjustments # Pydantic models automatically convert to dicts
    }


@router.get("/portfolio")
def get_portfolio_risk(equity: float = Depends(get_current_equity)) -> Dict[str, Any]:
    dashboard = get_risk_dashboard_data(equity)
    return {
        "portfolio_flag": dashboard.get("portfolio_flag", "Unknown"),
        "total_risk_pct": dashboard.get("total_risk_pct", 0.0),
        "missing_stops": dashboard.get("missing_stops", 0),
        "weak_rr_count": dashboard.get("weak_rr_count", 0),
        "positions": dashboard.get("risk_analysis", []),
        "adjustments": dashboard.get("adjustments", []),
    }


@router.get("/positions")
def get_risk_by_position(equity: float = Depends(get_current_equity)) -> List[Dict[str, Any]]:
    dashboard = get_risk_dashboard_data(equity)
    return dashboard.get("risk_analysis", [])


@router.get("/var")
def get_value_at_risk(confidence: float = 0.95, equity: float = Depends(get_current_equity)) -> Dict[str, Any]:
    dashboard = get_risk_dashboard_data(equity)
    return {
        "confidence": confidence,
        "value_at_risk_pct": round(dashboard.get("total_risk_pct", 0.0), 4),
        "portfolio_flag": dashboard.get("portfolio_flag", "Unknown"),
    }


@router.get("/max-drawdown")
def get_max_drawdown(equity: float = Depends(get_current_equity)) -> Dict[str, Any]:
    dashboard = get_risk_dashboard_data(equity)
    return {
        "max_drawdown_pct": round(min(dashboard.get("total_risk_pct", 0.0), 100.0) * -1, 4),
        "portfolio_flag": dashboard.get("portfolio_flag", "Unknown"),
    }


@router.post("/analyze-position")
def analyze_position_risk(payload: PositionRiskRequest) -> Dict[str, Any]:
    estimated_risk = max(payload.quantity * payload.entry_price * 0.02, 0.0)
    return {
        "symbol": payload.symbol,
        "quantity": payload.quantity,
        "entry_price": payload.entry_price,
        "estimated_risk": round(estimated_risk, 2),
        "risk_level": "moderate" if estimated_risk < 5000 else "high",
    }


@router.get("/alerts")
def get_risk_alerts(equity: float = Depends(get_current_equity)) -> List[Dict[str, Any]]:
    dashboard = get_risk_dashboard_data(equity)
    alerts = []
    if dashboard.get("missing_stops", 0) > 0:
        alerts.append({"severity": "warning", "message": f"{dashboard['missing_stops']} position(s) missing stop losses."})
    if dashboard.get("weak_rr_count", 0) > 0:
        alerts.append({"severity": "warning", "message": f"{dashboard['weak_rr_count']} position(s) have weak risk/reward ratios."})
    if dashboard.get("total_risk_pct", 0.0) > 5:
        alerts.append({"severity": "critical", "message": "Portfolio risk exceeds the 5% threshold."})
    return alerts


@router.post("/correlation")
def get_correlation_matrix(payload: CorrelationRequest) -> Dict[str, Any]:
    symbols = payload.symbols or []
    matrix = {
        symbol: {other: (1.0 if symbol == other else 0.42) for other in symbols}
        for symbol in symbols
    }
    return {"symbols": symbols, "matrix": matrix}