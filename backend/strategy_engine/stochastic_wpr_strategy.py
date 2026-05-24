import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Constants from TheMasterMind.mq4
# These specific values trigger buy/sell signals.
STOCHASTIC_BUY_THRESHOLD: float = 3.0   # sig_buy < 3
STOCHASTIC_SELL_THRESHOLD: float = 97.0 # sig_sell > 97
WPR_BUY_THRESHOLD: float = -99.9        # sig_high < -99.9
WPR_SELL_THRESHOLD: float = -0.1        # sig_low > -0.1

def generate_stochastic_wpr_signals(
    stochastic_signal_line: np.ndarray, # Typically %D line of Stochastic
    williams_percent_r: np.ndarray # Williams %R
) -> Dict[str, Any]:
    """
    Generates BUY or SELL signals based on TheMasterMind.mq4's logic
    using Stochastic Oscillator and Williams %R.

    Args:
        stochastic_signal_line (np.ndarray): The signal line (e.g., %D) of the Stochastic Oscillator.
        williams_percent_r (np.ndarray): The Williams %R indicator values.

    Returns:
        Dict[str, Any]: A dictionary containing the signal ('BUY', 'SELL', 'NONE')
                        and a confidence score.
    """
    if len(stochastic_signal_line) == 0 or len(williams_percent_r) == 0:
        return {"signal": "NONE", "confidence": 0.0, "reason": "Insufficient indicator data."}

    # Get the latest indicator values
    latest_stoch_sig = stochastic_signal_line[-1]
    latest_wpr = williams_percent_r[-1]

    if np.isnan(latest_stoch_sig) or np.isnan(latest_wpr):
        return {"signal": "NONE", "confidence": 0.0, "reason": "Latest indicator values are NaN."}

    buy_value = 0
    sell_value = 0

    # Buy condition: sig_buy < 3 && sig_high < -99.9
    # Note: MQL's iStochastic returns values 0-100. Williams %R typically returns -100 to 0.
    # The condition `sig_high < -99.9` (for WPR) implies a very oversold condition, near -100.
    if latest_stoch_sig < STOCHASTIC_BUY_THRESHOLD and latest_wpr < WPR_BUY_THRESHOLD:
        buy_value = 1
        logger.info(f"Stochastic/WPR BUY signal detected. Stoch: {latest_stoch_sig:.2f}, WPR: {latest_wpr:.2f}")

    # Sell condition: sig_sell > 97 && sig_low > -0.1
    # The condition `sig_low > -0.1` (for WPR) implies a very overbought condition, near 0.
    if latest_stoch_sig > STOCHASTIC_SELL_THRESHOLD and latest_wpr > WPR_SELL_THRESHOLD:
        sell_value = 1
        logger.info(f"Stochastic/WPR SELL signal detected. Stoch: {latest_stoch_sig:.2f}, WPR: {latest_wpr:.2f}")

    # Determine final signal and confidence
    if buy_value > 0 and sell_value == 0:
        return {"signal": "BUY", "confidence": 0.8, "reason": "Stochastic and Williams %R indicate strong oversold/buy potential."}
    elif sell_value > 0 and buy_value == 0:
        return {"signal": "SELL", "confidence": 0.8, "reason": "Stochastic and Williams %R indicate strong overbought/sell potential."}
    else:
        # If both or neither are true, or conflicting signals exist, return NONE
        return {"signal": "NONE", "confidence": 0.0, "reason": "No clear signal from Stochastic/WPR, or conflicting signals."}

# Example usage (mock data)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Scenario 1: Strong BUY Signal
    mock_stoch_buy = np.array([50, 40, 2.5]) # Last value < 3
    mock_wpr_buy = np.array([-50, -80, -99.95]) # Last value < -99.9
    print("--- Scenario 1: Expect BUY Signal ---")
    signal_buy = generate_stochastic_wpr_signals(mock_stoch_buy, mock_wpr_buy)
    print(signal_buy)

    # Scenario 2: Strong SELL Signal
    mock_stoch_sell = np.array([50, 60, 97.5]) # Last value > 97
    mock_wpr_sell = np.array([-50, -20, -0.05]) # Last value > -0.1
    print("\n--- Scenario 2: Expect SELL Signal ---")
    signal_sell = generate_stochastic_wpr_signals(mock_stoch_sell, mock_wpr_sell)
    print(signal_sell)

    # Scenario 3: No Signal (Neutral)
    mock_stoch_neutral = np.array([50, 55, 60])
    mock_wpr_neutral = np.array([-50, -40, -30])
    print("\n--- Scenario 3: Expect NONE Signal ---")
    signal_neutral = generate_stochastic_wpr_signals(mock_stoch_neutral, mock_wpr_neutral)
    print(signal_neutral)
    
    # Scenario 4: Conflicting (should be NONE)
    mock_stoch_conflict = np.array([2.5, 97.5])
    mock_wpr_conflict = np.array([-99.95, -0.05])
    print("\n--- Scenario 4: Expect NONE Signal (Conflicting) ---")
    signal_conflict = generate_stochastic_wpr_signals(mock_stoch_conflict, mock_wpr_conflict)
    print(signal_conflict)