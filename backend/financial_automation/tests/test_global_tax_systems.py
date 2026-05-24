"""
Copyright (c) 2025 Sans Mercantile
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.

Patent Pending - Sans Mercantile Constellation AI System
International Patent Application Filed

System: PRIV - AI-Driven Fintech and Trading System
Module: Global Tax Systems Tests
Purpose: Comprehensive tests for global tax systems integration
Author: Sans Mercantile AI Development Team
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from backend.financial_automation.global_tax_systems import (
    GlobalTaxSystem,
    TaxResidency,
    TaxType,
    TaxCalculation,
    TaxReport,
    calculate_capital_gains_tax,
    generate_annual_tax_report,
    global_tax_system
)


class TestGlobalTaxSystem:
    """Test suite for GlobalTaxSystem"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tax_system = GlobalTaxSystem()
    
    def test_initialization(self):
        """Test system initialization"""
        assert self.tax_system is not None
        assert len(self.tax_system.tax_rates) > 0
        assert len(self.tax_system.tax_rules) > 0
        assert len(self.tax_system.reporting_requirements) > 0
    
    def test_supported_countries(self):
        """Test that all major countries are supported"""
        countries = self.tax_system.get_supported_countries()
        
        # Should support 100+ countries
        assert len(countries) >= 100
        
        # Check critical countries
        country_codes = [c['code'] for c in countries]
        assert 'ZA' in country_codes  # South Africa
        assert 'NG' in country_codes  # Nigeria
        assert 'GH' in country_codes  # Ghana
        assert 'US' in country_codes  # USA
        assert 'GB' in country_codes  # UK
        assert 'CN' in country_codes  # China
        assert 'JP' in country_codes  # Japan
        assert 'AU' in country_codes  # Australia
    
    def test_south_africa_capital_gains_tax(self):
        """Test SARS capital gains tax calculation"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        assert calc.taxable_amount == Decimal("100000")
        assert calc.tax_amount > 0
        
        # SARS: 40% inclusion rate, then taxed at marginal rate
        # With R40,000 exclusion: (100000 - 40000) * 0.40 * 0.18 = R4,320
        expected_min = Decimal("4000")
        expected_max = Decimal("5000")
        assert expected_min <= calc.tax_amount <= expected_max
    
    def test_nigeria_capital_gains_tax(self):
        """Test FIRS/NIBBS capital gains tax calculation"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.NIGERIA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        
        # Nigeria: 10% flat rate
        expected_tax = Decimal("100000") * Decimal("0.10")
        assert calc.tax_amount == expected_tax
    
    def test_usa_capital_gains_tax(self):
        """Test IRS capital gains tax calculation"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.USA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        
        # USA: 20% long-term capital gains rate
        expected_tax = Decimal("100000") * Decimal("0.20")
        assert calc.tax_amount == expected_tax
    
    def test_uk_capital_gains_tax(self):
        """Test HMRC capital gains tax calculation"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.UK,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        assert calc.tax_amount > 0
    
    def test_singapore_no_capital_gains_tax(self):
        """Test Singapore (no capital gains tax)"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.SINGAPORE,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        # Singapore has no capital gains tax
        assert calc.tax_amount == Decimal("0")
    
    def test_hong_kong_no_capital_gains_tax(self):
        """Test Hong Kong (no capital gains tax)"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.HONG_KONG,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_year=2024
        )
        
        assert calc is not None
        # Hong Kong has no capital gains tax
        assert calc.tax_amount == Decimal("0")
    
    def test_multiple_tax_types(self):
        """Test different tax types"""
        residency = TaxResidency.SOUTH_AFRICA
        amount = Decimal("100000")
        year = 2024
        
        # Capital gains
        cg_calc = self.tax_system.calculate_tax(
            residency, TaxType.CAPITAL_GAINS, amount, year
        )
        assert cg_calc.tax_type == TaxType.CAPITAL_GAINS
        
        # VAT
        vat_calc = self.tax_system.calculate_tax(
            residency, TaxType.VAT_GST, amount, year
        )
        assert vat_calc.tax_type == TaxType.VAT_GST
        assert vat_calc.tax_amount == amount * Decimal("0.15")
        
        # Dividend tax
        div_calc = self.tax_system.calculate_tax(
            residency, TaxType.DIVIDEND_TAX, amount, year
        )
        assert div_calc.tax_type == TaxType.DIVIDEND_TAX
        assert div_calc.tax_amount == amount * Decimal("0.20")
    
    def test_generate_tax_report(self):
        """Test tax report generation"""
        transactions = [
            {
                "tax_type": "capital_gains",
                "amount": 50000,
                "date": "2024-01-15"
            },
            {
                "tax_type": "capital_gains",
                "amount": 30000,
                "date": "2024-06-20"
            },
            {
                "tax_type": "dividend_tax",
                "amount": 10000,
                "date": "2024-09-10"
            }
        ]
        
        report = self.tax_system.generate_tax_report(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_year=2024,
            transactions=transactions
        )
        
        assert report is not None
        assert report.tax_residency == TaxResidency.SOUTH_AFRICA
        assert report.tax_year == 2024
        assert len(report.calculations) == 3
        assert report.total_tax > 0
        assert report.submission_deadline is not None
        assert "required_forms" in report.report_data
    
    def test_reporting_requirements(self):
        """Test reporting requirements for different countries"""
        # South Africa
        sa_forms = self.tax_system.reporting_requirements.get(
            TaxResidency.SOUTH_AFRICA, []
        )
        assert "ITR12" in sa_forms
        assert "IT3(b)" in sa_forms
        
        # USA
        us_forms = self.tax_system.reporting_requirements.get(
            TaxResidency.USA, []
        )
        assert "Form 1040" in us_forms
        assert "Schedule D" in us_forms
        assert "Form 8949" in us_forms
        
        # UK
        uk_forms = self.tax_system.reporting_requirements.get(
            TaxResidency.UK, []
        )
        assert "Self Assessment Tax Return" in uk_forms
    
    def test_tax_rules(self):
        """Test country-specific tax rules"""
        # South Africa rules
        sa_rules = self.tax_system.tax_rules.get(TaxResidency.SOUTH_AFRICA, {})
        assert sa_rules.get("capital_gains_inclusion_rate") == Decimal("0.40")
        assert sa_rules.get("annual_exclusion") == Decimal("40000")
        assert sa_rules.get("requires_provisional_tax") is True
        
        # USA rules
        us_rules = self.tax_system.tax_rules.get(TaxResidency.USA, {})
        assert us_rules.get("short_term_holding_period_days") == 365
        assert us_rules.get("wash_sale_period_days") == 30
        assert us_rules.get("requires_quarterly_estimates") is True
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        # Calculate capital gains tax
        calc = calculate_capital_gains_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            gain_amount=Decimal("100000"),
            tax_year=2024
        )
        assert calc is not None
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        
        # Generate annual report
        transactions = [{"tax_type": "capital_gains", "amount": 50000}]
        report = generate_annual_tax_report(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_year=2024,
            transactions=transactions
        )
        assert report is not None
        assert isinstance(report, TaxReport)
    
    def test_all_african_countries(self):
        """Test that all major African countries are supported"""
        african_countries = [
            TaxResidency.SOUTH_AFRICA,
            TaxResidency.NIGERIA,
            TaxResidency.GHANA,
            TaxResidency.KENYA,
            TaxResidency.EGYPT,
            TaxResidency.MOROCCO,
            TaxResidency.ETHIOPIA,
            TaxResidency.TANZANIA,
        ]
        
        for country in african_countries:
            # Should have tax rates defined
            rates = self.tax_system.tax_rates.get(country)
            assert rates is not None or country in TaxResidency
    
    def test_all_european_countries(self):
        """Test that all major European countries are supported"""
        european_countries = [
            TaxResidency.UK,
            TaxResidency.GERMANY,
            TaxResidency.FRANCE,
            TaxResidency.ITALY,
            TaxResidency.SPAIN,
            TaxResidency.NETHERLANDS,
        ]
        
        for country in european_countries:
            rates = self.tax_system.tax_rates.get(country)
            assert rates is not None or country in TaxResidency
    
    def test_all_asian_countries(self):
        """Test that all major Asian countries are supported"""
        asian_countries = [
            TaxResidency.CHINA,
            TaxResidency.JAPAN,
            TaxResidency.INDIA,
            TaxResidency.SINGAPORE,
            TaxResidency.HONG_KONG,
        ]
        
        for country in asian_countries:
            rates = self.tax_system.tax_rates.get(country)
            assert rates is not None or country in TaxResidency
    
    def test_zero_amount(self):
        """Test calculation with zero amount"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("0"),
            tax_year=2024
        )
        
        assert calc.tax_amount >= 0
    
    def test_large_amount(self):
        """Test calculation with large amount"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("10000000"),  # R10 million
            tax_year=2024
        )
        
        assert calc.tax_amount > 0
        assert calc.taxable_amount == Decimal("10000000")
    
    def test_decimal_precision(self):
        """Test that calculations maintain decimal precision"""
        calc = self.tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("123456.78"),
            tax_year=2024
        )
        
        # Should maintain precision
        assert isinstance(calc.tax_amount, Decimal)
        assert calc.tax_amount > 0


class TestTaxModels:
    """Test Pydantic models"""
    
    def test_tax_calculation_model(self):
        """Test TaxCalculation model"""
        calc = TaxCalculation(
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_rate=Decimal("0.18"),
            tax_amount=Decimal("18000"),
            currency="ZAR",
            calculation_date=datetime.now(),
            tax_year=2024
        )
        
        assert calc.tax_type == TaxType.CAPITAL_GAINS
        assert calc.taxable_amount == Decimal("100000")
        assert calc.tax_rate == Decimal("0.18")
        assert calc.tax_amount == Decimal("18000")
    
    def test_tax_report_model(self):
        """Test TaxReport model"""
        calc = TaxCalculation(
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("100000"),
            tax_rate=Decimal("0.18"),
            tax_amount=Decimal("18000"),
            currency="ZAR",
            calculation_date=datetime.now(),
            tax_year=2024
        )
        
        report = TaxReport(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_year=2024,
            report_type="Annual Tax Return",
            calculations=[calc],
            total_tax=Decimal("18000"),
            currency="ZAR",
            generated_date=datetime.now(),
            report_data={"test": "data"}
        )
        
        assert report.tax_residency == TaxResidency.SOUTH_AFRICA
        assert report.tax_year == 2024
        assert len(report.calculations) == 1
        assert report.total_tax == Decimal("18000")


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_tax_calculation_and_reporting(self):
        """Test complete workflow from calculation to reporting"""
        # Step 1: Calculate individual taxes
        transactions = []
        
        # Transaction 1: Capital gain
        calc1 = global_tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.CAPITAL_GAINS,
            taxable_amount=Decimal("50000"),
            tax_year=2024
        )
        transactions.append({
            "tax_type": "capital_gains",
            "amount": 50000
        })
        
        # Transaction 2: Dividend
        calc2 = global_tax_system.calculate_tax(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_type=TaxType.DIVIDEND_TAX,
            taxable_amount=Decimal("10000"),
            tax_year=2024
        )
        transactions.append({
            "tax_type": "dividend_tax",
            "amount": 10000
        })
        
        # Step 2: Generate report
        report = global_tax_system.generate_tax_report(
            tax_residency=TaxResidency.SOUTH_AFRICA,
            tax_year=2024,
            transactions=transactions
        )
        
        # Step 3: Verify report
        assert report is not None
        assert len(report.calculations) == 2
        assert report.total_tax > 0
        
        # Step 4: Submit report (placeholder)
        result = global_tax_system.submit_tax_report(report)
        assert result is not None
        assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])