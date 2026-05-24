import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Translation of the Sym array from symbolsynthesizer.mq5
# Format: {"main_pair": [leg1, leg2, calc_type]}
# calc_type: "L" for Left-side multiplication (e.g., EURUSD * USDJPY = EURJPY)
#            "S" for Right-side division (e.g., USDCHF / EURCHF = EURUSD)
# This array defines the specific currency triangles for which synthetic rates can be calculated.
CURRENCY_TRIANGLES: Dict[str, Tuple[str, str, str]] = {
    "EURUSD": ("EURGBP", "GBPUSD", "L"), # EURUSD = EURGBP * GBPUSD (but MQL implies EURGBP / GBPUSD?)
                                        # MQL: Sym[0][0]="EURUSD"; Sym[0][1]="EURGBP"; Sym[0][2]="GBPUSD"; Sym[0][3]="L"
                                        # This means EURUSD is synthesized from EURGBP and GBPUSD.
                                        # If "L", it means EURGBP * GBPUSD. (EUR/GBP * GBP/USD = EUR/USD). Correct.

    "GBPUSD": ("EURGBP", "EURUSD", "S"), # GBPUSD = EURUSD / EURGBP (EUR/USD / EUR/GBP = GBP/USD). Correct.
                                        # MQL: Sym[1][0]="GBPUSD"; Sym[1][1]="EURGBP"; Sym[1][2]="EURUSD"; Sym[1][3]="S"
                                        # This means GBPUSD is synthesized from EURGBP and EURUSD. If "S", it means EURUSD / EURGBP.

    "USDCHF": ("EURUSD", "EURCHF", "S"), # USDCHF = EURCHF / EURUSD (CHF/EUR * EUR/USD = CHF/USD, so 1/USDCHF)
                                        # MQL: Sym[2][0]="USDCHF"; Sym[2][1]="EURUSD"; Sym[2][2]="EURCHF"; Sym[2][3]="S"
                                        # This means USDCHF synthesized from EURUSD and EURCHF. If "S", then EURCHF / EURUSD. (EURCHF / EURUSD = CHF/USD). Correct.

    "USDJPY": ("EURUSD", "EURJPY", "S"), # USDJPY = EURJPY / EURUSD (JPY/EUR * EUR/USD = JPY/USD)
                                        # MQL: Sym[3][0]="USDJPY"; Sym[3][1]="EURUSD"; Sym[3][2]="EURJPY"; Sym[3][3]="S"
                                        # Then EURJPY / EURUSD.

    "USDCAD": ("EURUSD", "EURCAD", "S"), # USDCAD = EURCAD / EURUSD
                                        # MQL: Sym[4][0]="USDCAD"; Sym[4][1]="EURUSD"; Sym[4][2]="EURCAD"; Sym[4][3]="S"

    "AUDUSD": ("EURAUD", "EURUSD", "S"), # AUDUSD = EURUSD / EURAUD
                                        # MQL: Sym[5][0]="AUDUSD"; Sym[5][1]="EURAUD"; Sym[5][2]="EURUSD"; Sym[5][3]="S"

    "EURGBP": ("GBPUSD", "EURUSD", "S"), # EURGBP = EURUSD / GBPUSD (EUR/USD / GBP/USD = EUR/GBP). Correct.
                                        # MQL: Sym[6][0]="EURGBP"; Sym[6][1]="GBPUSD"; Sym[6][2]="EURUSD"; Sym[6][3]="S"
                                        # This means EURGBP is synthesized from GBPUSD and EURUSD. If "S", it means EURUSD / GBPUSD.

    "EURAUD": ("AUDUSD", "EURUSD", "S"), # EURAUD = EURUSD / AUDUSD (EUR/USD / AUD/USD = EUR/AUD). Correct.
                                        # MQL: Sym[7][0]="EURAUD"; Sym[7][1]="AUDUSD"; Sym[7][2]="EURUSD"; Sym[7][3]="S"

    "EURCHF": ("EURUSD", "USDCHF", "L"), # EURCHF = EURUSD * USDCHF (EUR/USD * USD/CHF = EUR/CHF). Correct.
                                        # MQL: Sym[8][0]="EURCHF"; Sym[8][1]="EURUSD"; Sym[8][2]="USDCHF"; Sym[8][3]="L"

    "EURJPY": ("EURUSD", "USDJPY", "L"), # EURJPY = EURUSD * USDJPY (EUR/USD * USD/JPY = EUR/JPY). Correct.
                                        # MQL: Sym[9][0]="EURJPY"; Sym[9][1]="EURUSD"; Sym[9][2]="USDJPY"; Sym[9][3]="L"

    "GBPJPY": ("GBPUSD", "USDJPY", "L"), # GBPJPY = GBPUSD * USDJPY (GBP/USD * USD/JPY = GBP/JPY). Correct.
                                        # MQL: Sym[10][0]="GBPJPY"; Sym[10][1]="GBPUSD"; Sym[10][2]="USDJPY"; Sym[10][3]="L"

    "AUDJPY": ("AUDUSD", "USDJPY", "L"), # AUDJPY = AUDUSD * USDJPY (AUD/USD * USD/JPY = AUD/JPY). Correct.
                                        # MQL: Sym[11][0]="AUDJPY"; Sym[11][1]="AUDUSD"; Sym[11][2]="USDJPY"; Sym[11][3]="L"

    "GBPCHF": ("GBPUSD", "USDCHF", "L"), # GBPCHF = GBPUSD * USDCHF (GBP/USD * USD/CHF = GBP/CHF). Correct.
                                        # MQL: Sym[12][0]="GBPCHF"; Sym[12][1]="GBPUSD"; Sym[12][2]="USDCHF"; Sym[12][3]="L"
}

def get_synthetic_cross_rates(
    main_pair: str,
    all_symbol_prices: Dict[str, Dict[str, float]] # {"EURUSD": {"bid": X, "ask": Y}, ...}
) -> Optional[Dict[str, float]]:
    """
    Calculates the synthetic bid and ask rates for a given main currency pair
    based on its constituent cross-pairs, as per symbolsynthesizer.mq5 logic.

    Args:
        main_pair (str): The currency pair for which to calculate the synthetic rate (e.g., "EURJPY").
        all_symbol_prices (Dict[str, Dict[str, float]]): Dictionary of current bid/ask prices
                                                        for all relevant currency symbols.

    Returns:
        Optional[Dict[str, float]]: A dictionary {"synthetic_bid": X, "synthetic_ask": Y}
                                    or None if the main_pair is not defined in CURRENCY_TRIANGLES
                                    or if required cross-pair prices are missing.
    """
    triangle_info = CURRENCY_TRIANGLES.get(main_pair)
    if not triangle_info:
        logger.warning(f"Main pair '{main_pair}' not defined in CURRENCY_TRIANGLES for synthetic rate calculation.")
        return None

    leg1_pair, leg2_pair, calc_type = triangle_info

    leg1_prices = all_symbol_prices.get(leg1_pair)
    leg2_prices = all_symbol_prices.get(leg2_pair)

    if not leg1_prices or not leg2_prices:
        logger.warning(f"Missing prices for legs {leg1_pair} or {leg2_pair} to calculate synthetic rate for {main_pair}.")
        return None

    leg1_bid = leg1_prices["bid"]
    leg1_ask = leg1_prices["ask"]
    leg2_bid = leg2_prices["bid"]
    leg2_ask = leg2_prices["ask"]

    synthetic_bid = 0.0
    synthetic_ask = 0.0

    # Logic based on MQL's 'L' (Left-side multiplication) or 'S' (Right-side division)
    if calc_type == "L": # Synthetic = Leg1 * Leg2 (e.g., EURUSD * USDJPY = EURJPY)
        synthetic_bid = leg1_bid * leg2_bid
        synthetic_ask = leg1_ask * leg2_ask
    elif calc_type == "S": # Synthetic = Leg2 / Leg1 (e.g., EURUSD / GBPUSD = EURGBP, where EURUSD is Leg2, GBPUSD is Leg1)
                           # Note: In MQL `Sym[X][3]="S"` implies `vBID=bid2/bid1` and `vASK=ask2/ask1`
                           # So it's always Leg2 / Leg1
        if leg1_ask == 0 or leg1_bid == 0: # Avoid division by zero
            logger.error(f"Cannot calculate synthetic rates for {main_pair}: Leg1 ({leg1_pair}) has zero ask/bid.")
            return None
        synthetic_bid = leg2_bid / leg1_ask # To buy Leg2 and sell Leg1, you get Leg2_bid / Leg1_ask
        synthetic_ask = leg2_ask / leg1_bid # To sell Leg2 and buy Leg1, you pay Leg2_ask / Leg1_bid
    else:
        logger.error(f"Unknown calculation type '{calc_type}' for {main_pair}.")
        return None
        
    return {"synthetic_bid": synthetic_bid, "synthetic_ask": synthetic_ask}

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Mock current prices
    mock_all_prices = {
        "EURUSD": {"bid": 1.0850, "ask": 1.0855},
        "USDJPY": {"bid": 150.00, "ask": 150.05},
        "EURGBP": {"bid": 0.8500, "ask": 0.8505},
        "GBPUSD": {"bid": 1.2700, "ask": 1.2705},
        "EURCHF": {"bid": 0.9500, "ask": 0.9505},
        "USDCHF": {"bid": 0.9000, "ask": 0.9005}
    }

    print("--- Calculating Synthetic EURJPY ---")
    # Expected: EURUSD * USDJPY
    # Synthetic Bid = 1.0850 * 150.00 = 162.75
    # Synthetic Ask = 1.0855 * 150.05 = 162.880275
    eurjpy_synthetic = get_synthetic_cross_rates("EURJPY", mock_all_prices)
    if eurjpy_synthetic:
        print(f"Synthetic EURJPY Bid: {eurjpy_synthetic['synthetic_bid']:.5f}")
        print(f"Synthetic EURJPY Ask: {eurjpy_synthetic['synthetic_ask']:.5f}")
    else:
        print("Failed to calculate synthetic EURJPY.")

    print("\n--- Calculating Synthetic EURGBP ---")
    # Expected: EURUSD / GBPUSD
    # Synthetic Bid = EURUSD.Bid / GBPUSD.Ask = 1.0850 / 1.2705 = 0.853994
    # Synthetic Ask = EURUSD.Ask / GBPUSD.Bid = 1.0855 / 1.2700 = 0.854724
    eurgbp_synthetic = get_synthetic_cross_rates("EURGBP", mock_all_prices)
    if eurgbp_synthetic:
        print(f"Synthetic EURGBP Bid: {eurgbp_synthetic['synthetic_bid']:.5f}")
        print(f"Synthetic EURGBP Ask: {eurgbp_synthetic['synthetic_ask']:.5f}")
    else:
        print("Failed to calculate synthetic EURGBP.")

    print("\n--- Calculating Synthetic USDCHF (missing required leg) ---")
    # Expected: EURCHF / EURUSD. We don't need USDCHF from triangle for USDCHF.
    # The triangle is USDCHF synthesized from EURUSD and EURCHF.
    # MQL `Sym[2][0]="USDCHF"; Sym[2][1]="EURUSD"; Sym[2][2]="EURCHF"; Sym[2][3]="S"`
    # This means `EURCHF / EURUSD` to get `USDCHF`. So, `vBID = bid2/bid1 = EURCHF.Bid / EURUSD.Ask`
    # This interpretation is complex. Let's use `symbolsynthesizer`'s own `Sym` definition and apply `bid2/bid1` etc.
    # Correcting my interpretation of MQL's 'S' for `USDCHF`:
    # `vBID = bid2/bid1` => `EURCHF.Bid / EURUSD.Ask`
    # `vASK = ask2/ask1` => `EURCHF.Ask / EURUSD.Bid`
    # Let's re-run example with actual definition for USDCHF:
    # Synthetic USDCHF Bid = EURCHF.Bid / EURUSD.Ask = 0.9500 / 1.0855 = 0.87517
    # Synthetic USDCHF Ask = EURCHF.Ask / EURUSD.Bid = 0.9505 / 1.0850 = 0.87607
    usdchf_synthetic = get_synthetic_cross_rates("USDCHF", mock_all_prices)
    if usdchf_synthetic:
        print(f"Synthetic USDCHF Bid: {usdchf_synthetic['synthetic_bid']:.5f}")
        print(f"Synthetic USDCHF Ask: {usdchf_synthetic['synthetic_ask']:.5f}")
    else:
        print("Failed to calculate synthetic USDCHF.")

    print("\n--- Calculating Synthetic EURAUD (not in list) ---")
    euraud_synthetic = get_synthetic_cross_rates("EURAUD", mock_all_prices)
    if euraud_synthetic:
        print(f"Synthetic EURAUD Bid: {euraud_synthetic['synthetic_bid']:.5f}")
        print(f"Synthetic EURAUD Ask: {euraud_synthetic['synthetic_ask']:.5f}")
    else:
        print("Failed to calculate synthetic EURAUD (expected due to no info in mock_all_prices).")

    print("\n--- Calculating Synthetic USDJPY (missing prices for leg1 or leg2) ---")
    mock_prices_missing_leg = {
        "EURUSD": {"bid": 1.0850, "ask": 1.0855},
        # USDJPY is main, needs EURUSD and EURJPY. EURJPY is missing.
    }
    usdjpy_synthetic_missing = get_synthetic_cross_rates("USDJPY", mock_prices_missing_leg)
    if usdjpy_synthetic_missing:
        print(f"Synthetic USDJPY Bid: {usdjpy_synthetic_missing['synthetic_bid']:.5f}")
    else:
        print("Failed to calculate synthetic USDJPY (expected due to missing leg prices).")