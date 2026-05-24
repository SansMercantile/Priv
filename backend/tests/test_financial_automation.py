"""
Unit tests for PRIV Financial Automation
"""

import pytest
from decimal import Decimal
from datetime import date
from backend.financial_automation.global_tax_systems import (
    GlobalTaxSystem,
    TaxResidency,
    TaxType,
    calculate_capital_gains_tax,
    generate_annual_tax_report
)


@pytest.fixture
def tax_system():
    """Create tax system instance"""
    return GlobalTaxSystem()


def test_tax_system_initialization(tax_system):
    """Test tax system initialization"""
    assert tax_system is not None
    assert len(tax_system.tax_rates) > 0
    assert len(tax_system.tax_rules) > 0


def test_currency_mapping(tax_system):
    """Test currency mapping for different residencies"""
    assert tax_system._get_currency_for_residency(TaxResidency.SOUTH_AFRICA) == "ZAR"
    assert tax_system._get_currency_for_residency(TaxResidency.USA) == "USD"
    assert tax_system._get_currency_for_residency(TaxResidency.UK) == "GBP"
    assert tax_system._get_currency_for_residency(TaxResidency.GERMANY) == "EUR"
    assert tax_system._get_currency_for_residency(TaxResidency.JAPAN) == "JPY"


def test_capital_gains_calculation(tax_system):
    """Test capital gains tax calculation"""
    calc = tax_system.calculate_tax(
        tax_residency=TaxResidency.SOUTH_AFRICA,
        tax_type=TaxType.CAPITAL_GAINS,
        taxable_amount=Decimal("100000"),
        tax_year=2024
    )
    
    assert calc.taxable_amount == Decimal("100000")
    assert calc.tax_rate > 0
    assert calc.tax_amount > 0
    assert calc.currency == "ZAR"


def test_income_tax_calculation(tax_system):
    """Test income tax calculation"""
    calc = tax_system.calculate_tax(
        tax_residency=TaxResidency.USA,
        tax_type=TaxType.INCOME_TAX,
        taxable_amount=Decimal("200000"),
        tax_year=2024
    )
    
    assert calc.taxable_amount == Decimal("200000")
    assert calc.tax_rate > 0
    assert calc.currency == "USD"


def test_vat_calculation(tax_system):
    """Test VAT/GST calculation"""
    calc = tax_system.calculate_tax(
        tax_residency=TaxResidency.UK,
        tax_type=TaxType.VAT_GST,
        taxable_amount=Decimal("50000"),
        tax_year=2024
    )
    
    assert calc.taxable_amount == Decimal("50000")
    assert calc.tax_rate == Decimal("0.20")  # UK VAT is 20%
    assert calc.currency == "GBP"


def test_tax_report_generation(tax_system):
    """Test tax report generation"""
    transactions = [
        {
            "type": "capital_gain",
            "amount": Decimal("50000"),
            "date": "2024-06-15"
        },
        {
            "type": "dividend",
            "amount": Decimal("10000"),
            "date": "2024-09-20"
        }
    ]
    
    report = tax_system.generate_tax_report(
        tax_residency=TaxResidency.SOUTH_AFRICA,
        tax_year=2024,
        transactions=transactions
    )
    
    assert report.tax_residency == TaxResidency.SOUTH_AFRICA
    assert report.tax_year == 2024
    assert len(report.calculations) > 0
    assert report.total_tax > 0


def test_supported_countries(tax_system):
    """Test supported countries list"""
    countries = tax_system.get_supported_countries()
    
    assert len(countries) > 0
    assert any(c["code"] == "ZA" for c in countries)
    assert any(c["code"] == "US" for c in countries)
    assert any(c["code"] == "GB" for c in countries)


def test_tax_submission(tax_system):
    """Test tax report submission"""
    transactions = [{"type": "capital_gain", "amount": Decimal("100000")}]
    
    report = tax_system.generate_tax_report(
        tax_residency=TaxResidency.SOUTH_AFRICA,
        tax_year=2024,
        transactions=transactions
    )
    
    result = tax_system.submit_tax_report(
        report=report,
        submission_method="electronic"
    )
    
    assert "status" in result
    assert "submission_date" in result


def test_convenience_functions():
    """Test convenience functions"""
    calc = calculate_capital_gains_tax(
        tax_residency=TaxResidency.USA,
        gain_amount=Decimal("75000"),
        tax_year=2024
    )
    
    assert calc.taxable_amount == Decimal("75000")
    assert calc.currency == "USD"


def test_multiple_tax_types(tax_system):
    """Test calculations for multiple tax types"""
    residency = TaxResidency.CANADA
    amount = Decimal("100000")
    year = 2024
    
    # Test different tax types
    cg_calc = tax_system.calculate_tax(residency, TaxType.CAPITAL_GAINS, amount, year)
    income_calc = tax_system.calculate_tax(residency, TaxType.INCOME_TAX, amount, year)
    vat_calc = tax_system.calculate_tax(residency, TaxType.VAT_GST, amount, year)
    
    assert cg_calc.tax_amount != income_calc.tax_amount
    assert all(c.currency == "CAD" for c in [cg_calc, income_calc, vat_calc])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])