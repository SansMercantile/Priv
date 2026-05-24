# backend/risk_analysis/risk_analyzer.py

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """
    Comprehensive risk analysis engine for PRIV system.
    Analyzes market risk, portfolio risk, and systemic risk factors.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.info("RiskAnalyzer initialized")
    
    async def analyze_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze portfolio-level risk metrics.
        
        Args:
            portfolio_data: Portfolio information including positions, values, etc.
            
        Returns:
            Risk analysis results
        """
        try:
            self.logger.info("Analyzing portfolio risk")
            
            # Extract portfolio components
            positions = portfolio_data.get("positions", [])
            total_value = portfolio_data.get("total_value", 0)
            
            if not positions or total_value <= 0:
                return {"status": "error", "message": "Invalid portfolio data"}
            
            # Calculate risk metrics
            risk_metrics = await self._calculate_portfolio_metrics(positions, total_value)
            
            # Assess risk levels
            risk_assessment = self._assess_portfolio_risk_level(risk_metrics)
            
            result = {
                "status": "success",
                "risk_metrics": risk_metrics,
                "risk_assessment": risk_assessment,
                "timestamp": datetime.now().isoformat(),
                "recommendations": self._generate_risk_recommendations(risk_assessment)
            }
            
            self.logger.info(f"Portfolio risk analysis completed: {risk_assessment['overall_risk']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio risk: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def analyze_market_risk(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market-level risk factors.
        
        Args:
            market_data: Market data including indices, volatility, correlations, etc.
            
        Returns:
            Market risk analysis results
        """
        try:
            self.logger.info("Analyzing market risk")
            
            # Extract market components
            indices = market_data.get("indices", {})
            volatility_data = market_data.get("volatility", {})
            correlations = market_data.get("correlations", {})
            
            # Calculate market risk metrics
            market_metrics = await self._calculate_market_metrics(indices, volatility_data, correlations)
            
            # Assess market risk levels
            market_assessment = self._assess_market_risk_level(market_metrics)
            
            result = {
                "status": "success",
                "market_metrics": market_metrics,
                "market_assessment": market_assessment,
                "timestamp": datetime.now().isoformat(),
                "market_outlook": self._generate_market_outlook(market_assessment)
            }
            
            self.logger.info(f"Market risk analysis completed: {market_assessment['market_risk']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing market risk: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def analyze_systemic_risk(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze systemic risk factors.
        
        Args:
            system_data: System-wide data including liquidity, credit, operational metrics, etc.
            
        Returns:
            Systemic risk analysis results
        """
        try:
            self.logger.info("Analyzing systemic risk")
            
            # Extract system components
            liquidity_metrics = system_data.get("liquidity", {})
            credit_metrics = system_data.get("credit", {})
            operational_metrics = system_data.get("operational", {})
            
            # Calculate systemic risk metrics
            systemic_metrics = await self._calculate_systemic_metrics(liquidity_metrics, credit_metrics, operational_metrics)
            
            # Assess systemic risk levels
            systemic_assessment = self._assess_systemic_risk_level(systemic_metrics)
            
            result = {
                "status": "success",
                "systemic_metrics": systemic_metrics,
                "systemic_assessment": systemic_assessment,
                "timestamp": datetime.now().isoformat(),
                "system_stability": systemic_assessment['stability_score']
            }
            
            self.logger.info(f"Systemic risk analysis completed: stability={systemic_assessment['stability_score']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing systemic risk: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def _calculate_portfolio_metrics(self, positions: List[Dict[str, Any]], total_value: float) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        try:
            metrics = {}
            
            # Concentration risk
            if positions:
                position_values = [pos.get("value", 0) for pos in positions]
                total_positions = sum(position_values)
                concentration_risk = max(position_values) / total_positions if total_positions > 0 else 0
                metrics["concentration_risk"] = concentration_risk
            
            # Sector diversification
            sectors = {}
            for position in positions:
                sector = position.get("sector", "unknown")
                value = position.get("value", 0)
                sectors[sector] = sectors.get(sector, 0) + value
            
            sector_weights = {sector: value/total_value for sector, value in sectors.items() if total_value > 0}
            diversification_score = self._calculate_diversification_score(sector_weights)
            metrics["diversification_score"] = diversification_score
            
            # Value at Risk (simplified)
            var_95 = self._calculate_var_simplified(positions, confidence=0.95)
            metrics["value_at_risk_95"] = var_95
            
            # Maximum drawdown estimation
            max_drawdown = self._estimate_max_drawdown(positions)
            metrics["estimated_max_drawdown"] = max_drawdown
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}", exc_info=True)
            return {}
    
    async def _calculate_market_metrics(self, indices: Dict[str, Any], volatility_data: Dict[str, Any], 
                                      correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market risk metrics"""
        try:
            metrics = {}
            
            # Market volatility
            if volatility_data:
                avg_volatility = np.mean([v for v in volatility_data.values() if v > 0])
                metrics["average_volatility"] = avg_volatility
                
                # Volatility regime
                if avg_volatility < 15:
                    metrics["volatility_regime"] = "low"
                elif avg_volatility < 25:
                    metrics["volatility_regime"] = "moderate"
                else:
                    metrics["volatility_regime"] = "high"
            
            # Market correlation
            if correlations:
                avg_correlation = np.mean([c for c in correlations.values() if abs(c) <= 1])
                metrics["average_correlation"] = avg_correlation
                
                # Correlation regime
                if abs(avg_correlation) < 0.3:
                    metrics["correlation_regime"] = "low"
                elif abs(avg_correlation) < 0.6:
                    metrics["correlation_regime"] = "moderate"
                else:
                    metrics["correlation_regime"] = "high"
            
            # Market stress indicators
            stress_indicators = self._calculate_stress_indicators(indices)
            metrics.update(stress_indicators)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating market metrics: {e}", exc_info=True)
            return {}
    
    async def _calculate_systemic_metrics(self, liquidity_metrics: Dict[str, Any], 
                                        credit_metrics: Dict[str, Any], 
                                        operational_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate systemic risk metrics"""
        try:
            metrics = {}
            
            # Liquidity risk
            if liquidity_metrics:
                liquidity_ratio = liquidity_metrics.get("current_ratio", 1.0)
                metrics["liquidity_ratio"] = liquidity_ratio
                
                # Liquidity stress test
                stress_test_result = self._liquidity_stress_test(liquidity_metrics)
                metrics["liquidity_stress_score"] = stress_test_result
            
            # Credit risk
            if credit_metrics:
                credit_score = credit_metrics.get("credit_score", 100)
                metrics["credit_score"] = credit_score
                
                # Credit quality assessment
                if credit_score >= 80:
                    metrics["credit_quality"] = "excellent"
                elif credit_score >= 60:
                    metrics["credit_quality"] = "good"
                elif credit_score >= 40:
                    metrics["credit_quality"] = "fair"
                else:
                    metrics["credit_quality"] = "poor"
            
            # Operational risk
            if operational_metrics:
                operational_score = operational_metrics.get("operational_score", 100)
                metrics["operational_score"] = operational_score
                
                # System reliability
                uptime = operational_metrics.get("system_uptime", 100)
                metrics["system_uptime"] = uptime
                
                if uptime >= 99.9:
                    metrics["system_reliability"] = "excellent"
                elif uptime >= 99.0:
                    metrics["system_reliability"] = "good"
                else:
                    metrics["system_reliability"] = "needs_attention"
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating systemic metrics: {e}", exc_info=True)
            return {}
    
    def _assess_portfolio_risk_level(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall portfolio risk level"""
        try:
            assessment = {}
            
            # Overall risk score (0-100, higher is riskier)
            risk_score = 0
            
            # Concentration risk (0-40 points)
            concentration_risk = metrics.get("concentration_risk", 0)
            if concentration_risk > 0.25:  # >25% in single position
                risk_score += 30
            elif concentration_risk > 0.15:  # >15% in single position
                risk_score += 20
            elif concentration_risk > 0.1:   # >10% in single position
                risk_score += 10
            
            # Diversification score (0-30 points, inverted)
            diversification_score = metrics.get("diversification_score", 100)
            risk_score += max(0, (100 - diversification_score) * 0.3)
            
            # Value at Risk (0-30 points)
            var_95 = metrics.get("value_at_risk_95", 0)
            if var_95 > 0.05:  # >5% VaR
                risk_score += 30
            elif var_95 > 0.03:  # >3% VaR
                risk_score += 20
            elif var_95 > 0.02:  # >2% VaR
                risk_score += 10
            
            assessment["risk_score"] = risk_score
            
            # Risk level classification
            if risk_score >= 70:
                assessment["overall_risk"] = "high"
                assessment["risk_color"] = "red"
            elif risk_score >= 40:
                assessment["overall_risk"] = "medium"
                assessment["risk_color"] = "yellow"
            else:
                assessment["overall_risk"] = "low"
                assessment["risk_color"] = "green"
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk level: {e}", exc_info=True)
            return {"overall_risk": "unknown", "risk_color": "gray"}
    
    def _assess_market_risk_level(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall market risk level"""
        try:
            assessment = {}
            
            # Market risk factors
            volatility_regime = metrics.get("volatility_regime", "moderate")
            correlation_regime = metrics.get("correlation_regime", "moderate")
            
            # Overall market risk
            if volatility_regime == "high" or correlation_regime == "high":
                assessment["market_risk"] = "high"
                assessment["market_color"] = "red"
            elif volatility_regime == "moderate" or correlation_regime == "moderate":
                assessment["market_risk"] = "medium"
                assessment["market_color"] = "yellow"
            else:
                assessment["market_risk"] = "low"
                assessment["market_color"] = "green"
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing market risk level: {e}", exc_info=True)
            return {"market_risk": "unknown", "market_color": "gray"}
    
    def _assess_systemic_risk_level(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall systemic risk level"""
        try:
            assessment = {}
            
            # Stability score (0-100, higher is more stable)
            stability_components = []
            
            # Liquidity component
            liquidity_ratio = metrics.get("liquidity_ratio", 1.0)
            if liquidity_ratio >= 2.0:
                stability_components.append(95)
            elif liquidity_ratio >= 1.5:
                stability_components.append(85)
            elif liquidity_ratio >= 1.0:
                stability_components.append(70)
            else:
                stability_components.append(40)
            
            # Credit component
            credit_score = metrics.get("credit_score", 100)
            stability_components.append(credit_score)
            
            # Operational component
            system_reliability = metrics.get("system_reliability", "good")
            reliability_scores = {"excellent": 95, "good": 80, "needs_attention": 50}
            stability_components.append(reliability_scores.get(system_reliability, 70))
            
            # Calculate overall stability score
            stability_score = np.mean(stability_components) if stability_components else 70
            
            assessment["stability_score"] = stability_score
            
            # Stability classification
            if stability_score >= 90:
                assessment["system_stability"] = "excellent"
                assessment["stability_color"] = "green"
            elif stability_score >= 75:
                assessment["system_stability"] = "good"
                assessment["stability_color"] = "green"
            elif stability_score >= 60:
                assessment["system_stability"] = "fair"
                assessment["stability_color"] = "yellow"
            else:
                assessment["system_stability"] = "poor"
                assessment["stability_color"] = "red"
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing systemic risk level: {e}", exc_info=True)
            return {"system_stability": "unknown", "stability_color": "gray"}
    
    def _calculate_diversification_score(self, sector_weights: Dict[str, float]) -> float:
        """Calculate portfolio diversification score"""
        try:
            if not sector_weights:
                return 0
            
            # Calculate Herfindahl-Hirschman Index (concentration measure)
            hhi = sum(weight**2 for weight in sector_weights.values())
            
            # Convert to diversification score (0-100, higher is better)
            num_sectors = len(sector_weights)
            max_diversification = 1.0 / num_sectors if num_sectors > 0 else 1.0
            diversification_score = max(0, (max_diversification - hhi) / max_diversification * 100)
            
            return diversification_score
            
        except Exception as e:
            self.logger.error(f"Error calculating diversification score: {e}", exc_info=True)
            return 0
    
    def _calculate_var_simplified(self, positions: List[Dict[str, Any]], confidence: float) -> float:
        """Calculate simplified Value at Risk"""
        try:
            if not positions:
                return 0
            
            # Simplified VaR calculation using historical volatility
            # In a real implementation, this would use proper statistical methods
            
            position_values = [pos.get("value", 0) for pos in positions]
            total_value = sum(position_values)
            
            if total_value <= 0:
                return 0
            
            # Estimate volatility (simplified)
            estimated_volatility = 0.02  # 2% daily volatility (simplified)
            
            # Calculate VaR using normal distribution approximation
            # VaR = Position Value * Volatility * Z-score
            from scipy.stats import norm
            z_score = norm.ppf(1 - confidence)
            var = total_value * estimated_volatility * abs(z_score)
            
            return var / total_value  # Return as percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}", exc_info=True)
            return 0
    
    def _estimate_max_drawdown(self, positions: List[Dict[str, Any]]) -> float:
        """Estimate maximum potential drawdown"""
        try:
            if not positions:
                return 0
            
            # Simplified estimation based on asset types and market conditions
            # In a real implementation, this would use historical data
            
            max_drawdown = 0
            
            for position in positions:
                asset_type = position.get("asset_type", "equity")
                
                # Different asset types have different typical max drawdowns
                if asset_type == "equity":
                    max_drawdown = max(max_drawdown, 0.50)  # 50% max drawdown for equities
                elif asset_type == "bond":
                    max_drawdown = max(max_drawdown, 0.20)  # 20% max drawdown for bonds
                elif asset_type == "commodity":
                    max_drawdown = max(max_drawdown, 0.60)  # 60% max drawdown for commodities
                else:
                    max_drawdown = max(max_drawdown, 0.40)  # 40% default
            
            return max_drawdown
            
        except Exception as e:
            self.logger.error(f"Error estimating max drawdown: {e}", exc_info=True)
            return 0
    
    def _calculate_stress_indicators(self, indices: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market stress indicators"""
        try:
            indicators = {}
            
            # VIX equivalent (simplified)
            if "vix" in indices:
                vix_value = indices["vix"]
                if vix_value > 30:
                    indicators["vix_stress"] = "high"
                elif vix_value > 20:
                    indicators["vix_stress"] = "moderate"
                else:
                    indicators["vix_stress"] = "low"
            
            # Market breadth
            if "advance_decline" in indices:
                advance_decline = indices["advance_decline"]
                if advance_decline < 0.8:
                    indicators["market_breadth"] = "weak"
                elif advance_decline > 1.2:
                    indicators["market_breadth"] = "strong"
                else:
                    indicators["market_breadth"] = "neutral"
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating stress indicators: {e}", exc_info=True)
            return {}
    
    def _liquidity_stress_test(self, liquidity_metrics: Dict[str, Any]) -> float:
        """Perform liquidity stress test"""
        try:
            # Simplified liquidity stress test
            current_ratio = liquidity_metrics.get("current_ratio", 1.0)
            quick_ratio = liquidity_metrics.get("quick_ratio", 1.0)
            cash_ratio = liquidity_metrics.get("cash_ratio", 0.2)
            
            # Stress score (0-100, higher is more stressed)
            stress_score = 0
            
            if current_ratio < 1.0:
                stress_score += 40
            elif current_ratio < 1.5:
                stress_score += 20
            
            if quick_ratio < 0.8:
                stress_score += 30
            elif quick_ratio < 1.0:
                stress_score += 15
            
            if cash_ratio < 0.1:
                stress_score += 30
            elif cash_ratio < 0.2:
                stress_score += 15
            
            return stress_score
            
        except Exception as e:
            self.logger.error(f"Error in liquidity stress test: {e}", exc_info=True)
            return 50  # Default moderate stress
    
    def _generate_risk_recommendations(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate risk management recommendations"""
        try:
            recommendations = []
            
            overall_risk = risk_assessment.get("overall_risk", "unknown")
            
            if overall_risk == "high":
                recommendations.extend([
                    "Consider reducing position sizes to limit exposure",
                    "Implement tighter stop-loss levels",
                    "Increase cash allocation for safety",
                    "Review and rebalance portfolio concentration",
                    "Consider hedging strategies for protection"
                ])
            elif overall_risk == "medium":
                recommendations.extend([
                    "Monitor positions closely for changes",
                    "Consider partial position adjustments",
                    "Review stop-loss levels periodically",
                    "Maintain current diversification levels"
                ])
            elif overall_risk == "low":
                recommendations.extend([
                    "Maintain current risk management approach",
                    "Consider opportunities for increased exposure if aligned with strategy",
                    "Continue regular portfolio monitoring"
                ])
            else:
                recommendations.append("Unable to provide specific recommendations due to insufficient risk data")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating risk recommendations: {e}", exc_info=True)
            return ["Error generating recommendations"]
    
    def _generate_market_outlook(self, market_assessment: Dict[str, Any]) -> str:
        """Generate market outlook based on risk assessment"""
        try:
            market_risk = market_assessment.get("market_risk", "unknown")
            
            if market_risk == "high":
                return "Market conditions indicate elevated risk. Expect increased volatility and potential downside pressure. Consider defensive positioning."
            elif market_risk == "medium":
                return "Market conditions are moderately risky. Maintain balanced approach with careful monitoring of developments."
            elif market_risk == "low":
                return "Market conditions appear stable with low risk. Favorable environment for risk-taking within appropriate limits."
            else:
                return "Market outlook unclear due to insufficient data. Exercise caution and maintain diversified approach."
                
        except Exception as e:
            self.logger.error(f"Error generating market outlook: {e}", exc_info=True)
            return "Market outlook unavailable due to analysis error"