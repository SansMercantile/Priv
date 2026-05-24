# backend/financial_automation/sars_tax_reporting.py

import logging
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# --- SARS Tax Constants for 2024/2025 Tax Year (Illustrative) ---
# These values should be updated annually from official SARS publications.
SARS_ANNUAL_EXCLUSION = Decimal("40000.00")
SARS_INCLUSION_RATE_INDIVIDUAL = Decimal("0.40") # 40% for individuals

class Transaction(BaseModel):
    """Represents a single financial transaction (buy or sell)."""
    asset_name: str
    transaction_type: str  # 'buy' or 'sell'
    quantity: Decimal
    price_per_unit: Decimal
    transaction_date: datetime
    transaction_costs: Decimal = Decimal("0.00")

    @property
    def base_cost(self) -> Decimal:
        return self.quantity * self.price_per_unit + self.transaction_costs

    @property
    def proceeds(self) -> Decimal:
        return self.quantity * self.price_per_unit - self.transaction_costs

class SarsTaxCalculator:
    """
    Calculates tax liabilities according to South African Revenue Service (SARS) rules,
    with a focus on Capital Gains Tax (CGT).
    """
    def __init__(self, transactions: List[Transaction]):
        self.transactions = sorted(transactions, key=lambda t: t.transaction_date)
        self.disposal_events: List[Dict[str, Any]] = []
        logger.info("SarsTaxCalculator initialized.")

    def _calculate_cgt_events(self):
        """
        Processes transactions to identify disposal events and calculate capital gains or losses
        using the First-In, First-Out (FIFO) accounting method.
        """
        # This is a simplified FIFO implementation. A real-world scenario would need to handle
        # corporate actions like stock splits, and partial sales more robustly.
        asset_buys: Dict[str, List[Transaction]] = {}

        for tx in self.transactions:
            if tx.transaction_type == 'buy':
                asset_buys.setdefault(tx.asset_name, []).append(tx)
            elif tx.transaction_type == 'sell':
                if tx.asset_name not in asset_buys or not asset_buys[tx.asset_name]:
                    logger.warning(f"Sell transaction for {tx.asset_name} with no prior purchase history. Skipping.")
                    continue

                proceeds = tx.proceeds
                quantity_to_sell = tx.quantity
                base_cost_for_sale = Decimal("0.00")

                while quantity_to_sell > 0 and asset_buys[tx.asset_name]:
                    oldest_buy = asset_buys[tx.asset_name][0]
                    
                    if oldest_buy.quantity <= quantity_to_sell:
                        # Entire oldest buy parcel is sold
                        base_cost_for_sale += oldest_buy.base_cost
                        quantity_to_sell -= oldest_buy.quantity
                        asset_buys[tx.asset_name].pop(0)
                    else:
                        # Partial sale of the oldest buy parcel
                        proportion = quantity_to_sell / oldest_buy.quantity
                        base_cost_for_sale += oldest_buy.base_cost * proportion
                        oldest_buy.quantity -= quantity_to_sell
                        quantity_to_sell = Decimal("0.00")

                capital_gain_loss = proceeds - base_cost_for_sale
                self.disposal_events.append({
                    "asset_name": tx.asset_name,
                    "disposal_date": tx.transaction_date,
                    "proceeds": proceeds,
                    "base_cost": base_cost_for_sale,
                    "capital_gain_loss": capital_gain_loss
                })

    def generate_sars_report(self) -> Dict[str, Any]:
        """
        Generates a summary report for SARS tax filing purposes.
        """
        self._calculate_cgt_events()

        total_capital_gain = sum(event['capital_gain_loss'] for event in self.disposal_events)
        
        # Apply the annual exclusion
        net_capital_gain = total_capital_gain - SARS_ANNUAL_EXCLUSION
        if net_capital_gain < 0:
            net_capital_gain = Decimal("0.00") # Exclusion cannot create a loss

        # Apply the inclusion rate
        taxable_gain = net_capital_gain * SARS_INCLUSION_RATE_INDIVIDUAL

        # Quantize to two decimal places for currency
        quantizer = Decimal("0.01")

        report = {
            "tax_year": f"{datetime.now().year - 1}/{datetime.now().year}",
            "currency": "ZAR",
            "summary": {
                "total_proceeds": sum(e['proceeds'] for e in self.disposal_events).quantize(quantizer, ROUND_HALF_UP),
                "total_base_cost": sum(e['base_cost'] for e in self.disposal_events).quantize(quantizer, ROUND_HALF_UP),
                "total_capital_gain_loss": total_capital_gain.quantize(quantizer, ROUND_HALF_UP),
                "annual_exclusion": SARS_ANNUAL_EXCLUSION.quantize(quantizer, ROUND_HALF_UP),
                "net_capital_gain": net_capital_gain.quantize(quantizer, ROUND_HALF_UP),
                "inclusion_rate": f"{SARS_INCLUSION_RATE_INDIVIDUAL:.0%}",
                "taxable_gain": taxable_gain.quantize(quantizer, ROUND_HALF_UP)
            },
            "disposal_events": [
                {k: (v.quantize(quantizer, ROUND_HALF_UP) if isinstance(v, Decimal) else v) for k, v in event.items()}
                for event in self.disposal_events
            ]
        }
        logger.info("SARS Capital Gains Tax report generated successfully.")
        return report

