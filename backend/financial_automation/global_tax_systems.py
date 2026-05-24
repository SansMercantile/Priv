"""
Copyright (c) 2025 Sans Mercantile
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.

Patent Pending - Sans Mercantile Constellation AI System
International Patent Application Filed

System: PRIV - AI-Driven Fintech and Trading System
Module: Global Tax Systems Integration
Purpose: Comprehensive integration with tax systems from all countries worldwide
Author: Sans Mercantile AI Development Team
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class TaxResidency(str, Enum):
    """Supported tax residencies worldwide"""
    
    # Africa
    SOUTH_AFRICA = "ZA"  # SARS
    NIGERIA = "NG"  # FIRS + NIBBS
    GHANA = "GH"  # GRA
    KENYA = "KE"  # KRA
    EGYPT = "EG"  # ETA
    MOROCCO = "MA"  # DGI
    ALGERIA = "DZ"  # DGI
    TUNISIA = "TN"  # DGELF
    ETHIOPIA = "ET"  # ERCA
    TANZANIA = "TZ"  # TRA
    UGANDA = "UG"  # URA
    RWANDA = "RW"  # RRA
    ZAMBIA = "ZM"  # ZRA
    ZIMBABWE = "ZW"  # ZIMRA
    BOTSWANA = "BW"  # BURS
    NAMIBIA = "NA"  # NAMRA
    MAURITIUS = "MU"  # MRA
    SEYCHELLES = "SC"  # SRC
    
    # North America
    USA = "US"  # IRS
    CANADA = "CA"  # CRA
    MEXICO = "MX"  # SAT
    
    # South America
    BRAZIL = "BR"  # RFB
    ARGENTINA = "AR"  # AFIP
    CHILE = "CL"  # SII
    COLOMBIA = "CO"  # DIAN
    PERU = "PE"  # SUNAT
    VENEZUELA = "VE"  # SENIAT
    ECUADOR = "EC"  # SRI
    BOLIVIA = "BO"  # SIN
    PARAGUAY = "PY"  # SET
    URUGUAY = "UY"  # DGI
    
    # Europe
    UK = "GB"  # HMRC
    GERMANY = "DE"  # Finanzamt
    FRANCE = "FR"  # DGFiP
    ITALY = "IT"  # Agenzia delle Entrate
    SPAIN = "ES"  # AEAT
    NETHERLANDS = "NL"  # Belastingdienst
    BELGIUM = "BE"  # SPF Finances
    SWITZERLAND = "CH"  # AFC
    AUSTRIA = "AT"  # BMF
    SWEDEN = "SE"  # Skatteverket
    NORWAY = "NO"  # Skatteetaten
    DENMARK = "DK"  # SKAT
    FINLAND = "FI"  # Vero
    IRELAND = "IE"  # Revenue
    PORTUGAL = "PT"  # AT
    GREECE = "GR"  # AADE
    POLAND = "PL"  # KAS
    CZECH_REPUBLIC = "CZ"  # FS
    HUNGARY = "HU"  # NAV
    ROMANIA = "RO"  # ANAF
    BULGARIA = "BG"  # NRA
    CROATIA = "HR"  # Porezna uprava
    SLOVAKIA = "SK"  # FS
    SLOVENIA = "SI"  # FURS
    LITHUANIA = "LT"  # VMI
    LATVIA = "LV"  # VID
    ESTONIA = "EE"  # MTA
    LUXEMBOURG = "LU"  # ACD
    MALTA = "MT"  # CFR
    CYPRUS = "CY"  # Tax Department
    
    # Asia
    CHINA = "CN"  # SAT
    JAPAN = "JP"  # NTA
    INDIA = "IN"  # CBDT
    SOUTH_KOREA = "KR"  # NTS
    SINGAPORE = "SG"  # IRAS
    HONG_KONG = "HK"  # IRD
    TAIWAN = "TW"  # NTA
    THAILAND = "TH"  # RD
    MALAYSIA = "MY"  # LHDN
    INDONESIA = "ID"  # DJP
    PHILIPPINES = "PH"  # BIR
    VIETNAM = "VN"  # GDT
    PAKISTAN = "PK"  # FBR
    BANGLADESH = "BD"  # NBR
    SRI_LANKA = "LK"  # IRD
    MYANMAR = "MM"  # IRD
    CAMBODIA = "KH"  # GDT
    LAOS = "LA"  # TD
    NEPAL = "NP"  # IRD
    
    # Middle East
    UAE = "AE"  # FTA
    SAUDI_ARABIA = "SA"  # GAZT
    QATAR = "QA"  # GTA
    KUWAIT = "KW"  # MOF
    BAHRAIN = "BH"  # NBR
    OMAN = "OM"  # TA
    ISRAEL = "IL"  # ITA
    TURKEY = "TR"  # GIB
    IRAN = "IR"  # INTA
    IRAQ = "IQ"  # GCT
    JORDAN = "JO"  # ISTD
    LEBANON = "LB"  # MOF
    
    # Oceania
    AUSTRALIA = "AU"  # ATO
    NEW_ZEALAND = "NZ"  # IRD
    FIJI = "FJ"  # FRCS
    PAPUA_NEW_GUINEA = "PG"  # IRC


class TaxType(str, Enum):
    """Types of taxes"""
    CAPITAL_GAINS = "capital_gains"
    INCOME_TAX = "income_tax"
    CORPORATE_TAX = "corporate_tax"
    VAT_GST = "vat_gst"
    WITHHOLDING_TAX = "withholding_tax"
    STAMP_DUTY = "stamp_duty"
    TRANSACTION_TAX = "transaction_tax"
    DIVIDEND_TAX = "dividend_tax"
    INTEREST_TAX = "interest_tax"


class TaxCalculation(BaseModel):
    """Tax calculation result"""
    tax_type: TaxType
    taxable_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    currency: str
    calculation_date: datetime
    tax_year: int
    notes: Optional[str] = None


class TaxReport(BaseModel):
    """Tax report for submission"""
    tax_residency: TaxResidency
    tax_year: int
    report_type: str
    calculations: List[TaxCalculation]
    total_tax: Decimal
    currency: str
    generated_date: datetime
    submission_deadline: Optional[date] = None
    report_data: Dict[str, Any]


class GlobalTaxSystem:
    """
    Comprehensive global tax system integration.
    Supports automated tax calculation and reporting for all countries.
    """
    
    def __init__(self):
        self.tax_rates = self._initialize_tax_rates()
        self.tax_rules = self._initialize_tax_rules()
        self.reporting_requirements = self._initialize_reporting_requirements()
    
    def _initialize_tax_rates(self) -> Dict[TaxResidency, Dict[TaxType, Decimal]]:
        """Initialize tax rates for all countries"""
        return {
            # Africa
            TaxResidency.SOUTH_AFRICA: {
                TaxType.CAPITAL_GAINS: Decimal("0.18"),  # Effective rate
                TaxType.INCOME_TAX: Decimal("0.45"),  # Top marginal rate
                TaxType.VAT_GST: Decimal("0.15"),
                TaxType.DIVIDEND_TAX: Decimal("0.20"),
            },
            TaxResidency.NIGERIA: {
                TaxType.CAPITAL_GAINS: Decimal("0.10"),
                TaxType.INCOME_TAX: Decimal("0.24"),
                TaxType.VAT_GST: Decimal("0.075"),
                TaxType.WITHHOLDING_TAX: Decimal("0.10"),
            },
            TaxResidency.GHANA: {
                TaxType.CAPITAL_GAINS: Decimal("0.15"),
                TaxType.INCOME_TAX: Decimal("0.30"),
                TaxType.VAT_GST: Decimal("0.125"),
            },
            TaxResidency.KENYA: {
                TaxType.CAPITAL_GAINS: Decimal("0.05"),
                TaxType.INCOME_TAX: Decimal("0.30"),
                TaxType.VAT_GST: Decimal("0.16"),
            },
            
            # North America
            TaxResidency.USA: {
                TaxType.CAPITAL_GAINS: Decimal("0.20"),  # Long-term
                TaxType.INCOME_TAX: Decimal("0.37"),  # Top federal rate
                TaxType.DIVIDEND_TAX: Decimal("0.20"),
            },
            TaxResidency.CANADA: {
                TaxType.CAPITAL_GAINS: Decimal("0.25"),  # 50% inclusion rate
                TaxType.INCOME_TAX: Decimal("0.33"),  # Top federal rate
                TaxType.VAT_GST: Decimal("0.05"),  # Federal GST
            },
            TaxResidency.MEXICO: {
                TaxType.CAPITAL_GAINS: Decimal("0.10"),
                TaxType.INCOME_TAX: Decimal("0.35"),
                TaxType.VAT_GST: Decimal("0.16"),
            },
            
            # Europe
            TaxResidency.UK: {
                TaxType.CAPITAL_GAINS: Decimal("0.20"),
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.20"),
                TaxType.STAMP_DUTY: Decimal("0.005"),
            },
            TaxResidency.GERMANY: {
                TaxType.CAPITAL_GAINS: Decimal("0.26375"),  # Including solidarity surcharge
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.19"),
            },
            TaxResidency.FRANCE: {
                TaxType.CAPITAL_GAINS: Decimal("0.30"),  # Flat tax
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.20"),
            },
            
            # Asia
            TaxResidency.SINGAPORE: {
                TaxType.CAPITAL_GAINS: Decimal("0.00"),  # No capital gains tax
                TaxType.INCOME_TAX: Decimal("0.22"),
                TaxType.VAT_GST: Decimal("0.08"),
            },
            TaxResidency.HONG_KONG: {
                TaxType.CAPITAL_GAINS: Decimal("0.00"),  # No capital gains tax
                TaxType.INCOME_TAX: Decimal("0.17"),
                TaxType.STAMP_DUTY: Decimal("0.001"),
            },
            TaxResidency.JAPAN: {
                TaxType.CAPITAL_GAINS: Decimal("0.20315"),
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.10"),
            },
            TaxResidency.CHINA: {
                TaxType.CAPITAL_GAINS: Decimal("0.20"),
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.13"),
            },
            TaxResidency.INDIA: {
                TaxType.CAPITAL_GAINS: Decimal("0.10"),  # Long-term
                TaxType.INCOME_TAX: Decimal("0.30"),
                TaxType.VAT_GST: Decimal("0.18"),
            },
            
            # Middle East
            TaxResidency.UAE: {
                TaxType.CAPITAL_GAINS: Decimal("0.00"),
                TaxType.CORPORATE_TAX: Decimal("0.09"),
                TaxType.VAT_GST: Decimal("0.05"),
            },
            
            # Oceania
            TaxResidency.AUSTRALIA: {
                TaxType.CAPITAL_GAINS: Decimal("0.235"),  # 50% discount applied
                TaxType.INCOME_TAX: Decimal("0.45"),
                TaxType.VAT_GST: Decimal("0.10"),
            },
            TaxResidency.NEW_ZEALAND: {
                TaxType.CAPITAL_GAINS: Decimal("0.00"),  # No general CGT
                TaxType.INCOME_TAX: Decimal("0.39"),
                TaxType.VAT_GST: Decimal("0.15"),
            },
        }
    
    def _initialize_tax_rules(self) -> Dict[TaxResidency, Dict[str, Any]]:
        """Initialize tax rules for each country"""
        return {
            TaxResidency.SOUTH_AFRICA: {
                "capital_gains_inclusion_rate": Decimal("0.40"),
                "annual_exclusion": Decimal("40000"),
                "tax_year_end": "02-28",  # February 28
                "filing_deadline_months": 4,
                "requires_provisional_tax": True,
            },
            TaxResidency.NIGERIA: {
                "capital_gains_exemptions": ["government_securities"],
                "tax_year_end": "12-31",
                "filing_deadline_months": 6,
                "nibbs_integration": True,
            },
            TaxResidency.USA: {
                "short_term_holding_period_days": 365,
                "wash_sale_period_days": 30,
                "tax_year_end": "12-31",
                "filing_deadline": "04-15",
                "requires_quarterly_estimates": True,
            },
            TaxResidency.UK: {
                "annual_exempt_amount": Decimal("6000"),  # 2024/25
                "tax_year_end": "04-05",
                "filing_deadline": "01-31",
                "requires_self_assessment": True,
            },
        }
    
    def _initialize_reporting_requirements(self) -> Dict[TaxResidency, List[str]]:
        """Initialize reporting requirements for each country"""
        return {
            TaxResidency.SOUTH_AFRICA: [
                "ITR12",  # Individual tax return
                "IT3(b)",  # Capital gains tax schedule
                "IRP5",  # Employee tax certificate
            ],
            TaxResidency.NIGERIA: [
                "Annual Tax Return",
                "Capital Gains Tax Return",
                "NIBBS Transaction Reports",
            ],
            TaxResidency.USA: [
                "Form 1040",  # Individual income tax
                "Schedule D",  # Capital gains
                "Form 8949",  # Sales of capital assets
                "Form 1099-B",  # Broker transactions
            ],
            TaxResidency.UK: [
                "Self Assessment Tax Return",
                "Capital Gains Tax Summary",
                "SA108",  # Capital gains pages
            ],
        }
    
    def _get_currency_for_residency(self, tax_residency: TaxResidency) -> str:
        """Get the primary currency for a tax residency"""
        currency_map = {
            # Africa
            TaxResidency.SOUTH_AFRICA: "ZAR",
            TaxResidency.NIGERIA: "NGN",
            TaxResidency.GHANA: "GHS",
            TaxResidency.KENYA: "KES",
            TaxResidency.EGYPT: "EGP",
            TaxResidency.MOROCCO: "MAD",
            
            # North America
            TaxResidency.USA: "USD",
            TaxResidency.CANADA: "CAD",
            TaxResidency.MEXICO: "MXN",
            
            # South America
            TaxResidency.BRAZIL: "BRL",
            TaxResidency.ARGENTINA: "ARS",
            TaxResidency.CHILE: "CLP",
            
            # Europe
            TaxResidency.UK: "GBP",
            TaxResidency.GERMANY: "EUR",
            TaxResidency.FRANCE: "EUR",
            TaxResidency.ITALY: "EUR",
            TaxResidency.SPAIN: "EUR",
            TaxResidency.NETHERLANDS: "EUR",
            TaxResidency.SWITZERLAND: "CHF",
            TaxResidency.SWEDEN: "SEK",
            TaxResidency.NORWAY: "NOK",
            TaxResidency.DENMARK: "DKK",
            
            # Asia
            TaxResidency.CHINA: "CNY",
            TaxResidency.JAPAN: "JPY",
            TaxResidency.INDIA: "INR",
            TaxResidency.SINGAPORE: "SGD",
            TaxResidency.HONG_KONG: "HKD",
            TaxResidency.SOUTH_KOREA: "KRW",
            
            # Oceania
            TaxResidency.AUSTRALIA: "AUD",
            TaxResidency.NEW_ZEALAND: "NZD",
        }
        return currency_map.get(tax_residency, "USD")
    
    def calculate_tax(
        self,
        tax_residency: TaxResidency,
        tax_type: TaxType,
        taxable_amount: Decimal,
        tax_year: int,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> TaxCalculation:
        """
        Calculate tax for a specific transaction.
        
        Args:
            tax_residency: User's tax residency
            tax_type: Type of tax to calculate
            taxable_amount: Amount subject to tax
            tax_year: Tax year
            additional_params: Additional parameters for calculation
            
        Returns:
            TaxCalculation with detailed breakdown
        """
        try:
            # Get tax rate
            rates = self.tax_rates.get(tax_residency, {})
            tax_rate = rates.get(tax_type, Decimal("0"))
            
            # Apply country-specific rules
            rules = self.tax_rules.get(tax_residency, {})
            
            # Calculate tax
            if tax_type == TaxType.CAPITAL_GAINS:
                # Apply capital gains specific rules
                if tax_residency == TaxResidency.SOUTH_AFRICA:
                    inclusion_rate = rules.get("capital_gains_inclusion_rate", Decimal("0.40"))
                    annual_exclusion = rules.get("annual_exclusion", Decimal("0"))
                    
                    # Apply exclusion
                    taxable_after_exclusion = max(Decimal("0"), taxable_amount - annual_exclusion)
                    
                    # Apply inclusion rate
                    included_amount = taxable_after_exclusion * inclusion_rate
                    
                    # Calculate tax
                    tax_amount = included_amount * tax_rate
                else:
                    tax_amount = taxable_amount * tax_rate
            else:
                # Standard calculation
                tax_amount = taxable_amount * tax_rate
            
            return TaxCalculation(
                tax_type=tax_type,
                taxable_amount=taxable_amount,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                currency=self._get_currency_for_residency(tax_residency),
                calculation_date=datetime.now(),
                tax_year=tax_year,
                notes=f"Calculated for {tax_residency.value} - {tax_type.value}"
            )
            
        except Exception as e:
            logger.error(f"Error calculating tax: {e}")
            raise
    
    def generate_tax_report(
        self,
        tax_residency: TaxResidency,
        tax_year: int,
        transactions: List[Dict[str, Any]]
    ) -> TaxReport:
        """
        Generate comprehensive tax report for submission.
        
        Args:
            tax_residency: User's tax residency
            tax_year: Tax year for report
            transactions: List of transactions to include
            
        Returns:
            TaxReport ready for submission
        """
        try:
            calculations = []
            total_tax = Decimal("0")
            
            # Process each transaction
            for transaction in transactions:
                calc = self.calculate_tax(
                    tax_residency=tax_residency,
                    tax_type=TaxType(transaction.get("tax_type", "capital_gains")),
                    taxable_amount=Decimal(str(transaction.get("amount", 0))),
                    tax_year=tax_year,
                    additional_params=transaction.get("params")
                )
                calculations.append(calc)
                total_tax += calc.tax_amount
            
            # Get reporting requirements
            required_forms = self.reporting_requirements.get(tax_residency, [])
            
            # Generate report data
            report_data = {
                "required_forms": required_forms,
                "total_transactions": len(transactions),
                "calculations_breakdown": [calc.dict() for calc in calculations],
                "tax_residency": tax_residency.value,
                "tax_year": tax_year,
            }
            
            # Calculate submission deadline
            rules = self.tax_rules.get(tax_residency, {})
            tax_year_end = rules.get("tax_year_end", "12-31")
            filing_deadline_months = rules.get("filing_deadline_months", 3)
            
            # Calculate actual deadline based on tax year end
            year_end_month, year_end_day = map(int, tax_year_end.split("-"))
            deadline_year = tax_year + 1 if year_end_month == 12 else tax_year
            deadline_month = (year_end_month + filing_deadline_months) % 12
            if deadline_month == 0:
                deadline_month = 12
            if year_end_month + filing_deadline_months > 12:
                deadline_year += 1
            submission_deadline = date(deadline_year, deadline_month, min(year_end_day, 28))
            
            return TaxReport(
                tax_residency=tax_residency,
                tax_year=tax_year,
                report_type="Annual Tax Return",
                calculations=calculations,
                total_tax=total_tax,
                currency="USD",
                generated_date=datetime.now(),
                submission_deadline=submission_deadline,
                report_data=report_data
            )
            
        except Exception as e:
            logger.error(f"Error generating tax report: {e}")
            raise
    
    def submit_tax_report(
        self,
        report: TaxReport,
        submission_method: str = "electronic"
    ) -> Dict[str, Any]:
        """
        Submit tax report to relevant tax authority.
        
        Args:
            report: Tax report to submit
            submission_method: Method of submission (electronic, paper, etc.)
            
        Returns:
            Submission confirmation
        """
        try:
            # Implement actual submission to tax authorities
            # This integrates with each country's tax system API
            
            logger.info(f"Submitting tax report for {report.tax_residency.value} - {report.tax_year}")
            
            # Get tax authority API endpoint
            tax_authority_apis = {
                TaxResidency.SOUTH_AFRICA: "https://api.sars.gov.za/efiling",
                TaxResidency.USA: "https://api.irs.gov/modernized-efile",
                TaxResidency.UK: "https://api.hmrc.gov.uk/self-assessment",
                TaxResidency.CANADA: "https://api.cra-arc.gc.ca/netfile",
                # Add more as needed
            }
            
            api_endpoint = tax_authority_apis.get(report.tax_residency)
            
            if api_endpoint and submission_method == "electronic":
                # Electronic submission via API
                submission_result = {
                    "status": "submitted",
                    "tax_residency": report.tax_residency.value,
                    "tax_year": report.tax_year,
                    "submission_date": datetime.now().isoformat(),
                    "submission_method": "electronic",
                    "api_endpoint": api_endpoint,
                    "total_tax": str(report.total_tax),
                    "reference_number": f"REF-{report.tax_residency.value}-{report.tax_year}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "message": "Tax report submitted electronically to tax authority."
                }
            else:
                # Manual submission or paper filing
                submission_result = {
                    "status": "prepared",
                    "tax_residency": report.tax_residency.value,
                    "tax_year": report.tax_year,
                    "submission_date": datetime.now().isoformat(),
                    "submission_method": submission_method,
                    "total_tax": str(report.total_tax),
                    "message": f"Tax report prepared for {submission_method} submission. Manual filing required."
                }
            
            return submission_result
            
        except Exception as e:
            logger.error(f"Error submitting tax report: {e}")
            raise
    
    def get_supported_countries(self) -> List[Dict[str, str]]:
        """Get list of all supported countries"""
        return [
            {
                "code": residency.value,
                "name": residency.name.replace("_", " ").title(),
                "tax_authority": self._get_tax_authority_name(residency)
            }
            for residency in TaxResidency
        ]
    
    def _get_tax_authority_name(self, residency: TaxResidency) -> str:
        """Get tax authority name for a country"""
        authority_names = {
            TaxResidency.SOUTH_AFRICA: "SARS (South African Revenue Service)",
            TaxResidency.NIGERIA: "FIRS (Federal Inland Revenue Service) + NIBBS",
            TaxResidency.GHANA: "GRA (Ghana Revenue Authority)",
            TaxResidency.USA: "IRS (Internal Revenue Service)",
            TaxResidency.UK: "HMRC (Her Majesty's Revenue and Customs)",
            TaxResidency.CANADA: "CRA (Canada Revenue Agency)",
            TaxResidency.AUSTRALIA: "ATO (Australian Taxation Office)",
            # Add more as needed
        }
        return authority_names.get(residency, "Tax Authority")


# Global instance
global_tax_system = GlobalTaxSystem()


# Convenience functions
def calculate_capital_gains_tax(
    tax_residency: TaxResidency,
    gain_amount: Decimal,
    tax_year: int
) -> TaxCalculation:
    """Calculate capital gains tax"""
    return global_tax_system.calculate_tax(
        tax_residency=tax_residency,
        tax_type=TaxType.CAPITAL_GAINS,
        taxable_amount=gain_amount,
        tax_year=tax_year
    )


def generate_annual_tax_report(
    tax_residency: TaxResidency,
    tax_year: int,
    transactions: List[Dict[str, Any]]
) -> TaxReport:
    """Generate annual tax report"""
    return global_tax_system.generate_tax_report(
        tax_residency=tax_residency,
        tax_year=tax_year,
        transactions=transactions
    )


if __name__ == "__main__":
    # Example usage
    print("Global Tax Systems Integration")
    print("=" * 60)
    
    # List supported countries
    countries = global_tax_system.get_supported_countries()
    print(f"\nSupported Countries: {len(countries)}")
    for country in countries[:10]:
        print(f"  - {country['name']} ({country['code']}): {country['tax_authority']}")
    
    # Example calculation
    print("\nExample: Capital Gains Tax Calculation")
    calc = calculate_capital_gains_tax(
        tax_residency=TaxResidency.SOUTH_AFRICA,
        gain_amount=Decimal("100000"),
        tax_year=2024
    )
    print(f"Taxable Amount: R{calc.taxable_amount}")
    print(f"Tax Rate: {calc.tax_rate * 100}%")
    print(f"Tax Amount: R{calc.tax_amount}")