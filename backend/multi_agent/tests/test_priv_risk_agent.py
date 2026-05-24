"""
Copyright (c) 2025 Sans Mercantile
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.

Patent Pending - Sans Mercantile Constellation AI System
International Patent Application Filed

System: PRIV - AI-Driven Fintech and Trading System
Module: Priv Risk Agent Tests
Purpose: Comprehensive tests for enhanced risk management agent
Author: Sans Mercantile AI Development Team
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
import numpy as np

from backend.multi_agent.priv_risk_agent import (
    PrivRiskAgent, RiskMetrics, RiskLimits
)
from backend.multi_agent.priv_agent_protocol import (
    AgentMessage, MessageType, TradeProposal, ArbitrationVote
)


class TestPrivRiskAgent:
    """Comprehensive test suite for PrivRiskAgent"""
    
    @pytest.fixture
    async def risk_agent(self):
        """Create risk agent for testing"""
        agent = PrivRiskAgent()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio data for testing"""
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
            ]
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, risk_agent):
        """Test risk agent initialization"""
        assert risk_agent.agent_type.value == "RISK_AGENT"
        assert risk_agent.agent_id == "priv_risk_agent_001"
        assert risk_agent.risk_limits.max_exposure_per_symbol == Decimal("0.10")
        assert risk_agent.var_confidence_level == Decimal("0.95")
        assert len(risk_agent.stress_test_scenarios) == 8
    
    @pytest.mark.asyncio
    async def test_risk_metrics_calculation(self, risk_agent, sample_portfolio):
        """Test comprehensive risk metrics calculation"""
        risk_metrics = await risk_agent.calculate_risk_metrics(sample_portfolio)
        
        assert risk_metrics is not None
        assert risk_metrics.portfolio_value == Decimal("2500000")
        assert risk_metrics.daily_var > 0
        assert risk_metrics.weekly_var > risk_metrics.daily_var
        assert risk_metrics.monthly_var > risk_metrics.weekly_var
        assert risk_metrics.volatility > 0
        assert isinstance(risk_metrics.correlation_matrix, np.ndarray)
        assert risk_metrics.concentration_risk >= 0
        assert risk_metrics.liquidity_risk >= 0
        assert risk_metrics.risk_score >= 0
    
    @pytest.mark.asyncio
    async def test_var_calculation(self, risk_agent):
        """Test Value at Risk calculation"""
        returns = [0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.03, 0.01, -0.01, 0.02]
        var_95 = await risk_agent.calculate_var(returns, Decimal("0.95"))
        
        assert var_95 >= 0
        assert isinstance(var_95, Decimal)
    
    @pytest.mark.asyncio
    async def test_volatility_calculation(self, risk_agent):
        """Test volatility calculation"""
        returns = [0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.03, 0.01, -0.01, 0.02]
        volatility = await risk_agent.calculate_volatility(returns)
        
        assert volatility > 0
        assert isinstance(volatility, Decimal)
        # Annualized volatility should be reasonable
        assert volatility > Decimal("0.1") and volatility < Decimal("2.0")
    
    @pytest.mark.asyncio
    async def test_concentration_risk_calculation(self, risk_agent, sample_portfolio):
        """Test concentration risk calculation"""
        positions = sample_portfolio["positions"]
        concentration_risk = await risk_agent.calculate_concentration_risk(positions)
        
        assert concentration_risk >= 0
        assert concentration_risk <= 1
        assert isinstance(concentration_risk, Decimal)
    
    @pytest.mark.asyncio
    async def test_liquidity_risk_calculation(self, risk_agent, sample_portfolio):
        """Test liquidity risk calculation"""
        positions = sample_portfolio["positions"]
        liquidity_risk = await risk_agent.calculate_liquidity_risk(positions)
        
        assert liquidity_risk >= 0
        assert liquidity_risk <= 1
        assert isinstance(liquidity_risk, Decimal)
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, risk_agent):
        """Test Sharpe and Sortino ratio calculations"""
        returns = [0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.03, 0.01, -0.01, 0.02]
        
        sharpe = await risk_agent.calculate_sharpe_ratio(returns)
        sortino = await risk_agent.calculate_sortino_ratio(returns)
        
        assert isinstance(sharpe, Decimal)
        assert isinstance(sortino, Decimal)
        # Sharpe ratio can be negative but should be reasonable
        assert sharpe > Decimal("-5") and sharpe < Decimal("5")
    
    @pytest.mark.asyncio
    async def test_overall_risk_score_calculation(self, risk_agent):
        """Test overall risk score calculation"""
        risk_factors = {
            "var": Decimal("50000"),
            "volatility": Decimal("0.25"),
            "concentration": Decimal("0.3"),
            "liquidity": Decimal("0.2"),
            "correlation": Decimal("0.7")
        }
        
        risk_score = await risk_agent.calculate_overall_risk_score(risk_factors)
        
        assert risk_score >= 0
        assert risk_score <= 1
        assert isinstance(risk_score, Decimal)
    
    @pytest.mark.asyncio
    async def test_risk_limit_violations(self, risk_agent, sample_portfolio):
        """Test risk limit violation detection"""
        risk_metrics = await risk_agent.calculate_risk_metrics(sample_portfolio)
        violations = await risk_agent.check_risk_limits(risk_metrics)
        
        assert isinstance(violations, list)
        # Should detect violations if any limits are exceeded
        for violation in violations:
            assert "type" in violation
            assert "severity" in violation
            assert "value" in violation
            assert "limit" in violation
    
    @pytest.mark.asyncio
    async def test_stress_testing(self, risk_agent, sample_portfolio):
        """Test stress testing scenarios"""
        risk_metrics = await risk_agent.calculate_risk_metrics(sample_portfolio)
        stress_results = await risk_agent.perform_stress_testing(risk_metrics)
        
        assert isinstance(stress_results, dict)
        assert len(stress_results) == len(risk_agent.stress_test_scenarios)
        
        for scenario, results in stress_results.items():
            assert scenario in risk_agent.stress_test_scenarios
            assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_trade_risk_assessment(self, risk_agent):
        """Test comprehensive trade risk assessment"""
        trade_risk = await risk_agent.calculate_comprehensive_trade_risk(
            symbol="AAPL",
            quantity=Decimal("500"),
            price=Decimal("200"),
            trade_type="buy"
        )
        
        assert trade_risk is not None
        assert "risk_level" in trade_risk
        assert "risk_score" in trade_risk
        assert "var_impact" in trade_risk
        assert "concentration_impact" in trade_risk
        assert "liquidity_impact" in trade_risk
        assert "jurisdiction_compliance" in trade_risk
        assert "tax_implications" in trade_risk
        assert "approval_status" in trade_risk
        assert "monitoring_requirements" in trade_risk
        
        # Test specific values
        assert trade_risk["risk_level"] in ["low", "medium", "high", "unknown"]
        assert 0 <= float(trade_risk["risk_score"]) <= 1
        assert float(trade_risk["var_impact"]) >= 0
    
    @pytest.mark.asyncio
    async def test_jurisdiction_compliance(self, risk_agent):
        """Test jurisdiction compliance checking"""
        compliance = await risk_agent.check_jurisdiction_compliance("AAPL", "buy")
        
        assert compliance in ["compliant", "jurisdiction_not_supported", "symbol_restricted", "compliance_error"]
    
    @pytest.mark.asyncio
    async def test_tax_implications_calculation(self, risk_agent):
        """Test tax implications calculation"""
        tax_implications = await risk_agent.calculate_trade_tax_implications(
            "AAPL", Decimal("100000"), "sell"
        )
        
        assert "jurisdictions" in tax_implications
        assert "total_tax_burden" in tax_implications
        assert "reporting_complexity" in tax_implications
        assert isinstance(tax_implications["jurisdictions"], dict)
        assert len(tax_implications["jurisdictions"]) > 0
    
    @pytest.mark.asyncio
    async def test_risk_report_generation(self, risk_agent, sample_portfolio):
        """Test risk report generation"""
        risk_report = await risk_agent.generate_risk_report(
            tax_residency="ZA",  # South Africa
            tax_year=2024,
            transactions=[{"tax_type": "capital_gains", "amount": 50000}]
        )
        
        assert risk_report is not None
        assert risk_report.tax_residency == "ZA"
        assert risk_report.tax_year == 2024
        assert len(risk_report.calculations) > 0
        assert risk_report.total_tax > 0
        assert risk_report.submission_deadline is not None
    
    @pytest.mark.asyncio
    async def test_message_handling(self, risk_agent):
        """Test trade proposal message handling"""
        trade_message = AgentMessage(
            message_type=MessageType.TRADE_PROPOSAL,
            sender_id="test_agent",
            recipient_id=risk_agent.agent_id,
            data={
                "trade_proposal": {
                    "trade_id": "test_trade_001",
                    "symbol": "AAPL",
                    "quantity": 100,
                    "price": 150.0,
                    "type": "buy"
                }
            },
            timestamp=datetime.now()
        )
        
        await risk_agent.handle_trade_proposal(trade_message)
        
        # The agent should process the message and generate a vote
        # (In a real test, we'd mock the message broker to verify the vote was sent)
    
    def test_risk_limits_dataclass(self):
        """Test RiskLimits dataclass"""
        limits = RiskLimits()
        assert limits.max_exposure_per_symbol == Decimal("0.10")
        assert limits.max_daily_loss_pct == Decimal("0.05")
        assert limits.max_portfolio_var == Decimal("0.02")
        
        # Test custom limits
        custom_limits = RiskLimits(
            max_exposure_per_symbol=Decimal("0.15"),
            max_daily_loss_pct=Decimal("0.03")
        )
        assert custom_limits.max_exposure_per_symbol == Decimal("0.15")
        assert custom_limits.max_daily_loss_pct == Decimal("0.03")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, risk_agent):
        """Test error handling in risk calculations"""
        # Test with empty data
        empty_portfolio = {"total_value": Decimal("0"), "positions": [], "historical_returns": []}
        
        risk_metrics = await risk_agent.calculate_risk_metrics(empty_portfolio)
        
        # Should handle gracefully
        assert risk_metrics.portfolio_value == Decimal("0")
        assert risk_metrics.daily_var == Decimal("0")
        assert risk_metrics.volatility == Decimal("0")
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, risk_agent, sample_portfolio):
        """Test performance under multiple calculations"""
        import time
        
        start_time = time.time()
        
        # Perform multiple risk calculations
        for i in range(10):
            risk_metrics = await risk_agent.calculate_risk_metrics(sample_portfolio)
            assert risk_metrics is not None
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 5 seconds for 10 calculations)
        assert execution_time < 5.0
        
        print(f"Performance test: {execution_time:.2f} seconds for 10 calculations")


class TestRiskMetrics:
    """Test RiskMetrics dataclass"""
    
    def test_risk_metrics_creation(self):
        """Test creating RiskMetrics instance"""
        risk_metrics = RiskMetrics(
            portfolio_value=Decimal("1000000"),
            daily_var=Decimal("20000"),
            weekly_var=Decimal("45000"),
            monthly_var=Decimal("100000"),
            max_drawdown=Decimal("0.15"),
            sharpe_ratio=Decimal("1.2"),
            sortino_ratio=Decimal("1.5"),
            beta=Decimal("1.1"),
            correlation_matrix=np.array([[1.0, 0.5], [0.5, 1.0]]),
            concentration_risk=Decimal("0.25"),
            liquidity_risk=Decimal("0.1"),
            volatility=Decimal("0.2"),
            risk_score=Decimal("0.6")
        )
        
        assert risk_metrics.portfolio_value == Decimal("1000000")
        assert risk_metrics.daily_var == Decimal("20000")
        assert risk_metrics.sharpe_ratio == Decimal("1.2")
        assert isinstance(risk_metrics.correlation_matrix, np.ndarray)


class TestIntegration:
    """Integration tests with other systems"""
    
    @pytest.mark.asyncio
    async def test_integration_with_global_tax_system(self, risk_agent):
        """Test integration with global tax system"""
        from backend.financial_automation.global_tax_systems import global_tax_system, TaxResidency, TaxType
        
        # Test tax calculation integration
        tax_calc = global_tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("50000"),
            tax_year=2024
        )
        
        assert tax_calc is not None
        assert tax_calc.tax_amount > 0
        assert tax_calc.tax_rate > 0
    
    @pytest.mark.asyncio
    async def test_integration_with_shared_resources(self, risk_agent):
        """Test integration with shared resources"""
        # Test that agent can access shared resources
        # This would typically involve mocking the HTTP client
        pass
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, risk_agent, sample_portfolio):
        """Test complete end-to-end workflow"""
        # Step 1: Calculate risk metrics
        risk_metrics = await risk_agent.calculate_risk_metrics(sample_portfolio)
        
        # Step 2: Check for violations
        violations = await risk_agent.check_risk_limits(risk_metrics)
        
        # Step 3: Generate stress test results
        stress_results = await risk_agent.perform_stress_testing(risk_metrics)
        
        # Step 4: Generate risk report
        risk_report = await risk_agent.generate_risk_report(
            tax_residency="ZA",
            tax_year=2024,
            transactions=[{"tax_type": "capital_gains", "amount": 50000}]
        )
        
        # Verify all steps completed successfully
        assert risk_metrics is not None
        assert isinstance(violations, list)
        assert isinstance(stress_results, dict)
        assert risk_report is not None
        assert risk_report.tax_residency == "ZA"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])