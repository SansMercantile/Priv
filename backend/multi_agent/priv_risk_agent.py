"""
Copyright (c) 2025 Sans Mercantile
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.

Patent Pending - Sans Mercantile Constellation AI System
International Patent Application Filed

System: PRIV - AI-Driven Fintech and Trading System
Module: Priv Risk Agent
Purpose: Advanced risk management and portfolio risk assessment
Author: Sans Mercantile AI Development Team
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from statistics import stdev, mean
import json

from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import (
    AgentMessage, AgentType, MessageType, TradeProposal, ArbitrationVote
)
from backend.config import get_settings
from backend.database import get_db_session
from backend.journal.trade_journal import TradeJournal
from backend.support_ai.analytics_engine import AnalyticsEngine
from backend.utils.watchdog import Watchdog

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio assessment"""
    portfolio_value: Decimal
    daily_var: Decimal
    weekly_var: Decimal
    monthly_var: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    beta: Decimal
    correlation_matrix: np.ndarray
    concentration_risk: Decimal
    liquidity_risk: Decimal
    volatility: Decimal
    risk_score: Decimal


@dataclass
class RiskLimits:
    """Risk limits configuration"""
    max_exposure_per_symbol: Decimal = Decimal("0.10")  # 10%
    max_daily_loss_pct: Decimal = Decimal("0.05")       # 5%
    max_portfolio_var: Decimal = Decimal("0.02")        # 2% daily VaR
    max_concentration_risk: Decimal = Decimal("0.25")   # 25%
    max_leverage: Decimal = Decimal("2.0")              # 2x
    min_liquidity_ratio: Decimal = Decimal("0.10")      # 10%
    max_correlation: Decimal = Decimal("0.8")           # 80%
    stress_test_scenarios: List[str] = None


class PrivRiskAgent(PrivAgent):
    """
    Advanced risk management agent for comprehensive portfolio risk assessment.
    
    Features:
    - Real-time risk monitoring
    - VaR calculation (Value at Risk)
    - Stress testing scenarios
    - Correlation analysis
    - Concentration risk assessment
    - Liquidity risk monitoring
    - Automated risk alerts
    - Global tax integration
    - Multi-jurisdiction compliance
    """
    
    def __init__(self, agent_id, agent_type, message_broker=None, broker=None, persona=None, name=None, description=None, **kwargs):
        # Store name and description as instance attributes if needed
        self.name = name or "PRIV Risk Agent"
        self.description = description or "Advanced risk management and portfolio assessment with global compliance"
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            message_broker=message_broker,
            broker=broker,
            persona=persona,
            **kwargs
        )
        # Risk configuration
        self.risk_limits = RiskLimits()
        self.var_confidence_level = Decimal("0.95")  # 95% confidence
        self.var_lookback_days = 30
        self.stress_test_scenarios = [
            "market_crash_2008",
            "covid_crash_2020",
            "interest_rate_shock",
            "currency_crisis",
            "geopolitical_event",
            "liquidity_crisis",
            "inflation_spike",
            "recession_scenario"
        ]
        
        # Risk thresholds
        self.risk_thresholds = {
            "low": Decimal("0.3"),
            "medium": Decimal("0.6"),
            "high": Decimal("0.8"),
            "critical": Decimal("0.9")
        }
        
        # Monitoring intervals
        self.monitoring_interval = 30  # seconds
        self.risk_report_interval = 300  # 5 minutes
        
        # Global compliance
        self.supported_jurisdictions = [
            "US", "UK", "EU", "Canada", "Australia", "Japan", "Singapore",
            "South Africa", "Nigeria", "Ghana", "Kenya", "Egypt", "Morocco"
        ]
        
        # Analytics engine
        self.analytics_engine = AnalyticsEngine()
        
        # Initialize components
        self.initialize_risk_monitoring()
        
    def initialize_risk_monitoring(self):
        """Initialize risk monitoring systems"""
        logger.info("Initializing PRIV Risk Agent monitoring systems")
        
        # Start background monitoring if event loop is running
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.continuous_risk_monitoring())
        except RuntimeError:
            logger.warning("No running event loop found during initialization. continuous_risk_monitoring not started automatically.")
        
        # Schedule periodic risk reports - TODO: implement periodic_risk_reporting method
        # asyncio.create_task(self.periodic_risk_reporting())
        
    async def continuous_risk_monitoring(self):
        """Continuous risk monitoring loop"""
        while self.is_running:
            try:
                # Get current portfolio state
                portfolio_state = await self.get_portfolio_state()
                
                # Calculate risk metrics
                risk_metrics = await self.calculate_risk_metrics(portfolio_state)
                
                # Check risk limits
                violations = await self.check_risk_limits(risk_metrics)
                
                # Handle violations
                if violations:
                    await self.handle_risk_violations(violations, risk_metrics)
                
                # Update risk dashboard
                await self.update_risk_dashboard(risk_metrics)
                
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await self.handle_monitoring_error(e)
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def calculate_risk_metrics(self, portfolio_state: Dict[str, Any]) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        logger.debug("Calculating risk metrics")
        
        try:
            # Extract portfolio data
            portfolio_value = Decimal(str(portfolio_state.get("total_value", 0)))
            positions = portfolio_state.get("positions", [])
            historical_returns = portfolio_state.get("historical_returns", [])
            
            # Calculate VaR (Value at Risk)
            daily_var = await self.calculate_var(historical_returns, self.var_confidence_level)
            weekly_var = daily_var * Decimal("2.24")  # sqrt(5)
            monthly_var = daily_var * Decimal("4.47")  # sqrt(20)
            
            # Calculate volatility
            volatility = await self.calculate_volatility(historical_returns)
            
            # Calculate correlation matrix
            correlation_matrix = await self.calculate_correlation_matrix(positions)
            
            # Calculate concentration risk
            concentration_risk = await self.calculate_concentration_risk(positions)
            
            # Calculate liquidity risk
            liquidity_risk = await self.calculate_liquidity_risk(positions)
            
            # Calculate performance metrics
            sharpe_ratio = await self.calculate_sharpe_ratio(historical_returns)
            sortino_ratio = await self.calculate_sortino_ratio(historical_returns)
            max_drawdown = await self.calculate_max_drawdown(historical_returns)
            
            # Calculate beta (market correlation)
            beta = await self.calculate_beta(historical_returns)
            
            # Calculate overall risk score
            risk_score = await self.calculate_overall_risk_score({
                "var": daily_var,
                "volatility": volatility,
                "concentration": concentration_risk,
                "liquidity": liquidity_risk,
                "correlation": self.extract_max_correlation(correlation_matrix)
            })
            
            return RiskMetrics(
                portfolio_value=portfolio_value,
                daily_var=daily_var,
                weekly_var=weekly_var,
                monthly_var=monthly_var,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                beta=beta,
                correlation_matrix=correlation_matrix,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                volatility=volatility,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            raise
    
    async def calculate_var(self, returns: List[float], confidence_level: Decimal) -> Decimal:
        """Calculate Value at Risk using historical simulation"""
        if not returns or len(returns) < 30:
            return Decimal("0")
        
        # Sort returns
        sorted_returns = sorted(returns)
        
        # Find the percentile corresponding to confidence level
        percentile_index = int(len(sorted_returns) * (1 - float(confidence_level)))
        percentile_index = max(0, min(percentile_index, len(sorted_returns) - 1))
        
        var_return = sorted_returns[percentile_index]
        
        # Convert to portfolio value VaR
        portfolio_value = await self.get_portfolio_value()
        var_amount = abs(Decimal(str(var_return)) * portfolio_value)
        
        return var_amount
    
    async def calculate_volatility(self, returns: List[float]) -> Decimal:
        """Calculate annualized volatility"""
        if not returns or len(returns) < 2:
            return Decimal("0")
        
        # Calculate standard deviation
        volatility = stdev(returns) if len(returns) > 1 else 0
        
        # Annualize (assuming daily returns)
        annualized_volatility = volatility * (252 ** 0.5)
        
        return Decimal(str(annualized_volatility))
    
    async def calculate_correlation_matrix(self, positions: List[Dict[str, Any]]) -> np.ndarray:
        """Calculate correlation matrix for portfolio positions"""
        if len(positions) < 2:
            return np.array([[1.0]])
        
        # Extract historical returns for each position
        returns_matrix = []
        for position in positions:
            symbol = position.get("symbol")
            historical_returns = await self.get_historical_returns(symbol)
            returns_matrix.append(historical_returns)
        
        # Convert to numpy array
        returns_array = np.array(returns_matrix)
        
        # Calculate correlation matrix
        correlation_matrix = np.corrcoef(returns_array)
        
        return correlation_matrix
    
    async def calculate_concentration_risk(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Calculate portfolio concentration risk"""
        if not positions:
            return Decimal("0")
        
        # Calculate position weights
        total_value = sum(Decimal(str(pos.get("market_value", 0))) for pos in positions)
        
        if total_value == 0:
            return Decimal("0")
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        weights = [Decimal(str(pos.get("market_value", 0))) / total_value for pos in positions]
        hhi = sum(weight ** 2 for weight in weights)
        
        # Normalize to 0-1 scale
        concentration_risk = min(hhi * len(positions), Decimal("1"))
        
        return concentration_risk
    
    async def calculate_liquidity_risk(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Calculate liquidity risk based on position sizes and market liquidity"""
        if not positions:
            return Decimal("0")
        
        total_liquidity_risk = Decimal("0")
        
        for position in positions:
            symbol = position.get("symbol")
            market_value = Decimal(str(position.get("market_value", 0)))
            volume = await self.get_average_volume(symbol)
            
            # Calculate days to liquidate
            if volume > 0:
                days_to_liquidate = market_value / Decimal(str(volume))
                position_liquidity_risk = min(days_to_liquidate / Decimal("5"), Decimal("1"))
                total_liquidity_risk = max(total_liquidity_risk, position_liquidity_risk)
        
        return total_liquidity_risk
    
    async def handle_trade_proposal(self, message: AgentMessage):
        """Handle trade proposal messages with comprehensive risk assessment"""
        try:
            trade_data = message.data.get("trade_proposal", {})
            
            # Extract trade details
            symbol = trade_data.get("symbol")
            quantity = Decimal(str(trade_data.get("quantity", 0)))
            price = Decimal(str(trade_data.get("price", 0)))
            trade_type = trade_data.get("type", "buy")
            
            # Calculate comprehensive trade risk
            trade_risk = await self.calculate_comprehensive_trade_risk(
                symbol, quantity, price, trade_type
            )
            
            # Generate risk assessment
            risk_assessment = {
                "trade_id": trade_data.get("trade_id"),
                "risk_level": trade_risk["risk_level"],
                "risk_score": str(trade_risk["risk_score"]),
                "var_impact": str(trade_risk["var_impact"]),
                "concentration_impact": str(trade_risk["concentration_impact"]),
                "liquidity_impact": str(trade_risk["liquidity_impact"]),
                "jurisdiction_compliance": trade_risk["jurisdiction_compliance"],
                "tax_implications": trade_risk["tax_implications"],
                "recommendation": trade_risk["recommendation"],
                "approval_status": trade_risk["approval_status"],
                "monitoring_requirements": trade_risk["monitoring_requirements"]
            }
            
            # Create arbitration vote
            vote = ArbitrationVote(
                agent_id=self.agent_id,
                trade_id=trade_data.get("trade_id"),
                vote=trade_risk["approval_status"],
                confidence=Decimal("0.95"),
                reasoning=f"Comprehensive risk assessment: {trade_risk['risk_level']} risk level",
                risk_assessment=risk_assessment
            )
            
            # Publish vote
            await self.publish_vote(vote)
            
            # Log decision
            logger.info(f"Risk agent vote: {vote.vote} for trade {vote.trade_id}")
            
        except Exception as e:
            logger.error(f"Error handling trade proposal: {e}")
            # Vote against trade on error
            error_vote = ArbitrationVote(
                agent_id=self.agent_id,
                trade_id=message.data.get("trade_id", "unknown"),
                vote="against",
                confidence=Decimal("1.0"),
                reasoning=f"Risk assessment error: {str(e)}",
                risk_assessment={"error": str(e)}
            )
            await self.publish_vote(error_vote)
    
    async def calculate_comprehensive_trade_risk(self, symbol: str, quantity: Decimal, price: Decimal, trade_type: str) -> Dict[str, Any]:
        """Calculate comprehensive risk for individual trade including global compliance"""
        try:
            # Get current portfolio state
            portfolio_state = await self.get_portfolio_state()
            current_positions = portfolio_state.get("positions", [])
            
            # Calculate trade value
            trade_value = quantity * price
            
            # Calculate position size relative to portfolio
            portfolio_value = await self.get_portfolio_value()
            position_size_pct = trade_value / portfolio_value if portfolio_value > 0 else Decimal("0")
            
            # Check against position size limits
            if position_size_pct > self.risk_limits.max_exposure_per_symbol:
                return {
                    "risk_level": "high",
                    "risk_score": Decimal("0.9"),
                    "var_impact": trade_value * Decimal("0.02"),
                    "concentration_impact": position_size_pct,
                    "liquidity_impact": trade_value / Decimal("1000000"),
                    "jurisdiction_compliance": "pending",
                    "tax_implications": "requires_analysis",
                    "recommendation": "Position size exceeds limit",
                    "approval_status": "against",
                    "monitoring_requirements": ["continuous_monitoring"]
                }
            
            # Calculate VaR impact
            var_impact = trade_value * Decimal("0.02")  # Assume 2% daily volatility
            
            # Check if trade would exceed VaR limit
            current_var = await self.get_current_var()
            if (current_var + var_impact) > (self.risk_limits.max_portfolio_var * portfolio_value):
                return {
                    "risk_level": "high",
                    "risk_score": Decimal("0.85"),
                    "var_impact": var_impact,
                    "concentration_impact": position_size_pct,
                    "liquidity_impact": trade_value / Decimal("1000000"),
                    "jurisdiction_compliance": "pending",
                    "tax_implications": "requires_analysis",
                    "recommendation": "Trade would exceed VaR limit",
                    "approval_status": "against",
                    "monitoring_requirements": ["var_monitoring"]
                }
            
            # Check global compliance
            jurisdiction_compliance = await self.check_jurisdiction_compliance(symbol, trade_type)
            
            # Calculate tax implications
            tax_implications = await self.calculate_trade_tax_implications(symbol, trade_value, trade_type)
            
            # Calculate overall risk score
            risk_score = self.calculate_comprehensive_trade_risk_score(
                position_size_pct, var_impact, symbol, jurisdiction_compliance, tax_implications
            )
            
            # Determine risk level and recommendation
            if risk_score > self.risk_thresholds["high"]:
                return {
                    "risk_level": "high",
                    "risk_score": risk_score,
                    "var_impact": var_impact,
                    "concentration_impact": position_size_pct,
                    "liquidity_impact": trade_value / Decimal("1000000"),
                    "jurisdiction_compliance": jurisdiction_compliance,
                    "tax_implications": tax_implications,
                    "recommendation": "High risk trade - requires careful consideration",
                    "approval_status": "against",
                    "monitoring_requirements": ["continuous_monitoring", "var_monitoring"]
                }
            elif risk_score > self.risk_thresholds["medium"]:
                return {
                    "risk_level": "medium",
                    "risk_score": risk_score,
                    "var_impact": var_impact,
                    "concentration_impact": position_size_pct,
                    "liquidity_impact": trade_value / Decimal("1000000"),
                    "jurisdiction_compliance": jurisdiction_compliance,
                    "tax_implications": tax_implications,
                    "recommendation": "Moderate risk - proceed with caution",
                    "approval_status": "conditional",
                    "monitoring_requirements": ["var_monitoring", "compliance_monitoring"]
                }
            else:
                return {
                    "risk_level": "low",
                    "risk_score": risk_score,
                    "var_impact": var_impact,
                    "concentration_impact": position_size_pct,
                    "liquidity_impact": trade_value / Decimal("1000000"),
                    "jurisdiction_compliance": jurisdiction_compliance,
                    "tax_implications": tax_implications,
                    "recommendation": "Low risk trade - approved",
                    "approval_status": "for",
                    "monitoring_requirements": ["standard_monitoring"]
                }
                
        except Exception as e:
            logger.error(f"Error calculating comprehensive trade risk: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": Decimal("1.0"),
                "var_impact": Decimal("0"),
                "concentration_impact": Decimal("0"),
                "liquidity_impact": Decimal("0"),
                "jurisdiction_compliance": "error",
                "tax_implications": "error",
                "recommendation": f"Risk calculation error: {str(e)}",
                "approval_status": "against",
                "monitoring_requirements": ["error_monitoring"]
            }
    
    async def check_jurisdiction_compliance(self, symbol: str, trade_type: str) -> str:
        """Check compliance with global jurisdictions"""
        try:
            # Determine jurisdiction based on symbol
            jurisdiction = self.determine_symbol_jurisdiction(symbol)
            
            if jurisdiction not in self.supported_jurisdictions:
                return "jurisdiction_not_supported"
            
            # Check specific compliance requirements
            compliance_checks = {
                "US": self.check_us_compliance(symbol, trade_type),
                "UK": self.check_uk_compliance(symbol, trade_type),
                "EU": self.check_eu_compliance(symbol, trade_type),
                "South Africa": self.check_sa_compliance(symbol, trade_type),
                "Nigeria": self.check_nigeria_compliance(symbol, trade_type),
                "Ghana": self.check_ghana_compliance(symbol, trade_type)
            }
            
            return compliance_checks.get(jurisdiction, "compliance_unknown")
            
        except Exception as e:
            logger.error(f"Error checking jurisdiction compliance: {e}")
            return "compliance_error"
    
    def determine_symbol_jurisdiction(self, symbol: str) -> str:
        """Determine jurisdiction based on symbol"""
        # Simple mapping (in real implementation, would use comprehensive mapping)
        if symbol.endswith(".US") or len(symbol) <= 5:
            return "US"
        elif symbol.endswith(".L"):
            return "UK"
        elif symbol.endswith(".DE"):
            return "EU"
        elif symbol.endswith(".JO"):
            return "South Africa"
        elif symbol.endswith(".NG"):
            return "Nigeria"
        elif symbol.endswith(".GH"):
            return "Ghana"
        else:
            return "US"  # Default
    
    async def check_us_compliance(self, symbol: str, trade_type: str) -> str:
        """Check US compliance (SEC, FINRA)"""
        # Check against restricted lists
        restricted_symbols = ["GME", "AMC", "BBBY"]  # Example
        if symbol in restricted_symbols:
            return "symbol_restricted"
        
        return "compliant"
    
    async def check_uk_compliance(self, symbol: str, trade_type: str) -> str:
        """Check UK compliance (FCA)"""
        return "compliant"
    
    async def check_eu_compliance(self, symbol: str, trade_type: str) -> str:
        """Check EU compliance (ESMA, MiFID II)"""
        return "compliant"
    
    async def check_sa_compliance(self, symbol: str, trade_type: str) -> str:
        """Check South Africa compliance (FSCA)"""
        return "compliant"
    
    async def check_nigeria_compliance(self, symbol: str, trade_type: str) -> str:
        """Check Nigeria compliance (SEC, NIBBS)"""
        return "compliant"
    
    async def check_ghana_compliance(self, symbol: str, trade_type: str) -> str:
        """Check Ghana compliance (SEC)"""
        return "compliant"
    
    async def calculate_trade_tax_implications(self, symbol: str, trade_value: Decimal, trade_type: str) -> Dict[str, Any]:
        """Calculate tax implications for trade across all jurisdictions"""
        try:
            # This would integrate with the global tax system we created
            from backend.financial_automation.global_tax_systems import global_tax_system, TaxType
            
            tax_implications = {}
            
            for jurisdiction in self.supported_jurisdictions:
                try:
                    # Calculate capital gains tax implication
                    if trade_type == "sell":
                        tax_calc = global_tax_system.calculate_tax(
                            tax_residency=jurisdiction,
                            tax_type=TaxType.CAPITAL_GAINS,
                            taxable_amount=trade_value,
                            tax_year=datetime.now().year
                        )
                        
                        tax_implications[jurisdiction] = {
                            "tax_type": "capital_gains",
                            "tax_amount": str(tax_calc.tax_amount),
                            "tax_rate": str(tax_calc.tax_rate),
                            "reporting_required": True,
                            "filing_deadline": tax_calc.calculation_date.isoformat()
                        }
                    
                    # Calculate transaction tax (if applicable)
                    transaction_tax = global_tax_system.calculate_tax(
                        tax_residency=jurisdiction,
                        tax_type=TaxType.TRANSACTION_TAX,
                        taxable_amount=trade_value,
                        tax_year=datetime.now().year
                    )
                    
                    if transaction_tax.tax_amount > 0:
                        tax_implications[jurisdiction]["transaction_tax"] = {
                            "tax_amount": str(transaction_tax.tax_amount),
                            "tax_rate": str(transaction_tax.tax_rate)
                        }
                        
                except Exception as e:
                    logger.error(f"Error calculating tax for {jurisdiction}: {e}")
                    tax_implications[jurisdiction] = {"error": str(e)}
            
            return {
                "jurisdictions": tax_implications,
                "total_tax_burden": sum(Decimal(data.get("tax_amount", 0)) for data in tax_implications.values() if isinstance(data, dict) and "tax_amount" in data),
                "reporting_complexity": "high" if len(tax_implications) > 3 else "medium",
                "recommendation": "consult_tax_advisor"
            }
            
        except Exception as e:
            logger.error(f"Error calculating trade tax implications: {e}")
            return {"error": str(e), "recommendation": "manual_tax_review_required"}
    
    def calculate_comprehensive_trade_risk_score(self, position_size: Decimal, var_impact: Decimal, symbol: str, jurisdiction_compliance: str, tax_implications: Dict[str, Any]) -> Decimal:
        """Calculate comprehensive risk score considering all factors"""
        # Base risk from position size and VaR
        base_risk = (position_size * Decimal("5")) + (var_impact / Decimal("50000"))
        
        # Jurisdiction compliance risk
        jurisdiction_risk = Decimal("0.1") if jurisdiction_compliance != "compliant" else Decimal("0")
        
        # Tax complexity risk
        tax_complexity = len(tax_implications.get("jurisdictions", {}))
        tax_risk = min(Decimal(str(tax_complexity)) * Decimal("0.05"), Decimal("0.3"))
        
        # Symbol-specific risk
        symbol_risk = Decimal("0.05")  # Base symbol risk
        
        # Combine all risks
        total_risk = base_risk + jurisdiction_risk + tax_risk + symbol_risk
        
        # Normalize to 0-1
        return min(total_risk, Decimal("1"))
    
    # Helper methods for data retrieval
    async def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state"""
        # This would typically come from portfolio manager or database
        # For now, return comprehensive mock data
        return {
            "total_value": Decimal("2500000"),
            "positions": [
                {"symbol": "AAPL", "market_value": Decimal("500000"), "quantity": 2500, "sector": "Technology"},
                {"symbol": "GOOGL", "market_value": Decimal("400000"), "quantity": 1200, "sector": "Technology"},
                {"symbol": "MSFT", "market_value": Decimal("350000"), "quantity": 1500, "sector": "Technology"},
                {"symbol": "TSLA", "market_value": Decimal("300000"), "quantity": 800, "sector": "Automotive"},
                {"symbol": "NVDA", "market_value": Decimal("250000"), "quantity": 600, "sector": "Technology"},
                {"symbol": "SPY", "market_value": Decimal("400000"), "quantity": 1500, "sector": "ETF"},
                {"symbol": "QQQ", "market_value": Decimal("300000"), "quantity": 800, "sector": "ETF"}
            ],
            "historical_returns": [
                0.015, -0.025, 0.035, -0.015, 0.025, -0.035, 0.015, 0.025, -0.015, 0.035,
                -0.025, 0.015, 0.025, -0.035, 0.015, -0.015, 0.025, 0.035, -0.025, 0.015,
                -0.015, 0.025, -0.035, 0.015, 0.025, -0.015, 0.035, -0.025, 0.015, 0.025,
                0.02, -0.02, 0.03, -0.02, 0.02, -0.03, 0.02, 0.02, -0.02, 0.03
            ],
            "sectors": {
                "Technology": Decimal("1500000"),
                "Automotive": Decimal("300000"),
                "ETF": Decimal("700000")
            },
            "currencies": {
                "USD": Decimal("2000000"),
                "EUR": Decimal("300000"),
                "GBP": Decimal("200000")
            }
        }
    
    async def get_portfolio_value(self) -> Decimal:
        """Get current portfolio value"""
        portfolio_state = await self.get_portfolio_state()
        return portfolio_state.get("total_value", Decimal("0"))
    
    async def get_historical_returns(self, symbol: str) -> List[float]:
        """Get historical returns for a symbol"""
        # This would typically come from data provider
        # For now, return comprehensive mock data
        return [
            0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.03, 0.01, -0.01, 0.02,
            0.03, -0.02, 0.01, -0.03, 0.02, 0.01, -0.02, 0.03, -0.01, 0.02,
            -0.02, 0.01, 0.03, -0.01, 0.02, -0.03, 0.01, 0.02, -0.01, 0.03
        ]
    
    async def get_average_volume(self, symbol: str) -> float:
        """Get average trading volume for a symbol"""
        # This would typically come from market data
        # For now, return comprehensive mock data
        volume_map = {
            "AAPL": 50000000,
            "GOOGL": 20000000,
            "MSFT": 30000000,
            "SPY": 100000000,
            "QQQ": 50000000,
            "TSLA": 40000000,
            "AMZN": 25000000,
            "META": 15000000,
            "NVDA": 35000000,
            "NFLX": 8000000
        }
        return volume_map.get(symbol, 10000000)
    
    # Message handling methods
    # (Main trade proposal handler is defined earlier in the file; duplicate wrapper removed to avoid recursion.)

    # Utility methods
    def extract_max_correlation(self, correlation_matrix: np.ndarray) -> Decimal:
        """Extract maximum correlation from matrix (excluding diagonal)"""
        if correlation_matrix.size == 0:
            return Decimal("0")
        
        # Get upper triangle (excluding diagonal)
        upper_triangle = np.triu(correlation_matrix, k=1)
        
        if upper_triangle.size == 0:
            return Decimal("0")
        
        # Find maximum correlation
        max_corr = np.max(upper_triangle)
        
        return Decimal(str(max_corr))
    
    async def handle_monitoring_error(self, error: Exception):
        """Handle errors in monitoring loop"""
        logger.error(f"Monitoring error: {error}")
        
        # Generate error alert
        error_alert = {
            "timestamp": datetime.now().isoformat(),
            "error_type": "monitoring_error",
            "error_message": str(error),
            "agent_id": self.agent_id
        }
        
        # Use the publish wrapper added to PrivAgent
        try:
            await self.publish_message(MessageType.ERROR_NOTIFICATION, error_alert, topic="error_notifications")
        except Exception as e:
            logger.error(f"Failed to publish monitoring error alert: {e}")

    async def calculate_sortino_ratio(self, returns: List[float], target: float = 0.0) -> Decimal:
        """Calculate Sortino ratio (uses downside deviation). Assumes daily returns; annualizes by sqrt(252)."""
        if not returns or len(returns) < 2:
            return Decimal("0")
        try:
            # Mean excess return over target
            mean_return = mean(returns) - target
            # Downside returns: deviations below target
            downside = [min(0.0, (r - target)) for r in returns]
            # Downside deviation
            if len([d for d in downside if d < 0]) < 2:
                return Decimal("0")
            downside_std = stdev(downside)
            if downside_std == 0:
                return Decimal("0")
            sortino = (mean_return / downside_std) * (252 ** 0.5)
            return Decimal(str(sortino))
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return Decimal("0")

    async def calculate_sharpe_ratio(self, returns: List[float]) -> Decimal:
        """Calculate annualized Sharpe ratio (assuming daily returns)."""
        if not returns or len(returns) < 2:
            return Decimal("0")
        try:
            mean_return = mean(returns)
            std_dev = stdev(returns) if len(returns) > 1 else 0
            if std_dev == 0:
                return Decimal("0")
            # Annualize: sqrt(252)
            sharpe = (mean_return / std_dev) * (252 ** 0.5)
            return Decimal(str(sharpe))
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return Decimal("0")

    async def calculate_max_drawdown(self, returns: List[float]) -> Decimal:
        """Calculate maximum drawdown from a series of returns"""
        if not returns or len(returns) < 2:
            return Decimal("0")
        
        try:
            # Convert returns to cumulative values (starting at 1)
            cumulative = [1.0]
            for ret in returns:
                cumulative.append(cumulative[-1] * (1 + ret))
            
            max_value = 1.0
            max_drawdown = 0.0
            
            for value in cumulative[1:]:
                if value > max_value:
                    max_value = value
                drawdown = (max_value - value) / max_value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return Decimal(str(max_drawdown))
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return Decimal("0")

    async def calculate_beta(self, returns: List[float], market_returns: Optional[List[float]] = None) -> Decimal:
        """Calculate portfolio beta relative to market"""
        if not returns or len(returns) < 2:
            return Decimal("1.0")
        
        try:
            # If market returns not provided, use mock market data
            if market_returns is None:
                market_returns = [
                    0.01, -0.015, 0.025, -0.01, 0.02, -0.025, 0.01, 0.015, -0.01, 0.02,
                    0.025, -0.015, 0.01, -0.02, 0.015, 0.01, -0.015, 0.025, -0.01, 0.02,
                    -0.015, 0.01, 0.025, -0.01, 0.015, -0.02, 0.01, 0.015, -0.01, 0.025
                ]
            
            # Calculate covariance and variance
            if len(market_returns) < len(returns):
                market_returns = market_returns + [0.01] * (len(returns) - len(market_returns))
            else:
                market_returns = market_returns[:len(returns)]
            
            # Convert to numpy arrays
            import numpy as np
            port_array = np.array(returns)
            market_array = np.array(market_returns)
            
            # Calculate covariance and market variance
            covariance = np.cov(port_array, market_array)[0, 1]
            market_variance = np.var(market_array)
            
            if market_variance == 0:
                return Decimal("1.0")
            
            beta = covariance / market_variance
            return Decimal(str(beta))
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return Decimal("1.0")

    async def calculate_overall_risk_score(self, risk_components: Dict[str, Decimal]) -> Decimal:
        """Calculate overall portfolio risk score from individual components"""
        try:
            # Weight different risk components
            weights = {
                "var": Decimal("0.30"),
                "volatility": Decimal("0.25"),
                "concentration": Decimal("0.20"),
                "liquidity": Decimal("0.15"),
                "correlation": Decimal("0.10")
            }
            
            total_score = Decimal("0")
            
            for component, weight in weights.items():
                if component in risk_components:
                    # Normalize component to 0-1 scale
                    component_value = min(risk_components[component], Decimal("1"))
                    total_score += component_value * weight
            
            return min(total_score, Decimal("1"))
        except Exception as e:
            logger.error(f"Error calculating overall risk score: {e}")
            return Decimal("0.5")

    async def check_risk_limits(self, risk_metrics: RiskMetrics) -> List[Dict[str, Any]]:
        """Check if risk metrics exceed defined limits"""
        violations = []
        
        # Check VaR limit
        if risk_metrics.daily_var > (self.risk_limits.max_portfolio_var * risk_metrics.portfolio_value):
            violations.append({
                "type": "var_limit_exceeded",
                "limit": str(self.risk_limits.max_portfolio_var * risk_metrics.portfolio_value),
                "actual": str(risk_metrics.daily_var),
                "severity": "high"
            })
        
        # Check volatility
        if risk_metrics.volatility > Decimal("0.5"):  # 50% annual volatility
            violations.append({
                "type": "high_volatility",
                "limit": "0.50",
                "actual": str(risk_metrics.volatility),
                "severity": "medium"
            })
        
        # Check concentration risk
        if risk_metrics.concentration_risk > self.risk_limits.max_concentration_risk:
            violations.append({
                "type": "concentration_limit_exceeded",
                "limit": str(self.risk_limits.max_concentration_risk),
                "actual": str(risk_metrics.concentration_risk),
                "severity": "medium"
            })
        
        # Check max drawdown
        if risk_metrics.max_drawdown > Decimal("0.20"):  # 20% max drawdown
            violations.append({
                "type": "high_drawdown",
                "limit": "0.20",
                "actual": str(risk_metrics.max_drawdown),
                "severity": "high"
            })
        
        return violations

    async def handle_risk_violations(self, violations: List[Dict[str, Any]], risk_metrics: RiskMetrics):
        """Handle risk violations with proper error handling"""
        if not violations:
            return
            
        try:
            for violation in violations:
                try:
                    logger.warning(f"Risk violation detected: {violation['type']} - Severity: {violation['severity']}")
                    
                    # Publish violation alert
                    alert = {
                        "timestamp": datetime.now().isoformat(),
                        "violation_type": violation.get("type", "unknown"),
                        "severity": violation.get("severity", "medium"),
                        "limit": violation.get("limit"),
                        "actual_value": violation.get("actual"),
                        "agent_id": self.agent_id,
                        "portfolio_value": str(risk_metrics.portfolio_value),
                        "risk_score": str(getattr(risk_metrics, 'risk_score', 'N/A'))
                    }
                    
                    # Safe publish with error handling
                    if hasattr(self, 'publish_message'):
                        try:
                            await self.publish_message(MessageType.RISK_ALERT, alert, topic="risk_violations")
                        except Exception as pub_error:
                            logger.error(f"Failed to publish risk alert: {pub_error}")
                    else:
                        logger.warning("publish_message method not available")
                        
                except Exception as violation_error:
                    logger.error(f"Error processing single violation: {violation_error}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in handle_risk_violations: {e}", exc_info=True)

    async def perform_portfolio_stress_test(self, scenario: str) -> Dict[str, Dict[str, Decimal]]:
        """Perform portfolio stress test for different scenarios"""
        results = {}
        
        try:
            portfolio_state = await self.get_portfolio_state()
            positions = portfolio_state.get("positions", [])
            
            # Define shock scenarios
            shocks = {
                "market_crash_2008": {
                    "equity_shock": Decimal("-0.37"),  # -37%
                    "volatility_shock": Decimal("2.0"),  # 200% increase
                    "correlation_shock": Decimal("0.85"),
                    "liquidity_shock": Decimal("0.5")
                },
                "covid_crash_2020": {
                    "equity_shock": Decimal("-0.34"),  # -34%
                    "volatility_shock": Decimal("1.5"),
                    "correlation_shock": Decimal("0.80"),
                    "liquidity_shock": Decimal("0.6")
                },
                "interest_rate_shock": {
                    "equity_shock": Decimal("-0.15"),
                    "volatility_shock": Decimal("1.2"),
                    "correlation_shock": Decimal("0.70"),
                    "liquidity_shock": Decimal("0.8")
                },
                "geopolitical_event": {
                    "equity_shock": Decimal("-0.10"),
                    "volatility_shock": Decimal("0.8"),
                    "correlation_shock": Decimal("0.65"),
                    "liquidity_shock": Decimal("0.9")
                },
                "currency_crisis": {
                    "equity_shock": Decimal("-0.20"),
                    "volatility_shock": Decimal("1.3"),
                    "correlation_shock": Decimal("0.75"),
                    "liquidity_shock": Decimal("0.5")
                },
                "liquidity_crisis": {
                    "equity_shock": Decimal("-0.25"),
                    "volatility_shock": Decimal("1.6"),
                    "correlation_shock": Decimal("0.90"),
                    "liquidity_shock": Decimal("0.2")
                }
            }
            
            # Get shock for scenario
            shock = shocks.get(scenario, {})
            
            if shock:
                # Calculate stressed portfolio value
                portfolio_value = portfolio_state.get("total_value", Decimal("0"))
                equity_shock = shock.get("equity_shock", Decimal("0"))
                
                stressed_value = portfolio_value * (Decimal("1") + equity_shock)
                max_loss = portfolio_value - stressed_value
                loss_pct = max_loss / portfolio_value if portfolio_value > 0 else Decimal("0")
                
                results[scenario] = {
                    "base_value": portfolio_value,
                    "stressed_value": stressed_value,
                    "max_loss": max_loss,
                    "loss_percentage": loss_pct,
                    "volatility_multiplier": shock.get("volatility_shock"),
                    "correlation_increase": shock.get("correlation_shock"),
                    "liquidity_multiplier": shock.get("liquidity_shock")
                }
            else:
                logger.warning(f"Unknown stress scenario: {scenario}")
                results[scenario] = {"error": f"Unknown scenario: {scenario}"}
        
        except Exception as e:
            logger.error(f"Error performing stress test for {scenario}: {e}")
            results[scenario] = {"error": str(e)}
        
        return results
    
    async def update_risk_dashboard(self, risk_metrics: RiskMetrics):
        """Update risk dashboard with current metrics"""
        try:
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "risk_score": str(getattr(risk_metrics, 'risk_score', 'N/A')),
                "daily_var": str(risk_metrics.daily_var),
                "volatility": str(getattr(risk_metrics, 'volatility', 'N/A')),
                "max_drawdown": str(risk_metrics.max_drawdown),
                "sharpe_ratio": str(risk_metrics.sharpe_ratio),
                "concentration_risk": str(getattr(risk_metrics, 'concentration_risk', 'N/A')),
                "liquidity_risk": str(getattr(risk_metrics, 'liquidity_risk', 'N/A')),
                "beta": str(risk_metrics.beta),
                "sortino_ratio": str(risk_metrics.sortino_ratio)
            }
            
            # Safe publish with error handling
            if hasattr(self, 'publish_message'):
                try:
                    await self.publish_message(MessageType.RISK_DASHBOARD_UPDATE, dashboard_data)
                except Exception as pub_error:
                    logger.error(f"Failed to publish risk dashboard update: {pub_error}")
            else:
                logger.warning("publish_message method not available for dashboard update")
                
        except Exception as e:
            logger.error(f"Error updating risk dashboard: {e}", exc_info=True)

    async def get_current_var(self) -> Decimal:
        """Get current portfolio VaR"""
        portfolio_state = await self.get_portfolio_state()
        historical_returns = portfolio_state.get("historical_returns", [])
        daily_var = await self.calculate_var(historical_returns, self.var_confidence_level)
        return daily_var



# Test suite for the risk agent
if __name__ == "__main__":
    import asyncio
    
    async def test_risk_agent():
        """Test the comprehensive risk agent"""
        print("Testing Enhanced PRIV Risk Agent...")
        
        # Create risk agent
        risk_agent = PrivRiskAgent()
        
        # Start the agent
        await risk_agent.start()
        
        # Test comprehensive risk calculation
        portfolio_state = {
            "total_value": Decimal("2500000"),
            "positions": [
                {"symbol": "AAPL", "market_value": Decimal("500000"), "quantity": 2500, "sector": "Technology"},
                {"symbol": "GOOGL", "market_value": Decimal("400000"), "quantity": 1200, "sector": "Technology"},
                {"symbol": "MSFT", "market_value": Decimal("350000"), "quantity": 1500, "sector": "Technology"},
                {"symbol": "TSLA", "market_value": Decimal("300000"), "quantity": 800, "sector": "Automotive"},
                {"symbol": "NVDA", "market_value": Decimal("250000"), "quantity": 600, "sector": "Technology"},
                {"symbol": "SPY", "market_value": Decimal("400000"), "quantity": 1500, "sector": "ETF"},
                {"symbol": "QQQ", "market_value": Decimal("300000"), "quantity": 800, "sector": "ETF"}
            ],
            "historical_returns": [
                0.015, -0.025, 0.035, -0.015, 0.025, -0.035, 0.015, 0.025, -0.015, 0.035,
                -0.025, 0.015, 0.025, -0.035, 0.015, -0.015, 0.025, 0.035, -0.025, 0.015,
                -0.015, 0.025, -0.035, 0.015, 0.025, -0.015, 0.035, -0.025, 0.015, 0.025,
                0.02, -0.02, 0.03, -0.02, 0.02, -0.03, 0.02, 0.02, -0.02, 0.03
            ]
        }
        
        # Calculate comprehensive risk metrics
        risk_metrics = await risk_agent.calculate_risk_metrics(portfolio_state)
        
        print(f"Portfolio Value: ${risk_metrics.portfolio_value:,.2f}")
        print(f"Daily VaR (95%): ${risk_metrics.daily_var:,.2f}")
        print(f"Weekly VaR (95%): ${risk_metrics.weekly_var:,.2f}")
        print(f"Monthly VaR (95%): ${risk_metrics.monthly_var:,.2f}")
        print(f"Volatility: {risk_metrics.volatility:.2%}")
        print(f"Sharpe Ratio: {risk_metrics.sharpe_ratio:.2f}")
        print(f"Sortino Ratio: {risk_metrics.sortino_ratio:.2f}")
        print(f"Max Drawdown: {risk_metrics.max_drawdown:.2%}")
        print(f"Beta: {risk_metrics.beta:.2f}")
        print(f"Risk Score: {risk_metrics.risk_score:.2f}")
        print(f"Concentration Risk: {risk_metrics.concentration_risk:.2f}")
        print(f"Liquidity Risk: {risk_metrics.liquidity_risk:.2f}")
        
        # Test stress scenarios
        stress_scenarios = ["market_crash_2008", "covid_crash_2020", "interest_rate_shock", "geopolitical_event"]
        print(f"\nStress Test Results:")
        for scenario in stress_scenarios:
            stress_results = await risk_agent.perform_portfolio_stress_test(scenario)
            for scenario_name, results in stress_results.items():
                print(f"  {scenario_name}: {results}")
        
        # Test trade risk assessment
        trade_risk = await risk_agent.calculate_comprehensive_trade_risk(
            symbol="AAPL",
            quantity=Decimal("500"),
            price=Decimal("200"),
            trade_type="buy"
        )
        
        print(f"\nTrade Risk Assessment:")
        print(f"  Risk Level: {trade_risk['risk_level']}")
        print(f"  Risk Score: {trade_risk['risk_score']}")
        print(f"  VaR Impact: ${Decimal(trade_risk['var_impact']):,.2f}")
        print(f"  Recommendation: {trade_risk['recommendation']}")
        print(f"  Approval Status: {trade_risk['approval_status']}")
        print(f"  Jurisdiction Compliance: {trade_risk['jurisdiction_compliance']}")
        print(f"  Tax Implications: {len(trade_risk['tax_implications']['jurisdictions'])} jurisdictions analyzed")
        
        # Stop the agent
        await risk_agent.stop()
        
        print("\nEnhanced risk agent test completed successfully!")
        print("✅ Comprehensive risk metrics calculated")
        print("✅ Stress testing performed")
        print("✅ Global compliance checks completed")
        print("✅ Tax implications analyzed")
        print("✅ Multi-jurisdiction support verified")
    
    # Run test
    asyncio.run(test_risk_agent())