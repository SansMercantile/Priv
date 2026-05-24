from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field # Using Pydantic for clearer data models

# --- Pydantic Models for Data Structure ---
# These models define the expected structure of input and output data,
# which can be very helpful for FastAPI's response_model and validation.

class Position(BaseModel):
    """Represents a trading position."""
    symbol: str
    entry_price: float
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    asset_class: str = "Equity"
    volatility_atr: Optional[float] = None
    win_probability: float = 0.5

class RiskMetrics(BaseModel):
    """Represents computed risk metrics for a single position."""
    symbol: str
    risk_amount: Optional[float] = None
    risk_pct: Optional[float] = None
    reward_pct: Optional[float] = None
    rr_ratio: Optional[float] = None
    kelly_fraction: Optional[float] = None
    note: str

class PortfolioRiskSummary(BaseModel):
    """Summarizes the overall risk of the portfolio."""
    total_risk_pct: float
    correlated_risk_warning: bool = False
    missing_stops: int
    weak_rr_count: int
    flag: str
    positions: List[RiskMetrics]

class RiskAdjustmentSuggestion(BaseModel):
    """Represents suggested adjustments for a single position."""
    symbol: str
    suggestions: List[str]

# --- Configuration Constants for Risk Logic ---
# These can be made configurable via environment variables or a config file if desired.
WEAK_RR_THRESHOLD: float = 1.5
OK_RR_THRESHOLD: float = 2.0
DEFAULT_MAX_RISK_PER_TRADE_PCT: float = 1.5
DEFAULT_PORTFOLIO_RISK_LIMIT_PCT: float = 5.0
DEFAULT_RR_TARGET: float = 2.0 # Target R:R for suggestions


import numpy as np

def calculate_kelly_criterion(win_prob: float, win_loss_ratio: float) -> float:
    """
    Calculates the Kelly Criterion fraction for optimal position sizing.
    Formula: K% = W - [(1 - W) / R]
    """
    try:
        if win_loss_ratio <= 0: return 0.0
        kelly_f = win_prob - ((1 - win_prob) / win_loss_ratio)
        return max(0.0, kelly_f)
    except Exception:
        return 0.0

def compute_risk_metrics(position: Position, account_equity: float) -> RiskMetrics:
    """
    Computes various risk and reward metrics for a given trading position.

    Args:
        position (Position): A dictionary or Pydantic model representing the trading position.
        account_equity (float): The total equity in the trading account.

    Returns:
        RiskMetrics: A Pydantic model containing the computed metrics.
    """
    if position.stop_loss is None:
        return RiskMetrics(
            symbol=position.symbol,
            risk_pct=None,
            reward_pct=None,
            rr_ratio=None,
            note="No stop loss set"
        )

    # Calculate risk per unit and total risk amount
    risk_per_unit = abs(position.entry_price - position.stop_loss)
    risk = risk_per_unit * position.volume

    # Handle division by zero for equity gracefully
    risk_pct = round((risk / account_equity) * 100, 2) if account_equity > 0 else None

    reward = None
    rr_ratio = None
    if position.take_profit is not None:
        reward_per_unit = abs(position.take_profit - position.entry_price)
        reward = reward_per_unit * position.volume
        # Handle division by zero for risk gracefully
        rr_ratio = round(reward / risk, 2) if risk > 0 else None

    # Quant-Grade Volatility Check
    vol_note = ""
    if position.volatility_atr and risk_per_unit < (1.5 * position.volatility_atr):
        vol_note = "[Tight Stop/High Noise] "

    # Kelly Criterion Calculation
    kelly_f = None
    if rr_ratio and rr_ratio > 0:
        kelly_f = round(calculate_kelly_criterion(position.win_probability, rr_ratio), 4)

    # Determine the note
    note = f"{vol_note}OK" if rr_ratio else f"{vol_note}No Take Profit set"
    if rr_ratio and rr_ratio < WEAK_RR_THRESHOLD:
        note = f"{vol_note}Weak R:R"
    elif rr_ratio and rr_ratio < OK_RR_THRESHOLD:
        note = f"{vol_note}Acceptable R:R"

    return RiskMetrics(
        symbol=position.symbol,
        risk_amount=round(risk, 2),
        risk_pct=risk_pct,
        reward_pct=round(reward, 2) if reward is not None else None,
        rr_ratio=rr_ratio,
        kelly_fraction=kelly_f,
        note=note
    )


def evaluate_portfolio_risk(
    positions: List[Position],
    equity: float,
    portfolio_risk_limit: float = DEFAULT_PORTFOLIO_RISK_LIMIT_PCT,
    weak_rr_threshold: float = WEAK_RR_THRESHOLD
) -> PortfolioRiskSummary:
    """
    Evaluates portfolio risk with Correlation-Awareness.
    """
    total_risk_pct = 0.0
    trades_without_sl = 0
    weak_rr_trades = 0

    # Correlation check: count positions in the same asset class
    class_distribution = {}
    
    risk_results = []
    for pos in positions:
        metrics = compute_risk_metrics(pos, equity)
        risk_results.append(metrics)
        
        if metrics.risk_pct: total_risk_pct += metrics.risk_pct
        if "No stop loss" in metrics.note: trades_without_sl += 1
        if metrics.rr_ratio and metrics.rr_ratio < weak_rr_threshold: weak_rr_trades += 1
        
        class_distribution[pos.asset_class] = class_distribution.get(pos.asset_class, 0) + 1

    # Correlation alert: > 50% of positions in one asset class
    is_correlated = any(count / len(positions) > 0.5 for count in class_distribution.values()) if positions else False

    portfolio_flag = "✅ Within risk limits"
    if total_risk_pct > portfolio_risk_limit:
        portfolio_flag = "⚠️ Portfolio risk exceeds limit"
    elif is_correlated:
        portfolio_flag = "⚠️ High Asset Correlation Risk"
    elif trades_without_sl > 0:
        portfolio_flag = "⚠️ Missing SL on some trades"

    return PortfolioRiskSummary(
        total_risk_pct=round(total_risk_pct, 2),
        correlated_risk_warning=is_correlated,
        missing_stops=trades_without_sl,
        weak_rr_count=weak_rr_trades,
        flag=portfolio_flag,
        positions=risk_results
    )


def suggest_risk_adjustments(
    position: Position,
    equity: float,
    max_risk_per_trade_pct: float = DEFAULT_MAX_RISK_PER_TRADE_PCT,
    rr_target: float = DEFAULT_RR_TARGET
) -> RiskAdjustmentSuggestion:
    """
    Suggests adjustments for a single trading position based on defined risk parameters.

    Args:
        position (Position): A dictionary or Pydantic model representing the trading position.
        equity (float): The total equity in the trading account.
        max_risk_per_trade_pct (float): The maximum acceptable percentage of account equity to risk per trade.
        rr_target (float): The target Risk:Reward ratio for suggestions.

    Returns:
        RiskAdjustmentSuggestion: A Pydantic model containing suggested adjustments for the position.
    """
    suggestions = []

    if position.stop_loss is None:
        suggestions.append("Set a stop loss to define acceptable risk.")
        return RiskAdjustmentSuggestion(symbol=position.symbol, suggestions=suggestions)

    price_diff = abs(position.entry_price - position.stop_loss)
    if price_diff == 0: # Handle potential division by zero if SL == Entry
        suggestions.append("Stop loss is at entry price, consider adjusting.")
        # Cannot calculate risk percentage or optimal volume without a valid price difference.
        return RiskAdjustmentSuggestion(symbol=position.symbol, suggestions=suggestions)


    risk_amount = price_diff * position.volume
    current_risk_pct = (risk_amount / equity) * 100 if equity > 0 else 0.0

    if current_risk_pct > max_risk_per_trade_pct:
        # Suggest lower volume to fit within limit
        # Ensure price_diff is not zero before division
        optimal_volume = round((max_risk_per_trade_pct / 100) * equity / price_diff, 2)
        suggestions.append(f"Reduce volume to {optimal_volume:.2f} to stay within {max_risk_per_trade_pct:.1f}% risk.")

    # Check and suggest R:R adjustment
    rr_actual = None
    if position.take_profit is not None:
        reward_per_unit = abs(position.take_profit - position.entry_price)
        if price_diff > 0: # Ensure not dividing by zero
            rr_actual = reward_per_unit / price_diff

    if rr_actual is None or rr_actual < rr_target:
        # Adjust take-profit for desired R:R
        # Assumes a long position (entry < SL means SL is below, TP should be above)
        # Or a short position (entry > SL means SL is above, TP should be below)
        # For simplicity, adjust from entry based on stop-loss distance
        target_tp_distance = price_diff * rr_target
        if position.entry_price < position.stop_loss: # Likely a short position, SL is above entry
             target_tp = position.entry_price - target_tp_distance # TP below entry
        else: # Likely a long position, SL is below entry
             target_tp = position.entry_price + target_tp_distance # TP above entry

        suggestions.append(f"Adjust take-profit to {target_tp:.2f} for {rr_target}:1 R:R.")

    if not suggestions: # If all other checks passed and no specific suggestions were added
        suggestions.append("Risk exposure is acceptable for this trade.")

    return RiskAdjustmentSuggestion(symbol=position.symbol, suggestions=suggestions)